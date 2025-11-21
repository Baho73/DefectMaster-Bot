# Docker - Быстрый запуск DefectMaster Bot

## 🐳 Запуск через Docker Compose (рекомендуется)

### Предварительные требования

1. **Docker** установлен: https://docs.docker.com/get-docker/
2. **Docker Compose** установлен (обычно идет с Docker Desktop)

### Шаг 1: Подготовка файлов

Убедитесь, что у вас есть:
- ✅ `.env` файл с настройками
- ✅ `service-account.json` в корне проекта

### Шаг 2: Создание папки для БД

```bash
mkdir -p data
```

### Шаг 3: Запуск бота

```bash
docker-compose up -d
```

**Параметры:**
- `-d` - запуск в фоновом режиме (detached)

### Шаг 4: Проверка логов

```bash
# Просмотр логов в реальном времени
docker-compose logs -f

# Последние 100 строк
docker-compose logs --tail=100

# Только ошибки
docker-compose logs | grep ERROR
```

### Остановка бота

```bash
docker-compose down
```

### Перезапуск после изменений

```bash
# Пересборка образа
docker-compose build

# Запуск с пересборкой
docker-compose up -d --build
```

---

## 🐋 Ручной запуск через Docker (без compose)

### Шаг 1: Сборка образа

```bash
docker build -t defectmaster-bot .
```

### Шаг 2: Создание volume для БД

```bash
docker volume create defectmaster-data
```

### Шаг 3: Запуск контейнера

```bash
docker run -d \
  --name defectmaster-bot \
  --restart always \
  --env-file .env \
  -v $(pwd)/service-account.json:/app/service-account.json:ro \
  -v defectmaster-data:/app/data \
  defectmaster-bot
```

**Windows PowerShell:**
```powershell
docker run -d `
  --name defectmaster-bot `
  --restart always `
  --env-file .env `
  -v ${PWD}/service-account.json:/app/service-account.json:ro `
  -v defectmaster-data:/app/data `
  defectmaster-bot
```

### Просмотр логов

```bash
docker logs -f defectmaster-bot
```

### Остановка и удаление

```bash
docker stop defectmaster-bot
docker rm defectmaster-bot
```

---

## 📊 Управление контейнером

### Статус контейнера

```bash
docker ps
# или
docker-compose ps
```

### Перезапуск

```bash
docker restart defectmaster-bot
# или
docker-compose restart
```

### Вход в контейнер (для отладки)

```bash
docker exec -it defectmaster-bot /bin/bash
# или
docker-compose exec bot /bin/bash
```

### Просмотр использования ресурсов

```bash
docker stats defectmaster-bot
```

---

## 🗄️ Работа с базой данных

### Бэкап БД

```bash
# Docker Compose
docker-compose exec bot cp /app/data/bot.db /app/data/bot.db.backup

# Копирование на хост
docker cp defectmaster-bot:/app/data/bot.db ./bot.db.backup
```

### Восстановление БД

```bash
docker cp ./bot.db.backup defectmaster-bot:/app/data/bot.db
docker-compose restart
```

---

## 🔧 Обновление бота

### Способ 1: Git pull + rebuild

```bash
# Остановить контейнер
docker-compose down

# Получить обновления
git pull

# Пересобрать и запустить
docker-compose up -d --build
```

### Способ 2: Ручная замена файлов

```bash
# Остановить
docker-compose down

# Обновить файлы (например, скопировать новый код)

# Пересобрать
docker-compose build

# Запустить
docker-compose up -d
```

---

## 🐛 Отладка проблем

### Контейнер не запускается

```bash
# Посмотреть логи
docker-compose logs

# Проверить статус
docker-compose ps

# Проверить конфигурацию
docker-compose config
```

### Ошибки в логах

```bash
# Фильтр только ошибок
docker-compose logs | grep -i error

# Последние 50 строк
docker-compose logs --tail=50
```

### Проблемы с .env

```bash
# Проверить переменные окружения в контейнере
docker exec defectmaster-bot env

# или
docker-compose exec bot env
```

### Проблемы с service-account.json

```bash
# Проверить наличие файла
docker exec defectmaster-bot ls -la /app/service-account.json

# Проверить содержимое
docker exec defectmaster-bot cat /app/service-account.json
```

---

## 📦 Структура Docker

### Dockerfile

```dockerfile
FROM python:3.10-slim

WORKDIR /app

# Установка зависимостей
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копирование кода
COPY . .

# Volume для БД
VOLUME ["/app/data"]

# Переменные окружения
ENV DATABASE_PATH=/app/data/bot.db
ENV PYTHONUNBUFFERED=1

# Запуск бота
CMD ["python", "main.py"]
```

### docker-compose.yml

```yaml
version: '3.8'

services:
  bot:
    build: .
    container_name: defectmaster-bot
    restart: always
    env_file:
      - .env
    volumes:
      - ./data:/app/data
      - ./service-account.json:/app/service-account.json:ro
    environment:
      - DATABASE_PATH=/app/data/bot.db
      - GOOGLE_SERVICE_ACCOUNT_FILE=/app/service-account.json
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

---

## 🚀 Продакшн развертывание

### На VPS с Docker

```bash
# 1. Подключиться к серверу
ssh user@your-server.com

# 2. Установить Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# 3. Клонировать проект
git clone <repo-url> defectmaster-bot
cd defectmaster-bot

# 4. Настроить .env и service-account.json

# 5. Запустить
docker-compose up -d

# 6. Проверить логи
docker-compose logs -f
```

### Автозапуск при перезагрузке сервера

Docker Compose автоматически настроен на `restart: always`, поэтому контейнер автоматически запустится после перезагрузки сервера.

---

## ⚙️ Дополнительные настройки

### Ограничение памяти

Отредактировать `docker-compose.yml`:

```yaml
services:
  bot:
    ...
    deploy:
      resources:
        limits:
          memory: 512M
        reservations:
          memory: 256M
```

### Сетевая изоляция

```yaml
services:
  bot:
    ...
    networks:
      - bot-network

networks:
  bot-network:
    driver: bridge
```

---

## 📋 Чеклист Docker развертывания

- [ ] Docker установлен
- [ ] Docker Compose установлен
- [ ] Создан `.env` с токенами
- [ ] `service-account.json` в корне проекта
- [ ] Создана папка `data/`
- [ ] Запущен `docker-compose build`
- [ ] Запущен `docker-compose up -d`
- [ ] Проверены логи (`docker-compose logs`)
- [ ] Бот отвечает в Telegram
- [ ] Настроен автозапуск (`restart: always`)

---

## 💡 Полезные команды

```bash
# Просмотр всех контейнеров
docker ps -a

# Удаление остановленных контейнеров
docker container prune

# Удаление неиспользуемых образов
docker image prune

# Очистка всего (осторожно!)
docker system prune -a

# Экспорт логов в файл
docker-compose logs > logs.txt

# Мониторинг в реальном времени
docker stats
```

---

**Готово!** Бот запущен в Docker и готов к работе.

Для продакшн используйте `docker-compose.yml` с настройками ограничения ресурсов и логирования.
