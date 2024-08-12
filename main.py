import socket
import threading
from utils import save_nickname, load_nickname


HOST = '0.0.0.0'
PORT = 36500
nickname = ""


def save_ip_address(ip_address, file_path='ips.txt'):
    try:
        # Читаем существующие IP-адреса из файла
        with open(file_path, 'r') as file:
            existing_ips = file.read().splitlines()
    except FileNotFoundError:
        # Если файла еще нет, считаем, что существующих IP-адресов нет
        existing_ips = []

    # Проверяем, есть ли уже такой IP-адрес в файле
    if ip_address not in existing_ips:
        with open(file_path, 'a') as file:
            file.write(ip_address + '\n')


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
