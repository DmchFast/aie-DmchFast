from __future__ import annotations

from pathlib import Path
from typing import Dict, Iterable, List, Union

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

PathLike = Union[str, Path]


def _ensure_dir(path: PathLike) -> Path:
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    return p


def plot_histograms_per_column(
    df: pd.DataFrame,
    out_dir: PathLike,
    max_columns: int = 6,
    bins: int = 20,
) -> List[Path]:
    """
    Для числовых колонок строит по отдельной гистограмме.
    Возвращает список путей к PNG.
    """
    out_dir = _ensure_dir(out_dir)
    numeric_df = df.select_dtypes(include="number")

    paths: List[Path] = []
    for i, name in enumerate(numeric_df.columns[:max_columns]):
        s = numeric_df[name].dropna()
        if s.empty:
            continue

        fig, ax = plt.subplots()
        ax.hist(s.values, bins=bins)
        ax.set_title(f"Histogram of {name}")
        ax.set_xlabel(name)
        ax.set_ylabel("Count")
        fig.tight_layout()

        out_path = out_dir / f"hist_{i+1}_{name}.png"
        fig.savefig(out_path)
        plt.close(fig)

        paths.append(out_path)

    return paths


def plot_missing_matrix(df: pd.DataFrame, out_path: PathLike) -> Path:
    """
    Простая визуализация пропусков: где True=пропуск, False=значение.
    """
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    if df.empty:
        # Рисуем пустой график
        fig, ax = plt.subplots()
        ax.text(0.5, 0.5, "Empty dataset", ha="center", va="center")
        ax.axis("off")
    else:
        mask = df.isna().values
        fig, ax = plt.subplots(figsize=(min(12, df.shape[1] * 0.4), 4))
        ax.imshow(mask, aspect="auto", interpolation="none")
        ax.set_xlabel("Columns")
        ax.set_ylabel("Rows")
        ax.set_title("Missing values matrix")
        ax.set_xticks(range(df.shape[1]))
        ax.set_xticklabels(df.columns, rotation=90, fontsize=8)
        ax.set_yticks([])

    fig.tight_layout()
    fig.savefig(out_path)
    plt.close(fig)
    return out_path


def plot_correlation_heatmap(df: pd.DataFrame, out_path: PathLike) -> Path:
    """
    Тепловая карта корреляции числовых признаков.
    """
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    numeric_df = df.select_dtypes(include="number")
    if numeric_df.shape[1] < 2:
        fig, ax = plt.subplots()
        ax.text(0.5, 0.5, "Not enough numeric columns for correlation", ha="center", va="center")
        ax.axis("off")
    else:
        corr = numeric_df.corr(numeric_only=True)
        fig, ax = plt.subplots(figsize=(min(10, corr.shape[1]), min(8, corr.shape[0])))
        im = ax.imshow(corr.values, vmin=-1, vmax=1, cmap="coolwarm", aspect="auto")
        ax.set_xticks(range(corr.shape[1]))
        ax.set_xticklabels(corr.columns, rotation=90, fontsize=8)
        ax.set_yticks(range(corr.shape[0]))
        ax.set_yticklabels(corr.index, fontsize=8)
        ax.set_title("Correlation heatmap")
        fig.colorbar(im, ax=ax, label="Pearson r")

    fig.tight_layout()
    fig.savefig(out_path)
    plt.close(fig)
    return out_path


def save_top_categories_tables(
    top_cats: Dict[str, pd.DataFrame],
    out_dir: PathLike,
) -> List[Path]:
    """
    Сохраняет top-k категорий по колонкам в отдельные CSV.
    """
    out_dir = _ensure_dir(out_dir)
    paths: List[Path] = []
    for name, table in top_cats.items():
        out_path = out_dir / f"top_values_{name}.csv"
        table.to_csv(out_path, index=False)
        paths.append(out_path)
    return paths


def plot_categorical_bars(
    df: pd.DataFrame,
    out_dir: PathLike,
    max_columns: int = 5,
    top_n: int = 10,
) -> List[Path]:
    """
    Строит bar-chart по количеству объектов в каждой категории
    для категориальных/строковых колонок.
    
    Возвращает список путей к PNG.
    """
    out_dir = _ensure_dir(out_dir)
    
    # Находим категориальные колонки
    categorical_cols = []
    for name in df.columns:
        s = df[name]
        if pd.api.types.is_object_dtype(s) or pd.api.types.is_categorical_dtype(s):
            categorical_cols.append(name)
    
    paths: List[Path] = []
    
    for i, name in enumerate(categorical_cols[:max_columns]):
        s = df[name].dropna()
        if s.empty:
            continue
        
        # Считаем топ-N категорий
        value_counts = s.value_counts().head(top_n)
        
        if len(value_counts) == 0:
            continue
        
        fig, ax = plt.subplots(figsize=(max(8, len(value_counts) * 0.6), 6))
        
        # Создаем bar chart
        bars = ax.bar(range(len(value_counts)), value_counts.values)
        ax.set_xlabel(name)
        ax.set_ylabel("Количество")
        ax.set_title(f"Распределение по '{name}' (топ-{len(value_counts)})")
        
        # Добавляем значения на бары
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                   f'{int(height)}', ha='center', va='bottom', fontsize=9)
        
        # Настраиваем подписи на оси X
        ax.set_xticks(range(len(value_counts)))
        ax.set_xticklabels(value_counts.index, rotation=45, ha='right', fontsize=9)
        
        # Добавляем сетку
        ax.grid(True, axis='y', alpha=0.3)
        
        fig.tight_layout()
        
        # Сохраняем график
        out_path = out_dir / f"categorical_{i+1}_{name}.png"
        fig.savefig(out_path, dpi=100, bbox_inches='tight')
        plt.close(fig)
        
        paths.append(out_path)
    
    return paths


def plot_numeric_boxplots(
    df: pd.DataFrame,
    out_dir: PathLike,
    max_columns: int = 6,
) -> List[Path]:
    """
    Строит boxplot для числовых колонок.
    
    Возвращает список путей к PNG.
    """
    out_dir = _ensure_dir(out_dir)
    
    # Находим числовые колонки
    numeric_cols = df.select_dtypes(include="number").columns.tolist()
    
    if not numeric_cols:
        return []
    
    paths: List[Path] = []
    
    # Ограничиваем количество колонок
    numeric_cols = numeric_cols[:max_columns]
    
    # Создаем один график с несколькими boxplot
    fig, ax = plt.subplots(figsize=(max(10, len(numeric_cols) * 2), 8))
    
    # Подготовка данных для boxplot
    data_to_plot = []
    labels = []
    
    for name in numeric_cols:
        s = df[name].dropna()
        if not s.empty:
            data_to_plot.append(s.values)
            labels.append(name)
    
    if not data_to_plot:
        plt.close(fig)
        return []
    
    # Создаем boxplot
    box = ax.boxplot(data_to_plot, labels=labels, patch_artist=True)
    
    # Настраиваем цвета
    colors = ['lightblue', 'lightgreen', 'lightcoral', 'lightyellow', 'lightpink', 'lightgray']
    for patch, color in zip(box['boxes'], colors[:len(data_to_plot)]):
        patch.set_facecolor(color)
    
    ax.set_title(f"Boxplot числовых признаков ({len(labels)} колонок)")
    ax.set_ylabel("Значения")
    ax.set_xlabel("Признаки")
    ax.grid(True, axis='y', alpha=0.3)
    
    # Поворачиваем подписи для лучшей читаемости
    ax.set_xticklabels(labels, rotation=45, ha='right', fontsize=10)
    
    fig.tight_layout()
    
    # Сохраняем график
    out_path = out_dir / f"boxplot_numeric.png"
    fig.savefig(out_path, dpi=100, bbox_inches='tight')
    plt.close(fig)
    
    paths.append(out_path)
    
    return paths