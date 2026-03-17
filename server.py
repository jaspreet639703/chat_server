import socket
import threading
import os
from datetime import datetime
from http.server import BaseHTTPRequestHandler, HTTPServer

Conntd_clients = {}
lock = threading.Lock()


# ---------------- HTTP HEALTH SERVER ----------------
class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write(b"Chat server running")


def start_http_server(port):
    httpd = HTTPServer(("0.0.0.0", port), HealthHandler)
    httpd.serve_forever()


# ---------------- SERVER LOG ----------------
def log_server(event):
    with open("server_log.txt", "a", encoding="utf-8") as f:
        time = datetime.now().strftime("%H:%M:%S")
        f.write("[" + time + "] " + event + "\n")


# ---------------- CHAT LOG ----------------
def log_chat(msg):
    with open("chat_history.txt", "a", encoding="utf-8") as f:
        time = datetime.now().strftime("%H:%M:%S")
        f.write("[" + time + "] " + msg + "\n")


# ---------------- BROADCAST ----------------
def broadcast_msg(msg, sender_sckt=None):

    with lock:
        clients = list(Conntd_clients.keys())

    for client_sckt in clients:
        if client_sckt != sender_sckt:
            try:
                client_sckt.send(msg.encode("utf-8"))
            except:
                with lock:
                    if client_sckt in Conntd_clients:
                        del Conntd_clients[client_sckt]
                client_sckt.close()


# ---------------- CLIENT HANDLER ----------------
def handle_client(client_sckt, adrs):

    username = None
    print("Client Connected:", adrs)

    try:
        while True:

            msg = client_sckt.recv(1024).decode("utf-8")

            if not msg:
                break

            parts = msg.split(" ", 1)
            cmd = parts[0]

            if cmd == "JOIN":

                username = parts[1].strip()

                with lock:
                    if username in Conntd_clients.values():
                        client_sckt.send("Username taken".encode())
                        continue

                    Conntd_clients[client_sckt] = username

                join_msg = "## " + username + " joined the chat ##"
                print(join_msg)
                broadcast_msg(join_msg)

            elif cmd == "MSG":

                text = parts[1]
                time = datetime.now().strftime("%H:%M")

                chat_msg = "[" + time + "] " + username + ": " + text

                print(chat_msg)
                log_chat(chat_msg)

                broadcast_msg(chat_msg, client_sckt)

            elif cmd == "USERS":

                with lock:
                    user_list = ", ".join(Conntd_clients.values())

                client_sckt.send(("All users: " + user_list).encode())

            elif cmd == "QUIT":
                break

    except:
        pass

    finally:

        with lock:
            if client_sckt in Conntd_clients:
                username = Conntd_clients[client_sckt]
                del Conntd_clients[client_sckt]

        client_sckt.close()

        if username:
            leave_msg = "## " + username + " left the chat ##"
            broadcast_msg(leave_msg)


# ---------------- TCP CHAT SERVER ----------------
def start_chat_server():

    tcp_port = 9000   # chat server port

    srvr_sckt = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srvr_sckt.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    srvr_sckt.bind(("0.0.0.0", tcp_port))
    srvr_sckt.listen(10)

    print("Chat server started on port:", tcp_port)

    while True:

        client_sckt, adrs = srvr_sckt.accept()

        thread = threading.Thread(
            target=handle_client,
            args=(client_sckt, adrs),
            daemon=True
        )

        thread.start()


# ---------------- MAIN ----------------
if __name__ == "__main__":

    port = int(os.environ.get("PORT", 10000))

    # start HTTP server (Render check)
    threading.Thread(
        target=start_http_server,
        args=(port,),
        daemon=True
    ).start()

    # start TCP chat server
    start_chat_server()
