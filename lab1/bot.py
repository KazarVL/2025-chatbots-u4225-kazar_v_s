import os
import json
import logging
from datetime import datetime, timedelta
from dotenv import load_dotenv
import telebot
from telebot import types

# Загрузка переменных окружения
load_dotenv()

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Константы
BOT_TOKEN = os.getenv('BOT_TOKEN') or "ВАШ_ТОКЕН_ЗДЕСЬ"  # Вставьте ваш токен
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

def save_json(file_path, data):
    """Сохранение данных в JSON файл"""
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        logger.error(f"Error saving {file_path}: {e}")
        return False

# Обработчики команд
@bot.message_handler(commands=['start'])
def send_welcome(message):
    """Обработчик команды /start"""
    welcome_text = f"""
Привет, {message.from_user.first_name}! 👋

Я бот-помощник для команды GameBored.

Доступные команды:
/start - Начало работы
/help - Помощь и список команд
/contacts - Контакты коллег
/events - Акции и события
/products - Наши товары
/digest - Ежедневный дайджест
/about - О компании
/debug - Отладочная информация

Просто напишите вопрос, и я постараюсь помочь!
    """
    bot.reply_to(message, welcome_text)

@bot.message_handler(commands=['help'])
def send_help(message):
    """Обработчик команды /help"""
    help_text = """
📋 Доступные команды:

/contacts - Контакты команды
/events - Акции и мероприятия  
/products - Товары и цены
/digest - Ежедневный дайджест
/about - О компании
/debug - Отладочная информация
/help - Эта справка

💡 Вы также можете задавать вопросы:
- "Какие игры есть?"
- "Сколько стоит кастомизация?"
- "Как сделать заказ?"
- "Есть ли скидки?"
- "Контакты менеджера"
    """
    bot.reply_to(message, help_text)

@bot.message_handler(commands=['contacts'])
def send_contacts(message):
    """Показать контакты коллег"""
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

@bot.message_handler(commands=['products'])
def send_products(message):
    """Показать товары и цены"""
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

@bot.message_handler(commands=['debug'])
def send_debug(message):
    """Отладочная информация"""
    try:
        events_exists = os.path.exists(EVENTS_FILE)
        contacts_exists = os.path.exists(CONTACTS_FILE)
        company_exists = os.path.exists(COMPANY_INFO_FILE)
        products_exists = os.path.exists(PRODUCTS_FILE)
        
        events_data = load_json(EVENTS_FILE)
        contacts_data = load_json(CONTACTS_FILE)
        company_data = load_json(COMPANY_INFO_FILE)
        products_data = load_json(PRODUCTS_FILE)
        
        response = f"""🔧 **Отладочная информация:**

📁 Файлы:
• events.json: {'✅' if events_exists else '❌'}
• contacts.json: {'✅' if contacts_exists else '❌'} 
• company_info.json: {'✅' if company_exists else '❌'}
• products.json: {'✅' if products_exists else '❌'}

📊 Данные:
• Событий: {len(events_data) if events_data else 0}
• Контактов: {len(contacts_data) if contacts_data else 0}
• Инфо о компании: {'✅' if company_data else '❌'}
• Товаров: {len(products_data.get('products', {})) if products_data else 0}

🤖 Бот активен! 🚀
        """
        
        bot.reply_to(message, response)
        
    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка отладки: {e}")

@bot.message_handler(func=lambda message: True)
def handle_all_messages(message):
    """Обработка всех текстовых сообщений"""
    user_message = message.text.lower()
    
    if any(word in user_message for word in ['компани', 'о компани', 'организац']):
        send_about(message)
    elif any(word in user_message for word in ['контакт', 'телефон', 'email', 'коллег']):
        send_contacts(message)
    elif any(word in user_message for word in ['событи', 'акци', 'встреч', 'мероприят']):
        send_events(message)
    elif any(word in user_message for word in ['товар', 'игр', 'цен', 'стоит', 'купить']):
        send_products(message)
    elif any(word in user_message for word in ['дайджест', 'итог', 'сводк']):
        send_digest(message)
    elif any(word in user_message for word in ['привет', 'здравств', 'hello', 'hi']):
        bot.reply_to(message, "Привет! Чем могу помочь? 😊")
    else:
        bot.reply_to(message, "Я пока не знаю ответ на этот вопрос. Попробуйте использовать команды из /help")

if __name__ == '__main__':
    logger.info("Bot is starting...")
    print("Бот запущен! Нажмите Ctrl+C для остановки.")
    bot.infinity_polling()