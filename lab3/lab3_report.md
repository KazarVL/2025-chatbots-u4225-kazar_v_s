University: [ITMO University](https://itmo.ru/ru/)
Faculty: [FICT](https://fict.itmo.ru)
Course: [Vibe Coding: AI-боты для бизнеса](https://github.com/itmo-ict-faculty/vibe-coding-for-business)
Year: 2025/2026
Group: u4225
Author: Kazar Vladimir Sergeevich
Lab: Lab2
Date of create: 25.10.2025
Date of finished: 04.11.2025

- URL бота: @itmoftmi_GameBored_bot

Отчет по деплою Telegram бота GameBored
1. Описание деплоя
Выбранный способ: Docker + VPS (Selected)
Почему именно этот способ:
а)Полный контроль над сервером
б)Надежность и стабильность работы 24/7
в)Гибкость в настройке и масштабировании
г)Подходит для учебного проекта с перспективой роста
д)URL бота: t.me/GameBored_Assistant_Bot

2. Процесс деплоя
Пошаговая инструкция:
2.1 Подготовка проекта
Создана структура файлов для Docker
Написан Dockerfile и docker-compose.yml
Подготовлены файлы данных (JSON)

2.2 Настройка VPS
Выбран тариф в cloud.reg.ru: 1 ядро, 1GB RAM, 10GB SSD
Установлен Docker и Docker Compose
Настроен firewall

2.3 Деплой на сервер
git clone <репозиторий>
docker-compose up -d --build

2.4.Настройка бота
Создан .env файл с токеном бота
Настроена база данных SQLite
Проверена работа всех команд

Проблемы и решения:
Проблема 1: Ошибки при сборке Docker
Причина: Медленные репозитории и таймауты
Решение: Использование легкого образа Alpine и китайских зеркал

Проблема 2: База данных не инициализировалась
Причина: Несоответствие названий методов в database.py
Решение: Исправление init_database() на init_db()

Проблема 3: Команды БД не работали
Причина: Файлы данных не копировались в контейнер
Решение: Ручное копирование через docker cp

3. Сбор фидбека
Количество пользователей: 5 тестовых пользователей

Статистика использования:
Наиболее популярные команды: /start, /products, /about
Добавлено 2 тестовых заказа
15+ запросов к базе данных

Скриншоты отзывов:

<img width="436" height="109" alt="image" src="https://github.com/user-attachments/assets/08b0aa2b-610e-4db1-a186-edde977838cb" />
<img width="469" height="93" alt="image" src="https://github.com/user-attachments/assets/b7845d17-ce20-408d-8403-365225d70714" />
<img width="435" height="88" alt="image" src="https://github.com/user-attachments/assets/6fd9859e-e26c-460c-9ead-d5570da20c20" />
<img width="449" height="88" alt="image" src="https://github.com/user-attachments/assets/5ba281ff-ffeb-4157-8802-5f981e932786" />

4. Анализ фидбека
Главные проблемы:
Сложность добавления заказов для новичков
Отсутствие поиска по клиентам
Нет фильтрации заказов по дате

Что понравилось пользователям:
Простой и понятный интерфейс
Полная информация о компании и товарах
Быстрый отклик команд

Приоритеты улучшений:
Улучшенная валидация команды /add_order
Поиск заказов по клиенту
Фильтрация заказов по дате

5. Улучшения
Реализованные улучшения:
1) Улучшенная валидация /add_order
Добавлены подсказки при ошибках
if len(args) < 3:
    help_text = "❌ Неверный формат!\\n✅ Используйте: /add_order [клиент] [товар] [количество]"
    bot.reply_to(message, help_text)
    return
2) Команда поиска /find_order
@bot.message_handler(commands=['find_order'])
def find_order(message):
    (Поиск заказов по имени клиента)
    orders = db.find_orders_by_customer(customer_name)
3. Команда /recent_orders
@bot.message_handler(commands=['recent_orders'])
def recent_orders(message):
    (Показ заказов за последние 7 дней)
    orders = db.get_orders_since(week_ago)

Демонстрация улучшений: 
Улучшенная валидация /add_order

<img width="409" height="251" alt="image" src="https://github.com/user-attachments/assets/7374e73e-fab4-49cb-a0de-f1effb3aaf5b" />

Команда поиска /find_order

<img width="241" height="257" alt="image" src="https://github.com/user-attachments/assets/4bbfb819-e17c-4ae8-92ba-7c10d8888f07" />

Команда /recent_orders

<img width="284" height="257" alt="image" src="https://github.com/user-attachments/assets/29d087d3-ad3b-45df-bd9e-4ae0317032d0" />


Результаты улучшений:
Уменьшилось количество ошибок при добавлении заказов
Пользователи могут быстро находить нужные заказы
Упростилась работа с актуальными данными

6. Выводы
Что получилось хорошо:
✅ Успешный деплой на VPS с Docker
✅ Стабильная работа 24/7
✅ Полная функциональность базы данных
✅ Понятный интерфейс для пользователей
✅ Быстрое реагирование на фидбек

Что можно улучшить дальше:
Добавить веб-панель для администрирования
Реализовать уведомления о новых заказах
Добавить систему ролей пользователей
Интегрировать с внешними API (доставка, платежи)

Чему научился:
Деплой приложений на VPS с Docker
Работа с SQLite в контейнерах
Обработка пользовательского фидбека
Оптимизация Docker образов
Решение сетевых проблем при деплое

Итог: Проект успешно завершен! Бот работает стабильно, пользователи довольны функциональностью, а архитектура позволяет легко масштабировать проект в будущем.
