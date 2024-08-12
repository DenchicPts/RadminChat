import socket
import threading
from utils import save_ip_address

BUFFER_SIZE = 1024


def connect_to_server(ip, port, nickname):
    client_socket = socket.socket()
    try:
        client_socket.connect((ip, port))
        print(f"Connected to server at {ip}:{port}")  # Debugging
        save_ip_address(ip + " - Server")
        # Отправка приветственного сообщения
        welcome_message = f"{nickname} has joined the chat"
        print(welcome_message)
        client_socket.send(welcome_message.encode('utf-8'))

        # Запуск потока для получения сообщений
        threading.Thread(target=receive_client_messages, args=(client_socket,), daemon=True).start()

        # Обработка пользовательского ввода для отправки сообщений
        while True:
            message = input()
            if message.strip():  # Проверяем, что сообщение не пустое после удаления пробелов
                full_message = f"{nickname}: {message}"
                if full_message != f"{nickname}: ":  # Проверяем, что сообщение не состоит только из никнейма и двоеточия
                    client_socket.send(full_message.encode('utf-8'))
    except (socket.timeout, socket.error) as e:
        print(f"Failed to connect to server: {e}")  # Debugging


def receive_client_messages(client_socket):
    while True:
        try:
            message = client_socket.recv(BUFFER_SIZE).decode('utf-8')
            if message:
                print(message)
            else:
                print("Server closed connection")
                break
        except Exception as e:
            print(f"Error receiving message: {e}")  # Debugging
            break
