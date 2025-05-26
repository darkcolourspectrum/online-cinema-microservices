# Python образ
FROM python:3.11-slim

# Рабочая директория
WORKDIR /app

# Файл зависимостей
COPY requirements.txt .

# Зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копируем код приложения
COPY . .

# Порт
EXPOSE 8002

# Запуск
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8002"]