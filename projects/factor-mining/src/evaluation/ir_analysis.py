"""
IR (Information Ratio) 分析模块

IR = IC 均值 / IC 标准差，衡量因子预测能力的稳定性。
- IR > 0.5 优秀，IR > 0.3 良好，IR > 0.1 可用
- IR 比 IC 更重要，因为稳定的弱信号比不稳定的强信号更有价值
"""

import numpy as np
import pandas as pd
from typing import Optional, Dict, List


class IRAnalysis:
    """
    IR 分析器

    计算因子的 IR (信息比率) 及相关稳定性指标。

    使用示例:
        >>> analyzer = IRAnalysis()
        >>> ir = analyzer.compute_ir(ic_series)
        >>> rolling_ir = analyzer.rolling_ir(ic_series, window=60)
    """

    @staticmethod
    def compute_ir(ic_series: pd.Series) -> float:
        """
        计算 IR: IC 均值 / IC 标准差

        IR 衡量因子预测能力的稳定性，是因子评估的核心指标。
        计算: IR = mean(IC) / std(IC)

        参数:
            ic_series: IC 时间序列

        返回:
            IR 值
        """
        ic_clean = ic_series.dropna()
        if len(ic_clean) < 2:
            return np.nan
        std = ic_clean.std()
        return ic_clean.mean() / std if std > 0 else 0.0

    @staticmethod
    def rolling_ir(ic_series: pd.Series, window: int = 60) -> pd.Series:
        """
        滚动 IR: 观察 IR 的时间变化

        原理: 因子有效性可能随时间变化，滚动 IR 可以捕捉这种变化。
              IR 持续下降可能意味着因子失效。

        参数:
            ic_series: IC 时间序列
            window: 滚动窗口 (交易日数)

        返回:
            滚动 IR 时间序列
        """
        rolling_mean = ic_series.rolling(window=window).mean()
        rolling_std = ic_series.rolling(window=window).std()
        return rolling_mean / rolling_std.replace(0, np.nan)

    @staticmethod
    def ir_by_period(ic_series: pd.Series,
                     period: str = "Q") -> pd.DataFrame:
        """
        按期间统计 IR

        按季度/年度统计 IR，观察因子有效性的周期性变化。

        参数:
            ic_series: IC 时间序列 (index 为日期)
            period: 分组周期 ("Q"=季度, "Y"=年度, "M"=月度)

        返回:
            DataFrame，包含每期的 IC 均值、IC 标准差、IR
        """
        ic_series = ic_series.dropna()
        ic_series.index = pd.to_datetime(ic_series.index)

        grouped = ic_series.groupby(pd.Grouper(freq=period))
        results = []
        for name, group in grouped:
            if len(group) >= 5:
                ic_mean = group.mean()
                ic_std = group.std()
                results.append({
                    "period": name,
                    "ic_mean": ic_mean,
                    "ic_std": ic_std,
                    "ir": ic_mean / ic_std if ic_std > 0 else 0,
                    "ic_pos_pct": (group > 0).mean(),
                    "count": len(group),
                })

        return pd.DataFrame(results)

    @staticmethod
    def multi_factor_ir_comparison(ic_dict: Dict[str, pd.Series]) -> pd.DataFrame:
        """
        多因子 IR 对比

        比较多个因子的 IR，帮助选择最有效的因子。

        参数:
            ic_dict: {因子名: IC 时间序列} 的字典

        返回:
            DataFrame，包含各因子的 IC 均值、IC 标准差、IR 等指标
        """
        results = []
        for name, ic_series in ic_dict.items():
            ic_clean = ic_series.dropna()
            if len(ic_clean) >= 5:
                ic_mean = ic_clean.mean()
                ic_std = ic_clean.std()
                results.append({
                    "factor": name,
                    "ic_mean": ic_mean,
                    "ic_std": ic_std,
                    "ir": ic_mean / ic_std if ic_std > 0 else 0,
                    "ic_pos_pct": (ic_clean > 0).mean(),
                    "max_ic": ic_clean.max(),
                    "min_ic": ic_clean.min(),
                    "count": len(ic_clean),
                })

        df = pd.DataFrame(results)
        if not df.empty:
            df = df.sort_values("ir", ascending=False, key=abs)
        return df

    @staticmethod
    def factor_stability_score(ic_series: pd.Series,
                                window: int = 20) -> pd.Series:
        """
        因子稳定性评分: IR 的滚动标准差的负值

        原理: IR 波动越小，因子越稳定。评分越高越好。
        计算: Stability = -std(IR_rolling)

        参数:
            ic_series: IC 时间序列
            window: 滚动窗口

        返回:
            因子稳定性评分时间序列
        """
        rolling_ir = IRAnalysis.rolling_ir(ic_series, window=window)
        # IR 的滚动波动率
        ir_volatility = rolling_ir.rolling(window=window).std()
        return -ir_volatility

    @staticmethod
    def ic_hit_rate(ic_series: pd.Series,
                    min_ic: float = 0.02) -> Dict[str, float]:
        """
        IC 命中率分析: IC 超过阈值的比例

        参数:
            ic_series: IC 时间序列
            min_ic: IC 阈值

        返回:
            包含各种命中率的字典
        """
        ic_clean = ic_series.dropna()
        if len(ic_clean) == 0:
            return {}

        return {
            "ic_positive_rate": (ic_clean > 0).mean(),
            "ic_negative_rate": (ic_clean < 0).mean(),
            "ic_above_threshold": (ic_clean.abs() > min_ic).mean(),
            "consecutive_positive_max": IRAnalysis._max_consecutive(ic_clean > 0),
            "consecutive_negative_max": IRAnalysis._max_consecutive(ic_clean < 0),
        }

    @staticmethod
    def _max_consecutive(bool_series: pd.Series) -> int:
        """计算布尔序列中最长连续 True 的长度"""
        groups = (~bool_series).cumsum()
        consecutive = bool_series.groupby(groups).sum()
        return int(consecutive.max()) if len(consecutive) > 0 else 0
