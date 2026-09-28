import pandas as pd
from pandas.core.interchange.dataframe_protocol import DataFrame

from src.reports import spending_by_category


def test_spending_by_category_returns_dataframe(sample_transactions: DataFrame) -> None:
    """Функция должна вернуть DataFrame."""
    result = spending_by_category(sample_transactions, "Продукты")
    assert isinstance(result, pd.DataFrame)


def test_spending_by_category_filters_category(sample_transactions: DataFrame) -> None:
    """Фильтрация по категории должна работать (регистронезависимо, частичное совпадение)."""
    result = spending_by_category(sample_transactions, "продукт")
    assert all(result["Категория"].str.lower().str.contains("продукт", na=False))
    assert set(result["Категория"].unique()) == {"Продукты"}


def test_spending_by_category_date_range_90_days(sample_transactions: DataFrame) -> None:
    """Должны остаться только транзакции за последние 3 месяца от target_date."""
    date = "25.09.2026"
    result = spending_by_category(sample_transactions, "Продукты", date)

    start_date = pd.Timestamp(date) - pd.DateOffset(months=3)

    dates = result["Дата платежа"]
    assert ((dates >= start_date) & (dates <= pd.Timestamp(date))).all()


def test_spending_by_category_sort_descending(sample_transactions: DataFrame) -> None:
    """Результат должен быть отсортирован по дате платежа по убыванию."""
    result = spending_by_category(sample_transactions, "Продукты")
    dates = result["Дата платежа"].tolist()
    assert dates == sorted(dates, reverse=True)


def test_spending_by_category_empty_result(sample_transactions: DataFrame) -> None:
    """Если совпадений нет — должен вернуться пустой DataFrame."""
    result = spending_by_category(sample_transactions, "Электроника")
    assert result.empty


def test_spending_by_category_handles_invalid_dates(sample_transactions: DataFrame) -> None:
    """Строки с невалидными датами должны исключаться из результата."""
    data = sample_transactions.copy()
    data.loc[0, "Дата платежа"] = "не_дата"
    result = spending_by_category(data, "Продукты")
    assert not result["Дата платежа"].isna().any()
