import socket
import json
import threading
import time
import tkinter as tk

SERVER_IP = "10.5.18.9"  #change this
SERVER_PORT = 9999
BUFFER_SIZE = 1024

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

player_id = None
players = {}

# Local position
x, y = 250, 250
seq = 0


# -------- CONNECT -------- #

def connect():
    global player_id

    sock.sendto(json.dumps({"type": "join"}).encode(), (SERVER_IP, SERVER_PORT))

    while player_id is None:
        data, _ = sock.recvfrom(BUFFER_SIZE)
        msg = json.loads(data.decode())

        if msg["type"] == "welcome":
            player_id = msg["id"]
            print("Connected as Player", player_id)


# -------- NETWORK -------- #

def send_loop():
    global x, y, seq

    last = (x, y)

    while True:
        if player_id and (x, y) != last:
            seq += 1
            sock.sendto(json.dumps({
                "type": "move",
                "id": player_id,
                "x": x,
                "y": y,
                "seq": seq
            }).encode(), (SERVER_IP, SERVER_PORT))

            last = (x, y)

        time.sleep(0.01)


def receive_loop():
    global players

    while True:
        data, _ = sock.recvfrom(BUFFER_SIZE)
        msg = json.loads(data.decode())

        if msg["type"] == "state":
            players = msg["players"]


# -------- UI -------- #

root = tk.Tk()
root.title("UDP Multiplayer Game")

canvas = tk.Canvas(root, width=500, height=500, bg="black")
canvas.pack()


def draw():
    canvas.delete("all")

    for pid, pos in players.items():
        px, py = pos["x"], pos["y"]

        color = "red" if int(pid) == player_id else "white"

        canvas.create_oval(px-10, py-10, px+10, py+10, fill=color)
        canvas.create_text(px, py-15, text=f"P{pid}", fill="yellow")

    root.after(50, draw)


# -------- CONTROLS -------- #

def move(event):
    global x, y

    speed = 10

    if event.keysym == "Up":
        y -= speed
    elif event.keysym == "Down":
        y += speed
    elif event.keysym == "Left":
        x -= speed
    elif event.keysym == "Right":
        x += speed


root.bind("<KeyPress>", move)


# -------- MAIN -------- #

def start():
    connect()

    threading.Thread(target=send_loop, daemon=True).start()
    threading.Thread(target=receive_loop, daemon=True).start()

    draw()
    root.mainloop()


if __name__ == "__main__":
    start()
