import discord
import os
import asyncio
from datetime import datetime

# =========================
# 🔐 CONFIG
# =========================

TOKEN = "SEU_BOT_TOKEN_AQUI"

CHANNELS = []

# =========================
# 🧠 DISCORD INTENTS
# =========================

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)

# =========================
# 🎨 ASCII BANNER (FIXO)
# =========================

ASCII = r"""
  ______     ______     __  __     ______     ______   ______
 /\  ___\   /\  == \   /\ \_\ \   /\  ___\   /\__  _\ /\  __ \
 \ \ \____  \ \  __<   \ \____ \  \ \___  \  \/_/\ \/ \ \  __ \
  \ \_____\  \ \_\ \_\  \/\_____\  \/\_____\    \ \_\  \ \_\ \_\
   \/_____/   \/_/ /_/   \/_____/   \/_____/     \/_/   \/_/\/_/

            ██████╗ ██████╗ ██╗   ██╗███████╗████████╗
            ██╔══██╗██╔══██╗██║   ██║██╔════╝╚══██╔══╝
            ██║  ██║██████╔╝██║   ██║███████╗   ██║
            ██║  ██║██╔══██╗██║   ██║╚════██║   ██║
            ██████╔╝██║  ██║╚██████╔╝███████║   ██║
            ╚═════╝ ╚═╝  ╚═╝ ╚═════╝ ╚══════╝   ╚═╝

              CRYSTAL IF - FORENSIC PANEL
"""

# =========================
# 🧾 LOG
# =========================

def log_message(channel_id, author, content):
    os.makedirs("logs", exist_ok=True)

    with open(f"logs/{channel_id}.log", "a", encoding="utf-8") as f:
        f.write(f"[{datetime.now()}] {author}: {content}\n")

# =========================
# 🖥 PAINEL LIVE
# =========================

def render_panel(channel, author, content):
    os.system("clear")

    print(ASCII)
    print("\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n")

    print(f"📡 CANAL: {channel}")
    print(f"👤 AUTOR: {author}")
    print(f"💬 MENSAGEM:\n{content}")

    print("\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n")
    print("STATUS: MONITORANDO EM TEMPO REAL...")

# =========================
# 📡 EVENTO REAL TIME
# =========================

@client.event
async def on_ready():
    os.system("clear")
    print(ASCII)
    print("\n[+] CRYSTAL IF ONLINE")
    print("[+] Painel forense ativo\n")

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    channel_id = message.channel.id
    author = message.author.name
    content = message.content

    if CHANNELS and channel_id not in CHANNELS:
        return

    log_message(channel_id, author, content)
    render_panel(channel_id, author, content)

# =========================
# 🚀 START
# =========================

client.run(TOKEN)
