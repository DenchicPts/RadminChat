import socket
import threading

BUFFER_SIZE = 1024


def connect_to_server(ip, port, nickname):
    client_socket = socket.socket()
    try:
        client_socket.connect((ip, port))
        print(f"Connected to server at {ip}:{port}")  # Debugging

        # Отправка приветственного сообщения

        welcome_message = f"{nickname} has joined the chat"
        client_socket.send(welcome_message.encode('utf-8'))

        # Start thread for receiving messages
        threading.Thread(target=receive_client_messages, args=(client_socket,), daemon=True).start()

        # Handle user input for sending messages
        while True:
            message = f"{nickname}: " + input()
            if message:
                client_socket.send(message.encode('utf-8'))
            else:
                print("Message cannot be empty.")
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
