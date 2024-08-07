import socket
import threading
import os

BUFFER_SIZE = 1024
IP_FILE = 'ip_list.txt'

clients = {}
addresses = {}

def load_ip_list():
    if os.path.exists(IP_FILE):
        with open(IP_FILE, 'r') as file:
            return [line.strip() for line in file if line.strip()]
    return []

def save_ip_list(ip_list):
    with open(IP_FILE, 'w') as file:
        for ip in ip_list:
            file.write(f"{ip}\n")

def receive_messages(server_socket, update_user_list, broadcast):
    while True:
        try:
            client_socket, client_address = server_socket.accept()
            print(f"Accepted connection from {client_address}")  # Debugging
            addresses[client_socket] = client_address[0]
            threading.Thread(target=handle_client, args=(client_socket, broadcast, update_user_list), daemon=True).start()
        except Exception as e:
            print(f"Error handling client: {e}")  # Debugging

def handle_client(client_socket, broadcast, update_user_list):
    try:
        # Принятие приветственного сообщения от клиента
        welcome_message = client_socket.recv(BUFFER_SIZE).decode('utf-8')
        if welcome_message:
            nickname = welcome_message.split(' ')[0]
            clients[client_socket] = nickname
            print(f"Welcome message from {addresses[client_socket]}: {welcome_message}")  # Debugging
            welcome_text = f"Добро пожаловать в канал, {nickname}!"
            broadcast(welcome_text)  # Отправляем приветственное сообщение всем
            update_user_list()

        while True:
            message = client_socket.recv(BUFFER_SIZE).decode('utf-8')
            if message:
                print(f"Received message from {addresses[client_socket]}: {message}")  # Debugging
                broadcast(message)  # Отправляем сообщение всем
            else:
                print(f"Client {addresses[client_socket]} disconnected")
                break
    except Exception as e:
        print(f"Error receiving message: {e}")  # Debugging
    finally:
        client_socket.close()
        if client_socket in clients:
            del clients[client_socket]
        if client_socket in addresses:
            del addresses[client_socket]
        update_user_list()

def broadcast(message, source_socket=None):
    # Отправляем сообщение всем клиентам, кроме отправителя

    for client_socket in list(clients.keys()):
        if client_socket != source_socket:
            try:
                client_socket.send(message.encode('utf-8'))
                print(f"Sent message to {addresses[client_socket]}: {message}")  # Debugging
            except Exception as e:
                print(f"Error sending message to {addresses[client_socket]}: {e}")  # Debugging
                client_socket.close()
                if client_socket in clients:
                    del clients[client_socket]
                if client_socket in addresses:
                    del addresses[client_socket]

    # Обновляем чат на сервере
    if source_socket is None:
        # Для сообщений, отправленных сервером (например, приветственное сообщение)
        print(f"Server broadcast: {message}")

def start_server(host, port, update_user_list, broadcast):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((host, port))
    server_socket.listen()
    print(f"Server listening on {host}:{port}")  # Debugging
    threading.Thread(target=receive_messages, args=(server_socket, update_user_list, broadcast), daemon=True).start()
