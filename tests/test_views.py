import json
from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

from src.views import main_info


@patch("src.views.get_stock_prices", return_value=[{"stock": "AAPL", "price": 185.75}])
@patch("src.views.get_currency_rates", return_value=[{"currency": "USD", "rate": 92.5}])
@patch("src.views.get_top_transactions", return_value=[])
@patch("src.views.get_info_on_cards", return_value=[])
@patch("src.views.filter_df_by_period")
@patch("src.views.get_a_date_range")
@patch("src.views.get_greeting", return_value="Добрый день")
def test_main_info_success(
    _mock_greeting: MagicMock,
    mock_date_range: MagicMock,
    mock_filter: MagicMock,
    _mock_cards: MagicMock,
    _mock_top: MagicMock,
    _mock_rates: MagicMock,
    _mock_stocks: MagicMock,
) -> None:
    mock_date_range.return_value = (datetime(2026, 8, 1), datetime(2026, 8, 17))
    mock_filter.return_value = MagicMock()
    mock_filter.return_value.empty = False

    result = main_info("2026-08-17 10:30:00")
    data = json.loads(result)

    assert data["greeting"] == "Добрый день"
    assert data["cards"] == []
    assert data["top_transactions"] == []
    assert data["currency_rates"] == [{"currency": "USD", "rate": 92.5}]
    assert data["stock_prices"] == [{"stock": "AAPL", "price": 185.75}]


@patch("src.views.get_stock_prices", return_value=[])
@patch("src.views.get_currency_rates", return_value=[])
@patch("src.views.get_top_transactions", return_value=[])
@patch("src.views.get_info_on_cards", return_value=[])
@patch("src.views.filter_df_by_period")
@patch("src.views.get_a_date_range")
@patch("src.views.get_greeting", return_value="Доброе утро")
def test_main_info_empty_df(
    _mock_greeting: MagicMock,
    mock_date_range: MagicMock,
    mock_filter: MagicMock,
    _mock_cards: MagicMock,
    _mock_top: MagicMock,
    _mock_rates: MagicMock,
    _mock_stocks: MagicMock,
) -> None:
    mock_date_range.return_value = (datetime(2026, 8, 1), datetime(2026, 8, 17))
    mock_filter.return_value = MagicMock()
    mock_filter.return_value.empty = True

    result = main_info("2026-08-17 10:30:00")
    data = json.loads(result)

    assert data["greeting"] == "Доброе утро"
    assert data["cards"] == []
    assert data["top_transactions"] == []


@patch("src.views.filter_df_by_period", side_effect=FileNotFoundError("Файл не найден: ./data/operations.xlsx"))
@patch("src.views.get_a_date_range")
@patch("src.views.get_greeting", return_value="Добрый день")
def test_main_info_file_not_found(
    _mock_greeting: MagicMock, mock_date_range: MagicMock, _mock_filter: MagicMock
) -> None:
    mock_date_range.return_value = (datetime(2026, 8, 1), datetime(2026, 8, 17))

    with pytest.raises(FileNotFoundError, match="Файл не найден"):
        main_info("2026-08-17 10:30:00")


@patch("src.views.get_a_date_range", side_effect=ValueError("Неверный формат даты"))
@patch("src.views.get_greeting", return_value="Добрый день")
def test_main_info_invalid_date(_mock_greeting: MagicMock, _mock_date_range: MagicMock) -> None:
    with pytest.raises(ValueError, match="Неверный формат даты"):
        main_info("invalid-date")


@patch("src.views.get_stock_prices", side_effect=Exception("Ошибка при выполнении запроса к API."))
@patch("src.views.get_currency_rates", return_value=[])
@patch("src.views.get_top_transactions", return_value=[])
@patch("src.views.get_info_on_cards", return_value=[])
@patch("src.views.filter_df_by_period")
@patch("src.views.get_a_date_range")
@patch("src.views.get_greeting", return_value="Добрый день")
def test_main_info_api_error(
    _mock_greeting: MagicMock,
    mock_date_range: MagicMock,
    mock_filter: MagicMock,
    _mock_cards: MagicMock,
    _mock_top: MagicMock,
    _mock_rates: MagicMock,
    _mock_stocks: MagicMock,
) -> None:
    mock_date_range.return_value = (datetime(2026, 8, 1), datetime(2026, 8, 17))
    mock_filter.return_value = MagicMock()
    mock_filter.return_value.empty = False

    with pytest.raises(Exception, match="Ошибка при выполнении запроса к API."):
        main_info("2026-08-17 10:30:00")
