import socket
import threading
import time

BUFFER_SIZE = 1024

class Server:
    def __init__(self, host, port, room_name, nickname):
        self.host = host
        self.port = port
        self.room_name = room_name
        self.nickname = nickname
        self.clients = {}
        self.addresses = {}
        self.room_password = None
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def start(self):
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen()
        print(f"Server listening on {self.host}:{self.port}")

        threading.Thread(target=self.accept_connections, daemon=True).start()
        threading.Thread(target=self.server_input_thread, daemon=True).start()

    def accept_connections(self):
        while True:
            try:
                client_socket, client_address = self.server_socket.accept()
                print(f"Accepted connection from {client_address}")
                self.addresses[client_socket] = client_address[0]
                threading.Thread(target=self.handle_client, args=(client_socket,), daemon=True).start()
            except Exception as e:
                print(f"Error handling client: {e}")

    def handle_client(self, client_socket):
        try:
            # Получаем первое сообщение от клиента (никнейм, название комнаты и пароль)
            welcome_message = client_socket.recv(BUFFER_SIZE).decode('utf-8')
            if welcome_message:
                parts = welcome_message.split(' ', 2)
                if len(parts) < 2:
                    print(f"Invalid welcome message from {self.addresses[client_socket]}")
                    client_socket.close()
                    return

                nickname = parts[0]
                client_room_name = parts[1]
                password = parts[2] if len(parts) > 2 else ""

                # Проверяем пароль
                if self.room_password and self.room_password != password:
                    print(f"Invalid password from {self.addresses[client_socket]}")
                    client_socket.send("Invalid password".encode('utf-8'))
                    client_socket.close()
                    return

                # Проверяем, не хост ли это (по IP)
                if self.addresses[client_socket] == '127.0.0.1':
                    self.room_name = client_room_name

                print(f"Room name: {self.room_name}, Password: {password}")

                # Добавляем клиента в список
                self.clients[client_socket] = nickname
                print(f"Welcome message from {self.addresses[client_socket]}: {welcome_message}")

                # Отправляем клиенту название комнаты
                client_socket.send(f"#ROOMNAME#{self.room_name}".encode('utf-8'))
                time.sleep(0.25)
                self.broadcast(f"Welcome to the chat, {nickname}!", client_socket)
                self.update_user_list()

            while True:
                message = client_socket.recv(BUFFER_SIZE).decode('utf-8')
                if message:
                    print(f"Received message from {self.addresses[client_socket]}: {message}")
                    if message.startswith("#CHANGEROOMNAME#") and self.addresses[client_socket] == '127.0.0.1':
                        new_name = message[len("#CHANGEROOMNAME#"):].strip()
                        if new_name:
                            self.room_name = new_name
                            self.broadcast(f"Room name changed to: {self.room_name}")
                    else:
                        self.broadcast(message, client_socket)
                else:
                    print(f"Client {self.addresses[client_socket]} disconnected")
                    break
        except Exception as e:
            print(f"Error receiving message: {e}")
        finally:
            self.remove_client(client_socket)

    def remove_client(self, client_socket):
        client_socket.close()
        if client_socket in self.clients:
            del self.clients[client_socket]
        if client_socket in self.addresses:
            del self.addresses[client_socket]
        self.update_user_list()

    def broadcast(self, message, source_socket=None):
        for client_socket in list(self.clients.keys()):
            if client_socket != source_socket:
                try:
                    client_socket.send(message.encode('utf-8'))
                except Exception as e:
                    print(f"Error sending message: {e}")
                    self.remove_client(client_socket)

    def update_user_list(self):
        user_list = [f"{nickname} - {ip}" for client_socket, nickname in self.clients.items() if (ip := self.addresses.get(client_socket))]
        self.broadcast(f"#USERS_IP#\n" + "\n".join(user_list))

    def server_input_thread(self):
        while True:
            try:
                message = input()
                if message:
                    self.broadcast(f"{self.nickname}: {message}")
            except KeyboardInterrupt:
                print("\nServer shutting down.")
                break

    def set_room_password(self, password):
        self.room_password = password
