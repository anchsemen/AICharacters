import sqlite3


conn = sqlite3.connect("chat_history.db")
cursor = conn.cursor()
cursor.execute("""
CREATE TABLE IF NOT EXISTS messages (
    user_id TEXT,
    message TEXT,
    sender TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
)
""")
conn.commit()


cursor.execute('''
    CREATE TABLE IF NOT EXISTS recall_memories (
        id TEXT PRIMARY KEY,
        user_id TEXT,
        memory TEXT,
        embedding BLOB
    )
''')
conn.commit()


def save_message_to_db(user_id, message, sender):
    cursor.execute("""
    INSERT INTO messages (user_id, message, sender)
    VALUES (?, ?, ?)
    """, (user_id, message, sender))
    conn.commit()


def load_history_from_db(user_id):
    cursor.execute("""
    SELECT message, sender FROM messages
    WHERE user_id = ?
    ORDER BY timestamp DESC
    LIMIT 10
    """, (user_id,))
    results = cursor.fetchall()
    print(results)
    return results[::-1]


def load_other_history_from_db(user_id):
    cursor.execute("""
    SELECT message, sender
    FROM messages
    WHERE user_id = ?
    ORDER BY timestamp
    """, (user_id,))
    all_messages = cursor.fetchall()

    return [{"sender": row[1], "content": row[0]} for row in all_messages]


def save_user_information(user_id: int, info: dict):
    """add new information about user"""
    try:
        # Создаем подключение к базе данных
        conn = sqlite3.connect('user_data.db')
        cursor = conn.cursor()

        # Создаем таблицу preferences, если она не существует
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS preferences (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT,
                value TEXT
            )
        ''')

        # Вставляем предпочтения в базу данных
        for item in info.values():
            cursor.execute('''
                INSERT INTO preferences (user_id, value)
                VALUES (?, ?)
            ''', (user_id, item))

        conn.commit()

    except sqlite3.Error as e:
        print(f"Ошибка базы данных: {e}")
        return f"Ошибка при сохранении данных: {e}"

    finally:
        conn.close()

    return "Информация о пользователе сохранена в базе данных"
