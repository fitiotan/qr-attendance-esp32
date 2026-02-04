#include "esp_camera.h"
#include <WiFi.h>
#include <HTTPClient.h>

//
// WARNING!!! PSRAM IC required for stability
//            Ensure ESP32 Wrover Module or other board with PSRAM is selected
//

// ===================
// Select camera model
// ===================
#define CAMERA_MODEL_AI_THINKER // Has PSRAM
#include "camera_pins.h"

// ===========================
// WiFi credentials
// ===========================
const char *ssid = "name"; // Replace with your SSID
const char *password = "password"; // Replace with your WiFi password

// ===========================
// Server configuration
// ===========================
const char* serverIP = "ipv4";  // Replace with your server IP
const int serverPort = 8000;
String statusURL = "http://" + String(serverIP) + ":" + String(serverPort) + "/esp32/status";
String uploadURL = "http://" + String(serverIP) + ":" + String(serverPort) + "/esp32/upload";

// ===========================
// Timing variables
// ===========================
unsigned long lastStatusCheck = 0;
unsigned long lastFrameTime = 0;
bool cameraActive = false;

#define STATUS_CHECK_INTERVAL 5000   // Check server status every 5 seconds
#define FRAME_INTERVAL 200           // Capture frame every 200ms (~5 FPS)

void setup() {
  Serial.begin(115200);
  Serial.setDebugOutput(false);
  delay(1000);
  Serial.println("\n\n========== ESP32-CAM QR Scanner ==========");
  Serial.println("Using Official Espressif Camera Library");

  camera_config_t config;
  config.ledc_channel = LEDC_CHANNEL_0;
  config.ledc_timer = LEDC_TIMER_0;
  config.pin_d0 = Y2_GPIO_NUM;
  config.pin_d1 = Y3_GPIO_NUM;
  config.pin_d2 = Y4_GPIO_NUM;
  config.pin_d3 = Y5_GPIO_NUM;
  config.pin_d4 = Y6_GPIO_NUM;
  config.pin_d5 = Y7_GPIO_NUM;
  config.pin_d6 = Y8_GPIO_NUM;
  config.pin_d7 = Y9_GPIO_NUM;
  config.pin_xclk = XCLK_GPIO_NUM;
  config.pin_pclk = PCLK_GPIO_NUM;
  config.pin_vsync = VSYNC_GPIO_NUM;
  config.pin_href = HREF_GPIO_NUM;
  config.pin_sccb_sda = SIOD_GPIO_NUM;
  config.pin_sccb_scl = SIOC_GPIO_NUM;
  config.pin_pwdn = PWDN_GPIO_NUM;
  config.pin_reset = RESET_GPIO_NUM;
  config.xclk_freq_hz = 20000000;
  config.pixel_format = PIXFORMAT_JPEG;
  config.grab_mode = CAMERA_GRAB_WHEN_EMPTY;
  
  // PSRAM configuration
  if (psramFound()) {
    Serial.println("[OK] PSRAM found - enabling high quality mode");
    config.fb_location = CAMERA_FB_IN_PSRAM;
    config.jpeg_quality = 10;
    config.fb_count = 2;
    config.grab_mode = CAMERA_GRAB_LATEST;
    config.frame_size = FRAMESIZE_QVGA;  // 320x240
  } else {
    Serial.println("[WARN] No PSRAM - using lower quality");
    config.fb_location = CAMERA_FB_IN_DRAM;
    config.jpeg_quality = 8;
    config.fb_count = 1;
    config.frame_size = FRAMESIZE_QQVGA;  // 160x120
  }

  // Camera init
  esp_err_t err = esp_camera_init(&config);
  if (err != ESP_OK) {
    Serial.printf("[ERROR] Camera init failed with error 0x%x\n", err);
    return;
  }
  Serial.println("[OK] Camera initialized!");

  // Sensor configuration
  sensor_t *s = esp_camera_sensor_get();
  if (s->id.PID == OV3660_PID) {
    s->set_vflip(s, 1);
    s->set_brightness(s, 1);
    s->set_saturation(s, -2);
  }
  
  // Set lower frame size for initial stability
  s->set_framesize(s, FRAMESIZE_QVGA);

  // WiFi connection
  Serial.print("[WIFI] Connecting to ");
  Serial.println(ssid);
  WiFi.begin(ssid, password);
  WiFi.setSleep(false);

  int wifi_attempts = 0;
  while (WiFi.status() != WL_CONNECTED && wifi_attempts < 20) {
    delay(500);
    Serial.print(".");
    wifi_attempts++;
  }

  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("\n[OK] WiFi connected!");
    Serial.print("[IP] ");
    Serial.println(WiFi.localIP());
    Serial.print("[SERVER] ");
    Serial.println(serverIP);
  } else {
    Serial.println("\n[ERROR] WiFi connection failed!");
  }

  lastStatusCheck = millis();
  lastFrameTime = millis();
}

void loop() {
  unsigned long now = millis();

  // ===== STATUS CHECK (every 5 seconds) =====
  if (now - lastStatusCheck >= STATUS_CHECK_INTERVAL) {
    lastStatusCheck = now;
    checkCameraStatus();
  }

  // ===== FRAME CAPTURE (every 200ms for ~5 FPS) =====
  if (now - lastFrameTime >= FRAME_INTERVAL) {
    lastFrameTime = now;

    if (cameraActive) {
      captureAndUpload();
    }
  }

  delay(5);
}

void checkCameraStatus() {
  if (WiFi.status() != WL_CONNECTED) {
    cameraActive = false;
    return;
  }

  HTTPClient http;
  http.begin(statusURL);
  http.setTimeout(3000);

  int httpResponseCode = http.GET();

  if (httpResponseCode == 200) {
    String response = http.getString();
    bool wasActive = cameraActive;
    cameraActive = (response.indexOf("\"active\":true") > 0);

    if (cameraActive != wasActive) {
      Serial.print("[STATUS] Camera: ");
      Serial.println(cameraActive ? "ACTIVE" : "INACTIVE");
    }
  } else {
    cameraActive = false;
  }

  http.end();
}

void captureAndUpload() {
  // Capture frame
  camera_fb_t *fb = esp_camera_fb_get();
  if (!fb) {
    Serial.println("[CAM] Capture failed");
    return;
  }

  // Upload to server
  HTTPClient http;
  http.begin(uploadURL);
  http.addHeader("Content-Type", "application/octet-stream");
  http.setTimeout(5000);

  int httpResponseCode = http.POST(fb->buf, fb->len);

  // Return frame buffer immediately
  esp_camera_fb_return(fb);

  if (httpResponseCode > 0) {
    String response = http.getString();

    if (response.indexOf("[SUCCESS]") > 0) {
      Serial.print("[SCAN] ");
      Serial.println(response);
      delay(1500);  // Prevent duplicate scans
    }
  } else {
    // Timeout or connection error
  }

  http.end();
}
