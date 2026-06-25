"""
IC 加权组合模块

以因子的 IC 值为权重进行加权组合，给予预测能力更强的因子更高权重。
"""

import numpy as np
import pandas as pd
from typing import Optional, Dict, List


class ICWeightCombination:
    """
    IC 加权组合器

    使用因子的历史 IC 值作为权重。

    使用示例:
        >>> combiner = ICWeightCombination()
        >>> combined = combiner.combine(factor_df, ic_values)
    """

    @staticmethod
    def combine(factors: pd.DataFrame,
                ic_values: pd.Series,
                factor_cols: Optional[List[str]] = None,
                use_abs: bool = True) -> pd.Series:
        """
        IC 加权组合

        参数:
            factors: 包含多列因子的 DataFrame
            ic_values: 各因子的 IC 均值 (index=因子名)
            factor_cols: 要组合的因子列名
            use_abs: 是否使用 IC 绝对值作为权重

        返回:
            IC 加权组合因子值序列
        """
        if factor_cols is None:
            factor_cols = factors.columns.tolist()

        sub = factors[factor_cols].copy()
        z_scores = (sub - sub.mean()) / sub.std().replace(0, np.nan)

        # 构造权重
        weights = {}
        for col in factor_cols:
            if col in ic_values.index:
                weights[col] = ic_values[col]
            else:
                weights[col] = 0.0

        weight_series = pd.Series(weights)

        if use_abs:
            # 使用 IC 绝对值归一化
            total = weight_series.abs().sum()
        else:
            total = weight_series.sum()

        if total > 0:
            weight_series = weight_series / total

        # 加权求和
        weighted = z_scores.multiply(weight_series, axis=1)
        return weighted.sum(axis=1)

    @staticmethod
    def rolling_ic_weight(factors: pd.DataFrame,
                           forward_returns: pd.Series,
                           window: int = 60,
                           factor_cols: Optional[List[str]] = None) -> pd.Series:
        """
        滚动 IC 加权: 使用滚动窗口内的 IC 作为权重

        原理: IC 可能随时间变化，使用滚动 IC 更能反映因子的近期表现。

        参数:
            factors: 包含多列因子的 DataFrame
            forward_returns: 未来收益率序列
            window: IC 计算窗口
            factor_cols: 要组合的因子列名

        返回:
            滚动 IC 加权组合因子值序列
        """
        from scipy import stats

        if factor_cols is None:
            factor_cols = factors.columns.tolist()

        sub = factors[factor_cols].copy()
        z_scores = (sub - sub.mean()) / sub.std().replace(0, np.nan)

        result = pd.Series(np.nan, index=factors.index)

        for i in range(window, len(factors)):
            # 计算窗口内各因子的 IC
            window_z = z_scores.iloc[i - window:i]
            window_ret = forward_returns.iloc[i - window:i]

            ic_weights = {}
            for col in factor_cols:
                valid = pd.DataFrame({
                    "f": window_z[col],
                    "r": window_ret
                }).dropna()
                if len(valid) >= 10:
                    corr, _ = stats.spearmanr(valid["f"], valid["r"])
                    ic_weights[col] = corr
                else:
                    ic_weights[col] = 0.0

            weight_series = pd.Series(ic_weights)
            total = weight_series.abs().sum()
            if total > 0:
                weight_series = weight_series / total

            result.iloc[i] = (z_scores.iloc[i] * weight_series).sum()

        return result

    @staticmethod
    def ic_ir_weight(factors: pd.DataFrame,
                      ic_dict: Dict[str, pd.Series],
                      factor_cols: Optional[List[str]] = None) -> pd.Series:
        """
        IC_IR 加权: 以 IC 信息比率作为权重

        原理: IR = IC_mean / IC_std，综合考虑预测能力和稳定性。

        参数:
            factors: 包含多列因子的 DataFrame
            ic_dict: {因子名: IC时间序列} 的字典
            factor_cols: 要组合的因子列名

        返回:
            IC_IR 加权组合因子值序列
        """
        if factor_cols is None:
            factor_cols = factors.columns.tolist()

        sub = factors[factor_cols].copy()
        z_scores = (sub - sub.mean()) / sub.std().replace(0, np.nan)

        # 计算各因子的 IR
        ir_weights = {}
        for col in factor_cols:
            if col in ic_dict:
                ic = ic_dict[col].dropna()
                if len(ic) >= 5:
                    ir = ic.mean() / ic.std() if ic.std() > 0 else 0
                    ir_weights[col] = ir
                else:
                    ir_weights[col] = 0.0
            else:
                ir_weights[col] = 0.0

        weight_series = pd.Series(ir_weights)
        total = weight_series.abs().sum()
        if total > 0:
            weight_series = weight_series / total

        weighted = z_scores.multiply(weight_series, axis=1)
        return weighted.sum(axis=1)
