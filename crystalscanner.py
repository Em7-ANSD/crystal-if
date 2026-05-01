from rich.live import Live
from rich.panel import Panel
from rich.layout import Layout
from rich.table import Table
from rich.console import Console
import threading
import time
import os
import json
from datetime import datetime, timedelta
import requests
import collections
import sys
import select

# =========================
# FILES
# =========================

KEY_FILE = "key_data.json"
CONFIG_FILE = "config.json"

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
# Risk Engine
# =========================

class RiskEngine:
    def __init__(self):
        self.users = {}

    def process_message(self, user_id, content):
        user = self.users.get(user_id, {"count": 0, "risk": 0})
        user["count"] += 1

        if user["count"] > 10:
            user["risk"] += 1

        self.users[user_id] = user
        return min(user["risk"], 10)

# =========================
# Investigation Engine
# =========================

class InvestigationEngine:
    def __init__(self):
        self.users = {}

    def analyze_message(self, user_id, content, timestamp):
        insights = []

        if user_id not in self.users:
            self.users[user_id] = {"count": 0, "last": timestamp}

        self.users[user_id]["count"] += 1

        if self.users[user_id]["count"] > 10:
            insights.append("Usuário dominante")

        delta = (timestamp - self.users[user_id]["last"]).total_seconds()
        if delta < 2:
            insights.append("Envio rápido")

        self.users[user_id]["last"] = timestamp

        return insights

    def generate_report(self):
        txt = "\n=== RELATÓRIO FORENSE ===\n"
        for uid, data in self.users.items():
            txt += f"\nUser {uid} | msgs: {data['count']}\n"
        return txt

# =========================
# KEY SYSTEM
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
# CONFIG
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

def reset_config():
    if os.path.exists(CONFIG_FILE):
        os.remove(CONFIG_FILE)
    print("\n[+] Config resetada\n")

def setup_panel():
    print("\n=== CONFIG ===\n")
    token = input("Token: ").strip()
    channel = input("Channel ID: ").strip()
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
                uid = m["author"]["id"]
                content = m.get("content", "")
                now = datetime.now()

                risk = risk_engine.process_message(uid, content)
                insights = investigation_engine.analyze_message(uid, content, now)

                messages.append({
                    "time": now.strftime("%H:%M:%S"),
                    "content": content,
                    "risk": risk,
                    "insights": insights
                })

                if len(messages) > 100:
                    messages.pop(0)

            time.sleep(2)

        except:
            time.sleep(2)

# =========================
# INPUT (SEM BUG)
# =========================

def comando_input():
    while True:
        time.sleep(0.1)

        if select.select([sys.stdin], [], [], 0)[0]:
            cmd = sys.stdin.readline().strip()

            if cmd.startswith("!enviar "):
                enviar_mensagem_discord(cmd[8:])

            elif cmd == "!relatorio":
                console.print(investigation_engine.generate_report())

            elif cmd == "!sair":
                os._exit(0)

# =========================
# UI
# =========================

def make_layout():
    layout = Layout()
    layout.split_column(
        Layout(name="header", size=3),
        Layout(name="body"),
        Layout(name="footer", size=3)
    )

    layout["header"].update(Panel("CRYSTAL FORENSIC SCANNER"))

    table = Table(expand=True)
    table.add_column("Hora")
    table.add_column("Mensagem")
    table.add_column("Risco")

    for m in messages[-20:]:
        table.add_row(m["time"], m["content"], str(m["risk"]))

    layout["body"].update(Panel(table))
    layout["footer"].update(Panel("Comandos: !relatorio | !enviar | !sair"))

    return layout

def run_dashboard():
    with Live(make_layout(), refresh_per_second=2):
        while True:
            time.sleep(0.5)

# =========================
# START
# =========================

def start_scanner():
    global TOKEN, CHANNEL_ID, HEADERS, risk_engine, investigation_engine

    config = load_config()
    if not config:
        setup_panel()
        config = load_config()

    TOKEN = config["token"]
    CHANNEL_ID = config["channel_id"]
    HEADERS = {"Authorization": TOKEN}

    risk_engine = RiskEngine()
    investigation_engine = InvestigationEngine()

    threading.Thread(target=scanner_loop, daemon=True).start()
    threading.Thread(target=run_dashboard, daemon=True).start()

    comando_input()

# =========================
# MENU
# =========================

def menu():
    while True:
        print("\n[1] Start Scanner")
        print("[2] Reset Config")
        print("[3] Login Key")
        print("[4] Sair")

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

if __name__ == "__main__":
    menu()
