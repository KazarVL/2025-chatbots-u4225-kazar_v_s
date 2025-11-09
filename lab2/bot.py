import os
import json
import logging
from datetime import datetime, timedelta
from dotenv import load_dotenv
import telebot
from telebot import types

# Попробуем импортировать базу данных
try:
    from database import DatabaseManager
    db = DatabaseManager()
    DB_AVAILABLE = True
    print("✅ База данных подключена успешно")
except ImportError as e:
    print(f"❌ Ошибка импорта database: {e}")
    DB_AVAILABLE = False
except Exception as e:
    print(f"❌ Ошибка инициализации БД: {e}")
    DB_AVAILABLE = False

# Загрузка переменных окружения
load_dotenv()

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Константы
BOT_TOKEN = os.getenv('BOT_TOKEN') or "ВАШ_ТОКЕН_ЗДЕСЬ"
DATA_FOLDER = 'data'

# Файлы для хранения данных
CONTACTS_FILE = os.path.join(DATA_FOLDER, 'contacts.json')
EVENTS_FILE = os.path.join(DATA_FOLDER, 'events.json')
COMPANY_INFO_FILE = os.path.join(DATA_FOLDER, 'company_info.json')
PRODUCTS_FILE = os.path.join(DATA_FOLDER, 'products.json')

# Создаем папку для данных, если её нет
os.makedirs(DATA_FOLDER, exist_ok=True)

# Создаем объект бота
bot = telebot.TeleBot(BOT_TOKEN)

def load_json(file_path):
    """Загрузка данных из JSON файла"""
    try:
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    except Exception as e:
        logger.error(f"Error loading {file_path}: {e}")
        return {}

# ========== ОСНОВНЫЕ КОМАНДЫ ==========

@bot.message_handler(commands=['start'])
def send_welcome(message):
    """Обработчик команды /start"""
    if DB_AVAILABLE:
        db.add_user(
            message.from_user.id,
            message.from_user.username,
            message.from_user.first_name,
            message.from_user.last_name
        )
        db.log_request(message.from_user.id, "/start", "Приветственное сообщение", "start")
    
    welcome_text = f"""
Привет, {message.from_user.first_name}! 👋

Я бот-помощник для команды GameBored.

📋 **Основные команды:**
/start - Начало работы
/help - Помощь и список команд
/contacts - Контакты коллег
/events - Акции и события
/products - Наши товары
/digest - Ежедневный дайджест
/about - О компании

🗃️ **Команды базы данных:**
/stats - Статистика бота
/my_requests - История ваших запросов  
/add_order - Добавить заказ
/orders - Просмотреть заказы
/tasks - Задачи команды
/debug - Отладочная информация

Просто напишите вопрос, и я постараюсь помочь!
    """
    bot.reply_to(message, welcome_text)

@bot.message_handler(commands=['help'])
def send_help(message):
    """Обработчик команды /help"""
    if DB_AVAILABLE:
        db.log_request(message.from_user.id, "/help", "Справка по командам", "help")
    
    help_text = """
📋 **Доступные команды:**

🏢 **Основные команды:**
/start - Начало работы
/help - Эта справка
/contacts - Контакты команды
/events - Акции и мероприятия  
/products - Товары и цены
/digest - Ежедневный дайджест
/about - О компании

🗃️ **Команды базы данных:**
/stats - Статистика бота и заказов
/my_requests - История ваших запросов
/add_order - Добавить новый заказ
/orders - Список всех заказов
/order - Детали заказа (например: /order 1)
/find_order - Поиск заказов по клиенту  🆕
/recent_orders - Свежие заказы (7 дней)  🆕
/tasks - Задачи команды
/add_test_task - Добавить тестовую задачу

🔧 **Технические команды:**
/debug - Отладочная информация
    """
    bot.reply_to(message, help_text)

@bot.message_handler(commands=['contacts'])
def send_contacts(message):
    """Показать контакты коллег"""
    if DB_AVAILABLE:
        db.log_request(message.from_user.id, "/contacts", "Показаны контакты", "contacts")
    
    contacts_data = load_json(CONTACTS_FILE)
    
    if not contacts_data:
        bot.reply_to(message, "📞 Контакты пока не добавлены.")
        return
    
    response = "📞 **Контакты команды GameBored:**\n\n"
    for name, info in contacts_data.items():
        response += f"👤 **{name}**\n"
        response += f"   💼 Должность: {info.get('position', 'Не указана')}\n"
        response += f"   📞 Телефон: {info.get('phone', 'Не указан')}\n"
        response += f"   📧 Email: {info.get('email', 'Не указан')}\n"
        response += f"   💬 {info.get('comment', 'Нет комментария')}\n\n"
    
    bot.reply_to(message, response)

@bot.message_handler(commands=['events'])
def send_events(message):
    """Показать события и акции"""
    if DB_AVAILABLE:
        db.log_request(message.from_user.id, "/events", "Показаны события", "events")
    
    try:
        events_data = load_json(EVENTS_FILE)
        
        if not events_data:
            bot.reply_to(message, "📅 Акций и событий на ближайшее время нет.")
            return
        
        today = datetime.now().date()
        response = "📅 **Текущие акции и события:**\n\n"
        
        for event_name, event_info in events_data.items():
            try:
                event_date = datetime.strptime(event_info['date'], '%Y-%m-%d').date()
                days_left = (event_date - today).days
                
                status_icon = "🟢" if days_left >= 0 else "🔴"
                days_text = f"через {days_left} дн." if days_left > 0 else "сегодня" if days_left == 0 else f"прошло {-days_left} дн. назад"
                
                response += f"{status_icon} **{event_name}**\n"
                response += f"   📅 {event_info['date']} ({days_text})\n"
                response += f"   🏷 {event_info['type']}\n"
                response += f"   📝 {event_info['description']}\n"
                response += f"   📊 {event_info.get('status', 'активно')}\n\n"
                
            except Exception as e:
                logger.error(f"Error processing event {event_name}: {e}")
                continue
        
        bot.reply_to(message, response)
        
    except Exception as e:
        logger.error(f"Error in events command: {e}")
        bot.reply_to(message, "❌ Ошибка при загрузке событий.")
@bot.message_handler(commands=['find_order'])
def find_order(message):
    """Поиск заказов по имени клиента"""
    if not DB_AVAILABLE:
        bot.reply_to(message, "❌ База данных временно недоступна")
        return

    args = message.text.split()[1:]
    if not args:
        bot.reply_to(message,
            "🔍 **Поиск заказов по клиенту**\n\n"
            "📝 **Использование:**\n"
            "`/find_order [имя_клиента]`\n\n"
            "💡 **Примеры:**\n"
            "`/find_order Иван`\n"
            "`/find_order Петров`\n"
            "`/find_order Мария`"
        )
        return

    try:
        customer_name = ' '.join(args)
        orders = db.find_orders_by_customer(customer_name)

        if not orders:
            bot.reply_to(message, f"🔍 Заказы для клиента '{customer_name}' не найдены")
            return

        response = f"🔍 **Найдено заказов для '{customer_name}': {len(orders)}**\n\n"
        
        for order in orders[:10]:  # Ограничиваем вывод
            order_id, cust_name, product, quantity, price, status, created_at, notes = order
            
            status_icons = {'новый': '🟡', 'в работе': '🟠', 'выполнен': '🟢', 'отменен': '🔴'}
            
            response += f"{status_icons.get(status, '⚪')} **Заказ #{order_id}**\n"
            response += f"👤 **{cust_name}**\n"
            response += f"🛍️ {product} (x{quantity})\n"
            response += f"💰 {price} руб.\n"
            response += f"📅 {created_at[:16]}\n"
            if notes:
                response += f"📝 {notes}\n"
            response += "\n"

        if len(orders) > 10:
            response += f"💡 Показано 10 из {len(orders)} заказов\n"

        bot.reply_to(message, response)
        db.log_request(message.from_user.id, f"/find_order {customer_name}", 
                       f"Найдено {len(orders)} заказов", "find_order")

    except Exception as e:
        logger.error(f"Error in find_order command: {e}")
        bot.reply_to(message, "❌ Произошла ошибка при поиске заказов")
@bot.message_handler(commands=['recent_orders'])
def recent_orders(message):
    """Показать свежие заказы (за последние 7 дней)"""
    if not DB_AVAILABLE:
        bot.reply_to(message, "❌ База данных временно недоступна")
        return

    try:
        # Заказы за последние 7 дней
        from datetime import datetime, timedelta
        week_ago = datetime.now() - timedelta(days=7)

        orders = db.get_orders_since(week_ago)

        if not orders:
            bot.reply_to(message,
                "📅 **Свежие заказы**\n\n"
                "За последние 7 дней заказов нет.\n\n"
                "💡 Используйте `/add_order` чтобы добавить новый заказ!"
            )
            return

        response = f"📅 **Свежие заказы (последние 7 дней): {len(orders)}**\n\n"
        
        for order in orders[:15]:  # Ограничиваем вывод
            order_id, cust_name, product, quantity, price, status, created_at, notes = order
            
            status_icons = {'новый': '🟡', 'в работе': '🟠', 'выполнен': '🟢', 'отменен': '🔴'}
            
            response += f"{status_icons.get(status, '⚪')} **Заказ #{order_id}**\n"
            response += f"👤 **{cust_name}**\n"
            response += f"🛍️ {product} (x{quantity})\n"
            response += f"💰 {price} руб.\n"
            response += f"📅 {created_at[:16]}\n"
            if notes:
                response += f"📝 {notes}\n"
            response += "\n"

        if len(orders) > 15:
            response += f"💡 Показано 15 из {len(orders)} заказов\n"

        bot.reply_to(message, response)
        db.log_request(message.from_user.id, "/recent_orders", 
                       f"Показано {len(orders)} заказов", "recent_orders")

    except Exception as e:
        logger.error(f"Error in recent_orders command: {e}")
        bot.reply_to(message, "❌ Произошла ошибка при получении заказов")

@bot.message_handler(commands=['products'])
def send_products(message):
    """Показать товары и цены"""
    if DB_AVAILABLE:
        db.log_request(message.from_user.id, "/products", "Показаны товары", "products")
    
    try:
        products_data = load_json(PRODUCTS_FILE)
        
        if not products_data or 'products' not in products_data:
            bot.reply_to(message, "🎲 Информация о товарах временно недоступна.")
            return
        
        response = "🎲 **Наши товары и цены:**\n\n"
        
        for product_key, product in products_data['products'].items():
            response += f"🎯 **{product['name']}**\n"
            response += f"   💰 Цена: {product['price']} руб.\n"
            if product.get('original_price'):
                response += f"   🔥 Было: {product['original_price']} руб. (скидка {product.get('discount', '')})\n"
            response += f"   📝 {product['description']}\n"
            response += f"   ⏱ Срок: {product['delivery_time']}\n\n"
        
        # Акции
        if products_data.get('current_promotions'):
            response += "🎁 **Акции:**\n"
            for promotion in products_data['current_promotions']:
                response += f"   • {promotion}\n"
        
        bot.reply_to(message, response)
        
    except Exception as e:
        logger.error(f"Error in products command: {e}")
        bot.reply_to(message, "❌ Ошибка при загрузке товаров.")

@bot.message_handler(commands=['digest'])
def send_digest(message):
    """Ежедневный дайджест"""
    if DB_AVAILABLE:
        db.log_request(message.from_user.id, "/digest", "Показан дайджест", "digest")
    
    contacts_data = load_json(CONTACTS_FILE)
    events_data = load_json(EVENTS_FILE)
    company_info = load_json(COMPANY_INFO_FILE)
    products_data = load_json(PRODUCTS_FILE)
    
    today = datetime.now().date()
    
    digest_text = "📊 **Ежедневный дайджест GameBored**\n\n"
    
    # Компания
    if company_info:
        digest_text += f"🏢 **{company_info.get('name', 'GameBored')}**\n"
        digest_text += f"   {company_info.get('description', '')}\n\n"
    
    # Активные акции
    active_events = []
    for event_name, event_info in events_data.items():
        try:
            event_date = datetime.strptime(event_info['date'], '%Y-%m-%d').date()
            days_diff = (event_date - today).days
            if days_diff >= 0:
                active_events.append((event_name, event_info, days_diff))
        except:
            continue
    
    if active_events:
        digest_text += "📅 **Активные акции:**\n"
        for event_name, event_info, days_diff in active_events[:3]:
            digest_text += f"   • {event_name} - {event_info['description']}\n"
        digest_text += "\n"
    
    # Товары
    if products_data and 'products' in products_data:
        digest_text += f"🎲 **Товаров в ассортименте:** {len(products_data['products'])}\n"
    
    digest_text += "\nХорошего дня! 🚀"
    
    bot.reply_to(message, digest_text)

@bot.message_handler(commands=['about'])
def send_about(message):
    """Информация о компании"""
    if DB_AVAILABLE:
        db.log_request(message.from_user.id, "/about", "Информация о компании", "about")
    
    company_info = load_json(COMPANY_INFO_FILE)
    
    if not company_info:
        default_info = """
🏢 **GameBored**

Творческая мастерская по кастомизации настольных игр.

🎯 **Что мы делаем:**
• Персонализированные версии популярных игр
• Игры с вашими фотографиями
• Уникальные подарки и развлечения

💼 **Наши ценности:**
- Качество
- Креативность
- Индивидуальный подход

📞 **Контакты:** gamebored@yandex.ru
        """
        bot.reply_to(message, default_info)
    else:
        response = f"""
🏢 **{company_info.get('name', 'GameBored')}**

{company_info.get('description', '')}

📞 **Контакты:**
Телефон: {company_info.get('phone', 'Не указан')}
Email: {company_info.get('email', 'gamebored@yandex.ru')}
Адрес: {company_info.get('address', 'СПб и по России')}

💼 **Сфера:** {company_info.get('industry', 'Кастомизация настольных игр')}

🎯 **Миссия:** {company_info.get('mission', '')}
        """
        bot.reply_to(message, response)

# ========== КОМАНДЫ БАЗЫ ДАННЫХ ==========

@bot.message_handler(commands=['stats'])
def send_stats(message):
    """Статистика бота и заказов"""
    if not DB_AVAILABLE:
        bot.reply_to(message, "❌ База данных временно недоступна")
        return
        
    try:
        db.add_user(
            message.from_user.id,
            message.from_user.username,
            message.from_user.first_name,
            message.from_user.last_name
        )
        
        bot_stats = db.get_bot_stats()
        orders_stats = db.get_order_stats()
        
        response = "📊 **Статистика GameBored Bot**\n\n"
        
        response += "👥 **Пользователи бота:**\n"
        response += f"   • Всего пользователей: {bot_stats.get('total_users', 0)}\n"
        response += f"   • Всего запросов: {bot_stats.get('total_requests', 0)}\n"
        response += f"   • Последняя активность: {bot_stats.get('last_activity', 'неизвестно')}\n\n"
        
        response += "🛒 **Статистика заказов:**\n"
        response += f"   • Всего заказов: {orders_stats.get('total_orders', 0)}\n"
        response += f"   • Уникальных клиентов: {orders_stats.get('unique_customers', 0)}\n"
        response += f"   • Общая выручка: {orders_stats.get('total_revenue', 0):.2f} руб.\n\n"
        
        status_stats = orders_stats.get('status_stats', [])
        if status_stats:
            response += "📈 **Заказы по статусам:**\n"
            for status, count in status_stats:
                response += f"   • {status}: {count}\n"
        else:
            response += "📈 Заказов пока нет\n"
        
        bot.reply_to(message, response)
        db.log_request(message.from_user.id, "/stats", "Показана статистика", "stats")
        
    except Exception as e:
        logger.error(f"Error in stats command: {e}")
        bot.reply_to(message, "❌ Ошибка при получении статистики")

@bot.message_handler(commands=['my_requests'])
def send_my_requests(message):
    """История запросов пользователя"""
    if not DB_AVAILABLE:
        bot.reply_to(message, "❌ База данных временно недоступна")
        return
        
    try:
        db.add_user(
            message.from_user.id,
            message.from_user.username,
            message.from_user.first_name,
            message.from_user.last_name
        )
        
        user_requests = db.get_user_requests(message.from_user.id, limit=5)
        
        if not user_requests:
            bot.reply_to(message, "📝 У вас еще нет истории запросов.")
            return
        
        response = "📝 **Ваши последние запросы:**\n\n"
        for i, (request_text, command_used, created_at) in enumerate(user_requests, 1):
            short_request = request_text[:50] + "..." if len(request_text) > 50 else request_text
            response += f"{i}. **{short_request}**\n"
            response += f"   Команда: {command_used or 'текст'}\n"
            response += f"   Время: {created_at[:16]}\n\n"
        
        bot.reply_to(message, response)
        db.log_request(message.from_user.id, "/my_requests", "Показана история", "my_requests")
        
    except Exception as e:
        logger.error(f"Error in my_requests command: {e}")
        bot.reply_to(message, "❌ Ошибка при получении истории запросов")

@bot.message_handler(commands=['add_order'])
def add_order_command(message):
    """Добавление нового заказа"""
    if not DB_AVAILABLE:
        bot.reply_to(message, "❌ База данных временно недоступна")
        return
        
    try:
        db.add_user(
            message.from_user.id,
            message.from_user.username,
            message.from_user.first_name,
            message.from_user.last_name
        )
        
        args = message.text.split()[1:]
        if len(args) < 3:
            help_text = (
                "❌ **Неверный формат команды!**\n\n"
                "✅ **Правильное использование:**\n"
                "`/add_order [имя_клиента] [товар] [количество]`\n\n"
                "📝 **Пример:**\n"
                "`/add_order Иван Мафия 1`\n"
                "`/add_order \"Иван Петров\" \"Персонализированная Мафия\" 2`\n\n"
                "🎲 **Доступные товары:**\n"
                "• Мафия (1790 руб.)\n• Мемо (1990 руб.)\n• Элиас (2500 руб.)"
            )
            bot.reply_to(message, help_text)
            return
        
        customer_name = args[0].replace('"', '')
        product_name = args[1].replace('"', '')
        
        try:
            quantity = int(args[2])
            if quantity <= 0:
                raise ValueError
        except ValueError:
            bot.reply_to(message, "❌ Количество должно быть положительным числом!")
            return
        
        prices = {
            'мафия': 1790,
            'мемо': 1990, 
            'элиас': 2500
        }
        
        product_lower = product_name.lower()
        price_per_item = prices.get(product_lower, 2000)
        total_price = quantity * price_per_item
        
        order_id = db.add_order(
            message.from_user.id,
            customer_name,
            product_name,
            quantity,
            total_price
        )
        
        if order_id:
            response = f"✅ **Заказ успешно добавлен!**\n\n"
            response += f"📋 **ID заказа:** #{order_id}\n"
            response += f"👤 **Клиент:** {customer_name}\n"
            response += f"🎯 **Товар:** {product_name}\n"
            response += f"📦 **Количество:** {quantity}\n"
            response += f"💰 **Сумма:** {total_price} руб.\n"
            response += f"📊 **Статус:** новый\n\n"
            response += f"💡 Заказ будет обработан в течение 24 часов."
            
            bot.reply_to(message, response)
            db.log_request(message.from_user.id, f"/add_order {customer_name} {product_name} {quantity}", 
                          f"Заказ добавлен ID: {order_id}", "add_order")
        else:
            bot.reply_to(message, "❌ Ошибка при добавлении заказа в базу данных")
            
    except Exception as e:
        logger.error(f"Error in add_order command: {e}")
        bot.reply_to(message, "❌ Произошла ошибка при добавлении заказа")

@bot.message_handler(commands=['orders'])
def send_orders(message):
    """Показать список заказов"""
    if not DB_AVAILABLE:
        bot.reply_to(message, "❌ База данных временно недоступна")
        return
        
    try:
        db.add_user(
            message.from_user.id,
            message.from_user.username,
            message.from_user.first_name,
            message.from_user.last_name
        )
        
        orders = db.get_orders(limit=10)
        
        if not orders:
            bot.reply_to(message, 
                "🛒 **Заказов пока нет**\n\n"
                "💡 Чтобы добавить заказ, используйте команду:\n"
                "`/add_order [клиент] [товар] [количество]`\n\n"
                "📝 Пример: `/add_order Иван Мафия 1`"
            )
            return
        
        response = f"🛒 **Последние заказы ({len(orders)}):**\n\n"
        
        for order in orders:
            order_id, customer_name, product_name, quantity, total_price, status, created_at, notes = order
            
            status_icons = {
                'новый': '🆕',
                'в работе': '🔄',
                'выполнен': '✅',
                'отменен': '❌'
            }
            
            response += f"{status_icons.get(status, '📦')} **Заказ #{order_id}**\n"
            response += f"   👤 {customer_name}\n"
            response += f"   🎯 {product_name} (x{quantity})\n"
            response += f"   💰 {total_price} руб.\n"
            response += f"   📊 {status}\n"
            response += f"   📅 {created_at[:16]}\n\n"
        
        response += "💡 Для подробной информации используйте `/order [номер]`"
        
        bot.reply_to(message, response)
        db.log_request(message.from_user.id, "/orders", f"Показано {len(orders)} заказов", "orders")
        
    except Exception as e:
        logger.error(f"Error in orders command: {e}")
        bot.reply_to(message, "❌ Ошибка при получении списка заказов")

@bot.message_handler(commands=['order'])
def send_order_detail(message):
    """Показать детали конкретного заказа"""
    if not DB_AVAILABLE:
        bot.reply_to(message, "❌ База данных временно недоступна")
        return
        
    try:
        db.add_user(
            message.from_user.id,
            message.from_user.username,
            message.from_user.first_name,
            message.from_user.last_name
        )
        
        args = message.text.split()[1:]
        if len(args) < 1:
            bot.reply_to(message, 
                "❌ **Укажите номер заказа!**\n\n"
                "✅ Использование: `/order [номер]`\n"
                "📝 Пример: `/order 1`\n\n"
                "💡 Список заказов: `/orders`"
            )
            return
        
        try:
            order_id = int(args[0])
        except ValueError:
            bot.reply_to(message, "❌ Номер заказа должен быть числом!")
            return
        
        orders = db.get_orders(limit=50)
        target_order = None
        
        for order in orders:
            if order[0] == order_id:
                target_order = order
                break
        
        if not target_order:
            bot.reply_to(message, f"❌ Заказ #{order_id} не найден!")
            return
        
        order_id, customer_name, product_name, quantity, total_price, status, created_at, notes = target_order
        
        status_icons = {
            'новый': '🆕',
            'в работе': '🔄',
            'выполнен': '✅',
            'отменен': '❌'
        }
        
        response = f"{status_icons.get(status, '📦')} **Заказ #{order_id}**\n\n"
        response += f"👤 **Клиент:** {customer_name}\n"
        response += f"🎯 **Товар:** {product_name}\n"
        response += f"📦 **Количество:** {quantity}\n"
        response += f"💰 **Сумма:** {total_price} руб.\n"
        response += f"📊 **Статус:** {status}\n"
        response += f"📅 **Создан:** {created_at[:16]}\n"
        
        if notes:
            response += f"📝 **Примечания:** {notes}\n"
        
        bot.reply_to(message, response)
        db.log_request(message.from_user.id, f"/order {order_id}", f"Показан заказ #{order_id}", "order")
        
    except Exception as e:
        logger.error(f"Error in order command: {e}")
        bot.reply_to(message, "❌ Ошибка при получении информации о заказе")

@bot.message_handler(commands=['tasks'])
def send_tasks(message):
    """Показать задачи команды"""
    if not DB_AVAILABLE:
        bot.reply_to(message, "❌ База данных временно недоступна")
        return
        
    try:
        db.add_user(
            message.from_user.id,
            message.from_user.username,
            message.from_user.first_name,
            message.from_user.last_name
        )
        
        tasks = db.get_tasks()
        
        if not tasks:
            bot.reply_to(message, 
                "✅ **Активных задач нет**\n\n"
                "💡 Хотите добавить тестовую задачу?\n"
                "Используйте команду:\n"
                "`/add_test_task`"
            )
            return
        
        response = "📋 **Задачи команды GameBored:**\n\n"
        for task in tasks:
            task_id, title, description, assigned_to, priority, status, due_date, created_at = task
            
            priority_icons = {
                'высокий': '🔴',
                'средний': '🟡', 
                'низкий': '🟢'
            }
            
            status_icons = {
                'к выполнению': '⏳',
                'в работе': '🔄', 
                'выполнено': '✅'
            }
            
            response += f"{priority_icons.get(priority, '⚪')} **{title}**\n"
            response += f"   {status_icons.get(status, '📝')} Статус: {status}\n"
            response += f"   👤 Ответственный: {assigned_to or 'не назначен'}\n"
            response += f"   🏷 Приоритет: {priority}\n"
            if due_date:
                response += f"   📅 Срок: {due_date}\n"
            if description:
                response += f"   📝 {description}\n"
            response += f"   🆔 ID: #{task_id}\n\n"
        
        bot.reply_to(message, response)
        db.log_request(message.from_user.id, "/tasks", f"Показано {len(tasks)} задач", "tasks")
        
    except Exception as e:
        logger.error(f"Error in tasks command: {e}")
        bot.reply_to(message, "❌ Ошибка при получении задач")

@bot.message_handler(commands=['add_test_task'])
def add_test_task(message):
    """Добавить тестовую задачу (для демонстрации)"""
    if not DB_AVAILABLE:
        bot.reply_to(message, "❌ База данных временно недоступна")
        return
        
    try:
        task_id = db.add_task(
            title="Обновить ассортимент товаров",
            description="Добавить новые темы для кастомизации игр",
            assigned_to="Менеджер по продукту",
            priority="средний",
            due_date="2024-12-20"
        )
        
        if task_id:
            response = (
                "✅ **Тестовая задача добавлена!**\n\n"
                f"📋 ID задачи: #{task_id}\n"
                "💡 Теперь используйте команду `/tasks` чтобы увидеть все задачи."
            )
            bot.reply_to(message, response)
            db.log_request(message.from_user.id, "/add_test_task", f"Добавлена задача ID: {task_id}", "add_test_task")
        else:
            bot.reply_to(message, "❌ Ошибка при добавлении тестовой задачи")
            
    except Exception as e:
        logger.error(f"Error in add_test_task command: {e}")
        bot.reply_to(message, "❌ Ошибка при добавлении тестовой задачи")

@bot.message_handler(commands=['debug'])
def send_debug(message):
    """Отладочная информация"""
    try:
        events_exists = os.path.exists(EVENTS_FILE)
        contacts_exists = os.path.exists(CONTACTS_FILE)
        company_exists = os.path.exists(COMPANY_INFO_FILE)
        products_exists = os.path.exists(PRODUCTS_FILE)
        db_exists = os.path.exists('gameboard_bot.db')
        
        events_data = load_json(EVENTS_FILE)
        contacts_data = load_json(CONTACTS_FILE)
        company_data = load_json(COMPANY_INFO_FILE)
        products_data = load_json(PRODUCTS_FILE)
        
        response = f"""🔧 **Отладочная информация:**

📁 **Файлы данных:**
• events.json: {'✅' if events_exists else '❌'} ({len(events_data) if events_data else 0} событий)
• contacts.json: {'✅' if contacts_exists else '❌'} ({len(contacts_data) if contacts_data else 0} контактов)
• company_info.json: {'✅' if company_exists else '❌'}
• products.json: {'✅' if products_exists else '❌'}
• gameboard_bot.db: {'✅' if db_exists else '❌'}

🤖 **База данных:** {'✅ Доступна' if DB_AVAILABLE else '❌ Недоступна'}

🤖 Бот активен! 🚀
        """
        
        bot.reply_to(message, response)
        if DB_AVAILABLE:
            db.log_request(message.from_user.id, "/debug", "Показана отладочная информация", "debug")
        
    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка отладки: {e}")

@bot.message_handler(func=lambda message: True)
def handle_all_messages(message):
    """Обработка всех текстовых сообщений"""
    try:
        if DB_AVAILABLE:
            db.add_user(
                message.from_user.id,
                message.from_user.username,
                message.from_user.first_name,
                message.from_user.last_name
            )
        
        user_message = message.text.lower()
        response_text = ""
        command_used = "text_message"
        
        if any(word in user_message for word in ['компани', 'о компани', 'организац']):
            send_about(message)
            response_text = "Информация о компании"
        elif any(word in user_message for word in ['контакт', 'телефон', 'email', 'коллег']):
            send_contacts(message)
            response_text = "Контакты команды"
        elif any(word in user_message for word in ['событи', 'акци', 'встреч', 'мероприят']):
            send_events(message)
            response_text = "События и акции"
        elif any(word in user_message for word in ['товар', 'игр', 'цен', 'стоит', 'купить']):
            send_products(message)
            response_text = "Товары и цены"
        elif any(word in user_message for word in ['дайджест', 'итог', 'сводк']):
            send_digest(message)
            response_text = "Ежедневный дайджест"
        elif any(word in user_message for word in ['статистик', 'статус', 'отчет']):
            send_stats(message)
            response_text = "Статистика бота"
        elif any(word in user_message for word in ['заказ', 'заказы', 'покуп']):
            send_orders(message)
            response_text = "Список заказов"
        elif any(word in user_message for word in ['задач', 'todo', 'дело']):
            send_tasks(message)
            response_text = "Задачи команды"
        elif any(word in user_message for word in ['истори', 'мои запрос']):
            send_my_requests(message)
            response_text = "История запросов"
        elif any(word in user_message for word in ['привет', 'здравств', 'hello', 'hi']):
            bot.reply_to(message, "Привет! Чем могу помочь? 😊")
            response_text = "Приветствие"
        else:
            bot.reply_to(message, "Я пока не знаю ответ на этот вопрос. Попробуйте использовать команды из /help")
            response_text = "Неизвестный запрос"
        
        if DB_AVAILABLE:
            db.log_request(
                message.from_user.id,
                message.text,
                response_text,
                command_used
            )
        
    except Exception as e:
        logger.error(f"Error handling message: {e}")
        bot.reply_to(message, "❌ Произошла ошибка при обработке запроса")

if __name__ == '__main__':
    logger.info("Bot is starting...")
    print("=" * 50)
    print("🤖 GameBoard Bot запущен!")
    print(f"📊 База данных: {'✅ Доступна' if DB_AVAILABLE else '❌ Недоступна'}")
    print("✅ Доступные команды БД:")
    print("   /stats - статистика")
    print("   /my_requests - история запросов") 
    print("   /add_order - добавить заказ")
    print("   /orders - список заказов")
    print("   /order - детали заказа")
    print("   /tasks - задачи команды")
    print("   /add_test_task - тестовая задача")
    print("=" * 50)
    bot.infinity_polling()
