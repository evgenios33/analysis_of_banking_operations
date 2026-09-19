import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Hashable

import pandas as pd
import requests
from dotenv import load_dotenv
from pandas import DataFrame
from requests import RequestException

load_dotenv()

API_KEY_FREECURRENCY = os.getenv("API_KEY_FREECURRENCY")
API_KEY_FINNHUB = os.getenv("API_KEY_FINNHUB")

FREECURRENCY_URL = "https://api.freecurrencyapi.com/v1/latest"
FINNHUB_URL = "https://finnhub.io/api/v1/quote"


def get_greeting() -> str:
    """
    Возвращает "Доброе утро", "Добрый день", "Добрый вечер" или "Доброй ночи" в зависимости от времени суток.
    """
    current_time = datetime.now().hour
    if 6 <= current_time < 12:
        return "Доброе утро"
    elif 12 <= current_time < 18:
        return "Добрый день"
    elif 18 <= current_time < 23:
        return "Добрый вечер"
    else:
        return "Доброй ночи"


def get_a_date_range(user_date: str, date_fmt: str = "%Y-%m-%d %H:%M:%S") -> tuple[datetime, datetime]:
    """
    Принимает на вход дату и формат даты (YYYY-MM-DD HH:MM:SS по умолчанию).
    Возвращает диапазон с начала месяца до указанной даты (включительно) в виде кортежа.
    """
    if not user_date or not (user_date := user_date.strip()):
        raise ValueError('"user_date" не может быть пустой строкой.')

    try:
        end_date = datetime.strptime(user_date, date_fmt)
    except ValueError as e:
        raise ValueError(f'Неверный формат даты "{user_date}". Ожидался формат "{date_fmt}".') from e

    start_date = end_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    return start_date, end_date


def filter_df_by_period(file_path: Path, start_date: datetime, end_date: datetime) -> DataFrame:
    """
    Принимает на вход путь к Excel-файлу и диапазон дат из функции get_a_date_range(),
    и возвращает отфильтрованный датафрейм с операциями в заданном диапазоне.
    """
    path = Path(file_path)

    if not path.is_file():
        raise FileNotFoundError(f"Файл не найден: {path.resolve()}")

    try:
        df = pd.read_excel(path, engine="openpyxl")
    except Exception as e:
        raise IOError(f"Не удалось прочитать Excel-файл: {e}") from e

    if "Дата операции" not in df.columns:
        raise ValueError(f'В файле отсутствует колонка "Дата операции". Доступные колонки: {list(df.columns)}')

    df["Дата операции"] = pd.to_datetime(df["Дата операции"], dayfirst=True, errors="coerce")

    mask = (df["Дата операции"] >= start_date) & (df["Дата операции"] <= end_date)
    filtered_df = df[mask].copy()

    return filtered_df


def get_info_on_cards(filtered_df: DataFrame) -> list[dict[Hashable, Any]]:
    """
    Принимает на вход отфильтрованный датафрейм из функции filter_df_by_period()
    и возвращает список словарей с данными по картам в формате:
    [
        {
            "last_digits": "4321", # последние 4 цифры номера карты
            "total_spent": 1255.90, # сумма расходов за период
            "cashback": 12.56 # сумма кэшбэка за период (1 рубль на каждые 100 рублей)
        }
    ]
    Если данные отсутствуют, возвращается пустой список.
    """
    required_cols = {"Сумма операции", "Номер карты"}
    missing = required_cols - set(filtered_df.columns)
    if missing:
        raise ValueError(f"В DataFrame отсутствуют колонки: {missing}")

    expenses_df = filtered_df[filtered_df["Сумма операции"] < 0].copy()
    expenses_df = expenses_df.rename(columns={"Сумма операции": "total_spent"}).dropna(subset=["Номер карты"])

    if expenses_df.empty:
        return []

    expenses_df["last_digits"] = expenses_df["Номер карты"].astype(str).str[-4:]

    agg_df = expenses_df.groupby("last_digits", as_index=False).agg(total_spent=("total_spent", "sum"))

    agg_df["total_spent"] = agg_df["total_spent"].abs()
    agg_df["cashback"] = (agg_df["total_spent"] / 100).round(2)

    info_on_cards_result = agg_df.to_dict(orient="records")
    return info_on_cards_result


def get_top_transactions(filtered_df: DataFrame, operation_count: int = 5) -> list[dict[Hashable, Any]]:
    """
    Принимает на вход отфильтрованный датафрейм из функции filter_df_by_period()
    и необязательный параметр количества операций operation_count.
    Возвращает Топ-5 (по умолчанию) операций по сумме расходов.
    """
    required_cols = {"Дата платежа", "Сумма операции", "Категория", "Описание"}
    missing = required_cols - set(filtered_df.columns)
    if missing:
        raise ValueError(f"В DataFrame отсутствуют колонки: {missing}")

    renamed_df = filtered_df.rename(
        columns={
            "Дата платежа": "date",
            "Сумма операции": "amount",
            "Категория": "category",
            "Описание": "description",
        }
    )
    renamed_df["amount"] = renamed_df["amount"].abs()

    sorted_by_amount_df = (
        renamed_df[["date", "amount", "category", "description"]]
        .sort_values(by="amount", ascending=False)
        .head(operation_count)
    ).copy()

    top_transactions_result = sorted_by_amount_df.to_dict(orient="records")
    return top_transactions_result


def load_settings(file_path: Path) -> Any:
    """
    Принимает на вход путь к файлу с пользовательскими настройками,
    считывает содержимое файла user_settings.json и возвращает данные в формате Python.
    """
    path = Path(file_path)
    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)


def get_currency_rates(file_path: Path) -> list[dict[str, float]]:
    """
    Принимает путь к файлу с пользовательскими настройками и
    возвращает актуальные курсы валют относительно RUB для списка валют из файла настроек.
    """
    user_settings_data = load_settings(file_path)
    user_currencies = user_settings_data.get("user_currencies")

    if not isinstance(user_currencies, list):
        raise ValueError('В файле настроек "user_currencies" должен быть списком.')

    currency_rate_list = []
    for currency in user_currencies:
        if not isinstance(currency, str):
            continue

        url = FREECURRENCY_URL
        params = {"base_currency": currency, "currencies": "RUB"}
        headers = {"apikey": f"{API_KEY_FREECURRENCY}"}

        try:
            response = requests.get(url, params=params, headers=headers, timeout=10)
            response.raise_for_status()
            result = response.json()
            currency_rate_dicts = {
                "currency": currency,
                "rate": round(result["data"]["RUB"], 2),
            }
            currency_rate_list.append(currency_rate_dicts)

        except requests.exceptions.RequestException:
            raise RequestException("Ошибка при выполнении запроса к API.")

    return currency_rate_list


def get_stock_prices(file_path: Path) -> list[dict[str, float]]:
    """
    Принимает путь к файлу с пользовательскими настройками и
    возвращает текущие цены акций для списка тикеров из файла настроек.
    """
    user_settings_data = load_settings(file_path)
    user_stocks = user_settings_data.get("user_stocks")

    if not isinstance(user_stocks, list):
        raise ValueError('В файле настроек "user_stocks" должен быть списком.')

    stock_prices_list = []
    for stock in user_stocks:
        if not isinstance(stock, str):
            continue

        url = FINNHUB_URL
        params = {"symbol": stock, "token": API_KEY_FINNHUB}

        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            result = response.json()
            stock_prices_dicts = {"stock": stock, "price": result["c"]}
            stock_prices_list.append(stock_prices_dicts)

        except requests.exceptions.RequestException:
            raise RequestException("Ошибка при выполнении запроса к API.")

    return stock_prices_list
