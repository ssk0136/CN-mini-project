import socket
import json
import threading
import time
from common import current_millis

SERVER_IP = "127.0.0.1"
SERVER_PORT = 9999
BUFFER_SIZE = 2048

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

player_id = None
seq = 0

# Local predicted state
x, y = 0, 0

# Server state buffer (for interpolation)
server_states = []

last_ping_time = 0


def connect():
    global player_id

    sock.sendto(json.dumps({"type": "connect"}).encode(), (SERVER_IP, SERVER_PORT))

    while player_id is None:
        data, _ = sock.recvfrom(BUFFER_SIZE)
        msg = json.loads(data.decode())

        if msg["type"] == "connect_ack":
            player_id = msg["player_id"]
            print("Connected as player", player_id)


def send_updates():
    global x, y, seq

    while True:
        seq += 1

        # Client-side prediction (simulate movement)
        x += 1
        y += 1

        packet = {
            "type": "update",
            "player_id": player_id,
            "seq": seq,
            "x": x,
            "y": y
        }

        sock.sendto(json.dumps(packet).encode(), (SERVER_IP, SERVER_PORT))
        time.sleep(0.05)


def send_ping():
    global last_ping_time

    while True:
        last_ping_time = current_millis()

        sock.sendto(json.dumps({
            "type": "ping",
            "time": last_ping_time
        }).encode(), (SERVER_IP, SERVER_PORT))

        time.sleep(2)


def receive_loop():
    while True:
        data, _ = sock.recvfrom(BUFFER_SIZE)
        msg = json.loads(data.decode())

        if msg["type"] == "state":
            server_states.append(msg)

            if len(server_states) > 10:
                server_states.pop(0)

        elif msg["type"] == "pong":
            rtt = current_millis() - msg["time"]
            print(f"Ping: {rtt} ms")


def interpolate():
    global x, y

    while True:
        if len(server_states) >= 2:
            s1 = server_states[-2]
            s2 = server_states[-1]

            t1 = s1["time"]
            t2 = s2["time"]

            now = current_millis()

            if t2 != t1:
                alpha = (now - t1) / (t2 - t1)
                alpha = max(0, min(1, alpha))

                if player_id in s1["players"] and player_id in s2["players"]:
                    x1 = s1["players"][player_id]["x"]
                    x2 = s2["players"][player_id]["x"]

                    y1 = s1["players"][player_id]["y"]
                    y2 = s2["players"][player_id]["y"]

                    x = x1 + (x2 - x1) * alpha
                    y = y1 + (y2 - y1) * alpha

                    print(f"Smoothed Position: ({x:.2f}, {y:.2f})")

        time.sleep(0.02)


if __name__ == "__main__":
    connect()

    threading.Thread(target=receive_loop, daemon=True).start()
    threading.Thread(target=send_updates, daemon=True).start()
    threading.Thread(target=send_ping, daemon=True).start()

    interpolate()
