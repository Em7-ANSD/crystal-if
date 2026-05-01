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

user_profiles = {}
seen = set()
messages = []  # Para armazenar mensagens recebidas para o painel

console = Console()

# =========================
# Risk Engine para Score de Risco
# =========================

class RiskEngine:
    def __init__(self):
        self.users = {}
        self.time_window_seconds = 10
        self.spam_threshold = 3
        self.short_msg_threshold = 3
        self.short_msg_length = 10

    def process_message(self, user_id, content):
        now = datetime.now()
        user_data = self.users.get(user_id, {
            'messages': collections.deque(maxlen=50),
            'short_msgs': collections.Counter(),
            'risk_score': 0
        })

        # Atualizar mensagens recentes
        user_data['messages'].append((now, content))
        # Mensagens curtas
        if len(content) <= self.short_msg_length:
            user_data['short_msgs'][content] += 1

        # Spam: mensagens repetidas
        message_texts = [msg[1] for msg in user_data['messages']]
        last_msgs = message_texts[-self.spam_threshold:]
        is_spam = False
        if len(last_msgs) >= self.spam_threshold and len(set(last_msgs)) == 1:
            is_spam = True

        # Flood: muitas mensagens na janela de tempo
        recent_msgs = [msg for msg in user_data['messages']
                       if (now - msg[0]).total_seconds() <= self.time_window_seconds]
        is_flood = len(recent_msgs) >= self.spam_threshold

        # Mensagens curtas repetidas
        short_repeats = sum(1 for count in user_data['short_msgs'].values() if count >= self.short_msg_threshold)

        # Atualiza risco
        risk_delta = 0
        if is_spam:
            risk_delta += 3
        if is_flood:
            risk_delta += 3
        if short_repeats > 0:
            risk_delta += 2

        user_data['risk_score'] = min(max(user_data['risk_score'] + risk_delta, 0), 10)
        self.users[user_id] = user_data
        return user_data['risk_score']

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
    print(BLUE + "CRYSTAL IF - SCANNER SYSTEM\n" + RESET)

# =========================
# 📡 SCANNER
# =========================

def fetch_messages(limit=20):
    url = f"https://discord.com/api/v10/channels/{CHANNEL_ID}/messages?limit={limit}"
    return requests.get(url, headers=HEADERS).json()

# =========================
# Scanner thread que atualiza a lista de mensagens
# =========================

def scanner_loop():
    global seen, messages, risk_engine, investigation_engine
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
                now_str = datetime.now().strftime("%H:%M:%S")
                # Processar risco
                risco = risk_engine.process_message(uid, content)
                # Análise investigativa
                insights = investigation_engine.analyze_message(uid, content, datetime.now())
                # Adicionar na lista de mensagens para painel
                messages.append({
                    "time": now_str,
                    "id": m["id"],
                    "content": content,
                    "risk": risco,
                    "insights": insights
                })
                # Limitar tamanho da lista
                if len(messages) > 100:
                    messages.pop(0)
            time.sleep(3)
        except Exception as e:
            print(f"Erro no scanner: {e}")
            time.sleep(3)

# =========================
# Enviar mensagem ao Discord
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
# Thread de comandos via input
# =========================

def comando_input():
    while True:
        try:
            cmd = input()
            if cmd.startswith("!enviar "):
                mensagem = cmd[len("!enviar "):]
                enviar_mensagem_discord(mensagem)
            elif cmd.lower() == "!sair":
                print("Encerrando comando input...")
                os._exit(0)
            elif cmd.lower() == "!relatorio":
                # Gera e exibe o relatório de investigação
                relatorio = investigation_engine.generate_report()
                print(relatorio)
        except Exception as e:
            print(f"Erro na entrada de comando: {e}")

# =========================
# Criar o painel com rich
# =========================

def make_layout():
    layout = Layout()
    layout.split_column(
        Layout(name="header", size=3),
        Layout(name="body", ratio=1),
        Layout(name="footer", size=3)
    )

    # Cabeçalho
    layout["header"].update(Panel("[bold cyan]🔍 crystalX - Discord Scanner Forense[/bold cyan]", style="bold green"))

    # Corpo com mensagens
    table = Table(expand=True)
    table.add_column("Hora", style="cyan", no_wrap=True)
    table.add_column("ID", style="magenta")
    table.add_column("Mensagem", style="white")
    table.add_column("Risco", style="red")
    for msg in messages[-20:]:
        risco_str = str(msg.get('risk', 0))
        insights_str = "\n".join(msg.get('insights', []))
        table.add_row(msg['time'], msg['id'], msg['content'], risco_str)
    layout["body"].update(Panel(table, title="Mensagens Recentes"))

    # Rodapé com instruções
    footer_text = "[bold yellow]Comandos:[/bold yellow] [green]!enviar mensagem[/green], [red]!sair[/red], [blue]!relatorio[/blue]"
    layout["footer"].update(Panel(footer_text))
    return layout

def run_dashboard():
    with Live(refresh_per_second=4, screen=True) as live:
        while True:
            live.update(make_layout())
            time.sleep(0.5)

# =========================
# Função principal
# =========================

def start_scanner():
    global TOKEN, CHANNEL_ID, HEADERS, risk_engine, investigation_engine
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

    # Instanciar RiskEngine e InvestigationEngine
    risk_engine = RiskEngine()
    investigation_engine = InvestigationEngine()

    # Thread do scanner
    threading.Thread(target=scanner_loop, daemon=True).start()
    # Thread do painel
    threading.Thread(target=run_dashboard, daemon=True).start()

    # Aqui fica na thread principal, assim você consegue digitar normalmente
    comando_input()

# =========================
# Menu principal
# =========================

def menu():
    while True:
        banner()
        print("[1] Start Scanner")
        print("[2] Reset Config")
        print("[3] Login Key")
        print("[4] Sair")
        print("\nDigite '!enviar Sua mensagem' para enviar uma mensagem ao Discord enquanto o scanner roda.")
        print("Digite '!sair' no comando de entrada para parar o comando.")
        print("Digite '!relatorio' para gerar o relatório completo de investigação.\n")
        op = input(">> ").strip()

        if op == "1":
            if login():
                start_scanner()
        elif op == "2":
            reset_config()
        elif op == "3":
            login()
        elif op == "4":
            print("\nSaindo...\n")
            break
        else:
            print("\nOpção inválida\n")
            time.sleep(1)

# =========================
# MAIN
# =========================

if __name__ == "__main__":
    menu()
