import json
from pathlib import Path
from unittest.mock import patch

import pandas as pd
import pytest
from pandas.core.interchange.dataframe_protocol import DataFrame

from src.services import (
    filter_by_substring,
    main_services,
    read_data_from_xlsx,
)
from src.utils import filter_df_by_period


def test_filter_find_in_description(sample_df: DataFrame) -> None:
    result = filter_by_substring(sample_df, "Магнит")
    assert len(result) == 1
    assert result.iloc[0]["Описание"] == "Магнит"


def test_filter_find_in_category(sample_df: DataFrame) -> None:
    result = filter_by_substring(sample_df, "Супермаркеты")
    assert len(result) == 1
    assert result.iloc[0]["Категория"] == "Супермаркеты"


def test_filter_case_insensitive(sample_df: DataFrame) -> None:
    result = filter_by_substring(sample_df, "ситидрайв")
    assert len(result) == 1


def test_filter_no_match(sample_df: DataFrame) -> None:
    result = filter_by_substring(sample_df, "Рандом")
    assert len(result) == 0
    assert isinstance(result, pd.DataFrame)


def test_filter_empty_substring(sample_df: DataFrame) -> None:
    # Пустая подстрока после re.escape — пустой паттерн, matches всё
    result = filter_by_substring(sample_df, "")
    assert len(result) == len(sample_df)


def test_filter_missing_column_raises() -> None:
    df = pd.DataFrame({"Название": ["test"], "Тип": ["ops"]})
    with pytest.raises(KeyError):
        filter_by_substring(df, "test")


def test_read_success(tmp_path: Path, sample_df: DataFrame) -> None:
    fake_file = tmp_path / "fake.xlsx"
    fake_file.write_text("dummy")

    with patch("pandas.read_excel", return_value=sample_df) as mock_read:
        result = filter_df_by_period(fake_file, pd.Timestamp("2026-08-06"), pd.Timestamp("2026-08-17"))

    assert not result.empty
    assert len(result) == 2
    mock_read.assert_called_once()


def test_read_file_not_found() -> None:
    with patch("pathlib.Path.is_file", return_value=False):
        with pytest.raises(FileNotFoundError):
            read_data_from_xlsx(Path("nonexistent.xlsx"))


def test_read_failure(tmp_path: Path) -> None:
    fake_file = tmp_path / "fake.xlsx"
    fake_file.write_text("dummy")

    with patch("pandas.read_excel", side_effect=Exception("boom")):
        with pytest.raises(IOError, match="Не удалось прочитать Excel-файл"):
            filter_df_by_period(fake_file, pd.Timestamp("2026-08-01"), pd.Timestamp("2026-08-31"))


def test_main_returns_valid_json(sample_df: DataFrame) -> None:
    with patch("src.services.read_data_from_xlsx", return_value=sample_df):
        result = main_services("Магнит")

    parsed = json.loads(result)
    assert isinstance(parsed, list)
    assert len(parsed) == 1
    assert all("Описание" in item for item in parsed)


def test_main_no_results_returns_empty_list_json(sample_df: DataFrame) -> None:
    with patch("src.services.read_data_from_xlsx", return_value=sample_df):
        result = main_services("Несуществующее")

    parsed = json.loads(result)
    assert parsed == []
