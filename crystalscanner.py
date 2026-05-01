import requests
import time
import threading
import os
import json
from datetime import datetime, timedelta

# =========================
# 📁 ARQUIVOS
# =========================

KEY_FILE = "key_data.json"
CONFIG_FILE = "config.json"

# =========================
# 🔑 KEYS
# =========================

VALID_KEYS = {
    "CRYSTAL-IF-001": 1,
    "TESTE-123": 0.01
}

# =========================
# 🌐 VARIÁVEIS GLOBAIS
# =========================

TOKEN = None
CHANNEL_ID = None
HEADERS = {}

user_profiles = {}
seen = set()

# =========================
# 🔐 KEY SYSTEM
# =========================

def save_key(key, expire_at):
    with open(KEY_FILE, "w") as f:
        json.dump({
            "key": key,
            "expire_at": expire_at.timestamp()
        }, f)

def load_key():
    try:
        with open(KEY_FILE, "r") as f:
            return json.load(f)
    except:
        return None

def is_key_valid(data):
    if not data:
        return False
    return datetime.now() <= datetime.fromtimestamp(data["expire_at"])

def login():
    saved = load_key()

    if saved and is_key_valid(saved):
        print("\n[+] Login automático via key salva\n")
        return True

    print("\n=== CRYSTAL IF | LOGIN ===\n")

    key = input("🔐 Digite sua KEY: ").strip()

    if key in VALID_KEYS:
        days = VALID_KEYS[key]
        expire = datetime.now() + timedelta(days=days)

        save_key(key, expire)

        print(f"\n[+] Acesso liberado até {expire}\n")
        return True

    print("\n[-] KEY inválida\n")
    return False

# =========================
# ⚙️ CONFIG SYSTEM
# =========================

def save_config(token, channel_id):
    with open(CONFIG_FILE, "w") as f:
        json.dump({
            "token": token,
            "channel_id": channel_id
        }, f)

def load_config():
    try:
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    except:
        return None

def setup_panel():
    print("\n=== CRYSTAL IF | PAINEL DE CONFIGURAÇÃO ===\n")

    token = input("🔑 Token: ").strip()
    channel = input("📡 Channel ID: ").strip()

    save_config(token, channel)

    print("\n[+] Configuração salva!\n")

# =========================
# 🎨 BANNER
# =========================

BLUE = "\033[34m"
RESET = "\033[0m"

art = r"""
______________________.___. _________________________  .____
\_   ___ \______   \__  |   |/   _____/\__    ___/  _  \ |    |
/    \  \/|       _//   |   |\_____  \   |    | /  /_\  \|    |
\     \___|    |   \\____   |/        \  |    |/    |    \    |___
 \______  /____|_  // ______/_______  /  |____|\____|__  /_______ \
        \/       \/ \/              \/                 \/        \/

________  .___  ________.___________________  .____
\______ \ |   |/  _____/|   \__    ___/  _  \ |    |
 |    |  \|   /   \  ___|   | |    | /  /_\  \|    |
 |    `   \   \    \_\  \   | |    |/    |    \    |___
/_______  /___|\______  /___| |____|\____|__  /_______ \
        \/            \/                    \/        \/

.___ ___________   _______________ ____________________.___  ________    ________________________ __________
|   |\      \   \ /   /\_   _____//   _____/\__    ___/|   |/  _____/   /  _  \__    ___/\_____  \\______   \
|   |/   |   \   Y   /  |    __)_ \_____  \   |    |   |   /   \  ___  /  /_\  \|    |    /   |   \|       _/
|   /    |    \     /   |        \/        \  |    |   |   \    \_\  \/    |    \    |   /    |    \    |   \
|___\____|__  /\___/   /_______  /_______  /  |____|   |___|\______  /\____|__  /____|   \_______  /____|_  /
            \/                 \/        \/                        \/         \/                 \/       \/
"""

def banner_loop():
    while True:
        os.system("clear")
        print(BLUE + art + RESET)
        print("\n[ CRYSTAL | IF - SCANNER ONLINE ]\n")
        time.sleep(0.5)

# =========================
# 📡 SCANNER
# =========================

def fetch_messages(limit=20):
    url = f"https://discord.com/api/v10/channels/{CHANNEL_ID}/messages?limit={limit}"
    r = requests.get(url, headers=HEADERS)

    if r.status_code != 200:
        print("Erro:", r.status_code)
        return []

    return r.json()

def analyze(content):
    flags = []
    c = content.lower()

    if len(c) > 200:
        flags.append("LONG")

    if c.count("!") > 5:
        flags.append("SPAM")

    return flags

def update(uid, flags):
    if uid not in user_profiles:
        user_profiles[uid] = {"count": 0, "flags": []}

    user_profiles[uid]["count"] += 1
    user_profiles[uid]["flags"].extend(flags)

def risk(uid):
    p = user_profiles.get(uid, {})
    return min(len(p.get("flags", [])) * 5 + p.get("count", 0), 100)

def scanner_loop():
    global seen

    while True:
        msgs = fetch_messages()

        for m in msgs:
            if m["id"] in seen:
                continue

            seen.add(m["id"])

            uid = m["author"]["id"]
            content = m.get("content", "")

            flags = analyze(content)
            update(uid, flags)

            print(f"{uid} | risk={risk(uid)} | {content[:40]}")

        time.sleep(3)

# =========================
# 🚀 MAIN
# =========================

def main():
    print("\n[ CRYSTAL IF INICIANDO ]\n")

    if not login():
        return

    config = load_config()

    if not config:
        setup_panel()
        config = load_config()

    global TOKEN, CHANNEL_ID, HEADERS

    TOKEN = config["token"]
    CHANNEL_ID = config["channel_id"]

    HEADERS = {
        "Authorization": TOKEN
    }

    threading.Thread(target=banner_loop, daemon=True).start()
    threading.Thread(target=scanner_loop, daemon=True).start()

    while True:
        time.sleep(1)

if __name__ == "__main__":
    main()
