from rich.live import Live
from rich.panel import Panel
from rich.layout import Layout
from rich.table import Table
from rich.console import Console
from rich.align import Align

import threading
import time
import os
import json
from datetime import datetime, timedelta
import requests

# =========================
# FILES
# =========================

KEY_FILE = "key_data.json"
CONFIG_FILE = "config.json"
COMMAND_FILE = "cmd.txt"

# =========================
# KEYS
# =========================

VALID_KEYS = {
    "CRYSTAL-IF-001": 1,
    "TESTE-123": 0.01
}

# =========================
# GLOBAL
# =========================

TOKEN = None
CHANNEL_ID = None
HEADERS = {}

seen = set()
messages = []

console = Console()

# =========================
# KEY SYSTEM
# =========================

def save_key(key, expire_at):
    with open(KEY_FILE, "w") as f:
        json.dump({"key": key, "expire_at": expire_at.timestamp()}, f)

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
        print("\n[+] Login automático via KEY salva\n")
        return True

    print("\n=== CRYSTAL IF | LOGIN ===\n")
    key = input("🔐 Key: ").strip()

    if key in VALID_KEYS:
        expire = datetime.now() + timedelta(days=VALID_KEYS[key])
        save_key(key, expire)
        print("\n[+] Acesso liberado\n")
        return True

    print("\n[-] KEY inválida\n")
    return False

# =========================
# CONFIG SYSTEM
# =========================

def save_config(token, channel_id):
    with open(CONFIG_FILE, "w") as f:
        json.dump({"token": token, "channel_id": channel_id}, f)

def load_config():
    try:
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    except:
        return None

def reset_config():
    if os.path.exists(CONFIG_FILE):
        os.remove(CONFIG_FILE)
    print("\n[+] Config resetada\n")

def setup_panel():
    print("\n=== CONFIG ===\n")
    token = input("🔑 Token: ").strip()
    channel = input("📡 Channel ID: ").strip()
    save_config(token, channel)

def test_config(token, channel_id):
    url = f"https://discord.com/api/v10/channels/{channel_id}/messages?limit=1"
    headers = {"Authorization": token}
    r = requests.get(url, headers=headers)
    return r.status_code == 200

# =========================
# SCANNER
# =========================

def fetch_messages():
    url = f"https://discord.com/api/v10/channels/{CHANNEL_ID}/messages?limit=20"
    return requests.get(url, headers=HEADERS).json()

def scanner_loop():
    global seen, messages

    while True:
        try:
            msgs = fetch_messages()

            if not isinstance(msgs, list):
                time.sleep(2)
                continue

            for m in msgs:
                if m["id"] in seen:
                    continue

                seen.add(m["id"])

                messages.append({
                    "time": datetime.now().strftime("%H:%M:%S"),
                    "user": m["author"]["id"],
                    "content": m.get("content", ""),
                    "risk": 0
                })

                if len(messages) > 100:
                    messages.pop(0)

            time.sleep(2)

        except:
            time.sleep(2)

# =========================
# CMD.TXT LOOP
# =========================

def comando_loop():
    while True:
        try:
            if os.path.exists(COMMAND_FILE):
                with open(COMMAND_FILE, "r") as f:
                    cmd = f.read().strip()

                os.remove(COMMAND_FILE)

                if cmd.startswith("!enviar "):
                    enviar_mensagem_discord(cmd[8:])

                elif cmd == "!sair":
                    os._exit(0)

                elif cmd == "!relatorio":
                    print(f"\nTotal mensagens: {len(messages)}\n")

        except Exception as e:
            print("Erro comando:", e)

        time.sleep(1)

# =========================
# LAYOUT
# =========================

def make_layout():
    layout = Layout()

    layout.split_column(
        Layout(name="header", size=3),
        Layout(name="body"),
        Layout(name="footer", size=3)
    )

    layout["header"].update(
        Panel(Align.center("[bold cyan]🔍 CrystalX Forensic[/bold cyan]"), style="green")
    )

    table = Table(expand=True)

    table.add_column("Hora", style="cyan")
    table.add_column("User", style="magenta")
    table.add_column("Mensagem", style="white")
    table.add_column("Risco", style="red")

    for msg in messages[-15:]:
        table.add_row(
            msg["time"],
            msg["user"],
            msg["content"],
            str(msg["risk"])
        )

    layout["body"].update(Panel(table, title="Monitoramento em Tempo Real"))

    layout["footer"].update(
        Panel("[yellow]Use: echo '!comando' > cmd.txt[/yellow]")
    )

    return layout

def run_dashboard():
    with Live(refresh_per_second=2) as live:
        while True:
            live.update(make_layout())
            time.sleep(0.5)

# =========================
# ENVIAR
# =========================

def enviar_mensagem_discord(msg):
    url = f"https://discord.com/api/v10/channels/{CHANNEL_ID}/messages"

    requests.post(url, headers={
        "Authorization": TOKEN,
        "Content-Type": "application/json"
    }, json={"content": msg})

# =========================
# START
# =========================

def start_scanner():
    global TOKEN, CHANNEL_ID, HEADERS

    config = load_config()

    if not config:
        setup_panel()
        config = load_config()

    if not test_config(config["token"], config["channel_id"]):
        print("Config inválida")
        return

    TOKEN = config["token"]
    CHANNEL_ID = config["channel_id"]
    HEADERS = {"Authorization": TOKEN}

    threading.Thread(target=scanner_loop, daemon=True).start()
    threading.Thread(target=run_dashboard, daemon=True).start()
    threading.Thread(target=comando_loop, daemon=True).start()

    while True:
        time.sleep(1)

# =========================
# MENU
# =========================

def menu():
    while True:
        os.system("clear")
        print("CRYSTAL IF\n")

        print("[1] Start Scanner")
        print("[2] Reset Config")
        print("[3] Login Key")
        print("[4] Sair\n")

        op = input(">> ")

        if op == "1":
            if login():
                start_scanner()

        elif op == "2":
            reset_config()

        elif op == "3":
            login()

        elif op == "4":
            break

# =========================
# MAIN
# =========================

if __name__ == "__main__":
    menu()
