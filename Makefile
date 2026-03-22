SHELL := /bin/zsh
.DEFAULT_GOAL := help

PYTHON := python3
VENV := .venv
PIP := $(VENV)/bin/pip
UVICORN := $(VENV)/bin/uvicorn
COMPOSE := docker compose
APP := app.main:app
HOST := 127.0.0.1
PORT := 8000

.PHONY: help venv install run build up down restart logs ps clean

help:
	@echo "Доступные команды:"
	@echo "  make venv      - создать виртуальное окружение"
	@echo "  make install   - установить зависимости в .venv"
	@echo "  make run       - локальный запуск FastAPI (uvicorn --reload)"
	@echo "  make build     - собрать Docker-образ"
	@echo "  make up        - запустить проект в Docker Compose"
	@echo "  make down      - остановить Docker Compose"
	@echo "  make restart   - перезапустить Docker Compose"
	@echo "  make logs      - логи Docker Compose"
	@echo "  make ps        - статус контейнеров"
	@echo "  make clean     - удалить локальные временные файлы"

venv:
	$(PYTHON) -m venv $(VENV)

install: venv
	$(PIP) install -r requirements.txt

run: install
	$(UVICORN) $(APP) --host $(HOST) --port $(PORT) --reload

build:
	$(COMPOSE) build

up:
	$(COMPOSE) up --build

down:
	$(COMPOSE) down

restart: down up

logs:
	$(COMPOSE) logs -f

ps:
	$(COMPOSE) ps

clean:
	rm -rf __pycache__ app/__pycache__
