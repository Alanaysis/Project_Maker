"""
规则引擎模块

实现防火墙规则的管理、匹配和执行。
"""

import json
import time
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import List, Optional, Dict, Any, Callable
from .packet import Packet, PacketInfo, Protocol, ip_in_cidr, port_in_range


class RuleAction(Enum):
    """规则动作"""
    ACCEPT = "accept"      # 允许通过
    DROP = "drop"          # 丢弃（不响应）
    REJECT = "reject"      # 拒绝（返回 ICMP 错误）
    LOG = "log"            # 仅记录日志
    COUNT = "count"        # 仅计数


class RuleDirection(Enum):
    """规则方向"""
    INCOMING = "incoming"   # 入站流量
    OUTGOING = "outgoing"   # 出站流量
    BOTH = "both"          # 双向


class RuleState(Enum):
    """规则状态"""
    ACTIVE = "active"      # 活跃
    DISABLED = "disabled"  # 禁用
    EXPIRED = "expired"    # 过期


@dataclass
class Rule:
    """防火墙规则

    Attributes:
        id: 规则唯一标识
        name: 规则名称
        priority: 优先级（数值越小优先级越高）
        action: 规则动作
        direction: 规则方向
        protocol: 协议类型（None 表示所有协议）
        src_ip: 源 IP/CIDR（None 表示所有 IP）
        dst_ip: 目的 IP/CIDR（None 表示所有 IP）
        src_port: 源端口/范围（None 表示所有端口）
        dst_port: 目的端口/范围（None 表示所有端口）
        state: 规则状态
        enabled: 是否启用
        created_at: 创建时间
        expires_at: 过期时间（None 表示永不过期）
        description: 规则描述
        tags: 规则标签
        match_count: 匹配次数统计
        metadata: 额外元数据
    """
    id: str
    name: str
    priority: int = 100
    action: RuleAction = RuleAction.DROP
    direction: RuleDirection = RuleDirection.BOTH
    protocol: Optional[Protocol] = None
    src_ip: Optional[str] = None
    dst_ip: Optional[str] = None
    src_port: Optional[str] = None
    dst_port: Optional[str] = None
    state: RuleState = RuleState.ACTIVE
    enabled: bool = True
    created_at: float = field(default_factory=time.time)
    expires_at: Optional[float] = None
    description: str = ""
    tags: List[str] = field(default_factory=list)
    match_count: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def is_expired(self) -> bool:
        """检查规则是否过期"""
        if self.expires_at is None:
            return False
        return time.time() > self.expires_at

    def matches(self, packet_info: PacketInfo) -> bool:
        """检查规则是否匹配数据包

        Args:
            packet_info: 数据包信息

        Returns:
            是否匹配
        """
        # 检查规则状态
        if not self.enabled or self.state != RuleState.ACTIVE:
            return False

        # 检查是否过期
        if self.is_expired():
            return False

        # 检查协议
        if self.protocol is not None and packet_info.protocol != self.protocol:
            return False

        # 检查源 IP
        if self.src_ip is not None:
            if not ip_in_cidr(packet_info.src_ip, self.src_ip):
                return False

        # 检查目的 IP
        if self.dst_ip is not None:
            if not ip_in_cidr(packet_info.dst_ip, self.dst_ip):
                return False

        # 检查源端口
        if self.src_port is not None and packet_info.src_port is not None:
            if not port_in_range(packet_info.src_port, self.src_port):
                return False

        # 检查目的端口
        if self.dst_port is not None and packet_info.dst_port is not None:
            if not port_in_range(packet_info.dst_port, self.dst_port):
                return False

        # 匹配成功，更新计数
        self.match_count += 1
        return True

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "name": self.name,
            "priority": self.priority,
            "action": self.action.value,
            "direction": self.direction.value,
            "protocol": self.protocol.value if self.protocol else None,
            "src_ip": self.src_ip,
            "dst_ip": self.dst_ip,
            "src_port": self.src_port,
            "dst_port": self.dst_port,
            "state": self.state.value,
            "enabled": self.enabled,
            "created_at": self.created_at,
            "expires_at": self.expires_at,
            "description": self.description,
            "tags": self.tags,
            "match_count": self.match_count,
            "metadata": self.metadata,
        }

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'Rule':
        """从字典创建规则"""
        protocol = None
        if data.get("protocol") is not None:
            protocol = Protocol(data["protocol"])

        return Rule(
            id=data["id"],
            name=data["name"],
            priority=data.get("priority", 100),
            action=RuleAction(data.get("action", "drop")),
            direction=RuleDirection(data.get("direction", "both")),
            protocol=protocol,
            src_ip=data.get("src_ip"),
            dst_ip=data.get("dst_ip"),
            src_port=data.get("src_port"),
            dst_port=data.get("dst_port"),
            state=RuleState(data.get("state", "active")),
            enabled=data.get("enabled", True),
            created_at=data.get("created_at", time.time()),
            expires_at=data.get("expires_at"),
            description=data.get("description", ""),
            tags=data.get("tags", []),
            match_count=data.get("match_count", 0),
            metadata=data.get("metadata", {}),
        )


class RuleSet:
    """规则集

    管理一组防火墙规则，支持添加、删除、排序和匹配。
    """

    def __init__(self):
        self._rules: Dict[str, Rule] = {}
        self._sorted_rules: List[Rule] = []
        self._dirty = True

    @property
    def rules(self) -> List[Rule]:
        """获取所有规则（按优先级排序）"""
        if self._dirty:
            self._sorted_rules = sorted(
                self._rules.values(),
                key=lambda r: r.priority
            )
            self._dirty = False
        return self._sorted_rules

    def add_rule(self, rule: Rule) -> bool:
        """添加规则

        Args:
            rule: 要添加的规则

        Returns:
            是否成功添加
        """
        if rule.id in self._rules:
            return False

        self._rules[rule.id] = rule
        self._dirty = True
        return True

    def remove_rule(self, rule_id: str) -> bool:
        """删除规则

        Args:
            rule_id: 规则 ID

        Returns:
            是否成功删除
        """
        if rule_id not in self._rules:
            return False

        del self._rules[rule_id]
        self._dirty = True
        return True

    def update_rule(self, rule: Rule) -> bool:
        """更新规则

        Args:
            rule: 要更新的规则

        Returns:
            是否成功更新
        """
        if rule.id not in self._rules:
            return False

        self._rules[rule.id] = rule
        self._dirty = True
        return True

    def get_rule(self, rule_id: str) -> Optional[Rule]:
        """获取规则

        Args:
            rule_id: 规则 ID

        Returns:
            规则对象，不存在返回 None
        """
        return self._rules.get(rule_id)

    def enable_rule(self, rule_id: str) -> bool:
        """启用规则"""
        rule = self.get_rule(rule_id)
        if rule is None:
            return False
        rule.enabled = True
        rule.state = RuleState.ACTIVE
        return True

    def disable_rule(self, rule_id: str) -> bool:
        """禁用规则"""
        rule = self.get_rule(rule_id)
        if rule is None:
            return False
        rule.enabled = False
        rule.state = RuleState.DISABLED
        return True

    def set_priority(self, rule_id: str, priority: int) -> bool:
        """设置规则优先级

        Args:
            rule_id: 规则 ID
            priority: 新的优先级值

        Returns:
            是否成功设置
        """
        rule = self.get_rule(rule_id)
        if rule is None:
            return False
        rule.priority = priority
        self._dirty = True
        return True

    def match(self, packet_info: PacketInfo) -> Optional[Rule]:
        """匹配数据包

        按优先级顺序匹配规则，返回第一个匹配的规则。

        Args:
            packet_info: 数据包信息

        Returns:
            匹配的规则，无匹配返回 None
        """
        for rule in self.rules:
            if rule.matches(packet_info):
                return rule
        return None

    def get_statistics(self) -> Dict[str, Any]:
        """获取规则集统计信息"""
        total = len(self._rules)
        active = sum(1 for r in self._rules.values() if r.enabled)
        disabled = total - active

        action_counts = {}
        for rule in self._rules.values():
            action = rule.action.value
            action_counts[action] = action_counts.get(action, 0) + 1

        total_matches = sum(r.match_count for r in self._rules.values())

        return {
            "total_rules": total,
            "active_rules": active,
            "disabled_rules": disabled,
            "action_counts": action_counts,
            "total_matches": total_matches,
        }

    def clear(self):
        """清空所有规则"""
        self._rules.clear()
        self._sorted_rules.clear()
        self._dirty = True

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "rules": [rule.to_dict() for rule in self.rules],
            "statistics": self.get_statistics(),
        }

    def save_to_file(self, filepath: str):
        """保存规则集到文件"""
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)

    def load_from_file(self, filepath: str):
        """从文件加载规则集"""
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)

        self.clear()
        for rule_data in data.get("rules", []):
            rule = Rule.from_dict(rule_data)
            self.add_rule(rule)


def create_default_rules() -> RuleSet:
    """创建默认规则集

    包含基本的防火墙规则：
    1. 允许回环流量
    2. 允许已建立的连接
    3. 允许 DNS 查询
    4. 允许 HTTP/HTTPS
    5. 阻止其他流量
    """
    rules = RuleSet()

    # 规则 1: 允许回环流量
    rules.add_rule(Rule(
        id="loopback-allow",
        name="允许回环流量",
        priority=10,
        action=RuleAction.ACCEPT,
        src_ip="127.0.0.0/8",
        dst_ip="127.0.0.0/8",
        description="允许本地回环接口的流量",
    ))

    # 规则 2: 允许 DNS 查询
    rules.add_rule(Rule(
        id="dns-allow",
        name="允许 DNS 查询",
        priority=20,
        action=RuleAction.ACCEPT,
        protocol=Protocol.UDP,
        dst_port="53",
        description="允许 UDP DNS 查询",
    ))

    # 规则 3: 允许 DNS TCP
    rules.add_rule(Rule(
        id="dns-tcp-allow",
        name="允许 DNS TCP",
        priority=21,
        action=RuleAction.ACCEPT,
        protocol=Protocol.TCP,
        dst_port="53",
        description="允许 TCP DNS 查询（大响应）",
    ))

    # 规则 4: 允许 HTTP
    rules.add_rule(Rule(
        id="http-allow",
        name="允许 HTTP",
        priority=30,
        action=RuleAction.ACCEPT,
        protocol=Protocol.TCP,
        dst_port="80",
        description="允许 HTTP 流量",
    ))

    # 规则 5: 允许 HTTPS
    rules.add_rule(Rule(
        id="https-allow",
        name="允许 HTTPS",
        priority=31,
        action=RuleAction.ACCEPT,
        protocol=Protocol.TCP,
        dst_port="443",
        description="允许 HTTPS 流量",
    ))

    # 规则 6: 允许 SSH
    rules.add_rule(Rule(
        id="ssh-allow",
        name="允许 SSH",
        priority=40,
        action=RuleAction.ACCEPT,
        protocol=Protocol.TCP,
        dst_port="22",
        description="允许 SSH 远程访问",
    ))

    # 规则 7: 允许 ICMP (ping)
    rules.add_rule(Rule(
        id="icmp-allow",
        name="允许 ICMP",
        priority=50,
        action=RuleAction.ACCEPT,
        protocol=Protocol.ICMP,
        description="允许 ICMP 流量（ping）",
    ))

    # 规则 8: 阻止 Telnet
    rules.add_rule(Rule(
        id="telnet-block",
        name="阻止 Telnet",
        priority=80,
        action=RuleAction.DROP,
        protocol=Protocol.TCP,
        dst_port="23",
        description="阻止不安全的 Telnet 协议",
    ))

    # 规则 9: 记录并阻止其他流量
    rules.add_rule(Rule(
        id="default-drop",
        name="默认丢弃",
        priority=1000,
        action=RuleAction.DROP,
        description="默认丢弃所有未匹配的流量",
    ))

    return rules


class RuleBuilder:
    """规则构建器

    提供流畅的 API 来构建规则。
    """

    def __init__(self, rule_id: str, name: str):
        self._rule = Rule(id=rule_id, name=name)

    def priority(self, priority: int) -> 'RuleBuilder':
        """设置优先级"""
        self._rule.priority = priority
        return self

    def action(self, action: RuleAction) -> 'RuleBuilder':
        """设置动作"""
        self._rule.action = action
        return self

    def direction(self, direction: RuleDirection) -> 'RuleBuilder':
        """设置方向"""
        self._rule.direction = direction
        return self

    def protocol(self, protocol: Protocol) -> 'RuleBuilder':
        """设置协议"""
        self._rule.protocol = protocol
        return self

    def src_ip(self, ip: str) -> 'RuleBuilder':
        """设置源 IP"""
        self._rule.src_ip = ip
        return self

    def dst_ip(self, ip: str) -> 'RuleBuilder':
        """设置目的 IP"""
        self._rule.dst_ip = ip
        return self

    def src_port(self, port: str) -> 'RuleBuilder':
        """设置源端口"""
        self._rule.src_port = port
        return self

    def dst_port(self, port: str) -> 'RuleBuilder':
        """设置目的端口"""
        self._rule.dst_port = port
        return self

    def description(self, desc: str) -> 'RuleBuilder':
        """设置描述"""
        self._rule.description = desc
        return self

    def tags(self, *tags: str) -> 'RuleBuilder':
        """设置标签"""
        self._rule.tags = list(tags)
        return self

    def expires_in(self, seconds: int) -> 'RuleBuilder':
        """设置过期时间"""
        self._rule.expires_at = time.time() + seconds
        return self

    def build(self) -> Rule:
        """构建规则"""
        return self._rule
