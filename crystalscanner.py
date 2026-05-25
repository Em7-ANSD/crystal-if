from rich.live import Live
from rich.panel import Panel
from rich.layout import Layout
from rich.table import Table
from rich.console import Console
from rich.align import Align
from rich.text import Text

import threading
import time
import os
import json
import re
import hashlib
from collections import defaultdict, deque
from datetime import datetime, timedelta

import requests

# =========================
# FILES
# =========================

KEY_FILE = "key_data.json"
CONFIG_FILE = "config.json"
COMMAND_FILE = "cmd.txt"
LOG_FILE = "logs.json"
EVIDENCE_DIR = "evidence"

os.makedirs(EVIDENCE_DIR, exist_ok=True)

# =========================
# REGEX
# =========================

REGEX_PATTERNS = {
    "TOKEN": r"[\w-]{24}\.[\w-]{6}\.[\w-]{27}",
    "EMAIL": r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+",
    "IP": r"\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b",
    "WEBHOOK": r"https://discord(?:app)?\.com/api/webhooks/\d+/[\w-]+",
    "URL": r"https?://[^\s]+"
}

# =========================
# THREAT WEIGHTS
# =========================

THREAT_WEIGHTS = {
    "TOKEN": 70,
    "WEBHOOK": 60,
    "IP": 20,
    "EMAIL": 15,
    "URL": 10,
    "SPAM": 25,
    "WATCHLIST": 80,
    "MASS_MENTION": 40,
    "SUSPICIOUS_ATTACHMENT": 40
}

# =========================
# WATCHLIST
# =========================

WATCHLIST = {
    "1234567890"
}

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

console = Console()

seen = set()
messages = deque(maxlen=300)
critical_alerts = deque(maxlen=20)

timeline = deque(maxlen=100)

user_stats = defaultdict(lambda: {
    "messages": 0,
    "risk_total": 0,
    "last_messages": deque(maxlen=10),
    "flags": defaultdict(int)
})

# EXTRA GLOBALS

global_threat = 0

user_reputation = defaultdict(lambda: 100)

ai_commentary = deque(maxlen=10)

INCIDENT_MODE = False

metrics = {
    "messages_per_minute": 0,
    "alerts_per_minute": 0
}

message_counter = 0
alert_counter = 0

SUSPICIOUS_EXT = {
    ".exe",
    ".scr",
    ".bat",
    ".cmd",
    ".ps1"
}

# =========================
# UTILS
# =========================


def sha256(data):
    return hashlib.sha256(data.encode()).hexdigest()

# =========================
# THREAT ENGINE
# =========================


def calculate_global_threat():
    global global_threat

    if not critical_alerts:
        global_threat = max(global_threat - 1, 0)
        return

    risks = [x["risk"] for x in critical_alerts]

    if risks:
        global_threat = min(
            int(sum(risks) / len(risks)),
            100
        )

# =========================
# THREAT BAR
# =========================


def threat_bar():
    filled = int(global_threat / 10)

    return (
        "█" * filled +
        "░" * (10 - filled)
    )

# =========================
# REPUTATION SYSTEM
# =========================


def update_reputation(user_id, risk):
    rep = user_reputation[user_id]

    rep -= int(risk / 10)

    rep = max(min(rep, 100), 0)

    user_reputation[user_id] = rep

# =========================
# AI COMMENTARY
# =========================


def ai_analyze(msg):
    content = msg["content"].lower()

    if "nitro" in content and "free" in content:
        ai_commentary.appendleft(
            "[AI] Possible Nitro scam detected."
        )

    if msg["risk"] >= 80:
        ai_commentary.appendleft(
            "[AI] Critical threat behavior identified."
        )

    if "@everyone" in content:
        ai_commentary.appendleft(
            "[AI] Mass mention detected."
        )

    if "http" in content and msg["risk"] >= 40:
        ai_commentary.appendleft(
            "[AI] Suspicious link behavior."
        )

# =========================
# ATTACHMENT ANALYSIS
# =========================


def analyze_attachments(m):
    flags = []

    for a in m.get("attachments", []):
        filename = a["filename"].lower()

        for ext in SUSPICIOUS_EXT:
            if filename.endswith(ext):
                flags.append(
                    "SUSPICIOUS_ATTACHMENT"
                )

    return flags

# =========================
# METRICS LOOP
# =========================


def metrics_loop():
    global message_counter
    global alert_counter

    while True:
        metrics["messages_per_minute"] = (
            message_counter
        )

        metrics["alerts_per_minute"] = (
            alert_counter
        )

        message_counter = 0
        alert_counter = 0

        time.sleep(60)

# =========================
# SEARCH SYSTEM
# =========================


def search_messages(term):
    console.print(
        f"\n[bold cyan]SEARCH[/bold cyan] {term}\n"
    )

    found = False

    for msg in messages:
        if term.lower() in msg["content"].lower():
            found = True

            console.print(
                f"[{msg['time']}] "
                f"{msg['user']} | "
                f"RISK {msg['risk']} | "
                f"{msg['content']}"
            )

    if not found:
        console.print("Nenhum resultado.")

# =========================
# EVIDENCE BROWSER
# =========================


def list_evidence():
    console.print(
        "\n[bold red]EVIDENCE FILES[/bold red]\n"
    )

    files = os.listdir(EVIDENCE_DIR)

    if not files:
        console.print("Nenhuma evidência.")
        return

    for f in files:
        console.print(f)

# =========================
# INCIDENT CONTROL
# =========================


def set_incident(state=True):
    global INCIDENT_MODE
    INCIDENT_MODE = state

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
        print("\n[+] Login automático\n")
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


def setup_panel():
    print("\n=== CONFIG ===\n")

    token = input("🔑 Token: ").strip()
    channel = input("📡 Channel ID: ").strip()

    save_config(token, channel)


def test_config(token, channel_id):
    url = f"https://discord.com/api/v10/channels/{channel_id}/messages?limit=1"

    r = requests.get(url, headers={
        "Authorization": token
    })

    return r.status_code == 200

# =========================
# ANALYSIS
# =========================


def analyze_message(content, user_id):
    risk = 0
    flags = []

    for flag, pattern in REGEX_PATTERNS.items():
        if re.search(pattern, content):
            flags.append(flag)
            risk += THREAT_WEIGHTS.get(flag, 0)

    if "@everyone" in content or "@here" in content:
        flags.append("MASS_MENTION")
        risk += THREAT_WEIGHTS["MASS_MENTION"]

    if user_id in WATCHLIST:
        flags.append("WATCHLIST")
        risk += THREAT_WEIGHTS["WATCHLIST"]

    recent = user_stats[user_id]["last_messages"]

    now = time.time()

    recent.append(now)

    recent_msgs = [x for x in recent if now - x < 10]

    if len(recent_msgs) >= 5:
        flags.append("SPAM")
        risk += THREAT_WEIGHTS["SPAM"]

    return min(risk, 100), flags

# =========================
# EVIDENCE
# =========================


def save_evidence(data):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    filename = os.path.join(EVIDENCE_DIR, f"evidence_{timestamp}.json")

    evidence = {
        "hash": sha256(json.dumps(data)),
        "timestamp": timestamp,
        "data": data
    }

    with open(filename, "w", encoding="utf-8") as f:
        json.dump(evidence, f, indent=4)

# =========================
# LOGGING
# =========================


def save_log(msg):
    try:
        logs = []

        if os.path.exists(LOG_FILE):
            with open(LOG_FILE, "r", encoding="utf-8") as f:
                logs = json.load(f)

        logs.append(msg)

        with open(LOG_FILE, "w", encoding="utf-8") as f:
            json.dump(logs, f, indent=4)

    except Exception as e:
        print("Erro log:", e)

# =========================
# DISCORD
# =========================


def fetch_messages():
    url = f"https://discord.com/api/v10/channels/{CHANNEL_ID}/messages?limit=20"

    r = requests.get(url, headers=HEADERS)

    if r.status_code == 429:
        retry = r.json().get("retry_after", 2)
        time.sleep(retry)
        return []

    return r.json()

# =========================
# SCANNER LOOP
# =========================


def scanner_loop():
    global message_counter
    global alert_counter

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

                content = m.get("content", "")
                user_id = m["author"]["id"]

                risk, flags = analyze_message(content, user_id)

                message_counter += 1

                attachment_flags = analyze_attachments(m)

                if attachment_flags:
                    flags.extend(attachment_flags)
                    risk += 40

                risk = min(risk, 100)

                msg_data = {
                    "id": m["id"],
                    "time": datetime.now().strftime("%H:%M:%S"),
                    "user": user_id,
                    "content": content,
                    "risk": risk,
                    "flags": flags
                }

                messages.append(msg_data)

                save_log(msg_data)

                ai_analyze(msg_data)

                timeline.appendleft(
                    f'[{msg_data["time"]}] {user_id}: {content[:40]}'
                )

                stats = user_stats[user_id]

                stats["messages"] += 1
                stats["risk_total"] += risk

                update_reputation(user_id, risk)

                for f in flags:
                    stats["flags"][f] += 1

                calculate_global_threat()

                if risk >= 60:
                    alert_counter += 1

                    critical_alerts.appendleft(msg_data)
                    save_evidence(msg_data)

                    try:
                        os.system("printf '\\a'")
                    except:
                        pass

                if INCIDENT_MODE:
                    save_evidence(msg_data)

            time.sleep(2)

        except Exception as e:
            print("Erro scanner:", e)
            time.sleep(2)

# =========================
# COMMANDS
# =========================


def export_report():
    report = {
        "messages": list(messages),
        "alerts": list(critical_alerts),
        "timeline": list(timeline)
    }

    with open("report.json", "w", encoding="utf-8") as f:
        json.dump(report, f, indent=4)


def investigate_user(user_id):
    console.print(f"\n[bold red]Investigação:[/bold red] {user_id}\n")

    stats = user_stats[user_id]

    console.print(f"Mensagens: {stats['messages']}")

    avg = 0

    if stats['messages']:
        avg = stats['risk_total'] / stats['messages']

    console.print(f"Risco médio: {avg:.2f}")

    console.print("Flags:")

    for k, v in stats["flags"].items():
        console.print(f" - {k}: {v}")


def comando_loop():
    while True:
        try:
            if os.path.exists(COMMAND_FILE):
                with open(COMMAND_FILE, "r") as f:
                    cmd = f.read().strip()

                os.remove(COMMAND_FILE)

                if cmd == "!exportar":
                    export_report()

                elif cmd.startswith("!investigar "):
                    investigate_user(cmd.split()[1])

                elif cmd == "!stats":
                    console.print(f"Mensagens: {len(messages)}")
                    console.print(f"Alertas: {len(critical_alerts)}")

                elif cmd.startswith("!search "):
                    term = cmd.split(maxsplit=1)[1]
                    search_messages(term)

                elif cmd == "!evidence":
                    list_evidence()

                elif cmd == "!incident start":
                    set_incident(True)

                elif cmd == "!incident stop":
                    set_incident(False)

                elif cmd == "!sair":
                    os._exit(0)

        except Exception as e:
            print("Erro comando:", e)

        time.sleep(1)

# =========================
# DASHBOARD
# =========================


def make_dashboard():
    layout = Layout()

    layout.split_column(
        Layout(name="header", size=3),
        Layout(name="main"),
        Layout(name="footer", size=3)
    )

    layout["main"].split_row(
        Layout(name="left"),
        Layout(name="right", ratio=2)
    )

    layout["left"].split_column(
        Layout(name="alerts"),
        Layout(name="timeline")
    )

    layout["header"].update(
        Panel(
            Align.center(
                "[bold cyan]CRYSTAL X FORENSIC SCANNER[/bold cyan]"
            ),
            style="green"
        )
    )

    ai_text = "\n".join(
        list(ai_commentary)[:5]
    )

    layout["alerts"].update(
        Panel(
            ai_text,
            title="AI Analysis"
        )
    )

    timeline_text = "\n".join(list(timeline)[:15])

    layout["timeline"].update(
        Panel(timeline_text, title="Timeline")
    )

    msg_table = Table(expand=True)

    msg_table.add_column("Hora")
    msg_table.add_column("User")
    msg_table.add_column("Mensagem")
    msg_table.add_column("Risk")
    msg_table.add_column("Flags")

    for msg in list(messages)[-15:]:
        risk = msg["risk"]

        style = "green"

        if risk >= 60:
            style = "red"
        elif risk >= 30:
            style = "yellow"

        msg_table.add_row(
            msg["time"],
            msg["user"],
            msg["content"][:50],
            str(risk),
            ", ".join(msg["flags"]),
            style=style
        )

    layout["right"].update(
        Panel(msg_table, title="Live Monitoring")
    )

    footer_text = (
        f"Threat: {threat_bar()} "
        f"{global_threat}% | "
        f"Msgs/min: {metrics['messages_per_minute']} | "
        f"Alerts/min: {metrics['alerts_per_minute']} | "
        f"Users: {len(user_stats)}"
    )

    layout["footer"].update(
        Panel(footer_text)
    )

    return layout

# =========================
# LIVE
# =========================


def run_dashboard():
    with Live(refresh_per_second=2, screen=True) as live:
        while True:
            live.update(make_dashboard())
            time.sleep(0.5)

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

    HEADERS = {
        "Authorization": TOKEN
    }

    threading.Thread(target=scanner_loop, daemon=True).start()
    threading.Thread(target=run_dashboard, daemon=True).start()
    threading.Thread(target=comando_loop, daemon=True).start()
    threading.Thread(target=metrics_loop, daemon=True).start()

    while True:
        time.sleep(1)

# =========================
# MENU
# =========================


def menu():
    while True:
        os.system("clear")

        print("CRYSTAL X FORENSIC\n")

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
