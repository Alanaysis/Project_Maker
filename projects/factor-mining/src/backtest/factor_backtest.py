"""
因子回测模块

完整评估单个因子的预测能力和投资价值。
包括 IC 分析、分组回测、衰减分析等全套评估流程。
"""

import numpy as np
import pandas as pd
from typing import Optional, Dict, List

from src.evaluation.ic_analysis import ICAnalysis
from src.evaluation.ir_analysis import IRAnalysis
from src.evaluation.group_backtest import GroupBacktest
from src.evaluation.decay_analysis import DecayAnalysis


class FactorBacktest:
    """
    因子回测器

    对单个因子进行全面的回测评估。

    使用示例:
        >>> backtest = FactorBacktest(n_groups=5)
        >>> result = backtest.run(factor_panel, return_panel)
        >>> backtest.print_summary(result)
    """

    def __init__(self, n_groups: int = 5, holding_period: int = 1):
        """
        初始化因子回测器

        参数:
            n_groups: 分组数量
            holding_period: 持仓周期 (天)
        """
        self.n_groups = n_groups
        self.holding_period = holding_period

    def run(self, factor_panel: pd.DataFrame,
            return_panel: pd.DataFrame) -> Dict:
        """
        执行完整因子回测

        参数:
            factor_panel: 因子面板 (index=日期, columns=股票)
            return_panel: 日收益率面板

        返回:
            包含所有回测结果的字典
        """
        results = {}

        # 1. IC 分析
        ic_analyzer = ICAnalysis()
        results["ic_summary"] = ic_analyzer.compute_ic_summary(
            factor_panel, return_panel)
        results["ic_series"] = ic_analyzer.compute_ic_series(
            factor_panel, return_panel)

        # 2. IR 分析
        ir_analyzer = IRAnalysis()
        results["ir"] = ir_analyzer.compute_ir(results["ic_series"])
        results["rolling_ir"] = ir_analyzer.rolling_ir(results["ic_series"])
        results["ir_by_quarter"] = ir_analyzer.ir_by_period(results["ic_series"])

        # 3. 分组回测
        group_bt = GroupBacktest(n_groups=self.n_groups)
        group_result = group_bt.run(factor_panel, return_panel,
                                     self.holding_period)
        results["group_returns"] = group_result["group_returns"]
        results["group_cumulative"] = group_result["cumulative"]
        results["long_short"] = group_result["long_short"]
        results["group_stats"] = group_result["group_stats"]
        results["monotonicity"] = group_result["monotonicity"]

        # 4. 衰减分析
        decay_analyzer = DecayAnalysis()
        decay_df = decay_analyzer.ic_decay_by_horizon(factor_panel, return_panel)
        results["ic_decay"] = decay_df
        results["half_life"] = decay_analyzer.estimate_half_life(decay_df)
        results["optimal_holding"] = decay_analyzer.optimal_holding_period(decay_df)
        results["persistence_score"] = decay_analyzer.factor_persistence_score(decay_df)

        # 5. 综合评分
        results["overall_score"] = self._compute_score(results)

        return results

    def _compute_score(self, results: Dict) -> Dict[str, float]:
        """
        计算因子综合评分

        综合考虑 IC、IR、单调性、持续性等指标。
        """
        score = 0
        details = {}

        # IC 评分 (0-25分)
        ic_mean = abs(results["ic_summary"]["ic_mean"])
        ic_score = min(25, ic_mean * 250)  # IC=0.1 得满分
        details["ic_score"] = ic_score

        # IR 评分 (0-25分)
        ir = abs(results["ir"]) if not np.isnan(results["ir"]) else 0
        ir_score = min(25, ir * 25)  # IR=1.0 得满分
        details["ir_score"] = ir_score

        # 单调性评分 (0-25分)
        mono = abs(results["monotonicity"]) if not np.isnan(results["monotonicity"]) else 0
        mono_score = mono * 25
        details["monotonicity_score"] = mono_score

        # 持续性评分 (0-25分)
        persist = results["persistence_score"] if not np.isnan(results["persistence_score"]) else 0
        persist_score = persist * 25
        details["persistence_score"] = persist_score

        total = ic_score + ir_score + mono_score + persist_score
        details["total"] = total

        # 评级
        if total >= 80:
            details["grade"] = "A (优秀)"
        elif total >= 60:
            details["grade"] = "B (良好)"
        elif total >= 40:
            details["grade"] = "C (一般)"
        else:
            details["grade"] = "D (较差)"

        return details

    @staticmethod
    def print_summary(results: Dict):
        """
        打印回测摘要

        参数:
            results: run() 方法的返回结果
        """
        print("=" * 60)
        print("因子回测报告")
        print("=" * 60)

        # IC 分析
        ic = results["ic_summary"]
        print(f"\n【IC 分析】")
        print(f"  IC 均值:     {ic['ic_mean']:.4f}")
        print(f"  IC 标准差:   {ic['ic_std']:.4f}")
        print(f"  IC_IR:       {ic['ic_ir']:.4f}")
        print(f"  IC > 0 比例: {ic['ic_pos_pct']:.2%}")
        print(f"  t 统计量:    {ic['t_stat']:.4f}")
        print(f"  p 值:        {ic['p_value']:.4f}")

        # 分组回测
        print(f"\n【分组回测】")
        stats = results["group_stats"]
        for g in stats.index:
            row = stats.loc[g]
            print(f"  G{g}: 年化收益={row['annualized_return']:.2%}, "
                  f"夏普={row['sharpe_ratio']:.2f}, "
                  f"最大回撤={row['max_drawdown']:.2%}")

        print(f"  多空年化收益: {stats.loc[self.n_groups, 'annualized_return'] - stats.loc[1, 'annualized_return']:.2%}")
        print(f"  单调性:       {results['monotonicity']:.4f}")

        # 衰减分析
        print(f"\n【衰减分析】")
        print(f"  半衰期:       {results['half_life']} 天")
        print(f"  最优持仓期:   {results['optimal_holding']} 天")
        print(f"  持续性评分:   {results['persistence_score']:.4f}")

        # 综合评分
        score = results["overall_score"]
        print(f"\n【综合评分】")
        print(f"  IC 评分:       {score['ic_score']:.1f}/25")
        print(f"  IR 评分:       {score['ir_score']:.1f}/25")
        print(f"  单调性评分:    {score['monotonicity_score']:.1f}/25")
        print(f"  持续性评分:    {score['persistence_score']:.1f}/25")
        print(f"  总分:          {score['total']:.1f}/100")
        print(f"  评级:          {score['grade']}")
        print("=" * 60)
