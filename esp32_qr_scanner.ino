#include "esp_camera.h"
#include <WiFi.h>
#include <HTTPClient.h>

// WiFi credentials
const char* ssid = "YOUR_WIFI_SSID";
const char* password = "YOUR_WIFI_PASSWORD";

// Server configuration
const char* serverIP = "ipv4";  // Replace with your server IP
const int serverPort = 8000;
String statusURL = "http://" + String(serverIP) + ":" + String(serverPort) + "/esp32/status";
String uploadURL = "http://" + String(serverIP) + ":" + String(serverPort) + "/esp32/upload";

// Camera pins for AI-Thinker ESP32-CAM
#define PWDN_GPIO_NUM     32
#define RESET_GPIO_NUM    -1
#define XCLK_GPIO_NUM      0
#define SIOD_GPIO_NUM     26
#define SIOC_GPIO_NUM     27
#define Y9_GPIO_NUM       35
#define Y8_GPIO_NUM       34
#define Y7_GPIO_NUM       39
#define Y6_GPIO_NUM       36
#define Y5_GPIO_NUM       21
#define Y4_GPIO_NUM       19
#define Y3_GPIO_NUM       18
#define Y2_GPIO_NUM        5
#define VSYNC_GPIO_NUM    25
#define HREF_GPIO_NUM     23
#define PCLK_GPIO_NUM     22

void setup() {
  Serial.begin(115200);
  Serial.println("\n\nESP32-CAM QR Scanner Starting...");

  // Initialize camera
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
  config.pin_sscb_sda = SIOD_GPIO_NUM;
  config.pin_sscb_scl = SIOC_GPIO_NUM;
  config.pin_pwdn = PWDN_GPIO_NUM;
  config.pin_reset = RESET_GPIO_NUM;
  config.xclk_freq_hz = 20000000;
  config.pixel_format = PIXFORMAT_JPEG;
  
  // Lower resolution to reduce memory usage
  config.frame_size = FRAMESIZE_QVGA;  // 320x240
  config.jpeg_quality = 12;
  config.fb_count = 1;

  // Camera init
  esp_err_t err = esp_camera_init(&config);
  if (err != ESP_OK) {
    Serial.printf("Camera init failed with error 0x%x\n", err);
    return;
  }
  
  Serial.println("Camera initialized!");

  // Connect to WiFi
  WiFi.begin(ssid, password);
  Serial.print("Connecting to WiFi");
  
  int wifi_retry = 0;
  while (WiFi.status() != WL_CONNECTED && wifi_retry < 20) {
    delay(500);
    Serial.print(".");
    wifi_retry++;
  }
  
  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("\nWiFi connected!");
    Serial.print("IP address: ");
    Serial.println(WiFi.localIP());
    Serial.print("Server: ");
    Serial.println(uploadURL);
  } else {
    Serial.println("\nFailed to connect to WiFi!");
  }
}

void loop() {
  // Check if WiFi is connected
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("WiFi disconnected, reconnecting...");
    WiFi.begin(ssid, password);
    delay(5000);
    return;
  }

  // Print connection info periodically
  static unsigned long lastPrint = 0;
  if (millis() - lastPrint > 10000) {  // Every 10 seconds
    Serial.println("=== Status ===");
    Serial.print("ESP32 IP: ");
    Serial.println(WiFi.localIP());
    Serial.print("Server IP: ");
    Serial.println(serverIP);
    Serial.print("Checking: ");
    Serial.println(statusURL);
    lastPrint = millis();
  }

  // Check server status to see if camera should be active
  if (!checkServerStatus()) {
    Serial.println("Camera inactive, waiting...");
    delay(3000);  // Check every 3 seconds
    return;
  }

  // Camera is active, capture and send frame
  Serial.println("Camera active - capturing frame...");
  
  camera_fb_t* fb = esp_camera_fb_get();
  if (!fb) {
    Serial.println("Camera capture failed");
    delay(1000);
    return;
  }

  // Send image to server
  HTTPClient http;
  http.begin(uploadURL);
  http.addHeader("Content-Type", "application/octet-stream");
  
  int httpResponseCode = http.POST(fb->buf, fb->len);
  
  if (httpResponseCode > 0) {
    String response = http.getString();
    Serial.print("Response: ");
    Serial.println(response);
    
    // If scan was successful, you could add a delay or LED indication
    if (response.indexOf("\"status\":\"OK\"") > 0) {
      Serial.println("✓ QR Code scanned successfully!");
      delay(2000);  // Prevent duplicate scans
    }
  } else {
    Serial.print("Error sending image: ");
    Serial.println(httpResponseCode);
  }
  
  http.end();
  esp_camera_fb_return(fb);
  
  delay(200);  // Capture every 200ms = 5 FPS (adjust for desired framerate: 100=10fps, 333=3fps, 500=2fps, 1000=1fps)
}

bool checkServerStatus() {
  HTTPClient http;
  http.begin(statusURL);
  http.setTimeout(5000);
  
  int httpResponseCode = http.GET();
  
  if (httpResponseCode > 0) {
    String response = http.getString();
    http.end();
    
    // Check if response contains "active":true
    if (response.indexOf("\"active\":true") > 0) {
      return true;
    }
  } else {
    Serial.print("Status check failed: ");
    Serial.println(httpResponseCode);
  }
  
  http.end();
  return false;
}
