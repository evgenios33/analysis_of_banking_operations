import logging
import os
from logging.handlers import RotatingFileHandler
from pathlib import Path

from .services import main_services
from .views import main_info

log_path = os.getenv("LOG_FILE", "logs/app.log")

log_dir = Path(log_path).parent
log_dir.mkdir(parents=True, exist_ok=True)

root_logger = logging.getLogger()
root_logger.setLevel(logging.DEBUG)

file_formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s: %(message)s")

file_handler = RotatingFileHandler(log_path, maxBytes=5 * 1024 * 1024, backupCount=3, encoding="utf-8")
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(file_formatter)

root_logger.addHandler(file_handler)

if __name__ == "__main__":
    print(main_info("2021-10-04 22:00:00"))
    print(main_services("каршер"))
