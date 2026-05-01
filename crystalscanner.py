import discord
import os
import json
import asyncio
from datetime import datetime, timedelta

# =========================
# 🔐 FILES
# =========================

KEY_FILE = "key.json"
CONFIG_FILE = "config.json"

# =========================
# 🔑 KEYS (exemplo)
# =========================

VALID_KEYS = {
    "CRYSTAL-IF-001": 1,
    "TESTE-123": 0.01
}

# =========================
# 🧠 STATE
# =========================

TOKEN = None
CHANNELS = []

# =========================
# 🎨 ASCII
# =========================

ASCII = r"""
  ______     ______     __  __     ______     ______   ______
 /\  ___\   /\  == \   /\ \_\ \   /\  ___\   /\__  _\ /\  __ \
 \ \ \____  \ \  __<   \ \____ \  \ \___  \  \/_/\ \/ \ \  __ \
  \ \_____\  \ \_\ \_\  \/\_____\  \/\_____\    \ \_\  \ \_\ \_\
   \/_____/   \/_/ /_/   \/_____/   \/_____/     \/_/   \/_/\/_/

              CRYSTAL IF - FORENSIC PANEL
"""

# =========================
# 🔐 KEY SYSTEM
# =========================

def save_key(key, expire):
    with open(KEY_FILE, "w") as f:
        json.dump({"key": key, "expire": expire.timestamp()}, f)

def load_key():
    try:
        return json.load(open(KEY_FILE))
    except:
        return None

def key_valid(data):
    if not data:
        return False
    return datetime.now().timestamp() < data["expire"]

def login_key():
    data = load_key()

    if data and key_valid(data):
        print("\n[+] Key active (auto-login)\n")
        return True

    key = input("🔐 Key: ").strip()

    if key in VALID_KEYS:
        expire = datetime.now() + timedelta(days=VALID_KEYS[key])
        save_key(key, expire)
        print("\n[+] Key accepted\n")
        return True

    print("\n[-] Invalid key\n")
    return False

# =========================
# ⚙️ CONFIG SYSTEM
# =========================

def save_config(token, channels):
    with open(CONFIG_FILE, "w") as f:
        json.dump({
            "token": token,
            "channels": channels
        }, f)

def load_config():
    try:
        return json.load(open(CONFIG_FILE))
    except:
        return None

def reset_config():
    if os.path.exists(CONFIG_FILE):
        os.remove(CONFIG_FILE)
    print("\n[+] Config reset\n")

def setup_config():
    print("\n=== SETUP ===\n")
    token = input("User Token: ").strip()
    channels = input("Channels (comma separated): ").split(",")

    channels = [int(c.strip()) for c in channels]

    save_config(token, channels)
    print("\n[+] Config saved\n")

# =========================
# 🧾 LOGS
# =========================

def log_msg(channel, author, content):
    os.makedirs("logs", exist_ok=True)

    with open(f"logs/{channel}.log", "a", encoding="utf-8") as f:
        f.write(f"[{datetime.now()}] {author}: {content}\n")

# =========================
# 🖥 PAINEL
# =========================

def render(channel, author, content):
    os.system("clear")
    print(ASCII)
    print("\n━━━━━━━━━━━━━━━━━━━━━━━\n")
    print(f"📡 Channel: {channel}")
    print(f"👤 Author: {author}")
    print(f"💬 Message:\n{content}")
    print("\n━━━━━━━━━━━━━━━━━━━━━━━\n")
    print("STATUS: LIVE MONITORING")

# =========================
# 🤖 DISCORD CLIENT
# =========================

class Client(discord.Client):
    def __init__(self):
        super().__init__(intents=discord.Intents.all())

    async def on_ready(self):
        os.system("clear")
        print(ASCII)
        print("\n[+] CRYSTAL IF ONLINE\n")

    async def on_message(self, message):
        # Process messages from monitored channels only
        if CHANNELS and message.channel.id not in CHANNELS:
            return

        log_msg(message.channel.id, message.author.name, message.content)
        render(message.channel.id, message.author.name, message.content)

# =========================
# 🚀 START SCANNER
# =========================

def start():
    global TOKEN, CHANNELS

    config = load_config()

    if not config:
        setup_config()
        config = load_config()

    TOKEN = config["token"]
    CHANNELS = config["channels"]

    client = Client()
    client.run(TOKEN, reconnect=True)

# =========================
# 📋 MENU
# =========================

def menu():
    while True:
        os.system("clear")
        print(ASCII)
        print("\n[1] Start Scanner")
        print("[2] Reset Config")
        print("[3] Login Key")
        print("[4] Exit\n")

        op = input(">> ").strip()

        if op == "1":
            if login_key():
                start()

        elif op == "2":
            reset_config()

        elif op == "3":
            login_key()

        elif op == "4":
            break

        else:
            print("Invalid")

# =========================
# 🚀 MAIN
# =========================

if __name__ == "__main__":
    menu()
