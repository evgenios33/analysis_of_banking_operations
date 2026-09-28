import logging
from pathlib import Path
from typing import Optional

import pandas as pd

from .decorators import save_to_excel

logger = logging.getLogger(__name__)


@save_to_excel(Path("report"))
def spending_by_category(transactions: pd.DataFrame, category: str, date: Optional[str] = None) -> pd.DataFrame:
    """
    Функция принимает на вход: датафрейм с транзакциями, название категории, опциональную дату
    (если дата не передана, то берется текущая дата).
    Возвращает траты по заданной категории за последние три месяца (от переданной даты).
    """
    result_df = transactions.copy()

    required_cols = ["Категория", "Дата платежа"]
    missing_cols = [col for col in required_cols if col not in result_df.columns]
    if missing_cols:
        logger.error(f"Отсутствуют обязательные колонки: {missing_cols}")
        raise KeyError(f"Отсутствуют обязательные колонки: {missing_cols}")

    result_df["Дата платежа"] = pd.to_datetime(result_df["Дата платежа"], format="%d.%m.%Y", errors="coerce")

    if date is None:
        target_date = pd.Timestamp.now()
        logger.debug(f"Дата не передана, используется текущая дата: {target_date}")
    else:
        if not isinstance(date, pd.Timestamp):
            target_date = pd.to_datetime(date, dayfirst=True)

    start_date = target_date - pd.DateOffset(months=3)
    logger.debug(f'Диапазон дат: "{start_date}", "{target_date}"')

    mask_category = (
        result_df["Категория"].fillna("").astype(str).str.lower().str.contains(category.lower(), na=False, regex=False)
    )

    mask_date = (result_df["Дата платежа"] >= start_date) & (result_df["Дата платежа"] <= target_date)

    filtered_df = result_df[mask_category & mask_date]
    if not filtered_df.empty:
        filtered_df = filtered_df.sort_values(by="Дата платежа", ascending=False)

    logger.info(
        f'Отфильтровано по категории "{category}" и диапазону дат с "{start_date}" по "{target_date}": '
        f"{len(filtered_df)} из {len(result_df)} строк."
    )

    return filtered_df
