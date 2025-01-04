import re
import socket
import threading
import time
import os
import gc
import database
import utils

class Client:
    def __init__(self, host, port, nickname, room_name="", password=""):
        self.sender_nickname = None
        self.is_txt_file = False
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
        file_thread = None
        while True:
            try:
                message = self.socket.recv(1024 * 10000)
                decoded_message, message_content = self.decode_message(message)

                if decoded_message and not self.is_txt_file:
                    self.process_message(message_content)
                    if message_content.startswith("FILE:"):
                        self.process_file_metadata(message_content)
                elif message:
                    self.handle_non_decoded_message(message, file_thread)
                else:
                    break

            except Exception as e:
                print(f"Error receiving message: {e}")
                break

    def decode_message(self, message):
        try:
            return True, message.decode('utf-8')
        except UnicodeDecodeError:
            return False, message

    def process_file_metadata(self, message):
        parts = message.split(":")
        self.sender_nickname = parts[1]
        self.file_name = parts[2]
        self.file_size = int(parts[3])
        self.file_counts = int(parts[4])
        self.received_size = 0
        self.file_accepted = True

        if self.file_name.lower().endswith(".txt") or self.file_name.lower().endswith(".java"):
            self.is_txt_file = True

    def handle_non_decoded_message(self, message, file_thread):
        if file_thread:
            file_thread.join()

        if self.is_txt_file:
            self.process_txt_file(message)
        else:
            file_thread = self.save_file_chunk(message)

        self.received_size += len(message)
        if self.received_size >= self.file_size and self.file_accepted:
            self.finalize_file_transfer(file_thread)

    def save_file_chunk(self, message):
        thread = threading.Thread(
            target=utils.save_file_chunk,
            args=(self.file_name, message, self.host),
            daemon=True
        )
        thread.start()
        return thread

    def process_txt_file(self, message):
        utils.receive_file_txt(message, self.file_name, self.host)

    def finalize_file_transfer(self, file_thread):
        if file_thread:
            file_thread.join()

        if not self.is_txt_file:
            finalizing_thread = threading.Thread(
                target=utils.finalize_file,
                args=(self.file_name, self.host),
                daemon=True
            )
            finalizing_thread.start()
            finalizing_thread.join()

        self.reset_file_transfer_state()

    def reset_file_transfer_state(self):
        self.is_txt_file = False
        self.file_accepted = False
        self.received_size = 0

        file_path = f"Save\\{self.host}"
        if self.file_callback:
            self.file_callback(self.file_name, file_path, self.sender_nickname)

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

    def process_message(self, message):
        # Модифицируем регулярное выражение для захвата содержимого команд, включая переносы строк
        commands = re.findall(r'(#\w+#)(.*?)((?=#\w+#)|$)', message, re.DOTALL)

        for command_tuple in commands:
            command = command_tuple[0].strip()  # Команда (#ROOMNAME#, #USERS_IP# и т.д.)
            data = command_tuple[1].strip()  # Данные после команды

            # Используем match-case для обработки команд
            match command:
                case "#ROOMNAME#":
                    self.handle_room_name(data)
                case "#USERS_IP#":
                    self.handle_users_ip(data)  # Передаём всю строку с пользователями
                case "#MESSAGE#":
                    self.handle_message(data)
                case "#FILE_EXISTS#":
                    self.handle_file_exists(data)
                case _ if "Invalid password" in command:
                    self.handle_invalid_password()
                case _:
                    print(f"Unrecognized command: {command}")


    def handle_room_name(self, room_name):
        self.room_name = room_name
        self.window_name_change()
        self.authenticated = True
        database.save_connection(True, self.host, self.room_name)

    def handle_users_ip(self, users_data):
        users = users_data.strip().split("\n")
        if self.message_callback:
            database.parse_users_info(users)
            self.update_user_list(users)

    def handle_message(self, message):
        if self.message_callback:
            self.message_callback(message)

    def handle_file_exists(self, file_name):
        print(f"Файл {file_name} уже существует на сервере. Передача отменена.")
        self.stop_file_transfer = True

    def handle_invalid_password(self):
        print("Invalid password")
        self.socket.close()
