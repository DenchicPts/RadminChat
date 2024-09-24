import subprocess
import time
import tkinter as tk
from tkinter import scrolledtext, messagebox, PhotoImage, filedialog, ttk
import pystray
from pystray import MenuItem as item
import threading
import utils
import client
import server
import os
from PIL import Image, ImageTk
from utils import get_ip_list

PORT = 36500

class ChatApplication:
    def __init__(self, root, nickname):
        self.root = root
        self.nickname = nickname
        self.root.title("Radmin Chat")
        self.root.geometry("700x500")
        self.root.configure(bg='black')

        self.icon_image = utils.create_custom_icon()
        self.icon_image.save('Config/Radmin Chat.ico')
        self.root.iconbitmap('Config/Radmin Chat.ico')

        self.tray_icon = None
        self.client = None
        self.server = None
        self.is_hosted = False

        self.create_buttons_frame()
        self.message_area = None
        self.user_listbox = None
        self.user_list = []

        self.chat_window = None
        self.root.protocol("WM_DELETE_WINDOW", self.hide_window)

    def create_buttons_frame(self):
        button_frame = tk.Frame(self.root, bg='black')
        button_frame.pack(pady=50, fill=tk.X)

        # Заблокировать изменение размера окна
        self.root.resizable(False, False)

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

        tk.Button(button_frame, text="Create Room", command=lambda: (
                                    messagebox.showerror("Error", "Комната уже создана") if self.is_hosted
                                    else self.show_room_settings()),
                                    **button_style).pack(pady=10)

        tk.Button(button_frame, text="Join Room", command=self.show_join_room_window, **button_style).pack(pady=10)
        tk.Button(button_frame, text="IP List", command=self.ip_list, **button_style).pack(pady=10)

        # Фрейм для состояния сервера
        status_frame = tk.Frame(self.root, bg='black')
        status_frame.pack(side=tk.LEFT, anchor='sw', padx=10, pady=10)

        # Кружок состояния сервера
        self.server_status_circle = tk.Canvas(status_frame, width=20, height=20, bg='black', highlightthickness=0)
        self.server_status_circle.pack(side=tk.LEFT)

        # Текст состояния сервера
        self.server_status_label = tk.Label(status_frame, text="Server is not started", fg='red', bg='black',
                                            font=('Helvetica', 12))
        self.server_status_label.pack(side=tk.LEFT)

        # Текст IP-адреса
        self.server_ip_label = tk.Label(status_frame, text="IP: N/A", fg='white', bg='black', font=('Helvetica', 12))
        self.server_ip_label.pack(side=tk.LEFT, padx=(10, 0))

        # Изначально скрываем IP
        self.server_ip_label.pack_forget()

        # Используем place для кнопок, чтобы разместить их над состоянием сервера
        return_button = tk.Button(self.root, text="Return", command=self.return_to_room, font=('Helvetica', 10),
                                  bg='#333', fg='white', width=6, height=1, bd=0, relief=tk.FLAT)
        return_button.place(x=35, y=435)  # Указываем точные координаты для размещения

        close_server_button = tk.Button(self.root, text="Close", command=self.close_server, font=('Helvetica', 10),
                                        bg='#333', fg='white', width=6, height=1, bd=0, relief=tk.FLAT)
        close_server_button.place(x=95, y=435)  # Указываем координаты для размещения рядом с Return to Room
        self.root.focus_force()


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
        icon_image = utils.create_custom_icon()
        menu = (item('Show', self.show_window), item('Quit', self.quit_window))
        icon = pystray.Icon("test", icon_image, "Radmin Chat", menu)
        threading.Thread(target=icon.run, daemon=True).start()
        return icon

    # Метод для закрытия сервера
    def close_server(self):
        if self.server:
            self.server.stop()  # Предполагаем, что у сервера есть метод stop
            self.server = None
            self.is_hosted = False
            self.update_server_status()

    def update_server_status(self):
        if self.is_hosted:
            # Зелёный кружок
            self.server_status_circle.create_oval(5, 5, 15, 15, fill='green')
            self.server_status_label.config(text="Server is running", fg='green')

            # Отображаем IP, если сервер запущен
            if self.server.host:

                self.server_ip_label.config(text=f"IP: {self.server.host}")
                self.server_ip_label.pack(side=tk.LEFT, padx=(10, 0))
        else:
            # Красный кружок
            self.server_status_circle.create_oval(5, 5, 15, 15, fill='red')
            self.server_status_label.config(text="Server is not started", fg='red')

            # Скрываем IP, если сервер не запущен
            self.server_ip_label.pack_forget()

    def return_to_room(self):
        if self.is_hosted:
            # Подключаемся как клиент к только что созданной комнате
            self.root.withdraw()
            if not self.server.host == "0.0.0.0":
                self.client = client.Client(self.server.host, 36500, self.nickname, self.server.room_name, self.server.room_password)
            else:
                self.client = client.Client("localhost", 36500, self.nickname, self.server.room_name, self.server.room_password)
            self.is_hosted = True
            self.client.connect()
            self.create_chat_window(self.server.room_name, self.server.host)  # Передаем IP адрес для заголовка окна
            self.client.start_listening(self.handle_message, self.update_user_list, self.chat_window_name_change, self.receive_file)
        else:
            print("No active room")


    def create_chat_window(self, room_name, server_ip):
        self.chat_window = tk.Toplevel()
        self.chat_window.iconbitmap('Config/Radmin Chat.ico')
        self.chat_window.title(f"{room_name} : {server_ip}")
        self.chat_window.geometry("800x600")
        self.chat_window.configure(bg='black')

        history_frame = tk.Frame(self.chat_window, bg='black')
        history_frame.grid(row=0, column=0, sticky='nsew', padx=5, pady=5)

        self.message_area = scrolledtext.ScrolledText(history_frame, wrap=tk.WORD, bg='black', fg='white', font=('Helvetica', 12), state=tk.DISABLED)
        self.message_area.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        user_list_frame = tk.Frame(self.chat_window, bg='black')
        user_list_frame.grid(row=0, column=1, sticky='ns', padx=5, pady=5)

        self.user_listbox = tk.Listbox(user_list_frame, bg='black', fg='white', font=('Helvetica', 12))
        self.user_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        input_frame = tk.Frame(self.chat_window, bg='black')
        input_frame.grid(row=1, column=0, columnspan=2, sticky='ew', padx=5, pady=5)

        # Загрузка иконок с корректировкой их размера до 35x35
        paperclip_icon = Image.open("Config/paperclip_icon.png").resize((35, 35))
        mic_icon = Image.open("Config/microphone_icon.png").resize((35, 35))
        smile_icon = Image.open("Config/smile_icon.png").resize((35, 35))
        save_icon = Image.open("Config/save_icon.png").resize((35, 35))

        # Преобразование изображений для работы с Tkinter
        paperclip_icon_tk = ImageTk.PhotoImage(paperclip_icon)
        mic_icon_tk = ImageTk.PhotoImage(mic_icon)
        smile_icon_tk = ImageTk.PhotoImage(smile_icon)
        save_icon_tk = ImageTk.PhotoImage(save_icon)

        # Создание кнопки для скрепки с прозрачным фоном
        self.paperclip_button = tk.Button(input_frame, image=paperclip_icon_tk, command=self.attach_file, bg='black', borderwidth=0, highlightthickness=0)
        self.paperclip_button.image = paperclip_icon_tk  # Сохраняем ссылку на изображение
        self.paperclip_button.pack(side=tk.LEFT, padx=(0, 5))

        # Поле для ввода сообщений (в центре), корректируем высоту
        self.message_entry = tk.Text(input_frame, bg='#333', fg='white', font=('Helvetica', 12), height=2, width=60)
        self.message_entry.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.message_entry.bind('<Return>', self.send_message)
        self.message_entry.bind('<Shift-Return>', lambda e: self.message_entry.insert(tk.END, ''))

        # Создание кнопок для микрофона, смайлика и сохранения чата с прозрачным фоном
        self.mic_button = tk.Button(input_frame, image=mic_icon_tk, command=self.record_audio, bg='black', borderwidth=0, highlightthickness=0)
        self.mic_button.image = mic_icon_tk  # Сохраняем ссылку на изображение
        self.mic_button.pack(side=tk.LEFT, padx=(5, 5))

        self.smile_button = tk.Button(input_frame, image=smile_icon_tk, command=self.open_emoji_menu, bg='black', borderwidth=0, highlightthickness=0)
        self.smile_button.image = smile_icon_tk  # Сохраняем ссылку на изображение
        self.smile_button.pack(side=tk.LEFT, padx=(5, 5))

        self.save_button = tk.Button(input_frame, image=save_icon_tk, command=lambda: self.save_chat(server_ip), bg='black', borderwidth=0, highlightthickness=0)
        self.save_button.image = save_icon_tk  # Сохраняем ссылку на изображение
        self.save_button.pack(side=tk.LEFT, padx=(5, 0))

        # Настройка пропорций сетки для правильного отображения
        self.chat_window.grid_rowconfigure(0, weight=1)
        self.chat_window.grid_columnconfigure(0, weight=1)
        self.chat_window.grid_columnconfigure(1, weight=0)
        self.chat_window.focus_force()
        self.chat_window.protocol("WM_DELETE_WINDOW", self.on_chat_window_close)


    def on_chat_window_close(self):
        if self.client:
            self.client.disconnect()  # Отключаем клиента, если он есть
        self.root.deiconify()  # Показать главное окно
        if self.server:
            self.update_server_status()  # Обновляем статус сервера
        self.chat_window.destroy()  # Закрыть окно чата

    def send_message(self, event=None):
        message = self.message_entry.get("1.0", tk.END).strip()
        if message:
            if not message.startswith("#"):
                message_to_send = "#MESSAGE#" + message
            else:
                message_to_send = message

            self.client.send_message(message_to_send)
            self.message_entry.delete("1.0", tk.END)
            self.message_area.configure(state=tk.NORMAL)
            self.message_area.insert(tk.END, f"You: {message}\n")
            self.message_area.configure(state=tk.DISABLED)
            self.message_area.yview(tk.END)
        return 'break'


    def update_user_list(self, users):
        self.user_listbox.delete(0, tk.END)
        for user in users:
            self.user_listbox.insert(tk.END, user)

    def show_room_settings(self):
        settings_window = tk.Toplevel(self.root)
        settings_window.title("Room Settings")
        settings_window.iconbitmap('Config/Radmin Chat.ico')
        settings_window.geometry("350x200")  # Увеличиваем размер окна для всех элементов
        settings_window.configure(bg='black')
        settings_window.resizable(False, False)

        frame = tk.Frame(settings_window, bg='black')
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        default_room_name, default_password, is_hidden = utils.load_room_settings()

        # Поле ввода имени комнаты
        tk.Label(frame, text="Room Name", fg='white', bg='black', font=('Helvetica', 12)).grid(row=0, column=0, sticky='w', pady=5)
        room_name_var = tk.StringVar(value=default_room_name)
        room_name_entry = tk.Entry(frame, textvariable=room_name_var, bg='#333', fg='white', font=('Helvetica', 12))
        room_name_entry.grid(row=0, column=1, sticky='ew', pady=5)

        # Выпадающий список IP-адресов
        tk.Label(frame, text="Host IP", fg='white', bg='black', font=('Helvetica', 12)).grid(row=1, column=0, sticky='w', pady=5)

        ip_var = tk.StringVar()
        available_ips = utils.get_available_ip_addresses()  # Предполагается, что у вас есть эта функция
        ip_combobox = ttk.Combobox(frame, textvariable=ip_var, values=available_ips, font=('Helvetica', 12))
        ip_combobox.grid(row=1, column=1, sticky='ew', pady=5)
        ip_combobox.current(0)  # Устанавливаем первый IP по умолчанию

        # Поле для пароля
        show_password_var = tk.BooleanVar()
        show_password_checkbox = tk.Checkbutton(frame, text="Password", bg='black', fg='white', font=('Helvetica', 12), variable=show_password_var, command=lambda: self.toggle_password_field(password_entry))
        show_password_checkbox.grid(row=2, column=0, sticky='w', pady=5)

        password_var = tk.StringVar(value=default_password)
        password_entry = tk.Entry(frame, textvariable=password_var, show="*", bg='#333', fg='white', font=('Helvetica', 12))
        password_entry.grid(row=2, column=1, sticky='ew', pady=5)

        if is_hidden:
            password_entry.grid_remove()  # Скрываем поле для пароля по умолчанию

        # Кнопка создания комнаты
        create_button = tk.Button(frame, text="Create Room", command=lambda: self.create_room_with_settings(settings_window, room_name_var, password_var, ip_var), bg='#333', fg='white', font=('Helvetica', 12))
        create_button.grid(row=3, column=0, columnspan=2, sticky='ew', pady=10)

        settings_window.bind('<Return>', lambda e: self.create_room_with_settings(settings_window, room_name_var, password_var, ip_var))
        settings_window.focus_force()


    def toggle_password_field(self, password_entry):

        if password_entry.winfo_ismapped():
            password_entry.grid_remove()
        else:
            password_entry.grid()

    def create_room_with_settings(self, settings_window, room_name_var, password_var, ip_var):
        room_name = room_name_var.get()
        password = password_var.get()
        selected_ip = ip_var.get()
        if not room_name:
            messagebox.showerror("Error", "Please enter a room name")
            settings_window.lift()
            return
        settings_window.destroy()

        self.root.withdraw()
        # Запускаем сервер в отдельном потоке
        def start_server_thread():
            try:
                self.server = server.Server(selected_ip, 36500, room_name, self.nickname, password)
                self.server.start()
            except Exception as e:
                print("Server shutted")

        threading.Thread(target=start_server_thread, daemon=True).start()
        # Подключаемся как клиент к только что созданной комнате
        if not selected_ip == "0.0.0.0":
            self.client = client.Client(selected_ip, 36500, self.nickname, room_name, password)
        else:
            self.client = client.Client("localhost", 36500, self.nickname, room_name, password)
        self.is_hosted = True
        self.client.connect()
        self.create_chat_window(room_name, selected_ip)  # Передаем IP адрес для заголовка окна
        self.client.start_listening(self.handle_message, self.update_user_list, self.chat_window_name_change, self.receive_file)

    def show_join_room_window(self):
        join_window = tk.Toplevel(self.root)
        join_window.title("Join Room")
        join_window.iconbitmap('Config/Radmin Chat.ico')
        join_window.configure(bg='black')
        join_window.geometry("300x150")
        join_window.resizable(False, False)

        frame = tk.Frame(join_window, bg='black')
        frame.grid(row=0, column=0, sticky='nsew', padx=10, pady=10)

        # Убираем Room Name, оставляем только Server IP и Password
        tk.Label(frame, text="Server IP", fg='white', bg='black', font=('Helvetica', 12)).grid(row=0, column=0, sticky='w', pady=5)
        server_ip_var = tk.StringVar()
        server_ip_entry = tk.Entry(frame, textvariable=server_ip_var, bg='#333', fg='white', font=('Helvetica', 12), width=20)
        server_ip_entry.grid(row=0, column=1, padx=(5, 10), pady=5)

        # Добавляем привязку события Ctrl + V для поля ввода Server IP
        #server_ip_entry.bind('<Control-v>', lambda e: server_ip_entry.event_generate('<<Paste>>'))

        tk.Label(frame, text="Password", fg='white', bg='black', font=('Helvetica', 12)).grid(row=1, column=0, sticky='w', pady=5)
        password_var = tk.StringVar()
        password_entry = tk.Entry(frame, textvariable=password_var, show="*", bg='#333', fg='white', font=('Helvetica', 12), width=20)
        password_entry.grid(row=1, column=1, padx=(5, 10), pady=5)

        # Добавляем привязку события Ctrl + V для поля ввода Password
        #password_entry.bind('<Control-v>', lambda e: password_entry.event_generate('<<Paste>>'))

        # Кнопка Join Room
        join_button = tk.Button(frame, text="Join Room", command=lambda: self.join_room(join_window, server_ip_var, password_var, join_button), bg='#333', fg='white', font=('Helvetica', 12), width=20)
        join_button.grid(row=2, column=0, columnspan=2, pady=10)

        # Привязка события Enter к полям ввода и кнопке Join Room
        join_window.bind('<Return>', lambda e: self.join_room(join_window, server_ip_var, password_var, join_button))

        join_window.grid_rowconfigure(0, weight=1)
        join_window.grid_rowconfigure(1, weight=1)
        join_window.grid_rowconfigure(2, weight=1)
        join_window.focus_force()

    def join_room(self, join_window, server_ip_var, password_var, join_button):
        server_ip = server_ip_var.get()
        password = password_var.get()
        self.attempt_connection_to_server(server_ip, PORT, self.nickname, password, join_window, join_button)


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
                    self.attempt_connection_to_server(ip, PORT, self.nickname, "", ip_window)
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



    def attempt_connection_to_server(self, server_ip, port, nickname, password, window=None, join_button=None):
        # Проверка на наличие IP-адреса
        if not server_ip:
            messagebox.showerror("Error", "Please enter server IP")
            if window and window.winfo_exists():
                window.lift()
            return

        # Блокируем кнопку на 5 секунд, чтобы предотвратить спам (если кнопка передана)
        if join_button:
            def unblock_button():
                if join_button.winfo_exists():  # Проверяем, существует ли кнопка
                    join_button.config(state=tk.NORMAL)

            join_button.config(state=tk.DISABLED)
            self.root.after(5000, unblock_button)  # 5000 мс = 5 секунд

        # Функция попытки подключения
        def attempt_connection():
            try:
                # Создаем и запускаем клиента
                self.client = client.Client(server_ip, port, nickname, "", password)

                # Пытаемся подключиться с тайм-аутом
                if self.client.connect_with_timeout():

                    if window and window.winfo_exists():
                        self.root.after(0, window.destroy)  # Закрываем окно после успешного подключения

                    self.root.withdraw()
                    self.create_chat_window("", server_ip)
                    time.sleep(0.10)
                    self.client.start_listening(self.handle_message, self.update_user_list, self.chat_window_name_change, self.receive_file )

                else:
                    # Если соединение не удалось, показываем сообщение об ошибке
                    if window and window.winfo_exists():
                        self.root.after(0, lambda: messagebox.showerror("Connection Error", "Unable to connect to the server. Please check the IP and try again."))
                    self.client = None  # Удаляем клиента при неудаче
                    if join_button:
                        self.root.after(0, unblock_button)  # Восстанавливаем состояние кнопки

            except Exception as e:
                messagebox.showerror("Connection Error", f"An error occurred: {str(e)}")

        # Запускаем попытку подключения в отдельном потоке, чтобы избежать зависания UI
        threading.Thread(target=attempt_connection, daemon=True, name="Attempt to connection").start()

    def chat_window_name_change(self):
        self.chat_window.title(f"{self.client.room_name} : {self.client.host}")

    def attach_file(self):
        # Открытие диалогового окна для выбора файла
        file_paths = filedialog.askopenfilenames()

        if file_paths:
            # Сообщаем клиенту отправить файл на сервер
            threading.Thread(target=self.client.send_file, args=(file_paths,)).start()

            # Отображаем сообщение в чате
            #file_name = os.path.basename(file_path)
            #self.message_area.config(state=tk.NORMAL)
            #self.message_area.insert(tk.END, f"Вы отправили файл: {file_name}\n")
            #self.message_area.config(state=tk.DISABLED)

    def record_audio(self):
        # Логика для записи аудио
        print("Record audio clicked!")

    def open_emoji_menu(self):
        # Логика для открытия меню эмодзи
        print("Emoji menu clicked!")

    def save_chat(self, server_ip):
        save_folder = "Save"
        file_path = os.path.join(save_folder, f"{server_ip}.txt")

        # Создание папки, если она не существует
        if not os.path.exists(save_folder):
            os.makedirs(save_folder)

        # Получение всех сообщений из чата
        messages = self.message_area.get("1.0", tk.END).strip()

        # Обработка строк, чтобы добавить приписку "(Файл)", если сообщение содержит ссылку на файл
        processed_messages = []
        for line in messages.split("\n"):
            if "Вы отправили файл:" in line or "получен и сохранён." in line:
                processed_messages.append(f"{line} (Файл)")
            else:
                processed_messages.append(line)

        # Сохранение всех сообщений в файл
        with open(file_path, "w", encoding="utf-8") as file:
            file.write("\n".join(processed_messages))

        print(f"Чат сохранён в файл: {file_path}")

    def receive_file(self, file_name, file_path, sender_nickname):
        # Отображаем информацию о получении файла в чате
        self.message_area.config(state=tk.NORMAL)

        if file_name.lower().endswith((".png", ".jpg", ".jpeg")):
            # Если это изображение, отображаем его в чате
            #self.message_area.insert(tk.END, f"Получено изображение: {file_name}\n")
            self.display_image_in_chat(file_path + f"\\{file_name}")
        else:
            # Создаём выделенный текст с файлом как ссылкой
            self.message_area.insert(tk.END, f"{sender_nickname}: ", "normal")
            self.message_area.insert(tk.END, file_name, "file_link")
            self.message_area.insert(tk.END, "\n")

            # Добавляем возможность открыть файл по клику
            self.message_area.tag_bind("file_link", "<Button-1>", lambda e: self.open_file_folder(file_path))
            self.message_area.tag_configure("file_link", foreground="blue", underline=True)

        self.message_area.config(state=tk.DISABLED)

    def display_image_in_chat(self, file_path):
        try:
            # Открываем изображение и изменяем его размер
            img = Image.open(file_path)
            img.thumbnail((200, 200))  # Ограничиваем размер изображения для чата
            img = ImageTk.PhotoImage(img)

            # Создаем изображение в текстовом поле
            self.message_area.image_create(tk.END, image=img)
            self.message_area.insert(tk.END, "\n")

            # Сохраняем ссылку на изображение в список, чтобы избежать garbage collection
            if not hasattr(self, 'images'):
                self.images = []  # Инициализируем список, если его ещё нет
            self.images.append(img)

        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось загрузить изображение: {e}")
    def open_file_folder(self, file_path):
        # Получаем путь к папке, где находится файл

        folder_path = os.getcwd() + f"\\{file_path}"
        if os.path.exists(folder_path):
            # Открываем папку в проводнике
            if os.name == 'nt':  # Проверяем, что мы на Windows
                subprocess.Popen(f'explorer "{folder_path}"')
            elif os.name == 'posix':  # Если на macOS или Linux
                subprocess.Popen(['xdg-open', folder_path])
            else:
                messagebox.showerror("Ошибка", "Операционная система не поддерживается")
        else:
            messagebox.showerror("Ошибка", f"Папка не найдена: {folder_path}")
