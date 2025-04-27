import re

DATE_PATTERN = r"(\d{4}\d{2}\d{2})"
REPORT_DATE_PATTERN = r"(\d{4}.\d{2}.\d{2})"

LOG_PATTERN = re.compile(
    r"""
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
""",
    re.VERBOSE,
)

CONFIG = {
    "REPORT_SIZE": 5,
    "REPORT_DIR": "./reports/",
    "LOG_DIR": "./log/",
    "LOG_FILE_PATH": "./log/",
}

BASE_TEMPLATE_PATH = "./templates/report.html"
