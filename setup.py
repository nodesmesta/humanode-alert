import os
import json
import subprocess

CONFIG_FILE = "config.json"

def create_config():
    if os.path.exists(CONFIG_FILE):
        print("config.json sudah ada.")
        with open(CONFIG_FILE) as f:
            existing_config = json.load(f)
            print(f"Nodename saat ini: {existing_config.get('nodename', '(tidak diatur)')}")
            change = input("Ingin mengubah nodename? (y/n): ").strip().lower()
            if change == "y":
                nodename = input("Masukkan nodename baru: ").strip()
                existing_config["nodename"] = nodename
                with open(CONFIG_FILE, "w") as f:
                    json.dump(existing_config, f, indent=4)
                print(f"Nodename berhasil diubah menjadi: {nodename}")
            return
    
    print("=== Konfigurasi Baru ===")
    token = input("Masukkan token bot Telegram Anda: ").strip()
    chat_id = input("Masukkan chat ID grup atau pengguna Telegram Anda: ").strip()
    username = input("Masukkan username Telegram Anda (tanpa @): ").strip()
    nodename = input("Masukkan nodename untuk node Anda: ").strip()

    config = {
        "telegram_token": token,
        "telegram_chat_id": chat_id,
        "username": username,
        "nodename": nodename
    }

    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=4)
    print("config.json berhasil dibuat.")

def create_systemd_service():
    service_content = f"""
[Unit]
Description=Checker Service
After=network.target

[Service]
Type=simple
ExecStart=/usr/bin/python3 {os.path.abspath("checker.py")}
WorkingDirectory={os.getcwd()}
Restart=always
User={os.environ.get("USER", "root")}

[Install]
WantedBy=multi-user.target
"""
    service_file = "/etc/systemd/system/checker.service"

    with open("checker.service", "w") as f:
        f.write(service_content)

    subprocess.run(["sudo", "mv", "checker.service", service_file], check=True)
    subprocess.run(["sudo", "systemctl", "daemon-reload"], check=True)
    subprocess.run(["sudo", "systemctl", "enable", "checker.service"], check=True)
    subprocess.run(["sudo", "systemctl", "start", "checker.service"], check=True)
    print("Service checker berhasil dibuat dan dijalankan.")

if __name__ == "__main__":
    create_config()
    create_systemd_service()
    print("Setup selesai.")
