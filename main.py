import socket
import threading
from utils import save_nickname, load_nickname, save_ip_address


HOST = '0.0.0.0'
PORT = 36500
nickname = ""





def start_server(host, port, nickname):
    import server
    server.start_server(host, port, nickname)

def connect_to_server(ip, port,nickname):
    import client
    client.connect_to_server(ip, port, nickname)

def main():
    nickname = load_nickname()
    if not nickname:
        save_nickname()

    while True:
        choice = input("Enter 'create' to start a new server or 'join' to connect to an existing server: ").strip().lower()
        if choice == 'create':
            start_server(HOST, PORT, nickname)
            break
        elif choice == 'join':
            ip = input("Enter server IP to join: ").strip()
            if ip:
                connect_to_server(ip, PORT, nickname)
                break
            else:
                print("Invalid IP address. Please enter a valid IP address.")
        else:
            print("Invalid choice. Please enter 'create' or 'join'.")

if __name__ == "__main__":
    main()
