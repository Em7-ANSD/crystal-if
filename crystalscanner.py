import discord
import os
import json
from datetime import datetime, timedelta

# =========================
# 📁 FILES
# =========================

KEY_FILE = "key.json"
CONFIG_FILE = "config.json"

# =========================
# 🔑 KEYS
# =========================

VALID_KEYS = {
    "CRYSTAL-IF-001": 1,
    "TESTE-123": 1
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
  ______     ______     __  __     ______
 /\  ___\   /\  == \   /\ \_\ \   /\  ___\
 \ \ \____  \ \  __<   \ \____ \  \ \___  \
  \ \_____\  \ \_\ \_\  \/\_____\  \/\_____\
   \/_____/   \/_/ /_/   \/_____/   \/_____/

        CRYSTAL IF - FORENSIC PANEL
"""

# =========================
# 🔐 KEY SYSTEM
# =========================

def save_key(key, expire):
    with open(KEY_FILE, "w") as f:
        json.dump({
            "key": key,
            "expire": expire.timestamp()
        }, f)

def load_key():
    try:
        with open(KEY_FILE, "r") as f:
            return json.load(f)
    except:
        return None

def key_valid(data):
    if not data:
        return False
    return datetime.now().timestamp() < data["expire"]

def auth():
    data = load_key()

    if data and key_valid(data):
        print("[+] Auto-login OK\n")
        return True

    key = input("Key: ").strip()

    if key in VALID_KEYS:
        expire = datetime.now() + timedelta(days=VALID_KEYS[key])
        save_key(key, expire)
        print("[+] Key aceita\n")
        return True

    print("[-] Key inválida\n")
    return False

# =========================
# ⚙️ CONFIG
# =========================

def save_config(token, channels):
    with open(CONFIG_FILE, "w") as f:
        json.dump({
            "token": token,
            "channels": channels
        }, f)

def load_config():
    try:
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    except:
        return None

def setup():
    print("\n=== Configuração Inicial ===")
    token = input("Digite seu Token de Conta (Selfbot): ").strip()
    canais_input = input("Digite os IDs dos canais, separados por vírgula: ").strip()
    canais = [int(c.strip()) for c in canais_input.split(",") if c.strip().isdigit()]

    save_config(token, canais)
    print("[+] Configuração salva!\n")

def reset():
    if os.path.exists(CONFIG_FILE):
        os.remove(CONFIG_FILE)
    print("[+] Config resetada\n")

# =========================
# 🖥 DISPLAY
# =========================

def display(msg):
    os.system("clear")
    print(ASCII)
    print("\n━━━━━━━━━━━━━━━━━━━\n")
    print(f"📡 {msg.channel.id}")
    print(f"👤 {msg.author}")
    print(f"💬 {msg.content}")
    print("\n━━━━━━━━━━━━━━━━━━━\n")

# =========================
# 🤖 SELFHOST
# =========================

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)

@client.event
async def on_ready():
    os.system("clear")
    print(ASCII)
    print("\n[+] SELFHOST ONLINE\n")
    print(f"Logged in as: {client.user}")

@client.event
async def on_message(message):
    if CHANNELS and message.channel.id not in CHANNELS:
        return

    display(message)

# =========================
# 🚀 START
# =========================

def start():
    global TOKEN, CHANNELS

    config = load_config()

    if not config:
        setup()
        config = load_config()

    TOKEN = config["token"]
    CHANNELS = config["channels"]

    client.run(TOKEN)  # Aqui, apenas TOKEN, sem argumentos extras

# =========================
# 📋 MENU
# =========================

def menu():
    while True:
        os.system("clear")
        print(ASCII)
        print("\n[1] Start")
        print("[2] Reset Config")
        print("[3] Key Login")
        print("[4] Exit\n")

        op = input(">> ")

        if op == "1":
            if auth():
                start()

        elif op == "2":
            reset()

        elif op == "3":
            auth()

        elif op == "4":
            break

# =========================
# ▶ START
# =========================

if __name__ == "__main__":
    menu()
