FROM python:3.10-slim
WORKDIR /app
COPY . .
RUN pip install pyTelegramBotAPI flask
CMD ["python", "main.py"]
