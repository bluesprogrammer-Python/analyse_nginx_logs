.ONESHELL:

APP_DIR = app
APP_VERSION = 1.0

.PHONY: help
help: ## Вывод справки
	@egrep '^[\.a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

.PHONY: up
up: ## Запуск контейнера
	@sudo docker compose up -d --no-deps --build

.PHONY: down
down: ## Остановка контейнера
	@sudo docker compose down

.PHONY: analyse
analyse: ## Запуск скрипта
	@sudo docker compose exec app uv run log_analyzer.py
