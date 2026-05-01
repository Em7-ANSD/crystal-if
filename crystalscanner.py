import discord
import requests
import time
import threading
import os
import json
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
CHANNEL_ID = None
HEADERS = {}

user_profiles = {}
seen = set()

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
    token = input("🔑 Token (de usuário ou bot): ").strip()
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
    print(BLUE + "CRYSTAL IF - SCANNER SYSTEM\n" + RESET)

# =========================
# 📡 SCANNER
# =========================
def fetch_messages(limit=20):
    url = f"https://discord.com/api/v10/channels/{CHANNEL_ID}/messages?limit={limit}"
    return requests.get(url, headers=HEADERS).json()

def scanner_loop():
    global seen
    print("\n[+] Scanner iniciado...\n")
    while True:
        try:
            msgs = fetch_messages()
            if not isinstance(msgs, list):
                print("Erro ao buscar mensagens ou nenhuma mensagem retornada.")
                time.sleep(3)
                continue
            for m in msgs:
                if m["id"] in seen:
                    continue
                seen.add(m["id"])
                uid = m["author"]["id"]
                content = m.get("content", "")
                print(f"[{datetime.now().strftime('%H:%M:%S')}] {uid} | {content}")
            time.sleep(3)
        except Exception as e:
            print(f"Erro no scanner: {e}")
            time.sleep(3)

# =========================
# 🚀 START SCANNER SAFE
# =========================
def start_scanner():
    global TOKEN, CHANNEL_ID, HEADERS
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
    threading.Thread(target=scanner_loop, daemon=True).start()
    threading.Thread(target=comando_input, daemon=True).start()
    while True:
        time.sleep(1)

# =========================
# 🧠 Thread de comando para enviar mensagem enquanto o scanner roda
# =========================
def comando_input():
    global TOKEN, CHANNEL_ID
    while True:
        cmd = input()
        if cmd.startswith("!enviar "):
            mensagem = cmd[len("!enviar "):]
            enviar_mensagem_discord(mensagem)
        elif cmd.lower() == "!sair":
            print("Encerrando comando input...")
            break
        elif cmd.lower() == "!raid":
            print("Tentando executar raid...")
            print("Envie a mensagem '!raid' no servidor para ativar o raid.")
        else:
            print("Comando não reconhecido.")

# =========================
# 📝 Função para enviar mensagem ao Discord
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
    if r.status_code in [200, 201]:
        print("Mensagem enviada com sucesso!")
    else:
        print(f"Erro ao enviar mensagem: {r.status_code}")
        print(r.text)

# =========================
# =========================
# AQUI COMEÇA A PARTE DE COMANDOS DA NOVA VERSÃO (SELF-BOT) QUE VOCÊ ENVIOU
# =========================
