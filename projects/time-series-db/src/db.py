"""
时间序列数据库主入口

提供统一的 API 接口，整合所有模块。
"""

import time
import logging
from typing import List, Dict, Tuple, Optional, Any
from pathlib import Path

from .engine.storage import StorageEngine
from .query.executor import QueryExecutor, QueryRequest, QueryResponse, BatchQueryRequest, BatchQueryResponse
from .query.aggregation import Aggregator
from .query.downsampling import Downsampler
from .retention.ttl import TTLManager

logger = logging.getLogger(__name__)


class TimeSeriesDB:
    """
    时间序列数据库

    主要功能:
    - 数据写入（单点/批量）
    - 数据查询（范围/聚合/降采样）
    - 数据保留（TTL/自动清理）
    """

    def __init__(
        self,
        data_dir: str = './data',
        default_ttl: Optional[int] = None,
        memtable_max_size: int = 64 * 1024 * 1024,
        flush_interval: int = 60,
        cleanup_interval: int = 3600,
        auto_start_cleanup: bool = True
    ):
        """
        初始化数据库

        Args:
            data_dir: 数据目录
            default_ttl: 默认 TTL（秒），None 表示不过期
            memtable_max_size: 内存表最大大小（字节）
            flush_interval: 刷盘间隔（秒）
            cleanup_interval: 清理间隔（秒）
            auto_start_cleanup: 是否自动启动清理线程
        """
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)

        # 初始化存储引擎
        config = {
            'memtable_max_size': memtable_max_size,
            'flush_interval': flush_interval,
        }
        self.storage = StorageEngine(str(self.data_dir), config)

        # 从 WAL 恢复数据
        self.storage.recover()

        # 初始化查询执行器
        self.query_executor = QueryExecutor(self.storage)

        # 初始化 TTL 管理器
        self.ttl_manager = TTLManager(
            storage_engine=self.storage,
            default_ttl=default_ttl,
            cleanup_interval=cleanup_interval,
            config_file=str(self.data_dir / 'ttl_config.json')
        )

        # 启动自动清理
        if auto_start_cleanup and default_ttl is not None:
            self.ttl_manager.start()

        logger.info(f"TimeSeriesDB initialized, data_dir: {data_dir}")

    def write(
        self,
        metric: str,
        tags: Dict[str, str],
        timestamp: int,
        value: float
    ) -> bool:
        """
        写入单个数据点

        Args:
            metric: 指标名称
            tags: 标签字典
            timestamp: 时间戳（秒）
            value: 数据值

        Returns:
            bool: 是否写入成功

        Example:
            >>> db.write(
            ...     metric="cpu_usage",
            ...     tags={"host": "server1"},
            ...     timestamp=1625097600,
            ...     value=45.2
            ... )
        """
        return self.storage.write(metric, tags, timestamp, value)

    def write_batch(self, points: List[Dict[str, Any]]) -> int:
        """
        批量写入数据点

        Args:
            points: 数据点列表，每个点包含:
                - metric (str): 指标名称
                - tags (Dict[str, str]): 标签
                - timestamp (int): 时间戳
                - value (float): 值

        Returns:
            int: 成功写入的点数

        Example:
            >>> db.write_batch([
            ...     {"metric": "cpu", "tags": {"host": "s1"}, "timestamp": 1000, "value": 45.2},
            ...     {"metric": "cpu", "tags": {"host": "s1"}, "timestamp": 1060, "value": 46.8},
            ... ])
        """
        return self.storage.write_batch(points)

    def query(
        self,
        metric: str,
        start: int,
        end: int,
        tags: Optional[Dict[str, str]] = None,
        aggregation: Optional[str] = None,
        downsample: Optional[str] = None,
        fill: Optional[str] = None,
        limit: Optional[int] = None,
        order: str = 'asc'
    ) -> List[Tuple[int, float]]:
        """
        查询数据

        Args:
            metric: 指标名称
            start: 开始时间戳
            end: 结束时间戳
            tags: 标签过滤
            aggregation: 聚合函数 (avg/max/min/sum/count/first/last/stddev)
            downsample: 降采样间隔 (1s/1m/1h/1d)
            fill: 填充策略 (null/0/prev/next)
            limit: 返回数量限制
            order: 排序方式 (asc/desc)

        Returns:
            List[Tuple[int, float]]: (timestamp, value) 列表

        Example:
            >>> # 查询最近 1 小时的数据
            >>> results = db.query(
            ...     metric="cpu_usage",
            ...     start=1625097600,
            ...     end=1625101200
            ... )
            >>>
            >>> # 查询并聚合
            >>> avg = db.query(
            ...     metric="cpu_usage",
            ...     start=1625097600,
            ...     end=1625101200,
            ...     aggregation="avg"
            ... )
            >>>
            >>> # 降采样查询
            >>> results = db.query(
            ...     metric="cpu_usage",
            ...     start=1625097600,
            ...     end=1625101200,
            ...     downsample="5m",
            ...     aggregation="avg"
            ... )
        """
        request = QueryRequest(
            metric=metric,
            start=start,
            end=end,
            tags=tags,
            aggregation=aggregation,
            downsample=downsample,
            fill=fill,
            limit=limit,
            order=order
        )
        response = self.query_executor.execute(request)
        return response.points

    def query_with_request(self, request: QueryRequest) -> QueryResponse:
        """
        使用 QueryRequest 对象查询

        Args:
            request: 查询请求对象

        Returns:
            QueryResponse: 查询响应对象
        """
        return self.query_executor.execute(request)

    def query_batch(self, request: BatchQueryRequest) -> BatchQueryResponse:
        """
        批量查询

        Args:
            request: 批量查询请求

        Returns:
            BatchQueryResponse: 批量查询响应
        """
        return self.query_executor.execute_batch(request)

    def latest(
        self,
        metric: str,
        tags: Optional[Dict[str, str]] = None
    ) -> Optional[Tuple[int, float]]:
        """
        获取最新数据点

        Args:
            metric: 指标名称
            tags: 标签过滤

        Returns:
            Optional[Tuple[int, float]]: (timestamp, value)

        Example:
            >>> result = db.latest("cpu_usage", {"host": "server1"})
            >>> if result:
            ...     timestamp, value = result
        """
        return self.query_executor.latest(metric, tags)

    def metrics(self) -> List[str]:
        """
        获取所有指标名称

        Returns:
            List[str]: 指标名称列表
        """
        return self.query_executor.metrics()

    def tag_keys(self, metric: str) -> List[str]:
        """
        获取指标的所有标签键

        Args:
            metric: 指标名称

        Returns:
            List[str]: 标签键列表
        """
        return self.query_executor.tag_keys(metric)

    def tag_values(self, metric: str, tag_key: str) -> List[str]:
        """
        获取指标的标签值

        Args:
            metric: 指标名称
            tag_key: 标签键

        Returns:
            List[str]: 标签值列表
        """
        return self.query_executor.tag_values(metric, tag_key)

    def set_ttl(self, metric: str, ttl_seconds: int) -> None:
        """
        设置 metric 级别 TTL

        Args:
            metric: 指标名称
            ttl_seconds: TTL 时间（秒）

        Example:
            >>> db.set_ttl("cpu_usage", 86400 * 30)  # 30天
        """
        self.ttl_manager.set_ttl(metric, ttl_seconds)

    def get_ttl(self, metric: str) -> Optional[int]:
        """
        获取 metric 的 TTL

        Args:
            metric: 指标名称

        Returns:
            Optional[int]: TTL 时间（秒）
        """
        return self.ttl_manager.get_ttl(metric)

    def list_ttl_configs(self) -> Dict[str, int]:
        """
        列出所有 TTL 配置

        Returns:
            Dict[str, int]: {metric: ttl_seconds}
        """
        return self.ttl_manager.list_configs()

    def cleanup(self, metric: Optional[str] = None) -> int:
        """
        手动触发清理

        Args:
            metric: 指定 metric，None 表示清理所有

        Returns:
            int: 清理的数据点数量
        """
        return self.ttl_manager.cleanup(metric)

    def flush(self) -> None:
        """手动触发刷盘"""
        self.storage.flush()

    def get_stats(self) -> Dict[str, Any]:
        """
        获取数据库统计信息

        Returns:
            Dict[str, Any]: 统计信息
        """
        storage_stats = self.storage.get_stats()
        ttl_stats = self.ttl_manager.get_stats()

        return {
            'storage': storage_stats,
            'ttl': ttl_stats,
        }

    def close(self) -> None:
        """关闭数据库"""
        logger.info("Closing TimeSeriesDB...")
        self.ttl_manager.stop()
        self.storage.close()
        logger.info("TimeSeriesDB closed")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
