import socket
import threading
import tkinter as tk
from tkinter import scrolledtext
import os

# Конфигурация
HOST = '0.0.0.0'  # Привязываемся ко всем доступным IP-адресам
PORT = 36500      # Порт для прослушивания
BUFFER_SIZE = 1024
IP_FILE = 'ip_list.txt'

# Список подключённых пользователей
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

def receive_messages(server_socket):
    while True:
        try:
            client_socket, client_address = server_socket.accept()
            print(f"Accepted connection from {client_address}")  # Отладка
            clients[client_socket] = client_address
            addresses[client_socket] = client_address[0]
            update_user_list()

            while True:
                try:
                    message = client_socket.recv(BUFFER_SIZE).decode('utf-8')
                    if message:
                        print(f"Received message: {message}")  # Отладка
                        broadcast(message, client_socket)
                    else:
                        break
                except Exception as e:
                    print(f"Error receiving message: {e}")  # Отладка
                    break
        except Exception as e:
            print(f"Error handling client: {e}")  # Отладка
        finally:
            client_socket.close()
            del clients[client_socket]
            del addresses[client_socket]
            update_user_list()

def broadcast(message, source_socket=None):
    for client_socket in clients:
        if client_socket != source_socket:
            try:
                client_socket.send(message.encode('utf-8'))
            except Exception as e:
                print(f"Error sending message: {e}")  # Отладка
                client_socket.close()
                del clients[client_socket]
                del addresses[client_socket]
    update_chat(message)

def update_chat(message):
    chat_window.config(state=tk.NORMAL)
    chat_window.insert(tk.END, message + '\n')
    chat_window.config(state=tk.DISABLED)
    chat_window.yview(tk.END)

def update_user_list():
    user_list.delete(0, tk.END)
    for address in addresses.values():
        user_list.insert(tk.END, address)

def send_message(event=None):
    message = message_entry.get()
    if message:
        formatted_message = f"{socket.gethostbyname(socket.gethostname())}: {message}"
        print(f"Sending message: {formatted_message}")  # Отладка
        broadcast(formatted_message)
        message_entry.delete(0, tk.END)

def start_server():
    global server_socket
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((HOST, PORT))
    server_socket.listen()
    print(f"Server listening on {HOST}:{PORT}")  # Отладка

    threading.Thread(target=receive_messages, args=(server_socket,), daemon=True).start()

def connect_to_server(ip):
    global client_socket
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        client_socket.connect((ip, PORT))
        print(f"Connected to server at {ip}:{PORT}")  # Отладка
        threading.Thread(target=receive_client_messages, args=(client_socket,), daemon=True).start()
    except (socket.timeout, socket.error) as e:
        print(f"Failed to connect to server: {e}")  # Отладка

def receive_client_messages(client_socket):
    while True:
        try:
            message = client_socket.recv(BUFFER_SIZE).decode('utf-8')
            if message:
                print(f"Received message: {message}")  # Отладка
                update_chat(message)
            else:
                break
        except Exception as e:
            print(f"Error receiving message: {e}")  # Отладка
            break

def initialize_console():
    while True:
        command = input("Enter 'create' to start a new room or 'join <IP>' to join an existing room: ").strip().lower()
        if command.startswith('create'):
            start_server()
            break
        elif command.startswith('join'):
            _, ip = command.split(maxsplit=1)
            if ip:
                connect_to_server(ip)
                break
            else:
                print("Please provide an IP address after 'join'")
        else:
            print("Invalid command. Use 'create' or 'join <IP>'.")

def initialize_gui():
    root = tk.Tk()
    root.title("Local Network Chat")
    root.configure(bg='black')

    frame = tk.Frame(root, bg='black')
    frame.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

    global chat_window
    chat_window = scrolledtext.ScrolledText(frame, state=tk.DISABLED, wrap=tk.WORD, bg='black', fg='white', font=('Helvetica', 12))
    chat_window.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    global user_list
    user_list = tk.Listbox(frame, bg='black', fg='white', font=('Helvetica', 12), width=20)
    user_list.pack(side=tk.RIGHT, fill=tk.Y)

    message_frame = tk.Frame(root, bg='black')
    message_frame.pack(padx=10, pady=5, fill=tk.X)

    global message_entry
    message_entry = tk.Entry(message_frame, bg='#333', fg='white', font=('Helvetica', 12))
    message_entry.pack(padx=10, pady=5, fill=tk.X)
    message_entry.bind('<Return>', send_message)

    root.mainloop()

# Запуск консольного интерфейса и GUI
if __name__ == "__main__":
    console_thread = threading.Thread(target=initialize_console, daemon=True)
    console_thread.start()

    # Запускаем GUI после завершения консольного ввода
    console_thread.join()
    initialize_gui()
