"""
状态检测模块

实现连接状态跟踪和状态表管理，支持 TCP/UDP/ICMP 连接状态。
"""

import time
import threading
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Dict, Optional, Tuple, List, Any
from .packet import Packet, PacketInfo, Protocol, TCPFlag


class ConnectionState(Enum):
    """连接状态

    TCP 状态机：
    NEW -> ESTABLISHED -> FIN_WAIT -> CLOSED
                        -> TIME_WAIT -> CLOSED
    """
    NEW = "new"                      # 新连接
    ESTABLISHED = "established"      # 已建立连接
    RELATED = "related"              # 相关连接
    FIN_WAIT = "fin_wait"            # 等待关闭
    CLOSE_WAIT = "close_wait"        # 等待关闭确认
    TIME_WAIT = "time_wait"          # 等待超时
    LAST_ACK = "last_ack"            # 最后确认
    CLOSED = "closed"                # 已关闭
    INVALID = "invalid"              # 无效状态


class TCPState(Enum):
    """TCP 连接状态机"""
    LISTEN = auto()
    SYN_SENT = auto()
    SYN_RECEIVED = auto()
    ESTABLISHED = auto()
    FIN_WAIT_1 = auto()
    FIN_WAIT_2 = auto()
    CLOSE_WAIT = auto()
    CLOSING = auto()
    LAST_ACK = auto()
    TIME_WAIT = auto()
    CLOSED = auto()


@dataclass
class ConnectionEntry:
    """连接表项

    Attributes:
        key: 连接标识 (protocol, src_ip, src_port, dst_ip, dst_port)
        state: 连接状态
        protocol: 协议类型
        src_ip: 源 IP
        src_port: 源端口
        dst_ip: 目的 IP
        dst_port: 目的端口
        created_at: 创建时间
        last_seen: 最后活动时间
        bytes_sent: 发送字节数
        bytes_received: 接收字节数
        packets_sent: 发送数据包数
        packets_received: 接收数据包数
        tcp_state: TCP 状态机状态
        timeout: 超时时间（秒）
    """
    key: str
    state: ConnectionState
    protocol: Protocol
    src_ip: str
    src_port: Optional[int]
    dst_ip: str
    dst_port: Optional[int]
    created_at: float = field(default_factory=time.time)
    last_seen: float = field(default_factory=time.time)
    bytes_sent: int = 0
    bytes_received: int = 0
    packets_sent: int = 0
    packets_received: int = 0
    tcp_state: TCPState = TCPState.CLOSED
    timeout: int = 300  # 默认 5 分钟超时

    @property
    def duration(self) -> float:
        """连接持续时间"""
        return self.last_seen - self.created_at

    @property
    def is_expired(self) -> bool:
        """检查是否过期"""
        return time.time() - self.last_seen > self.timeout

    def update_activity(self, is_outgoing: bool, packet_size: int):
        """更新活动统计"""
        self.last_seen = time.time()
        if is_outgoing:
            self.bytes_sent += packet_size
            self.packets_sent += 1
        else:
            self.bytes_received += packet_size
            self.packets_received += 1

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "key": self.key,
            "state": self.state.value,
            "protocol": self.protocol.name,
            "src_ip": self.src_ip,
            "src_port": self.src_port,
            "dst_ip": self.dst_ip,
            "dst_port": self.dst_port,
            "created_at": self.created_at,
            "last_seen": self.last_seen,
            "duration": self.duration,
            "bytes_sent": self.bytes_sent,
            "bytes_received": self.bytes_received,
            "packets_sent": self.packets_sent,
            "packets_received": self.packets_received,
            "tcp_state": self.tcp_state.name,
            "timeout": self.timeout,
            "is_expired": self.is_expired,
        }


class StateTable:
    """状态表

    管理所有活动连接的状态信息。
    """

    # 超时配置（秒）
    TCP_TIMEOUT = 300       # TCP 连接超时 5 分钟
    TCP_FIN_TIMEOUT = 30    # FIN_WAIT 超时 30 秒
    UDP_TIMEOUT = 60        # UDP 超时 1 分钟
    ICMP_TIMEOUT = 30       # ICMP 超时 30 秒

    def __init__(self, max_entries: int = 10000):
        """初始化状态表

        Args:
            max_entries: 最大连接表项数
        """
        self._entries: Dict[str, ConnectionEntry] = {}
        self._max_entries = max_entries
        self._lock = threading.RLock()

    def _make_key(self, protocol: Protocol, src_ip: str, src_port: Optional[int],
                  dst_ip: str, dst_port: Optional[int]) -> str:
        """生成连接标识键

        使用双向匹配：将较小的 IP:Port 放在前面
        """
        if src_port is not None and dst_port is not None:
            # TCP/UDP: 双向匹配
            src = f"{src_ip}:{src_port}"
            dst = f"{dst_ip}:{dst_port}"
            if (src_ip, src_port) > (dst_ip, dst_port):
                src, dst = dst, src
            return f"{protocol.name}:{src}-{dst}"
        else:
            # ICMP: 使用 identifier
            return f"{protocol.name}:{src_ip}-{dst_ip}"

    def _get_timeout(self, protocol: Protocol) -> int:
        """获取协议对应的超时时间"""
        if protocol == Protocol.TCP:
            return self.TCP_TIMEOUT
        elif protocol == Protocol.UDP:
            return self.UDP_TIMEOUT
        elif protocol == Protocol.ICMP:
            return self.ICMP_TIMEOUT
        return 300

    def get_connection(self, packet_info: PacketInfo) -> Optional[ConnectionEntry]:
        """获取连接表项

        Args:
            packet_info: 数据包信息

        Returns:
            连接表项，不存在返回 None
        """
        key = self._make_key(
            packet_info.protocol,
            packet_info.src_ip,
            packet_info.src_port,
            packet_info.dst_ip,
            packet_info.dst_port,
        )

        with self._lock:
            entry = self._entries.get(key)
            if entry is not None and entry.is_expired:
                del self._entries[key]
                return None
            return entry

    def create_connection(self, packet_info: PacketInfo,
                         is_outgoing: bool = True) -> ConnectionEntry:
        """创建新连接

        Args:
            packet_info: 数据包信息
            is_outgoing: 是否为出站连接

        Returns:
            新创建的连接表项
        """
        key = self._make_key(
            packet_info.protocol,
            packet_info.src_ip,
            packet_info.src_port,
            packet_info.dst_ip,
            packet_info.dst_port,
        )

        with self._lock:
            # 检查是否超过最大连接数
            if len(self._entries) >= self._max_entries:
                self._cleanup_expired()
                if len(self._entries) >= self._max_entries:
                    # 移除最旧的连接
                    oldest_key = min(
                        self._entries.keys(),
                        key=lambda k: self._entries[k].last_seen
                    )
                    del self._entries[oldest_key]

            timeout = self._get_timeout(packet_info.protocol)

            # 设置 TCP 初始状态
            tcp_state = TCPState.CLOSED
            if packet_info.is_tcp:
                if is_outgoing:
                    tcp_state = TCPState.SYN_SENT
                else:
                    tcp_state = TCPState.SYN_RECEIVED

            entry = ConnectionEntry(
                key=key,
                state=ConnectionState.NEW,
                protocol=packet_info.protocol,
                src_ip=packet_info.src_ip,
                src_port=packet_info.src_port,
                dst_ip=packet_info.dst_ip,
                dst_port=packet_info.dst_port,
                timeout=timeout,
                tcp_state=tcp_state,
            )
            entry.update_activity(is_outgoing, packet_info.length)

            self._entries[key] = entry
            return entry

    def update_connection(self, packet_info: PacketInfo,
                         is_outgoing: bool = True) -> Optional[ConnectionEntry]:
        """更新连接状态

        Args:
            packet_info: 数据包信息
            is_outgoing: 是否为出站流量

        Returns:
            更新后的连接表项，不存在返回 None
        """
        entry = self.get_connection(packet_info)
        if entry is None:
            return None

        with self._lock:
            entry.update_activity(is_outgoing, packet_info.length)

            # 更新 TCP 状态机
            if packet_info.is_tcp and packet_info.tcp_flags is not None:
                self._update_tcp_state(entry, packet_info)

            return entry

    def _update_tcp_state(self, entry: ConnectionEntry, packet_info: PacketInfo):
        """更新 TCP 状态机

        TCP 状态转换：
        CLOSED -> SYN_SENT -> ESTABLISHED -> FIN_WAIT_1 -> FIN_WAIT_2 -> TIME_WAIT -> CLOSED
        CLOSED -> SYN_RECEIVED -> ESTABLISHED -> CLOSE_WAIT -> LAST_ACK -> CLOSED
        """
        flags = packet_info.tcp_flags
        is_syn = bool(flags & TCPFlag.SYN.value)
        is_ack = bool(flags & TCPFlag.ACK.value)
        is_fin = bool(flags & TCPFlag.FIN.value)
        is_rst = bool(flags & TCPFlag.RST.value)

        # RST 直接关闭连接
        if is_rst:
            entry.tcp_state = TCPState.CLOSED
            entry.state = ConnectionState.CLOSED
            return

        # 状态转换
        if entry.tcp_state == TCPState.SYN_SENT:
            if is_syn and is_ack:
                entry.tcp_state = TCPState.ESTABLISHED
                entry.state = ConnectionState.ESTABLISHED
            elif is_syn:
                entry.tcp_state = TCPState.SYN_RECEIVED

        elif entry.tcp_state == TCPState.SYN_RECEIVED:
            if is_ack:
                entry.tcp_state = TCPState.ESTABLISHED
                entry.state = ConnectionState.ESTABLISHED

        elif entry.tcp_state == TCPState.ESTABLISHED:
            if is_fin:
                entry.tcp_state = TCPState.FIN_WAIT_1
                entry.state = ConnectionState.FIN_WAIT
                entry.timeout = self.TCP_FIN_TIMEOUT

        elif entry.tcp_state == TCPState.FIN_WAIT_1:
            if is_ack:
                entry.tcp_state = TCPState.FIN_WAIT_2
            elif is_fin:
                entry.tcp_state = TCPState.CLOSING

        elif entry.tcp_state == TCPState.FIN_WAIT_2:
            if is_fin:
                entry.tcp_state = TCPState.TIME_WAIT
                entry.state = ConnectionState.TIME_WAIT

        elif entry.tcp_state == TCPState.CLOSING:
            if is_ack:
                entry.tcp_state = TCPState.TIME_WAIT
                entry.state = ConnectionState.TIME_WAIT

        elif entry.tcp_state == TCPState.CLOSE_WAIT:
            if is_fin:
                entry.tcp_state = TCPState.LAST_ACK
                entry.state = ConnectionState.LAST_ACK

        elif entry.tcp_state == TCPState.LAST_ACK:
            if is_ack:
                entry.tcp_state = TCPState.CLOSED
                entry.state = ConnectionState.CLOSED

        elif entry.tcp_state == TCPState.TIME_WAIT:
            # 等待超时后自动清理
            pass

    def remove_connection(self, packet_info: PacketInfo) -> bool:
        """移除连接

        Args:
            packet_info: 数据包信息

        Returns:
            是否成功移除
        """
        key = self._make_key(
            packet_info.protocol,
            packet_info.src_ip,
            packet_info.src_port,
            packet_info.dst_ip,
            packet_info.dst_port,
        )

        with self._lock:
            if key in self._entries:
                del self._entries[key]
                return True
            return False

    def _cleanup_expired(self):
        """清理过期连接"""
        current_time = time.time()
        expired_keys = [
            key for key, entry in self._entries.items()
            if current_time - entry.last_seen > entry.timeout
        ]
        for key in expired_keys:
            del self._entries[key]

    def get_all_connections(self) -> List[ConnectionEntry]:
        """获取所有活动连接"""
        with self._lock:
            self._cleanup_expired()
            return list(self._entries.values())

    def get_connection_count(self) -> int:
        """获取活动连接数"""
        with self._lock:
            self._cleanup_expired()
            return len(self._entries)

    def get_statistics(self) -> Dict[str, Any]:
        """获取状态表统计信息"""
        with self._lock:
            self._cleanup_expired()

            protocol_counts = {}
            state_counts = {}

            for entry in self._entries.values():
                # 协议统计
                proto = entry.protocol.name
                protocol_counts[proto] = protocol_counts.get(proto, 0) + 1

                # 状态统计
                state = entry.state.value
                state_counts[state] = state_counts.get(state, 0) + 1

            return {
                "total_connections": len(self._entries),
                "max_entries": self._max_entries,
                "protocol_counts": protocol_counts,
                "state_counts": state_counts,
            }

    def clear(self):
        """清空状态表"""
        with self._lock:
            self._entries.clear()


class ConnectionTracker:
    """连接跟踪器

    高级连接跟踪接口，整合状态表和数据包处理。
    """

    def __init__(self, max_connections: int = 10000):
        """初始化连接跟踪器

        Args:
            max_connections: 最大连接数
        """
        self._state_table = StateTable(max_entries=max_connections)
        self._new_connection_callback = None
        self._connection_closed_callback = None

    @property
    def state_table(self) -> StateTable:
        """获取状态表"""
        return self._state_table

    def set_callbacks(self, on_new=None, on_closed=None):
        """设置回调函数

        Args:
            on_new: 新连接回调 (entry: ConnectionEntry)
            on_closed: 连接关闭回调 (entry: ConnectionEntry)
        """
        self._new_connection_callback = on_new
        self._connection_closed_callback = on_closed

    def process_packet(self, packet_info: PacketInfo,
                      is_outgoing: bool = True) -> Tuple[ConnectionState, Optional[ConnectionEntry]]:
        """处理数据包，更新连接状态

        Args:
            packet_info: 数据包信息
            is_outgoing: 是否为出站流量

        Returns:
            (连接状态, 连接表项) 元组
        """
        # 查找现有连接
        entry = self._state_table.get_connection(packet_info)

        if entry is None:
            # 新连接
            entry = self._state_table.create_connection(packet_info, is_outgoing)

            if self._new_connection_callback:
                self._new_connection_callback(entry)

            return entry.state, entry
        else:
            # 更新现有连接
            old_state = entry.state
            entry = self._state_table.update_connection(packet_info, is_outgoing)

            # 检查连接是否关闭
            if old_state != ConnectionState.CLOSED and entry.state == ConnectionState.CLOSED:
                if self._connection_closed_callback:
                    self._connection_closed_callback(entry)

            return entry.state, entry

    def is_established(self, packet_info: PacketInfo) -> bool:
        """检查连接是否已建立

        Args:
            packet_info: 数据包信息

        Returns:
            连接是否已建立
        """
        entry = self._state_table.get_connection(packet_info)
        if entry is None:
            return False
        return entry.state == ConnectionState.ESTABLISHED

    def get_connection_info(self, packet_info: PacketInfo) -> Optional[Dict[str, Any]]:
        """获取连接信息

        Args:
            packet_info: 数据包信息

        Returns:
            连接信息字典，不存在返回 None
        """
        entry = self._state_table.get_connection(packet_info)
        if entry is None:
            return None
        return entry.to_dict()

    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        return self._state_table.get_statistics()

    def cleanup(self):
        """清理过期连接"""
        self._state_table._cleanup_expired()
