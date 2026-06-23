"""持仓数据管理模块

提供持仓组合的数据结构和管理功能。
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional
import numpy as np
import pandas as pd


@dataclass
class Position:
    """单个持仓"""
    symbol: str
    quantity: float
    current_price: float
    asset_class: str = "equity"

    @property
    def market_value(self) -> float:
        """持仓市值"""
        return self.quantity * self.current_price


@dataclass
class Portfolio:
    """投资组合"""
    name: str
    positions: List[Position] = field(default_factory=list)

    def add_position(self, position: Position) -> None:
        """添加持仓"""
        self.positions.append(position)

    def remove_position(self, symbol: str) -> bool:
        """移除持仓"""
        for i, pos in enumerate(self.positions):
            if pos.symbol == symbol:
                self.positions.pop(i)
                return True
        return False

    def get_position(self, symbol: str) -> Optional[Position]:
        """获取指定持仓"""
        for pos in self.positions:
            if pos.symbol == symbol:
                return pos
        return None

    @property
    def total_value(self) -> float:
        """组合总市值"""
        return sum(pos.market_value for pos in self.positions)

    @property
    def symbols(self) -> List[str]:
        """所有持仓的标的代码"""
        return [pos.symbol for pos in self.positions]

    @property
    def weights(self) -> Dict[str, float]:
        """各持仓的权重"""
        total = self.total_value
        if total == 0:
            return {}
        return {pos.symbol: pos.market_value / total for pos in self.positions}

    def get_returns_data(self, returns_df: pd.DataFrame) -> pd.DataFrame:
        """从收益率数据中提取组合相关数据

        Args:
            returns_df: 包含各标的收益率的 DataFrame

        Returns:
            组合相关标的的收益率数据
        """
        available_symbols = [s for s in self.symbols if s in returns_df.columns]
        return returns_df[available_symbols]

    def calculate_portfolio_returns(self, returns_df: pd.DataFrame) -> np.ndarray:
        """计算组合收益率

        Args:
            returns_df: 包含各标的收益率的 DataFrame

        Returns:
            组合的历史收益率序列
        """
        weights = self.weights
        available_symbols = [s for s in self.symbols if s in returns_df.columns]

        if not available_symbols:
            raise ValueError("No matching symbols found in returns data")

        # 提取权重和收益率数据
        weight_values = np.array([weights[s] for s in available_symbols])
        returns_data = returns_df[available_symbols].values

        # 归一化权重
        weight_values = weight_values / weight_values.sum()

        # 计算加权收益率
        portfolio_returns = returns_data @ weight_values

        return portfolio_returns

    def to_dict(self) -> Dict:
        """转换为字典格式"""
        return {
            "name": self.name,
            "total_value": self.total_value,
            "num_positions": len(self.positions),
            "positions": [
                {
                    "symbol": pos.symbol,
                    "quantity": pos.quantity,
                    "current_price": pos.current_price,
                    "market_value": pos.market_value,
                    "weight": self.weights.get(pos.symbol, 0)
                }
                for pos in self.positions
            ]
        }
