import tkinter as tk
import gui
from utils import save_nickname, load_nickname, save_ip_address

HOST = '0.0.0.0'
PORT = 36500

def start_server(host, port, nickname):
    import server
    server.start_server(host, port, nickname)

def connect_to_server(ip, port, nickname):
    import client
    client.connect_to_server(ip, port, nickname)

def main():
    nickname = load_nickname()
    if not nickname:
        save_nickname()

    # Запуск GUI
    root = tk.Tk()
    app = gui.ChatApplication(root, nickname)
    root.mainloop()


if __name__ == "__main__":
    main()
