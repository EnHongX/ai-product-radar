.PHONY: up down logs migrate api-shell web-shell

up:
	docker compose up --build

down:
	docker compose down

logs:
	docker compose logs -f

migrate:
	docker compose run --rm api alembic upgrade head

api-shell:
	docker compose run --rm api sh

web-shell:
	docker compose run --rm web sh
