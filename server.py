import re
import socket
import threading
import os
import gc
import utils
import time
import asyncio

BUFFER_SIZE = 1024

class Server:
    def __init__(self, host, port, room_name, nickname, password):
        self.host = host
        self.port = port
        self.room_name = room_name
        self.nickname = nickname
        self.clients = {}
        self.addresses = {}
        self.room_password = password
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.stop_event = threading.Event()

        self.command_list = {
            "#CHANGEROOMNAME#": self.handle_room_name,
            "#MESSAGE#": self.handle_message,
        }


    def start(self):
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen()
        print(f"###Server listening on {self.host}:{self.port}")

        # Запуск асинхронной функции accept_connections
        asyncio.run(self.accept_connections())


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

                client_socket.send(f"#MESSAGE#Welcome to the chat, {nickname}!".encode('utf-8'))

                self.update_user_list()

            # Для работы с файлами
            file_accepted = False
            file_paths = None
            is_txt_file = False
            #
            while not self.stop_event.is_set():
                print(f"Столько потоков задействовано :{threading.active_count()}")
                message = client_socket.recv(BUFFER_SIZE * 10000)

                try:
                    message = message.decode('utf-8')
                    decoded_message = True
                except UnicodeDecodeError:
                    decoded_message = False

                if message and decoded_message and not is_txt_file:
                    print(f"SERVER Received message from {self.addresses[client_socket]}: {message}")
                    self.process_message(message, client_socket)

                    if message.startswith("FILE:"):
                        parts = message.split(":")
                        sender_nickname = parts[1]
                        file_name = parts[2]
                        file_size = int(parts[3])
                        file_counts = int(parts[4])
                        file_accepted = True
                        file_thread = None
                        received_size = 0

                        if file_name.lower().endswith(".txt") or file_name.lower().endswith(".java"):
                            is_txt_file = True

                        if file_paths:
                            file_paths.append(file_name)
                        else:
                            file_paths = [file_name]

                        # Проверка, существует ли файл на сервере
                        if utils.file_exists(file_name, file_size):
                            # Отправляем сообщение клиенту, что файл уже существует
                            client_socket.send(f"#FILE_EXISTS#{file_name}".encode('utf-8'))
                            print(f" FILE COUNTS {file_counts} FILE PATHS {file_paths}")
                            if file_counts == len(file_paths):
                                threading.Thread(target=self.send_files, args=(client_socket, file_paths, sender_nickname), daemon=True).start()
                                file_paths = None


                elif message and not decoded_message or is_txt_file:
                    if file_thread:
                        file_thread.join()

                    if not is_txt_file:
                        file_thread = threading.Thread(target=utils.save_file_chunk, args=(file_name, message,), daemon=True)
                        file_thread.start()
                    else:
                        utils.receive_file_txt(message, file_name)

                    received_size += len(message)
                    if received_size >= file_size and file_accepted:
                        if file_thread:
                            file_thread.join()

                        if not is_txt_file:
                            finalizing_file = threading.Thread(target=utils.finalize_file, args=(file_name,), daemon=True)
                            finalizing_file.start()
                            finalizing_file.join()

                        if file_counts == len(file_paths):
                            threading.Thread(target=self.send_files, args=(client_socket, file_paths, sender_nickname), daemon=True).start()
                            file_paths = None


                        file_accepted = False
                        is_txt_file = False
                        received_size = 0

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


    def send_files(self,client_socket, file_paths, nickname):
        file_paths = list(file_paths)
        for file_path in file_paths:
            self.send_file_thread(client_socket, file_path, len(file_paths), nickname)

    def send_file_thread(self, client_socket, file_name, file_counts, nickname):
        try:

            chunk_size = 1024 * 10000  # 10 MB
            file_path = f"Save/HOST/{file_name}"
            file_size = os.path.getsize(file_path)

            # Пересылка файла другим клиентам
            for client in self.clients:
                if True:
                    client.send(f"FILE:{nickname}:{file_name}:{file_size}:{file_counts}".encode('utf-8'))

                    # Отправляем файл чанками
                    with open(file_path, "rb") as f:
                        sent_size = 0
                        while sent_size < file_size:
                            chunk = f.read(chunk_size)
                            if not chunk:
                                break  # Если больше нечего читать, выходим из цикла

                            client.sendall(chunk)
                            sent_size += len(chunk)
                            del chunk
                            time.sleep(0.01)

            time.sleep(1.5)     # В случае чего увеличить задержку(зависит от качества соединения)
            gc.collect()
        except Exception as e:
            print(f"Ошибка при получении файла: {e}")

    def process_message(self, message, client_socket):
        # Модифицируем регулярное выражение для захвата содержимого команд, включая переносы строк
        commands = re.findall(r'(#\w+#)(.*?)((?=#\w+#)|$)', message, re.DOTALL)

        for command_tuple in commands:
            command = command_tuple[0].strip()  # Команда (#ROOMNAME#, #USERS_IP# и т.д.)
            data = command_tuple[1].strip()  # Данные после команды

            handler = self.command_list.get(command)
            if handler:
                # Вызов обработчика с данными и дополнительным параметром
                handler(data, client_socket)  # Передаем нужные значения
            else:
                print(f"Unrecognized command: {command}")

    def handle_message(self, message, client_socket):
        self.broadcast(f"#MESSAGE#{self.clients[client_socket]}: {message}", client_socket)

    def handle_room_name(self, data, client_socket):
        if self.addresses[client_socket] in {self.host, "127.0.0.1"}:
            new_name = data
            if new_name:
                self.room_name = new_name
                utils.save_room_settings(self.room_name, self.room_password)
                self.broadcast(f"#ROOMNAME#{self.room_name}")
                self.broadcast(f"Room name changed to: {self.room_name}")