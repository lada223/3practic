import socket
import json
import threading
from routing import build_graph, shortest_path

HOST = "127.0.0.1"


NAME = "Router1"

ROUTER_PORTS = {"Router1": 5001, "Router2": 5002, "Router3": 5003, "WirelessRouter": 5004}
PORT = ROUTER_PORTS[NAME]

with open("network.json", "r", encoding="utf-8") as f:
    network = json.load(f)
with open("clients.json", "r", encoding="utf-8") as f:
    clients = json.load(f)

graph = build_graph(network)
connected_clients = {}  # Кто подключен именно к ЭТОМУ роутеру


def forward(next_router, packet):
    """Пересылаем пакет соседнему роутеру по TCP"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((HOST, ROUTER_PORTS[next_router]))
        s.send(packet.encode())
        s.close()
        print(f"[{NAME}] → {next_router}: переслал.")
    except Exception as e:
        print(f"[{NAME}] Ошибка пересылки: {e}")


def process(packet):
    parts = packet.split("|")
    if len(parts) < 8 or parts[0] != "SRP": return

    source, target = parts[2], parts[3]
    print(f"\n[{NAME}] ПОЛУЧЕН ПАКЕТ: {source} -> {target}")

    # 1. Если получатель подключен к нам — отдаем ему
    if target in connected_clients:
        c = connected_clients[target]
        if c["protocol"] == "TCP":
            c["socket"].send(packet.encode())
        else:
            c["socket"].sendto(packet.encode(), c["addr"])
        print(f"[{NAME}] Доставлено локальному клиенту {target}")
        return

    # 2. Если не локальный — ищем путь
    src_router = clients[source]["router"]
    dst_router = clients[target]["router"]

    path, cost = shortest_path(graph, src_router, dst_router)
    print(f"[{NAME}] Маршрут: {' -> '.join(path)} (cost={cost})")

    if NAME in path:
        idx = path.index(NAME)
        if idx < len(path) - 1:
            forward(path[idx + 1], packet)


def handle_conn(conn, addr):
    sender = None
    try:
        reg = conn.recv(1024).decode()
        if reg.startswith("REGISTER|"):
            sender = reg.split("|")[1]
            connected_clients[sender] = {"socket": conn, "protocol": "TCP"}
            conn.send(b"OK")
            print(f"[{NAME}] TCP-клиент: {sender}")

        while True:
            data = conn.recv(4096)
            if not data: break
            process(data.decode())
    except:
        pass
    finally:
        if sender in connected_clients: del connected_clients[sender]
        conn.close()


def tcp_server():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind((HOST, PORT))
    s.listen()
    print(f"[{NAME}] TCP слушает {PORT}...")
    while True:
        conn, addr = s.accept()
        threading.Thread(target=handle_conn, args=(conn, addr), daemon=True).start()


def udp_server():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.bind((HOST, PORT))
    print(f"[{NAME}] UDP слушает {PORT}...")
    while True:
        data, addr = s.recvfrom(4096)
        msg = data.decode()
        if msg.startswith("REGISTER|"):
            sender = msg.split("|")[1]
            connected_clients[sender] = {"socket": s, "addr": addr, "protocol": "UDP"}
            s.sendto(b"OK", addr)
            print(f"[{NAME}] UDP-клиент: {sender}")
        else:
            process(msg)


if __name__ == "__main__":
    threading.Thread(target=tcp_server, daemon=True).start()
    udp_server()