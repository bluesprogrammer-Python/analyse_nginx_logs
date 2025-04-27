# Analyse nginx logs


### Описание
Скрипт считывает данные из файла с логами nginx и составляет отчёт по самым запрашиваемым адресам.

Стандартный конфиг находится в файле constants.py:
```python
CONFIG = {
    "REPORT_SIZE": 5, # кол-во URL с наибольшим временем обработки
    "REPORT_DIR": "./reports/", # директория с отчётами
    "LOG_DIR": "./log/", # директория с логами
    "LOG_FILE_PATH": "./", # путь до файла с логами работы скрипта
}
```
Логи по умолчанию пишутся в файл logs.log, но если в конфиге не указан путь до файла с логами, то
логи пишутся в stdout.
При необходимости можно использовать кастомный конфиг.
Для этого нужно переопределить нужные переменные из основного конфига в файле custom_config.py.

### Технологии в проекте
	structlog 25.2.0

### Установка
1. Склонируйте проект
```bash
git clone git@github.com:bluesprogrammer-Python/analyse_nginx_logs.git
cd analyse_nginx_logs
```
2. Установите пакеты make и uv, если они отсутствуют на ВМ
```bash
sudo apt install make # Ubuntu
pip install uv
pip install --upgrade uv
```
3. Запустите установку зависимостей и настройку pre-commit
```bash
make setup
```
4. Создание контейнера со скриптом
```bash
make up
```
Можно запустить одной командой
```bash
make setup up
```

### Запуск скрипта
Запуск скрипта со стандартным конфигом в файле constants.py
```bash
make analyse
```
Запуск скрипт с кастомным конфигом
```bash
make analyse ARGS="--config custom_config.py"
```

### Остальные команды
Вызов справки
```bash
make
make help
```
Остановка контейнера со скриптом
```bash
make down
```
Вход в систему контейнера
```bash
make bash
```
Просмотр информации о контейнере
```bash
make ps
```

### Запуск тестов
Для запуска тестов нужно выполнить команду
```bash
pytest -s tests.py
```

### Автор
Семёнов Сергей (Github - bluesprogrammer-Python, telegram - seregabrat9)
