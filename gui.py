import tkinter as tk
from tkinter import scrolledtext, messagebox
import pystray
from pystray import MenuItem as item
import threading
from utils import create_custom_icon

class ChatApplication:
    def __init__(self, root):
        self.root = root
        self.root.title("Radmin Chat")
        self.root.geometry("700x500")
        self.root.configure(bg='black')

        # Установка иконки приложения
        self.icon_image = create_custom_icon()
        self.icon_image.save('app_icon.ico')
        self.root.iconbitmap('app_icon.ico')

        self.tray_icon = None

        # Создание фрейма с кнопками
        self.create_buttons_frame()

        # Перехват закрытия окна
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

        tk.Button(button_frame, text="Create Room", command=self.create_room, **button_style).pack(pady=10)
        tk.Button(button_frame, text="Join Room", command=self.join_room, **button_style).pack(pady=10)
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

    def create_chat_window(self, room_name):
        chat_window = tk.Toplevel()
        chat_window.iconbitmap('Config\Radmin Chat.ico')
        chat_window.title(f"{room_name} : server ip")
        chat_window.geometry("800x600")
        chat_window.configure(bg='black')

        # Создаем фрейм для истории сообщений
        history_frame = tk.Frame(chat_window, bg='black')
        history_frame.grid(row=0, column=0, sticky='nsew', padx=5, pady=5)

        self.message_area = scrolledtext.ScrolledText(history_frame, wrap=tk.WORD, bg='black', fg='white', font=('Helvetica', 12), state=tk.DISABLED)
        self.message_area.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Создаем фрейм для списка участников
        user_list_frame = tk.Frame(chat_window, bg='black')
        user_list_frame.grid(row=0, column=1, sticky='ns', padx=5, pady=5)

        self.user_list = tk.Listbox(user_list_frame, bg='black', fg='white', font=('Helvetica', 12))
        self.user_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Создаем фрейм для ввода сообщений
        input_frame = tk.Frame(chat_window, bg='black')
        input_frame.grid(row=1, column=0, columnspan=2, sticky='ew', padx=5, pady=5)

        self.message_entry = tk.Text(input_frame, bg='#333', fg='white', font=('Helvetica', 12), height=3)
        self.message_entry.grid(row=0, column=0, sticky='ew')
        self.message_entry.bind('<Return>', self.send_message)
        self.message_entry.bind('<Shift-Return>', self.insert_newline)
        self.message_entry.bind('<KeyRelease>', self.adjust_text_height)

        chat_window.bind('<Configure>', self.on_resize)
        chat_window.grid_rowconfigure(0, weight=1)
        chat_window.grid_columnconfigure(0, weight=3)
        chat_window.grid_columnconfigure(1, weight=1)

        chat_window.protocol("WM_DELETE_WINDOW", lambda: self.close_chat_window(chat_window))

        # Скрываем главное окно
        self.root.withdraw()

    def close_chat_window(self, window):
        window.destroy()
        # Показываем главное окно
        self.root.deiconify()

    def send_message(self, event=None):
        message = self.message_entry.get("1.0", tk.END).strip()
        if message:
            self.message_area.config(state=tk.NORMAL)
            self.message_area.insert(tk.END, f"You: {message}\n")
            self.message_area.config(state=tk.DISABLED)
            self.message_area.yview(tk.END)
            self.message_entry.delete("1.0", tk.END)
            self.message_entry.configure(height=3)
        return 'break'

    def insert_newline(self, event=None):
        self.message_entry.insert(tk.INSERT, '\n')
        return 'break'

    def adjust_text_height(self, event=None):
        content_height = self.message_entry.get("1.0", 'end-1c').count('\n') + 1
        max_height = 6
        if content_height > 3:
            self.message_entry.configure(height=min(content_height, max_height))
        return 'break'

    def on_resize(self, event):
        self.update_entry_width()
        self.update_user_list_width()

    def update_entry_width(self):
        self.message_entry.config(width=self.message_area.winfo_width())

    def update_user_list_width(self):
        # Получаем ширину фрейма для списка участников
        user_list_frame = self.user_list.master
        user_list_frame_width = self.message_area.winfo_width() // 2
        user_list_frame.config(width=user_list_frame_width)

    def join_room(self):
        messagebox.showinfo("Join Room", "Join Room function called.")

    def ip_list(self):
        messagebox.showinfo("IP List", "IP List function called.")

    def show_room_settings(self):
        settings_window = tk.Toplevel(self.root)
        settings_window.title("Room Settings")
        settings_window.iconbitmap('Config\Radmin Chat.ico')
        settings_window.configure(bg='black')
        settings_window.geometry("300x200")
        settings_window.resizable(False, False)

        frame = tk.Frame(settings_window, bg='black')
        frame.grid(row=0, column=0, sticky='nsew', padx=10, pady=10)

        tk.Label(frame, text="Room Name", fg='white', bg='black', font=('Helvetica', 12)).grid(row=0, column=0, sticky='w', pady=5)
        room_name_var = tk.StringVar()
        room_name_entry = tk.Entry(frame, textvariable=room_name_var, bg='#333', fg='white', font=('Helvetica', 12))
        room_name_entry.grid(row=0, column=1, sticky='ew', pady=5)

        password_var = tk.IntVar()
        password_checkbox = tk.Checkbutton(frame, text="Password", variable=password_var, fg='white', bg='black', font=('Helvetica', 12), command=lambda: self.toggle_password_field(password_var))
        password_checkbox.grid(row=1, column=0, columnspan=2, sticky='w', pady=5)

        self.password_entry_var = tk.StringVar()
        self.password_entry = tk.Entry(frame, textvariable=self.password_entry_var, show="*", bg='#333', fg='white', font=('Helvetica', 12))
        self.password_entry.grid(row=2, column=0, columnspan=2, sticky='ew', pady=5)

        create_button = tk.Button(frame, text="Create Room", command=lambda: self.create_room_with_settings(settings_window, room_name_var, self.password_entry_var, password_var), bg='#333', fg='white', font=('Helvetica', 12))
        create_button.grid(row=3, column=0, columnspan=2, sticky='ew', pady=10)

        settings_window.bind('<Return>', lambda event: self.create_room_with_settings(settings_window, room_name_var, self.password_entry_var, password_var))

        self.toggle_password_field(password_var)

    def toggle_password_field(self, password_var):
        if password_var.get():
            self.password_entry.grid()
        else:
            self.password_entry.grid_remove()

    def create_room_with_settings(self, settings_window, room_name_var, password_var, password_checkbox):
        room_name = room_name_var.get()
        password = password_var.get()

        if not room_name:
            messagebox.showerror("Error", "Please enter a room name")
            settings_window.lift()
            return

        if password_checkbox.get() and not password:
            messagebox.showerror("Error", "Please enter a password")
            settings_window.lift()
            return

        settings_window.destroy()
        self.create_chat_window(room_name)

    def create_room(self):
        self.show_room_settings()

if __name__ == "__main__":
    root = tk.Tk()
    app = ChatApplication(root)
    root.mainloop()
