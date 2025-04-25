import argparse
import gzip
import json
import logging.config
import mimetypes
import os
import re
import statistics
import sys
from dataclasses import dataclass
from datetime import datetime
from operator import itemgetter
from string import Template
from typing import Any, Generator, Optional, TypedDict, cast

import structlog

from constants import BASE_TEMPLATE_PATH, CONFIG, DATE_PATTERN, LOG_PATTERN

RESULT = []
LOG_FILE_PATH = None

timestamper = structlog.processors.TimeStamper(fmt="iso", utc=True)

structlog.configure(
    processors=[
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        timestamper,
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
    ],
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)
log = structlog.get_logger()


parser = argparse.ArgumentParser()
parser.add_argument("--config", help="set absolute path to config file")
args = parser.parse_args()


@dataclass
class File:
    file_name: Optional[str]
    file_path: Optional[str]
    file_type: Optional[str]
    file_date: Optional[str]


class UrlSummary(TypedDict):
    count: int
    request_times: list[float]


class LogAnalyzer:
    log_file_data: File = File(
        file_type=None, file_date=None, file_name=None, file_path=None
    )

    def __init__(self) -> None:
        CONFIG: dict[str, Any]
        self.REPORT_SIZE: Optional[int | None] = CONFIG.get("REPORT_SIZE")
        self.REPORT_DIR: Optional[str | None] = CONFIG.get("REPORT_DIR")
        self.LOG_DIR: Optional[str | None] = CONFIG.get("LOG_DIR")
        self.LOG_FILE_PATH: Optional[str | None] = CONFIG.get("LOG_FILE_PATH")

    def get_config_data(self) -> None:
        """A method for parsing config"""
        if args.config:
            with open(args.config, "r", encoding="utf-8") as f:
                config_file_data = f.read()
                js = json.loads(config_file_data)
                self.REPORT_SIZE = (
                    js.get("REPORT_SIZE") if js.get("REPORT_SIZE") else self.REPORT_SIZE
                )
                self.REPORT_DIR = (
                    js.get("REPORT_DIR") if js.get("REPORT_DIR") else self.REPORT_DIR
                )
                self.LOG_DIR = js.get("LOG_DIR") if js.get("LOG_DIR") else self.LOG_DIR
                self.LOG_FILE_PATH = (
                    js.get("LOG_FILE_PATH")
                    if js.get("LOG_FILE_PATH")
                    else self.LOG_FILE_PATH
                )

    def get_logging_config(self) -> None:
        """A method for configure logs and choose output: stdout or file"""
        logging_config: dict[str, Any] = {}
        logging_config = {
            "version": 1,
            "disable_existing_loggers": False,
            "handlers": {
                "file": {
                    "level": "DEBUG",
                    "class": "logging.handlers.WatchedFileHandler",
                    "filename": "logs.log",
                },
                "default": {
                    "level": "DEBUG",
                    "class": "logging.StreamHandler",
                },
            },
            "loggers": {
                "root": {
                    "handlers": [],
                    "level": "DEBUG",
                    "propagate": True,
                },
            },
        }
        if self.LOG_FILE_PATH:
            logging_config["loggers"]["root"]["handlers"].append("file")
        else:
            logging_config["loggers"]["root"]["handlers"].append("default")

        logging.config.dictConfig(logging_config)

    def find_latest_file(self) -> None:
        """The method searches for the most recent nginx log by date in the format plain/gz"""
        for filename in os.listdir(self.LOG_DIR):
            file_path = f"{self.LOG_DIR}{filename}"
            file_type = mimetypes.guess_type(file_path)[1]
            if file_type == "gzip" or file_type is None:
                match = re.search(DATE_PATTERN, filename)
                if match:
                    file_date_str = match.group(1)
                    file_date = datetime.strptime(file_date_str, "%Y%m%d")
                    formatted_date = file_date.strftime("%Y.%m.%d")
                    if (
                        self.log_file_data.file_date is None
                        or formatted_date > self.log_file_data.file_date
                    ):
                        self.log_file_data.file_date = formatted_date
                        self.log_file_data.file_name = filename
                        self.log_file_data.file_path = file_path
                        self.log_file_data.file_type = file_type
            else:
                log.debug("Unknown file type found")
        if not self.log_file_data.file_date:
            log.warning("There is no log file for processing")
            sys.exit()

    def parse_file(self) -> Generator:
        """Generator function for parsing logs from a file"""
        open_func = gzip.open if self.log_file_data.file_type == "gzip" else open
        if self.log_file_data.file_path is not None:
            with open_func(self.log_file_data.file_path, "rt") as file:
                for line in file:
                    line = line.strip()
                    if line:
                        match = LOG_PATTERN.match(line)
                        if match:
                            data = match.groupdict()
                            yield data
                        else:
                            log.warning(
                                f"Строка в логах имеет неправильный формат - {line}"
                            )

    def analyse(self) -> None:
        """A method for analyzing logs"""
        summary: dict[str, UrlSummary] = {}
        count_data: int = 0

        # Calculating the number of unique URLs and creating a list with request_times
        for data_item in self.parse_file():
            if len(data_item["request"].split(" ")) > 1:
                url = data_item["request"].split(" ")[1]
                request_time = float(data_item["request_time"])
                if url not in summary:
                    summary[url] = UrlSummary(count=1, request_times=[request_time])
                else:
                    summary[url]["count"] += 1
                    summary[url]["request_times"].append(request_time)
                count_data += 1

        # Create statistics
        for url, dictionary in summary.items():
            statistic = {}
            request_times = cast(list[float], dictionary["request_times"])
            time_sum = sum(request_times)
            statistic["url"] = url
            statistic["count"] = dictionary["count"]
            statistic["time_sum"] = "{:.3f}".format(time_sum)
            statistic["time_avg"] = "{:.3f}".format(time_sum / 2)
            statistic["time_max"] = "{:.3f}".format(max(request_times))
            statistic["time_med"] = "{:.3f}".format(statistics.median(request_times))
            statistic["count_perc"] = "{:.3f}".format(
                dictionary["count"] * 100 / count_data
            )
            statistic["time_perc"] = "{:.3f}".format(time_sum * 100 / count_data)
            RESULT.append(statistic)

    def create_report(self) -> None:
        """A method for sorting and rendering an html template with a report"""
        sorted_result = sorted(RESULT, key=itemgetter("time_sum"), reverse=True)
        table_json = json.dumps(sorted_result[: self.REPORT_SIZE])
        with open(BASE_TEMPLATE_PATH, "r", encoding="utf-8") as file:
            template_string = file.read()
        template = Template(template_string)
        rendered_html = template.safe_substitute(table_json=table_json)
        report_path = f"{self.REPORT_DIR}report-{self.log_file_data.file_date}.html"
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(rendered_html)
        log.info(f"A report has been created - {report_path}")


def main():
    analyse_logs = LogAnalyzer()
    analyse_logs.get_config_data()
    analyse_logs.get_logging_config()
    log.info("Starting Script...")
    log.info(
        f"The script is running with this config data: REPORT_SIZE - {analyse_logs.REPORT_SIZE}, "
        f"REPORT_DIR - {analyse_logs.REPORT_DIR}, LOG_DIR - {analyse_logs.LOG_DIR}, LOG_FILE_PATH - {analyse_logs.LOG_FILE_PATH}"
    )
    analyse_logs.find_latest_file()
    analyse_logs.analyse()
    analyse_logs.create_report()


if __name__ == "__main__":
    main()
