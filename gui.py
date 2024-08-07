import tkinter as tk
from tkinter import scrolledtext

def initialize_gui(send_message_callback):
    root = tk.Tk()
    root.title("Local Network Chat")
    root.configure(bg='black')

    frame = tk.Frame(root, bg='black')
    frame.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

    chat_window = scrolledtext.ScrolledText(frame, state=tk.DISABLED, wrap=tk.WORD, bg='black', fg='white', font=('Helvetica', 12))
    chat_window.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    user_list = tk.Listbox(frame, bg='black', fg='white', font=('Helvetica', 12), width=20)
    user_list.pack(side=tk.RIGHT, fill=tk.Y)

    message_frame = tk.Frame(root, bg='black')
    message_frame.pack(padx=10, pady=5, fill=tk.X)

    message_entry = tk.Entry(message_frame, bg='#333', fg='white', font=('Helvetica', 12))
    message_entry.pack(padx=10, pady=5, fill=tk.X)
    message_entry.bind('<Return>', send_message_callback)

    return root, chat_window, user_list, message_entry
