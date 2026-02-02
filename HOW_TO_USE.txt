================================================================================
QR ATTENDANCE SYSTEM - HOW TO USE
================================================================================

ENGLISH VERSION
===============

TABLE OF CONTENTS
1. System Requirements
2. Installation & Setup
3. Starting the Application
4. First Time Setup
5. Admin Features
6. Client Features
7. Common Tasks
8. Troubleshooting

---

1. SYSTEM REQUIREMENTS
- Python 3.8 or higher
- Webcam or smartphone camera (for scanning QR codes)
- Web browser (Chrome, Firefox, Edge, Safari)
- Internet connection (localhost only)

---

2. INSTALLATION & SETUP

Step 1: Navigate to Project Directory
   Open PowerShell/Command Prompt and go to:
   cd C:\Users\fitio\Desktop\qr 點名

Step 2: Activate Virtual Environment
   .\absen\Scripts\Activate.ps1
   (You should see (absen) at the start of the terminal line)

Step 3: Install Dependencies (if not already installed)
   pip install -r requirements.txt

---

3. STARTING THE APPLICATION

Run the application:
   python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

You'll see output like:
   INFO:     Uvicorn running on http://127.0.0.1:8000
   INFO:     Application startup complete

Open your browser and go to: http://localhost:8000

---

4. FIRST TIME SETUP

When you first run the app:
   - You'll be automatically redirected to /setup page
   - Create the first ADMIN account
   - Enter Username and Password
   - Click "Create Admin Account"
   - You'll be redirected to login page

Now the system is ready to use!

---

5. ADMIN FEATURES

Admin Dashboard (/admin):
   - View QR scanning interface
   - Upload QR code images to record attendance
   - Register new client accounts
   - Logout button

How to Register a New Client:
   1. Click "Register New Client" button
   2. Enter client username and password
   3. Click "Register Client"
   4. Client account is created and ready to use

How to Scan Attendance:
   1. Ask client to show their QR code
   2. Take a photo of the QR code with your phone/camera
   3. On the admin dashboard, click "Choose File"
   4. Select the QR code image
   5. Click "Scan QR Code"
   6. System shows: ✓ Success: Attendance recorded (if valid)
   7. Or: ✗ Failed: QR expired/invalid/already used

Important: QR codes expire after 1 minute and can only be used once

---

6. CLIENT FEATURES

Client Dashboard (/client):
   - View their unique QR code
   - Generate new QR code
   - Logout button

How to Use as Client:
   1. Log in with your username and password
   2. Your QR code is automatically generated
   3. Show this QR code to the admin to record your attendance
   4. Code is valid for 1 minute
   5. If expired, click "Generate New QR Code" for a new one

---

7. COMMON TASKS

Task: Reset Forgotten Password
   - Only admin can create new accounts
   - Contact admin to reset your password

Task: Change Login Password
   - Currently not available in system
   - Contact admin if you need password change

Task: View Attendance Records
   - Data is stored in attendance.db (SQLite database)
   - Can be accessed using DB Browser for SQLite

Task: Restart the System
   - Press Ctrl+C in terminal to stop the app
   - Run python -m uvicorn app.main:app --reload again

---

8. TROUBLESHOOTING

Error: "ModuleNotFoundError: No module named 'fastapi'"
   Solution: Run: pip install -r requirements.txt

Error: "Address already in use"
   Solution: Change port number: --port 8001 instead of 8000

Error: "QR code not detected"
   Solution:
   - Make sure image is clear and well-lit
   - QR code should be visible and not blurry
   - Try a different angle

Error: "QR expired"
   Solution: Client needs to generate a new QR code (valid for 1 minute only)

Error: Database locked
   Solution: Restart the application (Ctrl+C and run again)

Keyboard Shortcut: Ctrl+C to stop the application

================================================================================

INDONESIAN VERSION (VERSI BAHASA INDONESIA)
===========================================

DAFTAR ISI
1. Persyaratan Sistem
2. Instalasi & Penyiapan
3. Memulai Aplikasi
4. Penyiapan Pertama Kali
5. Fitur Admin
6. Fitur Client
7. Tugas Umum
8. Troubleshooting

---

1. PERSYARATAN SISTEM
- Python 3.8 atau lebih tinggi
- Webcam atau kamera smartphone (untuk pemindaian kode QR)
- Browser web (Chrome, Firefox, Edge, Safari)
- Koneksi internet (localhost saja)

---

2. INSTALASI & PENYIAPAN

Langkah 1: Navigasi ke Direktori Proyek
   Buka PowerShell/Command Prompt dan pergi ke:
   cd C:\Users\fitio\Desktop\qr 點名

Langkah 2: Aktifkan Virtual Environment
   .\absen\Scripts\Activate.ps1
   (Anda akan melihat (absen) di awal baris terminal)

Langkah 3: Instal Dependensi (jika belum terinstal)
   pip install -r requirements.txt

---

3. MEMULAI APLIKASI

Jalankan aplikasi:
   python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

Anda akan melihat output seperti:
   INFO:     Uvicorn running on http://127.0.0.1:8000
   INFO:     Application startup complete

Buka browser Anda dan pergi ke: http://localhost:8000

---

4. PENYIAPAN PERTAMA KALI

Saat Anda pertama kali menjalankan aplikasi:
   - Anda akan secara otomatis dialihkan ke halaman /setup
   - Buat akun ADMIN pertama
   - Masukkan Nama Pengguna dan Kata Sandi
   - Klik "Create Admin Account"
   - Anda akan dialihkan ke halaman login

Sekarang sistem siap digunakan!

---

5. FITUR ADMIN

Dashboard Admin (/admin):
   - Lihat antarmuka pemindaian QR
   - Unggah gambar kode QR untuk mencatat kehadiran
   - Daftarkan akun klien baru
   - Tombol Logout

Cara Mendaftarkan Klien Baru:
   1. Klik tombol "Register New Client"
   2. Masukkan nama pengguna dan kata sandi klien
   3. Klik "Register Client"
   4. Akun klien dibuat dan siap digunakan

Cara Memindai Kehadiran:
   1. Minta klien menunjukkan kode QR mereka
   2. Ambil foto kode QR dengan ponsel/kamera Anda
   3. Di dashboard admin, klik "Choose File"
   4. Pilih gambar kode QR
   5. Klik "Scan QR Code"
   6. Sistem menampilkan: ✓ Success: Attendance recorded (jika valid)
   7. Atau: ✗ Failed: QR expired/invalid/already used

Penting: Kode QR berlaku selama 1 menit dan hanya dapat digunakan sekali

---

6. FITUR CLIENT

Dashboard Client (/client):
   - Lihat kode QR unik mereka
   - Hasilkan kode QR baru
   - Tombol Logout

Cara Menggunakan sebagai Client:
   1. Login dengan nama pengguna dan kata sandi Anda
   2. Kode QR Anda secara otomatis dihasilkan
   3. Tunjukkan kode QR ini kepada admin untuk mencatat kehadiran Anda
   4. Kode berlaku selama 1 menit
   5. Jika sudah kadaluarsa, klik "Generate New QR Code" untuk mendapatkan yang baru

---

7. TUGAS UMUM

Tugas: Mengatur Ulang Kata Sandi yang Terlupakan
   - Hanya admin yang dapat membuat akun baru
   - Hubungi admin jika Anda lupa kata sandi

Tugas: Ubah Kata Sandi Login
   - Saat ini tidak tersedia di sistem
   - Hubungi admin jika Anda perlu mengubah kata sandi

Tugas: Lihat Catatan Kehadiran
   - Data disimpan di attendance.db (database SQLite)
   - Dapat diakses menggunakan DB Browser untuk SQLite

Tugas: Restart Sistem
   - Tekan Ctrl+C di terminal untuk menghentikan aplikasi
   - Jalankan python -m uvicorn app.main:app --reload lagi

---

8. TROUBLESHOOTING

Kesalahan: "ModuleNotFoundError: No module named 'fastapi'"
   Solusi: Jalankan: pip install -r requirements.txt

Kesalahan: "Address already in use"
   Solusi: Ubah nomor port: --port 8001 bukan 8000

Kesalahan: "QR code not detected"
   Solusi:
   - Pastikan gambar jelas dan cahaya cukup
   - Kode QR harus terlihat dan tidak buram
   - Coba sudut berbeda

Kesalahan: "QR expired"
   Solusi: Klien perlu membuat kode QR baru (berlaku hanya 1 menit)

Kesalahan: Database locked
   Solusi: Restart aplikasi (Ctrl+C dan jalankan lagi)

Shortcut Keyboard: Ctrl+C untuk menghentikan aplikasi

================================================================================
END OF DOCUMENT
================================================================================
