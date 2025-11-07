import os
import json
import logging
from datetime import datetime, timedelta
from dotenv import load_dotenv
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Загрузка переменных окружения
load_dotenv()

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Константы
BOT_TOKEN = os.getenv('BOT_TOKEN')
DATA_FOLDER = 'data'

# Файлы для хранения данных
CONTACTS_FILE = os.path.join(DATA_FOLDER, 'contacts.json')
EVENTS_FILE = os.path.join(DATA_FOLDER, 'events.json')
COMPANY_INFO_FILE = os.path.join(DATA_FOLDER, 'company_info.json')

# Создаем папку для данных, если её нет
os.makedirs(DATA_FOLDER, exist_ok=True)

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

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    user = update.effective_user
    welcome_text = f"""
Привет, {user.first_name}! 👋

Я бот-помощник для вашей команды.

Доступные команды:
/start - Начало работы
/help - Помощь и список команд
/products - Товары и цены
/contacts - Контакты коллег
/events - Предстоящие события
/digest - Ежедневный дайджест
/about - О компании

Просто напишите вопрос, и я постараюсь помочь!
    """
    await update.message.reply_text(welcome_text)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /help"""
    help_text = """
📋 Доступные команды:

/contacts - Контакты команды
/events - Акции и мероприятия  
/products - Товары и цены
/digest - Ежедневный дайджест
/about - О компании
/help - Эта справка

💡 Вы также можете задавать вопросы:
- "Какие игры есть?"
- "Сколько стоит кастомизация?"
- "Как сделать заказ?"
- "Есть ли скидки?"
    """
    await update.message.reply_text(help_text)

async def contacts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать контакты коллег"""
    contacts_data = load_json(CONTACTS_FILE)
    
    if not contacts_data:
        await update.message.reply_text("📞 Контакты пока не добавлены.")
        return
    
    response = "📞 Контакты команды:\n\n"
    for name, info in contacts_data.items():
        response += f"👤 {name}\n"
        response += f"   Должность: {info.get('position', 'Не указана')}\n"
        response += f"   Телефон: {info.get('phone', 'Не указан')}\n"
        response += f"   Email: {info.get('email', 'Не указан')}\n"
        response += f"   Комментарий: {info.get('comment', 'Нет')}\n\n"
    
    await update.message.reply_text(response)

async def events(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать предстоящие события"""
    try:
        logger.info("Command /events received")
        
        events_data = load_json(EVENTS_FILE)
        logger.info(f"Loaded events data: {events_data}")
        
        if not events_data:
            await update.message.reply_text("📅 Событий на ближайшее время нет.")
            return
        
        today = datetime.now().date()
        response = "📅 **Предстоящие события и акции:**\n\n"
        events_found = False
        
        for event_name, event_info in events_data.items():
            try:
                event_date = datetime.strptime(event_info['date'], '%Y-%m-%d').date()
                days_left = (event_date - today).days
                
                # Показываем все события (прошедшие и будущие)
                status_icon = "🟢" if days_left >= 0 else "🔴"
                days_text = f"через {days_left} дн." if days_left > 0 else "сегодня" if days_left == 0 else f"прошло {-days_left} дн. назад"
                
                response += f"{status_icon} **{event_name}**\n"
                response += f"   📅 Дата: {event_info['date']} ({days_text})\n"
                response += f"   🏷 Тип: {event_info['type']}\n"
                response += f"   📝 {event_info['description']}\n"
                response += f"   📊 Статус: {event_info.get('status', 'активно')}\n\n"
                events_found = True
                
            except Exception as e:
                logger.error(f"Error processing event {event_name}: {e}")
                continue
        
        if not events_found:
            response = "❌ Не удалось загрузить информацию о событиях."
        
        await update.message.reply_text(response)
        
    except Exception as e:
        logger.error(f"Error in events command: {e}")
        await update.message.reply_text("❌ Произошла ошибка при загрузке событий. Проверьте файл events.json")

async def digest(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Ежедневный дайджест"""
    # Загружаем данные
    contacts_data = load_json(CONTACTS_FILE)
    events_data = load_json(EVENTS_FILE)
    company_info = load_json(COMPANY_INFO_FILE)
    
    today = datetime.now().date()
    
    # Формируем дайджест
    digest_text = "📊 Ежедневный дайджест\n\n"
    
    # Информация о компании
    if company_info:
        digest_text += f"🏢 {company_info.get('name', 'Компания')}\n"
        digest_text += f"   {company_info.get('description', '')}\n\n"
    
    # Ближайшие события (на неделю вперед)
    upcoming_events = []
    for event_name, event_info in events_data.items():
        event_date = datetime.strptime(event_info['date'], '%Y-%m-%d').date()
        days_diff = (event_date - today).days
        if 0 <= days_diff <= 7:
            upcoming_events.append((event_name, event_info, days_diff))
    
    if upcoming_events:
        digest_text += "📅 Ближайшие события:\n"
        for event_name, event_info, days_diff in upcoming_events:
            digest_text += f"   • {event_name} ({event_info['date']}) - через {days_diff} дн.\n"
        digest_text += "\n"
    
    # Контакты команды
    if contacts_data:
        digest_text += f"👥 Команда: {len(contacts_data)} человек(а)\n"
    
    digest_text += "\nХорошего дня! 🚀"
    
    await update.message.reply_text(digest_text)

async def about(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Информация о компании"""
    company_info = load_json(COMPANY_INFO_FILE)
    
    if not company_info:
        # Базовая информация, если файл не заполнен
        default_info = """
🏢 Наша компания

Мы - команда профессионалов, работающая над интересными проектами.

Основные направления:
• Разработка программного обеспечения
• Технологические решения
• Командная работа

💼 Наши ценности:
- Качество
- Инновации
- Сотрудничество

Для получения подробной информации обратитесь к администратору.
        """
        await update.message.reply_text(default_info)
    else:
        response = f"""
🏢 {company_info.get('name', 'Компания')}

{company_info.get('description', '')}

📞 Контакты:
Телефон: {company_info.get('phone', 'Не указан')}
Email: {company_info.get('email', 'Не указан')}
Адрес: {company_info.get('address', 'Не указан')}

💼 Сфера: {company_info.get('industry', 'Не указана')}
        """
        await update.message.reply_text(response)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка текстовых сообщений"""
    user_message = update.message.text.lower()
    
    # Простой анализ сообщения
    if any(word in user_message for word in ['компани', 'о компани', 'организац']):
        await about(update, context)
    
    elif any(word in user_message for word in ['контакт', 'телефон', 'email', 'коллег']):
        await contacts(update, context)
    
    elif any(word in user_message for word in ['событи', 'встреч', 'мероприят', 'дедлайн']):
        await events(update, context)
    
    elif any(word in user_message for word in ['дайджест', 'итог', 'сводк']):
        await digest(update, context)
    
    elif any(word in user_message for word in ['привет', 'здравств', 'hello', 'hi']):
        await update.message.reply_text("Привет! Чем могу помочь? 😊")
    
    else:
        await update.message.reply_text(
            "Я пока не знаю ответ на этот вопрос. "
            "Попробуйте использовать команды из меню /help или задайте вопрос по-другому."
        )

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик ошибок"""
    logger.error(f"Exception while handling an update: {context.error}")

def main():
    """Основная функция запуска бота"""
    if not BOT_TOKEN:
        logger.error("BOT_TOKEN not found in environment variables")
        return
    
    # Создаем приложение
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Добавляем обработчики
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("products", products))
    application.add_handler(CommandHandler("contacts", contacts))
    application.add_handler(CommandHandler("events", events))
    application.add_handler(CommandHandler("digest", digest))
    application.add_handler(CommandHandler("about", about))
    
    # Обработчик текстовых сообщений
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Обработчик ошибок
    application.add_error_handler(error_handler)
    
    # Запуск бота
    logger.info("Bot is starting...")
    application.run_polling()

async def products(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать ассортимент товаров"""
    try:
        products_data = load_json(os.path.join(DATA_FOLDER, 'products.json'))
        
        if not products_data or 'products' not in products_data:
            await update.message.reply_text("🎲 Информация о товарах временно недоступна.")
            return
        
        response = "🎲 **Наши товары и цены:**\n\n"
        
        for product_key, product in products_data['products'].items():
            response += f"🎯 **{product['name']}**\n"
            response += f"   💰 Цена: {product['price']} руб.\n"
            if product.get('original_price'):
                response += f"   🔥 Было: {product['original_price']} руб. (скидка {product.get('discount', '')})\n"
            response += f"   📝 {product['description']}\n"
            response += f"   ⏱ Срок изготовления: {product['delivery_time']}\n\n"
        
        # Добавляем информацию об акциях
        if products_data.get('current_promotions'):
            response += "🎁 **Текущие акции:**\n"
            for promotion in products_data['current_promotions']:
                response += f"   • {promotion}\n"
        
        await update.message.reply_text(response)
    except Exception as e:
        logger.error(f"Error in products command: {e}")
        await update.message.reply_text("❌ Произошла ошибка при загрузке информации о товарах.")

if __name__ == '__main__':
    main()