import pytest

from log_analyzer import LogAnalyzer


@pytest.fixture
def setup_logs(tmp_path):
    log_dir = tmp_path / "logs/"
    log_dir.mkdir()

    filenames = [
        "nginx-access-ui.log-20230101.gz",
        "nginx-access-ui.log-20230215.gz",
    ]

    for name in filenames:
        file_path = log_dir / name
        file_path.write_text("dummy")

    return str(log_dir) + "/"


def test_find_latest_file_correctly_selects_latest(setup_logs: str):
    analyzer = LogAnalyzer()
    analyzer.LOG_DIR = setup_logs

    analyzer.find_latest_file()

    assert analyzer.log_file_data.file_name == "nginx-access-ui.log-20230215.gz"
    assert analyzer.log_file_data.file_date == "2023.02.15"
    print("Тест прошел успешно!")
