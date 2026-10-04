import sqlite3
from datetime import datetime


class Database:
    """Класс для работы с SQLite-базой данных ресторана: пользователи, меню, заказы, корзина и адреса."""

    def __init__(self, db_name="restaurant.db"):
        """Инициализирует подключение и создаёт таблицы при первом запуске."""
        self.db_name = db_name
        self.init_db()

    def get_conn(self):
        """Возвращает активное соединение с БД, создаёт его при необходимости."""
        if not hasattr(self, '_conn') or self._conn is None:
            self._conn = sqlite3.connect(self.db_name)
            self._conn.row_factory = sqlite3.Row
        return self._conn

    @property
    def cursor(self):
        """Возвращает курсор для выполнения SQL-запросов."""
        return self.get_conn().cursor()

    def init_db(self):
        """Выполняет инициализацию: создаёт таблицы и добавляет тестовые данные при необходимости."""
        try:
            self._create_tables()
            self._ensure_test_data()
        except Exception as e:
            print(f"Ошибка инициализации БД: {e}")

    def _create_tables(self):
        """Создаёт все необходимые таблицы, если они ещё не существуют."""
        c = self.cursor

        c.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                phone TEXT,
                password TEXT NOT NULL,
                role TEXT DEFAULT 'customer',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )''')

        c.execute('''
            CREATE TABLE IF NOT EXISTS addresses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                address TEXT NOT NULL UNIQUE
            )''')

        c.execute('''
            CREATE TABLE IF NOT EXISTS menu (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                price REAL NOT NULL,
                image BLOB,
                is_available BOOLEAN DEFAULT 1,
                grams INTEGER DEFAULT 0,
                calories REAL DEFAULT 0,
                proteins REAL DEFAULT 0,
                fats REAL DEFAULT 0,
                carbs REAL DEFAULT 0,
                composition TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )''')

        c.execute('''
            CREATE TABLE IF NOT EXISTS cart (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                dish_id INTEGER NOT NULL,
                quantity INTEGER DEFAULT 1,
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
                FOREIGN KEY (dish_id) REFERENCES menu (id) ON DELETE CASCADE
            )''')

        c.execute('''
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                address_id INTEGER NOT NULL DEFAULT 1,
                table_number INTEGER DEFAULT 1,
                status TEXT DEFAULT 'sent_to_kitchen',
                payment_method TEXT DEFAULT 'Наличные',
                total_amount REAL NOT NULL,
                order_number TEXT UNIQUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                customer_name TEXT,
                FOREIGN KEY (user_id) REFERENCES users (id),
                FOREIGN KEY (address_id) REFERENCES addresses (id)
            )''')

        c.execute('''
            CREATE TABLE IF NOT EXISTS order_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id INTEGER NOT NULL,
                dish_id INTEGER NOT NULL,
                quantity INTEGER NOT NULL,
                price REAL NOT NULL,
                FOREIGN KEY (order_id) REFERENCES orders (id) ON DELETE CASCADE,
                FOREIGN KEY (dish_id) REFERENCES menu (id)
            )''')

        self.get_conn().commit()

    def _ensure_test_data(self):
        """Добавляет тестовых пользователей и адреса, если таблицы пусты."""
        c = self.cursor

        c.execute("SELECT COUNT(*) FROM users")
        if c.fetchone()[0] == 0:
            self._add_test_users()

        c.execute("SELECT COUNT(*) FROM addresses")
        if c.fetchone()[0] == 0:
            self._add_test_addresses()

    def _add_test_users(self):
        """Вставляет набор тестовых пользователей с разными ролями."""
        users = [
            ('Администратор', '1', '+79123456789', '1', 'admin'),
            ('Повар Иван', '3', '+79123456788', '3', 'chef'),
            ('Официант Мария', '4', '+79123456787', '4', 'waiter'),
            ('Клиент Петр', '2', '+79123456786', '2', 'customer'),
            ('Тест User', 'test@mail.ru', '+79123456785', 'test', 'customer')
        ]
        self.cursor.executemany(
            "INSERT INTO users (name, email, phone, password, role) VALUES (?, ?, ?, ?, ?)",
            users
        )
        self.get_conn().commit()

    def _add_test_addresses(self):
        """Вставляет тестовые адреса заведений."""
        addresses = [
            ('ул. Главная, 123',),
            ('пр. Северный, 456',),
            ('ул. Южная, 789',)
        ]
        self.cursor.executemany("INSERT INTO addresses (address) VALUES (?)", addresses)
        self.get_conn().commit()

    # === Пользователи ===

    def create_user(self, name, email, phone, password):
        """Создаёт нового пользователя. Возвращает True при успехе, False — если email занят."""
        try:
            self.cursor.execute(
                "INSERT INTO users (name, email, phone, password) VALUES (?, ?, ?, ?)",
                (name, email, phone, password)
            )
            self.get_conn().commit()
            return True
        except sqlite3.IntegrityError:
            return False

    def get_user_by_email(self, email):
        """Возвращает данные пользователя по email или None, если не найден."""
        c = self.cursor
        c.execute("SELECT * FROM users WHERE email = ?", (email,))
        return c.fetchone()

    def get_all_users(self):
        """Возвращает всех пользователей, отсортированных по дате регистрации (новые — первыми)."""
        c = self.cursor
        c.execute("SELECT * FROM users ORDER BY created_at DESC")
        return c.fetchall()

    def update_user_role(self, user_id, new_role):
        """Обновляет роль пользователя. Возвращает True, если запись изменена."""
        c = self.cursor
        c.execute("UPDATE users SET role = ? WHERE id = ?", (new_role, user_id))
        self.get_conn().commit()
        return c.rowcount > 0

    # === Меню ===

    def get_menu_items(self):
        """Возвращает список доступных блюд (is_available=1), отсортированных по названию."""
        c = self.cursor
        c.execute("""
            SELECT id, name, description, price, image,
                   grams, calories, proteins, fats, carbs, composition
            FROM menu WHERE is_available = 1 ORDER BY name
        """)
        return c.fetchall()

    def add_menu_item(self, name, description, price, image_data=None,
                      grams=0, calories=0, proteins=0, fats=0, carbs=0, composition=""):
        """Добавляет новое блюдо в меню. Возвращает True при успехе."""
        c = self.cursor
        c.execute("""
            INSERT INTO menu (name, description, price, image, grams,
                              calories, proteins, fats, carbs, composition)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (name, description, price, image_data, grams,
              calories, proteins, fats, carbs, composition))
        self.get_conn().commit()
        return c.rowcount > 0

    def delete_menu_item(self, dish_id):
        """Удаляет блюдо из меню по ID. Возвращает True, если запись удалена."""
        c = self.cursor
        c.execute("DELETE FROM menu WHERE id = ?", (dish_id,))
        self.get_conn().commit()
        return c.rowcount > 0

    # === Адреса ===

    def get_addresses(self):
        """Возвращает все адреса, отсортированные по названию."""
        c = self.cursor
        c.execute("SELECT id, address FROM addresses ORDER BY address")
        return c.fetchall()

    # === Корзина ===

    def add_to_cart(self, user_id, dish_id, quantity=1):
        """Добавляет блюдо в корзину пользователя (увеличивает количество, если уже есть)."""
        c = self.cursor
        c.execute("SELECT id, quantity FROM cart WHERE user_id = ? AND dish_id = ?", (user_id, dish_id))
        existing = c.fetchone()
        if existing:
            c.execute("UPDATE cart SET quantity = ? WHERE id = ?", (existing[1] + quantity, existing[0]))
        else:
            c.execute("INSERT INTO cart (user_id, dish_id, quantity) VALUES (?, ?, ?)", (user_id, dish_id, quantity))
        self.get_conn().commit()
        return True

    def get_cart(self, user_id):
        """Возвращает содержимое корзины пользователя: ID записи, ID блюда, название, описание, количество, сумму."""
        c = self.cursor
        c.execute('''
            SELECT c.id, c.dish_id, m.name, m.description, c.quantity, (m.price * c.quantity) as total
            FROM cart c
            JOIN menu m ON c.dish_id = m.id
            WHERE c.user_id = ?
        ''', (user_id,))
        return c.fetchall()

    def remove_from_cart(self, cart_id):
        """Удаляет одну запись из корзины по её ID."""
        c = self.cursor
        c.execute("DELETE FROM cart WHERE id = ?", (cart_id,))
        self.get_conn().commit()
        return c.rowcount > 0

    def clear_cart(self, user_id):
        """Очищает всю корзину пользователя."""
        c = self.cursor
        c.execute("DELETE FROM cart WHERE user_id = ?", (user_id,))
        self.get_conn().commit()
        return c.rowcount > 0

    def create_order(self, user_id, address_id, table_number, payment_method, total_amount):
        """Создаёт заказ из корзины, перемещает позиции в order_items и очищает корзину.

        Возвращает кортеж (order_id, order_number) или (None, None) при ошибке.
        """
        c = self.cursor
        c.execute("SELECT name FROM users WHERE id = ?", (user_id,))
        user = c.fetchone()
        customer_name = user[0] if user else "Гость"
        order_number = self._generate_order_number()
        c.execute('''
            INSERT INTO orders (user_id, address_id, table_number,
                                payment_method, total_amount, order_number, customer_name)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (user_id, address_id, table_number, payment_method, total_amount, order_number, customer_name))
        order_id = c.lastrowid
        cart_items = self.get_cart(user_id)
        for item in cart_items:
            dish_id = item[1]
            quantity = item[4]
            c.execute("SELECT price FROM menu WHERE id = ? AND is_available = 1", (dish_id,))
            menu_item = c.fetchone()
            if not menu_item:
                self.get_conn().rollback()
                return None, None
            dish_price = menu_item[0]
            c.execute("INSERT INTO order_items (order_id, dish_id, quantity, price) VALUES (?, ?, ?, ?)",
                      (order_id, dish_id, quantity, dish_price))
        self.clear_cart(user_id)
        self.get_conn().commit()
        return order_id, order_number

    def _generate_order_number(self):
        """Генерирует уникальный номер заказа в формате YYYYMMDDHHMMSSXX (XX — счётчик за секунду)."""
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        c = self.cursor
        c.execute("SELECT COUNT(*) FROM orders WHERE order_number LIKE ?", (f"{timestamp}%",))
        count = c.fetchone()[0]
        return f"{timestamp}{count + 1:02d}"

    def get_user_orders(self, user_id):
        """Возвращает все заказы пользователя с присоединённым адресом, отсортированные по дате (новые — первыми)."""
        c = self.cursor
        c.execute('''
            SELECT o.id, o.user_id, o.address_id, o.table_number, o.status,
                   o.payment_method, o.total_amount, o.order_number,
                   o.created_at, o.customer_name, a.address
            FROM orders o
            LEFT JOIN addresses a ON o.address_id = a.id
            WHERE o.user_id = ?
            ORDER BY o.created_at DESC
        ''', (user_id,))
        return c.fetchall()

    def get_order_items(self, order_id):
        """Возвращает состав заказа: название блюда, количество, цену за шт, итоговую сумму по позиции."""
        c = self.cursor
        c.execute('''
            SELECT m.name, oi.quantity, oi.price, (oi.quantity * oi.price) as total
            FROM order_items oi
            JOIN menu m ON oi.dish_id = m.id
            WHERE oi.order_id = ?
        ''', (order_id,))
        return c.fetchall()

    def get_orders_by_status(self, status, address_id=None):
        """Возвращает заказы с указанным статусом.

        Если указан address_id — фильтрует по нему.
        Результат включает данные заказа, адрес и имя пользователя (для повара/официанта).
        """
        c = self.cursor
        if address_id:
            c.execute('''
                SELECT o.id, o.user_id, o.address_id, o.table_number, o.status,
                       o.payment_method, o.total_amount, o.order_number,
                       o.created_at, o.customer_name, a.address, u.name
                FROM orders o
                LEFT JOIN addresses a ON o.address_id = a.id
                LEFT JOIN users u ON o.user_id = u.id
                WHERE o.status = ? AND o.address_id = ?
                ORDER BY o.created_at ASC
            ''', (status, address_id))
        else:
            c.execute('''
                SELECT o.id, o.user_id, o.address_id, o.table_number, o.status,
                       o.payment_method, o.total_amount, o.order_number,
                       o.created_at, o.customer_name, a.address, u.name
                FROM orders o
                LEFT JOIN addresses a ON o.address_id = a.id
                LEFT JOIN users u ON o.user_id = u.id
                WHERE o.status = ?
                ORDER BY o.created_at ASC
            ''', (status,))
        return c.fetchall()

    def update_order_status(self, order_id, new_status):
        """Обновляет статус заказа. Возвращает True, если запись изменена."""
        c = self.cursor
        c.execute("UPDATE orders SET status = ? WHERE id = ?", (new_status, order_id))
        self.get_conn().commit()
        return c.rowcount > 0

    def close(self):
        """Закрывает соединение с базой данных."""
        if hasattr(self, '_conn') and self._conn:
            self._conn.close()
            self._conn = None

    def __del__(self):
        """Гарантирует закрытие соединения при уничтожении объекта."""
        self.close()