import json
import logging

from .file_paths import PATH_OPERATIONS_FILE, PATH_USER_SETTINGS_FILE
from .utils import (
    filter_df_by_period,
    get_a_date_range,
    get_currency_rates,
    get_greeting,
    get_info_on_cards,
    get_stock_prices,
    get_top_transactions,
)

views_logger = logging.getLogger(__name__)
views_logger.setLevel(logging.DEBUG)
file_handler = logging.FileHandler("logs/views.log", mode="a", encoding="utf-8")
file_formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s: %(message)s")
file_handler.setFormatter(file_formatter)
views_logger.addHandler(file_handler)


def main_info(user_date: str) -> str:
    """
    Собирает комплексный отчёт по финансовым операциям за период с начала месяца,
    на который выпадает входящая дата, по входящую дату.

    Функция формирует JSON‑строку со следующими данными:
        - приветствие;
        - агрегированная информация по картам (расходы, кешбэк);
        - топ‑5 транзакций по сумме;
        - курсы валют (относительно RUB) для пользовательских валют;
        - текущие цены акций для пользовательских тикеров.
    """
    try:
        # Приветствие
        greeting = get_greeting()

        # Определение диапазона дат
        start_date, end_date = get_a_date_range(user_date)
        views_logger.debug(f"Период отчёта: {start_date} — {end_date}")

        # Загрузка и фильтрация операций
        filtered_df = filter_df_by_period(PATH_OPERATIONS_FILE, start_date, end_date)

        if filtered_df.empty:
            views_logger.info(f"В указанном периоде нет операций для файла {PATH_OPERATIONS_FILE}")

        # Инфо по каждой карте
        cards = get_info_on_cards(filtered_df)

        # Топ-5 транзакций по сумме платежа
        top_transactions = get_top_transactions(filtered_df)

        # Курс валют
        currency_rates = get_currency_rates(PATH_USER_SETTINGS_FILE)

        # Стоимость акций из S&P500
        stock_prices = get_stock_prices(PATH_USER_SETTINGS_FILE)

        data = {
            "greeting": greeting,
            "cards": cards,
            "top_transactions": top_transactions,
            "currency_rates": currency_rates,
            "stock_prices": stock_prices,
        }

        json_data = json.dumps(data, ensure_ascii=False, indent=4)
        return json_data

    except FileNotFoundError as e:
        views_logger.error(f"Файл не найден: {e}")
        raise
    except ValueError as e:
        views_logger.error(f"Ошибка в параметрах даты: {e}")
        raise
    except Exception as e:
        views_logger.exception(f"Непредвиденная ошибка при формировании отчёта: {e}")
        raise
