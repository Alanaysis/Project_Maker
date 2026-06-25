"""
因子衰减分析模块

分析因子预测能力随持仓时间的变化，帮助确定最优持仓周期。
好的因子应该在多个持仓周期都有稳定的预测能力。
"""

import numpy as np
import pandas as pd
from scipy import stats
from typing import Optional, Dict, List


class DecayAnalysis:
    """
    因子衰减分析器

    分析因子 IC 随持仓天数的衰减情况。

    使用示例:
        >>> analyzer = DecayAnalysis()
        >>> decay = analyzer.ic_decay_by_horizon(factor_panel, return_panel)
        >>> half_life = analyzer.estimate_half_life(decay)
    """

    @staticmethod
    def ic_decay_by_horizon(factor_panel: pd.DataFrame,
                             return_panel: pd.DataFrame,
                             max_horizon: int = 20) -> pd.DataFrame:
        """
        计算不同持仓周期的 IC 值

        参数:
            factor_panel: 因子面板 (index=日期, columns=股票)
            return_panel: 日收益率面板
            max_horizon: 最大持仓天数

        返回:
            DataFrame: horizon, ic_mean, ic_std, ic_ir
        """
        results = []

        for horizon in range(1, max_horizon + 1):
            # 计算 horizon 天累计收益
            cum_return = return_panel.rolling(window=horizon).sum()

            # 计算每期的 Rank IC
            common_dates = factor_panel.index.intersection(cum_return.index)
            ics = []
            for date in common_dates:
                f = factor_panel.loc[date]
                r = cum_return.loc[date]
                valid = pd.DataFrame({"f": f, "r": r}).dropna()
                if len(valid) >= 10:
                    corr, _ = stats.spearmanr(valid["f"], valid["r"])
                    ics.append(corr)

            if ics:
                ic_arr = np.array(ics)
                results.append({
                    "horizon": horizon,
                    "ic_mean": np.mean(ic_arr),
                    "ic_std": np.std(ic_arr),
                    "ic_ir": np.mean(ic_arr) / np.std(ic_arr) if np.std(ic_arr) > 0 else 0,
                    "ic_positive_rate": (ic_arr > 0).mean(),
                })

        return pd.DataFrame(results)

    @staticmethod
    def estimate_half_life(decay_df: pd.DataFrame,
                            threshold_ratio: float = 0.5) -> Optional[int]:
        """
        估计 IC 半衰期: IC 衰减到初始值一半所需的天数

        原理: 半衰期越长，因子持续性越好。

        参数:
            decay_df: ic_decay_by_horizon 的返回结果
            threshold_ratio: 半衰阈值比例 (默认 0.5)

        返回:
            半衰期 (天数)，如果无法估计则返回 None
        """
        if decay_df.empty:
            return None

        initial_ic = decay_df.iloc[0]["ic_mean"]
        if abs(initial_ic) < 1e-6:
            return None

        threshold = abs(initial_ic) * threshold_ratio

        for _, row in decay_df.iterrows():
            if abs(row["ic_mean"]) < threshold:
                return int(row["horizon"])

        # IC 始终高于阈值
        return int(decay_df.iloc[-1]["horizon"])

    @staticmethod
    def optimal_holding_period(decay_df: pd.DataFrame) -> int:
        """
        确定最优持仓周期: IC_IR 最大的持仓天数

        原理: 选择 IR 最高的持仓周期，平衡预测能力和稳定性。

        参数:
            decay_df: ic_decay_by_horizon 的返回结果

        返回:
            最优持仓天数
        """
        if decay_df.empty:
            return 1
        best_idx = decay_df["ic_ir"].abs().idxmax()
        return int(decay_df.loc[best_idx, "horizon"])

    @staticmethod
    def factor_persistence_score(decay_df: pd.DataFrame) -> float:
        """
        因子持续性评分: IC 衰减曲线下的面积

        原理: 面积越大，因子在各持仓周期的综合表现越好。
        计算: 标准化的 AUC (Area Under Curve)

        参数:
            decay_df: ic_decay_by_horizon 的返回结果

        返回:
            持续性评分 (0 到 1)
        """
        if decay_df.empty:
            return 0.0

        ic_values = decay_df["ic_mean"].abs().values
        max_ic = ic_values.max()
        if max_ic < 1e-6:
            return 0.0

        # 归一化后计算 AUC
        normalized = ic_values / max_ic
        auc = np.trapezoid(normalized, dx=1)
        # 归一化到 0-1
        return auc / len(normalized)

    @staticmethod
    def decay_curve_fit(decay_df: pd.DataFrame) -> Dict[str, float]:
        """
        拟合 IC 衰减曲线: 使用指数衰减模型

        模型: IC(t) = IC_0 * exp(-lambda * t)

        参数:
            decay_df: ic_decay_by_horizon 的返回结果

        返回:
            拟合参数: {"ic_0": 初始IC, "lambda": 衰减速率, "r_squared": 拟合优度}
        """
        if len(decay_df) < 3:
            return {"ic_0": np.nan, "lambda": np.nan, "r_squared": np.nan}

        t = decay_df["horizon"].values.astype(float)
        ic = decay_df["ic_mean"].abs().values

        # 对数变换后线性拟合
        valid = ic > 1e-10
        if valid.sum() < 3:
            return {"ic_0": np.nan, "lambda": np.nan, "r_squared": np.nan}

        log_ic = np.log(ic[valid])
        t_valid = t[valid]

        # 线性回归: log(IC) = log(IC_0) - lambda * t
        slope, intercept, r_value, _, _ = stats.linregress(t_valid, log_ic)

        return {
            "ic_0": np.exp(intercept),
            "lambda": -slope,
            "r_squared": r_value ** 2,
            "half_life": np.log(2) / (-slope) if slope < 0 else np.inf,
        }
