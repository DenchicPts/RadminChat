import multiprocessing
import os
import tkinter as tk
import gui
import utils
import database


def main():
    save_folder = "Config"
    database.init_db()
    if not os.path.exists(save_folder):
        os.makedirs(save_folder)

    nickname = utils.load_nickname_settings()
    if nickname == None:
        nickname = utils.save_nickname_settings()

    print("##ORIGIN##")
    # Запуск GUI
    root = tk.Tk()
    app = gui.ChatApplication(root, nickname)
    root.mainloop()

if __name__ == "__main__":
    multiprocessing.freeze_support()    # Необходимая фигня для того чтобы создание новых процессов было бы возможным
    main()
