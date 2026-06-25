"""
规则引擎测试
"""

import time
import pytest
from src.packet import PacketInfo, Protocol
from src.rules import (
    Rule, RuleSet, RuleAction, RuleDirection, RuleState,
    RuleBuilder, create_default_rules
)


class TestRule:
    """规则测试"""

    def test_create_rule(self):
        """测试创建规则"""
        rule = Rule(
            id="test-rule",
            name="Test Rule",
            priority=100,
            action=RuleAction.ACCEPT,
            protocol=Protocol.TCP,
            dst_port="80",
        )

        assert rule.id == "test-rule"
        assert rule.name == "Test Rule"
        assert rule.priority == 100
        assert rule.action == RuleAction.ACCEPT
        assert rule.protocol == Protocol.TCP
        assert rule.dst_port == "80"

    def test_rule_matches_protocol(self):
        """测试协议匹配"""
        rule = Rule(
            id="tcp-rule",
            name="TCP Rule",
            action=RuleAction.ACCEPT,
            protocol=Protocol.TCP,
        )

        # 匹配 TCP
        info = PacketInfo(
            timestamp=time.time(),
            src_ip="192.168.1.1",
            dst_ip="10.0.0.1",
            protocol=Protocol.TCP,
        )
        assert rule.matches(info) is True

        # 不匹配 UDP
        info.protocol = Protocol.UDP
        assert rule.matches(info) is False

    def test_rule_matches_ip(self):
        """测试 IP 匹配"""
        rule = Rule(
            id="ip-rule",
            name="IP Rule",
            action=RuleAction.DROP,
            src_ip="192.168.1.0/24",
        )

        # 匹配
        info = PacketInfo(
            timestamp=time.time(),
            src_ip="192.168.1.100",
            dst_ip="10.0.0.1",
            protocol=Protocol.TCP,
        )
        assert rule.matches(info) is True

        # 不匹配
        info.src_ip = "10.0.0.1"
        assert rule.matches(info) is False

    def test_rule_matches_port(self):
        """测试端口匹配"""
        rule = Rule(
            id="port-rule",
            name="Port Rule",
            action=RuleAction.ACCEPT,
            dst_port="80",
        )

        # 匹配
        info = PacketInfo(
            timestamp=time.time(),
            src_ip="192.168.1.1",
            dst_ip="10.0.0.1",
            protocol=Protocol.TCP,
            dst_port=80,
        )
        assert rule.matches(info) is True

        # 不匹配
        info.dst_port = 443
        assert rule.matches(info) is False

    def test_rule_disabled(self):
        """测试禁用规则"""
        rule = Rule(
            id="disabled-rule",
            name="Disabled Rule",
            enabled=False,
            action=RuleAction.ACCEPT,
        )

        info = PacketInfo(
            timestamp=time.time(),
            src_ip="192.168.1.1",
            dst_ip="10.0.0.1",
            protocol=Protocol.TCP,
        )
        assert rule.matches(info) is False

    def test_rule_expired(self):
        """测试过期规则"""
        rule = Rule(
            id="expired-rule",
            name="Expired Rule",
            action=RuleAction.ACCEPT,
            expires_at=time.time() - 100,  # 已过期
        )

        info = PacketInfo(
            timestamp=time.time(),
            src_ip="192.168.1.1",
            dst_ip="10.0.0.1",
            protocol=Protocol.TCP,
        )
        assert rule.matches(info) is False
        assert rule.is_expired() is True

    def test_rule_match_count(self):
        """测试匹配计数"""
        rule = Rule(
            id="count-rule",
            name="Count Rule",
            action=RuleAction.ACCEPT,
        )

        info = PacketInfo(
            timestamp=time.time(),
            src_ip="192.168.1.1",
            dst_ip="10.0.0.1",
            protocol=Protocol.TCP,
        )

        assert rule.match_count == 0
        rule.matches(info)
        assert rule.match_count == 1
        rule.matches(info)
        assert rule.match_count == 2

    def test_rule_to_dict(self):
        """测试规则转字典"""
        rule = Rule(
            id="test-rule",
            name="Test Rule",
            priority=50,
            action=RuleAction.ACCEPT,
            protocol=Protocol.TCP,
            dst_port="80",
            description="Test description",
        )

        data = rule.to_dict()
        assert data["id"] == "test-rule"
        assert data["name"] == "Test Rule"
        assert data["priority"] == 50
        assert data["action"] == "accept"
        assert data["protocol"] == 6
        assert data["dst_port"] == "80"

    def test_rule_from_dict(self):
        """测试从字典创建规则"""
        data = {
            "id": "test-rule",
            "name": "Test Rule",
            "priority": 50,
            "action": "accept",
            "protocol": 6,
            "dst_port": "80",
        }

        rule = Rule.from_dict(data)
        assert rule.id == "test-rule"
        assert rule.name == "Test Rule"
        assert rule.priority == 50
        assert rule.action == RuleAction.ACCEPT
        assert rule.protocol == Protocol.TCP
        assert rule.dst_port == "80"


class TestRuleSet:
    """规则集测试"""

    def test_add_rule(self):
        """测试添加规则"""
        ruleset = RuleSet()
        rule = Rule(id="test", name="Test", action=RuleAction.ACCEPT)

        assert ruleset.add_rule(rule) is True
        assert len(ruleset.rules) == 1

    def test_add_duplicate_rule(self):
        """测试添加重复规则"""
        ruleset = RuleSet()
        rule = Rule(id="test", name="Test", action=RuleAction.ACCEPT)

        ruleset.add_rule(rule)
        assert ruleset.add_rule(rule) is False
        assert len(ruleset.rules) == 1

    def test_remove_rule(self):
        """测试删除规则"""
        ruleset = RuleSet()
        rule = Rule(id="test", name="Test", action=RuleAction.ACCEPT)

        ruleset.add_rule(rule)
        assert ruleset.remove_rule("test") is True
        assert len(ruleset.rules) == 0

    def test_remove_nonexistent_rule(self):
        """测试删除不存在的规则"""
        ruleset = RuleSet()
        assert ruleset.remove_rule("nonexistent") is False

    def test_get_rule(self):
        """测试获取规则"""
        ruleset = RuleSet()
        rule = Rule(id="test", name="Test", action=RuleAction.ACCEPT)

        ruleset.add_rule(rule)
        retrieved = ruleset.get_rule("test")
        assert retrieved is not None
        assert retrieved.id == "test"

    def test_priority_ordering(self):
        """测试优先级排序"""
        ruleset = RuleSet()

        # 添加不同优先级的规则
        ruleset.add_rule(Rule(id="low", name="Low", priority=100, action=RuleAction.DROP))
        ruleset.add_rule(Rule(id="high", name="High", priority=10, action=RuleAction.ACCEPT))
        ruleset.add_rule(Rule(id="mid", name="Mid", priority=50, action=RuleAction.LOG))

        rules = ruleset.rules
        assert rules[0].id == "high"
        assert rules[1].id == "mid"
        assert rules[2].id == "low"

    def test_match_first_rule(self):
        """测试匹配第一个规则"""
        ruleset = RuleSet()

        ruleset.add_rule(Rule(id="first", name="First", priority=10, action=RuleAction.ACCEPT))
        ruleset.add_rule(Rule(id="second", name="Second", priority=20, action=RuleAction.DROP))

        info = PacketInfo(
            timestamp=time.time(),
            src_ip="192.168.1.1",
            dst_ip="10.0.0.1",
            protocol=Protocol.TCP,
        )

        matched = ruleset.match(info)
        assert matched is not None
        assert matched.id == "first"

    def test_match_no_rule(self):
        """测试无匹配规则"""
        ruleset = RuleSet()

        ruleset.add_rule(Rule(
            id="tcp-only",
            name="TCP Only",
            action=RuleAction.ACCEPT,
            protocol=Protocol.TCP,
        ))

        info = PacketInfo(
            timestamp=time.time(),
            src_ip="192.168.1.1",
            dst_ip="10.0.0.1",
            protocol=Protocol.UDP,
        )

        matched = ruleset.match(info)
        assert matched is None

    def test_enable_disable_rule(self):
        """测试启用/禁用规则"""
        ruleset = RuleSet()
        rule = Rule(id="test", name="Test", action=RuleAction.ACCEPT)
        ruleset.add_rule(rule)

        # 禁用规则
        ruleset.disable_rule("test")
        assert rule.enabled is False
        assert rule.state == RuleState.DISABLED

        # 启用规则
        ruleset.enable_rule("test")
        assert rule.enabled is True
        assert rule.state == RuleState.ACTIVE

    def test_set_priority(self):
        """测试设置优先级"""
        ruleset = RuleSet()
        rule = Rule(id="test", name="Test", priority=100, action=RuleAction.ACCEPT)
        ruleset.add_rule(rule)

        ruleset.set_priority("test", 50)
        assert rule.priority == 50

    def test_statistics(self):
        """测试统计信息"""
        ruleset = RuleSet()

        ruleset.add_rule(Rule(id="r1", name="R1", action=RuleAction.ACCEPT))
        ruleset.add_rule(Rule(id="r2", name="R2", action=RuleAction.DROP))
        ruleset.add_rule(Rule(id="r3", name="R3", action=RuleAction.ACCEPT, enabled=False))

        stats = ruleset.get_statistics()
        assert stats["total_rules"] == 3
        assert stats["active_rules"] == 2
        assert stats["disabled_rules"] == 1
        assert stats["action_counts"]["accept"] == 2
        assert stats["action_counts"]["drop"] == 1

    def test_clear(self):
        """测试清空规则集"""
        ruleset = RuleSet()
        ruleset.add_rule(Rule(id="r1", name="R1", action=RuleAction.ACCEPT))
        ruleset.add_rule(Rule(id="r2", name="R2", action=RuleAction.DROP))

        ruleset.clear()
        assert len(ruleset.rules) == 0


class TestRuleBuilder:
    """规则构建器测试"""

    def test_build_basic(self):
        """测试基本构建"""
        rule = (RuleBuilder("test", "Test Rule")
               .priority(50)
               .action(RuleAction.ACCEPT)
               .protocol(Protocol.TCP)
               .dst_port("80")
               .description("Test description")
               .build())

        assert rule.id == "test"
        assert rule.name == "Test Rule"
        assert rule.priority == 50
        assert rule.action == RuleAction.ACCEPT
        assert rule.protocol == Protocol.TCP
        assert rule.dst_port == "80"
        assert rule.description == "Test description"

    def test_build_with_ip(self):
        """测试带 IP 的构建"""
        rule = (RuleBuilder("test", "Test Rule")
               .src_ip("192.168.1.0/24")
               .dst_ip("10.0.0.0/8")
               .build())

        assert rule.src_ip == "192.168.1.0/24"
        assert rule.dst_ip == "10.0.0.0/8"

    def test_build_with_tags(self):
        """测试带标签的构建"""
        rule = (RuleBuilder("test", "Test Rule")
               .tags("security", "block", "external")
               .build())

        assert "security" in rule.tags
        assert "block" in rule.tags
        assert "external" in rule.tags


class TestDefaultRules:
    """默认规则测试"""

    def test_create_default_rules(self):
        """测试创建默认规则"""
        ruleset = create_default_rules()

        assert len(ruleset.rules) > 0

        # 检查是否有回环规则
        loopback = ruleset.get_rule("loopback-allow")
        assert loopback is not None
        assert loopback.action == RuleAction.ACCEPT

        # 检查是否有默认丢弃规则
        default_drop = ruleset.get_rule("default-drop")
        assert default_drop is not None
        assert default_drop.action == RuleAction.DROP

    def test_default_rules_priority(self):
        """测试默认规则优先级"""
        ruleset = create_default_rules()

        # 回环规则应该有最高优先级
        loopback = ruleset.get_rule("loopback-allow")
        default_drop = ruleset.get_rule("default-drop")

        assert loopback.priority < default_drop.priority


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
