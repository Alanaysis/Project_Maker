"""
IC (Information Coefficient) 分析模块

IC 是因子评估最核心的指标，衡量因子值与未来收益率之间的相关性。
- IC (Rank IC): 因子排名与未来收益率排名的 Spearman 相关系数
- IC > 0.03 即有统计意义，IC > 0.05 较好，IC > 0.10 优秀
"""

import numpy as np
import pandas as pd
from scipy import stats
from typing import Optional, Tuple, Dict


class ICAnalysis:
    """
    IC 分析器

    计算因子的 IC (信息系数) 及其统计特征。

    核心指标:
        - IC 均值: 因子预测能力的期望
        - IC 标准差: 因子预测能力的稳定性
        - IC > 0 比例: 因子方向一致性
        - IC_IR: IC 均值 / IC 标准差，综合评价指标

    使用示例:
        >>> analyzer = ICAnalysis()
        >>> result = analyzer.compute_ic(factor_series, returns_series)
        >>> print(f"IC 均值: {result['ic_mean']:.4f}")
        >>> print(f"IC_IR: {result['ic_ir']:.4f}")
    """

    @staticmethod
    def rank_ic(factor: pd.Series, forward_return: pd.Series) -> float:
        """
        计算单期 Rank IC

        Rank IC 使用 Spearman 秩相关，对极端值更稳健。
        计算: IC = spearman_corr(rank(factor), rank(return))

        参数:
            factor: 因子值序列
            forward_return: 未来收益率序列

        返回:
            Rank IC 值 (-1 到 1)
        """
        # 去除缺失值
        valid = pd.DataFrame({"factor": factor, "return": forward_return}).dropna()
        if len(valid) < 10:
            return np.nan

        corr, _ = stats.spearmanr(valid["factor"], valid["return"])
        return corr

    @staticmethod
    def pearson_ic(factor: pd.Series, forward_return: pd.Series) -> float:
        """
        计算单期 Pearson IC

        Pearson IC 使用线性相关系数，对极端值敏感。
        计算: IC = pearson_corr(factor, return)

        参数:
            factor: 因子值序列
            forward_return: 未来收益率序列

        返回:
            Pearson IC 值 (-1 到 1)
        """
        valid = pd.DataFrame({"factor": factor, "return": forward_return}).dropna()
        if len(valid) < 10:
            return np.nan
        return valid["factor"].corr(valid["return"])

    @classmethod
    def compute_ic_series(cls, factor_panel: pd.DataFrame,
                           return_panel: pd.DataFrame,
                           method: str = "rank") -> pd.Series:
        """
        计算 IC 时间序列 (每期一个 IC 值)

        参数:
            factor_panel: 因子面板 (index=日期, columns=股票)
            return_panel: 收益率面板 (index=日期, columns=股票)
            method: "rank" 或 "pearson"

        返回:
            IC 时间序列 (index=日期)
        """
        ic_func = cls.rank_ic if method == "rank" else cls.pearson_ic

        common_dates = factor_panel.index.intersection(return_panel.index)
        ic_values = {}
        for date in common_dates:
            ic_values[date] = ic_func(factor_panel.loc[date],
                                       return_panel.loc[date])

        return pd.Series(ic_values, name=f"IC_{method}")

    @classmethod
    def compute_ic_summary(cls, factor_panel: pd.DataFrame,
                            return_panel: pd.DataFrame,
                            method: str = "rank") -> Dict[str, float]:
        """
        计算 IC 统计摘要

        返回以下指标:
            - ic_mean:     IC 均值
            - ic_std:      IC 标准差
            - ic_ir:       IC 信息比率 (IC_mean / IC_std)
            - ic_pos_pct:  IC > 0 的比例
            - ic_abs_mean: |IC| 均值
            - t_stat:      t 统计量 (检验 IC 是否显著不为 0)
            - p_value:     p 值

        参数:
            factor_panel: 因子面板
            return_panel: 收益率面板
            method: "rank" 或 "pearson"

        返回:
            包含各统计指标的字典
        """
        ic_series = cls.compute_ic_series(factor_panel, return_panel, method)
        ic_series = ic_series.dropna()

        if len(ic_series) == 0:
            return {k: np.nan for k in [
                "ic_mean", "ic_std", "ic_ir", "ic_pos_pct",
                "ic_abs_mean", "t_stat", "p_value", "count"
            ]}

        ic_mean = ic_series.mean()
        ic_std = ic_series.std()
        t_stat = ic_mean / (ic_std / np.sqrt(len(ic_series))) if ic_std > 0 else 0
        p_value = 2 * (1 - stats.t.cdf(abs(t_stat), df=len(ic_series) - 1))

        return {
            "ic_mean": ic_mean,
            "ic_std": ic_std,
            "ic_ir": ic_mean / ic_std if ic_std > 0 else 0,
            "ic_pos_pct": (ic_series > 0).mean(),
            "ic_abs_mean": ic_series.abs().mean(),
            "t_stat": t_stat,
            "p_value": p_value,
            "count": len(ic_series),
        }

    @staticmethod
    def ic_decay(factor_panel: pd.DataFrame,
                 return_panel: pd.DataFrame,
                 max_lag: int = 20) -> pd.DataFrame:
        """
        IC 衰减分析: 计算不同持仓周期下的 IC 值

        原理: 好的因子应该在多个持仓周期都有稳定的 IC。
              IC 衰减慢说明因子持续性好。

        参数:
            factor_panel: 因子面板
            return_panel: 日收益率面板
            max_lag: 最大持仓天数

        返回:
            DataFrame，columns=["lag", "ic_mean", "ic_ir"]
        """
        results = []
        for lag in range(1, max_lag + 1):
            # 计算 lag 日累计收益
            cum_return = return_panel.rolling(window=lag).sum()
            # 与因子对齐
            common_dates = factor_panel.index.intersection(cum_return.index)
            ics = []
            for date in common_dates:
                valid = pd.DataFrame({
                    "f": factor_panel.loc[date],
                    "r": cum_return.loc[date]
                }).dropna()
                if len(valid) >= 10:
                    corr, _ = stats.spearmanr(valid["f"], valid["r"])
                    ics.append(corr)

            if ics:
                ic_arr = np.array(ics)
                results.append({
                    "lag": lag,
                    "ic_mean": np.mean(ic_arr),
                    "ic_std": np.std(ic_arr),
                    "ic_ir": np.mean(ic_arr) / np.std(ic_arr) if np.std(ic_arr) > 0 else 0,
                })

        return pd.DataFrame(results)

    @staticmethod
    def monthly_ic_heatmap_data(factor_panel: pd.DataFrame,
                                 return_panel: pd.DataFrame) -> pd.DataFrame:
        """
        月度 IC 热力图数据

        按年月汇总 IC 值，用于绘制热力图观察因子的时间稳定性。

        参数:
            factor_panel: 因子面板
            return_panel: 收益率面板

        返回:
            DataFrame，index=月份 (1-12), columns=年份, values=IC均值
        """
        ic_series = ICAnalysis.compute_ic_series(factor_panel, return_panel)
        ic_series.index = pd.to_datetime(ic_series.index)

        # 按年月分组
        monthly = ic_series.groupby(
            [ic_series.index.year, ic_series.index.month]
        ).mean()
        monthly.index.names = ["year", "month"]

        # 转换为热力图格式
        heatmap = monthly.unstack(level="month")
        heatmap.columns = [f"{m}月" for m in heatmap.columns]
        return heatmap
