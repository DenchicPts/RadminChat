import socket
import threading
import time
import os
import gc

import database
import utils
import asyncio

class Client:
    def __init__(self, host, port, nickname, room_name="", password=""):
        self.host = host
        self.port = port
        self.nickname = nickname
        self.room_name = room_name
        self.password = password
        self.socket = None
        self.message_callback = None
        self.update_user_list = None
        self.window_name_change = None
        self.file_callback = None
        self.authenticated = False

        print(host)

    def connect(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((self.host, self.port))
        self.send_message(f"{self.nickname }*{self.room_name}*{self.password}")

    def start_listening(self, callback, update_list, name_change, receive_file_gui):
        self.message_callback = callback
        self.update_user_list = update_list
        self.window_name_change = name_change
        self.file_callback = receive_file_gui
        threading.Thread(target=self.listen_for_messages, daemon=True).start()

    def listen_for_messages(self):
        while True:
            try:
                message = self.socket.recv(1024 * 10000)
                try:
                    message = message.decode('utf-8')
                    decoded_message = True
                except UnicodeDecodeError:
                    decoded_message = False


                if message and decoded_message:
                    print(f"CLIENT Received {message}")
                    if "Invalid password" in message:
                        print("Invalid password")
                        self.socket.close()
                        break
                    elif message.startswith("#ROOMNAME#"):
                        self.room_name = message[len("#ROOMNAME#"):]
                        self.window_name_change()
                        self.authenticated = True  # Аутентификация успешна
                        database.save_connection(True, self.host, self.room_name)
                        # print(f"Connected to room: {self.room_name}")

                    elif message.startswith("#USERS_IP#"):
                        users = message[len("#USERS_IP#"):].strip().split("\n")
                        if self.message_callback:
                            database.parse_users_info(users)
                            self.update_user_list(users)

                    elif message.startswith("FILE:"):
                        parts = message.split(":")
                        sender_nickname = parts[1]  # Получаем никнейм отправителя
                        file_name = parts[2]
                        file_size = int(parts[3])
                        received_size = 0
                        file_data = b""

                    elif message.startswith("#MESSAGE#"):
                        message_to_send = message[len("#MESSAGE#"):].strip()
                        self.message_callback(message_to_send)

                elif message and not decoded_message:
                    file_data += message
                    received_size += len(message)
                    if received_size >= file_size:
                        utils.file_save(file_name, file_data, self.host)
                        del file_data, received_size
                        file_path = f"Save\\{self.host}"
                        if self.file_callback:
                            self.file_callback(file_name, file_path, sender_nickname)

                else:
                    break
            except Exception as e:
                print(f"Error receiving message: {e}")
                break

    def send_message(self, message):
        if self.socket:
            self.socket.send(message.encode('utf-8'))

    def disconnect(self):
        # Останавливаем прослушивание и закрываем сокет
        self.listening = False
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
            self.socket = None

    def connect_with_timeout(self, timeout=3):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.settimeout(1)  # Устанавливаем тайм-аут в 1 секунду на попытку подключения

        self.authenticated = False
        for _ in range(timeout):
            try:
                self.socket.connect((self.host, self.port))
                self.authenticated = True
                break
            except (socket.timeout, socket.error) as e:
                print(f"Connection attempt failed: {e}")
                time.sleep(1)

        self.socket.settimeout(None)  # Сбрасываем тайм-аут после подключения
        if self.authenticated:
            self.send_message(f"{self.nickname}*{self.room_name}*{self.password}")
            message = self.socket.recv(1024).decode('utf-8')
            print(f"Connect with timeout ///{message}")
            if message == "Invalid password":
                self.authenticated = False

        return self.authenticated


    # Заготовка под большое количество файлов
    def send_file(self, file_path):
        # Отправка файла в отдельном потоке
        threading.Thread(target=self.send_file_thread, args=(file_path,), daemon=True).start()



    def send_file_thread(self, file_path):
        try:
            file_name = os.path.basename(file_path)
            file_size = os.path.getsize(file_path)
            chunk_size = 1024 * 10000 # 10 MBait speed


            # Отправка заголовка с информацией о файле
            file_info_message = f"FILE:{self.nickname}:{file_name}:{file_size}"
            self.socket.send(file_info_message.encode('utf-8'))
            time.sleep(0.1)

            # Отправляем файл чанками
            with open(file_path, "rb") as f:
                sent_size = 0
                while sent_size < file_size:
                    # Читаем кусок данных
                    chunk = f.read(chunk_size)
                    if not chunk:
                        break  # Если больше нечего читать, выходим из цикла

                    # Отправляем чанк
                    self.socket.sendall(chunk)
                    sent_size += len(chunk)
                    # Небольшая задержка, чтобы избежать забивки сокета
                    del chunk
                    time.sleep(0.01)

            gc.collect()

            print(f"Файл {file_name} отправлен на сервер.")
        except Exception as e:
            print(f"Ошибка при отправке файла: {e}")

