import re, subprocess, time, webbrowser, pystray, threading, utils, os, voice
import tkinter as tk
from tkinter import messagebox, filedialog
from pystray import MenuItem as item
from network import textClient, textServer
from PIL import Image, ImageTk
import soundfile as sf
from multiprocessing import Process
import customtkinter as ctk
from utils import get_ip_list, threaded
import allbinds as abind
import tkinter.font as tkFont
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
        self.application_icon = 'Config/Radmin Chat.ico'


        self.tray_icon = None
        self.client = None
        self.server_process = None
        self.is_hosted = False
        self.server_room_name = None
        self.server_password = None
        self.server_selected_ip = None


        self.create_buttons_frame()
        self.message_frame = None
        self.user_listbox = None
        self.user_list = []
        self.active_audio_widget = None
        self.VoiceRecorder = voice.VoiceRecorder()

        self.chat_window = None
        self.root.protocol("WM_DELETE_WINDOW", self.hide_window)

    def create_buttons_frame(self):
        # Создаем фрейм для кнопок
        button_frame = ctk.CTkFrame(self.root, fg_color='black')
        button_frame.pack(pady=50, fill=ctk.X)

        # Заблокировать изменение размера окна
        self.root.resizable(False, False)

        # Кнопка "Create Room"
        ctk.CTkButton(button_frame, text="Create Room", command=lambda: (
            messagebox.showerror("Error", "Комната уже создана") if self.is_hosted
            else self.show_room_settings()), font=('Helvetica', 16), fg_color='#333', text_color='white', hover_color='#555', corner_radius=8, width=200, height=50).pack(pady=10)

        # Кнопка "Join Room"
        ctk.CTkButton(button_frame, text="Join Room", command=self.show_join_room_window, font=('Helvetica', 16), fg_color='#333', text_color='white', hover_color='#555', corner_radius=8, width=200, height=50).pack(pady=10)

        # Кнопка "IP List"
        ctk.CTkButton(button_frame, text="IP List", command=self.ip_list, font=('Helvetica', 16), fg_color='#333', text_color='white', hover_color='#555', corner_radius=8, width=200, height=50).pack(pady=10)

        # Фрейм для состояния сервера
        status_frame = ctk.CTkFrame(self.root, fg_color='black')
        status_frame.pack(side=ctk.LEFT, anchor='sw', padx=10, pady=10)

        # Кружок состояния сервера (оставлен на Canvas)
        self.server_status_circle = ctk.CTkCanvas(status_frame, width=20, height=20, bg='black', highlightthickness=0)
        self.server_status_circle.pack(side=ctk.LEFT)

        # Текст состояния сервера
        self.server_status_label = ctk.CTkLabel(status_frame, text="Server is not started", text_color='red', font=('Helvetica', 12))
        self.server_status_label.pack(side=ctk.LEFT)

        # Текст IP-адреса
        self.server_ip_label = ctk.CTkLabel(status_frame, text="IP: N/A", text_color='white', font=('Helvetica', 12))
        self.server_ip_label.pack(side=ctk.LEFT, padx=(10, 0))

        # Изначально скрываем IP
        self.server_ip_label.pack_forget()

        # Кнопка "Return"
        return_button = ctk.CTkButton(self.root, text="Return", command=self.return_to_room, font=('Helvetica', 14), fg_color='#333', text_color='white', width=60, height=30, corner_radius=15)
        return_button.place(x=20, y=435)  # Указываем точные координаты для размещения

        # Кнопка "Close"
        close_server_button = ctk.CTkButton(self.root, text="Close", command=self.close_server, font=('Helvetica', 14), fg_color='#333', text_color='white', width=60, height=30, corner_radius=15)
        close_server_button.place(x=100, y=435)  # Указываем координаты для размещения рядом с Return to Room

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
        if self.server_process:
            self.server_process.terminate()  # Завершает процесс
            self.server_process.join()
            self.is_hosted = False
            self.update_server_status()

    def update_server_status(self):
        if self.is_hosted:
            # Зелёный кружок
            self.server_status_circle.create_oval(5, 5, 15, 15, fill='green')
            self.server_status_label.configure(text="Server is running", text_color='green')

            # Отображаем IP, если сервер запущен
            if self.is_hosted:

                self.server_ip_label.configure(text=f"IP: {self.server_selected_ip}")
                self.server_ip_label.pack(side=tk.LEFT, padx=(10, 0))
        else:
            # Красный кружок
            self.server_status_circle.create_oval(5, 5, 15, 15, fill='red')
            self.server_status_label.configure(text="Server is not started", text_color='red')

            # Скрываем IP, если сервер не запущен
            self.server_ip_label.pack_forget()

    def return_to_room(self):
        if self.is_hosted:
            # Подключаемся как клиент к только что созданной комнате
            self.root.withdraw()
            if not self.server_selected_ip == "0.0.0.0":
                self.client = textClient.Client(self.server_selected_ip, 36500, self.nickname, self.server_room_name, self.server_password)
            else:
                self.client = textClient.Client("localhost", 36500, self.nickname, self.server_room_name, self.server_password)
            self.is_hosted = True
            self.client.connect()
            self.create_chat_window(self.server_room_name, self.server_selected_ip)  # Передаем IP адрес для заголовка окна
            self.client.start_listening(self.handle_message, self.update_user_list, self.chat_window_name_change, self.receive_file)
        else:
            print("No active room")


    def create_chat_window(self, room_name, server_ip):
        self.chat_window = ctk.CTkToplevel()
        #   self.chat_window.withdraw()
        #   self.chat_window.after(50, self.chat_window.deiconify())
        self.chat_window.title(f"{room_name} : {server_ip}")
        self.chat_window.geometry("800x600")
        self.chat_window.minsize(500, 350)
        self.chat_window.after(300, lambda: self.chat_window.iconbitmap(self.application_icon))
        # Фрейм для списка пользователей справа
        user_list_frame = ctk.CTkFrame(self.chat_window, fg_color='#252850', width=150)
        user_list_frame.grid(row=0, column=2, rowspan=2, sticky='ns', padx=0, pady=0)

        # Заголовок для списка пользователей
        self.user_list_label = ctk.CTkLabel(user_list_frame, text="Список пользователей", text_color='white')
        self.user_list_label.grid(row=0, column=0, pady=(0, 10))

        # Прокручиваемый Canvas для списка пользователей
        self.user_frame = ctk.CTkScrollableFrame(user_list_frame, fg_color='#252850', width=200)
        self.user_frame.grid(row=1, column=0, sticky="nsew", padx=0, pady=0)

        # Фрейм слева
        left_frame = ctk.CTkFrame(self.chat_window, fg_color='#1E213D', width=40)
        left_frame.grid(row=0, column=0, rowspan=2, sticky='ns', padx=0, pady=0)

        # Фрейм для верхней панели с кнопками
        top_buttons_frame = ctk.CTkFrame(self.chat_window, fg_color='#1E213D', height=50)
        top_buttons_frame.grid(row=0, column=1, sticky='ew', padx=0, pady=0)

        self.exit_button = ctk.CTkButton(top_buttons_frame, text="Выход", command=self.on_chat_window_close,
                                         fg_color=None, hover_color=None, text_color="white")
        self.exit_button.grid(row=0, column=0, padx=0)

        # Фрейм для сообщений
        message_frame = ctk.CTkFrame(self.chat_window, fg_color='#1E213D')
        message_frame.grid(row=1, column=1, sticky='nsew', padx=0, pady=0)

        self.message_frame = ctk.CTkScrollableFrame(message_frame, fg_color='#252850')
        self.message_frame.pack(fill="both", expand=True)

        # Фрейм для ввода сообщений и кнопок (внизу)
        input_frame = ctk.CTkFrame(message_frame, fg_color=None)
        input_frame.pack(side="bottom", fill="x", padx=5, pady=5)
        input_frame.grid_columnconfigure(1, weight=1)

        # Загрузка иконок
        paperclip_icon = ctk.CTkImage(light_image=Image.open("Config/paperclip_icon.png").resize((45, 45)), size=(45, 45))
        mic_icon = ctk.CTkImage(light_image=Image.open("Config/microphone_icon.png").resize((45, 45)), size=(30, 30))
        smile_icon = ctk.CTkImage(light_image=Image.open("Config/smile_icon.png").resize((45, 45)), size=(30, 30))
        save_icon = ctk.CTkImage(light_image=Image.open("Config/save_icon.png").resize((45, 45)), size=(30, 30))

        # Кнопка для скрепки
        self.paperclip_button = ctk.CTkButton(input_frame, image=paperclip_icon, command=self.attach_file,
                                              fg_color="transparent", hover=False, width=60, height=60, text="")
        self.paperclip_button.grid(row=0, column=0, padx=(0, 0))

        # Поле для ввода сообщений
        self.message_entry = ctk.CTkTextbox(input_frame, fg_color='#333', text_color='white', font=('Helvetica', 14), height=60)
        self.message_entry.grid(row=0, column=1, sticky='ew', padx=(0, 0))  # sticky='ew' растягивает элемент

        # Заполнитель текста
        self.placeholder_text = "Введите сообщение"
        self.message_entry.insert(tk.END, self.placeholder_text)
        self.message_entry.configure(text_color='grey')  # Цвет заполнителя

        # Кнопки для микрофона, смайлика и сохранения чата
        self.mic_button = ctk.CTkButton(input_frame, image=mic_icon, fg_color="transparent", hover=False, text="",
                                        width=30, height=30)
        self.mic_button.grid(row=0, column=2, padx=(0, 0))

        self.smile_button = ctk.CTkButton(input_frame, image=smile_icon, command=self.open_emoji_menu,
                                          fg_color="transparent", hover=False, width=30, height=30, text="")
        self.smile_button.grid(row=0, column=3, padx=(0, 0))

        self.save_button = ctk.CTkButton(input_frame, image=save_icon, command=lambda: self.save_chat(server_ip),
                                         fg_color="transparent", hover=False, width=30, height=30, text="")
        self.save_button.grid(row=0, column=4, padx=(0, 0))
        self.is_unpressed = False

        def on_mouse_press(event):
            self.is_unpressed = not self.is_unpressed  # Меняем флаг при нажатии кнопки
            self.last_mouse_y = event.y  # Сохраняем координату Y при нажатии
            self.drag_direction = None  # Для отслеживания направления движения мыши
            mouse_y = event.y
            for widget in self.message_frame.winfo_children():
                widget_y_top = widget.winfo_y()
                widget_y_bottom = widget.winfo_y() + widget.winfo_height()
                if widget_y_top <= mouse_y <= widget_y_bottom:
                    widget.toggle_selection()  # Меняем выделение для виджета, на который нажали

        def on_mouse_drag(event):
            mouse_y = event.y
            direction = "down" if mouse_y > self.last_mouse_y else "up"  # Определяем направление движения мыши

            # Если направление изменилось, обновляем флаг
            if self.drag_direction is None:
                self.drag_direction = direction
            elif self.drag_direction != direction:
                self.is_unpressed = not self.is_unpressed
                self.drag_direction = direction

            for widget in self.message_frame.winfo_children():
                widget_y_top = widget.winfo_y()
                widget_y_bottom = widget.winfo_y() + widget.winfo_height()

                # Если курсор находится на виджете
                if widget_y_top <= mouse_y <= widget_y_bottom:
                    if not widget.is_selected and self.is_unpressed:
                        widget.toggle_selection()  # Выделяем, если движемся вниз
                    elif widget.is_selected and not self.is_unpressed:
                        widget.toggle_selection()  # Снимаем выделение при движении вверх

            self.last_mouse_y = mouse_y  # Обновляем последнюю позицию Y

        def chat_allbinds():
            self.message_entry.bind('<FocusIn>', self.on_focus_in)
            self.message_entry.bind('<FocusOut>', self.on_focus_out)
            self.message_entry.bind('<Return>', self.send_message)
            self.message_entry.bind('<Shift-Return>', lambda e: self.message_entry.insert(tk.END, ''))
            self.mic_button.bind('<ButtonPress-1>', self.start_recording)
            self.mic_button.bind('<ButtonRelease-1>', self.stop_recording)
            self.chat_window.bind("<Control-c>", lambda event: self.copy_selected_messages())
            self.message_frame.bind("<Button-1>", lambda event: on_mouse_press(event))
            self.message_frame.bind("<B1-Motion>", lambda event: on_mouse_drag(event))
            self.message_entry.bind('<Control-Left>', abind.move_cursor_left)
            self.message_entry.bind('<Control-Right>', abind.move_cursor_right)
            # Бинды для выделения текста по словам
            self.message_entry.bind('<Control-Shift-Left>', abind.select_word_left)
            self.message_entry.bind('<Control-Shift-Right>', abind.select_word_right)
            self.message_entry.bind("<Control-v>", self.paste_link)

        #Привязываем события
        chat_allbinds()
        # Настройка пропорций сетки
        self.chat_window.grid_rowconfigure(1, weight=1)
        self.chat_window.grid_columnconfigure(1, weight=1)
        self.chat_window.focus_force()
        #   self.message_entry.focus() Не работает. Должно быть выделение фрейма ввода сообщений при заходе

        self.chat_window.protocol("WM_DELETE_WINDOW", self.on_chat_window_close)

    def paste_link(self, event):
        """ Обрабатывает вставку ссылки с заменой на формат [text](url). """
        clipboard_text = self.root.clipboard_get()

        if re.match(r'^(https?|ftp)://|^www\.', clipboard_text):  # Проверка, что это ссылка
            selected_text = self.message_entry.get("sel.first", "sel.last")

            if selected_text:
                self.message_entry.delete("sel.first", "sel.last")
                formatted_link = f"[{selected_text}]({clipboard_text})"
                self.message_entry.insert("insert", formatted_link)

            return "break"  # Остановка стандартной вставки текста

    def on_focus_in(self, event):
        # Удаляем заполнител, если он активен
        if self.message_entry.get("1.0", tk.END).strip() == self.placeholder_text:
            self.message_entry.delete("1.0", tk.END)
            self.message_entry.configure(text_color='white')  # Возвращаем цвет текста

    def on_focus_out(self, event):
        # Восстанавливаем заполнитель, если поле пустое
        if self.message_entry.get("1.0", tk.END).strip() == '':
            self.message_entry.insert(tk.END, self.placeholder_text)
            self.message_entry.configure(text_color='grey')  # Цвет заполнителя

    def copy_selected_messages(self):
        selected_texts = []

        # Собираем тексты всех выделенных сообщений
        for widget in self.message_frame.winfo_children():
            if hasattr(widget, 'is_selected') and widget.is_selected:
                selected_texts.append(widget.text)

        if selected_texts:
            # Проверяем корректность работы с буфером обмена
            try:
                self.chat_window.clipboard_clear()
                self.chat_window.clipboard_append("\n\n".join(selected_texts))
                self.chat_window.update()  # Обновляем буфер обмена
            except Exception as e:
                print(f"Ошибка копирования в буфер: {e}")

    def on_chat_window_close(self):
        if self.active_audio_widget:
            self.active_audio_widget.stop_audio()
            self.active_audio_widget = None
        if self.client:
            self.client.disconnect()  # Отключаем клиента, если он есть
        self.root.deiconify()  # Показать главное окно
        if self.is_hosted:
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
            self.add_message(message, sender="You")
        return 'break'

    def add_message(self, text, sender=""):

        # Сообщения пользователя будут справа, остальные — слева
        if sender == "You":
            message_widget = MessageWidget(self.message_frame, text)
            message_widget.pack(fill="none", padx=5, pady=5, anchor="e")
        else:
            message_widget = MessageWidget(self.message_frame, text, sender)
            message_widget.pack(fill="none", padx=5, pady=5, anchor="w")

        # Прокручиваем вниз, чтобы показывать последнее сообщение
        self.message_frame.update_idletasks()
        self.message_frame._parent_canvas.yview_moveto(1.0)


    def update_user_list(self, users):
        # Очищаем текущие кнопки пользователей
        for widget in self.user_frame.winfo_children():
            widget.destroy()

        # Добавляем новые кнопки для каждого пользователя
        for user in users:
            user_button = UserButtonWidget(self.user_frame, username=user, width=120)  # Фиксированная ширина кнопки
            user_button.pack(pady=2, padx=5, fill='x')

    def show_room_settings(self):
        settings_window = ctk.CTkToplevel(self.root)
        settings_window.title("Room Settings")

        # Для отображения иконки
        settings_window.after(300, lambda: settings_window.iconbitmap(self.application_icon))

        settings_window.geometry("270x180")  # Размер окна для всех элементов
        settings_window.configure(fg_color='black')  # Задаем черный цвет фона
        settings_window.resizable(False, False)

        # Сделать окно поверх всех остальных
        settings_window.attributes('-topmost', True)

        frame = ctk.CTkFrame(settings_window, fg_color='black')
        frame.pack(fill=ctk.BOTH, expand=True, padx=10, pady=10)

        default_room_name, default_password, is_hidden = utils.load_room_settings()

        # Поле ввода имени комнаты
        ctk.CTkLabel(frame, text="Room Name", text_color='white', font=('Helvetica', 12)).grid(row=0, column=0, sticky='w', pady=5)
        room_name_var = ctk.StringVar(value=default_room_name)
        room_name_entry = ctk.CTkEntry(frame, textvariable=room_name_var, fg_color='#333', text_color='white', font=('Helvetica', 12))
        room_name_entry.grid(row=0, column=1, sticky='ew', pady=5)

        # Выпадающий список IP-адресов
        ctk.CTkLabel(frame, text="Host IP", text_color='white', font=('Helvetica', 12)).grid(row=1, column=0, sticky='w', pady=5)

        ip_var = ctk.StringVar()
        available_ips = utils.get_available_ip_addresses()  # Предполагается, что у вас есть эта функция
        ip_combobox = ctk.CTkComboBox(frame, variable=ip_var, values=available_ips, font=('Helvetica', 12))
        ip_combobox.grid(row=1, column=1, sticky='ew', pady=5)
        ip_combobox.set(available_ips[0])  # Устанавливаем первый IP по умолчанию

        # Поле для пароля
        show_password_var = ctk.BooleanVar()
        show_password_checkbox = ctk.CTkCheckBox(frame, text="Password", text_color='white', font=('Helvetica', 12), variable=show_password_var, command=lambda: self.toggle_password_field(password_entry))
        show_password_checkbox.grid(row=2, column=0, sticky='w', pady=5)

        password_var = ctk.StringVar(value=default_password)
        password_entry = ctk.CTkEntry(frame, textvariable=password_var, show="*", fg_color='#333', text_color='white', font=('Helvetica', 12))
        password_entry.grid(row=2, column=1, sticky='ew', pady=5)

        if is_hidden:
            password_entry.grid_remove()  # Скрываем поле для пароля по умолчанию

        # Кнопка создания комнаты
        create_button = ctk.CTkButton(frame, text="Create Room", command=lambda: self.create_room_with_settings(settings_window, room_name_var, password_var, ip_var), fg_color='#333', text_color='white', font=('Helvetica', 12))
        create_button.grid(row=3, column=0, columnspan=2, sticky='ew', pady=10)

        settings_window.bind('<Return>', lambda e: self.create_room_with_settings(settings_window, room_name_var, password_var, ip_var))
        settings_window.focus_force()


    def toggle_password_field(self, password_entry):

        if password_entry.winfo_ismapped():
            password_entry.grid_remove()
        else:
            password_entry.grid()

    def create_room_with_settings(self, settings_window, room_name_var, password_var, ip_var):
        self.server_room_name = room_name_var.get()
        self.server_password = password_var.get()
        self.server_selected_ip = ip_var.get()
        if not self.server_room_name:
            messagebox.showerror("Error", "Please enter a room name")
            settings_window.lift()
            return
        settings_window.destroy()

        self.root.withdraw()

        # Запускаем сервер в отдельном процессе
        self.server_process = Process(target=start_server_process,
                                      args=(self.server_selected_ip, self.server_room_name, self.nickname, self.server_password)
                                      )
        self.server_process.start()
        # Подключаемся как клиент к только что созданной комнате
        if not self.server_selected_ip == "0.0.0.0":
            self.client = textClient.Client(self.server_selected_ip, 36500, self.nickname, self.server_room_name, self.server_password)
        else:
            self.client = textClient.Client("localhost", 36500, self.nickname, self.server_room_name, self.server_password)
        self.is_hosted = True
        self.client.connect()
        self.create_chat_window(self.server_room_name, self.server_selected_ip)  # Передаем IP адрес для заголовка окна
        self.client.start_listening(self.handle_message, self.update_user_list, self.chat_window_name_change, self.receive_file)

    def show_join_room_window(self):
        join_window = ctk.CTkToplevel(self.root)
        join_window.title("Join Room")

        # Для отображения иконки
        join_window.after(300, lambda: join_window.iconbitmap(self.application_icon))

        join_window.geometry("300x150")
        join_window.resizable(False, False)

        # Сделать окно поверх всех остальных
        join_window.attributes('-topmost', True)

        # Создаём фрейм
        frame = ctk.CTkFrame(join_window)
        frame.grid(row=0, column=0, sticky='nsew', padx=10, pady=10)

        # Label для ввода Server IP
        ctk.CTkLabel(frame, text="Server IP", font=('Helvetica', 12)).grid(row=0, column=0, sticky='w', pady=5)

        server_ip_var = ctk.StringVar()
        server_ip_entry = ctk.CTkEntry(frame, textvariable=server_ip_var, font=('Helvetica', 12), width=200)
        server_ip_entry.grid(row=0, column=1, padx=(5, 10), pady=5)

        # Label для ввода Password
        ctk.CTkLabel(frame, text="Password", font=('Helvetica', 12)).grid(row=1, column=0, sticky='w', pady=5)

        password_var = ctk.StringVar()
        password_entry = ctk.CTkEntry(frame, textvariable=password_var, show="*", font=('Helvetica', 12), width=200)
        password_entry.grid(row=1, column=1, padx=(5, 10), pady=5)

        # Кнопка Join Room
        join_button = ctk.CTkButton(frame, text="Join Room", command=lambda: self.join_room(join_window, server_ip_var, password_var, join_button), width=200)
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
        # Проверка, содержит ли сообщение двоеточие
        if ':' in message:
            # Разделяем строку на отправителя и само сообщение
            sender, text = message.split(':', 1)
            sender = f"{sender}:"  # Добавляем двоеточие к имени отправителя
        else:
            # Если двоеточие не найдено, сообщение от сервера
            sender = "Server"
            text = message  # Всё сообщение - это текст

        # Вызываем функцию добавления сообщения с правильным отправителем
        self.add_message(text.strip(), sender=sender)

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
                    join_button.configure(state=tk.NORMAL)

            join_button.configure(state=tk.DISABLED)
            self.root.after(5000, unblock_button)  # 5000 мс = 5 секунд

        # Функция попытки подключения
        def attempt_connection():
            try:
                # Создаем и запускаем клиента
                self.client = textClient.Client(server_ip, port, nickname, "", password)

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
        self.server_room_name = self.client.room_name
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
        messages = self.message_frame.get("1.0", tk.END).strip()

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
        # Проверяем тип файла
        if file_name.lower().endswith((".png", ".jpg", ".jpeg")):
            # Если это изображение, отображаем его в чате
            self.display_image_in_chat(file_path + f"\\{file_name}")
        elif file_name.lower().endswith(".ogg"):
            # Если это аудиофайл
            self.add_audio_message(file_path + f"\\{file_name}")
        else:
            # Добавляем новый FileWidget для файла
            file_widget = FileWidget(self.message_frame, file_name, file_path, sender=sender_nickname)
            file_widget.pack(fill="none", padx=5, pady=5, anchor="w")

        # Прокручиваем вниз, чтобы показывать последнее сообщение
        self.message_frame.update_idletasks()
        self.message_frame._parent_canvas.yview_moveto(1.0)

    def display_image_in_chat(self, file_path):
        try:
            # Открываем изображение и изменяем его размер
            img = Image.open(file_path)
            img.thumbnail((200, 200))  # Ограничиваем размер изображения для чата
            img_ctk = ctk.CTkImage(img)

            # Создаем изображение в текстовом поле
            self.message_frame.image_create("end", image=img_ctk)
            self.message_frame.insert("end", "\n")

            # Сохраняем ссылку на изображение в список, чтобы избежать garbage collection
            if not hasattr(self, 'images'):
                self.images = []  # Инициализируем список, если его ещё нет
            self.images.append(img_ctk)

        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось загрузить изображение: {e}")


    def start_recording(self, event):
        self.VoiceRecorder.start_recording()

    @threaded
    def stop_recording(self, event):
        recording_stop = threading.Thread(target=self.VoiceRecorder.stop_recording, daemon=True)
        recording_stop.start()
        recording_stop.join()
        # Логика отправки файла на сервер после записи
        self.send_voice_message(self.VoiceRecorder.output_file)
        self.add_audio_message(self.VoiceRecorder.output_file)

    def send_voice_message(self, file_path):
        print(f"Отправка голосового сообщения {file_path}")
        file_path = [file_path]
        threading.Thread(target=self.client.send_file, args=(file_path,), daemon=True).start()

    def add_audio_message(self, audio_file):
        """Функция для добавления аудиосообщения в чат."""

        # Получаем размер файла в килобайтах
        file_size_kb = round(os.path.getsize(audio_file) / 1024, 2)  # Преобразуем байты в килобайты

        # Определяем длительность аудиофайла
        with sf.SoundFile(audio_file) as audio:
            frames = len(audio)
            sample_rate = audio.samplerate
            duration_seconds = frames / sample_rate  # Длительность в секундах

        # Создаем Frame для аудиосообщения
        audio_message_frame = ctk.CTkFrame(self.message_frame, fg_color="black")
        audio_message_frame.pack(fill="x", pady=5)

        # Создаем виджет аудиосообщения
        audio_widget = voice.AudioMessageWidget(audio_message_frame, audio_file, duration_seconds, file_size_kb, self)
        audio_widget.pack(fill="x")

        # Прокручиваем чат вниз после добавления аудиосообщения
        self.message_frame.update_idletasks()  # Обновляем, чтобы размеры всех виджетов обновились
        self.message_frame._parent_canvas.yview_moveto(1.0)  # Прокрутка в самый низ


def start_server_process(ip, name, nickname, password):
    try:
        server_process = textServer.Server(ip, 36500, name, nickname, password)
        server_process.start()
    except Exception as e:
        print("Server shutted")



class MessageWidget(ctk.CTkFrame):
    def __init__(self, parent, text, sender=""):
        super().__init__(parent, fg_color="#2c2f33", border_color="#2c2f33", border_width=1)
        self.text = text
        self.is_selected = False  # Флаг выделения

        # Создаем текстовое поле для отображения сообщения
        self.textbox = ctk.CTkTextbox(self, fg_color="#2c2f33", text_color="white", font=('Helvetica', 12), height=2, wrap="word")
        self.textbox.pack(padx=10, pady=5, anchor="w", fill="both", expand=True)

        # Вставляем текст и выделяем ссылки
        self.process_links(f"{sender} {text}")
        self.adjust_textbox_size() # Требуется исправить так как текст задаёт неправильную ширину, нужно для того чтобы избавится от скрола в боксе
        self.textbox.configure(state="disabled")  # Запрещаем редактирование текста пользователем

    def process_links(self, text):
        """Обрабатываем текст, выделяя ссылки синим цветом и добавляя события."""
        self.textbox.insert("1.0", text)

        # Найдем все ссылки в формате [текст](ссылка)
        links = re.finditer(r'\[(.*?)\]\((.*?)\)', text)
        for match in links:
            link_text, link_url = match.groups()
            start_idx = f"1.0 + {match.start()} chars"
            end_idx = f"1.0 + {match.start() + len(link_text)} chars"

            # Удаляем формат [текст](ссылка) и оставляем только текст
            self.textbox.delete(f"1.0 + {match.start()} chars", f"1.0 + {match.end()} chars")
            self.textbox.insert(f"1.0 + {match.start()} chars", link_text)

            # Настраиваем тег для ссылки
            self.textbox.tag_add(link_text, start_idx, end_idx)
            self.textbox.tag_config(link_text, foreground="deepskyblue1", underline=False)
            self.textbox.tag_bind(link_text, "<Enter>", lambda e, tag=link_text: self.textbox.tag_config(tag, underline=True))
            self.textbox.tag_bind(link_text, "<Leave>", lambda e, tag=link_text: self.textbox.tag_config(tag, underline=False))
            self.textbox.tag_bind(link_text, "<Button-1>", lambda e, url=link_url: webbrowser.open(url))

    def update_size(self):
        # Устанавливаем размер фрейма в зависимости от текста
        self.update_idletasks()
        self.configure(width=self.textbox.winfo_width(), height=self.textbox.winfo_height())

    def toggle_selection(self):
        # Переключаем выделение и изменяем цвет фона
        self.is_selected = not self.is_selected
        if self.is_selected:
            self.configure(fg_color="#2c778f")  # Цвет для выделенного сообщения
            self.textbox.configure(fg_color="#2c778f")
        else:
            self.configure(fg_color="#2c2f33")  # Исходный цвет
            self.textbox.configure(fg_color="#2c2f33")

    def adjust_textbox_size(self):
        """Подстраиваем размер текстового виджета под содержимое."""
        # Получаем шрифт, используемый в текстовом виджете
        font = tkFont.Font(family='Helvetica', size=12)
        text = self.text  # Используем текст сообщения
        lines = text.split("\n")
        max_line_width = max(font.measure(line) for line in lines)
        text_height = font.metrics('linespace')  # Высота строки
        num_lines = len(lines)
        max_width = 300  # Максимальная ширина виджета
        padding = 30  # Отступы

        # Вычисляем итоговые размеры с учетом отступов
        new_width = min(max_line_width + padding, max_width)  # Ограничиваем ширину
        new_height = (text_height * num_lines) + padding - (padding // 2)  # Высота виджета

        # Устанавливаем ширину и высоту текстового виджета
        self.textbox.configure(width=new_width, height=new_height)



class UserButtonWidget(ctk.CTkButton):
    def __init__(self, master=None, username="", *args, **kwargs):
        super().__init__(master, text=username, command=self.on_click, *args, **kwargs)
        self.username = username
        self.configure(width=50, font=('Helvetica', 12), fg_color="transparent")
    def on_click(self):
        # Здесь можно добавить обработчик нажатия на кнопку
        print(f"Нажатие на {self.username}")

class FileWidget(ctk.CTkFrame):
    def __init__(self, parent, file_name, file_path, sender="You", *args, **kwargs):
        super().__init__(parent, fg_color="#2c2f33", border_color="#2c2f33", border_width=1, *args, **kwargs)

        self.file_name = file_name
        self.file_path = file_path
        self.is_selected = False
        self.text = f"{sender}: {file_name}"

        # Кнопка с иконкой файла
        #self.file_button = ctk.CTkButton(self, width=35, height=35, image=self.get_file_icon(), text="", command=self.open_file_folder, fg_color=None)
        self.file_button = ctk.CTkButton(self, width=35, height=35, text="📦", command=self.open_file_folder, fg_color=None, corner_radius=100)
        self.file_button.pack(side="left", padx=5, pady=5)

        # Метка с именем файла
        self.label = ctk.CTkLabel(self, text=f"{sender}: {file_name}", fg_color=None, text_color="white", font=('Helvetica', 12), anchor="w")
        self.label.pack(side="left", padx=10, pady=5, fill="both", )

    def get_file_icon(self):
        """Получаем иконку файла (смайлик) в виде изображения."""
        file_icon_path = "📦"  # Укажите путь к иконке документа (png)
        return ctk.CTkImage(file_icon_path, size=(35, 35))  # Преобразуем в иконку нужного размера

    def open_file_folder(self):
        """Открываем проводник с папкой, где находится файл."""
        folder_path = os.getcwd() + f"\\{self.file_path}"
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

    def toggle_selection(self):
        # Переключаем выделение и изменяем цвет фона
        self.is_selected = not self.is_selected
        if self.is_selected:
            self.configure(fg_color="#2c778f")  # Цвет для выделенного сообщения
            self.label.configure(fg_color="#2c778f")
        else:
            self.configure(fg_color="#2c2f33")  # Исходный цвет
            self.label.configure(fg_color="#2c2f33")