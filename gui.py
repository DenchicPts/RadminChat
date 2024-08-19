import tkinter as tk
from tkinter import scrolledtext, messagebox
import pystray
from pystray import MenuItem as item
import threading
from utils import create_custom_icon
import client
import server
from utils import get_ip_list
from main import PORT

class ChatApplication:
    def __init__(self, root, nickname):
        self.root = root
        self.nickname = nickname
        self.root.title("Radmin Chat")
        self.root.geometry("700x500")
        self.root.configure(bg='black')

        self.icon_image = create_custom_icon()
        self.icon_image.save('Config/Radmin Chat.ico')
        self.root.iconbitmap('Config/Radmin Chat.ico')

        self.tray_icon = None
        self.client = None
        self.server = None

        self.create_buttons_frame()

        self.user_listbox = None
        self.user_list = []

        self.root.protocol("WM_DELETE_WINDOW", self.hide_window)

    def create_buttons_frame(self):
        button_frame = tk.Frame(self.root, bg='black')
        button_frame.pack(pady=50, fill=tk.X)

        button_style = {
            'font': ('Helvetica', 16),
            'bg': '#333',
            'fg': 'white',
            'activebackground': '#555',
            'activeforeground': 'white',
            'bd': 0,
            'relief': tk.FLAT,
            'width': 15,
            'height': 2
        }

        tk.Button(button_frame, text="Create Room", command=self.show_room_settings, **button_style).pack(pady=10)
        tk.Button(button_frame, text="Join Room", command=self.show_join_room_window, **button_style).pack(pady=10)
        tk.Button(button_frame, text="IP List", command=self.ip_list, **button_style).pack(pady=10)

    def quit_window(self, icon, item):
        icon.stop()
        self.root.quit()
        self.root.destroy()

    def hide_window(self):
        self.root.withdraw()
        self.tray_icon = self.create_tray_icon()

    def show_window(self, icon, item):
        if self.tray_icon is not None:
            self.tray_icon.stop()
            self.tray_icon = None
        self.root.deiconify()

    def create_tray_icon(self):
        icon_image = create_custom_icon()
        menu = (item('Show', self.show_window), item('Quit', self.quit_window))
        icon = pystray.Icon("test", icon_image, "Radmin Chat", menu)
        threading.Thread(target=icon.run, daemon=True).start()
        return icon

    def create_chat_window(self, room_name, server_ip):
        chat_window = tk.Toplevel()
        chat_window.iconbitmap('Config\Radmin Chat.ico')
        chat_window.title(f"{room_name} : {server_ip}")
        chat_window.geometry("800x600")
        chat_window.configure(bg='black')

        history_frame = tk.Frame(chat_window, bg='black')
        history_frame.grid(row=0, column=0, sticky='nsew', padx=5, pady=5)

        self.message_area = scrolledtext.ScrolledText(history_frame, wrap=tk.WORD, bg='black', fg='white', font=('Helvetica', 12), state=tk.DISABLED)
        self.message_area.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        user_list_frame = tk.Frame(chat_window, bg='black')
        user_list_frame.grid(row=0, column=1, sticky='ns', padx=5, pady=5)

        self.user_listbox = tk.Listbox(user_list_frame, bg='black', fg='white', font=('Helvetica', 12))
        self.user_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        input_frame = tk.Frame(chat_window, bg='black')
        input_frame.grid(row=1, column=0, columnspan=2, sticky='ew', padx=5, pady=5)

        self.message_entry = tk.Text(input_frame, bg='#333', fg='white', font=('Helvetica', 12), height=3)
        self.message_entry.grid(row=0, column=0, sticky='ew')
        self.message_entry.bind('<Return>', self.send_message)
        self.message_entry.bind('<Shift-Return>', lambda e: self.message_entry.insert(tk.END, '\n'))

        send_button = tk.Button(input_frame, text="Send", command=self.send_message, bg='#333', fg='white', font=('Helvetica', 12))
        send_button.grid(row=0, column=1, padx=5)

        chat_window.grid_rowconfigure(0, weight=1)
        chat_window.grid_columnconfigure(0, weight=1)
        chat_window.grid_columnconfigure(1, weight=0)

            # Закрытие окна чата с разрывом соединения и возвратом к стартовому меню
        chat_window.protocol("WM_DELETE_WINDOW", lambda: (
            self.client.disconnect() if self.client else None,
            self.root.deiconify(),  # Возвращаем стартовое меню
            chat_window.destroy()  # Закрываем окно чата
        ))

    def send_message(self, event=None):
        message = self.message_entry.get("1.0", tk.END).strip()
        if message:
            self.client.send_message(message)
            self.message_entry.delete("1.0", tk.END)
            self.message_area.configure(state=tk.NORMAL)
            self.message_area.insert(tk.END, f"You: {message}\n")
            self.message_area.configure(state=tk.DISABLED)
            self.message_area.yview(tk.END)
        return 'break'


# Не работает
    def update_user_list(self, users):
        self.user_listbox.delete(0, tk.END)
        for user in users:
            self.user_listbox.insert(tk.END, user)

    def show_room_settings(self):
        settings_window = tk.Toplevel(self.root)
        settings_window.title("Room Settings")
        settings_window.iconbitmap('Config/Radmin Chat.ico')
        settings_window.geometry("400x150")
        settings_window.configure(bg='black')

        frame = tk.Frame(settings_window, bg='black')
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        tk.Label(frame, text="Room Name", fg='white', bg='black', font=('Helvetica', 12)).grid(row=0, column=0, sticky='w', pady=5)
        room_name_var = tk.StringVar()
        room_name_entry = tk.Entry(frame, textvariable=room_name_var, bg='#333', fg='white', font=('Helvetica', 12))
        room_name_entry.grid(row=0, column=1, sticky='ew', pady=5)

        show_password_var = tk.BooleanVar()
        show_password_checkbox = tk.Checkbutton(frame, text="Password", bg='black', fg='white', font=('Helvetica', 12), variable=show_password_var, command=lambda: self.toggle_password_field(password_entry))
        show_password_checkbox.grid(row=1, column=0, sticky='w', pady=5)

        password_var = tk.StringVar()
        password_entry = tk.Entry(frame, textvariable=password_var, show="*", bg='#333', fg='white', font=('Helvetica', 12))
        password_entry.grid(row=1, column=1, sticky='ew', pady=5)
        password_entry.grid_remove()  # Скрываем поле для пароля по умолчанию

        create_button = tk.Button(frame, text="Create Room", command=lambda: self.create_room_with_settings(settings_window, room_name_var, password_var), bg='#333', fg='white', font=('Helvetica', 12))
        create_button.grid(row=2, column=0, columnspan=2, sticky='ew', pady=10)


    def toggle_password_field(self, password_entry):
        if password_entry.winfo_ismapped():
            password_entry.grid_remove()
        else:
            password_entry.grid()

    def create_room_with_settings(self, settings_window, room_name_var, password_var):
        room_name = room_name_var.get()
        password = password_var.get()

        if not room_name:
            messagebox.showerror("Error", "Please enter a room name")
            settings_window.lift()
            return

        settings_window.destroy()

        self.root.withdraw()
        # Запускаем сервер в отдельном потоке
        def start_server_thread():
            self.server = server.start_server("0.0.0.0", 36500, self.nickname)

        threading.Thread(target=start_server_thread, daemon=True).start()

        # Подключаемся как клиент к только что созданной комнате
        self.client = client.Client("localhost", 36500, self.nickname, room_name, password)
        self.client.connect()
        self.client.start_listening(self.handle_message)
        self.create_chat_window(room_name, "0.0.0.0")  # Передаем IP адрес для заголовка окна

    def show_join_room_window(self):
        join_window = tk.Toplevel(self.root)
        join_window.title("Join Room")
        join_window.iconbitmap('Config\Radmin Chat.ico')
        join_window.configure(bg='black')
        join_window.geometry("300x150")
        join_window.resizable(False, False)

        frame = tk.Frame(join_window, bg='black')
        frame.grid(row=0, column=0, sticky='nsew', padx=10, pady=10)

        # Убираем Room Name, оставляем только Server IP и Password
        tk.Label(frame, text="Server IP", fg='white', bg='black', font=('Helvetica', 12)).grid(row=0, column=0, sticky='w', pady=5)
        server_ip_var = tk.StringVar()
        server_ip_entry = tk.Entry(frame, textvariable=server_ip_var, bg='#333', fg='white', font=('Helvetica', 12))
        server_ip_entry.grid(row=0, column=1, sticky='ew', pady=5)

        tk.Label(frame, text="Password (if any)", fg='white', bg='black', font=('Helvetica', 12)).grid(row=1, column=0, sticky='w', pady=5)
        password_var = tk.StringVar()
        password_entry = tk.Entry(frame, textvariable=password_var, show="*", bg='#333', fg='white', font=('Helvetica', 12))
        password_entry.grid(row=1, column=1, sticky='ew', pady=5)

        join_button = tk.Button(frame, text="Join Room", command=lambda: self.join_room(join_window, server_ip_var, password_var, join_button), bg='#333', fg='white', font=('Helvetica', 12))
        join_button.grid(row=2, column=0, columnspan=2, sticky='ew', pady=10)



        join_window.grid_rowconfigure(0, weight=1)
        join_window.grid_rowconfigure(1, weight=1)
        join_window.grid_rowconfigure(2, weight=1)

    def join_room(self, join_window, server_ip_var, password_var, join_button):
        server_ip = server_ip_var.get()
        password = password_var.get()

        if not server_ip:
            messagebox.showerror("Error", "Please enter server IP")
            join_window.lift()
            return

        # Блокируем кнопку на 5 секунд, чтобы предотвратить спам
        def unblock_button():
            if join_button.winfo_exists():  # Проверяем, существует ли кнопка
                join_button.config(state=tk.NORMAL)

        join_button.config(state=tk.DISABLED)
        self.root.after(5000, unblock_button)  # 5000 мс = 5 секунд

        def attempt_connection():
            # Создаем и запускаем клиента
            self.client = client.Client(server_ip, 36500, self.nickname, "", password)  # Пустая строка для room_name

            # Пытаемся подключиться с тайм-аутом
            if self.client.connect_with_timeout():
                # Если соединение успешно, запускаем прослушивание сообщений
                self.client.start_listening(self.handle_message)
                if join_window.winfo_exists():  # Проверяем, существует ли окно
                    self.root.after(0, join_window.destroy)  # Закрываем окно после успешного подключения
                self.root.withdraw()
                self.root.after(0, self.create_chat_window, "Unknown Room", server_ip)  # Передаем фиксированное название комнаты
            else:
                # Если соединение не удалось, показываем сообщение об ошибке и возвращаем окно
                if join_window.winfo_exists():  # Проверяем, существует ли окно
                    self.root.after(0, lambda: messagebox.showerror("Connection Error", "Unable to connect to the server. Please check the IP and try again."))
                self.client = None  # Удаляем клиента при неудаче
                self.root.after(0, unblock_button)  # Восстанавливаем состояние кнопки

        # Запускаем попытку подключения в отдельном потоке, чтобы избежать зависания UI
        threading.Thread(target=attempt_connection, daemon=True).start()

    def handle_message(self, message):
        self.message_area.configure(state=tk.NORMAL)
        self.message_area.insert(tk.END, f"{message}\n")
        self.message_area.configure(state=tk.DISABLED)
        self.message_area.yview(tk.END)

    def ip_list(self):
        def on_double_click(event):
            try:
                # Получаем выбранный элемент
                selection = ip_listbox.curselection()
                if not selection:
                    return  # Нет выбора, ничего не делаем

                # Извлекаем IP из выбранного элемента
                selected_item = ip_listbox.get(selection[0])
                ip, server_type = selected_item.split(" - ")

                # Разделяем IP и порт


                if server_type.strip() == "Server":
                    # Если это сервер, начинаем подключение
                    self.connect_to_server(ip, PORT, self.nickname, ip_window)
                else:
                    messagebox.showinfo("Info", "Selected IP is not a server.")
            except Exception as e:
                messagebox.showerror("Error", f"An error occurred: {e}")

        ip_window = tk.Toplevel(self.root)
        ip_window.title("IP List")
        ip_window.iconbitmap('Config\Radmin Chat.ico')
        ip_window.geometry("300x200")
        ip_window.configure(bg='black')
        ip_window.resizable(False, False)

        frame = tk.Frame(ip_window, bg='black')
        frame.pack(fill=tk.BOTH, expand=True)

        ip_listbox = tk.Listbox(frame, bg='#333', fg='white', font=('Helvetica', 12))
        ip_listbox.pack(fill=tk.BOTH, expand=True)

        # Заполняем список IP
        ip_list = get_ip_list()
        for ip in ip_list:
            ip_listbox.insert(tk.END, ip.strip())

        # Привязываем обработчик двойного клика
        ip_listbox.bind("<Double-1>", on_double_click)


    def connect_to_server(self, ip, port, nickname, window):
        def attempt_connection():
            try:
                # Создаем и запускаем клиента
                self.client = client.Client(ip, port, nickname, "", "")  # Пустая строка для room_name и password

                # Пытаемся подключиться
                if self.client.connect_with_timeout():
                    # Если соединение успешно, запускаем прослушивание сообщений
                    self.client.start_listening(self.handle_message)
                    messagebox.showinfo("Success", "Connected to the server successfully!")
                    if window.winfo_exists():
                        window.destroy()
                        self.root.withdraw()
                    self.root.after(0, self.create_chat_window, "Unknown Room", ip)  # Передаем фиксированное название комнаты
                else:
                    messagebox.showerror("Connection Error", "Unable to connect to the server. Please check the IP and try again.")
            except Exception as e:
                messagebox.showerror("Connection Error", f"An error occurred: {str(e)}")

        # Запускаем попытку подключения в отдельном потоке, чтобы избежать зависания UI
        threading.Thread(target=attempt_connection, daemon=True).start()
