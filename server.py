import socket
import threading
from utils import save_ip_address
from main import HOST, PORT

BUFFER_SIZE = 1024

clients = {}
addresses = {}
room_passwords = {}  # Хранение паролей для комнат

def start_server(host, port, nickname):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((host, port))
    server_socket.listen()
    print(f"Server listening on {host}:{port}")

    def receive_messages(broadcast):
        while True:
            try:
                client_socket, client_address = server_socket.accept()
                print(f"Accepted connection from {client_address}")
                save_ip_address(client_address[0] + " - Client")
                addresses[client_socket] = client_address[0]
                threading.Thread(target=handle_client, args=(client_socket, broadcast), daemon=True).start()
            except Exception as e:
                print(f"Error handling client: {e}")

    def handle_client(client_socket, broadcast):
        try:
            welcome_message = client_socket.recv(BUFFER_SIZE).decode('utf-8')
            if welcome_message:
                nickname, room_name, password = welcome_message.split(' ', 2)
                if room_name in room_passwords and password != room_passwords[room_name]:
                    client_socket.send("Invalid password".encode('utf-8'))
                    client_socket.close()
                    return

                clients[client_socket] = nickname
                print(f"Welcome message from {addresses[client_socket]}: {welcome_message}")
                broadcast(f"Welcome to the chat, {nickname}!", client_socket)
                update_user_list()  # Обновляем список пользователей

            while True:
                message = client_socket.recv(BUFFER_SIZE).decode('utf-8')
                if message:
                    print(f"Received message from {addresses[client_socket]}: {message}")
                    broadcast(message, client_socket)
                else:
                    print(f"Client {addresses[client_socket]} disconnected")
                    break
        except Exception as e:
            print(f"Error receiving message: {e}")
        finally:
            client_socket.close()
            if client_socket in clients:
                del clients[client_socket]
            if client_socket in addresses:
                del addresses[client_socket]
            update_user_list()  # Обновляем список пользователей при отключении

    def broadcast(message, source_socket=None):
        for client_socket in list(clients.keys()):
            if client_socket != source_socket:
                try:
                    client_socket.send(message.encode('utf-8'))
                    print(f"Sent message to {addresses[client_socket]}: {message}")
                except Exception as e:
                    print(f"Error sending message: {e}")
                    client_socket.close()
                    if client_socket in clients:
                        del clients[client_socket]
                    if client_socket in addresses:
                        del addresses[client_socket]
                    update_user_list()  # Обновляем список пользователей при ошибке

    def update_user_list():
        user_list = [f"{nickname} - {ip}" for client_socket, nickname in clients.items() if (ip := addresses.get(client_socket))]
        broadcast("\n".join(user_list))

    def server_input_thread(broadcast, nickname):
        while True:
            try:
                message = input()
                if message:
                    broadcast(f"{nickname}: {message}")
            except KeyboardInterrupt:
                print("\nServer shutting down.")
                break

    # Start server and input threads
    threading.Thread(target=receive_messages, args=(broadcast,), daemon=True).start()
    server_input_thread(broadcast, nickname)



def set_room_password(room_name, password):
    room_passwords[room_name] = password
