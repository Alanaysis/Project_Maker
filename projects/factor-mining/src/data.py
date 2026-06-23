"""数据生成与加载模块

提供模拟股票数据生成功能，用于因子挖掘学习和测试。
"""

import numpy as np
import pandas as pd
from typing import Optional, Tuple


def generate_stock_data(n_stocks: int = 50, n_days: int = 500,
                        seed: int = 42) -> dict:
    """生成模拟股票数据

    生成包含价格、成交量、最高最低价的模拟数据。
    价格遵循几何布朗运动，加入一些横截面差异。

    Args:
        n_stocks: 股票数量
        n_days: 交易日天数
        seed: 随机种子

    Returns:
        dict with keys: 'price', 'volume', 'high', 'low', 'returns', 'market_cap'
    """
    rng = np.random.RandomState(seed)

    dates = pd.bdate_range(start='2023-01-01', periods=n_days, freq='B')
    tickers = [f'STOCK_{i:03d}' for i in range(n_stocks)]

    # 股票参数 (横截面差异)
    mu = rng.normal(0.0003, 0.0005, n_stocks)  # 日均收益
    sigma = rng.uniform(0.01, 0.04, n_stocks)   # 日波动率

    # 生成收益率
    returns_data = np.zeros((n_days, n_stocks))
    for i in range(n_stocks):
        returns_data[:, i] = rng.normal(mu[i], sigma[i], n_days)

    # 加入一些共同因子 (市场因子)
    market_factor = rng.normal(0.0002, 0.015, n_days)
    betas = rng.uniform(0.5, 1.5, n_stocks)
    for i in range(n_stocks):
        returns_data[:, i] += betas[i] * market_factor

    # 加入一些可被因子捕捉的模式
    # 动量效应: 过去收益与未来收益正相关
    for i in range(n_stocks):
        momentum = pd.Series(returns_data[:, i]).rolling(20).mean().fillna(0).values
        returns_data[:, i] += 0.1 * momentum + rng.normal(0, 0.001, n_days)

    returns_df = pd.DataFrame(returns_data, index=dates, columns=tickers)

    # 价格序列
    init_prices = rng.uniform(10, 100, n_stocks)
    price_data = np.zeros((n_days, n_stocks))
    price_data[0] = init_prices
    for t in range(1, n_days):
        price_data[t] = price_data[t-1] * (1 + returns_data[t])
    price_df = pd.DataFrame(price_data, index=dates, columns=tickers)

    # 最高最低价
    daily_range = np.abs(returns_data) + rng.uniform(0, 0.01, (n_days, n_stocks))
    high_data = price_data * (1 + daily_range / 2)
    low_data = price_data * (1 - daily_range / 2)
    high_df = pd.DataFrame(high_data, index=dates, columns=tickers)
    low_df = pd.DataFrame(low_data, index=dates, columns=tickers)

    # 成交量 (对数正态, 与波动率正相关)
    base_volume = rng.lognormal(15, 1, n_stocks)  # 基础成交量
    volume_noise = rng.lognormal(0, 0.5, (n_days, n_stocks))
    vol_factor = 1 + 5 * np.abs(returns_data)  # 大涨大跌时放量
    volume_data = base_volume * volume_noise * vol_factor
    volume_df = pd.DataFrame(volume_data, index=dates, columns=tickers)

    # 市值
    market_cap = price_data[-1] * rng.uniform(1e8, 1e10, n_stocks)
    market_cap_series = pd.Series(market_cap, index=tickers, name='market_cap')

    return {
        'price': price_df,
        'volume': volume_df,
        'high': high_df,
        'low': low_df,
        'returns': returns_df,
        'market_cap': market_cap_series,
    }


def load_example_data() -> dict:
    """加载示例数据 (默认参数)"""
    return generate_stock_data()


def split_train_test(data: dict, train_ratio: float = 0.7) -> Tuple[dict, dict]:
    """将数据分割为训练集和测试集

    Args:
        data: 数据字典
        train_ratio: 训练集占比

    Returns:
        (train_data, test_data) 两个字典
    """
    n = len(data['price'])
    split_idx = int(n * train_ratio)

    train, test = {}, {}
    for key in data:
        if isinstance(data[key], pd.DataFrame):
            train[key] = data[key].iloc[:split_idx]
            test[key] = data[key].iloc[split_idx:]
        elif isinstance(data[key], pd.Series):
            train[key] = data[key]
            test[key] = data[key]
        else:
            train[key] = data[key]
            test[key] = data[key]

    return train, test
