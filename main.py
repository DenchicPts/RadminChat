import tkinter as tk
import gui
import utils


HOST = '0.0.0.0'
PORT = 36500

def start_server(host, port, nickname):
    import server
    server.start_server(host, port, nickname)

def connect_to_server(ip, port, nickname):
    import client
    client.connect_to_server(ip, port, nickname)

def main():
    nickname = utils.load_nickname()
    if not nickname:
        utils.save_nickname()
        nickname = utils.load_nickname()

#pisun big
    if not nickname:
        while True:
            nickname = nickname


    # Запуск GUI
    root = tk.Tk()
    app = gui.ChatApplication(root, nickname)
    root.mainloop()


if __name__ == "__main__":
    main()
