"""
防火墙主引擎

整合所有模块，提供完整的防火墙功能。
"""

import os
import time
import signal
import threading
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List, Callable
from enum import Enum, auto

from .packet import Packet, PacketInfo, Protocol
from .rules import Rule, RuleSet, RuleAction, RuleDirection, create_default_rules
from .state import ConnectionState, StateTable, ConnectionTracker
from .logger import FirewallLogger, LogLevel, LogType, IntrusionDetector
from .config import FirewallConfig, ConfigManager


class FirewallState(Enum):
    """防火墙状态"""
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"


@dataclass
class FirewallStatistics:
    """防火墙统计信息"""
    start_time: float = 0
    packets_processed: int = 0
    packets_accepted: int = 0
    packets_dropped: int = 0
    packets_rejected: int = 0
    rules_matched: int = 0
    alerts_generated: int = 0
    bytes_processed: int = 0

    @property
    def uptime(self) -> float:
        """运行时间（秒）"""
        if self.start_time == 0:
            return 0
        return time.time() - self.start_time

    @property
    def packets_per_second(self) -> float:
        """每秒处理数据包数"""
        uptime = self.uptime
        if uptime == 0:
            return 0
        return self.packets_processed / uptime

    @property
    def accept_rate(self) -> float:
        """接受率"""
        if self.packets_processed == 0:
            return 0
        return self.packets_accepted / self.packets_processed

    @property
    def drop_rate(self) -> float:
        """丢弃率"""
        if self.packets_processed == 0:
            return 0
        return self.packets_dropped / self.packets_processed

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "start_time": self.start_time,
            "uptime": self.uptime,
            "packets_processed": self.packets_processed,
            "packets_accepted": self.packets_accepted,
            "packets_dropped": self.packets_dropped,
            "packets_rejected": self.packets_rejected,
            "rules_matched": self.rules_matched,
            "alerts_generated": self.alerts_generated,
            "bytes_processed": self.bytes_processed,
            "packets_per_second": self.packets_per_second,
            "accept_rate": self.accept_rate,
            "drop_rate": self.drop_rate,
        }


class Firewall:
    """防火墙主引擎

    整合包过滤、状态检测、规则管理和日志记录功能。
    """

    def __init__(self, config: Optional[FirewallConfig] = None):
        """初始化防火墙

        Args:
            config: 防火墙配置，None 则使用默认配置
        """
        # 配置
        self._config = config or FirewallConfig()

        # 状态
        self._state = FirewallState.STOPPED
        self._statistics = FirewallStatistics()

        # 核心组件
        self._rule_set = create_default_rules()
        self._connection_tracker = ConnectionTracker(
            max_connections=self._config.max_connections
        )
        self._logger = FirewallLogger(
            name=self._config.name,
            log_dir=self._config.log_dir,
        )
        self._ids = IntrusionDetector(self._logger)

        # 回调函数
        self._packet_callbacks: List[Callable[[PacketInfo, RuleAction], None]] = []
        self._alert_callbacks: List[Callable[[str, PacketInfo], None]] = []

        # 线程控制
        self._lock = threading.Lock()
        self._running = False

        # 设置日志级别
        log_level = {
            "debug": LogLevel.DEBUG,
            "info": LogLevel.INFO,
            "warning": LogLevel.WARNING,
            "error": LogLevel.ERROR,
        }.get(self._config.log_level, LogLevel.INFO)
        self._logger.set_level(log_level)

        # 设置 IDS 阈值
        self._ids._max_connections_per_minute = self._config.max_connections_per_minute
        self._ids._max_ports_per_minute = self._config.max_ports_per_minute
        self._ids._syn_flood_threshold = self._config.syn_flood_threshold

    @property
    def state(self) -> FirewallState:
        """获取防火墙状态"""
        return self._state

    @property
    def is_running(self) -> bool:
        """检查是否正在运行"""
        return self._state == FirewallState.RUNNING

    @property
    def statistics(self) -> FirewallStatistics:
        """获取统计信息"""
        return self._statistics

    @property
    def rule_set(self) -> RuleSet:
        """获取规则集"""
        return self._rule_set

    @property
    def connection_tracker(self) -> ConnectionTracker:
        """获取连接跟踪器"""
        return self._connection_tracker

    @property
    def logger(self) -> FirewallLogger:
        """获取日志记录器"""
        return self._logger

    def load_config(self, config_path: str):
        """加载配置文件

        Args:
            config_path: 配置文件路径
        """
        manager = ConfigManager()
        self._config = manager.load_config(config_path)
        self._apply_config()

    def load_rules(self, rules_path: str):
        """加载规则文件

        Args:
            rules_path: 规则文件路径
        """
        self._rule_set.load_from_file(rules_path)
        self._logger.log_system(f"Loaded rules from {rules_path}")

    def save_rules(self, rules_path: str):
        """保存规则文件

        Args:
            rules_path: 规则文件路径
        """
        self._rule_set.save_to_file(rules_path)
        self._logger.log_system(f"Saved rules to {rules_path}")

    def _apply_config(self):
        """应用配置"""
        # 更新日志级别
        log_level = {
            "debug": LogLevel.DEBUG,
            "info": LogLevel.INFO,
            "warning": LogLevel.WARNING,
            "error": LogLevel.ERROR,
        }.get(self._config.log_level, LogLevel.INFO)
        self._logger.set_level(log_level)

        # 更新 IDS 阈值
        self._ids._max_connections_per_minute = self._config.max_connections_per_minute
        self._ids._max_ports_per_minute = self._config.max_ports_per_minute
        self._ids._syn_flood_threshold = self._config.syn_flood_threshold

    def add_rule(self, rule: Rule) -> bool:
        """添加规则

        Args:
            rule: 要添加的规则

        Returns:
            是否成功添加
        """
        result = self._rule_set.add_rule(rule)
        if result:
            self._logger.log_system(f"Added rule: {rule.name} ({rule.id})")
        return result

    def remove_rule(self, rule_id: str) -> bool:
        """删除规则

        Args:
            rule_id: 规则 ID

        Returns:
            是否成功删除
        """
        rule = self._rule_set.get_rule(rule_id)
        if rule is None:
            return False

        result = self._rule_set.remove_rule(rule_id)
        if result:
            self._logger.log_system(f"Removed rule: {rule.name} ({rule_id})")
        return result

    def update_rule(self, rule: Rule) -> bool:
        """更新规则

        Args:
            rule: 要更新的规则

        Returns:
            是否成功更新
        """
        result = self._rule_set.update_rule(rule)
        if result:
            self._logger.log_system(f"Updated rule: {rule.name} ({rule.id})")
        return result

    def enable_rule(self, rule_id: str) -> bool:
        """启用规则"""
        result = self._rule_set.enable_rule(rule_id)
        if result:
            self._logger.log_system(f"Enabled rule: {rule_id}")
        return result

    def disable_rule(self, rule_id: str) -> bool:
        """禁用规则"""
        result = self._rule_set.disable_rule(rule_id)
        if result:
            self._logger.log_system(f"Disabled rule: {rule_id}")
        return result

    def set_rule_priority(self, rule_id: str, priority: int) -> bool:
        """设置规则优先级

        Args:
            rule_id: 规则 ID
            priority: 新的优先级值

        Returns:
            是否成功设置
        """
        result = self._rule_set.set_priority(rule_id, priority)
        if result:
            self._logger.log_system(f"Set rule {rule_id} priority to {priority}")
        return result

    def add_packet_callback(self, callback: Callable[[PacketInfo, RuleAction], None]):
        """添加数据包处理回调"""
        self._packet_callbacks.append(callback)

    def add_alert_callback(self, callback: Callable[[str, PacketInfo], None]):
        """添加告警回调"""
        self._alert_callbacks.append(callback)

    def process_packet(self, packet: Packet,
                      is_outgoing: bool = False) -> RuleAction:
        """处理数据包

        这是防火墙的核心方法，处理流程：
        1. 解析数据包信息
        2. 检查连接状态（如果启用状态检测）
        3. 匹配规则
        4. 执行动作
        5. 记录日志

        Args:
            packet: 网络数据包
            is_outgoing: 是否为出站流量

        Returns:
            执行的规则动作
        """
        if not self.is_running:
            return RuleAction.DROP

        packet_info = packet.info
        action = RuleAction.DROP
        matched_rule = None

        with self._lock:
            self._statistics.packets_processed += 1
            self._statistics.bytes_processed += packet_info.length

            # 状态检测
            if self._config.enable_stateful:
                conn_state, conn_entry = self._connection_tracker.process_packet(
                    packet_info, is_outgoing
                )

                # 已建立的连接默认允许
                if conn_state == ConnectionState.ESTABLISHED:
                    action = RuleAction.ACCEPT
                    self._logger.log_state_change(
                        f"Established connection: {packet_info}",
                        packet_info
                    )

            # 规则匹配
            if action != RuleAction.ACCEPT:
                matched_rule = self._rule_set.match(packet_info)

                if matched_rule:
                    action = matched_rule.action
                    self._statistics.rules_matched += 1
                    self._logger.log_rule_match(packet_info, matched_rule, action)
                else:
                    # 默认动作
                    if self._config.default_action == "accept":
                        action = RuleAction.ACCEPT
                    else:
                        action = RuleAction.DROP

            # 执行动作
            if action == RuleAction.ACCEPT:
                self._statistics.packets_accepted += 1
                self._logger.log_accepted(packet_info, matched_rule)
            elif action == RuleAction.DROP:
                self._statistics.packets_dropped += 1
                self._logger.log_dropped(
                    packet_info,
                    reason=f"Rule: {matched_rule.name}" if matched_rule else "Default drop",
                    rule=matched_rule
                )
            elif action == RuleAction.REJECT:
                self._statistics.packets_rejected += 1
                self._logger.log_dropped(
                    packet_info,
                    reason="Rejected",
                    rule=matched_rule
                )

            # 入侵检测
            if self._config.enable_ids:
                self._ids.analyze_packet(packet_info, action)

            # 触发回调
            for callback in self._packet_callbacks:
                try:
                    callback(packet_info, action)
                except Exception as e:
                    self._logger.log_system(
                        f"Packet callback error: {e}",
                        LogLevel.ERROR
                    )

        return action

    def process_raw_packet(self, data: bytes,
                          is_outgoing: bool = False) -> RuleAction:
        """处理原始数据包

        Args:
            data: 原始数据包数据
            is_outgoing: 是否为出站流量

        Returns:
            执行的规则动作
        """
        packet = Packet.from_ip(data)
        if packet is None:
            self._logger.log_system("Failed to parse packet", LogLevel.WARNING)
            return RuleAction.DROP

        return self.process_packet(packet, is_outgoing)

    def start(self):
        """启动防火墙"""
        if self._state != FirewallState.STOPPED:
            self._logger.log_system("Firewall is already running", LogLevel.WARNING)
            return

        self._state = FirewallState.STARTING
        self._logger.log_system("Starting firewall...")

        # 初始化统计
        self._statistics = FirewallStatistics()
        self._statistics.start_time = time.time()

        # 清空状态表
        self._connection_tracker.state_table.clear()

        # 启动状态清理线程
        self._running = True
        self._cleanup_thread = threading.Thread(
            target=self._cleanup_loop,
            daemon=True
        )
        self._cleanup_thread.start()

        self._state = FirewallState.RUNNING
        self._logger.log_system("Firewall started successfully")

    def stop(self):
        """停止防火墙"""
        if self._state != FirewallState.RUNNING:
            return

        self._state = FirewallState.STOPPING
        self._logger.log_system("Stopping firewall...")

        self._running = False

        # 等待清理线程结束
        if hasattr(self, '_cleanup_thread'):
            self._cleanup_thread.join(timeout=5)

        self._state = FirewallState.STOPPED
        self._logger.log_system("Firewall stopped")

    def _cleanup_loop(self):
        """状态清理循环"""
        while self._running:
            try:
                self._connection_tracker.cleanup()
                time.sleep(10)  # 每 10 秒清理一次
            except Exception as e:
                self._logger.log_system(
                    f"Cleanup error: {e}",
                    LogLevel.ERROR
                )

    def get_statistics(self) -> Dict[str, Any]:
        """获取完整统计信息"""
        return {
            "firewall": self._statistics.to_dict(),
            "rules": self._rule_set.get_statistics(),
            "connections": self._connection_tracker.get_statistics(),
            "logger": self._logger.get_statistics(),
            "ids": self._ids.get_statistics(),
        }

    def get_connections(self) -> List[Dict[str, Any]]:
        """获取所有活动连接"""
        connections = self._connection_tracker.state_table.get_all_connections()
        return [conn.to_dict() for conn in connections]

    def get_rules(self) -> List[Dict[str, Any]]:
        """获取所有规则"""
        return [rule.to_dict() for rule in self._rule_set.rules]

    def get_recent_logs(self, count: int = 100,
                       log_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """获取最近的日志"""
        lt = None
        if log_type:
            lt = LogType(log_type)
        logs = self._logger.get_recent_logs(count, lt)
        return [log.to_dict() for log in logs]

    def get_alerts(self, count: int = 100) -> List[Dict[str, Any]]:
        """获取告警日志"""
        alerts = self._logger.get_alerts(count)
        return [alert.to_dict() for alert in alerts]

    def reset_statistics(self):
        """重置统计信息"""
        self._statistics = FirewallStatistics()
        self._statistics.start_time = time.time()
        self._ids.reset_trackers()
        self._logger.log_system("Statistics reset")

    def __enter__(self):
        """上下文管理器入口"""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.stop()
        return False
