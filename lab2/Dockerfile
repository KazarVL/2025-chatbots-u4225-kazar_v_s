FROM python:3.11-slim

WORKDIR /app

# Копируем зависимости
COPY requirements.txt .

# Устанавливаем Python зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копируем код приложения
COPY . .

# Создаем папку для данных (если нужно)
RUN mkdir -p /app/data

# Запускаем бота
CMD ["python", "bot.py"]
