"""数据处理模块测试"""

import time
import pytest
from src.data_processor import (
    DataPoint, FilterOperator, AggregationType, RuleAction,
    FilterRule, DataFilter, DataAggregator, Rule, RuleEngine,
)


@pytest.fixture
def sample_data_points():
    """创建测试数据点"""
    now = time.time()
    return [
        DataPoint(
            timestamp=now - 60,
            source="sensor-1",
            metric="temperature",
            value=25.5,
            tags={"location": "room-A"},
        ),
        DataPoint(
            timestamp=now - 30,
            source="sensor-1",
            metric="temperature",
            value=26.0,
            tags={"location": "room-A"},
        ),
        DataPoint(
            timestamp=now,
            source="sensor-2",
            metric="humidity",
            value=60.0,
            tags={"location": "room-B"},
        ),
    ]


class TestFilterRule:
    """过滤规则测试"""

    def test_eq_operator(self):
        """测试等于操作符"""
        rule = FilterRule(field="source", operator=FilterOperator.EQ, value="sensor-1")
        dp_match = DataPoint(timestamp=0, source="sensor-1", metric="test", value=1)
        dp_no_match = DataPoint(timestamp=0, source="sensor-2", metric="test", value=1)

        assert rule.matches(dp_match) is True
        assert rule.matches(dp_no_match) is False

    def test_gt_operator(self):
        """测试大于操作符"""
        rule = FilterRule(field="value", operator=FilterOperator.GT, value=20)

        dp_high = DataPoint(timestamp=0, source="s", metric="m", value=25)
        dp_low = DataPoint(timestamp=0, source="s", metric="m", value=15)

        assert rule.matches(dp_high) is True
        assert rule.matches(dp_low) is False

    def test_in_operator(self):
        """测试在列表中操作符"""
        rule = FilterRule(field="source", operator=FilterOperator.IN, value=["sensor-1", "sensor-2"])

        dp_match = DataPoint(timestamp=0, source="sensor-1", metric="m", value=0)
        dp_no_match = DataPoint(timestamp=0, source="sensor-3", metric="m", value=0)

        assert rule.matches(dp_match) is True
        assert rule.matches(dp_no_match) is False

    def test_tags_field(self):
        """测试标签字段过滤"""
        rule = FilterRule(field="tags.location", operator=FilterOperator.EQ, value="room-A")

        dp_match = DataPoint(timestamp=0, source="s", metric="m", value=0, tags={"location": "room-A"})
        dp_no_match = DataPoint(timestamp=0, source="s", metric="m", value=0, tags={"location": "room-B"})

        assert rule.matches(dp_match) is True
        assert rule.matches(dp_no_match) is False

    def test_negate(self):
        """测试取反"""
        rule = FilterRule(field="source", operator=FilterOperator.EQ, value="sensor-1", negate=True)

        dp = DataPoint(timestamp=0, source="sensor-1", metric="m", value=0)

        assert rule.matches(dp) is False


class TestDataFilter:
    """数据过滤器测试"""

    def test_single_rule(self, sample_data_points):
        """测试单规则过滤"""
        f = DataFilter()
        f.add_rule(FilterRule(field="source", operator=FilterOperator.EQ, value="sensor-1"))

        result = f.filter(sample_data_points)
        assert len(result) == 2

    def test_and_mode(self, sample_data_points):
        """测试 AND 模式"""
        f = DataFilter()
        f.set_match_mode(True)
        f.add_rule(FilterRule(field="source", operator=FilterOperator.EQ, value="sensor-1"))
        f.add_rule(FilterRule(field="metric", operator=FilterOperator.EQ, value="temperature"))

        result = f.filter(sample_data_points)
        assert len(result) == 2

    def test_or_mode(self, sample_data_points):
        """测试 OR 模式"""
        f = DataFilter()
        f.set_match_mode(False)
        f.add_rule(FilterRule(field="source", operator=FilterOperator.EQ, value="sensor-1"))
        f.add_rule(FilterRule(field="metric", operator=FilterOperator.EQ, value="humidity"))

        result = f.filter(sample_data_points)
        assert len(result) == 3

    def test_no_rules(self, sample_data_points):
        """测试无规则"""
        f = DataFilter()
        result = f.filter(sample_data_points)
        assert len(result) == 3


class TestDataAggregator:
    """数据聚合器测试"""

    def test_avg_aggregation(self):
        """测试平均值聚合"""
        agg = DataAggregator(window_size=300)

        now = time.time()
        for i in range(5):
            agg.add(DataPoint(
                timestamp=now - 60 + i,
                source="sensor-1",
                metric="temperature",
                value=20.0 + i,
            ))

        result = agg.aggregate(AggregationType.AVG)
        assert "sensor-1:temperature" in result
        assert result["sensor-1:temperature"] == 22.0  # (20+21+22+23+24)/5

    def test_count_aggregation(self):
        """测试计数聚合"""
        agg = DataAggregator(window_size=300)

        now = time.time()
        for i in range(3):
            agg.add(DataPoint(
                timestamp=now - 10 + i,
                source="sensor-1",
                metric="test",
                value=i,
            ))

        result = agg.aggregate(AggregationType.COUNT)
        assert result["sensor-1:test"] == 3

    def test_min_max_aggregation(self):
        """测试最小最大值聚合"""
        agg = DataAggregator(window_size=300)

        now = time.time()
        values = [10, 20, 5, 15, 25]
        for v in values:
            agg.add(DataPoint(
                timestamp=now,
                source="s",
                metric="m",
                value=v,
            ))

        result = agg.aggregate(AggregationType.MIN)
        assert result["s:m"] == 5

        result = agg.aggregate(AggregationType.MAX)
        assert result["s:m"] == 25


class TestRuleEngine:
    """规则引擎测试"""

    def test_forward_rule(self):
        """测试转发规则"""
        engine = RuleEngine()
        engine.add_rule(Rule(
            rule_id="r1",
            name="forward all",
            action=RuleAction.FORWARD,
        ))

        dp = DataPoint(timestamp=0, source="s", metric="m", value=1)
        result = engine.process(dp)

        assert result is not None
        assert result.value == 1

    def test_drop_rule(self):
        """测试丢弃规则"""
        engine = RuleEngine()
        engine.add_rule(Rule(
            rule_id="r1",
            name="drop bad data",
            conditions=[FilterRule(field="value", operator=FilterOperator.LT, value=0)],
            action=RuleAction.DROP,
        ))

        dp_good = DataPoint(timestamp=0, source="s", metric="m", value=10)
        dp_bad = DataPoint(timestamp=0, source="s", metric="m", value=-1)

        assert engine.process(dp_good) is not None
        assert engine.process(dp_bad) is None

    def test_transform_rule(self):
        """测试转换规则"""
        engine = RuleEngine()
        engine.add_rule(Rule(
            rule_id="r1",
            name="scale values",
            action=RuleAction.TRANSFORM,
            action_params={"type": "scale", "factor": 2.0},
        ))

        dp = DataPoint(timestamp=0, source="s", metric="m", value=10)
        result = engine.process(dp)

        assert result is not None
        assert result.value == 20.0

    def test_alert_rule(self):
        """测试告警规则"""
        engine = RuleEngine()

        alerts_received = []
        engine.register_alert_callback(lambda a: alerts_received.append(a))

        engine.add_rule(Rule(
            rule_id="r1",
            name="high temp alert",
            conditions=[FilterRule(field="value", operator=FilterOperator.GT, value=30)],
            action=RuleAction.ALERT,
            action_params={"severity": "warning"},
        ))

        dp = DataPoint(timestamp=0, source="s", metric="temperature", value=35)
        result = engine.process(dp)

        assert result is not None
        assert len(alerts_received) == 1
        assert alerts_received[0]["rule_name"] == "high temp alert"

    def test_rule_priority(self):
        """测试规则优先级"""
        engine = RuleEngine()

        # 低优先级规则
        engine.add_rule(Rule(
            rule_id="r1",
            name="low priority",
            action=RuleAction.TRANSFORM,
            action_params={"type": "offset", "offset": 100},
            priority=1,
        ))

        # 高优先级规则（应该先执行）
        engine.add_rule(Rule(
            rule_id="r2",
            name="high priority drop",
            conditions=[FilterRule(field="value", operator=FilterOperator.LT, value=0)],
            action=RuleAction.DROP,
            priority=10,
        ))

        dp = DataPoint(timestamp=0, source="s", metric="m", value=-5)
        result = engine.process(dp)

        # 高优先级规则丢弃了数据
        assert result is None

    def test_process_batch(self):
        """测试批量处理"""
        engine = RuleEngine()
        engine.add_rule(Rule(
            rule_id="r1",
            name="drop negatives",
            conditions=[FilterRule(field="value", operator=FilterOperator.LT, value=0)],
            action=RuleAction.DROP,
        ))

        data_points = [
            DataPoint(timestamp=0, source="s", metric="m", value=10),
            DataPoint(timestamp=0, source="s", metric="m", value=-5),
            DataPoint(timestamp=0, source="s", metric="m", value=20),
        ]

        result = engine.process_batch(data_points)
        assert len(result) == 2

    def test_stats(self):
        """测试统计信息"""
        engine = RuleEngine()
        engine.add_rule(Rule(
            rule_id="r1",
            name="test",
            action=RuleAction.FORWARD,
        ))

        dp = DataPoint(timestamp=0, source="s", metric="m", value=1)
        engine.process(dp)

        stats = engine.get_stats()
        assert stats["total_rules"] == 1
        assert stats["stats"]["forwarded"] == 1
