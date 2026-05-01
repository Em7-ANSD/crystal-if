import curses
import threading
import time
import requests
import json
import os
from datetime import datetime, timedelta

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

user_profiles = {}
seen = set()
messages = []  # Lista de mensagens recebidas

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

def reset_config():
    if os.path.exists(CONFIG_FILE):
        os.remove(CONFIG_FILE)
    print("\n[+] Config resetada\n")

def setup_panel():
    print("\n=== PAINEL DE CONFIGURAÇÃO ===\n")
    token = input("🔑 Token (de usuário): ").strip()
    channel = input("📡 Channel ID: ").strip()
    save_config(token, channel)
    print("\n[+] Config salva\n")

def test_config(token, channel_id):
    url = f"https://discord.com/api/v10/channels/{channel_id}/messages?limit=1"
    headers = {"Authorization": token}
    r = requests.get(url, headers=headers)
    return r.status_code == 200

# =========================
# 🎨 BANNER
# =========================

BLUE = "\033[34m"
RESET = "\033[0m"

def banner():
    os.system("clear")
    print(BLUE + "CRYSTAL IF - HACKER PANEL\n" + RESET)

# =========================
# 📡 SCANNER
# =========================

def fetch_messages(limit=20):
    url = f"https://discord.com/api/v10/channels/{CHANNEL_ID}/messages?limit={limit}"
    return requests.get(url, headers=HEADERS).json()

def scanner_loop():
    global messages, seen
    while True:
        try:
            msgs = fetch_messages()
            if not isinstance(msgs, list):
                time.sleep(3)
                continue
            for m in msgs:
                if m["id"] in seen:
                    continue
                seen.add(m["id"])
                uid = m["author"]["id"]
                content = m.get("content", "")
                timestamp = datetime.now().strftime('%H:%M:%S')
                messages.append(f"{timestamp} {uid}: {content}")
            time.sleep(3)
        except:
            time.sleep(3)

# =========================
# Enviar mensagem
# =========================

def enviar_mensagem_discord(mensagem):
    global TOKEN, CHANNEL_ID
    url = f"https://discord.com/api/v10/channels/{CHANNEL_ID}/messages"
    headers = {
        "Authorization": TOKEN,
        "Content-Type": "application/json"
    }
    data = {
        "content": mensagem
    }
    r = requests.post(url, headers=headers, json=data)
    return r.status_code in [200, 201]

# =========================
# Interface curses
# =========================

def run_dashboard(stdscr):
    global messages
    curses.curs_set(0)
    stdscr.nodelay(True)
    height, width = stdscr.getmaxyx()

    while True:
        stdscr.clear()

        # Banner
        stdscr.addstr(0, 2, "🖥️  CRYSTAL IF - HACKER PANEL", curses.A_BOLD)

        # Status
        stdscr.addstr(2, 2, "[*] Scanner: Ativo", curses.color_pair(2))
        stdscr.addstr(3, 2, f"[*] Mensagens recebidas: {len(messages)}")

        # Últimas mensagens
        stdscr.addstr(5, 2, "Últimas mensagens:")
        for i, msg in enumerate(messages[-10:]):
            if 6 + i < height - 4:
                stdscr.addstr(6 + i, 4, msg[:width - 8])

        # Instruções
        stdscr.addstr(height - 3, 2, "Comando: (use '!enviar mensagem' ou '!sair')", curses.A_BOLD)

        stdscr.refresh()

        try:
            key = stdscr.getkey()
            if key == 'q':
                break
        except:
            pass
        time.sleep(0.5)

# Thread de entrada de comandos
def command_input(stdscr):
    global TOKEN, CHANNEL_ID
    while True:
        curses.echo()
        stdscr.addstr(curses.LINES - 2, 2, "Digite comando: ")
        stdscr.clrtoeol()
        cmd = stdscr.getstr(curses.LINES - 2, 18).decode('utf-8')
        curses.noecho()

        if cmd.startswith("!enviar "):
            mensagem = cmd[len("!enviar "):]
            sucesso = enviar_mensagem_discord(mensagem)
            if sucesso:
                messages.append(f"{datetime.now().strftime('%H:%M:%S')} [Você]: {mensagem}")
        elif cmd.lower() == "!sair":
            break
        time.sleep(0.1)

# =========================
# Main
# =========================

def main():
    global TOKEN, CHANNEL_ID, HEADERS, seen, messages

    # Carregar ou configurar
    config = load_config()
    if not config:
        print("\n[-] Nenhuma config encontrada\n")
        setup_panel()
        config = load_config()

    if not test_config(config["token"], config["channel_id"]):
        print("\n[-] Config inválida ou token quebrado\n")
        setup_panel()
        config = load_config()

    TOKEN = config["token"]
    CHANNEL_ID = config["channel_id"]
    HEADERS = {"Authorization": TOKEN}
    seen = set()
    messages = []

    # Inicia thread do scanner
    threading.Thread(target=scanner_loop, daemon=True).start()

    # Inicia curses
    curses.wrapper(run_curses)

def run_curses(stdscr):
    # Thread do painel
    threading.Thread(target=run_dashboard, args=(stdscr,), daemon=True).start()
    # Thread de comandos
    command_input(stdscr)

if __name__ == "__main__":
    main()
