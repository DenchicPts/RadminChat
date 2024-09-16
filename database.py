import sqlite3


def init_db():
    conn = sqlite3.connect('connections.db')  # Подключаемся к базе данных (если её нет, она будет создана)
    cursor = conn.cursor()

    # Создаём таблицу, если она не существует
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS connections (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            type TEXT NOT NULL,
            ip TEXT NOT NULL,
            nickname_or_room TEXT
        )
    ''')

    conn.commit()
    conn.close()

def save_connection(is_server, ip, nickname_or_room):
    conn = sqlite3.connect('connections.db')
    cursor = conn.cursor()

    # Определяем тип (сервер или клиент)
    connection_type = 'Server' if is_server else 'Client'

    # Проверяем, существует ли запись с таким же ником и IP
    cursor.execute('''
        SELECT * FROM connections WHERE nickname_or_room = ? AND ip = ?
    ''', (nickname_or_room, ip))

    existing_entry = cursor.fetchone()

    if existing_entry:
        ...
        #print(f"Запись с ником {nickname_or_room} и IP {ip} уже существует.")
    else:
        # Если записи нет, то добавляем новую
        cursor.execute('''
            INSERT INTO connections (type, ip, nickname_or_room)
            VALUES (?, ?, ?)
        ''', (connection_type, ip, nickname_or_room))
        conn.commit()
        #print(f"Запись {nickname_or_room} - {ip} добавлена.")

    conn.close()

def parse_users_info(user_info_list):
    parsed_users = []

    for user_info in user_info_list:
        user_info = user_info.strip()  # Убираем лишние пробелы у каждой строки
        try:
            nickname, ip = user_info.split(" - ")
            save_connection(False, ip, nickname)
            parsed_users.append((nickname, ip))
        except ValueError:
            print(f"Некорректный формат строки: {user_info}")

    return parsed_users

