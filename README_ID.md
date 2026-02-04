# Sistem Kehadiran Kode QR

Sistem pelacakan kehadiran modern dan real-time menggunakan kode QR dan modul ESP32-CAM. Mendukung check-in/check-out, feed kamera langsung, dan antarmuka web yang responsif.

## Fitur

✅ **Pembuatan Kode QR** - Kode QR dinamis dengan masa berlaku 60 detik  
✅ **Sistem Check-In/Check-Out** - Melacak kehadiran harian dengan kode QR dua mode  
✅ **Feed Kamera ESP32 Langsung** - Video real-time dari ESP32-CAM dengan 5 FPS yang dioptimalkan  
✅ **Dashboard Admin** - Kelola klien, lihat log kehadiran, dukungan entri manual  
✅ **Portal Klien** - Buat dan pindai kode QR dengan antarmuka yang sadar status  
✅ **Manajemen Sesi** - Timeout 15 menit dengan invalidasi otomatis saat server restart  
✅ **Responsif Seluler** - Berfungsi penuh di ponsel, tablet, dan desktop  
✅ **Pencatatan Kehadiran** - Database SQLite persisten dengan stempel waktu check-in/check-out  
✅ **Prioritas Privasi** - Feed kamera secara otomatis dihapus saat logout, kamera berhenti, atau server restart  

## Persyaratan Perangkat Keras

- **ESP32-AI-Thinker** dengan kamera OV2640 dan PSRAM
- **Kabel USB** untuk pemrograman
- **Jaringan WiFi** untuk konektivitas

## Stack Perangkat Lunak

- **Backend**: FastAPI 0.128.0 dengan Uvicorn
- **Database**: SQLite dengan SQLAlchemy ORM
- **Frontend**: HTML5, CSS3, JavaScript (Vanilla)
- **Kamera**: Perpustakaan kamera resmi Espressif dengan optimasi PSRAM

## Struktur Proyek

```
qr 點名/
├── app/
│   ├── __init__.py
│   ├── main.py           # Backend FastAPI, endpoint, manajemen sesi
│   ├── auth.py           # Autentikasi pengguna
│   ├── database.py       # Setup SQLAlchemy
│   ├── models.py         # Model database (User, Attendance, QRCode)
│   ├── qr.py             # Logika pembuatan kode QR
│   └── scan.py           # Pemindaian dan pemrosesan kode QR
├── templates/
│   ├── setup.html        # Halaman setup admin awal
│   ├── login.html        # Halaman login
│   ├── admin.html        # Dashboard admin dengan kontrol kamera
│   ├── admin_register.html # Pendaftaran klien
│   ├── client.html       # Portal check-in/check-out klien
│   └── index.html        # Halaman fallback
├── static/
│   └── style.css         # Gaya global
├── esp32_qr_scanner_v3.ino  # Firmware ESP32
├── attendance.db         # Database SQLite (dibuat otomatis)
├── requirements.txt      # Dependensi Python
└── README.md             # File ini
```

## Memulai Cepat

### 1. Instal Dependensi Python

```bash
cd "c:\Users\fitio\Desktop\qr 點名"
python -m venv absen
absen\Scripts\activate
pip install -r requirements.txt
```

### 2. Inisialisasi Database dan Mulai Server

```bash
python -m uvicorn app.main:app --reload --host 0.0.0.0
```

Server berjalan di: `http://0.0.0.0:8000`

### 3. Setup Pengguna Admin

1. Buka browser: `http://localhost:8000`
2. Buat akun admin (otomatis diarahkan ke halaman setup)
3. Login dengan kredensial admin

### 4. Konfigurasi Firmware ESP32

1. Buka `esp32_qr_scanner_v3.ino` di Arduino IDE
2. Pilih Board: **ESP32 Dev Module**
3. Konfigurasi kredensial WiFi:
   ```cpp
   const char* ssid = "ssid_anda";
   const char* password = "password_anda";
   const char* serverIP = "ip_server_anda";  // misal, 10.21.55.146
   ```
4. Upload ke ESP32

### 5. Daftarkan Pengguna Klien

1. Login sebagai admin
2. Klik **"➕ Register New Client"**
3. Buat akun klien

## Endpoint API

### Autentikasi
- `GET /` - Redirect root (auth diperlukan)
- `GET /setup` - Halaman setup admin
- `POST /setup` - Buat admin awal
- `GET /login` - Halaman login
- `POST /login` - Autentikasi pengguna
- `GET /logout` - Logout dan hapus kamera

### Rute Admin
- `GET /admin` - Dashboard admin
- `GET /admin/clients` - Daftar semua pengguna klien
- `GET /admin/attendance` - Dapatkan 20 catatan kehadiran terakhir
- `POST /admin/manual-attendance` - Catat check-in/check-out secara manual
- `GET /admin/register` - Halaman pendaftaran klien
- `POST /admin/register` - Daftarkan pengguna klien baru

### Rute Klien
- `GET /client` - Portal kode QR klien
- `GET /client/check-status` - Periksa apakah klien sudah check-in (mengembalikan `{"checked_in": bool}`)
- `POST /generate_qr` - Buat kode QR baru
- `GET /generate_qr` - Buat kode QR (fallback GET)

### Integrasi ESP32
- `GET /esp32/info` - Info koneksi server untuk ESP32
- `GET /esp32/status` - Periksa apakah kamera harus aktif (polling endpoint)
- `POST /esp32/activate` - Aktifkan kamera (hanya admin)
- `POST /esp32/deactivate` - Nonaktifkan kamera (hapus frame)
- `POST /esp32/upload` - Upload frame + pindai kode QR
- `GET /esp32/stream` - Dapatkan frame kamera terbaru (preview langsung)

## Skema Database

### Pengguna
```sql
CREATE TABLE user (
    id INTEGER PRIMARY KEY,
    username VARCHAR UNIQUE NOT NULL,
    password_hash VARCHAR NOT NULL,
    role VARCHAR NOT NULL  -- "admin" atau "client"
);
```

### Kehadiran
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

### Kode QR
```sql
CREATE TABLE qrcode (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL,
    qr_path VARCHAR NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    expires_at DATETIME
);
```

## Manajemen Sesi

- **Usia Maksimum**: 15 menit (900 detik)
- **Invalidasi Restart**: Menggunakan ID `server_generation` untuk invalidasi semua sesi saat server restart
- **Auto-Logout**: Semua pengguna logout dan dialihkan ke login setelah restart server
- **Hapus Kamera**: Frame dihapus saat logout, kamera berhenti, atau server restart

## Konfigurasi ESP32

### Pengaturan Pengambilan Frame
- **Resolusi**: QVGA (320×240) dengan PSRAM, QQVGA (160×120) tanpa
- **Kualitas**: 10 (dengan PSRAM), 8 (tanpa)
- **Frame Rate**: 5 FPS (interval 200ms)
- **Poll Status**: Setiap 5 detik

### Setup WiFi
Perbarui di `esp32_qr_scanner_v3.ino`:
```cpp
const char* ssid = "tio";
const char* password = "12345678";
const char* serverIP = "10.21.55.146";
```

## Pemecahan Masalah

### ESP32 Tidak Terhubung
1. Verifikasi SSID dan password WiFi di firmware
2. Periksa server berjalan: `http://server_ip:8000/esp32/info`
3. Pastikan ESP32 dan server berada di jaringan yang sama
4. Periksa monitor serial untuk kesalahan koneksi WiFi

### Kode QR Tidak Terpindai
1. Pastikan ESP32 diaktifkan di dashboard admin
2. Periksa feed kamera menampilkan video langsung
3. Verifikasi kode QR terbuka dengan baik dan fokus
4. Uji dengan kode QR uji (sederhana, kontras tinggi)

### Feed Kamera Macet
1. Periksa penggunaan CPU/memori server
2. Restart ESP32 dengan siklus daya
3. Kurangi frame rate di firmware (FRAME_INTERVAL)

### Sesi Terus Habis Waktu
- Timeout adalah 15 menit tanpa aktivitas
- Reset timer dengan membuat permintaan apa pun ke server
- Logout dan login untuk menyegarkan sesi

## Deskripsi File

| File | Tujuan |
|------|--------|
| `app/main.py` | Server FastAPI, semua endpoint, manajemen sesi |
| `app/auth.py` | Hashing password dan autentikasi pengguna |
| `app/database.py` | Konfigurasi mesin SQLAlchemy |
| `app/models.py` | Model ORM SQLAlchemy |
| `app/qr.py` | Pembuatan kode QR dan manajemen file |
| `app/scan.py` | Deteksi kode QR dan pencatatan kehadiran |
| `templates/admin.html` | Dashboard admin dengan kontrol ESP32 |
| `templates/client.html` | Portal check-in/check-out klien |
| `esp32_qr_scanner_v3.ino` | Firmware ESP32 dengan optimasi PSRAM |

## Catatan Keamanan

- ⚠️ Ubah `secret_key` di SessionMiddleware `app/main.py` untuk produksi
- ⚠️ Gunakan HTTPS di lingkungan produksi
- ⚠️ Simpan kredensial WiFi dengan aman di ESP32 (pertimbangkan enkripsi firmware)
- ✅ Password di-hash dengan bcrypt
- ✅ Timeout sesi diterapkan (15 menit)
- ✅ Feed kamera dihapus saat logout

## Pengembangan

### Jalankan dengan Auto-Reload
```bash
python -m uvicorn app.main:app --reload --host 0.0.0.0
```

### Reset Database
```bash
del attendance.db
# Server akan otomatis membuat database baru pada jalankan berikutnya
```

### Hapus Cache Kode QR
```bash
del static\qr_*.png
```

## Dependensi

Lihat [requirements.txt](requirements.txt) untuk daftar lengkap:
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

## Lisensi

Proyek pribadi untuk penggunaan internal.

## Dukungan

Untuk pertanyaan atau masalah:
1. Periksa bagian pemecahan masalah
2. Tinjau output terminal untuk pesan kesalahan
3. Periksa log server saat startup
4. Verifikasi ESP32 bertenaga dan terhubung dengan baik
