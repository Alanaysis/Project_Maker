"""回测框架模块

提供基于因子的简单回测框架，支持等权/市值加权、交易成本、换仓频率等。
"""

import numpy as np
import pandas as pd
from typing import Optional, Dict, List
from dataclasses import dataclass, field


@dataclass
class BacktestConfig:
    """回测配置"""
    n_groups: int = 5                  # 分组数
    rebalance_freq: int = 1            # 换仓频率 (天)
    top_group_only: bool = False       # 是否仅做多最高组
    transaction_cost: float = 0.001    # 单边交易成本
    weight_method: str = 'equal'       # 加权方式: 'equal' / 'market_cap'
    benchmark: Optional[pd.Series] = None  # 基准收益


class BacktestEngine:
    """因子回测引擎"""

    def __init__(self, factor: pd.DataFrame, returns: pd.DataFrame,
                 config: Optional[BacktestConfig] = None):
        """
        Args:
            factor: 因子值 DataFrame, index=日期, columns=股票代码
            returns: 日收益率 DataFrame, 同上结构
            config: 回测配置
        """
        common_dates = factor.index.intersection(returns.index)
        common_cols = factor.columns.intersection(returns.columns)
        self.factor = factor.loc[common_dates, common_cols]
        self.returns = returns.loc[common_dates, common_cols]
        self.config = config or BacktestConfig()

    def run(self) -> 'BacktestResult':
        """执行回测

        Returns:
            BacktestResult 回测结果对象
        """
        cfg = self.config
        dates = self.factor.index
        portfolio_values = [1.0]
        daily_returns = []
        holdings_history = []
        turnover_list = []
        prev_weights = None

        for i, date in enumerate(dates):
            if i % cfg.rebalance_freq == 0:
                # 换仓日：根据因子值分配权重
                weights = self._allocate_weights(date)
                holdings_history.append((date, weights))

                # 计算换手率
                if prev_weights is not None:
                    turnover = self._calc_turnover(prev_weights, weights)
                    turnover_list.append((date, turnover))
                prev_weights = weights
            else:
                weights = prev_weights

            if weights is None or weights.sum() == 0:
                daily_returns.append(0.0)
                portfolio_values.append(portfolio_values[-1])
                continue

            # 当日组合收益
            ret = self.returns.loc[date]
            common = weights.index.intersection(ret.dropna().index)
            if len(common) == 0:
                daily_returns.append(0.0)
                portfolio_values.append(portfolio_values[-1])
                continue

            w = weights[common]
            w = w / (w.sum() + 1e-10)  # 归一化
            port_ret = (w * ret[common]).sum()

            # 扣除交易成本 (简化: 只在换仓日扣)
            if i % cfg.rebalance_freq == 0 and turnover_list:
                cost = cfg.transaction_cost * 2 * turnover_list[-1][1]
                port_ret -= cost

            # 防止极端收益率导致溢出 (限制在合理范围内)
            port_ret = np.clip(port_ret, -0.2, 0.2)
            daily_returns.append(port_ret)
            portfolio_values.append(portfolio_values[-1] * (1 + port_ret))

        # 构建结果
        result = BacktestResult(
            daily_returns=pd.Series(daily_returns, index=dates, name='portfolio'),
            portfolio_values=pd.Series(portfolio_values[1:], index=dates,
                                       name='nav'),
            holdings_history=holdings_history,
            turnover=pd.Series(
                [t[1] for t in turnover_list],
                index=[t[0] for t in turnover_list]
            ) if turnover_list else pd.Series(dtype=float),
            benchmark=cfg.benchmark,
            config=cfg,
        )
        return result

    def _allocate_weights(self, date) -> Optional[pd.Series]:
        """根据因子值分配权重"""
        cfg = self.config
        f = self.factor.loc[date].dropna()
        if len(f) < cfg.n_groups:
            return None

        try:
            groups = pd.qcut(f, cfg.n_groups, labels=False, duplicates='drop')
        except ValueError:
            return None

        if cfg.top_group_only:
            target_group = cfg.n_groups - 1
            mask = groups == target_group
        else:
            # 多空策略: 做多最高组, 做空最低组
            target_group = cfg.n_groups - 1
            bottom_group = 0
            mask = (groups == target_group) | (groups == bottom_group)

        selected = f[mask]
        if len(selected) == 0:
            return None

        weights = pd.Series(0.0, index=self.factor.columns)
        if cfg.weight_method == 'equal':
            # 等权: 最高组正权重, 最低组负权重
            top = selected[groups[mask] == target_group]
            bot = selected[groups[mask] == bottom_group] if not cfg.top_group_only else pd.Series(dtype=float)
            if len(top) > 0:
                weights[top.index] = 1.0 / len(top)
            if len(bot) > 0:
                weights[bot.index] = -1.0 / len(bot)
        else:
            # 按因子值加权
            weights[selected.index] = selected / selected.abs().sum()

        return weights

    def _calc_turnover(self, old_weights: pd.Series,
                       new_weights: pd.Series) -> float:
        """计算换手率"""
        common = old_weights.index.intersection(new_weights.index)
        diff = (new_weights[common] - old_weights[common]).abs()
        return diff.sum() / 2


class BacktestResult:
    """回测结果"""

    def __init__(self, daily_returns: pd.Series, portfolio_values: pd.Series,
                 holdings_history: list, turnover: pd.Series,
                 benchmark: Optional[pd.Series], config: BacktestConfig):
        self.daily_returns = daily_returns
        self.portfolio_values = portfolio_values
        self.holdings_history = holdings_history
        self.turnover = turnover
        self.benchmark = benchmark
        self.config = config

    def summary(self, ann_factor: int = 252) -> Dict[str, float]:
        """绩效摘要"""
        r = self.daily_returns
        cum = (1 + r).prod()
        n = len(r)

        ann_return = cum ** (ann_factor / max(n, 1)) - 1
        ann_vol = r.std() * np.sqrt(ann_factor)
        sharpe = ann_return / (ann_vol + 1e-10)

        # 最大回撤
        cum_values = self.portfolio_values
        peak = cum_values.cummax()
        dd = (cum_values - peak) / (peak + 1e-10)
        max_dd = dd.min()

        # Calmar 比率
        calmar = ann_return / (abs(max_dd) + 1e-10)

        # 胜率
        win_rate = (r > 0).mean()

        result = {
            'total_return': round(cum - 1, 4),
            'ann_return': round(ann_return, 4),
            'ann_volatility': round(ann_vol, 4),
            'sharpe_ratio': round(sharpe, 4),
            'max_drawdown': round(max_dd, 4),
            'calmar_ratio': round(calmar, 4),
            'win_rate': round(win_rate, 4),
            'avg_turnover': round(self.turnover.mean(), 4) if len(self.turnover) > 0 else 0,
            'trading_days': n,
        }

        # 如果有基准，计算超额收益
        if self.benchmark is not None:
            bm = self.benchmark.reindex(r.index).fillna(0)
            excess = r - bm
            result['excess_ann_return'] = round(
                (1 + excess).prod() ** (ann_factor / max(n, 1)) - 1, 4)
            result['info_ratio'] = round(
                excess.mean() / (excess.std() + 1e-10) * np.sqrt(ann_factor), 4)

        return result

    def to_dataframe(self) -> pd.DataFrame:
        """将每日收益和净值转为 DataFrame"""
        df = pd.DataFrame({
            'daily_return': self.daily_returns,
            'nav': self.portfolio_values,
        })
        df['cumulative_return'] = df['nav'] - 1
        df['drawdown'] = df['nav'] / df['nav'].cummax() - 1
        return df


def multi_factor_backtest(factors: Dict[str, pd.DataFrame],
                          returns: pd.DataFrame,
                          weights: Optional[Dict[str, float]] = None,
                          config: Optional[BacktestConfig] = None) -> BacktestResult:
    """多因子组合回测

    Args:
        factors: {因子名: 因子DataFrame} 字典
        returns: 收益率 DataFrame
        weights: {因子名: 权重} 字典, 等权为 None
        config: 回测配置

    Returns:
        回测结果
    """
    if weights is None:
        weights = {k: 1.0 / len(factors) for k in factors}

    # 截面标准化后加权
    normalized = {}
    for name, f in factors.items():
        mean = f.mean(axis=1)
        std = f.std(axis=1)
        normalized[name] = f.sub(mean, axis=0).div(std + 1e-10, axis=0)

    composite = sum(normalized[name] * weights.get(name, 0)
                    for name in factors)

    engine = BacktestEngine(composite, returns, config)
    return engine.run()
