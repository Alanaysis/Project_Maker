"""
因子更新模块

管理因子的增量更新、回溯计算和版本控制。
"""

import numpy as np
import pandas as pd
from datetime import datetime
from typing import Optional, Dict, Callable


class FactorUpdater:
    """
    因子更新器

    管理因子数据的增量更新流程。

    使用示例:
        >>> updater = FactorUpdater()
        >>> updater.update("momentum", new_data, factor_func)
    """

    def __init__(self):
        """初始化因子更新器"""
        self.update_history = []

    def update(self, factor_name: str,
               price_data: pd.DataFrame,
               factor_func: Callable,
               existing_factor: Optional[pd.DataFrame] = None) -> pd.DataFrame:
        """
        增量更新因子

        如果存在已有因子数据，仅计算新数据部分；否则全量计算。

        参数:
            factor_name: 因子名称
            price_data: 最新价格数据
            factor_func: 因子计算函数
            existing_factor: 已有的因子数据

        返回:
            更新后的因子数据
        """
        if existing_factor is not None and not existing_factor.empty:
            # 增量更新: 仅计算新数据
            last_date = existing_factor.index[-1]
            new_data = price_data[price_data.index > last_date]

            if new_data.empty:
                return existing_factor

            # 需要一些历史数据用于计算 (如 MA 需要前面的数据)
            lookback = 60  # 最大回看天数
            overlap_start = max(0, price_data.index.get_loc(last_date) - lookback)
            calc_data = price_data.iloc[overlap_start:]

            new_factor = factor_func(calc_data)
            # 只取新数据部分
            new_factor = new_factor[new_factor.index > last_date]

            # 合并
            updated = pd.concat([existing_factor, new_factor])
        else:
            # 全量计算
            updated = factor_func(price_data)

        # 记录更新历史
        self.update_history.append({
            "factor_name": factor_name,
            "update_time": datetime.now().isoformat(),
            "rows_added": len(updated) - (len(existing_factor) if existing_factor is not None else 0),
            "total_rows": len(updated),
        })

        return updated

    def backfill(self, factor_name: str,
                  price_data: pd.DataFrame,
                  factor_func: Callable,
                  start_date: Optional[str] = None,
                  end_date: Optional[str] = None) -> pd.DataFrame:
        """
        回溯计算因子

        计算历史区间的因子值，用于因子研究和回测。

        参数:
            factor_name: 因子名称
            price_data: 价格数据
            factor_func: 因子计算函数
            start_date: 开始日期
            end_date: 结束日期

        返回:
            历史因子数据
        """
        if start_date:
            price_data = price_data[price_data.index >= start_date]
        if end_date:
            price_data = price_data[price_data.index <= end_date]

        result = factor_func(price_data)

        self.update_history.append({
            "factor_name": factor_name,
            "update_time": datetime.now().isoformat(),
            "type": "backfill",
            "date_range": f"{price_data.index[0]} ~ {price_data.index[-1]}",
            "total_rows": len(result),
        })

        return result

    def get_update_history(self, factor_name: Optional[str] = None) -> pd.DataFrame:
        """
        获取更新历史

        参数:
            factor_name: 因子名称筛选

        返回:
            更新历史 DataFrame
        """
        history = self.update_history
        if factor_name:
            history = [h for h in history if h["factor_name"] == factor_name]
        return pd.DataFrame(history)

    @staticmethod
    def validate_update(old_data: pd.DataFrame,
                         new_data: pd.DataFrame) -> Dict:
        """
        验证更新数据的质量

        参数:
            old_data: 更新前的数据
            new_data: 更新后的数据

        返回:
            验证结果字典
        """
        issues = []

        # 检查数据连续性
        if len(old_data) > 0 and len(new_data) > 0:
            old_end = old_data.index[-1]
            new_start = new_data.index[0]
            if new_start <= old_end:
                issues.append("新数据与旧数据时间重叠")

        # 检查缺失值比例
        missing_rate = new_data.isna().mean().mean()
        if missing_rate > 0.3:
            issues.append(f"新数据缺失值比例过高: {missing_rate:.2%}")

        # 检查数据分布
        if len(old_data) > 0 and len(new_data) > 0:
            old_mean = old_data.mean().mean()
            new_mean = new_data.mean().mean()
            old_std = old_data.std().mean()

            if old_std > 0:
                drift = abs(new_mean - old_mean) / old_std
                if drift > 3:
                    issues.append(f"数据分布漂移严重: z-score = {drift:.2f}")

        return {
            "is_valid": len(issues) == 0,
            "issues": issues,
            "old_rows": len(old_data),
            "new_rows": len(new_data),
            "missing_rate": missing_rate if len(new_data) > 0 else 0,
        }
