"""
製造ダッシュボード用ヘルパー関数
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Union
from pathlib import Path
import json


def format_datetime(dt: Union[datetime, str], format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
    """日時をフォーマット"""
    if isinstance(dt, str):
        try:
            dt = pd.to_datetime(dt)
        except:
            return dt
    
    if pd.isna(dt):
        return ""
    
    return dt.strftime(format_str)


def format_number(value: Union[int, float], decimal_places: int = 2) -> str:
    """数値をフォーマット"""
    if pd.isna(value):
        return ""
    
    try:
        if decimal_places == 0:
            return f"{int(value):,}"
        else:
            return f"{float(value):,.{decimal_places}f}"
    except:
        return str(value)


def calculate_percentage(numerator: Union[int, float], 
                        denominator: Union[int, float]) -> float:
    """パーセンテージを計算"""
    if pd.isna(numerator) or pd.isna(denominator) or denominator == 0:
        return 0.0
    
    return (numerator / denominator) * 100


def get_date_range(days: int = 7, end_date: Optional[datetime] = None) -> tuple:
    """日付範囲を取得"""
    if end_date is None:
        end_date = datetime.now()
    
    start_date = end_date - timedelta(days=days)
    return start_date, end_date


def validate_file_path(file_path: Union[str, Path]) -> bool:
    """ファイルパスの妥当性をチェック"""
    try:
        path = Path(file_path)
        return path.exists() and path.is_file()
    except:
        return False


def safe_divide(numerator: Union[int, float], 
                denominator: Union[int, float], 
                default: float = 0.0) -> float:
    """安全な除算"""
    try:
        if denominator == 0:
            return default
        return numerator / denominator
    except:
        return default


def clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """DataFrameをクリーニング"""
    if df.empty:
        return df
    
    # 重複行を削除
    df = df.drop_duplicates()
    
    # 空白文字列をNaNに変換
    df = df.replace(r'^\s*$', np.nan, regex=True)
    
    # カラム名の空白を削除
    df.columns = df.columns.str.strip()
    
    return df


def get_file_info(file_path: Union[str, Path]) -> Dict[str, Any]:
    """ファイル情報を取得"""
    try:
        path = Path(file_path)
        if not path.exists():
            return {}
        
        stat = path.stat()
        return {
            "name": path.name,
            "size": stat.st_size,
            "modified": datetime.fromtimestamp(stat.st_mtime),
            "extension": path.suffix.lower(),
            "is_file": path.is_file(),
            "absolute_path": str(path.absolute())
        }
    except:
        return {}


def create_summary_stats(df: pd.DataFrame, 
                        numeric_columns: Optional[List[str]] = None) -> Dict[str, Any]:
    """サマリー統計を作成"""
    if df.empty:
        return {}
    
    stats = {
        "total_rows": len(df),
        "total_columns": len(df.columns),
        "memory_usage": df.memory_usage(deep=True).sum(),
        "null_counts": df.isnull().sum().to_dict()
    }
    
    # 数値列の統計
    if numeric_columns is None:
        numeric_columns = df.select_dtypes(include=[np.number]).columns.tolist()
    
    if numeric_columns:
        numeric_stats = {}
        for col in numeric_columns:
            if col in df.columns:
                numeric_stats[col] = {
                    "mean": df[col].mean(),
                    "median": df[col].median(),
                    "std": df[col].std(),
                    "min": df[col].min(),
                    "max": df[col].max(),
                    "count": df[col].count()
                }
        stats["numeric_stats"] = numeric_stats
    
    return stats


def export_to_json(data: Dict[str, Any], file_path: Union[str, Path]) -> bool:
    """データをJSONファイルにエクスポート"""
    try:
        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2, default=str)
        
        return True
    except:
        return False


def load_from_json(file_path: Union[str, Path]) -> Dict[str, Any]:
    """JSONファイルからデータを読み込み"""
    try:
        path = Path(file_path)
        if not path.exists():
            return {}
        
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return {}


def generate_report_filename(report_type: str, 
                           timestamp: Optional[datetime] = None,
                           extension: str = "xlsx") -> str:
    """レポートファイル名を生成"""
    if timestamp is None:
        timestamp = datetime.now()
    
    timestamp_str = timestamp.strftime("%Y%m%d_%H%M%S")
    return f"{report_type}_{timestamp_str}.{extension}"


def chunk_dataframe(df: pd.DataFrame, chunk_size: int = 1000) -> List[pd.DataFrame]:
    """DataFrameをチャンクに分割"""
    if df.empty:
        return []
    
    chunks = []
    for i in range(0, len(df), chunk_size):
        chunk = df.iloc[i:i + chunk_size]
        chunks.append(chunk)
    
    return chunks


def merge_dataframes(dataframes: List[pd.DataFrame], 
                    how: str = "outer") -> pd.DataFrame:
    """複数のDataFrameをマージ"""
    if not dataframes:
        return pd.DataFrame()
    
    if len(dataframes) == 1:
        return dataframes[0]
    
    result = dataframes[0]
    for df in dataframes[1:]:
        if not df.empty:
            # 共通のカラムを見つけてマージ
            common_columns = list(set(result.columns) & set(df.columns))
            if common_columns:
                result = pd.merge(result, df, on=common_columns, how=how)
            else:
                # 共通カラムがない場合は連結
                result = pd.concat([result, df], ignore_index=True, sort=False)
    
    return result