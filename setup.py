import os
import json
import subprocess
import sys

# Nama file konfigurasi dan service
CONFIG_FILE = "config.json"
CHECKER_SCRIPT = os.path.join(os.environ.get("HOME", "/root"), "humanode-alert", "checker.py")
SERVICE_FILE = "/etc/systemd/system/auth_checker.service"

# Fungsi untuk menginstal pustaka Python yang dibutuhkan
def install_dependencies():
    print("Menginstal pustaka Python yang diperlukan...")
    required_packages = ["requests"]
    try:
        installed_packages = subprocess.check_output([sys.executable, "-m", "pip", "freeze"], text=True)
        installed_packages = [pkg.split("==")[0] for pkg in installed_packages.splitlines()]

        packages_to_install = [pkg for pkg in required_packages if pkg not in installed_packages]
        if packages_to_install:
            subprocess.check_call([sys.executable, "-m", "pip", "install", *packages_to_install])
            print("Pustaka berhasil diinstal!")
        else:
            print("Semua pustaka sudah terinstal.")
    except subprocess.CalledProcessError as e:
        print(f"Gagal menginstal pustaka Python: {e}")

# Fungsi untuk membuat file konfigurasi
def create_config():
    if os.path.exists(CONFIG_FILE):
        print("Konfigurasi sudah ada. Menggunakan konfigurasi yang ada.")
        return

    print("\n=== Konfigurasi Telegram Bot ===")
    token = input("Masukkan token bot Telegram Anda: ").strip()
    chat_id = input("Masukkan chat ID grup atau pengguna Telegram Anda: ").strip()
    username = input("Masukkan username Telegram Anda (tanpa @): ").strip()

    # Menyimpan konfigurasi
    config = {
        "telegram_token": token,
        "telegram_chat_id": chat_id,
        "username": username
    }
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=4)

    print("\nKonfigurasi berhasil dibuat!")
    print(f"File konfigurasi disimpan di: {os.path.abspath(CONFIG_FILE)}")

# Fungsi untuk membuat service systemd
def create_systemd_service():
    service_content = f"""
[Unit]
Description=Auth Checker Service
After=network.target

[Service]
Type=simple
ExecStart=/usr/bin/python3 {CHECKER_SCRIPT}
WorkingDirectory={os.path.dirname(CHECKER_SCRIPT)}
Restart=always
User={os.environ.get("USER", "root")}

[Install]
WantedBy=multi-user.target
"""
    try:
        with open("auth_checker.service", "w") as f:
            f.write(service_content)

        # Pindahkan service file ke /etc/systemd/system
        subprocess.run(["sudo", "mv", "auth_checker.service", SERVICE_FILE], check=True)
        subprocess.run(["sudo", "systemctl", "daemon-reload"], check=True)
        subprocess.run(["sudo", "systemctl", "enable", "auth_checker.service"], check=True)
        subprocess.run(["sudo", "systemctl", "start", "auth_checker.service"], check=True)

        print("\nService berhasil dibuat dan dijalankan di latar belakang!")
    except subprocess.CalledProcessError as e:
        print(f"Gagal membuat service systemd: {e}")

# Fungsi untuk membersihkan file sementara di /tmp
def clean_tmp_files():
    tmp_files = ["/tmp/initial_notify_done"]
    for file in tmp_files:
        if os.path.exists(file):
            os.remove(file)
            print(f"File sementara {file} berhasil dihapus.")

# Menjalankan proses instalasi
if __name__ == "__main__":
    print("=== Instalasi Aplikasi Autentikasi Node ===")
    clean_tmp_files()
    install_dependencies()
    create_config()
    create_systemd_service()
    print("\nInstalasi selesai. Anda dapat memeriksa status service dengan perintah:")
    print("sudo systemctl status auth_checker.service")
