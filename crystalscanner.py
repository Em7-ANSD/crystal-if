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

# =========================
# 📁 FILES
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
# 🌐 GLOBAL
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
        self.time_window_seconds = 10

    def process_message(self, user_id, content):
        now = datetime.now()
        user = self.users.get(user_id, {"msgs": [], "risk": 0})

        user["msgs"].append((now, content))

        # flood
        recent = [m for m in user["msgs"] if (now - m[0]).total_seconds() < 10]
        if len(recent) >= 5:
            user["risk"] += 2

        # spam
        if len(user["msgs"]) >= 3:
            last = [m[1] for m in user["msgs"][-3:]]
            if len(set(last)) == 1:
                user["risk"] += 3

        user["risk"] = min(user["risk"], 10)
        self.users[user_id] = user
        return user["risk"]

# =========================
# Investigation Engine
# =========================

class InvestigationEngine:
    def __init__(self):
        self.activity = {}
        self.timeline = []

    def analyze_message(self, user_id, content, timestamp):
        insights = []

        if user_id not in self.activity:
            self.activity[user_id] = {"count": 0, "last": timestamp}

        user = self.activity[user_id]
        user["count"] += 1

        if user["count"] > 10:
            insights.append("Usuário dominante")

        delta = (timestamp - user["last"]).total_seconds()
        if delta < 2:
            insights.append("Envio rápido")

        user["last"] = timestamp

        self.timeline.append(timestamp)
        if len(self.timeline) > 15:
            self.timeline.pop(0)

        if len(self.timeline) >= 10:
            if (self.timeline[-1] - self.timeline[0]).total_seconds() < 5:
                insights.append("Pico de atividade")

        return insights

    def generate_report(self):
        txt = "\n=== RELATÓRIO ===\n"
        for uid, data in self.activity.items():
            txt += f"\nUser {uid} | msgs: {data['count']}\n"
        return txt

# =========================
# CONFIG
# =========================

def load_config():
    try:
        with open(CONFIG_FILE) as f:
            return json.load(f)
    except:
        return None

def setup():
    token = input("Token: ")
    channel = input("Channel ID: ")
    with open(CONFIG_FILE, "w") as f:
        json.dump({"token": token, "channel_id": channel}, f)

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

    lay["bot"].update(Panel("!relatorio"))

    return lay

def dashboard():
    with Live(refresh_per_second=4, screen=True) as live:
        while True:
            live.update(layout())
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

    cfg = load_config()
    if not cfg:
        setup()
        cfg = load_config()

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
