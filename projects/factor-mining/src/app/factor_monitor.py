"""
因子监控模块

实时监控因子的健康状态，包括 IC 趋势、覆盖率、异常检测等。
"""

import numpy as np
import pandas as pd
from typing import Optional, Dict, List
from datetime import datetime


class FactorMonitor:
    """
    因子监控器

    监控因子的各项健康指标，及时发现因子失效或异常。

    使用示例:
        >>> monitor = FactorMonitor()
        >>> status = monitor.check_health("momentum", ic_series, factor_data)
        >>> monitor.get_alerts()
    """

    def __init__(self, ic_threshold: float = 0.02,
                 coverage_threshold: float = 0.8,
                 drift_threshold: float = 2.0):
        """
        初始化因子监控器

        参数:
            ic_threshold: IC 告警阈值
            coverage_threshold: 覆盖率告警阈值
            drift_threshold: 因子漂移告警阈值 (标准差倍数)
        """
        self.ic_threshold = ic_threshold
        self.coverage_threshold = coverage_threshold
        self.drift_threshold = drift_threshold
        self.alerts = []

    def check_health(self, factor_name: str,
                      ic_series: pd.Series,
                      factor_data: pd.DataFrame,
                      lookback: int = 20) -> Dict:
        """
        检查因子健康状态

        参数:
            factor_name: 因子名称
            ic_series: IC 时间序列
            factor_data: 最新因子数据
            lookback: 回看窗口

        返回:
            健康状态字典
        """
        status = {
            "factor_name": factor_name,
            "check_time": datetime.now().isoformat(),
            "alerts": [],
            "status": "healthy",
        }

        # 1. IC 趋势检查
        recent_ic = ic_series.tail(lookback)
        ic_mean = recent_ic.mean()
        ic_trend = self._check_ic_trend(ic_series, lookback)

        if abs(ic_mean) < self.ic_threshold:
            status["alerts"].append({
                "level": "warning",
                "type": "ic_low",
                "message": f"近 {lookback} 日 IC 均值过低: {ic_mean:.4f}",
            })

        if ic_trend["trend"] == "declining":
            status["alerts"].append({
                "level": "warning",
                "type": "ic_declining",
                "message": f"IC 呈下降趋势，斜率: {ic_trend['slope']:.4f}",
            })

        # 2. 覆盖率检查
        coverage = factor_data.notna().mean().mean()
        if coverage < self.coverage_threshold:
            status["alerts"].append({
                "level": "critical",
                "type": "low_coverage",
                "message": f"因子覆盖率过低: {coverage:.2%}",
            })

        # 3. 因子分布检查
        distribution = self._check_distribution(factor_data)
        if distribution["is_drifted"]:
            status["alerts"].append({
                "level": "warning",
                "type": "distribution_drift",
                "message": f"因子分布漂移，z-score: {distribution['drift_score']:.2f}",
            })

        # 4. 更新状态
        critical_alerts = [a for a in status["alerts"] if a["level"] == "critical"]
        warning_alerts = [a for a in status["alerts"] if a["level"] == "warning"]

        if critical_alerts:
            status["status"] = "critical"
        elif warning_alerts:
            status["status"] = "warning"

        status["metrics"] = {
            "recent_ic_mean": ic_mean,
            "coverage": coverage,
            "factor_mean": factor_data.mean().mean(),
            "factor_std": factor_data.std().mean(),
        }

        # 记录告警
        for alert in status["alerts"]:
            self.alerts.append({**alert, "factor_name": factor_name,
                                "time": datetime.now().isoformat()})

        return status

    def _check_ic_trend(self, ic_series: pd.Series,
                         lookback: int) -> Dict:
        """检查 IC 趋势"""
        recent = ic_series.tail(lookback).dropna()
        if len(recent) < 5:
            return {"trend": "unknown", "slope": 0}

        x = np.arange(len(recent))
        slope = np.polyfit(x, recent.values, 1)[0]

        if slope < -0.001:
            trend = "declining"
        elif slope > 0.001:
            trend = "improving"
        else:
            trend = "stable"

        return {"trend": trend, "slope": slope}

    def _check_distribution(self, factor_data: pd.DataFrame) -> Dict:
        """检查因子分布是否漂移"""
        latest = factor_data.iloc[-1].dropna()
        historical = factor_data.iloc[:-1]

        if len(historical) < 20:
            return {"is_drifted": False, "drift_score": 0}

        hist_mean = historical.mean().mean()
        hist_std = historical.std().mean()

        if hist_std == 0:
            return {"is_drifted": False, "drift_score": 0}

        drift_score = abs(latest.mean() - hist_mean) / hist_std
        return {
            "is_drifted": drift_score > self.drift_threshold,
            "drift_score": drift_score,
        }

    def get_alerts(self, factor_name: Optional[str] = None,
                    level: Optional[str] = None) -> List[Dict]:
        """
        获取告警列表

        参数:
            factor_name: 按因子名筛选
            level: 按告警级别筛选

        返回:
            告警列表
        """
        filtered = self.alerts
        if factor_name:
            filtered = [a for a in filtered if a["factor_name"] == factor_name]
        if level:
            filtered = [a for a in filtered if a["level"] == level]
        return filtered

    def generate_status_report(self, statuses: List[Dict]) -> str:
        """
        生成状态报告

        参数:
            statuses: 各因子的健康状态列表

        返回:
            报告文本
        """
        lines = ["=" * 50, "因子健康状态报告", "=" * 50, ""]

        for status in statuses:
            icon = {"healthy": "[OK]", "warning": "[!]", "critical": "[X]"}
            icon_str = icon.get(status["status"], "[?]")
            lines.append(f"{icon_str} {status['factor_name']}: {status['status']}")

            if status["alerts"]:
                for alert in status["alerts"]:
                    lines.append(f"    - {alert['message']}")

        healthy_count = sum(1 for s in statuses if s["status"] == "healthy")
        lines.append("")
        lines.append(f"总计: {len(statuses)} 个因子, "
                      f"{healthy_count} 个健康, "
                      f"{len(statuses) - healthy_count} 个异常")

        return "\n".join(lines)
