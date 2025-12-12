from __future__ import annotations

import pandas as pd

from eda_cli.core import (
    compute_quality_flags,
    correlation_matrix,
    flatten_summary_for_print,
    missing_table,
    summarize_dataset,
    top_categories,
)


def _sample_df() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "age": [10, 20, 30, None],
            "height": [140, 150, 160, 170],
            "city": ["A", "B", "A", None],
        }
    )


def test_summarize_dataset_basic():
    df = _sample_df()
    summary = summarize_dataset(df)

    assert summary.n_rows == 4
    assert summary.n_cols == 3
    assert any(c.name == "age" for c in summary.columns)
    assert any(c.name == "city" for c in summary.columns)

    summary_df = flatten_summary_for_print(summary)
    assert "name" in summary_df.columns
    assert "missing_share" in summary_df.columns


def test_missing_table_and_quality_flags():
    df = _sample_df()
    missing_df = missing_table(df)

    assert "missing_count" in missing_df.columns
    assert missing_df.loc["age", "missing_count"] == 1

    summary = summarize_dataset(df)
    flags = compute_quality_flags(summary, missing_df)
    assert 0.0 <= flags["quality_score"] <= 1.0


def test_correlation_and_top_categories():
    df = _sample_df()
    corr = correlation_matrix(df)
    # корреляция между age и height существует
    assert "age" in corr.columns or corr.empty is False

    top_cats = top_categories(df, max_columns=5, top_k=2)
    assert "city" in top_cats
    city_table = top_cats["city"]
    assert "value" in city_table.columns
    assert len(city_table) <= 2

#---

def test_compute_quality_flags_new_heuristics():
    """Тест новых эвристик качества данных."""
    # Тест 1: DataFrame с константной колонкой
    df_const = pd.DataFrame({
        "id": [1, 2, 3, 4],
        "constant_col": [5, 5, 5, 5],  # Константная колонка
        "normal_col": [1, 2, 3, 4],
    })
    
    summary_const = summarize_dataset(df_const)
    missing_df_const = missing_table(df_const)
    flags_const = compute_quality_flags(summary_const, missing_df_const)
    
    assert flags_const["has_constant_columns"] == True
    assert "constant_col" in flags_const["constant_columns"]
    assert len(flags_const["constant_columns"]) == 1
    
    # Тест 2: DataFrame с высокой кардинальностью (строковая колонка)
    # Создаем строковую колонку с 150 уникальными значениями
    df_high_card = pd.DataFrame({
        "string_id": [f"id_{i}" for i in range(150)],  # 150 уникальных строковых значений
        "category": ["A"] * 150,  # Низкая кардинальность
        "numeric_col": list(range(150)),  # Числовая колонка (не должна считаться)
    })
    
    summary_high_card = summarize_dataset(df_high_card)
    missing_df_high_card = missing_table(df_high_card)
    flags_high_card = compute_quality_flags(summary_high_card, missing_df_high_card)
    
    # string_id должен быть определен как колонка с высокой кардинальностью
    assert flags_high_card["has_high_cardinality_categoricals"] == True
    assert "string_id" in flags_high_card["high_cardinality_columns"]
    assert len(flags_high_card["high_cardinality_columns"]) == 1
    
    # Тест 3: DataFrame без проблем
    df_normal = pd.DataFrame({
        "id": [1, 2, 3],
        "value": [10.5, 20.3, 30.7],
        "category": ["A", "B", "C"],
    })
    
    summary_normal = summarize_dataset(df_normal)
    missing_df_normal = missing_table(df_normal)
    flags_normal = compute_quality_flags(summary_normal, missing_df_normal)
    
    assert flags_normal["has_constant_columns"] == False
    assert flags_normal["has_high_cardinality_categoricals"] == False
    assert len(flags_normal["constant_columns"]) == 0
    assert len(flags_normal["high_cardinality_columns"]) == 0


def test_top_categories_with_custom_k():
    """Тест функции top_categories с пользовательским top_k."""
    df = pd.DataFrame({
        "category": ["A", "B", "C", "A", "B", "D", "E", "F", "G", "H"],
        "value": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
    })
    
    # Тест с top_k=3
    top_cats_3 = top_categories(df, top_k=3)
    assert "category" in top_cats_3
    assert len(top_cats_3["category"]) == 3
    
    # Тест с top_k=5
    top_cats_5 = top_categories(df, top_k=5)
    assert len(top_cats_5["category"]) == 5
    
    #---