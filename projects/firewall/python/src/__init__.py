"""
防火墙 (Firewall) - Python 实现

一个完整的网络防火墙系统，支持包过滤、状态检测、规则管理和日志记录。
"""

__version__ = "1.0.0"
__author__ = "Learning Project"

from .packet import Packet, PacketInfo, Protocol, TCPFlag
from .rules import Rule, RuleSet, RuleAction, RuleDirection, RuleBuilder
from .state import ConnectionState, StateTable, ConnectionTracker
from .logger import FirewallLogger, LogLevel
from .firewall import Firewall, FirewallConfig, FirewallState
from .config import ConfigManager

__all__ = [
    # Packet
    "Packet",
    "PacketInfo",
    "Protocol",
    "TCPFlag",
    # Rules
    "Rule",
    "RuleSet",
    "RuleAction",
    "RuleDirection",
    "RuleBuilder",
    # State
    "ConnectionState",
    "StateTable",
    "ConnectionTracker",
    # Logger
    "FirewallLogger",
    "LogLevel",
    # Firewall
    "Firewall",
    "FirewallConfig",
    "FirewallState",
    # Config
    "ConfigManager",
]
