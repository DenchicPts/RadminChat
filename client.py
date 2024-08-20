import socket
import threading
import time
from utils import save_ip_address

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

        self.authenticated = False

        print(host)

    def connect(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((self.host, self.port))
        self.send_message(f"{self.nickname }*{self.room_name}*{self.password}")

    def start_listening(self, callback, update_list, name_change):
        self.message_callback = callback
        self.update_user_list = update_list
        self.window_name_change = name_change
        threading.Thread(target=self.listen_for_messages, daemon=True).start()

    def listen_for_messages(self):
        while True:
            try:
                message = self.socket.recv(1024).decode('utf-8')
                print("Message from server " + message)
                if message:
                    if "Invalid password" in message:
                        print("Invalid password")
                        self.socket.close()
                        break
                    elif message.startswith("#ROOMNAME#"):
                        self.room_name = message[len("#ROOMNAME#"):]
                        self.window_name_change()
                        self.authenticated = True  # Аутентификация успешна
                        print(f"Connected to room: {self.room_name}")
                    elif message.startswith("#USERS_IP#"):
                        users = message[len("#USERS_IP#"):].strip().split("\n")
                        if self.message_callback:
                            self.update_user_list(users)
                    elif self.message_callback:
                        self.message_callback(message)
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

        connected = False
        for _ in range(timeout):
            try:
                self.socket.connect((self.host, self.port))
                save_ip_address(self.host + " - Server")
                connected = True
                break
            except (socket.timeout, socket.error) as e:
                print(f"Connection attempt failed: {e}")
                time.sleep(1)

        self.socket.settimeout(None)  # Сбрасываем тайм-аут после подключения
        if connected:
            self.send_message(f"{self.nickname}*{self.room_name}*{self.password}")
        return connected
