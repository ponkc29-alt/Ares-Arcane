FROM python:3.10-slim
WORKDIR /app
COPY . .
RUN pip install aiogram
EXPOSE 8000
CMD python main.py & python -m http.server 8000
