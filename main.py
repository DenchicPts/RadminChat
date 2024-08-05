import tkinter as tk
from tkinter import messagebox
import random
import string
import socket
import threading
import pyperclip

def generate_room_key():
    letters_and_digits = string.ascii_uppercase + string.digits
    return ''.join(random.choice(letters_and_digits) for i in range(6))

class MainApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Chat Application")
        self.root.geometry("600x400")
        self.root.configure(bg='black')

        self.create_buttons()
        self.show_ip_address()

        # История IP адресов
        self.ip_history = set()

    def create_buttons(self):
        self.button_frame = tk.Frame(self.root, bg='black')
        self.button_frame.pack(pady=20)

        tk.Button(self.button_frame, text="Create Room", command=self.create_room, bg='grey', fg='white').grid(row=0, column=0, padx=10)
        tk.Button(self.button_frame, text="Join Room", command=self.join_room, bg='grey', fg='white').grid(row=0, column=1, padx=10)
        tk.Button(self.button_frame, text="IP History", command=self.show_ip_history, bg='grey', fg='white').grid(row=0, column=2, padx=10)
        tk.Button(self.button_frame, text="Exit", command=self.root.quit, bg='grey', fg='white').grid(row=0, column=3, padx=10)

    def create_room(self):
        self.room_window = CreateRoomWindow(self.root, self)

    def join_room(self):
        self.room_window = JoinRoomWindow(self.root, self)

    def show_ip_history(self):
        self.ip_history_window = IPHistoryWindow(self.root, self.ip_history)

    def show_ip_address(self):
        ip_frame = tk.Frame(self.root, bg='black')
        ip_frame.pack(side=tk.BOTTOM, pady=10)
        ip_address = socket.gethostbyname(socket.gethostname())
        tk.Label(ip_frame, text=f"Your IP: {ip_address}", bg='black', fg='white').pack()

    def enter_chat_room(self, room_name, key, is_admin=False):
        self.root.withdraw()
        self.chat_room_window = ChatRoomWindow(self.root, room_name, key, is_admin, self.ip_history)

class CreateRoomWindow:
    def __init__(self, master, main_app):
        self.main_app = main_app
        self.top = tk.Toplevel(master)
        self.top.title("Create Room")
        self.top.geometry("300x150")
        self.top.configure(bg='black')

        tk.Label(self.top, text="Room Name:", bg='black', fg='white').pack(pady=5)
        self.room_name_entry = tk.Entry(self.top)
        self.room_name_entry.pack(pady=5)

        tk.Button(self.top, text="Create", command=self.create_room, bg='grey', fg='white').pack(pady=10)

    def create_room(self):
        room_name = self.room_name_entry.get()
        if room_name:
            key = generate_room_key()
            messagebox.showinfo("Room Created", f"Room '{room_name}' created with key: {key}")
            self.top.destroy()
            self.main_app.enter_chat_room(room_name, key, is_admin=True)
        else:
            messagebox.showwarning("Input Error", "Please enter a room name.")

class JoinRoomWindow:
    def __init__(self, master, main_app):
        self.main_app = main_app
        self.top = tk.Toplevel(master)
        self.top.title("Join Room")
        self.top.geometry("300x150")
        self.top.configure(bg='black')

        tk.Label(self.top, text="Room Key:", bg='black', fg='white').pack(pady=5)
        self.room_key_entry = tk.Entry(self.top)
        self.room_key_entry.pack(pady=5)

        tk.Button(self.top, text="Join", command=self.join_room, bg='grey', fg='white').pack(pady=10)

    def join_room(self):
        room_key = self.room_key_entry.get()
        if room_key:
            if self.is_valid_room_key(room_key):
                self.top.destroy()
                self.main_app.enter_chat_room("Unknown Room", room_key, is_admin=False)
            else:
                messagebox.showwarning("Invalid Key", "Room key is incorrect.")
        else:
            messagebox.showwarning("Input Error", "Please enter a room key.")

    def is_valid_room_key(self, key):
        # Здесь должна быть логика проверки ключа комнаты
        # Например, запрос к серверу или поиск в локальной базе данных
        # Для демонстрации, будем считать ключ валидным, если его длина равна 6
        return len(key) == 6

class IPHistoryWindow:
    def __init__(self, master, ip_history):
        self.top = tk.Toplevel(master)
        self.top.title("IP History")
        self.top.geometry("300x200")
        self.top.configure(bg='black')

        self.ip_list = tk.Listbox(self.top, bg='black', fg='white')
        self.ip_list.pack(pady=10, fill=tk.BOTH, expand=True)

        self.update_ip_list(ip_history)

    def update_ip_list(self, ip_history):
        for ip in ip_history:
            self.ip_list.insert(tk.END, ip)

class ChatRoomWindow:
    def __init__(self, master, room_name, key, is_admin, ip_history):
        self.top = tk.Toplevel(master)
        self.top.title(room_name)
        self.top.geometry("700x500")
        self.top.configure(bg='black')

        self.top.grid_rowconfigure(0, weight=5)
        self.top.grid_rowconfigure(1, weight=1)
        self.top.grid_rowconfigure(2, weight=1)
        self.top.grid_columnconfigure(0, weight=3)
        self.top.grid_columnconfigure(1, weight=1)

        self.chat_frame = tk.Frame(self.top, bg='black')
        self.chat_frame.grid(row=0, column=0, sticky="nsew")
        self.users_frame = tk.Frame(self.top, bg='black')
        self.users_frame.grid(row=0, column=1, sticky="ns")
        self.key_frame = tk.Frame(self.top, bg='black')
        self.key_frame.grid(row=2, column=1, sticky="sew")

        self.chat_text = tk.Text(self.chat_frame, state='disabled', bg='black', fg='white', wrap=tk.WORD, font=("Arial", 12))
        self.chat_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.users_list = tk.Listbox(self.users_frame, bg='black', fg='white', width=30, font=("Arial", 12))
        self.users_list.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        self.msg_entry = tk.Entry(self.top, bg='black', fg='white', font=("Arial", 12))
        self.msg_entry.grid(row=2, column=0, columnspan=1, sticky="ew")
        self.msg_entry.bind("<Return>", self.send_message)

        self.is_admin = is_admin
        self.room_name = room_name
        self.key = key
        self.ip_history = ip_history

        self.key_label = tk.Label(self.key_frame, text=f"Room Key: {key}", bg='black', fg='white', cursor="hand2", font=("Arial", 12))
        self.key_label.pack(side=tk.BOTTOM, pady=10)
        self.key_label.bind("<Button-1>", self.copy_key_to_clipboard)

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self.sock.bind(("", 9999))

        self.receiver_thread = threading.Thread(target=self.receive_messages)
        self.receiver_thread.start()

        self.send_announce()

    def copy_key_to_clipboard(self, event):
        pyperclip.copy(self.key)
        messagebox.showinfo("Copied", "Room key copied to clipboard!")

    def send_message(self, event=None):
        msg = self.msg_entry.get()
        if msg:
            self.chat_text.config(state='normal')
            self.chat_text.insert(tk.END, f"You: {msg}\n")
            self.chat_text.config(state='disabled')
            self.msg_entry.delete(0, tk.END)
            self.sock.sendto(f"{msg}".encode(), ('<broadcast>', 9999))

    def receive_messages(self):
        while True:
            try:
                msg, addr = self.sock.recvfrom(1024)
                msg = msg.decode()
                if msg.startswith("ANNOUNCE"):
                    username, user_ip = msg.split()[1:]
                    user_entry = f"{username} - {user_ip}"
                    if user_entry not in self.users_list.get(0, tk.END):
                        self.users_list.insert(tk.END, user_entry)
                        self.ip_history.add(user_ip)  # Добавление IP в историю
                else:
                    if not msg.startswith("You: "):
                        self.chat_text.config(state='normal')
                        self.chat_text.insert(tk.END, f"{msg}\n")
                        self.chat_text.config(state='disabled')
            except:
                break

    def send_announce(self):
        username = "User"  # Замените на настоящее имя пользователя
        ip_address = socket.gethostbyname(socket.gethostname())
        announce_msg = f"ANNOUNCE {username} {ip_address}"
        self.sock.sendto(announce_msg.encode(), ('<broadcast>', 9999))
        self.top.after(10000, self.send_announce)  # Повторяем каждые 10 секунд

if __name__ == "__main__":
    root = tk.Tk()
    app = MainApp(root)
    root.mainloop()
