import requests
import time
import threading
import os
import json
from datetime import datetime, timedelta
from dateutil.parser import parse

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
# Novo: armazenamento de metadados
# =========================

metadados = []

def analisar_metadados():
    if not metadados:
        print("Nenhum dado de metadados para analisar ainda.")
        return
    
    # Converter lista de dicts em manipulação manual
    # Adicionar uma chave 'hora' para cada item
    for item in metadados:
        item['timestamp_obj'] = item['timestamp']
        # 'timestamp' já é um datetime, se não, converta aqui
        # item['timestamp_obj'] = datetime.strptime(item['timestamp'], "%Y-%m-%dT%H:%M:%S.%fZ")
        item['hora'] = item['timestamp_obj'].hour

    # Distribuição de atividades por hora
    atividades_por_hora = {}
    for item in metadados:
        h = item['hora']
        atividades_por_hora[h] = atividades_por_hora.get(h, 0) + 1

    print("\nDistribuição de atividades por hora:")
    for hour in sorted(atividades_por_hora):
        print(f"{hour}:00 - {atividades_por_hora[hour]} mensagens")
    
    # Plotagem
    import matplotlib.pyplot as plt
    horas = sorted(atividades_por_hora)
    valores = [atividades_por_hora[h] for h in horas]
    plt.figure(figsize=(10,6))
    plt.bar(horas, valores)
    plt.title('Atividades por Hora')
    plt.xlabel('Hora do dia')
    plt.ylabel('Número de mensagens')
    plt.show()

    # Atividades fora do horário (exemplo: 8h às 22h)
    horarios_atipicos = [item for item in metadados if item['hora'] < 8 or item['hora'] > 22]
    print("\nAtividades fora do horário normal:")
    for at in horarios_atipicos:
        print(f"{at['timestamp']} - {at['content']}")

    # Mudanças de localização
    locais_unicos = set(item['localizacao'] for item in metadados)
    if len(locais_unicos) > 1:
        print(f"\nMudanças de localização detectadas: {locais_unicos}")
    else:
        print("\nSem mudanças de localização detectadas.")

    # Dispositivos utilizados
    dispositivos_unicos = set(item['dispositivo'] for item in metadados)
    print(f"\nDispositivos utilizados: {dispositivos_unicos}")

def scanner_loop():
    global seen, metadados

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
                timestamp_str = m["timestamp"]
                # Converter timestamp usando dateutil.parser.parse
                timestamp = parse(timestamp_str)
                localizacao = m.get("localizacao", "Desconhecido")
                dispositivo = m.get("dispositivo", "Desconhecido")

                # Armazenar metadados
                metadados.append({
                    "id_mensagem": m["id"],
                    "user_id": uid,
                    "content": content,
                    "timestamp": timestamp,
                    "localizacao": localizacao,
                    "dispositivo": dispositivo
                })

                print(f"[{datetime.now().strftime('%H:%M:%S')}] {uid} | {content}")

            analisar_metadados()

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

    while True:
        time.sleep(1)

# =========================
# 📋 MENU PRINCIPAL
# =========================

def menu():
    while True:
        banner()
        print("[1] Start Scanner")
        print("[2] Reset Config")
        print("[3] Login Key")
        print("[4] Exit\n")
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
# 🚀 MAIN
# =========================

if __name__ == "__main__":
    menu()
