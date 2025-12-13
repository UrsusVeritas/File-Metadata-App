# 1. СТРОИТЕЛЬНАЯ СТАДИЯ (Builder Stage) - Для установки зависимостей
FROM python:3.11-slim as builder

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 2. ФИНАЛЬНАЯ СТАДИЯ (Final Stage) - Легкий образ с кодом
FROM python:3.11-slim

# Копируем установленные зависимости из builder-стадии
COPY --from=builder /usr/local/ /usr/local/

WORKDIR /app
COPY . .

EXPOSE 5000

# Запуск приложения через Gunicorn
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app:app"]