"""
数据加载器 - 加载和管理历史数据

⭐ 重点理解：数据加载器的职责
- 从文件加载数据
- 数据格式转换
- 数据验证和清洗
- 按时间序列提供数据

💡 值得思考：
- 如何处理缺失数据？
- 如何处理复权价格？
- 如何支持实时数据流？
"""

import pandas as pd
from datetime import datetime
from typing import Dict, List, Optional, Iterator
from pathlib import Path

from ..core.events import MarketDataEvent


class DataLoader:
    """
    数据加载器

    ⭐ 重点：数据加载器是回测的数据源
    - 支持 CSV 文件加载
    - 支持 DataFrame 直接传入
    - 按时间顺序提供数据

    💡 值得思考：
    - 如何支持多种数据格式？
    - 如何实现数据缓存？
    - 如何处理大数据集？
    """

    def __init__(self):
        self._data: Dict[str, pd.DataFrame] = {}
        self._current_index: Dict[str, int] = {}

    def load_csv(self, filepath: str, symbol: str = None) -> None:
        """
        从 CSV 文件加载数据

        Args:
            filepath: CSV 文件路径
            symbol: 标的代码（可选，从文件名推断）
        """
        path = Path(filepath)
        if symbol is None:
            symbol = path.stem

        df = pd.read_csv(filepath)

        # 标准化列名
        df = self._normalize_columns(df)

        # 验证数据
        self._validate_data(df, symbol)

        self._data[symbol] = df
        self._current_index[symbol] = 0

    def load_dataframe(self, df: pd.DataFrame, symbol: str) -> None:
        """
        从 DataFrame 加载数据

        Args:
            df: 数据 DataFrame
            symbol: 标的代码
        """
        df = self._normalize_columns(df)
        self._validate_data(df, symbol)
        self._data[symbol] = df
        self._current_index[symbol] = 0

    def _normalize_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        标准化列名

        💡 值得思考：为什么需要标准化？
        - 不同数据源列名不同
        - 统一接口便于策略开发
        """
        column_mapping = {
            "Date": "date",
            "Open": "open",
            "High": "high",
            "Low": "low",
            "Close": "close",
            "Volume": "volume",
            "Adj Close": "adj_close"
        }

        df = df.rename(columns=column_mapping)

        # 确保日期列存在
        if "date" in df.columns:
            df["date"] = pd.to_datetime(df["date"])
            df = df.sort_values("date").reset_index(drop=True)

        return df

    def _validate_data(self, df: pd.DataFrame, symbol: str) -> None:
        """
        验证数据完整性

        ⭐ 重点：数据验证的重要性
        - 缺失数据会导致策略错误
        - 异常值会影响回测结果
        """
        required_columns = ["open", "high", "low", "close", "volume"]
        missing = [col for col in required_columns if col not in df.columns]

        if missing:
            raise ValueError(f"Missing columns for {symbol}: {missing}")

        # 检查缺失值
        null_counts = df[required_columns].isnull().sum()
        if null_counts.any():
            print(f"Warning: {symbol} has missing values: {null_counts.to_dict()}")

    def get_symbols(self) -> List[str]:
        """获取所有标的代码"""
        return list(self._data.keys())

    def get_data(self, symbol: str) -> pd.DataFrame:
        """获取标的数据"""
        if symbol not in self._data:
            raise KeyError(f"Symbol {symbol} not found")
        return self._data[symbol]

    def get_bar_count(self, symbol: str) -> int:
        """获取标的数据条数"""
        if symbol not in self._data:
            return 0
        return len(self._data[symbol])

    def get_bar(self, symbol: str, index: int) -> Optional[Dict]:
        """
        获取指定索引的K线数据

        Args:
            symbol: 标的代码
            index: 数据索引

        Returns:
            Dict: OHLCV 数据字典
        """
        if symbol not in self._data:
            return None

        df = self._data[symbol]
        if index < 0 or index >= len(df):
            return None

        row = df.iloc[index]
        return {
            "date": row.get("date"),
            "open": row["open"],
            "high": row["high"],
            "low": row["low"],
            "close": row["close"],
            "volume": row["volume"]
        }

    def get_bars(self, symbol: str, start: int = 0, end: int = None) -> List[Dict]:
        """
        获取多个K线数据

        Args:
            symbol: 标的代码
            start: 起始索引
            end: 结束索引

        Returns:
            List[Dict]: OHLCV 数据列表
        """
        if symbol not in self._data:
            return []

        df = self._data[symbol]
        if end is None:
            end = len(df)

        bars = []
        for i in range(start, min(end, len(df))):
            row = df.iloc[i]
            bars.append({
                "date": row.get("date"),
                "open": row["open"],
                "high": row["high"],
                "low": row["low"],
                "close": row["close"],
                "volume": row["volume"]
            })

        return bars

    def iter_bars(self, symbol: str) -> Iterator[Dict]:
        """
        迭代器方式获取K线数据

        💡 值得思考：迭代器 vs 列表？
        - 迭代器内存效率高
        - 适合大数据集
        """
        if symbol not in self._data:
            return

        for i in range(len(self._data[symbol])):
            yield self.get_bar(symbol, i)

    def reset(self) -> None:
        """重置所有索引"""
        for symbol in self._current_index:
            self._current_index[symbol] = 0
