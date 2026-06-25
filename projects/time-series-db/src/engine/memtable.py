"""
内存表 (MemTable)

使用有序数据结构实现高性能的内存数据存储。
支持快速插入、查询和范围查询。
"""

import threading
import sys
from typing import List, Dict, Tuple, Optional, Any
from sortedcontainers import SortedDict


class MemTable:
    """
    内存表实现

    使用 SortedDict 作为底层数据结构，保证数据按时间戳排序。
    支持并发读写，达到容量上限后触发刷盘。

    数据格式:
        key: (metric, frozenset(tags.items()), timestamp)
        value: (value, sequence_number)
    """

    def __init__(self, max_size: int = 64 * 1024 * 1024):
        """
        初始化内存表

        Args:
            max_size: 最大容量（字节），默认 64MB
        """
        self.data = SortedDict()
        self.size = 0
        self.max_size = max_size
        self.lock = threading.RLock()
        self.sequence = 0  # 用于处理相同时间戳的数据

    def put(self, metric: str, tags: Dict[str, str], timestamp: int, value: float) -> bool:
        """
        写入单个数据点

        Args:
            metric: 指标名称
            tags: 标签字典
            timestamp: 时间戳（秒）
            value: 数据值

        Returns:
            bool: 是否写入成功
        """
        key = (metric, frozenset(tags.items()), timestamp)
        self.sequence += 1

        with self.lock:
            # 如果 key 已存在，更新大小
            if key in self.data:
                old_size = self._estimate_value_size(self.data[key])
                self.size -= old_size

            self.data[key] = (value, self.sequence)
            self.size += self._estimate_key_size(key) + self._estimate_value_size((value, self.sequence))

            return True

    def put_batch(self, points: List[Dict[str, Any]]) -> int:
        """
        批量写入数据点

        Args:
            points: 数据点列表，每个点包含 metric, tags, timestamp, value

        Returns:
            int: 成功写入的点数
        """
        count = 0
        with self.lock:
            for point in points:
                metric = point['metric']
                tags = point['tags']
                timestamp = point['timestamp']
                value = point['value']

                key = (metric, frozenset(tags.items()), timestamp)
                self.sequence += 1

                if key in self.data:
                    old_size = self._estimate_value_size(self.data[key])
                    self.size -= old_size

                self.data[key] = (value, self.sequence)
                self.size += self._estimate_key_size(key) + self._estimate_value_size((value, self.sequence))
                count += 1

        return count

    def get(self, metric: str, tags: Dict[str, str], timestamp: int) -> Optional[float]:
        """
        获取单个数据点

        Args:
            metric: 指标名称
            tags: 标签字典
            timestamp: 时间戳

        Returns:
            Optional[float]: 数据值，不存在返回 None
        """
        key = (metric, frozenset(tags.items()), timestamp)
        with self.lock:
            result = self.data.get(key)
            return result[0] if result else None

    def range_query(
        self,
        metric: str,
        start: int,
        end: int,
        tags: Optional[Dict[str, str]] = None
    ) -> List[Tuple[int, float]]:
        """
        范围查询

        Args:
            metric: 指标名称
            start: 开始时间戳
            end: 结束时间戳
            tags: 标签过滤（可选）

        Returns:
            List[Tuple[int, float]]: (timestamp, value) 列表
        """
        results = []
        tag_set = frozenset(tags.items()) if tags else None

        with self.lock:
            for key, (value, _) in self.data.items():
                m, t, ts = key
                if m != metric:
                    continue
                if ts < start:
                    continue
                if ts > end:
                    break  # 已排序，后续时间戳更大
                if tag_set and not tag_set.issubset(t):
                    continue
                results.append((ts, value))

        return results

    def latest(self, metric: str, tags: Optional[Dict[str, str]] = None) -> Optional[Tuple[int, float]]:
        """
        获取最新数据点

        Args:
            metric: 指标名称
            tags: 标签过滤（可选）

        Returns:
            Optional[Tuple[int, float]]: (timestamp, value)，不存在返回 None
        """
        tag_set = frozenset(tags.items()) if tags else None

        with self.lock:
            # 从后向前遍历
            for key, (value, _) in reversed(self.data.items()):
                m, t, ts = key
                if m != metric:
                    continue
                if tag_set and not tag_set.issubset(t):
                    continue
                return (ts, value)

        return None

    def delete_before(self, metric: str, before_timestamp: int) -> int:
        """
        删除指定时间之前的数据

        Args:
            metric: 指标名称
            before_timestamp: 时间戳阈值

        Returns:
            int: 删除的数据点数量
        """
        count = 0
        keys_to_delete = []

        with self.lock:
            for key in self.data.keys():
                m, t, ts = key
                if m == metric and ts < before_timestamp:
                    keys_to_delete.append(key)
                elif m == metric and ts >= before_timestamp:
                    break  # 已排序，后续时间戳更大

            for key in keys_to_delete:
                value = self.data.pop(key)
                self.size -= self._estimate_key_size(key) + self._estimate_value_size(value)
                count += 1

        return count

    def is_full(self) -> bool:
        """检查内存表是否已满"""
        with self.lock:
            return self.size >= self.max_size

    def get_size(self) -> int:
        """获取当前内存表大小"""
        with self.lock:
            return self.size

    def get_count(self) -> int:
        """获取数据点数量"""
        with self.lock:
            return len(self.data)

    def clear(self) -> None:
        """清空内存表"""
        with self.lock:
            self.data.clear()
            self.size = 0
            self.sequence = 0

    def get_all(self) -> List[Tuple[str, Dict[str, str], int, float]]:
        """
        获取所有数据（用于刷盘）

        Returns:
            List[Tuple[str, Dict, int, float]]: (metric, tags, timestamp, value) 列表
        """
        results = []
        with self.lock:
            for key, (value, _) in self.data.items():
                metric, tag_set, timestamp = key
                tags = dict(tag_set)
                results.append((metric, tags, timestamp, value))
        return results

    def _estimate_key_size(self, key: Tuple) -> int:
        """估算 key 的内存占用"""
        metric, tag_set, timestamp = key
        size = sys.getsizeof(metric)
        for k, v in tag_set:
            size += sys.getsizeof(k) + sys.getsizeof(v)
        size += sys.getsizeof(timestamp)
        return size

    def _estimate_value_size(self, value: Tuple) -> int:
        """估算 value 的内存占用"""
        return sys.getsizeof(value[0]) + sys.getsizeof(value[1])

    def __len__(self) -> int:
        return self.get_count()

    def __contains__(self, key: Tuple) -> bool:
        return key in self.data
