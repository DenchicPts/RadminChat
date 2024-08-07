import socket
import threading
import tkinter as tk
import os
from client import connect_to_server, send_message
from server import start_server, broadcast, clients, addresses
from gui import initialize_gui

HOST = '0.0.0.0'
PORT = 36500
NICK_FILE = 'nickname.txt'

client_socket = None
nickname = None

def update_chat(message):
    chat_window.config(state=tk.NORMAL)
    chat_window.insert(tk.END, message + '\n')
    chat_window.config(state=tk.DISABLED)
    chat_window.yview(tk.END)

def update_user_list():
    user_list.delete(0, tk.END)
    for client_socket, address in addresses.items():
        nickname = clients.get(client_socket, "Unknown")
        user_list.insert(tk.END, f"{address} ({nickname})")

def send_message_callback(event=None):
    global client_socket
    message = message_entry.get()
    if message:
        formatted_message = f"{nickname}: {message}"
        print(f"Sending message: {formatted_message}")  # Debugging
        if client_socket:
            send_message(client_socket, formatted_message)
        update_chat(formatted_message)
        message_entry.delete(0, tk.END)

def load_nickname():
    if os.path.exists(NICK_FILE):
        with open(NICK_FILE, 'r') as file:
            return file.readline().strip()
    return None

def save_nickname(nick):
    with open(NICK_FILE, 'w') as file:
        file.write(nick)

def initialize_console():
    global client_socket
    global nickname
    nickname = load_nickname()
    if not nickname:
        nickname = input("Enter your nickname: ").strip()
        save_nickname(nickname)

    while True:
        command = input("Enter 'create' to start a new room or 'join <IP>' to join an existing room: ").strip().lower()
        if command.startswith('create'):
            start_server(HOST, PORT, update_user_list, broadcast)
            break
        elif command.startswith('join'):
            _, ip = command.split(maxsplit=1)
            if ip:
                client_socket = connect_to_server(ip, PORT, update_chat, nickname)
                break
            else:
                print("Please provide an IP address after 'join'")
        else:
            print("Invalid command. Use 'create' or 'join <IP>'.")

if __name__ == "__main__":
    console_thread = threading.Thread(target=initialize_console, daemon=True)
    console_thread.start()

    # Запускаем GUI после завершения консольного ввода
    console_thread.join()

    root, chat_window, user_list, message_entry = initialize_gui(send_message_callback)
    root.mainloop()
