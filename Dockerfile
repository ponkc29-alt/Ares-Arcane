FROM python:3.10-slim
WORKDIR /app
COPY . .
RUN pip install aiogram
# Эта магия запустит бота и одновременно откроет порт 8000, чтобы Koyeb был доволен
CMD python main.py & python -m http.server 8000
