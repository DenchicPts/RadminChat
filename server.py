import socket
import threading
import os
import gc
import utils
import time
import asyncio

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
        self.stop_event = threading.Event()

    def start(self):
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen()
        print(f"###Server listening on {self.host}:{self.port}")

        # Запуск асинхронной функции accept_connections
        asyncio.run(self.accept_connections())
        asyncio.run(self.server_input_thread())


    def stop(self):
        self.stop_event.set()
        self.server_socket.close()
        print("Server is shutdown")
        for client_socket in list(self.clients.keys()):
            self.remove_client(client_socket)


    async def accept_connections(self):
        #loop = asyncio.get_running_loop()
        while not self.stop_event.is_set():
            try:
                client_socket, client_address = self.server_socket.accept()
                # print(f"SERVER Accepted connection from {client_address}")
                self.addresses[client_socket] = client_address[0]
                threading.Thread(target=self.handle_client, args=(client_socket,), daemon=True).start()
            except Exception as e:
                print(f"SERVER Error handling client: {e}")

    def handle_client(self, client_socket):
        try:
            # Получаем первое сообщение от клиента (никнейм, название комнаты и пароль)
            welcome_message = client_socket.recv(BUFFER_SIZE).decode('utf-8')
            # print(welcome_message)
            if welcome_message:
                parts = welcome_message.split('*')
                if len(parts) < 2:
                    print(f"SERVER Invalid welcome message from {self.addresses[client_socket]}")
                    client_socket.close()
                    return

                nickname = parts[0]
                client_room_name = parts[1]
                password = parts[2] if len(parts) > 2 else ""

                # Проверяем пароль
                if self.room_password and self.room_password != password:
                    print(f"SERVER Invalid password from {self.addresses[client_socket]}")
                    client_socket.send("Invalid password".encode('utf-8'))
                    client_socket.close()
                    return
                else:
                    print(f"SERVER Success connection from {self.addresses[client_socket]}")
                    client_socket.send("#MESSAGE#Success connection".encode('utf-8'))
                    time.sleep(0.20)

                # Проверяем, не хост ли это (по IP)
                if self.addresses[client_socket] in {self.host, "127.0.0.1"}:
                    self.room_name = client_room_name

                print(f"SERVER Room name: {self.room_name}, Password: {password}")

                # Добавляем клиента в список
                self.clients[client_socket] = nickname
                # print(f"SERVER Welcome message from {self.addresses[client_socket]}: {welcome_message}")

                # Отправляем клиенту название комнаты
                client_socket.send(f"#ROOMNAME#{self.room_name}".encode('utf-8'))
                utils.save_room_settings(self.room_name, password)
                time.sleep(0.25)

                self.broadcast(f"#MESSAGE#Welcome to the chat, {nickname}!", client_socket)
                self.update_user_list()

            while not self.stop_event.is_set():
                gc.collect()

                message = client_socket.recv(BUFFER_SIZE * 10000)
                try:
                    message = message.decode('utf-8')
                    decoded_message = True
                except UnicodeDecodeError:
                    decoded_message = False

                if message and decoded_message:
                    print(f"SERVER Received message from {self.addresses[client_socket]}: {message}")
                    if message.startswith("#CHANGEROOMNAME#") and self.addresses[client_socket] in {self.host, "127.0.0.1"}:
                        new_name = message[len("#CHANGEROOMNAME#"):].strip()
                        if new_name:
                            self.room_name = new_name
                            utils.save_room_settings(self.room_name, self.room_password)
                            self.broadcast(f"#ROOMNAME#{self.room_name}")
                            self.broadcast(f"Room name changed to: {self.room_name}")

                    elif message.startswith("FILE:"):
                        parts = message.split(":")
                        sender_nickname = parts[1]  # Получаем никнейм отправителя
                        file_name = parts[2]
                        file_size = int(parts[3])
                        received_size = 0
                        file_data = b""

                    elif message.startswith("#MESSAGE#"):
                        message_to_send = message[len("#MESSAGE#"):].strip()
                        self.broadcast(f"#MESSAGE#{self.clients[client_socket]}: {message_to_send}", client_socket)

                elif message and not decoded_message:
                    file_data += message
                    received_size += len(message)
                    if received_size >= file_size:
                        utils.file_save(file_name, file_data)
                        threading.Thread(target=self.send_file, args=(client_socket, file_name, file_size, file_data, sender_nickname)).start()
                        del file_data, received_size

                elif message:
                    del message

                else:
                    print(f"###Client {self.addresses[client_socket]} disconnected")
                    break
        except Exception as e:
            print(f"Error receiving message: {e}")
        finally:
            print(f"###Client {self.addresses[client_socket]} disconnected")
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
                    print(f"###Error sending message: {e}")
                    self.remove_client(client_socket)

    def update_user_list(self):
        user_list = [f"{nickname} - {ip}" for client_socket, nickname in self.clients.items() if (ip := self.addresses.get(client_socket))]
        self.broadcast(f"#USERS_IP#\n" + "\n".join(user_list))

    async def server_input_thread(self):
        while not self.stop_event.is_set():
            try:
                message = input()
                if message:
                    self.broadcast(f"{self.nickname}: {message}")
            except KeyboardInterrupt:
                print("\nServer shutting down.")
                break

    def set_room_password(self, password):
        self.room_password = password

    def send_file(self, client_socket, file_name, file_size, file_data, nickname):
        try:
            # Пересылка файла другим клиентам
            for client in self.clients:
                if not client == client_socket:
                    client.send(f"FILE:{nickname}:{file_name}:{file_size}".encode('utf-8'))
                    client.sendall(file_data)

            del file_data
            gc.collect()

        except Exception as e:
            print(f"Ошибка при получении файла: {e}")
