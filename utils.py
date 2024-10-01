import json
import os
import socket
import sqlite3
import threading

import psutil
from PIL import Image, ImageDraw, ImageFont


def save_nickname_settings(filename="settings.json"):
    nickname = input("Enter your nickname: ").strip()
    if not os.path.exists(filename):
        # Если файл не существует, создаём новый с пустым содержимым
        data = {}
    else:
        # Если файл существует, читаем его содержимое
        with open(filename, "r") as file:
            data = json.load(file)

    # Обновляем данные
    data["nickname"] = nickname

    # Сохраняем обновлённые данные в файл
    with open(filename, "w") as file:
        json.dump(data, file, indent=4)

    return nickname

def create_custom_icon():
    # Размер иконки
    size = (64, 64)

    # Создаем новое изображение с прозрачным фоном
    image = Image.new('RGBA', size, color=(0, 0, 0, 0))
    draw = ImageDraw.Draw(image)

    # Определяем шрифт и размер
    try:
        # Загружаем стандартный шрифт
        font = ImageFont.truetype("georgia.ttf", 32)
    except IOError:
        # Если стандартный шрифт не доступен, используем шрифт по умолчанию
        font = ImageFont.load_default()

    # Текст и его размер
    text = "RC"
    # Получаем размеры текста
    text_bbox = draw.textbbox((0, 0), text, font=font)
    text_width = text_bbox[2] - text_bbox[0]
    text_height = text_bbox[3] - text_bbox[1]

    # Позиционируем текст в центре, но с корректировкой по вертикали
    vertical_offset = -5  # Параметр для подъема текста (отрицательное значение поднимет текст)
    text_position = ((size[0] - text_width) // 2, (size[1] - text_height) // 2 + vertical_offset)

    # Рисуем круг с белым фоном
    draw.ellipse([0, 0, size[0], size[1]], fill=(0, 0, 0, 0), outline=(255, 255, 255), width=2)

    # Создаем маску для круга
    mask = Image.new('L', size, 0)
    mask_draw = ImageDraw.Draw(mask)
    mask_draw.ellipse([0, 0, size[0], size[1]], fill=255)

    # Применяем маску к изображению
    image.putalpha(mask)

    # Рисуем текст на изображении
    draw.text(text_position, text, font=font, fill=(255, 255, 255))

    return image

def get_ip_list():
    try:
        with open('Config/ip_history.txt', 'r') as file:
            return file.readlines()
    except FileNotFoundError:
        return []


def get_available_ip_addresses():
    ip_addresses = []

    # Добавляем 0.0.0.0 как общий IP
    ip_addresses.append("0.0.0.0")
    try:
        # Получаем локальные IP-адреса сетевых интерфейсов
        for iface_name, iface_addresses in psutil.net_if_addrs().items():
            for address in iface_addresses:
                if address.family == socket.AF_INET:
                    ip_addresses.append(address.address)
    except Exception as e:
        print(e)
    return ip_addresses

def save_room_settings(room_name, password, filename="settings.json"):
    # Проверяем, существует ли файл
    if not os.path.exists(filename):
        # Если файл не существует, создаём новый с пустым содержимым
        data = {}
    else:
        # Если файл существует, читаем его содержимое
        with open(filename, "r") as file:
            data = json.load(file)

    # Обновляем данные
    data["room_name"] = room_name
    data["password"] = password
    if password:
        data["is_hidden_password_BT"] = False
    else:
        data["is_hidden_password_BT"] = True

    # Сохраняем обновлённые данные в файл
    with open(filename, "w") as file:
        json.dump(data, file, indent=4)

def load_room_settings(filename="settings.json"):
    # Проверяем, существует ли файл
    if not os.path.exists(filename):
        return None, None, None

    # Читаем данные из файла
    with open(filename, "r") as file:
        data = json.load(file)

    # Возвращаем название комнаты, если оно существует
    return data.get("room_name", ""), data.get("password", ""), data.get("is_hidden_password_BT", "")


def load_nickname_settings(filename="settings.json"):
    # Проверяем, существует ли файл
    if not os.path.exists(filename):
        return None


    # Читаем данные из файла
    with open(filename, "r") as file:
        data = json.load(file)

    return data.get("nickname", "")

def file_exists(file_name, file_size):
    # Путь к файлу в папке Save/HOST
    file_path = os.path.join("Save", "HOST", file_name)
    # Проверяем, существует ли файл и совпадает ли его размер
    if os.path.exists(file_path):
        existing_size = os.path.getsize(file_path)
        return existing_size == file_size
    return False

def save_file_chunk(file_name, file_data, folder_to_save="HOST"):
    # Создание папки, если её нет
    save_folder = f"Save/{folder_to_save}"
    if not os.path.exists(save_folder):
        os.makedirs(save_folder)

    # Формируем временное имя файла с расширением .temp
    temp_file_name = f"{file_name}.temp"
    file_path = os.path.join(save_folder, temp_file_name)

    # Открываем файл в режиме добавления бинарных данных
    with open(file_path, "ab") as f:
        f.write(file_data)  # Добавляем новую порцию данных

def finalize_file(file_name, folder_to_save="HOST"):
    # Переименование файла с .temp на исходное имя
    save_folder = f"Save/{folder_to_save}"
    temp_file_name = f"{file_name}.temp"
    temp_file_path = os.path.join(save_folder, temp_file_name)
    final_file_path = os.path.join(save_folder, file_name)

    if os.path.exists(temp_file_path):
    # Проверка, существует ли файл с таким именем и размерами
        if os.path.exists(final_file_path):
            temp_size = os.path.getsize(temp_file_path)
            final_size = os.path.getsize(final_file_path)
            if temp_size == final_size:
                # Удаляем временный файл
                os.remove(temp_file_path)
                #print(f"Файл {final_file_path} уже существует с тем же размером. Временный файл {temp_file_name} удалён.")
                return


        os.rename(temp_file_path, final_file_path)
        print(f"Файл {file_name} полностью получен")
    else:
        print(f"Ошибка: временный файл {temp_file_name} не найден.")

def receive_file_txt(file_data, file_name, folder_to_save="HOST"):
    # Запись данных в файл в режиме добавления (append)
    save_folder = f"Save/{folder_to_save}"
    os.makedirs(save_folder, exist_ok=True)

    file_path = os.path.join(save_folder, file_name)
    print(file_data)
    with open(file_path, 'a', encoding='utf-8') as file:
        for line in file_data.splitlines():
            file.write(line + '\n')
    print(f"Файл {file_name} сохранён")


def threaded(func):
    """Декоратор для выполнения функции в отдельном потоке"""
    def wrapper(*args, **kwargs):
        thread = threading.Thread(target=func, args=args, kwargs=kwargs, daemon=True)
        thread.start()
    return wrapper
