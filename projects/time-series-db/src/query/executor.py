"""
查询执行器

处理查询请求，协调存储引擎、聚合和降采样。
"""

import time
from typing import List, Dict, Tuple, Optional, Any
from dataclasses import dataclass, field

from ..engine.storage import StorageEngine
from .aggregation import Aggregator, MultiAggregator
from .downsampling import Downsampler, AdaptiveDownsampler


@dataclass
class QueryRequest:
    """查询请求"""
    metric: str
    start: int
    end: int
    tags: Optional[Dict[str, str]] = None
    aggregation: Optional[str] = None
    downsample: Optional[str] = None
    fill: Optional[str] = None
    limit: Optional[int] = None
    order: str = 'asc'  # 'asc' or 'desc'


@dataclass
class QueryResponse:
    """查询响应"""
    metric: str
    points: List[Tuple[int, float]]
    aggregation: Optional[str] = None
    downsample: Optional[str] = None
    count: int = 0
    execution_time: float = 0.0


@dataclass
class BatchQueryRequest:
    """批量查询请求"""
    queries: List[QueryRequest]


@dataclass
class BatchQueryResponse:
    """批量查询响应"""
    results: List[QueryResponse]
    total_execution_time: float = 0.0


class QueryExecutor:
    """
    查询执行器

    处理查询请求，支持:
    - 时间范围查询
    - 标签过滤
    - 聚合查询
    - 降采样
    - 分页
    """

    def __init__(self, storage_engine: StorageEngine):
        """
        初始化查询执行器

        Args:
            storage_engine: 存储引擎实例
        """
        self.storage = storage_engine
        self.max_points = 1000000  # 最大返回点数

    def execute(self, request: QueryRequest) -> QueryResponse:
        """
        执行查询

        Args:
            request: 查询请求

        Returns:
            QueryResponse: 查询响应
        """
        start_time = time.time()

        # 验证请求
        self._validate_request(request)

        # 从存储引擎查询数据
        points = self.storage.query(
            metric=request.metric,
            start=request.start,
            end=request.end,
            tags=request.tags
        )

        # 应用降采样
        if request.downsample:
            downsampler = Downsampler(
                interval=request.downsample,
                aggregation=request.aggregation or 'avg',
                fill=request.fill
            )
            points = downsampler.downsample(points)
        elif request.aggregation and not request.downsample:
            # 如果只有聚合没有降采样，对整个结果应用聚合
            values = [v for _, v in points]
            if values:
                agg_value = Aggregator.aggregate(values, request.aggregation)
                points = [(request.start, agg_value)]

        # 应用排序
        if request.order == 'desc':
            points = list(reversed(points))

        # 应用分页
        if request.limit and len(points) > request.limit:
            points = points[:request.limit]

        execution_time = time.time() - start_time

        return QueryResponse(
            metric=request.metric,
            points=points,
            aggregation=request.aggregation,
            downsample=request.downsample,
            count=len(points),
            execution_time=execution_time
        )

    def execute_batch(self, request: BatchQueryRequest) -> BatchQueryResponse:
        """
        执行批量查询

        Args:
            request: 批量查询请求

        Returns:
            BatchQueryResponse: 批量查询响应
        """
        start_time = time.time()

        results = []
        for query in request.queries:
            response = self.execute(query)
            results.append(response)

        total_time = time.time() - start_time

        return BatchQueryResponse(
            results=results,
            total_execution_time=total_time
        )

    def latest(self, metric: str, tags: Optional[Dict[str, str]] = None) -> Optional[Tuple[int, float]]:
        """
        获取最新数据点

        Args:
            metric: 指标名称
            tags: 标签过滤

        Returns:
            Optional[Tuple[int, float]]: (timestamp, value)
        """
        return self.storage.latest(metric, tags)

    def metrics(self) -> List[str]:
        """
        获取所有指标名称

        Returns:
            List[str]: 指标名称列表
        """
        metrics = set()

        # 从 SSTable 元数据获取
        for metric in self.storage.sstables.keys():
            metrics.add(metric)

        # 从 MemTable 获取
        data = self.storage.memtable.get_all()
        for metric, _, _, _ in data:
            metrics.add(metric)

        return sorted(list(metrics))

    def tag_keys(self, metric: str) -> List[str]:
        """
        获取指标的所有标签键

        Args:
            metric: 指标名称

        Returns:
            List[str]: 标签键列表
        """
        # 从 MemTable 提取标签键
        tag_keys = set()
        data = self.storage.memtable.get_all()
        for m, tags, _, _ in data:
            if m == metric:
                tag_keys.update(tags.keys())
        return sorted(tag_keys)

    def tag_values(self, metric: str, tag_key: str) -> List[str]:
        """
        获取指标的标签值

        Args:
            metric: 指标名称
            tag_key: 标签键

        Returns:
            List[str]: 标签值列表
        """
        # 从 MemTable 提取标签值
        tag_values = set()
        data = self.storage.memtable.get_all()
        for m, tags, _, _ in data:
            if m == metric and tag_key in tags:
                tag_values.add(tags[tag_key])
        return sorted(tag_values)

    def _validate_request(self, request: QueryRequest) -> None:
        """验证查询请求"""
        if not request.metric:
            raise ValueError("Metric is required")

        if request.start >= request.end:
            raise ValueError("Start must be less than end")

        if request.aggregation and request.aggregation not in Aggregator.list_functions():
            raise ValueError(f"Unknown aggregation function: {request.aggregation}")

        if request.order not in ('asc', 'desc'):
            raise ValueError("Order must be 'asc' or 'desc'")


class QueryBuilder:
    """
    查询构建器

    提供链式 API 构建查询请求。
    """

    def __init__(self, executor: QueryExecutor):
        self.executor = executor
        self._metric = None
        self._start = None
        self._end = None
        self._tags = None
        self._aggregation = None
        self._downsample = None
        self._fill = None
        self._limit = None
        self._order = 'asc'

    def metric(self, metric: str) -> 'QueryBuilder':
        """设置指标名称"""
        self._metric = metric
        return self

    def time_range(self, start: int, end: int) -> 'QueryBuilder':
        """设置时间范围"""
        self._start = start
        self._end = end
        return self

    def last(self, seconds: int) -> 'QueryBuilder':
        """设置最近 N 秒"""
        self._end = int(time.time())
        self._start = self._end - seconds
        return self

    def tag(self, key: str, value: str) -> 'QueryBuilder':
        """添加标签过滤"""
        if self._tags is None:
            self._tags = {}
        self._tags[key] = value
        return self

    def tags(self, tags: Dict[str, str]) -> 'QueryBuilder':
        """设置标签过滤"""
        self._tags = tags
        return self

    def aggregate(self, func: str) -> 'QueryBuilder':
        """设置聚合函数"""
        self._aggregation = func
        return self

    def downsample(self, interval: str, fill: Optional[str] = None) -> 'QueryBuilder':
        """设置降采样"""
        self._downsample = interval
        self._fill = fill
        return self

    def limit(self, limit: int) -> 'QueryBuilder':
        """设置返回数量限制"""
        self._limit = limit
        return self

    def order(self, order: str) -> 'QueryBuilder':
        """设置排序方式"""
        self._order = order
        return self

    def build(self) -> QueryRequest:
        """构建查询请求"""
        if not self._metric:
            raise ValueError("Metric is required")
        if not self._start or not self._end:
            raise ValueError("Time range is required")

        return QueryRequest(
            metric=self._metric,
            start=self._start,
            end=self._end,
            tags=self._tags,
            aggregation=self._aggregation,
            downsample=self._downsample,
            fill=self._fill,
            limit=self._limit,
            order=self._order
        )

    def execute(self) -> QueryResponse:
        """构建并执行查询"""
        request = self.build()
        return self.executor.execute(request)
