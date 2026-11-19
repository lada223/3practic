import socket
import threading
import json
from crypto import xor_encrypt, xor_decrypt

HOST = "127.0.0.1"


NAME = "Client1"

with open("clients.json", "r", encoding="utf-8") as f:
    clients = json.load(f)

ROUTER_PORTS = {"Router1": 5001, "Router2": 5002, "Router3": 5003, "WirelessRouter": 5004}
PORT = ROUTER_PORTS[clients[NAME]["router"]]
PROTOCOL = clients[NAME]["protocol"]

MY_KEY = input("Введите ключ шифрования (например, 123): ")

if PROTOCOL == "TCP":
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((HOST, PORT))
else:
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.bind((HOST, 0))  # Свой порт для ответов

# Регистрация
if PROTOCOL == "TCP":
    s.send(f"REGISTER|{NAME}".encode())
    print(s.recv(1024).decode())
else:
    s.sendto(f"REGISTER|{NAME}".encode(), (HOST, PORT))
    print(s.recvfrom(1024)[0].decode())


def listen():
    while True:
        try:
            data = s.recv(4096) if PROTOCOL == "TCP" else s.recvfrom(4096)[0]
            msg = data.decode()
            if msg.startswith("SRP|DATA|"):
                parts = msg.split("|")
                payload = parts[7]
                try:
                    print(f"\n📩  Получено: {xor_decrypt(payload, MY_KEY)}")
                except:
                    print(f"\n⚠️  Ошибка расшифровки! (неверный ключ)")
        except:
            break


threading.Thread(target=listen, daemon=True).start()

print(f"[{NAME}] Готов. Введите данные для отправки.")
while True:
    target = input("Кому: ")
    prio = input("Приоритет (NORMAL/HIGH): ").upper()
    text = input("Текст: ")

    if text.lower() == "exit": break

    enc_text = xor_encrypt(text, MY_KEY)
    packet = f"SRP|DATA|{NAME}|{target}|{PROTOCOL}|{prio}|1|{enc_text}"

    if PROTOCOL == "TCP":
        s.send(packet.encode())
    else:
        s.sendto(packet.encode(), (HOST, PORT))
    print(f"Отправлено (HEX): {enc_text}")