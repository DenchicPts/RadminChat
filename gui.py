import tkinter as tk
from tkinter import scrolledtext, messagebox
import pystray
from pystray import MenuItem as item
import threading
from utils import create_custom_icon

# Глобальная переменная для иконки
tray_icon = None

# Функция для выхода из программы
def quit_window(icon, item):
    icon.stop()
    root.quit()  # Завершаем основной цикл Tkinter
    root.destroy()  # Закрываем главное окно

# Функция для сворачивания окна в трей
def hide_window():
    global tray_icon
    root.withdraw()  # Скрыть главное окно
    tray_icon = create_tray_icon()  # Создать иконку в трее

# Функция для отображения окна из трея
def show_window(icon, item):
    global tray_icon
    if tray_icon is not None:
        tray_icon.stop()  # Остановить иконку в трее
        tray_icon = None  # Сбрасываем значение
    root.deiconify()  # Показать главное окно

# Функция для создания иконки трея
def create_tray_icon():
    icon_image = create_custom_icon()
    menu = (item('Show', show_window), item('Quit', quit_window))
    icon = pystray.Icon("test", icon_image, "Radmin Chat", menu)
    threading.Thread(target=icon.run, daemon=True).start()
    return icon

# Функция для открытия окна чата
def create_chat_window():
    # Создаем новое окно
    chat_window = tk.Toplevel()
    chat_window.title("Chat Room")
    chat_window.geometry("800x600")
    chat_window.configure(bg='black')

    # Создаем фрейм для истории сообщений
    history_frame = tk.Frame(chat_window, bg='black')
    history_frame.grid(row=0, column=0, sticky='nsew', padx=5, pady=5)

    # Создаем виджет ScrolledText для истории сообщений
    global message_area
    message_area = scrolledtext.ScrolledText(history_frame, wrap=tk.WORD, bg='black', fg='white', font=('Helvetica', 12), state=tk.DISABLED)
    message_area.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    # Создаем фрейм для списка участников
    global user_list_frame
    user_list_frame = tk.Frame(chat_window, bg='black')
    user_list_frame.grid(row=0, column=1, sticky='ns', padx=5, pady=5)

    # Создаем виджет Listbox для списка участников
    global user_list
    user_list = tk.Listbox(user_list_frame, bg='black', fg='white', font=('Helvetica', 12))
    user_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    # Создаем фрейм для ввода сообщений
    input_frame = tk.Frame(chat_window, bg='black')
    input_frame.grid(row=1, column=0, columnspan=2, sticky='ew', padx=5, pady=5)

    # Создаем виджет Text для ввода сообщений
    global message_entry
    message_entry = tk.Text(input_frame, bg='#333', fg='white', font=('Helvetica', 12), height=3)
    message_entry.grid(row=0, column=0, sticky='ew')
    message_entry.bind('<Return>', send_message)
    message_entry.bind('<Shift-Return>', insert_newline)

    # Настраиваем ограничение на высоту
    message_entry.bind('<KeyRelease>', adjust_text_height)

    # Обновляем размеры при изменении окна
    chat_window.bind('<Configure>', on_resize)

    # Настроим веса колонок и строк
    chat_window.grid_rowconfigure(0, weight=1)
    chat_window.grid_columnconfigure(0, weight=3)
    chat_window.grid_columnconfigure(1, weight=1)

    chat_window.protocol("WM_DELETE_WINDOW", lambda: close_chat_window(chat_window))

def close_chat_window(window):
    window.destroy()
    show_window(None, None)

def send_message(event=None):
    message = message_entry.get("1.0", tk.END).strip()
    if message:
        message_area.config(state=tk.NORMAL)
        message_area.insert(tk.END, f"You: {message}\n")
        message_area.config(state=tk.DISABLED)
        message_area.yview(tk.END)
        message_entry.delete("1.0", tk.END)
        message_entry.configure(height=3)  # Сброс высоты поля ввода сообщений
    return 'break'

def insert_newline(event=None):
    message_entry.insert(tk.INSERT, '\n')
    return 'break'

def adjust_text_height(event=None):
    # Изменение высоты поля ввода сообщений в зависимости от количества строк
    content_height = message_entry.get("1.0", 'end-1c').count('\n') + 1
    max_height = 6  # Максимум 6 строк
    if content_height > 3:
        message_entry.configure(height=min(content_height, max_height))  # Устанавливаем высоту
    return 'break'

def on_resize(event):
    update_entry_width()
    update_user_list_width()

def update_entry_width():
    # Устанавливаем ширину для поля ввода сообщений, равную ширине истории сообщений
    message_entry.config(width=message_area.winfo_width())

def update_user_list_width():
    # Динамическое увеличение ширины списка пользователей
    user_list_frame_width = message_area.winfo_width() // 2
    user_list_frame.config(width=user_list_frame_width)

# Функция для создания комнаты
def create_room():
    root.withdraw()  # Скрываем главное окно
    create_chat_window()  # Создаем окно чата

# Функция для подключения к комнате
def join_room():
    messagebox.showinfo("Join Room", "Join Room function called.")

# Функция для отображения списка IP
def ip_list():
    messagebox.showinfo("IP List", "IP List function called.")

# Создаем главное окно
root = tk.Tk()
root.title("Radmin Chat")
root.geometry("700x500")
root.configure(bg='black')  # Установка черного фона

# Установка иконки приложения
icon_image = create_custom_icon()
icon_image.save('app_icon.ico')
root.iconbitmap('app_icon.ico')

# Создаем фрейм для размещения кнопок
button_frame = tk.Frame(root, bg='black')
button_frame.pack(pady=50, fill=tk.X)

# Создаем кнопки
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

tk.Button(button_frame, text="Create Room", command=create_room, **button_style).pack(pady=10)
tk.Button(button_frame, text="Join Room", command=join_room, **button_style).pack(pady=10)
tk.Button(button_frame, text="IP List", command=ip_list, **button_style).pack(pady=10)

# Перехватываем закрытие окна
root.protocol("WM_DELETE_WINDOW", hide_window)

# Запускаем главное окно
root.mainloop()
