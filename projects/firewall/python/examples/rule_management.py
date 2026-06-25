#!/usr/bin/env python3
"""
规则管理示例

演示如何动态管理防火墙规则。
"""

import sys
import os
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src import (
    Firewall, FirewallConfig,
    Rule, RuleSet, RuleAction, RuleDirection,
    Protocol, RuleBuilder,
)


def demo_rule_creation():
    """演示规则创建"""
    print("\n=== 规则创建演示 ===")

    # 方法 1: 直接创建
    rule1 = Rule(
        id="direct-rule",
        name="直接创建的规则",
        priority=100,
        action=RuleAction.ACCEPT,
        protocol=Protocol.TCP,
        dst_port="80",
        description="直接使用构造函数创建",
    )
    print(f"方法 1 - 直接创建: {rule1.name}")

    # 方法 2: 使用构建器
    rule2 = (RuleBuilder("builder-rule", "构建器创建的规则")
            .priority(50)
            .action(RuleAction.DROP)
            .protocol(Protocol.TCP)
            .src_ip("192.168.1.0/24")
            .dst_port("23")
            .description("使用 RuleBuilder 创建")
            .tags("security", "telnet")
            .build())
    print(f"方法 2 - 构建器: {rule2.name}")

    # 方法 3: 从字典创建
    rule_data = {
        "id": "dict-rule",
        "name": "字典创建的规则",
        "priority": 75,
        "action": "reject",
        "protocol": 6,
        "dst_port": "22",
        "description": "从字典数据创建",
    }
    rule3 = Rule.from_dict(rule_data)
    print(f"方法 3 - 字典: {rule3.name}")

    return [rule1, rule2, rule3]


def demo_rule_set_management():
    """演示规则集管理"""
    print("\n=== 规则集管理演示 ===")

    ruleset = RuleSet()

    # 添加规则
    rules = [
        Rule(id="r1", name="规则1", priority=10, action=RuleAction.ACCEPT),
        Rule(id="r2", name="规则2", priority=20, action=RuleAction.DROP),
        Rule(id="r3", name="规则3", priority=30, action=RuleAction.ACCEPT),
        Rule(id="r4", name="规则4", priority=40, action=RuleAction.LOG),
        Rule(id="r5", name="规则5", priority=50, action=RuleAction.REJECT),
    ]

    for rule in rules:
        ruleset.add_rule(rule)
        print(f"添加规则: {rule.name} (优先级: {rule.priority})")

    # 列出规则
    print("\n当前规则列表 (按优先级排序):")
    for rule in ruleset.rules:
        print(f"  - {rule.name}: {rule.action.value}")

    # 修改优先级
    print("\n修改规则优先级...")
    ruleset.set_priority("r3", 5)
    print(f"规则 r3 优先级修改为 5")

    # 列出规则
    print("\n修改后的规则列表:")
    for rule in ruleset.rules:
        print(f"  - {rule.name}: {rule.action.value} (优先级: {rule.priority})")

    # 禁用规则
    print("\n禁用规则 r2...")
    ruleset.disable_rule("r2")

    # 统计信息
    stats = ruleset.get_statistics()
    print(f"\n规则统计:")
    print(f"  总规则数: {stats['total_rules']}")
    print(f"  活跃规则: {stats['active_rules']}")
    print(f"  禁用规则: {stats['disabled_rules']}")


def demo_rule_matching():
    """演示规则匹配"""
    print("\n=== 规则匹配演示 ===")

    import time
    from src.packet import PacketInfo

    ruleset = RuleSet()

    # 添加规则
    ruleset.add_rule(Rule(
        id="http",
        name="HTTP",
        priority=10,
        action=RuleAction.ACCEPT,
        protocol=Protocol.TCP,
        dst_port="80",
    ))

    ruleset.add_rule(Rule(
        id="https",
        name="HTTPS",
        priority=11,
        action=RuleAction.ACCEPT,
        protocol=Protocol.TCP,
        dst_port="443",
    ))

    ruleset.add_rule(Rule(
        id="ssh",
        name="SSH",
        priority=20,
        action=RuleAction.ACCEPT,
        protocol=Protocol.TCP,
        dst_port="22",
    ))

    ruleset.add_rule(Rule(
        id="block-telnet",
        name="阻止 Telnet",
        priority=5,
        action=RuleAction.DROP,
        protocol=Protocol.TCP,
        dst_port="23",
    ))

    ruleset.add_rule(Rule(
        id="default",
        name="默认丢弃",
        priority=1000,
        action=RuleAction.DROP,
    ))

    # 测试匹配
    test_cases = [
        ("HTTP 请求", 80),
        ("HTTPS 请求", 443),
        ("SSH 请求", 22),
        ("Telnet 请求", 23),
        ("MySQL 请求", 3306),
    ]

    for name, port in test_cases:
        info = PacketInfo(
            timestamp=time.time(),
            src_ip="192.168.1.1",
            dst_ip="10.0.0.1",
            protocol=Protocol.TCP,
            dst_port=port,
        )
        matched = ruleset.match(info)
        if matched:
            print(f"{name} (端口 {port}): 匹配规则 '{matched.name}' -> {matched.action.value}")
        else:
            print(f"{name} (端口 {port}): 无匹配规则")


def demo_rule_persistence():
    """演示规则持久化"""
    print("\n=== 规则持久化演示 ===")

    # 创建规则集
    ruleset = RuleSet()
    ruleset.add_rule(Rule(
        id="rule1",
        name="规则1",
        priority=10,
        action=RuleAction.ACCEPT,
        protocol=Protocol.TCP,
        dst_port="80",
        description="HTTP 流量",
    ))
    ruleset.add_rule(Rule(
        id="rule2",
        name="规则2",
        priority=20,
        action=RuleAction.DROP,
        protocol=Protocol.TCP,
        dst_port="23",
        description="Telnet 流量",
    ))

    # 保存到文件
    filepath = "examples/rules_example.json"
    ruleset.save_to_file(filepath)
    print(f"规则已保存到: {filepath}")

    # 显示文件内容
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    print(f"\n文件内容:")
    print(json.dumps(data, indent=2, ensure_ascii=False))

    # 从文件加载
    new_ruleset = RuleSet()
    new_ruleset.load_from_file(filepath)
    print(f"\n从文件加载的规则数: {len(new_ruleset.rules)}")

    # 清理
    os.remove(filepath)
    print(f"\n清理示例文件")


def demo_temporary_rules():
    """演示临时规则"""
    print("\n=== 临时规则演示 ===")

    import time

    # 创建临时规则
    temp_rule = (RuleBuilder("temp-ssh", "临时 SSH 访问")
                .priority(5)
                .action(RuleAction.ACCEPT)
                .protocol(Protocol.TCP)
                .dst_port("22")
                .expires_in(3600)  # 1 小时后过期
                .description("临时允许 SSH 访问")
                .build())

    print(f"临时规则: {temp_rule.name}")
    print(f"过期时间: {temp_rule.expires_at}")
    print(f"是否过期: {temp_rule.is_expired()}")

    # 创建已过期的规则
    expired_rule = (RuleBuilder("expired", "已过期规则")
                   .priority(10)
                   .action(RuleAction.ACCEPT)
                   .expires_in(-100)  # 已过期
                   .build())

    print(f"\n过期规则: {expired_rule.name}")
    print(f"是否过期: {expired_rule.is_expired()}")


def demo_rule_statistics():
    """演示规则统计"""
    print("\n=== 规则统计演示 ===")

    import time
    from src.packet import PacketInfo

    ruleset = RuleSet()

    # 添加规则
    ruleset.add_rule(Rule(id="r1", name="规则1", priority=10, action=RuleAction.ACCEPT))
    ruleset.add_rule(Rule(id="r2", name="规则2", priority=20, action=RuleAction.DROP))
    ruleset.add_rule(Rule(id="r3", name="规则3", priority=30, action=RuleAction.ACCEPT))

    # 模拟匹配
    for i in range(10):
        info = PacketInfo(
            timestamp=time.time(),
            src_ip="192.168.1.1",
            dst_ip="10.0.0.1",
            protocol=Protocol.TCP,
        )
        ruleset.match(info)

    # 显示统计
    stats = ruleset.get_statistics()
    print(f"规则统计:")
    print(f"  总规则数: {stats['total_rules']}")
    print(f"  总匹配次数: {stats['total_matches']}")
    print(f"  动作分布: {stats['action_counts']}")

    # 显示每个规则的匹配次数
    print(f"\n规则匹配详情:")
    for rule in ruleset.rules:
        print(f"  - {rule.name}: {rule.match_count} 次匹配")


def main():
    """主函数"""
    print("防火墙规则管理示例")
    print("=" * 50)

    demo_rule_creation()
    demo_rule_set_management()
    demo_rule_matching()
    demo_rule_persistence()
    demo_temporary_rules()
    demo_rule_statistics()

    print("\n" + "=" * 50)
    print("规则管理示例完成！")


if __name__ == "__main__":
    main()
