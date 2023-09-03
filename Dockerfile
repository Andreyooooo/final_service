# Используем образ Python Alpine
FROM python:3.9-alpine

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем файлы проекта в контейнер
COPY . /app

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt


# Запускаем сервер
CMD [ "python", "./server.py" ]