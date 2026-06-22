"""
模拟数据生成器 - 生成测试用的市场数据

⭐ 重点理解：为什么需要模拟数据？
- 回测需要历史数据
- 测试需要可控的数据
- 开发阶段没有真实数据

💡 值得思考：
- 如何生成逼真的市场数据？
- 几何布朗运动 vs 简单随机游走
- 如何模拟波动率聚集效应？
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Optional


class DataGenerator:
    """
    市场数据生成器

    ⭐ 重点：数据生成的数学模型
    - 几何布朗运动：dS = μSdt + σSdW
    - S: 价格, μ: 漂移率, σ: 波动率, dW: 维纳过程

    💡 值得思考：
    - 如何生成多标的相关数据？
    - 如何模拟不同市场状态？
    - 如何加入跳跃过程？
    """

    def __init__(self, seed: int = 42):
        """
        初始化数据生成器

        Args:
            seed: 随机种子，保证结果可重现
        """
        self.seed = seed
        np.random.seed(seed)

    def generate_gbm(
        self,
        symbol: str,
        start_price: float = 100.0,
        days: int = 252,
        mu: float = 0.1,
        sigma: float = 0.2,
        start_date: datetime = None
    ) -> pd.DataFrame:
        """
        生成几何布朗运动数据

        ⭐ 重点：GBM 是金融数据建模的基础
        - 价格变动服从对数正态分布
        - 收益率独立同分布
        - 适用于股票、外汇等

        Args:
            symbol: 标的代码
            start_price: 起始价格
            days: 交易日数
            mu: 年化漂移率（预期收益率）
            sigma: 年化波动率
            start_date: 起始日期

        Returns:
            DataFrame: OHLCV 数据

        💡 值得思考：
        - mu 和 sigma 如何从历史数据估计？
        - GBM 的局限性是什么？
        """
        if start_date is None:
            start_date = datetime.now() - timedelta(days=days)

        # 生成日收益率
        dt = 1 / 252  # 一年252个交易日
        daily_returns = np.random.normal(
            (mu - 0.5 * sigma**2) * dt,
            sigma * np.sqrt(dt),
            days
        )

        # 生成价格序列
        prices = start_price * np.exp(np.cumsum(daily_returns))

        # 生成 OHLCV 数据
        data = []
        for i in range(days):
            date = start_date + timedelta(days=i)
            close = prices[i]

            # 模拟日内波动
            daily_vol = sigma * np.sqrt(dt) * close
            high = close + abs(np.random.normal(0, daily_vol * 0.5))
            low = close - abs(np.random.normal(0, daily_vol * 0.5))
            open_price = close + np.random.normal(0, daily_vol * 0.3)

            # 确保 OHLC 关系正确
            high = max(high, open_price, close)
            low = min(low, open_price, close)

            # 生成成交量
            base_volume = 1000000
            volume = int(base_volume * np.exp(np.random.normal(0, 0.3)))

            data.append({
                "date": date,
                "symbol": symbol,
                "open": round(open_price, 2),
                "high": round(high, 2),
                "low": round(low, 2),
                "close": round(close, 2),
                "volume": volume
            })

        return pd.DataFrame(data)

    def generate_multi_symbols(
        self,
        symbols: List[str],
        days: int = 252,
        correlation: float = 0.5,
        start_date: datetime = None
    ) -> pd.DataFrame:
        """
        生成多个相关标的的数据

        ⭐ 重点：相关性建模
        - 使用 Cholesky 分解生成相关随机数
        - 相关性矩阵必须正定

        💡 值得思考：
        - 相关性如何影响组合风险？
        - 如何模拟危机时的相关性变化？

        Args:
            symbols: 标的列表
            days: 交易日数
            correlation: 标的间相关性
            start_date: 起始日期

        Returns:
            DataFrame: 多标的 OHLCV 数据
        """
        n = len(symbols)

        # 构建相关性矩阵
        corr_matrix = np.full((n, n), correlation)
        np.fill_diagonal(corr_matrix, 1.0)

        # Cholesky 分解
        try:
            L = np.linalg.cholesky(corr_matrix)
        except np.linalg.LinAlgError:
            # 如果矩阵不正定，使用单位矩阵
            L = np.eye(n)

        # 生成相关随机数
        independent_randoms = np.random.normal(0, 1, (days, n))
        correlated_randoms = independent_randoms @ L.T

        # 为每个标的生成数据
        all_data = []
        for i, symbol in enumerate(symbols):
            # 不同标的有不同的参数
            mu = np.random.uniform(0.05, 0.15)
            sigma = np.random.uniform(0.15, 0.3)
            start_price = np.random.uniform(50, 200)

            if start_date is None:
                start_date = datetime.now() - timedelta(days=days)

            dt = 1 / 252
            daily_returns = (mu - 0.5 * sigma**2) * dt + sigma * np.sqrt(dt) * correlated_randoms[:, i]
            prices = start_price * np.exp(np.cumsum(daily_returns))

            for j in range(days):
                date = start_date + timedelta(days=j)
                close = prices[j]
                daily_vol = sigma * np.sqrt(dt) * close
                high = close + abs(np.random.normal(0, daily_vol * 0.5))
                low = close - abs(np.random.normal(0, daily_vol * 0.3))
                open_price = close + np.random.normal(0, daily_vol * 0.2)
                high = max(high, open_price, close)
                low = min(low, open_price, close)
                volume = int(1000000 * np.exp(np.random.normal(0, 0.3)))

                all_data.append({
                    "date": date,
                    "symbol": symbol,
                    "open": round(open_price, 2),
                    "high": round(high, 2),
                    "low": round(low, 2),
                    "close": round(close, 2),
                    "volume": volume
                })

        return pd.DataFrame(all_data)

    def generate_trending_data(
        self,
        symbol: str,
        trend: str = "up",
        days: int = 252,
        start_price: float = 100.0,
        start_date: datetime = None
    ) -> pd.DataFrame:
        """
        生成有明确趋势的数据

        💡 值得思考：如何测试策略在不同市场状态下的表现？
        - 上升趋势
        - 下降趋势
        - 震荡市场

        Args:
            symbol: 标的代码
            trend: 趋势类型 "up", "down", "sideways"
            days: 交易日数
            start_price: 起始价格
            start_date: 起始日期
        """
        if trend == "up":
            mu, sigma = 0.3, 0.15
        elif trend == "down":
            mu, sigma = -0.2, 0.2
        else:  # sideways
            mu, sigma = 0.02, 0.25

        return self.generate_gbm(
            symbol=symbol,
            start_price=start_price,
            days=days,
            mu=mu,
            sigma=sigma,
            start_date=start_date
        )
