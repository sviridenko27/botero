# Кондитерская витрина (FastAPI)

Веб-сайт витрина с разделами:
- Серийная продукция (торты, пирожные)
- Каталог (свадебные, день рождения, детские, все)
- Начинки
- Доставка и оплата (телефон, адрес, условия)

Также доступна панель владельца для управления товарами и контентом.

## Технологии
- Backend: FastAPI + SQLAlchemy + SQLite
- Frontend: Jinja2 шаблоны + HTML/CSS/JS

## Установка и запуск

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Сайт: `http://127.0.0.1:8000/`

Админка: `http://127.0.0.1:8000/admin/login`

## Доступ в админ-панель
По умолчанию:
- `owner`
- `owner123`

Можно переопределить переменными окружения:
- `ADMIN_USERNAME`
- `ADMIN_PASSWORD`
- `SESSION_SECRET`
- `DATABASE_URL` (по умолчанию `sqlite:///./shop.db`)

## Запуск через Docker Compose

```bash
docker compose up --build
```

Приложение будет доступно на `http://127.0.0.1:8000/`.

Данные SQLite сохраняются в директории `data/` на хосте.

Остановить контейнеры:

```bash
docker compose down
```

## Запуск через Makefile

```bash
make build
make up
```

Полезные команды:
- `make run` - локальный запуск через `uvicorn --reload`
- `make down` - остановить контейнеры
- `make logs` - смотреть логи

## API
- `GET /api/products` - список товаров
- `GET /api/fillings` - список начинок
