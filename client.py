import socket
import threading

BUFFER_SIZE = 1024

def connect_to_server(ip, port, update_chat, nickname):
    client_socket = socket.socket()
    try:
        client_socket.connect((ip, port))
        print(f"Connected to server at {ip}:{port}")  # Debugging

        # Отправка приветственного сообщения
        welcome_message = f"{nickname} has joined the chat"
        client_socket.send(welcome_message.encode('utf-8'))

        threading.Thread(target=receive_client_messages, args=(client_socket, update_chat), daemon=True).start()
        return client_socket
    except (socket.timeout, socket.error) as e:
        print(f"Failed to connect to server: {e}")  # Debugging
        return None

def receive_client_messages(client_socket, update_chat):
    while True:
        try:
            message = client_socket.recv(BUFFER_SIZE).decode('utf-8')
            if message:
                print(f"Received message: {message}")  # Debugging
                update_chat(message)
            else:
                print("Server closed connection")
                break
        except Exception as e:
            print(f"Error receiving message: {e}")  # Debugging
            break

def send_message(client_socket, message):
    try:
        client_socket.send(message.encode('utf-8'))
        print(f"Sent message: {message}")  # Debugging
    except Exception as e:
        print(f"Error sending message: {e}")  # Debugging
        client_socket.close()
