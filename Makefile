.PHONY: help up down build migrate shell logs ps clean backup restore

help:
	@echo "Доступные команды:"
	@echo "  make up          - Запустить проект (с пересборкой)"
	@echo "  make down        - Остановить и удалить контейнеры"
	@echo "  make build       - Пересобрать образ"
	@echo "  make migrate     - Применить миграции"
	@echo "  make shell       - Зайти в shell веб-контейнера"
	@echo "  make logs        - Посмотреть логи"
	@echo "  make ps          - Статус контейнеров"
	@echo "  make clean       - Полная очистка (осторожно!)"
	@echo "  make backup      - Создать бэкап базы"

up:
	docker compose up --build -d
	@echo "Проект запущен! Открой http://localhost:8000"

down:
	docker compose down

build:
	docker compose build --no-cache

migrate:
	docker compose exec web python manage.py migrate

shell:
	docker compose exec web python manage.py shell

logs:
	docker compose logs -f web

ps:
	docker compose ps

clean:
	docker compose down -v --remove-orphans
	docker system prune -f

backup:
	docker compose exec db pg_dump -U ${POSTGRES_USER} ${POSTGRES_DB} > backup_$(date +%Y%m%d_%H%M%S).sql
	@echo "Бэкап создан!"