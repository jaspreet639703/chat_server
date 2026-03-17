import socket
import threading
import os
from datetime import datetime

# store connected clients
Conntd_clients = {}
lock = threading.Lock()


# ---------------- SERVER LOG ----------------
def log_server(event):
    with open("server_log.txt", "a", encoding="utf-8") as f:
        time = datetime.now().strftime("%H:%M:%S")
        f.write(f"[{time}] {event}\n")


# ---------------- CHAT HISTORY ----------------
def log_chat(msg):
    with open("chat_history.txt", "a", encoding="utf-8") as f:
        time = datetime.now().strftime("%H:%M:%S")
        f.write(f"[{time}] {msg}\n")


# ---------------- BROADCAST ----------------
def broadcast_msg(msg, sender_sckt=None):

    msg = msg + "\n"

    with lock:
        for client_sckt in list(Conntd_clients):

            if client_sckt != sender_sckt:

                try:
                    client_sckt.send(msg.encode("utf-8"))

                except:
                    client_sckt.close()

                    if client_sckt in Conntd_clients:
                        del Conntd_clients[client_sckt]


# ---------------- HANDLE CLIENT ----------------
def handle_client(client_sckt, adrs):

    username = None

    print("Client Connected:", adrs)
    log_server("Client Connected: " + str(adrs))

    try:

        while True:

            msg = client_sckt.recv(1024).decode("utf-8")

            if not msg:
                break

            parts = msg.split(" ", 1)
            cmd = parts[0]

            # ---------- JOIN ----------
            if cmd == "JOIN":

                username = parts[1].strip()

                with lock:

                    if username in Conntd_clients.values():

                        client_sckt.send(
                            "Username already taken\n".encode("utf-8")
                        )
                        continue

                    Conntd_clients[client_sckt] = username

                join_msg = f"## {username} joined the chat ##"

                print(join_msg)
                log_server(join_msg)

                broadcast_msg(join_msg)

            # ---------- MESSAGE ----------
            elif cmd == "MSG":

                if len(parts) > 1:
                    text = parts[1]
                else:
                    continue

                time = datetime.now().strftime("%H:%M")

                chat_msg = f"[{time}] {username}: {text}"

                print(chat_msg)

                log_chat(chat_msg)

                broadcast_msg(chat_msg, client_sckt)

            # ---------- USERS ----------
            elif cmd == "USERS":

                with lock:
                    user_list = ", ".join(Conntd_clients.values())

                msg = "All users: " + user_list + "\n"

                client_sckt.send(msg.encode("utf-8"))

            # ---------- QUIT ----------
            elif cmd == "QUIT":
                break

    except Exception as e:
        print("Client error:", e)

    finally:

        with lock:

            if client_sckt in Conntd_clients:

                username = Conntd_clients[client_sckt]

                del Conntd_clients[client_sckt]

        client_sckt.close()

        if username:

            leave_msg = f"## {username} left the chat ##"

            print(leave_msg)

            log_server(leave_msg)

            broadcast_msg(leave_msg)


# ---------------- SERVER START ----------------
def start_server():

    port = int(os.environ.get("PORT", 8000))

    srvr_sckt = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    srvr_sckt.bind(("0.0.0.0", port))

    srvr_sckt.listen(50)

    print("Chat server started on port:", port)

    log_server("Chat server started on port: " + str(port))

    while True:

        client_sckt, adrs = srvr_sckt.accept()

        thread = threading.Thread(
            target=handle_client,
            args=(client_sckt, adrs),
            daemon=True
        )

        thread.start()


if __name__ == "__main__":
    start_server()
