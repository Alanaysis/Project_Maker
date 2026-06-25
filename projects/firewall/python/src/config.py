"""
配置管理模块

实现防火墙配置的加载、保存和管理。
"""

import os
import json
import yaml
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from .rules import Rule, RuleSet, RuleAction, RuleDirection
from .packet import Protocol


@dataclass
class FirewallConfig:
    """防火墙配置

    Attributes:
        name: 防火墙名称
        version: 配置版本
        log_dir: 日志目录
        log_level: 日志级别
        max_connections: 最大连接数
        rules_file: 规则文件路径
        enable_stateful: 是否启用状态检测
        enable_ids: 是否启用入侵检测
        default_action: 默认动作
        interfaces: 监听接口列表
    """
    name: str = "PythonFirewall"
    version: str = "1.0.0"
    log_dir: str = "logs"
    log_level: str = "info"
    max_connections: int = 10000
    rules_file: str = "rules.json"
    enable_stateful: bool = True
    enable_ids: bool = True
    default_action: str = "drop"
    interfaces: List[str] = field(default_factory=lambda: ["eth0"])

    # 超时配置
    tcp_timeout: int = 300
    udp_timeout: int = 60
    icmp_timeout: int = 30

    # IDS 配置
    max_connections_per_minute: int = 100
    max_ports_per_minute: int = 20
    syn_flood_threshold: int = 1000

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "name": self.name,
            "version": self.version,
            "log_dir": self.log_dir,
            "log_level": self.log_level,
            "max_connections": self.max_connections,
            "rules_file": self.rules_file,
            "enable_stateful": self.enable_stateful,
            "enable_ids": self.enable_ids,
            "default_action": self.default_action,
            "interfaces": self.interfaces,
            "timeouts": {
                "tcp": self.tcp_timeout,
                "udp": self.udp_timeout,
                "icmp": self.icmp_timeout,
            },
            "ids": {
                "max_connections_per_minute": self.max_connections_per_minute,
                "max_ports_per_minute": self.max_ports_per_minute,
                "syn_flood_threshold": self.syn_flood_threshold,
            },
        }

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'FirewallConfig':
        """从字典创建配置"""
        config = FirewallConfig()
        config.name = data.get("name", config.name)
        config.version = data.get("version", config.version)
        config.log_dir = data.get("log_dir", config.log_dir)
        config.log_level = data.get("log_level", config.log_level)
        config.max_connections = data.get("max_connections", config.max_connections)
        config.rules_file = data.get("rules_file", config.rules_file)
        config.enable_stateful = data.get("enable_stateful", config.enable_stateful)
        config.enable_ids = data.get("enable_ids", config.enable_ids)
        config.default_action = data.get("default_action", config.default_action)
        config.interfaces = data.get("interfaces", config.interfaces)

        # 超时配置
        timeouts = data.get("timeouts", {})
        config.tcp_timeout = timeouts.get("tcp", config.tcp_timeout)
        config.udp_timeout = timeouts.get("udp", config.udp_timeout)
        config.icmp_timeout = timeouts.get("icmp", config.icmp_timeout)

        # IDS 配置
        ids = data.get("ids", {})
        config.max_connections_per_minute = ids.get("max_connections_per_minute", config.max_connections_per_minute)
        config.max_ports_per_minute = ids.get("max_ports_per_minute", config.max_ports_per_minute)
        config.syn_flood_threshold = ids.get("syn_flood_threshold", config.syn_flood_threshold)

        return config


class ConfigManager:
    """配置管理器

    负责加载、保存和管理防火墙配置。
    """

    def __init__(self, config_dir: str = "configs"):
        """初始化配置管理器

        Args:
            config_dir: 配置文件目录
        """
        self._config_dir = config_dir
        self._config: Optional[FirewallConfig] = None
        self._ruleset: Optional[RuleSet] = None

    @property
    def config(self) -> FirewallConfig:
        """获取当前配置"""
        if self._config is None:
            self._config = FirewallConfig()
        return self._config

    @property
    def ruleset(self) -> RuleSet:
        """获取当前规则集"""
        if self._ruleset is None:
            self._ruleset = RuleSet()
        return self._ruleset

    def load_config(self, filepath: Optional[str] = None) -> FirewallConfig:
        """加载配置文件

        Args:
            filepath: 配置文件路径，None 则使用默认路径

        Returns:
            加载的配置对象
        """
        if filepath is None:
            filepath = os.path.join(self._config_dir, "firewall.yaml")

        if not os.path.exists(filepath):
            # 使用默认配置
            self._config = FirewallConfig()
            return self._config

        # 根据文件扩展名选择解析方式
        ext = os.path.splitext(filepath)[1].lower()

        with open(filepath, 'r', encoding='utf-8') as f:
            if ext in ('.yaml', '.yml'):
                data = yaml.safe_load(f)
            elif ext == '.json':
                data = json.load(f)
            else:
                raise ValueError(f"Unsupported config format: {ext}")

        self._config = FirewallConfig.from_dict(data)
        return self._config

    def save_config(self, filepath: Optional[str] = None):
        """保存配置文件

        Args:
            filepath: 配置文件路径，None 则使用默认路径
        """
        if filepath is None:
            filepath = os.path.join(self._config_dir, "firewall.yaml")

        # 创建目录
        os.makedirs(os.path.dirname(filepath), exist_ok=True)

        # 根据文件扩展名选择保存方式
        ext = os.path.splitext(filepath)[1].lower()

        with open(filepath, 'w', encoding='utf-8') as f:
            if ext in ('.yaml', '.yml'):
                yaml.dump(self.config.to_dict(), f, default_flow_style=False, allow_unicode=True)
            elif ext == '.json':
                json.dump(self.config.to_dict(), f, indent=2, ensure_ascii=False)
            else:
                raise ValueError(f"Unsupported config format: {ext}")

    def load_rules(self, filepath: Optional[str] = None) -> RuleSet:
        """加载规则文件

        Args:
            filepath: 规则文件路径，None 则使用默认路径

        Returns:
            加载的规则集
        """
        if filepath is None:
            filepath = os.path.join(self._config_dir, self.config.rules_file)

        self._ruleset = RuleSet()

        if not os.path.exists(filepath):
            # 使用默认规则
            from .rules import create_default_rules
            self._ruleset = create_default_rules()
            return self._ruleset

        self._ruleset.load_from_file(filepath)
        return self._ruleset

    def save_rules(self, filepath: Optional[str] = None):
        """保存规则文件

        Args:
            filepath: 规则文件路径，None 则使用默认路径
        """
        if filepath is None:
            filepath = os.path.join(self._config_dir, self.config.rules_file)

        # 创建目录
        os.makedirs(os.path.dirname(filepath), exist_ok=True)

        self.ruleset.save_to_file(filepath)

    def create_default_config(self) -> FirewallConfig:
        """创建默认配置"""
        self._config = FirewallConfig()
        return self._config

    def create_default_rules(self) -> RuleSet:
        """创建默认规则集"""
        from .rules import create_default_rules
        self._ruleset = create_default_rules()
        return self._ruleset

    def add_rule(self, rule: Rule) -> bool:
        """添加规则"""
        return self.ruleset.add_rule(rule)

    def remove_rule(self, rule_id: str) -> bool:
        """删除规则"""
        return self.ruleset.remove_rule(rule_id)

    def update_rule(self, rule: Rule) -> bool:
        """更新规则"""
        return self.ruleset.update_rule(rule)


def create_sample_config() -> Dict[str, Any]:
    """创建示例配置"""
    return {
        "name": "PythonFirewall",
        "version": "1.0.0",
        "log_dir": "logs",
        "log_level": "info",
        "max_connections": 10000,
        "rules_file": "rules.json",
        "enable_stateful": True,
        "enable_ids": True,
        "default_action": "drop",
        "interfaces": ["eth0"],
        "timeouts": {
            "tcp": 300,
            "udp": 60,
            "icmp": 30,
        },
        "ids": {
            "max_connections_per_minute": 100,
            "max_ports_per_minute": 20,
            "syn_flood_threshold": 1000,
        },
    }


def create_sample_rules() -> List[Dict[str, Any]]:
    """创建示例规则"""
    return [
        {
            "id": "loopback-allow",
            "name": "允许回环流量",
            "priority": 10,
            "action": "accept",
            "src_ip": "127.0.0.0/8",
            "dst_ip": "127.0.0.0/8",
            "description": "允许本地回环接口的流量",
        },
        {
            "id": "ssh-allow",
            "name": "允许 SSH",
            "priority": 20,
            "action": "accept",
            "protocol": 6,
            "dst_port": "22",
            "description": "允许 SSH 远程访问",
        },
        {
            "id": "http-allow",
            "name": "允许 HTTP",
            "priority": 30,
            "action": "accept",
            "protocol": 6,
            "dst_port": "80",
            "description": "允许 HTTP 流量",
        },
        {
            "id": "https-allow",
            "name": "允许 HTTPS",
            "priority": 31,
            "action": "accept",
            "protocol": 6,
            "dst_port": "443",
            "description": "允许 HTTPS 流量",
        },
        {
            "id": "default-drop",
            "name": "默认丢弃",
            "priority": 1000,
            "action": "drop",
            "description": "默认丢弃所有未匹配的流量",
        },
    ]
