import os


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
