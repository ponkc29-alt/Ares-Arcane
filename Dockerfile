FROM python:3.10-slim

WORKDIR /app

# Копируем файлы
COPY . .

# Устанавливаем нужные библиотеки (telebot и flask)
RUN pip install pyTelegramBotAPI flask

# Открываем порт 8080 для Koyeb
EXPOSE 8080

# Запускаем нашего бота
CMD ["python", "main.py"]
