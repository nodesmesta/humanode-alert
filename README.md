# Humanode Alert

<p align="center">
  <img src="logo/NodeSemesta.png" alt="Humanode Alert Logo" width="200">
</p>

---

**Humanode Alert** adalah sistem yang memonitor status autentikasi node Humanode Anda dan mengirimkan notifikasi ke Telegram. Aplikasi ini menggunakan Python dan diatur menggunakan systemd untuk berjalan secara otomatis di latar belakang.

## Fitur Utama
- Mengirimkan notifikasi awal bahwa node Anda adalah validator.
- Mengingatkan Anda sebelum autentikasi kadaluarsa.
- Memberitahukan jika autentikasi telah kadaluarsa.

## Persyaratan
Sebelum memulai, pastikan sistem Anda memiliki:
- **Python 3.7+**
- **Git**
- **Access ke Telegram Bot API** (dapatkan token bot dari BotFather).

## Instalasi
Ikuti langkah-langkah berikut untuk menginstal Humanode Alert:

### 1. Clone Repositori
```bash
# Clone repositori ini
$ git clone https://github.com/nodesmesta/humanode-alert.git

# Masuk ke direktori project
$ cd humanode-alert
```

### 2. Jalankan Setup
Setup script akan:
- Menginstal dependensi yang diperlukan.
- Membuat file konfigurasi untuk Telegram.
- Membuat dan mengaktifkan service systemd.

```bash
$ python3 setup.py
```

### 3. Konfigurasi Telegram
Selama proses setup, Anda akan diminta untuk:
- **Token Bot Telegram**: Masukkan token bot Anda dari BotFather.
- **Chat ID**: ID grup atau pengguna Telegram tempat notifikasi akan dikirim.
- **Username**: Username Telegram Anda (tanpa `@`).

File konfigurasi akan disimpan sebagai `config.json` di direktori project.

### 4. Periksa Status Service
Pastikan service berjalan dengan benar:
```bash
$ sudo systemctl status auth_checker.service
```

Jika service berjalan, Anda akan melihat output seperti:
```
● auth_checker.service - Auth Checker Service
     Loaded: loaded (/etc/systemd/system/auth_checker.service; enabled; vendor preset: enabled)
     Active: active (running) since [timestamp]
```

### 5. Logs
Untuk memeriksa log output:
```bash
$ sudo journalctl -u auth_checker.service -f
```

## Struktur Proyek
```
.
├── checker.py       # Script utama untuk memantau status autentikasi
├── config.json      # File konfigurasi (dibuat saat setup)
├── setup.py         # Script instalasi dan konfigurasi systemd
└── README.md        # Dokumentasi
```

## Catatan Penting
- **Lokasi Checker**: Script `checker.py` secara otomatis diarahkan ke lokasi yang benar oleh `setup.py`. Anda tidak perlu mengedit path secara manual.
- **Pembaruan Link Autentikasi**: Jika link autentikasi berubah, `checker.py` secara otomatis mencoba mendapatkan link terbaru.

## Kontribusi
Kami menyambut kontribusi untuk meningkatkan Humanode Alert. Silakan fork repositori ini dan kirimkan pull request Anda.

## Lisensi
Proyek ini dilisensikan di bawah [MIT License](LICENSE).

---

Nikmati pengalaman memantau node Humanode Anda dengan Humanode Alert!

