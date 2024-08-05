import tkinter as tk
from tkinter import messagebox
import random
import string
import socket
import threading

def generate_room_key():
    letters_and_digits = string.ascii_uppercase + string.digits
    return ''.join(random.choice(letters_and_digits) for i in range(6))

class MainApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Chat Application")
        self.root.geometry("500x300")
        self.root.configure(bg='black')

        self.create_buttons()

    def create_buttons(self):
        tk.Button(self.root, text="Create Room", command=self.create_room, bg='grey', fg='white').pack(pady=10)
        tk.Button(self.root, text="Join Room", command=self.join_room, bg='grey', fg='white').pack(pady=10)
        tk.Button(self.root, text="Users List", command=self.show_users_list, bg='grey', fg='white').pack(pady=10)
        tk.Button(self.root, text="Exit", command=self.root.quit, bg='grey', fg='white').pack(pady=10)

    def create_room(self):
        self.room_window = CreateRoomWindow(self.root, self)

    def join_room(self):
        self.room_window = JoinRoomWindow(self.root, self)

    def show_users_list(self):
        self.users_list_window = UsersListWindow(self.root)

    def enter_chat_room(self, room_name, key, is_admin=False):
        self.root.withdraw()
        self.chat_room_window = ChatRoomWindow(self.root, room_name, key, is_admin)

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
            # Проверка ключа комнаты должна быть добавлена здесь
            self.top.destroy()
            self.main_app.enter_chat_room("Unknown Room", room_key, is_admin=False)
        else:
            messagebox.showwarning("Input Error", "Please enter a room key.")

class UsersListWindow:
    def __init__(self, master):
        self.top = tk.Toplevel(master)
        self.top.title("Users List")
        self.top.geometry("300x200")
        self.top.configure(bg='black')

        self.users_list = tk.Listbox(self.top, bg='black', fg='white')
        self.users_list.pack(pady=10, fill=tk.BOTH, expand=True)

        # Здесь будут реальные пользователи из сети
        self.update_users_list()

    def update_users_list(self):
        # Пример списка пользователей
        self.users_list.insert(tk.END, "User1 - 192.168.1.1")
        self.users_list.insert(tk.END, "User2 - 192.168.1.2")

class ChatRoomWindow:
    def __init__(self, master, room_name, key, is_admin):
        self.top = tk.Toplevel(master)
        self.top.title(room_name)
        self.top.geometry("500x300")
        self.top.configure(bg='black')
        #self.top.overrideredirect(True)  # Скрыть верхнюю панель

        # Настройка сетки
        self.top.grid_rowconfigure(0, weight=1)
        self.top.grid_columnconfigure(0, weight=4)
        self.top.grid_columnconfigure(1, weight=1)

        # Название комнаты


        # Чат и список пользователей
        self.chat_frame = tk.Frame(self.top, bg='black')
        self.chat_frame.grid(row=1, column=0, sticky="nsew")
        self.users_frame = tk.Frame(self.top, bg='black')
        self.users_frame.grid(row=1, column=1, sticky="ns")

        self.chat_text = tk.Text(self.chat_frame, state='disabled', bg='black', fg='white', font=("Arial", 9), wrap=tk.WORD)
        self.chat_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.users_list = tk.Listbox(self.users_frame, bg='black', fg='white', width=25)
        self.users_list.pack(side=tk.RIGHT, fill=tk.Y)

        # Поле ввода сообщения
        self.msg_entry = tk.Entry(self.top, bg='black', fg='white', font=("Arial", 9))
        self.msg_entry.grid(row=2, column=0, columnspan=2, sticky="ew")
        self.msg_entry.bind("<Return>", self.send_message)

        self.is_admin = is_admin
        self.room_name = room_name
        self.key = key

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self.sock.bind(("", 9999))

        self.receiver_thread = threading.Thread(target=self.receive_messages)
        self.receiver_thread.start()

        self.send_announce()

    def send_message(self, event=None):
        msg = self.msg_entry.get()
        if msg:
            self.chat_text.config(state='normal')
            self.chat_text.insert(tk.END, f"You: {msg}\n")
            self.chat_text.config(state='disabled')
            self.msg_entry.delete(0, tk.END)
            self.sock.sendto(msg.encode(), ('<broadcast>', 9999))

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
                else:
                    if not msg.startswith("You: "):
                        self.chat_text.config(state='normal')
                        self.chat_text.insert(tk.END, f"{msg}\n")
                        self.chat_text.config(state='disabled')
            except:
                break

    def send_announce(self):
        username = "YourUsername"  # Замените на настоящее имя пользователя
        ip_address = socket.gethostbyname(socket.gethostname())
        announce_msg = f"ANNOUNCE {username} {ip_address}"
        self.sock.sendto(announce_msg.encode(), ('<broadcast>', 9999))
        self.top.after(10000, self.send_announce)  # Повторяем каждые 10 секунд

if __name__ == "__main__":
    root = tk.Tk()
    app = MainApp(root)
    root.mainloop()
