"""数据处理模块 - 数据过滤、聚合和规则引擎"""

import time
import re
from abc import ABC, abstractmethod
from enum import Enum
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Union
from collections import defaultdict


class FilterOperator(Enum):
    """过滤操作符"""
    EQ = "eq"          # 等于
    NEQ = "neq"        # 不等于
    GT = "gt"          # 大于
    GTE = "gte"        # 大于等于
    LT = "lt"          # 小于
    LTE = "lte"        # 小于等于
    IN = "in"          # 在列表中
    NOT_IN = "not_in"  # 不在列表中
    CONTAINS = "contains"  # 包含
    REGEX = "regex"    # 正则匹配


class AggregationType(Enum):
    """聚合类型"""
    COUNT = "count"    # 计数
    SUM = "sum"        # 求和
    AVG = "avg"        # 平均值
    MIN = "min"        # 最小值
    MAX = "max"        # 最大值
    FIRST = "first"    # 第一个值
    LAST = "last"      # 最后一个值
    STDDEV = "stddev"  # 标准差


class RuleAction(Enum):
    """规则动作"""
    FORWARD = "forward"      # 转发数据
    DROP = "drop"            # 丢弃数据
    TRANSFORM = "transform"  # 转换数据
    ALERT = "alert"          # 触发告警
    AGGREGATE = "aggregate"  # 聚合数据


@dataclass
class DataPoint:
    """数据点"""
    timestamp: float
    source: str
    metric: str
    value: Any
    tags: Dict[str, str] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "source": self.source,
            "metric": self.metric,
            "value": self.value,
            "tags": self.tags,
            "metadata": self.metadata,
        }


@dataclass
class FilterRule:
    """过滤规则"""
    field: str
    operator: FilterOperator
    value: Any
    negate: bool = False

    def matches(self, data_point: DataPoint) -> bool:
        """检查数据点是否匹配规则"""
        # 获取字段值
        field_value = self._get_field_value(data_point)
        if field_value is None:
            return self.negate

        # 执行比较
        result = self._compare(field_value)
        return not result if self.negate else result

    def _get_field_value(self, data_point: DataPoint) -> Any:
        """获取数据点的字段值"""
        if self.field == "value":
            return data_point.value
        elif self.field == "source":
            return data_point.source
        elif self.field == "metric":
            return data_point.metric
        elif self.field.startswith("tags."):
            tag_key = self.field[5:]
            return data_point.tags.get(tag_key)
        elif self.field.startswith("metadata."):
            meta_key = self.field[9:]
            return data_point.metadata.get(meta_key)
        return None

    def _compare(self, field_value: Any) -> bool:
        """执行比较操作"""
        try:
            if self.operator == FilterOperator.EQ:
                return field_value == self.value
            elif self.operator == FilterOperator.NEQ:
                return field_value != self.value
            elif self.operator == FilterOperator.GT:
                return float(field_value) > float(self.value)
            elif self.operator == FilterOperator.GTE:
                return float(field_value) >= float(self.value)
            elif self.operator == FilterOperator.LT:
                return float(field_value) < float(self.value)
            elif self.operator == FilterOperator.LTE:
                return float(field_value) <= float(self.value)
            elif self.operator == FilterOperator.IN:
                return field_value in self.value
            elif self.operator == FilterOperator.NOT_IN:
                return field_value not in self.value
            elif self.operator == FilterOperator.CONTAINS:
                return str(self.value) in str(field_value)
            elif self.operator == FilterOperator.REGEX:
                return bool(re.search(str(self.value), str(field_value)))
        except (TypeError, ValueError):
            return False
        return False


class DataFilter:
    """数据过滤器

    支持多种过滤规则的组合，用于筛选边缘设备产生的数据。
    """

    def __init__(self, name: str = "default"):
        self.name = name
        self._rules: List[FilterRule] = []
        self._match_all = True  # True=AND, False=OR

    def add_rule(self, rule: FilterRule) -> "DataFilter":
        """添加过滤规则"""
        self._rules.append(rule)
        return self

    def set_match_mode(self, match_all: bool) -> "DataFilter":
        """设置匹配模式 (AND/OR)"""
        self._match_all = match_all
        return self

    def filter(self, data_points: List[DataPoint]) -> List[DataPoint]:
        """过滤数据点列表"""
        return [dp for dp in data_points if self.matches(dp)]

    def matches(self, data_point: DataPoint) -> bool:
        """检查单个数据点是否匹配所有规则"""
        if not self._rules:
            return True

        if self._match_all:
            return all(rule.matches(data_point) for rule in self._rules)
        else:
            return any(rule.matches(data_point) for rule in self._rules)

    def clear_rules(self) -> None:
        """清空所有规则"""
        self._rules.clear()


class DataAggregator:
    """数据聚合器

    支持按时间窗口、标签等维度聚合数据。
    """

    def __init__(self, window_size: float = 60.0):
        self.window_size = window_size  # 时间窗口大小（秒）
        self._buffer: Dict[str, List[DataPoint]] = defaultdict(list)

    def add(self, data_point: DataPoint) -> None:
        """添加数据点到缓冲区"""
        key = f"{data_point.source}:{data_point.metric}"
        self._buffer[key].append(data_point)
        self._cleanup(key)

    def _cleanup(self, key: str) -> None:
        """清理过期数据"""
        cutoff = time.time() - self.window_size
        self._buffer[key] = [
            dp for dp in self._buffer[key]
            if dp.timestamp >= cutoff
        ]

    def aggregate(
        self,
        aggregation_type: AggregationType,
        source: Optional[str] = None,
        metric: Optional[str] = None,
    ) -> Dict[str, Any]:
        """执行聚合计算"""
        results = {}

        for key, points in self._buffer.items():
            parts = key.split(":")
            if len(parts) != 2:
                continue

            src, met = parts
            if source and src != source:
                continue
            if metric and met != metric:
                continue

            if not points:
                continue

            values = [p.value for p in points if isinstance(p.value, (int, float))]
            if not values:
                continue

            result_key = key
            if aggregation_type == AggregationType.COUNT:
                results[result_key] = len(points)
            elif aggregation_type == AggregationType.SUM:
                results[result_key] = sum(values)
            elif aggregation_type == AggregationType.AVG:
                results[result_key] = sum(values) / len(values)
            elif aggregation_type == AggregationType.MIN:
                results[result_key] = min(values)
            elif aggregation_type == AggregationType.MAX:
                results[result_key] = max(values)
            elif aggregation_type == AggregationType.FIRST:
                results[result_key] = values[0]
            elif aggregation_type == AggregationType.LAST:
                results[result_key] = values[-1]
            elif aggregation_type == AggregationType.STDDEV:
                if len(values) > 1:
                    mean = sum(values) / len(values)
                    variance = sum((x - mean) ** 2 for x in values) / (len(values) - 1)
                    results[result_key] = variance ** 0.5
                else:
                    results[result_key] = 0.0

        return results

    def get_window_data(
        self,
        source: Optional[str] = None,
        metric: Optional[str] = None,
    ) -> List[DataPoint]:
        """获取时间窗口内的数据"""
        result = []
        for key, points in self._buffer.items():
            parts = key.split(":")
            if len(parts) != 2:
                continue

            src, met = parts
            if source and src != source:
                continue
            if metric and met != metric:
                continue

            result.extend(points)

        return sorted(result, key=lambda p: p.timestamp)

    def clear(self) -> None:
        """清空缓冲区"""
        self._buffer.clear()


@dataclass
class Rule:
    """处理规则"""
    rule_id: str
    name: str
    description: str = ""
    conditions: List[FilterRule] = field(default_factory=list)
    action: RuleAction = RuleAction.FORWARD
    action_params: Dict[str, Any] = field(default_factory=dict)
    priority: int = 0
    enabled: bool = True

    def evaluate(self, data_point: DataPoint) -> bool:
        """评估规则条件"""
        if not self.enabled:
            return False

        if not self.conditions:
            return True

        return all(cond.matches(data_point) for cond in self.conditions)


class RuleEngine:
    """规则引擎

    根据预定义规则处理边缘数据，支持转发、丢弃、转换、告警等操作。
    """

    def __init__(self):
        self._rules: List[Rule] = []
        self._handlers: Dict[RuleAction, Callable] = {
            RuleAction.FORWARD: self._handle_forward,
            RuleAction.DROP: self._handle_drop,
            RuleAction.TRANSFORM: self._handle_transform,
            RuleAction.ALERT: self._handle_alert,
            RuleAction.AGGREGATE: self._handle_aggregate,
        }
        self._alert_callbacks: List[Callable] = []
        self._stats = defaultdict(int)

    def add_rule(self, rule: Rule) -> None:
        """添加规则"""
        self._rules.append(rule)
        self._rules.sort(key=lambda r: r.priority, reverse=True)

    def remove_rule(self, rule_id: str) -> bool:
        """移除规则"""
        for i, rule in enumerate(self._rules):
            if rule.rule_id == rule_id:
                self._rules.pop(i)
                return True
        return False

    def register_alert_callback(self, callback: Callable) -> None:
        """注册告警回调"""
        self._alert_callbacks.append(callback)

    def process(self, data_point: DataPoint) -> Optional[DataPoint]:
        """处理单个数据点"""
        for rule in self._rules:
            if rule.evaluate(data_point):
                self._stats[f"rule_{rule.rule_id}_triggered"] += 1
                handler = self._handlers.get(rule.action)
                if handler:
                    return handler(data_point, rule)

        # 没有匹配规则，默认转发
        self._stats["default_forward"] += 1
        return data_point

    def process_batch(self, data_points: List[DataPoint]) -> List[DataPoint]:
        """批量处理数据点"""
        results = []
        for dp in data_points:
            result = self.process(dp)
            if result is not None:
                results.append(result)
        return results

    def _handle_forward(self, data_point: DataPoint, rule: Rule) -> DataPoint:
        """处理转发动作"""
        self._stats["forwarded"] += 1
        return data_point

    def _handle_drop(self, data_point: DataPoint, rule: Rule) -> Optional[DataPoint]:
        """处理丢弃动作"""
        self._stats["dropped"] += 1
        return None

    def _handle_transform(self, data_point: DataPoint, rule: Rule) -> DataPoint:
        """处理转换动作"""
        self._stats["transformed"] += 1

        # 应用转换参数
        transform_type = rule.action_params.get("type")
        if transform_type == "scale":
            factor = rule.action_params.get("factor", 1.0)
            if isinstance(data_point.value, (int, float)):
                data_point.value *= factor
        elif transform_type == "offset":
            offset = rule.action_params.get("offset", 0)
            if isinstance(data_point.value, (int, float)):
                data_point.value += offset
        elif transform_type == "rename_metric":
            new_name = rule.action_params.get("new_name")
            if new_name:
                data_point.metric = new_name
        elif transform_type == "add_tag":
            tag_key = rule.action_params.get("key")
            tag_value = rule.action_params.get("value")
            if tag_key:
                data_point.tags[tag_key] = tag_value

        return data_point

    def _handle_alert(self, data_point: DataPoint, rule: Rule) -> DataPoint:
        """处理告警动作"""
        self._stats["alerts"] += 1

        alert_info = {
            "rule_id": rule.rule_id,
            "rule_name": rule.name,
            "data_point": data_point.to_dict(),
            "timestamp": time.time(),
            "params": rule.action_params,
        }

        for callback in self._alert_callbacks:
            try:
                callback(alert_info)
            except Exception:
                pass

        return data_point

    def _handle_aggregate(self, data_point: DataPoint, rule: Rule) -> DataPoint:
        """处理聚合动作（由外部聚合器处理）"""
        self._stats["aggregate_requested"] += 1
        return data_point

    def get_stats(self) -> Dict[str, Any]:
        """获取规则引擎统计"""
        return {
            "total_rules": len(self._rules),
            "enabled_rules": sum(1 for r in self._rules if r.enabled),
            "stats": dict(self._stats),
        }

    def get_rules(self) -> List[Dict[str, Any]]:
        """获取所有规则"""
        return [
            {
                "rule_id": r.rule_id,
                "name": r.name,
                "description": r.description,
                "action": r.action.value,
                "priority": r.priority,
                "enabled": r.enabled,
                "conditions_count": len(r.conditions),
            }
            for r in self._rules
        ]
