import requests
import time
import random
import threading
import os

# =========================
# 🔐 CONFIG
# =========================

TOKEN = "SEU_TOKEN_AQUI"
CHANNEL_ID = "SEU_CHANNEL_ID"

HEADERS = {
    "Authorization": TOKEN
}

user_profiles = {}
seen = set()

# =========================
# 🎨 ASCII BANNER
# =========================

RED = "\033[91m"
WHITE = "\033[97m"
RESET = "\033[0m"

art = r"""
______________________.___. _________________________  .____
\_   ___ \______   \__  |   |/   _____/\__    ___/  _  \ |    |
/    \  \/|       _//   |   |\_____  \   |    | /  /_\  \|    |
\     \___|    |   \\____   |/        \  |    |/    |    \    |___
 \______  /____|_  // ______/_______  /  |____|\____|__  /_______ \
        \/       \/ \/              \/                 \/        \/

________  .___  ________.___________________  .____
\______ \ |   |/  _____/|   \__    ___/  _  \ |    |
 |    |  \|   /   \  ___|   | |    | /  /_\  \|    |
 |    `   \   \    \_\  \   | |    |/    |    \    |___
/_______  /___|\______  /___| |____|\____|__  /_______ \
        \/            \/                    \/        \/

___________________ _____________________ _______    _________.____________
\_   _____/\_____  \\______   \_   _____/ \      \  /   _____/|   \_   ___ \
 |    __)   /   |   \|       _/|    __)_  /   |   \ \_____  \ |   /    \  \/
 |     \   /    |    \    |   \|        \/    |    \/        \|   \     \____
 \___  /   \_______  /____|_  /_______  /\____|__  /_______  /|___|\______  /
     \/            \/       \/        \/         \/        \/             \/

.___ ___________   _______________ ____________________.___  ________    ________________________ __________
|   |\      \   \ /   /\_   _____//   _____/\__    ___/|   |/  _____/   /  _  \__    ___/\_____  \\______   \
|   |/   |   \   Y   /  |    __)_ \_____  \   |    |   |   /   \  ___  /  /_\  \|    |    /   |   \|       _/
|   /    |    \     /   |        \/        \  |    |   |   \    \_\  \/    |    \    |   /    |    \    |   \
|___\____|__  /\___/   /_______  /_______  /  |____|   |___|\______  /\____|__  /____|   \_______  /____|_  /
            \/                 \/        \/                        \/         \/                 \/       \/
"""

def colorize(text):
    out = ""
    for ch in text:
        if ch != " ":
            out += random.choice([RED, WHITE]) + ch
        else:
            out += " "
    return out + RESET

def banner_loop():
    while True:
        os.system("clear")
        print(colorize(art))
        print("\n[ CRYSTAL | IF - SCANNER ONLINE ]\n")
        time.sleep(0.2)

# =========================
# 📡 DISCORD SCANNER
# =========================

def fetch_messages(limit=20):
    url = f"https://discord.com/api/v10/channels/{CHANNEL_ID}/messages?limit={limit}"
    r = requests.get(url, headers=HEADERS)

    if r.status_code != 200:
        print("Erro:", r.status_code)
        return []

    return r.json()

def analyze(content):
    flags = []
    c = content.lower()

    if len(c) > 200:
        flags.append("LONG")

    if c.count("!") > 5:
        flags.append("SPAM")

    return flags

def update(uid, flags):
    if uid not in user_profiles:
        user_profiles[uid] = {"count": 0, "flags": []}

    user_profiles[uid]["count"] += 1
    user_profiles[uid]["flags"].extend(flags)

def risk(uid):
    p = user_profiles.get(uid, {})
    return min(len(p.get("flags", [])) * 5 + p.get("count", 0), 100)

def scanner_loop():
    global seen

    while True:
        msgs = fetch_messages()

        for m in msgs:
            if m["id"] in seen:
                continue

            seen.add(m["id"])

            uid = m["author"]["id"]
            content = m.get("content", "")

            flags = analyze(content)
            update(uid, flags)

            print(f"{uid} | risk={risk(uid)} | {content[:40]}")

        time.sleep(3)

# =========================
# 🚀 MAIN
# =========================

def main():
    print("[+] CRYSTAL | Investigadora Forense do Discord iniciando...")

    threading.Thread(target=banner_loop, daemon=True).start()
    threading.Thread(target=scanner_loop, daemon=True).start()

    while True:
        time.sleep(1)

if __name__ == "__main__":
    main()
