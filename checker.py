import os
import requests
import datetime
import subprocess
import time
import json

# Direktori kerja dinamis berdasarkan variabel lingkungan HOME
HOME_DIR = os.environ.get("HOME", "/root")
HUMANODE_DIR = os.path.join(HOME_DIR, ".humanode/workspaces/default")
HUMANODE_PEER = os.path.join(HUMANODE_DIR, "humanode-peer")
CHAIN_SPEC = os.path.join(HUMANODE_DIR, "chainspec.json")

# Endpoint untuk bioauth_status
url = "http://127.0.0.1:9933"
headers = {"Content-Type": "application/json"}
payload = {
    "jsonrpc": "2.0",
    "method": "bioauth_status",
    "params": [],
    "id": 1
}

auth_url_command = f"{HUMANODE_PEER} bioauth auth-url --rpc-url-ngrok-detect --chain {CHAIN_SPEC}"

# Memuat konfigurasi dari file config.json
CONFIG_FILE = "config.json"
with open(CONFIG_FILE) as f:
    config = json.load(f)

telegram_token = config["telegram_token"]
telegram_chat_id = config["telegram_chat_id"]
username = config["username"]

telegram_api_url = f"https://api.telegram.org/bot{telegram_token}/sendMessage"

# Variabel global untuk melacak status dan link terakhir
last_status = None
last_auth_url = None
NOTIFY_FLAG = "/tmp/initial_notify_done"  # Penanda untuk notifikasi awal

# Fungsi untuk mendapatkan IP server
def get_server_ip():
    try:
        ip = requests.get("https://api.ipify.org").text
        return ip
    except requests.exceptions.RequestException as e:
        print(f"Gagal mendapatkan IP server: {e}")
        return "Tidak diketahui"

# Fungsi untuk mendapatkan URL autentikasi
def get_auth_url(retries=5, delay=10):
    for attempt in range(retries):
        try:
            if not os.path.exists(HUMANODE_PEER):
                raise FileNotFoundError(f"File {HUMANODE_PEER} tidak ditemukan.")
            result = subprocess.check_output(auth_url_command, shell=True, text=True).strip()
            if result:
                return result
        except subprocess.CalledProcessError as e:
            print(f"[Retry {attempt + 1}/{retries}] Gagal mendapatkan URL autentikasi: {e}")
        time.sleep(delay)
    print("Gagal mendapatkan URL autentikasi setelah beberapa percobaan.")
    return "Tidak tersedia"

# Fungsi untuk mengirim notifikasi ke Telegram
def send_telegram_message(message):
    try:
        if len(message) > 4096:
            print("Pesan terlalu panjang untuk dikirim, memotong pesan.")
            message = message[:4093] + "..."

        payload = {
            "chat_id": telegram_chat_id,
            "text": message,
            "parse_mode": "HTML"
        }
        response = requests.post(telegram_api_url, json=payload)
        if response.status_code == 200:
            print("Notifikasi berhasil dikirim ke Telegram.")
        else:
            print(f"Gagal mengirim notifikasi ke Telegram. Status kode: {response.status_code}, Respons: {response.text}")
    except requests.exceptions.RequestException as e:
        print(f"Terjadi kesalahan saat mengirim notifikasi Telegram: {e}")

# Fungsi untuk notifikasi awal bahwa Anda adalah validator
def notify_initial_status():
    if os.path.exists(NOTIFY_FLAG):
        print("Notifikasi awal sudah dikirim sebelumnya. Melewati...")
        return

    server_ip = get_server_ip()
    auth_url = get_auth_url()

    try:
        response = requests.post(url, json=payload, headers=headers)
        response_data = response.json()

        if "result" in response_data and "Active" in response_data["result"]:
            expires_at = response_data["result"]["Active"]["expires_at"]
            expires_at_seconds = expires_at / 1000
            current_time = datetime.datetime.now().timestamp()
            remaining_seconds = int(expires_at_seconds - current_time)
            hours, remainder = divmod(remaining_seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            formatted_remaining_time = f"{hours}:{minutes:02}:{seconds:02}"
        else:
            formatted_remaining_time = "Tidak tersedia"

        message = (
            f"✅ @{username} Anda adalah validator!\n"
            f"IP Address: <b>{server_ip}</b>\n"
            f"Waktu autentikasi Anda: <b>{formatted_remaining_time}</b>\n"
            f"Link autentikasi Anda: <a href='{auth_url}'>{auth_url}</a>"
        )

        send_telegram_message(message)

        with open(NOTIFY_FLAG, "w") as f:
            f.write("Notifikasi awal sudah dikirim.")
        print("Notifikasi awal berhasil dikirim.")

    except Exception as e:
        print(f"Terjadi kesalahan saat mengirim notifikasi awal: {e}")
        send_telegram_message(
            f"❌ @{username} Terjadi kesalahan saat memeriksa status validator.\n"
            f"Kesalahan: {e}"
        )

# Fungsi utama untuk memeriksa status autentikasi dan pengingat
def check_bioauth_status():
    global last_status, last_auth_url
    try:
        server_ip = get_server_ip()
        auth_url = get_auth_url()
        
        if auth_url != last_auth_url:
            last_auth_url = auth_url
            send_telegram_message(
                f"🔄 @{username}, link autentikasi Anda telah berubah.\n"
                f"Link baru: <a href='{auth_url}'>{auth_url}</a>"
            )
        
        response = requests.post(url, json=payload, headers=headers)

        if response.status_code == 200:
            response_data = response.json()
            if "result" in response_data and "Active" in response_data["result"]:
                expires_at = response_data["result"]["Active"]["expires_at"]
                expires_at_seconds = expires_at / 1000
                current_time = datetime.datetime.now().timestamp()
                remaining_seconds = int(expires_at_seconds - current_time)

                hours, remainder = divmod(remaining_seconds, 3600)
                minutes, seconds = divmod(remainder, 60)
                formatted_remaining_time = f"{hours}:{minutes:02}:{seconds:02}"

                current_status = f"{hours}:{minutes:02}:{seconds:02}"

                if current_status != last_status:
                    last_status = current_status

                    if 3600 <= remaining_seconds <= 3660:
                        message = (
                            f"⚠️ @{username}, bioauth akan kedaluwarsa dalam <b>1 jam</b>.\n"
                            f"IP Address: <b>{server_ip}</b>\n"
                            f"Sisa waktu: <b>{formatted_remaining_time}</b>\n"
                            f"Link autentikasi: <a href='{auth_url}'>Klik di sini</a>"
                        )
                        send_telegram_message(message)

                    if 0 < remaining_seconds <= 600 and remaining_seconds % 300 == 0:
                        message = (
                            f"⚠️ @{username}, bioauth akan kedaluwarsa dalam <b>{remaining_seconds // 60} menit</b>.\n"
                            f"IP Address: <b>{server_ip}</b>\n"
                            f"Sisa waktu: <b>{formatted_remaining_time}</b>\n"
                            f"Link autentikasi: <a href='{auth_url}'>Klik di sini</a>"
                        )
                        send_telegram_message(message)

                if remaining_seconds <= 0:
                    if abs(remaining_seconds) % 300 == 0:
                        message = (
                            f"❌ @{username}, bioauth telah kedaluwarsa.\n"
                            f"IP Address: <b>{server_ip}</b>\n"
                            f"Link autentikasi: <a href='{auth_url}'>Klik di sini</a>"
                        )
                        send_telegram_message(message)
        else:
            send_telegram_message(f"❌ Gagal menghubungi server RPC.")
    except Exception as e:
        print(f"Kesalahan: {e}")

if __name__ == "__main__":
    notify_initial_status()
    while True:
        check_bioauth_status()
        time.sleep(60)
