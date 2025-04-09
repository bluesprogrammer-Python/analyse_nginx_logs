import argparse
import os
import re
import json
import gzip
import statistics
import structlog
import logging
import mimetypes
from dataclasses import dataclass
from datetime import datetime
from string import Template
from flask import Flask, render_template
from operator import itemgetter
from typing import Generator


app = Flask(__name__, template_folder='./reports')

DATE_PATTERN = r'(\d{4}\d{2}\d{2})'
LOG_PATTERN = re.compile(r'''
    (?P<remote_addr>\S+)
    \s+(?P<remote_user>\S+)
    \s+(?P<http_x_real_ip>\S+)
    \s+\[(?P<time_local>.+?)\]
    \s+"(?P<request>.*?)"
    \s+(?P<status>\d{3})
    \s+(?P<body_bytes_sent>\d+)
    \s+"(?P<http_referer>.*?)"
    \s+"(?P<http_user_agent>.*?)"
    \s+(?P<http_x_forwarded_for>.*?)
    \s+"(?P<http_x_request_id>.*?)"
    \s+"(?P<http_x_rb_user>.*?)"
    \s+(?P<request_time>\d+\.\d+)
''', re.VERBOSE)
CONFIG = {
    "REPORT_SIZE": 1000,
    "REPORT_DIR": "./reports/",
    "LOG_DIR": "./log/"
}
BASE_TEMPLATE_PATH = './templates/report.html'
RESULT = []

logging.basicConfig(
    format='%(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler("logs.log"),
        logging.StreamHandler()
    ]
)

structlog.configure(
    processors=[
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.StackInfoRenderer(),
        structlog.dev.set_exc_info,
        structlog.processors.TimeStamper(fmt="%Y-%m-%d %H:%M:%S", utc=False),
        structlog.dev.ConsoleRenderer()
    ],
    context_class=dict,
    wrapper_class=structlog.stdlib.BoundLogger,
    logger_factory=structlog.stdlib.LoggerFactory(),
)

# Нужно учитывать логи уровня DEBUG, INFO и ERROR
log = structlog.get_logger()


@dataclass
class File:
    file_name: str
    file_path: str
    file_type: str
    file_date: str


def find_latest_file(config_data: dict) -> dataclass:
    """Функция ищет самый свежий по дате лог nginx в формате plain/gz"""
    LOG_DIR = config_data['LOG_DIR']
    latest_file_name = None
    latest_file_path = None
    latest_file_date = None
    latest_file_type = None
    for filename in os.listdir(LOG_DIR):
        file_path = f"{LOG_DIR}{filename}"
        file_type = mimetypes.guess_type(file_path)[1]
        if file_type == 'gzip' or file_type is None:
            match = re.search(DATE_PATTERN, filename)
            if match:
                file_date_str = match.group(1)
                file_date = datetime.strptime(file_date_str, '%Y%m%d')
                formatted_date = file_date.strftime('%Y.%m.%d')
                if latest_file_date is None or formatted_date > latest_file_date:
                    latest_file_date = formatted_date
                    latest_file_name = filename
                    latest_file_path = file_path
                    latest_file_date = formatted_date
        else:
            log.info('Найден неизвестный тип файла')
    if not latest_file_name:
        log.warning('Файл с логами для обработки отсутствует')
    if latest_file_name:
        return File(latest_file_name, latest_file_path, latest_file_type, latest_file_date)


def parse_file(file_data: dataclass) -> Generator:
    """Функция-генератор для парсинга логов из файла"""
    open_func = gzip.open if file_data.file_type == "gzip" else open
    with open_func(file_data.file_path, 'rt') as file:
        for line in file:
            line = line.strip()
            if line:
                match = LOG_PATTERN.match(line)
                if match:
                    data = match.groupdict()
                    yield data
                else:
                    log.warning(f'Строка в логах имеет неправильный формат - {line}')


def analyse_log(file_data: dataclass):
    """Функция для анализа логов"""
    summary = {}
    count_data = 0

    # Подсчёт кол-ва уникальных url и создание списка request_times
    for data_item in parse_file(file_data):
        if len(data_item['request'].split(' ')) > 1:
            url = data_item['request'].split(' ')[1]
            request_time = float(data_item['request_time'])
            if url not in summary:
                summary[url] = {
                    'count': 1,
                    'request_times': [request_time],
                }
            else:
                summary[url]['count'] += 1
                summary[url]['request_times'].append(request_time)
            count_data += 1

    # Создание статистики
    for url, dictionary in summary.items():
        statistic = {}
        time_sum = sum(dictionary['request_times'])
        statistic['url'] = url
        statistic['count'] = dictionary['count']
        statistic['time_sum'] = '{:.3f}'.format(time_sum)
        statistic['time_avg'] = '{:.3f}'.format(time_sum / 2)
        statistic['time_max'] = '{:.3f}'.format(max(dictionary['request_times']))
        statistic['time_med'] = '{:.3f}'.format(statistics.median(dictionary['request_times']))
        statistic['count_perc'] = '{:.3f}'.format(dictionary['count'] * 100 / count_data)
        statistic['time_perc'] = '{:.3f}'.format(time_sum * 100 / count_data)
        RESULT.append(statistic)


def create_report(file_data: dataclass, config_data: dict) -> None:
    """Функция для сортировки и рендеринга html-шаблона с отчётом"""
    REPORT_DIR = config_data['REPORT_DIR']
    REPORT_SIZE = config_data['REPORT_SIZE']
    sorted_result = sorted(RESULT, key=itemgetter('time_sum'), reverse=True)
    table_json = json.dumps(sorted_result[:REPORT_SIZE])
    with open(BASE_TEMPLATE_PATH, 'r', encoding='utf-8') as file:
        template_string = file.read()
    template = Template(template_string)
    rendered_html = template.safe_substitute(table_json=table_json)
    report_patch = f"{REPORT_DIR}report-{file_data.file_date}.html"
    with open(report_patch, 'w', encoding='utf-8') as f:
        f.write(rendered_html)


@app.route('/')
def index():
    return render_template('report-2018.06.30.html')


def main(config):
    log.info("Скрипт запущен")
    config_data = CONFIG
    if config:
        print("Чтение конфига из файла")

    file_data = find_latest_file(config_data)
    analyse_log(file_data)
    create_report(file_data, config_data)
    app.run(debug=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', help='Для указания пути до кастомного конфига')
    args = parser.parse_args()
    main(args.config)
