import socket
import json
import threading
import time
from common import current_millis, TICK_RATE

SERVER_IP = "0.0.0.0"
SERVER_PORT = 9999
BUFFER_SIZE = 2048

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((SERVER_IP, SERVER_PORT))

clients = {}
next_player_id = 1
lock = threading.Lock()

print(f"Server running on {SERVER_IP}:{SERVER_PORT}")


def register_client(addr):
    global next_player_id

    with lock:
        player_id = next_player_id
        next_player_id += 1

        clients[player_id] = {
            "addr": addr,
            "x": 0,
            "y": 0,
            "last_seq": -1,
            "last_seen": current_millis()
        }

    return player_id


def handle_message(data, addr):
    try:
        msg = json.loads(data.decode())

        if msg["type"] == "connect":
            player_id = register_client(addr)

            response = {
                "type": "connect_ack",
                "player_id": player_id
            }
            sock.sendto(json.dumps(response).encode(), addr)
            return

        player_id = msg.get("player_id")
        if player_id not in clients:
            return

        client = clients[player_id]

        # Packet ordering (handles packet loss/out-of-order)
        seq = msg.get("seq", 0)
        if seq <= client["last_seq"]:
            return

        client["last_seq"] = seq
        client["last_seen"] = current_millis()

        if msg["type"] == "update":
            client["x"] = msg["x"]
            client["y"] = msg["y"]

        elif msg["type"] == "ping":
            sock.sendto(json.dumps({
                "type": "pong",
                "time": msg["time"]
            }).encode(), addr)

    except Exception as e:
        print("Error:", e)


def broadcast_state():
    state = {
        "type": "state",
        "time": current_millis(),
        "players": {
            pid: {"x": c["x"], "y": c["y"]}
            for pid, c in clients.items()
        }
    }

    data = json.dumps(state).encode()

    for c in clients.values():
        sock.sendto(data, c["addr"])


def receive_loop():
    while True:
        data, addr = sock.recvfrom(BUFFER_SIZE)
        threading.Thread(target=handle_message, args=(data, addr), daemon=True).start()


def broadcast_loop():
    while True:
        broadcast_state()
        time.sleep(1 / TICK_RATE)


if __name__ == "__main__":
    threading.Thread(target=receive_loop, daemon=True).start()
    broadcast_loop()
