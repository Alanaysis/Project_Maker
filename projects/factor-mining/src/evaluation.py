"""因子评估模块

提供 IC 分析、分组回测、因子衰减等评估方法。
"""

import numpy as np
import pandas as pd
from scipy import stats
from typing import Optional, Tuple, Dict, List


class FactorEvaluator:
    """因子评估器"""

    def __init__(self, factor: pd.DataFrame, returns: pd.DataFrame,
                 periods: int = 1):
        """
        Args:
            factor: 因子值 DataFrame, index=日期, columns=股票代码
            returns: 未来收益率 DataFrame, 同上结构
            periods: 收益率对应的持有期(天数)
        """
        # 对齐日期
        common_dates = factor.index.intersection(returns.index)
        common_cols = factor.columns.intersection(returns.columns)
        self.factor = factor.loc[common_dates, common_cols]
        self.returns = returns.loc[common_dates, common_cols]
        self.periods = periods

    def rank_ic(self, method: str = 'spearman') -> pd.Series:
        """Rank IC (秩相关系数): 每期截面因子 rank 与收益率 rank 的相关系数

        Args:
            method: 'spearman' 或 'pearson'

        Returns:
            每期 IC 值的 Series
        """
        ic_series = []
        dates = []
        for date in self.factor.index:
            f = self.factor.loc[date].dropna()
            r = self.returns.loc[date].dropna()
            common = f.index.intersection(r.index)
            if len(common) < 10:
                continue
            if method == 'spearman':
                corr, _ = stats.spearmanr(f[common], r[common])
            else:
                corr, _ = stats.pearsonr(f[common], r[common])
            ic_series.append(corr)
            dates.append(date)
        return pd.Series(ic_series, index=dates, name='IC')

    def ic_summary(self) -> Dict[str, float]:
        """IC 统计摘要

        Returns:
            包含 IC 均值、标准差、ICIR、t 统计量、IC>0 占比的字典
        """
        ic = self.rank_ic()
        if len(ic) == 0:
            return {'IC_mean': np.nan, 'IC_std': np.nan,
                    'ICIR': np.nan, 'IC_tstat': np.nan,
                    'IC_positive_ratio': np.nan}

        ic_mean = ic.mean()
        ic_std = ic.std()
        icir = ic_mean / (ic_std + 1e-10)
        t_stat = ic_mean / (ic_std / np.sqrt(len(ic)) + 1e-10)
        positive_ratio = (ic > 0).mean()

        return {
            'IC_mean': round(ic_mean, 4),
            'IC_std': round(ic_std, 4),
            'ICIR': round(icir, 4),
            'IC_tstat': round(t_stat, 4),
            'IC_positive_ratio': round(positive_ratio, 4),
            'IC_count': len(ic),
        }

    def group_returns(self, n_groups: int = 5) -> pd.DataFrame:
        """分组收益: 按因子值将股票分为 n 组，计算每组的平均收益

        Args:
            n_groups: 分组数

        Returns:
            DataFrame, index=日期, columns=[G1, G2, ..., Gn], G1=因子最小组
        """
        group_ret = pd.DataFrame(index=self.factor.index,
                                  columns=[f'G{i+1}' for i in range(n_groups)])

        for date in self.factor.index:
            f = self.factor.loc[date].dropna()
            r = self.returns.loc[date].dropna()
            common = f.index.intersection(r.index)
            if len(common) < n_groups:
                continue
            f_vals = f[common]
            r_vals = r[common]
            # 按因子值分组
            try:
                groups = pd.qcut(f_vals, n_groups, labels=False, duplicates='drop')
            except ValueError:
                continue
            for g in range(n_groups):
                mask = groups == g
                if mask.any():
                    group_ret.loc[date, f'G{g+1}'] = r_vals[mask].mean()

        return group_ret.astype(float)

    def long_short_return(self, n_groups: int = 5) -> pd.Series:
        """多空收益: 做多因子最大组, 做空因子最小组

        Returns:
            每期多空收益 Series
        """
        gr = self.group_returns(n_groups)
        return gr[f'G{n_groups}'] - gr['G1']

    def long_only_return(self, n_groups: int = 5) -> pd.Series:
        """纯多头收益: 仅做多因子最大组

        Returns:
            每期多头收益 Series
        """
        gr = self.group_returns(n_groups)
        return gr[f'G{n_groups}']

    def cumulative_returns(self, n_groups: int = 5) -> pd.DataFrame:
        """分组累计收益

        Returns:
            累计收益 DataFrame
        """
        gr = self.group_returns(n_groups)
        return (1 + gr).cumprod() - 1

    def factor_turnover(self, n_groups: int = 5,
                        window: int = 1) -> pd.Series:
        """因子换手率: 衡量因子持仓的稳定性

        Returns:
            每期换手率 Series (0~1)
        """
        turnover_list = []
        dates = []
        prev_top = None
        for date in self.factor.index:
            f = self.factor.loc[date].dropna()
            if len(f) < n_groups:
                continue
            try:
                groups = pd.qcut(f, n_groups, labels=False, duplicates='drop')
            except ValueError:
                continue
            top = set(groups[groups == n_groups - 1].index)
            if prev_top is not None and len(top) > 0:
                overlap = len(top & prev_top)
                turnover = 1 - overlap / max(len(top), 1)
                turnover_list.append(turnover)
                dates.append(date)
            prev_top = top
        return pd.Series(turnover_list, index=dates, name='turnover')

    def factor_decay(self, max_lag: int = 10,
                     n_groups: int = 5) -> pd.DataFrame:
        """因子衰减分析: 不同持有期的多空收益

        Args:
            max_lag: 最大持有期
            n_groups: 分组数

        Returns:
            DataFrame, index=持有期, columns=[long_short_return, IC]
        """
        results = []
        for lag in range(1, max_lag + 1):
            # 计算 lag 期收益率
            future_ret = self.returns.shift(-lag)
            evaluator = FactorEvaluator(self.factor, future_ret, periods=lag)
            ic = evaluator.rank_ic().mean()
            ls = evaluator.long_short_return(n_groups).mean()
            results.append({'lag': lag, 'long_short_return': ls, 'IC': ic})

        return pd.DataFrame(results).set_index('lag')

    def performance_summary(self, n_groups: int = 5,
                            ann_factor: float = 252) -> Dict[str, float]:
        """综合绩效摘要

        Args:
            n_groups: 分组数
            ann_factor: 年化因子 (日频=252, 周频=52, 月频=12)

        Returns:
            绩效指标字典
        """
        ls_ret = self.long_short_return(n_groups)
        long_ret = self.long_only_return(n_groups)
        ic_summary = self.ic_summary()

        def _ann_return(r):
            if len(r) == 0:
                return 0
            cum = (1 + r).prod()
            n_periods = len(r)
            return cum ** (ann_factor / n_periods) - 1

        def _ann_volatility(r):
            return r.std() * np.sqrt(ann_factor)

        def _sharpe(r):
            vol = _ann_volatility(r)
            return _ann_return(r) / (vol + 1e-10)

        def _max_drawdown(r):
            cum = (1 + r).cumprod()
            peak = cum.cummax()
            dd = (cum - peak) / (peak + 1e-10)
            return dd.min()

        result = {
            'long_short_ann_return': round(_ann_return(ls_ret), 4),
            'long_short_ann_vol': round(_ann_volatility(ls_ret), 4),
            'long_short_sharpe': round(_sharpe(ls_ret), 4),
            'long_short_max_dd': round(_max_drawdown(ls_ret), 4),
            'long_only_ann_return': round(_ann_return(long_ret), 4),
            'long_only_sharpe': round(_sharpe(long_ret), 4),
        }
        result.update(ic_summary)
        return result
