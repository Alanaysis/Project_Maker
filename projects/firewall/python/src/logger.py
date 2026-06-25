"""
日志记录模块

实现防火墙日志记录，支持流量日志和告警日志。
"""

import os
import json
import time
import logging
import threading
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Optional, Dict, Any, List, Callable
from datetime import datetime
from .packet import PacketInfo, Protocol
from .rules import Rule, RuleAction


class LogLevel(Enum):
    """日志级别"""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    ALERT = "alert"
    CRITICAL = "critical"


class LogType(Enum):
    """日志类型"""
    TRAFFIC = "traffic"      # 流量日志
    RULE = "rule"            # 规则匹配日志
    ALERT = "alert"          # 告警日志
    STATE = "state"          # 状态变化日志
    SYSTEM = "system"        # 系统日志


@dataclass
class LogEntry:
    """日志条目

    Attributes:
        timestamp: 时间戳
        log_type: 日志类型
        level: 日志级别
        message: 日志消息
        packet_info: 数据包信息
        rule: 匹配的规则
        action: 执行的动作
        extra: 额外信息
    """
    timestamp: float = field(default_factory=time.time)
    log_type: LogType = LogType.TRAFFIC
    level: LogLevel = LogLevel.INFO
    message: str = ""
    packet_info: Optional[PacketInfo] = None
    rule: Optional[Rule] = None
    action: Optional[RuleAction] = None
    extra: Dict[str, Any] = field(default_factory=dict)

    @property
    def datetime(self) -> datetime:
        """获取日期时间对象"""
        return datetime.fromtimestamp(self.timestamp)

    def format_message(self, format_type: str = "text") -> str:
        """格式化日志消息

        Args:
            format_type: 格式类型 ("text" 或 "json")

        Returns:
            格式化后的日志消息
        """
        if format_type == "json":
            return self.to_json()

        # 文本格式
        parts = [
            self.datetime.strftime("%Y-%m-%d %H:%M:%S"),
            f"[{self.level.value.upper()}]",
            f"[{self.log_type.value}]",
        ]

        if self.packet_info:
            parts.append(str(self.packet_info))

        if self.rule:
            parts.append(f"rule={self.rule.name}")

        if self.action:
            parts.append(f"action={self.action.value}")

        if self.message:
            parts.append(self.message)

        return " | ".join(parts)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        data = {
            "timestamp": self.timestamp,
            "datetime": self.datetime.isoformat(),
            "log_type": self.log_type.value,
            "level": self.level.value,
            "message": self.message,
        }

        if self.packet_info:
            data["packet"] = {
                "src_ip": self.packet_info.src_ip,
                "dst_ip": self.packet_info.dst_ip,
                "protocol": self.packet_info.protocol.name,
                "src_port": self.packet_info.src_port,
                "dst_port": self.packet_info.dst_port,
                "length": self.packet_info.length,
            }

        if self.rule:
            data["rule"] = {
                "id": self.rule.id,
                "name": self.rule.name,
            }

        if self.action:
            data["action"] = self.action.value

        if self.extra:
            data["extra"] = self.extra

        return data

    def to_json(self) -> str:
        """转换为 JSON 字符串"""
        return json.dumps(self.to_dict(), ensure_ascii=False)


class LogBuffer:
    """日志缓冲区

    使用环形缓冲区存储日志条目，支持自动清理。
    """

    def __init__(self, max_size: int = 10000):
        """初始化日志缓冲区

        Args:
            max_size: 最大缓冲区大小
        """
        self._buffer: List[LogEntry] = []
        self._max_size = max_size
        self._lock = threading.Lock()

    def add(self, entry: LogEntry):
        """添加日志条目"""
        with self._lock:
            self._buffer.append(entry)
            if len(self._buffer) > self._max_size:
                # 移除最旧的条目
                self._buffer = self._buffer[-self._max_size:]

    def get_recent(self, count: int = 100) -> List[LogEntry]:
        """获取最近的日志条目"""
        with self._lock:
            return self._buffer[-count:]

    def get_by_type(self, log_type: LogType, count: int = 100) -> List[LogEntry]:
        """按类型获取日志条目"""
        with self._lock:
            filtered = [e for e in self._buffer if e.log_type == log_type]
            return filtered[-count:]

    def get_by_level(self, level: LogLevel, count: int = 100) -> List[LogEntry]:
        """按级别获取日志条目"""
        with self._lock:
            filtered = [e for e in self._buffer if e.level == level]
            return filtered[-count:]

    def clear(self):
        """清空缓冲区"""
        with self._lock:
            self._buffer.clear()

    @property
    def size(self) -> int:
        """获取当前缓冲区大小"""
        return len(self._buffer)


class FirewallLogger:
    """防火墙日志记录器

    提供统一的日志记录接口，支持多种输出方式。
    """

    def __init__(self, name: str = "firewall", log_dir: str = "logs"):
        """初始化日志记录器

        Args:
            name: 日志记录器名称
            log_dir: 日志文件目录
        """
        self._name = name
        self._log_dir = log_dir
        self._buffer = LogBuffer()
        self._lock = threading.Lock()

        # 日志级别过滤
        self._min_level = LogLevel.DEBUG

        # 输出配置
        self._console_output = True
        self._file_output = True
        self._json_format = False

        # 回调函数
        self._alert_callbacks: List[Callable[[LogEntry], None]] = []

        # 初始化 Python 日志记录器
        self._logger = logging.getLogger(name)
        self._logger.setLevel(logging.DEBUG)

        # 创建日志目录
        if log_dir:
            os.makedirs(log_dir, exist_ok=True)

        # 设置文件处理器
        if log_dir:
            self._setup_file_handlers()

        # 统计信息
        self._stats = {
            "total_logs": 0,
            "traffic_logs": 0,
            "alert_logs": 0,
            "rule_logs": 0,
        }

    def _setup_file_handlers(self):
        """设置文件处理器"""
        # 流量日志
        traffic_handler = logging.FileHandler(
            os.path.join(self._log_dir, "traffic.log"),
            encoding='utf-8'
        )
        traffic_handler.setLevel(logging.DEBUG)
        traffic_formatter = logging.Formatter(
            '%(asctime)s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        traffic_handler.setFormatter(traffic_formatter)

        # 告警日志
        alert_handler = logging.FileHandler(
            os.path.join(self._log_dir, "alerts.log"),
            encoding='utf-8'
        )
        alert_handler.setLevel(logging.WARNING)
        alert_formatter = logging.Formatter(
            '%(asctime)s | %(levelname)s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        alert_handler.setFormatter(alert_formatter)

        self._logger.addHandler(traffic_handler)
        self._logger.addHandler(alert_handler)

    def set_level(self, level: LogLevel):
        """设置最小日志级别"""
        self._min_level = level

    def enable_console_output(self, enabled: bool = True):
        """启用/禁用控制台输出"""
        self._console_output = enabled

    def enable_json_format(self, enabled: bool = True):
        """启用/禁用 JSON 格式"""
        self._json_format = enabled

    def add_alert_callback(self, callback: Callable[[LogEntry], None]):
        """添加告警回调函数

        Args:
            callback: 回调函数，接收 LogEntry 参数
        """
        self._alert_callbacks.append(callback)

    def _should_log(self, level: LogLevel) -> bool:
        """检查是否应该记录日志"""
        levels = list(LogLevel)
        return levels.index(level) >= levels.index(self._min_level)

    def _log(self, entry: LogEntry):
        """内部日志记录方法"""
        if not self._should_log(entry.level):
            return

        with self._lock:
            # 添加到缓冲区
            self._buffer.add(entry)

            # 更新统计
            self._stats["total_logs"] += 1
            if entry.log_type == LogType.TRAFFIC:
                self._stats["traffic_logs"] += 1
            elif entry.log_type == LogType.ALERT:
                self._stats["alert_logs"] += 1
            elif entry.log_type == LogType.RULE:
                self._stats["rule_logs"] += 1

            # 格式化消息
            format_type = "json" if self._json_format else "text"
            message = entry.format_message(format_type)

            # 控制台输出
            if self._console_output:
                level_colors = {
                    LogLevel.DEBUG: "\033[36m",    # 青色
                    LogLevel.INFO: "\033[32m",     # 绿色
                    LogLevel.WARNING: "\033[33m",  # 黄色
                    LogLevel.ERROR: "\033[31m",    # 红色
                    LogLevel.ALERT: "\033[35m",    # 紫色
                    LogLevel.CRITICAL: "\033[41m", # 红色背景
                }
                color = level_colors.get(entry.level, "")
                reset = "\033[0m"
                print(f"{color}{message}{reset}")

            # 文件输出
            if self._file_output:
                log_level = {
                    LogLevel.DEBUG: logging.DEBUG,
                    LogLevel.INFO: logging.INFO,
                    LogLevel.WARNING: logging.WARNING,
                    LogLevel.ERROR: logging.ERROR,
                    LogLevel.ALERT: logging.WARNING,
                    LogLevel.CRITICAL: logging.CRITICAL,
                }.get(entry.level, logging.INFO)
                self._logger.log(log_level, entry.format_message("text"))

            # 告警回调
            if entry.log_type == LogType.ALERT:
                for callback in self._alert_callbacks:
                    try:
                        callback(entry)
                    except Exception:
                        pass

    def log_traffic(self, packet_info: PacketInfo, action: RuleAction,
                   rule: Optional[Rule] = None, message: str = ""):
        """记录流量日志

        Args:
            packet_info: 数据包信息
            action: 执行的动作
            rule: 匹配的规则
            message: 额外消息
        """
        entry = LogEntry(
            log_type=LogType.TRAFFIC,
            level=LogLevel.INFO,
            message=message,
            packet_info=packet_info,
            rule=rule,
            action=action,
        )
        self._log(entry)

    def log_rule_match(self, packet_info: PacketInfo, rule: Rule,
                      action: RuleAction):
        """记录规则匹配日志

        Args:
            packet_info: 数据包信息
            rule: 匹配的规则
            action: 执行的动作
        """
        entry = LogEntry(
            log_type=LogType.RULE,
            level=LogLevel.INFO,
            message=f"Rule matched: {rule.name}",
            packet_info=packet_info,
            rule=rule,
            action=action,
        )
        self._log(entry)

    def log_alert(self, message: str, packet_info: Optional[PacketInfo] = None,
                 level: LogLevel = LogLevel.ALERT, extra: Optional[Dict] = None):
        """记录告警日志

        Args:
            message: 告警消息
            packet_info: 相关数据包信息
            level: 告警级别
            extra: 额外信息
        """
        entry = LogEntry(
            log_type=LogType.ALERT,
            level=level,
            message=message,
            packet_info=packet_info,
            extra=extra or {},
        )
        self._log(entry)

    def log_state_change(self, message: str, packet_info: Optional[PacketInfo] = None):
        """记录状态变化日志

        Args:
            message: 状态变化消息
            packet_info: 相关数据包信息
        """
        entry = LogEntry(
            log_type=LogType.STATE,
            level=LogLevel.INFO,
            message=message,
            packet_info=packet_info,
        )
        self._log(entry)

    def log_system(self, message: str, level: LogLevel = LogLevel.INFO):
        """记录系统日志

        Args:
            message: 系统消息
            level: 日志级别
        """
        entry = LogEntry(
            log_type=LogType.SYSTEM,
            level=level,
            message=message,
        )
        self._log(entry)

    def log_dropped(self, packet_info: PacketInfo, reason: str = "",
                   rule: Optional[Rule] = None):
        """记录丢弃数据包日志

        Args:
            packet_info: 数据包信息
            reason: 丢弃原因
            rule: 匹配的规则
        """
        message = f"Packet dropped: {reason}" if reason else "Packet dropped"
        entry = LogEntry(
            log_type=LogType.TRAFFIC,
            level=LogLevel.WARNING,
            message=message,
            packet_info=packet_info,
            rule=rule,
            action=RuleAction.DROP,
        )
        self._log(entry)

    def log_accepted(self, packet_info: PacketInfo, rule: Optional[Rule] = None):
        """记录允许数据包日志

        Args:
            packet_info: 数据包信息
            rule: 匹配的规则
        """
        entry = LogEntry(
            log_type=LogType.TRAFFIC,
            level=LogLevel.INFO,
            message="Packet accepted",
            packet_info=packet_info,
            rule=rule,
            action=RuleAction.ACCEPT,
        )
        self._log(entry)

    def get_recent_logs(self, count: int = 100,
                       log_type: Optional[LogType] = None) -> List[LogEntry]:
        """获取最近的日志条目

        Args:
            count: 返回条目数
            log_type: 日志类型过滤

        Returns:
            日志条目列表
        """
        if log_type:
            return self._buffer.get_by_type(log_type, count)
        return self._buffer.get_recent(count)

    def get_alerts(self, count: int = 100) -> List[LogEntry]:
        """获取告警日志"""
        return self._buffer.get_by_type(LogType.ALERT, count)

    def get_statistics(self) -> Dict[str, Any]:
        """获取日志统计信息"""
        return {
            **self._stats,
            "buffer_size": self._buffer.size,
            "min_level": self._min_level.value,
        }

    def clear(self):
        """清空日志缓冲区"""
        self._buffer.clear()


class IntrusionDetector:
    """入侵检测器

    基于日志分析检测异常行为。
    """

    def __init__(self, logger: FirewallLogger):
        """初始化入侵检测器

        Args:
            logger: 日志记录器
        """
        self._logger = logger
        self._connection_attempts: Dict[str, List[float]] = {}
        self._port_scan_tracker: Dict[str, set] = {}
        self._syn_flood_tracker: Dict[str, int] = {}

        # 阈值配置
        self._max_connections_per_minute = 100
        self._max_ports_per_minute = 20
        self._syn_flood_threshold = 1000

        self._lock = threading.Lock()

    def analyze_packet(self, packet_info: PacketInfo, action: RuleAction):
        """分析数据包，检测异常行为

        Args:
            packet_info: 数据包信息
            action: 执行的动作
        """
        current_time = time.time()

        with self._lock:
            # 检测连接频率异常
            self._check_connection_rate(packet_info, current_time)

            # 检测端口扫描
            if packet_info.is_tcp:
                self._check_port_scan(packet_info, current_time)

            # 检测 SYN Flood
            if packet_info.is_tcp and packet_info.tcp_flags is not None:
                self._check_syn_flood(packet_info, current_time)

    def _check_connection_rate(self, packet_info: PacketInfo, current_time: float):
        """检查连接频率"""
        src_ip = packet_info.src_ip

        if src_ip not in self._connection_attempts:
            self._connection_attempts[src_ip] = []

        # 清理过期记录
        self._connection_attempts[src_ip] = [
            t for t in self._connection_attempts[src_ip]
            if current_time - t < 60
        ]

        # 添加新记录
        self._connection_attempts[src_ip].append(current_time)

        # 检查是否超过阈值
        if len(self._connection_attempts[src_ip]) > self._max_connections_per_minute:
            self._logger.log_alert(
                f"High connection rate from {src_ip}: "
                f"{len(self._connection_attempts[src_ip])} connections/minute",
                packet_info=packet_info,
                level=LogLevel.ALERT,
                extra={"src_ip": src_ip, "rate": len(self._connection_attempts[src_ip])}
            )

    def _check_port_scan(self, packet_info: PacketInfo, current_time: float):
        """检查端口扫描"""
        src_ip = packet_info.src_ip
        dst_port = packet_info.dst_port

        if dst_port is None:
            return

        if src_ip not in self._port_scan_tracker:
            self._port_scan_tracker[src_ip] = set()

        self._port_scan_tracker[src_ip].add(dst_port)

        # 检查是否扫描了太多端口
        if len(self._port_scan_tracker[src_ip]) > self._max_ports_per_minute:
            self._logger.log_alert(
                f"Possible port scan from {src_ip}: "
                f"{len(self._port_scan_tracker[src_ip])} ports scanned",
                packet_info=packet_info,
                level=LogLevel.ALERT,
                extra={"src_ip": src_ip, "ports_scanned": len(self._port_scan_tracker[src_ip])}
            )

    def _check_syn_flood(self, packet_info: PacketInfo, current_time: float):
        """检查 SYN Flood 攻击"""
        # 检查是否为 SYN 包
        if packet_info.tcp_flags is None:
            return

        from .packet import TCPFlag
        is_syn = bool(packet_info.tcp_flags & TCPFlag.SYN.value)
        is_ack = bool(packet_info.tcp_flags & TCPFlag.ACK.value)

        if is_syn and not is_ack:
            src_ip = packet_info.src_ip
            if src_ip not in self._syn_flood_tracker:
                self._syn_flood_tracker[src_ip] = 0

            self._syn_flood_tracker[src_ip] += 1

            if self._syn_flood_tracker[src_ip] > self._syn_flood_threshold:
                self._logger.log_alert(
                    f"Possible SYN flood from {src_ip}: "
                    f"{self._syn_flood_tracker[src_ip]} SYN packets",
                    packet_info=packet_info,
                    level=LogLevel.CRITICAL,
                    extra={"src_ip": src_ip, "syn_count": self._syn_flood_tracker[src_ip]}
                )

    def reset_trackers(self):
        """重置跟踪器"""
        with self._lock:
            self._connection_attempts.clear()
            self._port_scan_tracker.clear()
            self._syn_flood_tracker.clear()

    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        with self._lock:
            return {
                "tracked_ips": len(self._connection_attempts),
                "port_scan_ips": len(self._port_scan_tracker),
                "syn_flood_ips": len(self._syn_flood_tracker),
            }
