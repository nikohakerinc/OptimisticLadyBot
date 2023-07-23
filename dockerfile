# Установка образа Alpine Linux содержащего Python 3.10.11 из DockerHub
FROM python:3.10.11-alpine3.16

# Запускаем команду pip install для всех необходимых библиотек
RUN pip install --upgrade pip \
    && pip install python-dotenv \
    && pip install requests \
    && pip install openai \
    && pip install beautifulsoup4 \
    && pip install pytz \
    && pip install aiogram

# Создаем рабочую директорию с ботом внутри контейнера
WORKDIR /opt/LadyBot