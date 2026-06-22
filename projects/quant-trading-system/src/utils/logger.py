"""
日志工具 - 统一的日志管理

⭐ 重点理解：日志的重要性
- 调试：追踪程序执行流程
- 审计：记录交易历史
- 监控：实时观察系统状态

💡 值得思考：
- 日志级别如何划分？
- 如何实现日志的持久化？
- 如何实现日志的实时查看？
"""

import logging
from datetime import datetime
from typing import Optional


class TradingLogger:
    """
    交易日志器

    ⭐ 重点：日志器的设计
    - 支持不同日志级别
    - 支持控制台和文件输出
    - 支持结构化日志
    """

    def __init__(self, name: str = "quant_trading", level: str = "INFO"):
        """
        初始化日志器

        Args:
            name: 日志器名称
            level: 日志级别
        """
        self.logger = logging.getLogger(name)
        self.logger.setLevel(getattr(logging, level.upper()))

        # 避免重复添加处理器
        if not self.logger.handlers:
            self._setup_handlers()

    def _setup_handlers(self) -> None:
        """设置日志处理器"""
        # 控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)

        # 格式化器
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_handler.setFormatter(formatter)

        self.logger.addHandler(console_handler)

    def info(self, message: str) -> None:
        """记录信息日志"""
        self.logger.info(message)

    def warning(self, message: str) -> None:
        """记录警告日志"""
        self.logger.warning(message)

    def error(self, message: str) -> None:
        """记录错误日志"""
        self.logger.error(message)

    def debug(self, message: str) -> None:
        """记录调试日志"""
        self.logger.debug(message)

    def trade(self, message: str) -> None:
        """
        记录交易日志

        💡 值得思考：交易日志需要记录哪些信息？
        - 时间戳
        - 标的
        - 方向
        - 价格
        - 数量
        - 原因
        """
        self.logger.info(f"[TRADE] {message}")

    def risk(self, message: str) -> None:
        """记录风险日志"""
        self.logger.warning(f"[RISK] {message}")

    def performance(self, message: str) -> None:
        """记录性能日志"""
        self.logger.info(f"[PERF] {message}")


# 全局日志器实例
logger = TradingLogger()
