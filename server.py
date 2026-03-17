import socket
import threading
from datetime import datetime

Conntd_clients = {}
lock = threading.Lock()

#server log
def log_server(event):
    with open("server_log.txt", "a", encoding="utf-8") as f:
        time = datetime.now().strftime("%H:%M:%S")
        f.write("[" + time + "] " + event + "\n")

#chat history
def log_chat(msg):
    with open("chat_history.txt", "a", encoding="utf-8") as f:
        time = datetime.now().strftime("%H:%M:%S")
        f.write("[" + time + "] " + msg + "\n")

def broadcast_msg(msg, sender_sckt=None):
    # Send message to all connected clients
    for client_sckt in list(Conntd_clients):
        if client_sckt != sender_sckt:
            try:
                client_sckt.send(msg.encode("utf-8"))
            except:
                client_sckt.close()
                if client_sckt in Conntd_clients:
                    del Conntd_clients[client_sckt]

# Handle each client
def handle_client(client_sckt, adrs):
    username = None
    print("Client Connected:-", adrs)
    log_server("Client Connected:- " + str(adrs))
    
    try:
        while True:
            msg = client_sckt.recv(1024).decode("utf-8")
            if not msg:
                break
            
            parts = msg.split(" ", 1)  #divide msg from 1st space
            cmd = parts[0]
            
            #JOIN cmd
            if cmd == "JOIN":
                username = parts[1].strip()
                
                with lock:
                    if username in Conntd_clients.values():
                        client_sckt.send("Username is already taken.".encode("utf-8"))
                        continue
                    Conntd_clients[client_sckt] = username

                join_msg = "## " + username + " joined the chat ##"
                print(join_msg)
                log_server(join_msg)
                broadcast_msg(join_msg)
            
            #MSG cmd
            elif cmd == "MSG":
                if len(parts)>1:
                    text = parts[1]
                else:
                    continue
                time = datetime.now().strftime("%H:%M")
                chat_msg = "[" + time + "] " + username + ": " + text

                print(chat_msg)
                log_chat(chat_msg)
                broadcast_msg(chat_msg, client_sckt)
            
            #QUIT cmd
            elif cmd == "QUIT":
                break
            
            elif cmd == "USERS":
                with lock:
                    user_list = ", ".join(Conntd_clients.values())
                All_Users = "All users: " + user_list
                client_sckt.send(All_Users.encode("utf-8"))
            
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
            print(leave_msg)
            log_server(leave_msg)
            broadcast_msg(leave_msg)     

def start_server():
    srvr_sckt = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  #Address Family use IPv4 and use TCP
    
    srvr_sckt.bind(("0.0.0.0", 8000))
    
    srvr_sckt.listen(10)
    
    print("Chat server started on the Port:-", 8000)
    log_server("Chat server started on the Port:- 8000")
    
    while True:
        client_sckt, adrs = srvr_sckt.accept()
        thread = threading.Thread(target = handle_client, args=(client_sckt,adrs))
        thread.start()

if __name__ == "__main__":
    start_server()
