import discord
import os
import json
import asyncio
from datetime import datetime, timedelta

# =========================
# 🔐 ARQUIVOS
# =========================

KEY_FILE = "chave.json"
CONFIG_FILE = "config.json"

# =========================
# 🔑 CHAVES (exemplo)
# =========================

CHAVES_VALIDAS = {
    "CRYSTAL-IF-001": 1,
    "TESTE-123": 0.01
}

# =========================
# 🧠 ESTADO
# =========================

TOKEN = None
CANAL_MONITORADOS = []

# =========================
# 🎨 ASCII
# =========================

ASCII = r"""
  ______     ______     __  __     ______     ______   ______
 /\  ___\   /\  == \   /\ \_\ \   /\  ___\   /\__  _\ /\  __ \
 \ \ \____  \ \  __<   \ \____ \  \ \___  \  \/_/\ \/ \ \  __ \
  \ \_____\  \ \_\ \_\  \/\_____\  \/\_____\    \ \_\  \ \_\ \_\
   \/_____/   \/_/ /_/   \/_____/   \/_____/     \/_/   \/_/\/_/

              CRYSTAL IF - PAINEL FORENSE
"""

# =========================
# 🔐 SISTEMA DE CHAVE
# =========================

def salvar_chave(chave, expiracao):
    with open(CHAVE_FILE, "w") as f:
        json.dump({"chave": chave, "expiracao": expiracao.timestamp()}, f)

def carregar_chave():
    try:
        return json.load(open(CHAVE_FILE))
    except:
        return None

def chave_valida(dados):
    if not dados:
        return False
    return datetime.now().timestamp() < dados["expiracao"]

def login_chave():
    dados = carregar_chave()

    if dados and chave_valida(dados):
        print("\n[+] Chave ativa (auto-login)\n")
        return True

    chave = input("🔐 Chave: ").strip()

    if chave in CHAVES_VALIDAS:
        expiracao = datetime.now() + timedelta(days=CHAVES_VALIDAS[chave])
        salvar_chave(chave, expiracao)
        print("\n[+] Chave aceita\n")
        return True

    print("\n[-] Chave inválida\n")
    return False

# =========================
# ⚙️ SISTEMA DE CONFIGURAÇÃO
# =========================

def salvar_config(token, canais):
    with open(CONFIG_FILE, "w") as f:
        json.dump({
            "token": token,
            "canais": canais
        }, f)

def carregar_config():
    try:
        return json.load(open(CONFIG_FILE))
    except:
        return None

def resetar_config():
    if os.path.exists(CONFIG_FILE):
        os.remove(CONFIG_FILE)
    print("\n[+] Configuração resetada\n")

def configurar():
    print("\n=== CONFIGURAÇÃO ===\n")
    token = input("Token do Bot: ").strip()
    canais = input("Canais (separados por vírgula): ").split(",")

    canais = [int(c.strip()) for c in canais]

    salvar_config(token, canais)
    print("\n[+] Configuração salva\n")

# =========================
# 🧾 LOGS
# =========================

def log_mensagem(canal, autor, conteudo):
    os.makedirs("logs", exist_ok=True)

    with open(f"logs/{canal}.log", "a", encoding="utf-8") as f:
        f.write(f"[{datetime.now()}] {autor}: {conteudo}\n")

# =========================
# 🖥 PAINEL
# =========================

def renderizar(canal, autor, conteudo):
    os.system("clear")
    print(ASCII)
    print("\n━━━━━━━━━━━━━━━━━━━━━━━\n")
    print(f"📡 Canal: {canal}")
    print(f"👤 Autor: {autor}")
    print(f"💬 Mensagem:\n{conteudo}")
    print("\n━━━━━━━━━━━━━━━━━━━━━━━\n")
    print("STATUS: MONITORAMENTO AO VIVO")

# =========================
# 🤖 CLIENTE DISCORD
# =========================

class SelfBot(discord.Client):
    def __init__(self):
        super().__init__(intents=discord.Intents.all())

    async def on_ready(self):
        os.system("clear")
        print(ASCII)
        print("\n[+] CRYSTAL IF ONLINE\n")

    async def on_message(self, mensagem):
        # Processar apenas mensagens do próprio bot e canais monitorados
        if mensagem.author != self.user or (CANAL_MONITORADOS and mensagem.channel.id not in CANAL_MONITORADOS):
            return

        log_mensagem(mensagem.channel.id, mensagem.author.name, mensagem.content)
        renderizar(mensagem.channel.id, mensagem.author.name, mensagem.content)

# =========================
# 🚀 INICIAR MONITOR
# =========================

def iniciar_monitor():
    global TOKEN, CANAL_MONITORADOS

    config = carregar_config()

    if not config:
        configurar()
        config = carregar_config()

    TOKEN = config["token"]
    CANAL_MONITORADOS = config["canais"]

    cliente = SelfBot()
    cliente.run(TOKEN, reconnect=True)

# =========================
# 📋 MENU
# =========================

def menu():
    while True:
        os.system("clear")
        print(ASCII)
        print("\n[1] Iniciar Monitor")
        print("[2] Resetar Config")
        print("[3] Login Chave")
        print("[4] Sair\n")

        opcao = input(">> ").strip()

        if opcao == "1":
            if login_chave():
                iniciar_monitor()

        elif opcao == "2":
            resetar_config()

        elif opcao == "3":
            login_chave()

        elif opcao == "4":
            break

        else:
            print("Inválido")

# =========================
# 🚀 PRINCIPAL
# =========================

if __name__ == "__main__":
    menu()
