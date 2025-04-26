.ONESHELL:

APP_DIR = app
APP_VERSION = 1.0

.PHONY: help
help: ## Вывод справки
	@egrep '^[\.a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

.PHONY: setup
setup: ## Установка проекта и pre-commit
	@uv sync
	@. .venv/bin/activate
	@pre-commit autoupdate
	@pre-commit install
	@echo ""
	@echo "$$(tput setaf 1)Активируй venv с помощью: $$(tput setaf 2)source .venv/bin/activate$$(tput sgr0)"
	@echo ""

.PHONY: up
up: ## Запуск контейнера
	@sudo docker compose up -d --no-deps --build

.PHONY: down
down: ## Остановка контейнера
	@sudo docker compose down

.PHONY: analyse
analyse: ## Запуск скрипта
	@sudo docker compose exec app uv run log_analyzer.py

.PHONY: pre-commit
pre-commit: ## Запуск pre-commit для всех файлов
	@pre-commit run --all-files
