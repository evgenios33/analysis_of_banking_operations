import functools
import logging
from pathlib import Path
from typing import Callable, ParamSpec, TypeVar

import pandas as pd

logger = logging.getLogger(__name__)

P = ParamSpec("P")
R = TypeVar("R", bound=pd.DataFrame)


def save_to_excel(filename: str | Path) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """
    Декоратор принимает имя файла и записывает в данный файл результат, который возвращает функция, формирующая отчет.
    Формат файла - Excel.
    """

    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        @functools.wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            df = func(*args, **kwargs)

            path = Path(filename)
            if path.suffix == "":
                path = path.with_suffix(".xlsx")

            parent = path.parent
            if parent and not parent.exists():
                parent.mkdir(parents=True, exist_ok=True)
                logger.debug(f"Создана папка для отчётов: {parent}")

            sheet_name = func.__name__
            try:
                df.to_excel(
                    path,
                    index=False,
                    engine="openpyxl",
                    sheet_name=sheet_name,
                )
            except Exception as e:
                logger.error(f"Не удалось сохранить Excel-файл {path}: {e}")
                raise

            return df

        return wrapper

    return decorator
