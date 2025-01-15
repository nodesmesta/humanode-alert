import os
import requests
import json
import time
import subprocess
import logging

# Konfigurasi logging
logging.basicConfig(
    filename="checker.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

# File konfigurasi
CONFIG_FILE = "config.json"
WORKSPACE_FILE = os.path.expanduser("~/.humanode/workspaces/default/workspace.json")

if not os.path.exists(CONFIG_FILE):
    raise FileNotFoundError("config.json tidak ditemukan. Jalankan setup.py terlebih dahulu.")
if not os.path.exists(WORKSPACE_FILE):
    raise FileNotFoundError(f"workspace.json tidak ditemukan di {WORKSPACE_FILE}.")

# Muat konfigurasi
with open(CONFIG_FILE) as f:
    config = json.load(f)

telegram_token = config["telegram_token"]
telegram_chat_id = config["telegram_chat_id"]
username = config["username"]
nodename = config.get("nodename", "Tidak diatur")

telegram_api_url = f"https://api.telegram.org/bot{telegram_token}/sendMessage"

# Muat data dari workspace.json
with open(WORKSPACE_FILE) as f:
    workspace_data = json.load(f)

rpc_url_mode = workspace_data.get("rpcUrlMode", {}).get("type", "")
ngrok_path = workspace_data.get("ngrokPath", "ngrok-wrapper")

# Fungsi untuk mendeteksi URL RPC
def get_rpc_url():
    if rpc_url_mode == "ngrok-auto-detect":
        try:
            result = subprocess.check_output([ngrok_path, "urls", "http"], text=True)
            url = result.strip()
            logging.info(f"RPC URL ditemukan: {url}")
            return url
        except subprocess.CalledProcessError as e:
            logging.error(f"Gagal mendeteksi RPC URL: {e}")
            return None
    else:
        logging.warning("RPC URL tidak ditemukan secara otomatis.")
        return None

rpc_url = get_rpc_url()
if not rpc_url:
    raise RuntimeError("Tidak dapat mendeteksi RPC URL. Pastikan ngrok berjalan atau periksa konfigurasi.")

status_payload = {
    "jsonrpc": "2.0",
    "method": "bioauth_status",
    "params": [],
    "id": 1,
}

# Fungsi untuk mengirim pesan ke Telegram
def send_telegram_message(message):
    try:
        full_message = f"Node: <b>{nodename}</b>\n{message}"
        response = requests.post(
            telegram_api_url,
            json={"chat_id": telegram_chat_id, "text": full_message, "parse_mode": "HTML"},
        )
        if response.status_code == 200:
            logging.info("Notifikasi berhasil dikirim ke Telegram.")
        else:
            logging.error(
                f"Gagal mengirim notifikasi ke Telegram: {response.status_code}, {response.text}"
            )
    except Exception as e:
        logging.error(f"Kesalahan saat mengirim pesan Telegram: {e}")

# Fungsi untuk memeriksa status bioauth
def check_bioauth():
    try:
        response = requests.post(
            rpc_url, json=status_payload, timeout=10
        )
        if response.status_code == 200:
            result = response.json().get("result", {})
            if "Active" in result:
                expires_at = result["Active"]["expires_at"]
                expires_in = int((expires_at / 1000) - time.time())

                # Format waktu kedaluwarsa
                hours, remainder = divmod(expires_in, 3600)
                minutes, seconds = divmod(remainder, 60)
                formatted_time = f"{hours} jam, {minutes} menit, {seconds} detik"

                # Kirim notifikasi jika waktu hampir habis
                if expires_in < 3600:
                    send_telegram_message(
                        f"⚠️ @{username}, sesi bioauth Anda akan kedaluwarsa dalam <b>{formatted_time}</b>."
                    )
                logging.info(f"Sesi bioauth akan kedaluwarsa dalam {formatted_time}.")
            else:
                logging.warning("Sesi bioauth tidak aktif.")
        else:
            logging.error(f"Kesalahan RPC: {response.status_code}, {response.text}")
            send_telegram_message(f"❌ @{username}, terjadi kesalahan RPC saat memeriksa status bioauth.")
    except requests.exceptions.RequestException as e:
        logging.error(f"Kesalahan saat memeriksa bioauth: {e}")
        send_telegram_message(
            f"❌ @{username}, tidak dapat menghubungi server RPC. Harap periksa koneksi atau status server."
        )

# Fungsi utama
if __name__ == "__main__":
    logging.info(f"Memulai pengecekan bioauth untuk Node: {nodename}.")
    while True:
        check_bioauth()
        time.sleep(60)
