import requests
import time
import random
import threading
import os
import json
from datetime import datetime, timedelta

# =========================
# 🔐 CONFIG
# =========================

TOKEN = "SEU_TOKEN_AQUI"
CHANNEL_ID = "SEU_CHANNEL_ID"

HEADERS = {
    "Authorization": TOKEN
}

user_profiles = {}
seen = set()

# =========================
# 🔑 SISTEMA DE KEY
# =========================

KEY_FILE = "key_data.json"

VALID_KEYS = {
    "CRYSTAL-IF-001": 1,   # 1 dia
    "TESTE-123": 0.01      # teste curto (~15 min)
}

def save_key(key, expire_at):
    data = {
        "key": key,
        "expire_at": expire_at.timestamp()
    }
    with open(KEY_FILE, "w") as f:
        json.dump(data, f)

def load_key():
    try:
        with open(KEY_FILE, "r") as f:
            return json.load(f)
    except:
        return None

def is_key_valid(data):
    if not data:
        return False

    expire_at = datetime.fromtimestamp(data["expire_at"])
    return datetime.now() <= expire_at

def login():
    saved = load_key()

    if saved and is_key_valid(saved):
        print("\n[+] LOGIN AUTOMÁTICO LIBERADO (KEY SALVA)\n")
        return True

    print("\n=== CRYSTAL IF | PAINEL DE ACESSO ===\n")

    key = input("🔐 Digite sua key: ").strip()

    if key in VALID_KEYS:
        days = VALID_KEYS[key]
        expire_at = datetime.now() + timedelta(days=days)

        save_key(key, expire_at)

        print(f"\n[+] Acesso liberado")
        print(f"[+] Expira em: {expire_at}\n")
        return True

    print("\n[-] Key inválida\n")
    return False

# =========================
# 🎨 ASCII BANNER (AZUL FIXO)
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
# 📡 DISCORD SCANNER
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
    print("\n[ CRYSTAL | IF iniciando... ]")

    if not login():
        return

    threading.Thread(target=banner_loop, daemon=True).start()
    threading.Thread(target=scanner_loop, daemon=True).start()

    while True:
        time.sleep(1)

if __name__ == "__main__":
    main()
