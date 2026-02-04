# QR Code Attendance System

A modern, real-time attendance tracking system using QR codes and an ESP32-CAM module. Features check-in/check-out support, live camera feed, and a responsive web interface.

## Features

✅ **QR Code Generation** - Dynamic QR codes with 60-second expiry  
✅ **Check-In/Check-Out System** - Tracks daily attendance with dual-state QR codes  
✅ **Live ESP32 Camera Feed** - Real-time video feed from ESP32-CAM with optimized 5 FPS  
✅ **Admin Dashboard** - Manage clients, view attendance logs, manual entry support  
✅ **Client Portal** - Generate and scan QR codes with status-aware interface  
✅ **Session Management** - 15-minute timeout with automatic invalidation on server restart  
✅ **Mobile Responsive** - Fully functional on phones, tablets, and desktops  
✅ **Attendance Logging** - Persistent SQLite database with check-in/check-out timestamps  
✅ **Privacy-First** - Camera feed automatically scrubbed on logout, camera stop, or server restart  

## Hardware Requirements

- **ESP32-AI-Thinker** with OV2640 camera and PSRAM
- **USB Cable** for programming
- **WiFi Network** for connectivity

## Software Stack

- **Backend**: FastAPI 0.128.0 with Uvicorn
- **Database**: SQLite with SQLAlchemy ORM
- **Frontend**: HTML5, CSS3, JavaScript (Vanilla)
- **Camera**: Official Espressif camera library with PSRAM optimization

## Project Structure

```
qr 點名/
├── app/
│   ├── __init__.py
│   ├── main.py           # FastAPI backend, endpoints, session management
│   ├── auth.py           # User authentication
│   ├── database.py       # SQLAlchemy setup
│   ├── models.py         # Database models (User, Attendance, QRCode)
│   ├── qr.py             # QR code generation logic
│   └── scan.py           # QR code scanning and processing
├── templates/
│   ├── setup.html        # Initial admin setup page
│   ├── login.html        # Login page
│   ├── admin.html        # Admin dashboard with camera control
│   ├── admin_register.html # Client registration
│   ├── client.html       # Client QR code portal
│   └── index.html        # Fallback page
├── static/
│   └── style.css         # Global styles
├── esp32_qr_scanner_v3.ino  # ESP32 firmware
├── attendance.db         # SQLite database (auto-created)
├── requirements.txt      # Python dependencies
└── README.md             # This file
```

## Quick Start

### 1. Install Python Dependencies

```bash
cd "c:\Users\fitio\Desktop\qr 點名"
python -m venv absen
absen\Scripts\activate
pip install -r requirements.txt
```

### 2. Initialize Database and Start Server

```bash
python -m uvicorn app.main:app --reload --host 0.0.0.0
```

Server runs on: `http://0.0.0.0:8000`

### 3. Setup Admin User

1. Open browser: `http://localhost:8000`
2. Create admin account (auto-directed to setup page)
3. Login with admin credentials

### 4. Configure ESP32 Firmware

1. Open `esp32_qr_scanner_v3.ino` in Arduino IDE
2. Select Board: **ESP32 Dev Module**
3. Configure WiFi credentials:
   ```cpp
   const char* ssid = "your_ssid";
   const char* password = "your_password";
   const char* serverIP = "your_server_ip";  // e.g., 10.21.55.146
   ```
4. Upload to ESP32

### 5. Register Client Users

1. Login as admin
2. Click **"➕ Register New Client"**
3. Create client accounts

## API Endpoints

### Authentication
- `GET /` - Root redirect (auth required)
- `GET /setup` - Admin setup page
- `POST /setup` - Create initial admin
- `GET /login` - Login page
- `POST /login` - Authenticate user
- `GET /logout` - Logout and scrub camera

### Admin Routes
- `GET /admin` - Admin dashboard
- `GET /admin/clients` - List all client users
- `GET /admin/attendance` - Get last 20 attendance records
- `POST /admin/manual-attendance` - Record check-in/check-out manually
- `GET /admin/register` - Client registration page
- `POST /admin/register` - Register new client user

### Client Routes
- `GET /client` - Client QR code portal
- `GET /client/check-status` - Check if client already checked in (returns `{"checked_in": bool}`)
- `POST /generate_qr` - Generate new QR code
- `GET /generate_qr` - Generate QR code (GET fallback)

### ESP32 Integration
- `GET /esp32/info` - Server connection info for ESP32
- `GET /esp32/status` - Check if camera should be active (polling endpoint)
- `POST /esp32/activate` - Enable camera (admin only)
- `POST /esp32/deactivate` - Disable camera (scrubs frame)
- `POST /esp32/upload` - Upload frame + scan QR code
- `GET /esp32/stream` - Get latest camera frame (live preview)

## Database Schema

### Users
```sql
CREATE TABLE user (
    id INTEGER PRIMARY KEY,
    username VARCHAR UNIQUE NOT NULL,
    password_hash VARCHAR NOT NULL,
    role VARCHAR NOT NULL  -- "admin" or "client"
);
```

### Attendance
```sql
CREATE TABLE attendance (
    id INTEGER PRIMARY KEY,
    employee_id INTEGER NOT NULL,
    status VARCHAR NOT NULL,  -- "present", "absent", "checked_out"
    reason VARCHAR,
    check_in DATETIME,
    check_out DATETIME,
    scan_time DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

### QR Codes
```sql
CREATE TABLE qrcode (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL,
    qr_path VARCHAR NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    expires_at DATETIME
);
```

## Session Management

- **Max Age**: 15 minutes (900 seconds)
- **Restart Invalidation**: Uses `server_generation` ID to invalidate all sessions on server restart
- **Auto-Logout**: All users logged out and redirected to login after server restart
- **Camera Scrub**: Frame deleted on logout, camera stop, or server restart

## ESP32 Configuration

### Frame Capture Settings
- **Resolution**: QVGA (320×240) with PSRAM, QQVGA (160×120) without
- **Quality**: 10 (with PSRAM), 8 (without)
- **Frame Rate**: 5 FPS (200ms interval)
- **Status Poll**: Every 5 seconds

### WiFi Setup
Update in `esp32_qr_scanner_v3.ino`:
```cpp
const char* ssid = "tio";
const char* password = "12345678";
const char* serverIP = "10.21.55.146";
```

## Troubleshooting

### ESP32 Not Connecting
1. Verify WiFi SSID and password in firmware
2. Check server is running: `http://server_ip:8000/esp32/info`
3. Ensure ESP32 and server are on same network
4. Check serial monitor for WiFi connection errors

### QR Code Not Scanning
1. Ensure ESP32 is activated in admin dashboard
2. Check camera feed displays live video
3. Verify QR code is well-lit and in focus
4. Test with test QR codes (simple, high contrast)

### Camera Feed Freezing
1. Check server CPU/memory usage
2. Restart ESP32 by power cycle
3. Reduce frame rate in firmware (FRAME_INTERVAL)

### Session Keeps Timing Out
- Timeout is 15 minutes of inactivity
- Reset timer by making any request to server
- Logout and login to refresh session

## File Descriptions

| File | Purpose |
|------|---------|
| `app/main.py` | FastAPI server, all endpoints, session management |
| `app/auth.py` | Password hashing and user authentication |
| `app/database.py` | SQLAlchemy engine and session configuration |
| `app/models.py` | SQLAlchemy ORM models |
| `app/qr.py` | QR code generation and file management |
| `app/scan.py` | QR code detection and attendance recording |
| `templates/admin.html` | Admin dashboard with ESP32 control |
| `templates/client.html` | Client check-in/check-out portal |
| `esp32_qr_scanner_v3.ino` | ESP32 firmware with PSRAM optimization |

## Security Notes

- ⚠️ Change `secret_key` in `app/main.py` SessionMiddleware for production
- ⚠️ Use HTTPS in production environments
- ⚠️ Store WiFi credentials securely in ESP32 (consider firmware encryption)
- ✅ Passwords hashed with bcrypt
- ✅ Session timeout enforced (15 minutes)
- ✅ Camera feed scrubbed on logout

## Development

### Run with Auto-Reload
```bash
python -m uvicorn app.main:app --reload --host 0.0.0.0
```

### Reset Database
```bash
del attendance.db
# Server will auto-create new database on next run
```

### Clear QR Code Cache
```bash
del static\qr_*.png
```

## Dependencies

See [requirements.txt](requirements.txt) for full list:
- fastapi==0.128.0
- uvicorn==0.40.0
- sqlalchemy==2.0.46
- pydantic==2.12.5
- opencv-python==4.13.0.90
- qrcode==8.2
- pillow==12.1.0
- passlib==1.7.4
- bcrypt==3.2.2
- starlette==0.50.0
- python-multipart==0.0.22

## License

Private project for internal use.

## Support

For issues or questions:
1. Check troubleshooting section
2. Review terminal output for error messages
3. Check server logs at startup
4. Verify ESP32 is properly powered and connected
