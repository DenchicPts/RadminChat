import socket
import threading
import time
import os
import gc
import database
import utils

class Client:
    def __init__(self, host, port, nickname, room_name="", password=""):
        self.host = host
        self.port = port
        self.nickname = nickname
        self.room_name = room_name
        self.password = password
        self.socket = None
        # GUI Function
        self.message_callback = None
        self.update_user_list = None
        self.window_name_change = None
        self.file_callback = None
        # Boolean
        self.authenticated = False
        self.stop_file_transfer = False

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
        file_accepted = False
        is_txt_file = False
        while True:
            try:

                message = self.socket.recv(1024 * 10000)
                try:
                    message = message.decode('utf-8')
                    decoded_message = True
                except UnicodeDecodeError:
                    decoded_message = False


                if message and decoded_message and not is_txt_file:
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
                        file_counts = int(parts[4])
                        received_size = 0
                        file_accepted = True
                        file_thread = None

                        if file_name.lower().endswith(".txt") or file_name.lower().endswith(".java"):
                            is_txt_file = True

                    elif message.startswith("#MESSAGE#"):
                        message_to_send = message[len("#MESSAGE#"):].strip()
                        self.message_callback(message_to_send)

                    elif message.startswith("#FILE_EXISTS#"):
                        # Сервер сообщил, что файл уже существует
                        file_name = message[len("#FILE_EXISTS#"):].strip()
                        print(f"Файл {file_name} уже существует на сервере. Передача отменена.")
                        self.stop_file_transfer = True  # Устанавливаем флаг для остановки передачи



                elif message and not decoded_message or is_txt_file:
                    if file_thread:
                        file_thread.join()

                    if not is_txt_file:
                        file_thread = threading.Thread(target=utils.save_file_chunk, args=(file_name, message, self.host,), daemon=True)
                        file_thread.start()
                    else:
                        utils.receive_file_txt(message, file_name, self.host)

                    received_size += len(message)

                    if received_size >= file_size and file_accepted:
                        if file_thread:
                            file_thread.join()

                        if not is_txt_file:
                            finalizing_file = threading.Thread(target=utils.finalize_file, args=(file_name, self.host,), daemon=True)
                            finalizing_file.start()
                            finalizing_file.join()

                        is_txt_file = False
                        file_accepted = False
                        received_size = 0



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
    def send_file(self, file_paths):
        file_paths = list(file_paths)

        for file_path in file_paths:
            self.send_file_thread(file_path, len(file_paths))

#       while file_paths:  Вариант отправки 2
#           file_path = file_paths.pop(0)
#           self.send_file_thread(file_path)


    def send_file_thread(self, file_path, file_counts):
        try:
            file_name = os.path.basename(file_path)
            file_size = os.path.getsize(file_path)
            chunk_size = 1024 * 10000  # 10 MB

            # Отправка заголовка с информацией о файле
            file_info_message = f"FILE:{self.nickname}:{file_name}:{file_size}:{file_counts}"
            self.socket.send(file_info_message.encode('utf-8'))
            time.sleep(0.1)

            # Отправляем файл чанками
            with open(file_path, "rb") as f:
                sent_size = 0
                while sent_size < file_size:
                    if self.stop_file_transfer:
                        print(f"Передача файла {file_name} остановлена")
                        self.stop_file_transfer = False
                        return  # Остановка передачи файла

                    chunk = f.read(chunk_size)
                    if not chunk:
                        break  # Если больше нечего читать, выходим из цикла

                    self.socket.sendall(chunk)
                    sent_size += len(chunk)
                    del chunk
                    time.sleep(0.01)

            print(f"Файл {file_name} отправлен на сервер.")
            time.sleep(1.5) # В случае чего увеличить задержку(зависит от качества соединения)
        except Exception as e:
            print(f"Ошибка при отправке файла: {e}")

