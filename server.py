import socket
import threading

BUFFER_SIZE = 1024
clients = {}
addresses = {}


def receive_messages(server_socket, broadcast):
    while True:
        try:
            client_socket, client_address = server_socket.accept()
            print(f"Accepted connection from {client_address}")  # Debugging
            addresses[client_socket] = client_address[0]
            threading.Thread(target=handle_client, args=(client_socket, broadcast), daemon=True).start()
        except Exception as e:
            print(f"Error handling client: {e}")  # Debugging


def handle_client(client_socket, broadcast):
    try:
        # Принятие приветственного сообщения от клиента
        welcome_message = client_socket.recv(BUFFER_SIZE).decode('utf-8')
        if welcome_message:
            nickname = welcome_message.split(' ')[0]
            clients[client_socket] = nickname
            print(f"Welcome message from {addresses[client_socket]}: {welcome_message}")  # Debugging
            broadcast(f"Welcome to the chat, {nickname}!", client_socket)

        while True:
            message = client_socket.recv(BUFFER_SIZE).decode('utf-8')
            if message:
                print(f"Received message from {addresses[client_socket]}: {message}")  # Debugging
                broadcast(message, client_socket)
            else:
                print(f"Client {addresses[client_socket]} disconnected")
                break
    except Exception as e:
        print(f"Error receiving message: {e}")  # Debugging
    finally:
        client_socket.close()
        if client_socket in clients:
            del clients[client_socket]
        if client_socket in addresses:
            del addresses[client_socket]


def broadcast(message, source_socket=None):
    for client_socket in list(clients.keys()):
        if client_socket != source_socket:
            try:
                client_socket.send(message.encode('utf-8'))
                print(f"Sent message to {addresses[client_socket]}: {message}")  # Debugging
            except Exception as e:
                print(f"Error sending message: {e}")  # Debugging
                client_socket.close()
                if client_socket in clients:
                    del clients[client_socket]
                if client_socket in addresses:
                    del addresses[client_socket]


def server_input_thread(broadcast, nickname):
    while True:
        try:
            message = input()
            if message:
                broadcast(f"{nickname}: {message}")
        except KeyboardInterrupt:
            print("\nServer shutting down.")
            break


def start_server(host, port, nickname):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((host, port))
    server_socket.listen()
    print(f"Server listening on {host}:{port}")  # Debugging

    # Start the thread for handling incoming messages
    threading.Thread(target=receive_messages, args=(server_socket, broadcast), daemon=True).start()

    # Start the thread for handling server input
    server_input_thread(broadcast, nickname)
