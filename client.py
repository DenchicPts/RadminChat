import socket
import threading
import time
import os
import gc
import database
import utils

class Client:
    def __init__(self, host, port, nickname, room_name="", password=""):
        self.host = host
        self.port = port
        self.nickname = nickname
        self.room_name = room_name
        self.password = password
        self.socket = None
        # GUI Function
        self.message_callback = None
        self.update_user_list = None
        self.window_name_change = None
        self.file_callback = None
        # Boolean
        self.authenticated = False
        self.stop_file_transfer = False

        print(host)

    def connect(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((self.host, self.port))
        self.send_message(f"{self.nickname }*{self.room_name}*{self.password}")

    def start_listening(self, callback, update_list, name_change, receive_file_gui):
        self.message_callback = callback
        self.update_user_list = update_list
        self.window_name_change = name_change
        self.file_callback = receive_file_gui
        threading.Thread(target=self.listen_for_messages, daemon=True).start()

    def listen_for_messages(self):
        file_accepted = False
        is_txt_file = False
        while True:
            try:

                message = self.socket.recv(1024 * 10000)
                try:
                    message = message.decode('utf-8')
                    decoded_message = True
                except UnicodeDecodeError:
                    decoded_message = False


                if message and decoded_message and not is_txt_file:
                    print(f"CLIENT Received {message}")
                    if "Invalid password" in message:
                        print("Invalid password")
                        self.socket.close()
                        break
                    elif message.startswith("#ROOMNAME#"):
                        self.room_name = message[len("#ROOMNAME#"):]
                        self.window_name_change()
                        self.authenticated = True  # Аутентификация успешна
                        database.save_connection(True, self.host, self.room_name)
                        # print(f"Connected to room: {self.room_name}")

                    elif message.startswith("#USERS_IP#"):
                        users = message[len("#USERS_IP#"):].strip().split("\n")
                        if self.message_callback:
                            database.parse_users_info(users)
                            self.update_user_list(users)

                    elif message.startswith("FILE:"):
                        parts = message.split(":")
                        sender_nickname = parts[1]  # Получаем никнейм отправителя
                        file_name = parts[2]
                        file_size = int(parts[3])
                        file_counts = int(parts[4])
                        received_size = 0
                        file_accepted = True
                        file_thread = None

                        if file_name.lower().endswith(".txt") or file_name.lower().endswith(".java"):
                            is_txt_file = True

                    elif message.startswith("#MESSAGE#"):
                        message_to_send = message[len("#MESSAGE#"):].strip()
                        self.message_callback(message_to_send)

                    elif message.startswith("#FILE_EXISTS#"):
                        # Сервер сообщил, что файл уже существует
                        file_name = message[len("#FILE_EXISTS#"):].strip()
                        print(f"Файл {file_name} уже существует на сервере. Передача отменена.")
                        self.stop_file_transfer = True  # Устанавливаем флаг для остановки передачи



                elif message and not decoded_message or is_txt_file:
                    if file_thread:
                        file_thread.join()

                    if not is_txt_file:
                        file_thread = threading.Thread(target=utils.save_file_chunk, args=(file_name, message, self.host,), daemon=True)
                        file_thread.start()
                    else:
                        utils.receive_file_txt(message, file_name, self.host)

                    received_size += len(message)

                    if received_size >= file_size and file_accepted:
                        if file_thread:
                            file_thread.join()

                        if not is_txt_file:
                            finalizing_file = threading.Thread(target=utils.finalize_file, args=(file_name, self.host,), daemon=True)
                            finalizing_file.start()
                            finalizing_file.join()

                        is_txt_file = False
                        file_accepted = False
                        received_size = 0



                        file_path = f"Save\\{self.host}"
                        if self.file_callback:
                            self.file_callback(file_name, file_path, sender_nickname)

                else:
                    break
            except Exception as e:
                print(f"Error receiving message: {e}")
                break

    def send_message(self, message):
        if self.socket:
            self.socket.send(message.encode('utf-8'))

    def disconnect(self):
        # Останавливаем прослушивание и закрываем сокет
        self.listening = False
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
            self.socket = None

    def connect_with_timeout(self, timeout=3):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.settimeout(1)  # Устанавливаем тайм-аут в 1 секунду на попытку подключения

        self.authenticated = False
        for _ in range(timeout):
            try:
                self.socket.connect((self.host, self.port))
                self.authenticated = True
                break
            except (socket.timeout, socket.error) as e:
                print(f"Connection attempt failed: {e}")
                time.sleep(1)

        self.socket.settimeout(None)  # Сбрасываем тайм-аут после подключения
        if self.authenticated:
            self.send_message(f"{self.nickname}*{self.room_name}*{self.password}")
            message = self.socket.recv(1024).decode('utf-8')
            print(f"Connect with timeout ///{message}")
            if message == "Invalid password":
                self.authenticated = False

        return self.authenticated


    # Заготовка под большое количество файлов
    def send_file(self, file_paths):
        file_paths = list(file_paths)

        for file_path in file_paths:
            self.send_file_thread(file_path, len(file_paths))

#       while file_paths:  Вариант отправки 2
#           file_path = file_paths.pop(0)
#           self.send_file_thread(file_path)


    def send_file_thread(self, file_path, file_counts):
        try:
            file_name = os.path.basename(file_path)
            file_size = os.path.getsize(file_path)
            chunk_size = 1024 * 10000  # 10 MB

            # Отправка заголовка с информацией о файле
            file_info_message = f"FILE:{self.nickname}:{file_name}:{file_size}:{file_counts}"
            self.socket.send(file_info_message.encode('utf-8'))
            time.sleep(0.1)

            # Отправляем файл чанками
            with open(file_path, "rb") as f:
                sent_size = 0
                while sent_size < file_size:
                    if self.stop_file_transfer:
                        print(f"Передача файла {file_name} остановлена")
                        self.stop_file_transfer = False
                        return  # Остановка передачи файла

                    chunk = f.read(chunk_size)
                    if not chunk:
                        break  # Если больше нечего читать, выходим из цикла

                    self.socket.sendall(chunk)
                    sent_size += len(chunk)
                    del chunk
                    time.sleep(0.01)

            print(f"Файл {file_name} отправлен на сервер.")
            time.sleep(1.5) # В случае чего увеличить задержку(зависит от качества соединения)
        except Exception as e:
            print(f"Ошибка при отправке файла: {e}")



    def create_chat_window(self, room_name, server_ip):
        self.chat_window = ctk.CTkToplevel()
        self.chat_window.iconbitmap('Config/Radmin Chat.ico')
        self.chat_window.title(f"{room_name} : {server_ip}")
        self.chat_window.geometry("800x600")

        # Фрейм для списка пользователей справа
        user_list_frame = ctk.CTkFrame(self.chat_window, fg_color='black', width=200)
        user_list_frame.grid(row=0, column=2, rowspan=2, sticky='ns', padx=5, pady=5)

        # Заголовок для списка пользователей
        self.user_list_label = ctk.CTkLabel(user_list_frame, text="Список пользователей", text_color='white')
        self.user_list_label.pack(pady=(0, 10))

        # Создаем Canvas для списка пользователей
        self.user_canvas = ctk.CTkCanvas(user_list_frame, bg='black', width=200)
        self.user_canvas.pack(side=ctk.LEFT, fill=ctk.BOTH, expand=True)

        # Прокрутка для списка пользователей
        self.user_scrollbar = ctk.CTkScrollbar(user_list_frame, orientation="vertical", command=self.user_canvas.yview)
        self.user_canvas.configure(yscrollcommand=self.user_scrollbar.set)
        self.user_scrollbar.pack(side="right", fill="y")

        # Фрейм внутри Canvas для размещения виджетов с пользователями
        self.user_frame = ctk.CTkFrame(self.user_canvas, fg_color='black')
        self.user_canvas.create_window((0, 0), window=self.user_frame, anchor='nw')

        # Обновляем размер Canvas при изменении содержимого фрейма
        self.user_frame.bind("<Configure>", lambda event: self.user_canvas.configure(scrollregion=self.user_canvas.bbox("all")))

        # Фрейм слева (синий)
        left_frame = ctk.CTkFrame(self.chat_window, fg_color='blue', width=30)
        left_frame.grid(row=0, column=0, rowspan=2, sticky='ns', padx=5, pady=5)

        # Фрейм для верхней панели с кнопками (красный)
        top_buttons_frame = ctk.CTkFrame(self.chat_window, fg_color='red', height=50)
        top_buttons_frame.grid(row=0, column=1, sticky='ew', padx=5, pady=5)

        self.exit_button = ctk.CTkButton(top_buttons_frame, text="Выход", command=self.on_chat_window_close, fg_color=None, hover_color=None, text_color="white")
        self.exit_button.pack(side=ctk.LEFT, padx=5)

        # Создаем Canvas для сообщений
        self.history_canvas = ctk.CTkCanvas(self.chat_window, bg='white')
        self.history_canvas.grid(row=1, column=1, sticky='nsew', padx=5, pady=5)

        # Добавляем прокрутку отдельно от канваса
        self.scrollbar = ctk.CTkScrollbar(self.chat_window, orientation="vertical", command=self.history_canvas.yview)
        self.scrollbar.grid(row=1, column=2, sticky='ns')  # Размещаем скроллбар рядом с канвасом

        # Настраиваем канвас, чтобы он реагировал на скроллбар
        self.history_canvas.configure(yscrollcommand=self.scrollbar.set)

        # Фрейм для сообщений внутри Canvas
        self.message_frame = ctk.CTkFrame(self.history_canvas, fg_color='red')

        # Функция для динамической подстройки ширины фрейма
        def resize_message_frame(event):
            canvas_width = event.width
            self.history_canvas.itemconfig(self.message_frame_window, width=canvas_width)

        # Размещаем фрейм в Canvas
        self.message_frame_window = self.history_canvas.create_window((0, 0), window=self.message_frame, anchor='nw')

        # Привязываем изменение размера канваса к функции изменения фрейма
        self.history_canvas.bind("<Configure>", resize_message_frame)

        # Настраиваем скроллинг, чтобы он работал корректно
        self.message_frame.bind("<Configure>", lambda event: self.history_canvas.configure(scrollregion=self.history_canvas.bbox("all")))

        # Фрейм для ввода сообщений (внизу)
        input_frame = ctk.CTkFrame(self.chat_window, fg_color=None)
        input_frame.grid(row=2, column=1, columnspan=2, sticky='ew', padx=5, pady=5)

        # Загрузка иконок с корректировкой их размера до 35x35, используем CTkImage
        paperclip_icon = ctk.CTkImage(light_image=Image.open("Config/paperclip_icon.png").resize((45, 45)))
        mic_icon = ctk.CTkImage(light_image=Image.open("Config/microphone_icon.png").resize((45, 45)))
        smile_icon = ctk.CTkImage(light_image=Image.open("Config/smile_icon.png").resize((45, 45)))
        save_icon = ctk.CTkImage(light_image=Image.open("Config/save_icon.png").resize((45, 45)))

        # Создание кнопки для скрепки
        self.paperclip_button = ctk.CTkButton(input_frame, image=paperclip_icon, command=self.attach_file, fg_color="transparent", hover_color=None, width=60, height=60, text="", border_width=0)
        self.paperclip_button.pack(side=ctk.LEFT, padx=(0, 5))

        # Поле для ввода сообщений
        self.message_entry = ctk.CTkTextbox(input_frame, fg_color='#333', text_color='white', font=('Helvetica', 14), height=10, width=60)
        self.message_entry.pack(side=ctk.LEFT, fill=ctk.BOTH, expand=True)
        self.message_entry.bind('<Return>', self.send_message)
        self.message_entry.bind('<Shift-Return>', lambda e: self.message_entry.insert(tk.END, ''))

        # Создание кнопок для микрофона, смайлика и сохранения чата
        self.mic_button = ctk.CTkButton(input_frame, image=mic_icon, fg_color="transparent", hover_color=None, text="", width=60, height=60, border_width=0)
        self.mic_button.pack(side=ctk.LEFT, padx=(5, 5))
        self.mic_button.bind('<ButtonPress-1>', self.start_recording)
        self.mic_button.bind('<ButtonRelease-1>', self.stop_recording)

        self.smile_button = ctk.CTkButton(input_frame, image=smile_icon, command=self.open_emoji_menu, fg_color="transparent", hover_color=None, width=60, height=60, text="", border_width=0)
        self.smile_button.pack(side=ctk.LEFT, padx=(5, 5))

        self.save_button = ctk.CTkButton(input_frame, image=save_icon, command=lambda: self.save_chat(server_ip), fg_color="transparent", hover_color=None, width=60, height=60, text="", border_width=0)
        self.save_button.pack(side=ctk.LEFT, padx=(5, 0))

        # Настройка пропорций сетки
        self.chat_window.grid_rowconfigure(1, weight=1)
        self.chat_window.grid_columnconfigure(1, weight=1)
        self.chat_window.focus_force()
        self.chat_window.protocol("WM_DELETE_WINDOW", self.on_chat_window_close)
