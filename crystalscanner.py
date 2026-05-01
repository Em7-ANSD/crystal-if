import discord
import os
import json
import asyncio
from datetime import datetime, timedelta

# =========================
# 🔐 FILE MANAGEMENT
# =========================

KEY_FILE = "key.json"
CONFIG_FILE = "config.json"

# =========================
# 🔑 AUTHENTICATION KEYS
# =========================

VALID_KEYS = {
    "CRYSTAL-IF-001": 1,
    "TESTE-123": 0.01
}

# =========================
# 🧠 GLOBAL STATE
# =========================

TOKEN = None
MONITORED_CHANNELS = []

# =========================
# 🎨 ASCII ART
# =========================

ASCII_ART = r"""
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

def save_key(key, expire_time):
    """Save authentication key to file."""
    with open(KEY_FILE, "w") as f:
        json.dump({"key": key, "expire": expire_time.timestamp()}, f)

def load_key():
    """Load authentication key from file."""
    try:
        return json.load(open(KEY_FILE))
    except (FileNotFoundError, json.JSONDecodeError):
        return None

def is_key_valid(key_data):
    """Check if key is valid and not expired."""
    if not key_data:
        return False
    return datetime.now().timestamp() < key_data["expire"]

def authenticate_user():
    """Authenticate user with key system."""
    key_data = load_key()

    if key_data and is_key_valid(key_data):
        print("\n[+] Key active (auto-login)\n")
        return True

    key = input("🔐 Key: ").strip()

    if key in VALID_KEYS:
        expire_time = datetime.now() + timedelta(days=VALID_KEYS[key])
        save_key(key, expire_time)
        print("\n[+] Key accepted\n")
        return True

    print("\n[-] Invalid key\n")
    return False

# =========================
# ⚙️ CONFIGURATION SYSTEM
# =========================

def save_configuration(token, channels):
    """Save configuration to file."""
    with open(CONFIG_FILE, "w") as f:
        json.dump({
            "token": token,
            "channels": channels
        }, f)

def load_configuration():
    """Load configuration from file."""
    try:
        return json.load(open(CONFIG_FILE))
    except (FileNotFoundError, json.JSONDecodeError):
        return None

def reset_configuration():
    """Reset configuration file."""
    if os.path.exists(CONFIG_FILE):
        os.remove(CONFIG_FILE)
    print("\n[+] Configuration reset\n")

def setup_configuration():
    """Setup initial configuration."""
    print("\n=== SETUP ===\n")
    token = input("User Token: ").strip()
    channels = input("Channels (comma separated): ").split(",")

    channels = [int(c.strip()) for c in channels]

    save_configuration(token, channels)
    print("\n[+] Configuration saved\n")

# =========================
# 🧾 LOGGING SYSTEM
# =========================

def log_message(channel_id, author_name, content):
    """Log message to file."""
    os.makedirs("logs", exist_ok=True)

    with open(f"logs/{channel_id}.log", "a", encoding="utf-8") as f:
        f.write(f"[{datetime.now()}] {author_name}: {content}\n")

# =========================
# 🖥 DISPLAY SYSTEM
# =========================

def display_message(channel_id, author_name, content):
    """Display message on terminal."""
    os.system("clear")
    print(ASCII_ART)
    print("\n━━━━━━━━━━━━━━━━━━━━━━━\n")
    print(f"📡 Channel: {channel_id}")
    print(f"👤 Author: {author_name}")
    print(f"💬 Message:\n{content}")
    print("\n━━━━━━━━━━━━━━━━━━━━━━━\n")
    print("STATUS: LIVE MONITORING")

# =========================
# 🤖 DISCORD CLIENT
# =========================

class DiscordClient(discord.Client):
    """Custom Discord client class."""
    def __init__(self):
        super().__init__(intents=discord.Intents.all())

    async def on_ready(self):
        """Handle client ready event."""
        os.system("clear")
        print(ASCII_ART)
        print("\n[+] CRYSTAL IF ONLINE\n")

    async def on_message(self, message):
        """Handle incoming messages."""
        # Process messages from monitored channels only
        if MONITORED_CHANNELS and message.channel.id not in MONITORED_CHANNELS:
            return

        log_message(message.channel.id, message.author.name, message.content)
        display_message(message.channel.id, message.author.name, message.content)

# =========================
# 🚀 MAIN APPLICATION
# =========================

def start_application():
    """Start main application."""
    global TOKEN, MONITORED_CHANNELS

    config = load_configuration()

    if not config:
        setup_configuration()
        config = load_configuration()

    TOKEN = config["token"]
    MONITORED_CHANNELS = config["channels"]

    client = DiscordClient()
    client.run(TOKEN, reconnect=True)

# =========================
# 📋 MAIN MENU
# =========================

def main_menu():
    """Display main menu and handle user input."""
    while True:
        os.system("clear")
        print(ASCII_ART)
        print("\n[1] Start Scanner")
        print("[2] Reset Config")
        print("[3] Login Key")
        print("[4] Exit\n")

        choice = input(">> ").strip()

        if choice == "1":
            if authenticate_user():
                start_application()

        elif choice == "2":
            reset_configuration()

        elif choice == "3":
            authenticate_user()

        elif choice == "4":
            break

        else:
            print("Invalid")

# =========================
# 🚀 ENTRY POINT
# =========================

if __name__ == "__main__":
    main_menu()
