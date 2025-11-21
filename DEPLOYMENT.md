# Инструкция по деплою DefectMaster Bot

## Информация о сервере

- **IP-адрес:** 5.180.24.215
- **Пользователь:** root  
- **Путь к проекту:** /root/defectmaster-bot
- **Метод запуска:** Docker Compose

## Быстрый деплой (обновление файлов)

### 1. Остановка бота

```bash
ssh root@5.180.24.215 "cd /root/defectmaster-bot && docker compose down"
```

### 2. Обновление файлов с локальной машины

```bash
# Из директории D:\Python\Stroykontrol_mvp_01
scp config.py root@5.180.24.215:/root/defectmaster-bot/
scp .env root@5.180.24.215:/root/defectmaster-bot/
scp bot/services/*.py root@5.180.24.215:/root/defectmaster-bot/bot/services/
```

### 3. Пересборка и запуск

```bash
ssh root@5.180.24.215 "cd /root/defectmaster-bot && docker compose up -d --build"
```

### 4. Проверка логов

```bash
ssh root@5.180.24.215 "docker logs defectmaster-bot --tail 50"
```

## Основные команды

```bash
# Остановить бота
ssh root@5.180.24.215 "cd /root/defectmaster-bot && docker compose down"

# Запустить бота
ssh root@5.180.24.215 "cd /root/defectmaster-bot && docker compose up -d"

# Перезапустить бота
ssh root@5.180.24.215 "cd /root/defectmaster-bot && docker compose restart"

# Пересобрать и запустить
ssh root@5.180.24.215 "cd /root/defectmaster-bot && docker compose up -d --build"

# Посмотреть логи
ssh root@5.180.24.215 "docker logs defectmaster-bot --tail 100"

# Следить за логами
ssh root@5.180.24.215 "docker logs defectmaster-bot -f"
```

## Обновление промптов

Промпты хранятся в Google Docs и обновляются **автоматически без перезапуска бота**.

- Документ: https://docs.google.com/document/d/1wmjP5Oy1VjtFg9tMXEqiJHyAeCcqeergmDfM77qUFw0/edit
- Изменения применяются при следующей загрузке фото

## Важные файлы

- `.env` - переменные окружения (токены, API ключи)
- `service-account.json` - Google Service Account credentials
- `data/bot.db` - база данных SQLite

---

**Последнее обновление:** 2025-11-20
