"""
日志工具模块

本模块提供统一的日志记录功能。
"""

import logging
import sys
import json
import os
from typing import Dict, Any, Optional
from datetime import datetime


def setup_logging(
    log_file: Optional[str] = None,
    level: int = logging.INFO,
    rank: int = 0,
) -> logging.Logger:
    """
    设置日志记录器

    Args:
        log_file: 日志文件路径（可选）
        level: 日志级别
        rank: 当前进程 rank（只有 rank 0 会输出到控制台）

    Returns:
        Logger 实例
    """
    # 创建 logger
    logger = logging.getLogger("finetune_rl")
    logger.setLevel(level)

    # 清除已有的 handler
    logger.handlers.clear()

    # 日志格式
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # 控制台 handler（只有 rank 0）
    if rank == 0:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    # 文件 handler（可选）
    if log_file:
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


def log_metrics(
    metrics: Dict[str, Any],
    step: int,
    logger: Optional[logging.Logger] = None,
    log_file: Optional[str] = None,
):
    """
    记录训练指标

    Args:
        metrics: 指标字典
        step: 当前步数
        logger: Logger 实例
        log_file: 指标日志文件路径
    """
    # 格式化指标
    formatted = {k: f"{v:.4f}" if isinstance(v, float) else str(v) for k, v in metrics.items()}
    message = f"Step {step}: " + ", ".join(f"{k}={v}" for k, v in formatted.items())

    # 记录到 logger
    if logger:
        logger.info(message)

    # 记录到文件（JSON Lines 格式）
    if log_file:
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        record = {"step": step, "timestamp": datetime.now().isoformat(), **metrics}
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")


class MetricsTracker:
    """
    指标追踪器

    用于追踪和汇总训练过程中的指标
    """

    def __init__(self):
        self.metrics = {}
        self.history = {}

    def update(self, metrics: Dict[str, float], step: int):
        """
        更新指标

        Args:
            metrics: 指标字典
            step: 当前步数
        """
        for key, value in metrics.items():
            if key not in self.metrics:
                self.metrics[key] = []
                self.history[key] = []

            self.metrics[key].append(value)
            self.history[key].append({"step": step, "value": value})

    def get_latest(self, key: str) -> Optional[float]:
        """获取最新的指标值"""
        if key in self.metrics and self.metrics[key]:
            return self.metrics[key][-1]
        return None

    def get_mean(self, key: str, last_n: Optional[int] = None) -> Optional[float]:
        """获取指标的均值"""
        if key not in self.metrics or not self.metrics[key]:
            return None

        values = self.metrics[key]
        if last_n is not None:
            values = values[-last_n:]

        return sum(values) / len(values)

    def get_summary(self) -> Dict[str, Dict[str, float]]:
        """获取指标摘要"""
        summary = {}
        for key, values in self.metrics.items():
            if values:
                summary[key] = {
                    "latest": values[-1],
                    "mean": sum(values) / len(values),
                    "min": min(values),
                    "max": max(values),
                    "count": len(values),
                }
        return summary

    def reset(self):
        """重置指标"""
        for key in self.metrics:
            self.metrics[key] = []

    def save(self, file_path: str):
        """保存指标历史"""
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(self.history, f, ensure_ascii=False, indent=2)

    def load(self, file_path: str):
        """加载指标历史"""
        with open(file_path, "r", encoding="utf-8") as f:
            self.history = json.load(f)

        # 重建 metrics
        self.metrics = {}
        for key, records in self.history.items():
            self.metrics[key] = [r["value"] for r in records]
