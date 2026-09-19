import re
from pathlib import Path

import pandas as pd

from .file_paths import PATH_OPERATIONS_FILE


def main_services(substring: str) -> str:
    """
    Принимает подстроку для поиска и возвращает JSON-ответ со всеми транзакциями,
    содержащими запрос в описании или категории.
    """
    df = read_data_from_xlsx(PATH_OPERATIONS_FILE)

    filter_df = filter_by_substring(df, substring)

    result_json = filter_df.to_json(orient="records", force_ascii=False, indent=4)
    return result_json


def read_data_from_xlsx(file_path: Path) -> pd.DataFrame:
    """
    Принимает путь к Excel-файлу, читает и возвращает датафрейм с данными.
    """
    path = Path(file_path)

    if not path.is_file():
        raise FileNotFoundError(f"Файл не найден: {path.resolve()}")

    try:
        df = pd.read_excel(path, engine="openpyxl")
    except Exception as e:
        raise IOError(f"Не удалось прочитать Excel-файл: {e}") from e

    return df


def filter_by_substring(df: pd.DataFrame, substring: str) -> pd.DataFrame:
    """
    Принимает датафрейм с операциями и подстроку для поиска.
    Возвращает отфильтрованный датафрейм только с теми транзакциями,
    у которых в столбцах "Описание" или "Категория" встречается переданная подстрока.
    """
    pattern = re.escape(substring)

    mask_descriptions = df["Описание"].fillna("").astype(str).str.contains(pattern, na=False, case=False, regex=False)
    mask_categories = df["Категория"].fillna("").astype(str).str.contains(pattern, na=False, case=False, regex=False)

    combined_mask = mask_descriptions | mask_categories
    return df[combined_mask].copy()
