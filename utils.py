import os
import socket
import psutil
from PIL import Image, ImageDraw, ImageFont

def save_ip_address(ip_address, file_path='Config/ip_history.txt'):
    try:
        # Читаем существующие IP-адреса из файла
        with open(file_path, 'r') as file:
            existing_ips = file.read().splitlines()
    except FileNotFoundError:
        # Если файла еще нет, считаем, что существующих IP-адресов нет
        existing_ips = []

    # Проверяем, есть ли уже такой IP-адрес в файле
    if ip_address not in existing_ips:
        with open(file_path, 'a') as file:
            file.write(ip_address + '\n')


def load_nickname():
    try:
        with open('Config/nickname.txt', 'r') as nick:
            return nick.read().strip()
    except FileNotFoundError as e:
        return


def save_nickname():
    nickname = input("Enter your nickname: ").strip()

    # Проверяем, существует ли папка 'Config', и создаем её, если нет
    if not os.path.exists('Config'):
        os.makedirs('Config')

    with open('Config/nickname.txt', 'a') as nick:
        nick.write(nickname)

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


def file_save(file_name, file_data, folder_to_save="HOST"):
    # Сохранение файла на сервере
    save_folder = f"Save/{folder_to_save}"
    if not os.path.exists(save_folder):
        os.makedirs(save_folder)

    file_path = os.path.join(save_folder, file_name)
    with open(file_path, "wb") as f:
        f.write(file_data)
        f.close()
        del file_data
    print(f"Файл {file_name} получен и сохранён.")

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
