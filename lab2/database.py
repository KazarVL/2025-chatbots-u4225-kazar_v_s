import sqlite3
import logging
from datetime import datetime
import os

logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self, db_path='gameboard_bot.db'):
        self.db_path = db_path
        logger.info(f"🔄 Инициализация БД по пути: {os.path.abspath(self.db_path)}")
        self.init_db()

    def get_connection(self):
        """Создание соединения с базой данных"""
        logger.debug(f"📂 Подключение к БД: {self.db_path}")
        return sqlite3.connect(self.db_path)

    def init_db(self):
        """Инициализация базы данных и создание таблиц"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()

                # Таблица пользователей
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS users (
                        user_id INTEGER PRIMARY KEY,
                        username TEXT,
                        first_name TEXT,
                        last_name TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')

                # Таблица истории запросов
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS user_requests (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER,
                        request_text TEXT,
                        response_text TEXT,
                        command_used TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES users (user_id)
                    )
                ''')

                # Таблица заказов
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS orders (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER,
                        customer_name TEXT NOT NULL,
                        product_name TEXT NOT NULL,
                        quantity INTEGER DEFAULT 1,
                        total_price DECIMAL(10, 2),
                        status TEXT DEFAULT 'новый',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        notes TEXT,
                        FOREIGN KEY (user_id) REFERENCES users (user_id)
                    )
                ''')

                # Таблица задач команды
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS tasks (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        title TEXT NOT NULL,
                        description TEXT,
                        assigned_to TEXT,
                        priority TEXT DEFAULT 'средний',
                        status TEXT DEFAULT 'к выполнению',
                        due_date DATE,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')

                conn.commit()
                logger.info("✅ База данных успешно инициализирована")

        except Exception as e:
            logger.error(f"❌ Ошибка при инициализации БД: {e}")
            raise

    def add_user(self, user_id, username, first_name, last_name):
        """Добавление/обновление пользователя"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO users 
                    (user_id, username, first_name, last_name, last_activity)
                    VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
                ''', (user_id, username, first_name, last_name))
                conn.commit()
                logger.info(f"Пользователь {user_id} добавлен/обновлен")
        except Exception as e:
            logger.error(f"Ошибка при добавлении пользователя: {e}")

    def log_request(self, user_id, request_text, response_text, command_used):
        """Логирование запроса пользователя"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO user_requests 
                    (user_id, request_text, response_text, command_used)
                    VALUES (?, ?, ?, ?)
                ''', (user_id, request_text, response_text, command_used))
                conn.commit()
        except Exception as e:
            logger.error(f"Ошибка при логировании запроса: {e}")

    def add_order(self, user_id, customer_name, product_name, quantity, total_price, notes=""):
        """Добавление нового заказа"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO orders
                    (user_id, customer_name, product_name, quantity, total_price, notes)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (user_id, customer_name, product_name, quantity, total_price, notes))
                conn.commit()
                logger.info(f"Добавлен заказ для {customer_name}")
                return cursor.lastrowid
        except Exception as e:
            logger.error(f"Ошибка при добавлении заказа: {e}")
            return None

    def get_orders(self, user_id=None, status=None, limit=10):
        """Получение списка заказов"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                query = """
                    SELECT id, customer_name, product_name, quantity, total_price, status, created_at, notes
                    FROM orders
                """
                params = []
                conditions = []
                if user_id:
                    conditions.append("user_id = ?")
                    params.append(user_id)
                if status:
                    conditions.append("status = ?")
                    params.append(status)
                if conditions:
                    query += " WHERE " + " AND ".join(conditions)
                query += " ORDER BY created_at DESC LIMIT ?"
                params.append(limit)
                cursor.execute(query, params)
                return cursor.fetchall()
        except Exception as e:
            logger.error(f"Ошибка при получении заказов: {e}")
            return []

    def get_order_stats(self):
        """Получение статистики по заказам"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT COUNT(*) FROM orders')
                total_orders = cursor.fetchone()[0]
                cursor.execute('SELECT COUNT(DISTINCT customer_name) FROM orders')
                unique_customers = cursor.fetchone()[0]
                cursor.execute('SELECT SUM(total_price) FROM orders')
                total_revenue = cursor.fetchone()[0] or 0
                cursor.execute('SELECT status, COUNT(*) FROM orders GROUP BY status')
                status_stats = cursor.fetchall()
                return {
                    'total_orders': total_orders,
                    'unique_customers': unique_customers,
                    'total_revenue': total_revenue,
                    'status_stats': status_stats
                }
        except Exception as e:
            logger.error(f"Ошибка при получении статистики заказов: {e}")
            return {}

    def get_bot_stats(self):
        """Получение общей статистики бота"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT COUNT(*) FROM users')
                total_users = cursor.fetchone()[0]
                cursor.execute('SELECT COUNT(*) FROM user_requests')
                total_requests = cursor.fetchone()[0]
                cursor.execute('SELECT MAX(created_at) FROM user_requests')
                last_activity = cursor.fetchone()[0]
                return {
                    'total_users': total_users,
                    'total_requests': total_requests,
                    'last_activity': last_activity
                }
        except Exception as e:
            logger.error(f"Ошибка при получении статистики бота: {e}")
            return {}

    def get_user_requests(self, user_id, limit=10):
        """Получение истории запросов пользователя"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT request_text, command_used, created_at
                    FROM user_requests
                    WHERE user_id = ?
                    ORDER BY created_at DESC
                    LIMIT ?
                ''', (user_id, limit))
                return cursor.fetchall()
        except Exception as e:
            logger.error(f"Ошибка при получении истории запросов: {e}")
            return []

    def add_task(self, title, description, assigned_to, priority, due_date):
        """Добавление задачи для команды"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO tasks
                    (title, description, assigned_to, priority, due_date)
                    VALUES (?, ?, ?, ?, ?)
                ''', (title, description, assigned_to, priority, due_date))
                conn.commit()
                logger.info(f"Добавлена задача: {title}")
                return cursor.lastrowid
        except Exception as e:
            logger.error(f"Ошибка при добавлении задачи: {e}")
            return None

    def get_tasks(self, status=None):
        """Получение списка задач"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                if status:
                    cursor.execute('''
                        SELECT * FROM tasks
                        WHERE status = ?
                        ORDER BY due_date ASC, priority DESC
                    ''', (status,))
                else:
                    cursor.execute('''
                        SELECT * FROM tasks
                        ORDER BY due_date ASC, priority DESC
                    ''')
                return cursor.fetchall()
        except Exception as e:
            logger.error(f"Ошибка при получении задач: {e}")
            return []

    def find_orders_by_customer(self, customer_name):
        """Поиск заказов по имени клиента"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT id, customer_name, product_name, quantity, total_price, status, created_at, notes
                    FROM orders
                    WHERE customer_name LIKE ?
                    ORDER BY created_at DESC
                ''', (f'%{customer_name}%',))
                return cursor.fetchall()
        except Exception as e:
            logger.error(f"Ошибка при поиске заказов по клиенту: {e}")
            return []

    def get_orders_since(self, since_date):
        """Получение заказов начиная с указанной даты"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT id, customer_name, product_name, quantity, total_price, status, created_at, notes
                    FROM orders
                    WHERE created_at >= ?
                    ORDER BY created_at DESC
                ''', (since_date.strftime('%Y-%m-%d %H:%M:%S'),))
                return cursor.fetchall()
        except Exception as e:
            logger.error(f"Ошибка при получении заказов по дате: {e}")
            return []
