import os
import tkinter as tk
import gui
import utils


def main():
    save_folder = "Config"
    if not os.path.exists(save_folder):
        os.makedirs(save_folder)

    nickname = utils.load_nickname_settings()
    if nickname == None:
        nickname = utils.save_nickname_settings()


    # Запуск GUI
    root = tk.Tk()
    app = gui.ChatApplication(root, nickname)
    root.mainloop()

if __name__ == "__main__":
    main()
