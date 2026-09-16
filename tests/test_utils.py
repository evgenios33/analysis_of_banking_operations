from datetime import date, datetime
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from src.utils import (
    filter_df_by_period,
    get_a_date_range,
    get_currency_rates,
    get_greeting,
    get_info_on_cards,
    get_stock_prices,
    get_top_transactions,
    load_settings,
)


def test_get_greeting_morning() -> None:
    with patch("src.utils.datetime") as mock_datetime:
        mock_datetime.now.return_value = datetime(2026, 9, 10, 9, 0)
        assert get_greeting() == "Доброе утро"


def test_get_greeting_afternoon() -> None:
    with patch("src.utils.datetime") as mock_datetime:
        mock_datetime.now.return_value = datetime(2026, 9, 10, 14, 0)
        assert get_greeting() == "Добрый день"


def test_get_greeting_evening() -> None:
    with patch("src.utils.datetime") as mock_datetime:
        mock_datetime.now.return_value = datetime(2026, 9, 10, 20, 0)
        assert get_greeting() == "Добрый вечер"


def test_get_greeting_night() -> None:
    with patch("src.utils.datetime") as mock_datetime:
        mock_datetime.now.return_value = datetime(2026, 9, 10, 3, 0)
        assert get_greeting() == "Доброй ночи"


def test_get_a_date_range_valid() -> None:
    user_date = "2026-09-10 10:30:00"
    start, end = get_a_date_range(user_date)
    assert start == datetime(2026, 9, 1, 0, 0, 0)
    assert end == datetime(2026, 9, 10, 10, 30, 0)


def test_get_a_date_range_empty() -> None:
    with pytest.raises(ValueError, match='"user_date" не может быть пустой'):
        get_a_date_range("")


def test_get_a_date_range_invalid_format() -> None:
    with pytest.raises(ValueError, match="Неверный формат даты"):
        get_a_date_range("10-09-2026")


@patch("os.path.isfile", return_value=True)
@patch("src.utils.pd.read_excel")
def test_filter_df_by_period_success(mock_read_excel: MagicMock, _mock_isfile: MagicMock) -> None:
    df = pd.DataFrame(
        {
            "Дата операции": [
                "01.08.2026 10:00:00",
                "10.08.2026 12:00:00",
                "31.08.2026 18:00:00",
            ],
            "Сумма операции": [-100, -200, -300],
        }
    )
    mock_read_excel.return_value = df

    start = datetime(2026, 8, 1)
    end = datetime(2026, 8, 15)

    result = filter_df_by_period("./dummy.xlsx", start, end)

    assert mock_read_excel.called
    assert len(result) == 2

    dates = result["Дата операции"].dt.date.tolist()
    expected = [date(2026, 8, 1), date(2026, 8, 10)]
    assert dates == expected


@patch("os.path.isfile", return_value=False)
def test_filter_df_by_period_file_not_found(_mock_isfile: MagicMock) -> None:
    with pytest.raises(FileNotFoundError, match="Файл не найден"):
        filter_df_by_period("missing.xlsx", datetime(2026, 8, 1), datetime(2026, 8, 31))


@patch("os.path.isfile", return_value=True)
@patch("src.utils.pd.read_excel", return_value=pd.DataFrame({"OtherCol": [1, 2]}))
def test_filter_df_by_period_missing_date_column(_mock_read_excel: MagicMock, _mock_isfile: MagicMock) -> None:
    with pytest.raises(ValueError, match='отсутствует колонка "Дата операции"'):
        filter_df_by_period("dummy.xlsx", datetime(2026, 8, 1), datetime(2026, 8, 31))


def test_get_info_on_cards_normal() -> None:
    df = pd.DataFrame(
        {
            "Сумма операции": [-100.0, -250.5, 50.0],
            "Номер карты": ["*1234", "*5678", "*4321"],
        }
    )
    result = get_info_on_cards(df)
    assert isinstance(result, list)
    assert len(result) == 2

    total = sum(r["total_spent"] for r in result)
    expected_total = 100 + 250.5
    assert abs(total - expected_total) < 0.01


def test_get_info_on_cards_empty() -> None:
    df = pd.DataFrame({"Сумма операции": [], "Номер карты": []})
    assert get_info_on_cards(df) == []


def test_get_info_on_cards_missing_columns() -> None:
    df = pd.DataFrame({"OnlyCol": [1]})
    with pytest.raises(ValueError, match="отсутствуют колонки"):
        get_info_on_cards(df)


def test_get_top_transactions_top_n() -> None:
    df = pd.DataFrame(
        {
            "Дата платежа": ["01.01.2026"] * 6,
            "Сумма операции": [-10, -50, -20, -100, -30, -40],
            "Категория": ["A"] * 6,
            "Описание": ["X"] * 6,
        }
    )
    top = get_top_transactions(df, operation_count=3)
    assert len(top) == 3
    amounts = [t["amount"] for t in top]
    assert amounts == [100, 50, 40]


def test_get_top_transactions_missing_columns() -> None:
    df = pd.DataFrame({"OnlyCol": [1]})
    with pytest.raises(ValueError, match="отсутствуют колонки"):
        get_top_transactions(df)


@patch("builtins.open", new_callable=MagicMock)
@patch("json.load", return_value={"user_currencies": ["USD", "EUR"], "user_stocks": ["AAPL"]})
def test_load_settings_success(_mock_json_load: MagicMock, mock_open: MagicMock) -> None:
    data = load_settings("dummy.json")
    assert data["user_currencies"] == ["USD", "EUR"]
    mock_open.assert_called_once()


@patch("src.utils.load_settings")
@patch("requests.get")
def test_get_currency_rates_success(mock_get: MagicMock, mock_load_settings: MagicMock) -> None:
    mock_load_settings.return_value = {"user_currencies": ["USD"]}
    mock_get.return_value.json.return_value = {"data": {"RUB": 92.567}}
    mock_get.return_value.raise_for_status.return_value = None

    result = get_currency_rates("dummy.json")
    assert result == [{"currency": "USD", "rate": 92.57}]


@patch("src.utils.load_settings")
@patch("requests.get")
def test_get_currency_rates_api_error(mock_get: MagicMock, mock_load_settings: MagicMock) -> None:
    mock_load_settings.return_value = {"user_currencies": ["USD"]}
    mock_get.side_effect = Exception("Ошибка при выполнении запроса к API.")

    with pytest.raises(Exception, match="Ошибка при выполнении запроса к API."):
        get_currency_rates("dummy.json")


@patch("src.utils.load_settings")
@patch("requests.get")
def test_get_stock_prices_success(mock_get: MagicMock, mock_load_settings: MagicMock) -> None:
    mock_load_settings.return_value = {"user_stocks": ["AAPL"]}
    mock_get.return_value.json.return_value = {"c": 185.75}
    mock_get.return_value.raise_for_status.return_value = None

    result = get_stock_prices("dummy.json")
    assert result == [{"stock": "AAPL", "price": 185.75}]


@patch("src.utils.load_settings")
@patch("requests.get")
def test_get_stock_prices_api_error(mock_get: MagicMock, mock_load_settings: MagicMock) -> None:
    mock_load_settings.return_value = {"user_stocks": ["AAPL"]}
    mock_get.side_effect = Exception("Ошибка при выполнении запроса к API.")

    with pytest.raises(Exception, match="Ошибка при выполнении запроса к API."):
        get_stock_prices("dummy.json")
