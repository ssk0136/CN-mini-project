import socket
import json
import threading
import time

SERVER_IP = "0.0.0.0"
SERVER_PORT = 9999
BUFFER_SIZE = 1024

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((SERVER_IP, SERVER_PORT))

clients = {}  # player_id -> data
next_id = 1
lock = threading.Lock()

print("Server started on port", SERVER_PORT)


def handle_message(data, addr):
    global next_id

    try:
        msg = json.loads(data.decode())

        # -------- NEW CLIENT -------- #
        if msg["type"] == "join":
            with lock:
                player_id = next_id
                next_id += 1

                clients[player_id] = {
                    "addr": addr,
                    "x": 250,
                    "y": 250,
                    "last_seq": 0,
                    "time": time.time()
                }

            print(f"New player joined: Player {player_id} from {addr}")

            sock.sendto(json.dumps({
                "type": "welcome",
                "id": player_id
            }).encode(), addr)

        # -------- MOVEMENT -------- #
        elif msg["type"] == "move":
            pid = msg["id"]

            if pid in clients:
                # Ignore old packets
                if msg["seq"] > clients[pid]["last_seq"]:
                    clients[pid]["last_seq"] = msg["seq"]

                    old_x = clients[pid]["x"]
                    old_y = clients[pid]["y"]

                    clients[pid]["x"] = msg["x"]
                    clients[pid]["y"] = msg["y"]
                    clients[pid]["time"] = time.time()

                    print(f"Player {pid} moved from ({old_x}, {old_y}) -> ({msg['x']}, {msg['y']})")

    except:
        pass


def receive_loop():
    while True:
        data, addr = sock.recvfrom(BUFFER_SIZE)
        threading.Thread(target=handle_message, args=(data, addr), daemon=True).start()


def broadcast_loop():
    while True:
        # -------- REMOVE DEAD CLIENTS -------- #
        now = time.time()
        to_remove = []

        for pid, c in clients.items():
            if now - c["time"] > 5:
                to_remove.append(pid)

        for pid in to_remove:
            print(f"Player {pid} disconnected")
            del clients[pid]

        # -------- SEND STATE -------- #
        state = {
            "type": "state",
            "players": {
                pid: {"x": c["x"], "y": c["y"]}
                for pid, c in clients.items()
            }
        }

        data = json.dumps(state).encode()

        for c in clients.values():
            sock.sendto(data, c["addr"])

        time.sleep(0.05)


threading.Thread(target=receive_loop, daemon=True).start()
broadcast_loop()
