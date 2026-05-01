from rich.live import Live
from rich.panel import Panel
from rich.layout import Layout
from rich.table import Table
from rich.console import Console
import threading
import time
import os
import json
from datetime import datetime
import requests

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
        self.activity = {}

    def analyze_message(self, user_id, content, timestamp):
        insights = []

        if user_id not in self.activity:
            self.activity[user_id] = {"count": 0}

        self.activity[user_id]["count"] += 1

        if self.activity[user_id]["count"] > 10:
            insights.append("Usuário dominante")

        return insights

    def generate_report(self):
        txt = "\n=== RELATÓRIO ===\n"
        for uid, data in self.activity.items():
            txt += f"\nUser {uid} | msgs: {data['count']}\n"
        return txt

# =========================
# CONFIG
# =========================

def setup():
    token = input("Token: ")
    channel = input("Channel ID: ")
    with open("config.json", "w") as f:
        json.dump({"token": token, "channel_id": channel}, f)

def load():
    try:
        with open("config.json") as f:
            return json.load(f)
    except:
        return None

# =========================
# SCANNER
# =========================

def fetch():
    url = f"https://discord.com/api/v10/channels/{CHANNEL_ID}/messages?limit=10"
    return requests.get(url, headers=HEADERS).json()

def scanner():
    global seen, messages
    while True:
        try:
            msgs = fetch()
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
                    "msg": content,
                    "risk": risk,
                    "insights": insights
                })

                if len(messages) > 50:
                    messages.pop(0)

            time.sleep(2)

        except:
            time.sleep(2)

# =========================
# UI
# =========================

def layout():
    lay = Layout()
    lay.split_column(
        Layout(name="top", size=3),
        Layout(name="mid"),
        Layout(name="bot", size=3)
    )

    lay["top"].update(Panel("CRYSTAL FORENSIC"))

    table = Table()
    table.add_column("Hora")
    table.add_column("Msg")
    table.add_column("Risco")

    for m in messages[-10:]:
        table.add_row(m["time"], m["msg"], str(m["risk"]))

    lay["mid"].update(Panel(table))
    lay["bot"].update(Panel("Digite !relatorio"))

    return lay

def dashboard():
    # 🔥 SEM screen=True (corrigido)
    with Live(refresh_per_second=4) as live:
        while True:
            live.update(layout(), refresh=True)
            time.sleep(0.5)

# =========================
# INPUT
# =========================

def cmd():
    while True:
        c = input()
        if c == "!relatorio":
            print(investigation_engine.generate_report())

# =========================
# START
# =========================

def start():
    global TOKEN, CHANNEL_ID, HEADERS, risk_engine, investigation_engine

    cfg = load()
    if not cfg:
        setup()
        cfg = load()

    TOKEN = cfg["token"]
    CHANNEL_ID = cfg["channel_id"]
    HEADERS = {"Authorization": TOKEN}

    risk_engine = RiskEngine()
    investigation_engine = InvestigationEngine()

    threading.Thread(target=scanner, daemon=True).start()
    threading.Thread(target=dashboard, daemon=True).start()

    cmd()

# =========================

if __name__ == "__main__":
    start()
