"""
状态检测测试
"""

import time
import pytest
from src.packet import PacketInfo, Protocol, TCPFlag
from src.state import (
    ConnectionState, TCPState, ConnectionEntry, StateTable, ConnectionTracker
)


class TestConnectionEntry:
    """连接表项测试"""

    def test_create_entry(self):
        """测试创建连接表项"""
        entry = ConnectionEntry(
            key="TCP:192.168.1.1:12345-10.0.0.1:80",
            state=ConnectionState.NEW,
            protocol=Protocol.TCP,
            src_ip="192.168.1.1",
            src_port=12345,
            dst_ip="10.0.0.1",
            dst_port=80,
        )

        assert entry.state == ConnectionState.NEW
        assert entry.protocol == Protocol.TCP
        assert entry.src_ip == "192.168.1.1"
        assert entry.dst_port == 80

    def test_update_activity(self):
        """测试更新活动统计"""
        entry = ConnectionEntry(
            key="test",
            state=ConnectionState.NEW,
            protocol=Protocol.TCP,
            src_ip="192.168.1.1",
            src_port=12345,
            dst_ip="10.0.0.1",
            dst_port=80,
        )

        # 出站流量
        entry.update_activity(is_outgoing=True, packet_size=100)
        assert entry.bytes_sent == 100
        assert entry.packets_sent == 1

        # 入站流量
        entry.update_activity(is_outgoing=False, packet_size=200)
        assert entry.bytes_received == 200
        assert entry.packets_received == 1

    def test_is_expired(self):
        """测试过期检查"""
        entry = ConnectionEntry(
            key="test",
            state=ConnectionState.NEW,
            protocol=Protocol.TCP,
            src_ip="192.168.1.1",
            src_port=12345,
            dst_ip="10.0.0.1",
            dst_port=80,
            timeout=60,
        )

        # 刚创建，未过期
        assert entry.is_expired is False

        # 模拟过期
        entry.last_seen = time.time() - 100
        assert entry.is_expired is True

    def test_duration(self):
        """测试连接持续时间"""
        now = time.time()
        entry = ConnectionEntry(
            key="test",
            state=ConnectionState.NEW,
            protocol=Protocol.TCP,
            src_ip="192.168.1.1",
            src_port=12345,
            dst_ip="10.0.0.1",
            dst_port=80,
        )

        # 设置创建时间为 10 秒前
        entry.created_at = now - 10
        entry.last_seen = now
        assert entry.duration >= 10

    def test_to_dict(self):
        """测试转换为字典"""
        entry = ConnectionEntry(
            key="test",
            state=ConnectionState.NEW,
            protocol=Protocol.TCP,
            src_ip="192.168.1.1",
            src_port=12345,
            dst_ip="10.0.0.1",
            dst_port=80,
        )

        data = entry.to_dict()
        assert data["key"] == "test"
        assert data["state"] == "new"
        assert data["protocol"] == "TCP"
        assert data["src_ip"] == "192.168.1.1"
        assert data["dst_port"] == 80


class TestStateTable:
    """状态表测试"""

    def _create_packet_info(self, src_ip: str = "192.168.1.1",
                           dst_ip: str = "10.0.0.1",
                           src_port: int = 12345,
                           dst_port: int = 80,
                           protocol: Protocol = Protocol.TCP) -> PacketInfo:
        """创建测试用数据包信息"""
        return PacketInfo(
            timestamp=time.time(),
            src_ip=src_ip,
            dst_ip=dst_ip,
            protocol=protocol,
            src_port=src_port,
            dst_port=dst_port,
        )

    def test_create_connection(self):
        """测试创建连接"""
        table = StateTable()
        info = self._create_packet_info()

        entry = table.create_connection(info)
        assert entry is not None
        assert entry.state == ConnectionState.NEW
        assert entry.protocol == Protocol.TCP

    def test_get_connection(self):
        """测试获取连接"""
        table = StateTable()
        info = self._create_packet_info()

        # 创建连接
        table.create_connection(info)

        # 获取连接
        entry = table.get_connection(info)
        assert entry is not None
        assert entry.src_ip == "192.168.1.1"

    def test_get_nonexistent_connection(self):
        """测试获取不存在的连接"""
        table = StateTable()
        info = self._create_packet_info()

        entry = table.get_connection(info)
        assert entry is None

    def test_update_connection(self):
        """测试更新连接"""
        table = StateTable()
        info = self._create_packet_info()

        # 创建连接
        table.create_connection(info)

        # 更新连接
        entry = table.update_connection(info)
        assert entry is not None
        assert entry.packets_sent >= 1

    def test_remove_connection(self):
        """测试移除连接"""
        table = StateTable()
        info = self._create_packet_info()

        # 创建连接
        table.create_connection(info)

        # 移除连接
        assert table.remove_connection(info) is True
        assert table.get_connection(info) is None

    def test_remove_nonexistent_connection(self):
        """测试移除不存在的连接"""
        table = StateTable()
        info = self._create_packet_info()

        assert table.remove_connection(info) is False

    def test_bidirectional_matching(self):
        """测试双向匹配"""
        table = StateTable()

        # 创建出站连接
        out_info = self._create_packet_info(
            src_ip="192.168.1.1", dst_ip="10.0.0.1",
            src_port=12345, dst_port=80
        )
        table.create_connection(out_info, is_outgoing=True)

        # 创建入站响应
        in_info = self._create_packet_info(
            src_ip="10.0.0.1", dst_ip="192.168.1.1",
            src_port=80, dst_port=12345
        )

        # 应该匹配同一个连接
        entry = table.get_connection(in_info)
        assert entry is not None

    def test_connection_count(self):
        """测试连接计数"""
        table = StateTable()

        # 创建多个连接
        for i in range(5):
            info = self._create_packet_info(src_port=10000 + i)
            table.create_connection(info)

        assert table.get_connection_count() == 5

    def test_statistics(self):
        """测试统计信息"""
        table = StateTable()

        # 创建 TCP 连接
        info1 = self._create_packet_info(protocol=Protocol.TCP)
        table.create_connection(info1)

        # 创建 UDP 连接
        info2 = self._create_packet_info(protocol=Protocol.UDP, dst_port=53)
        table.create_connection(info2)

        stats = table.get_statistics()
        assert stats["total_connections"] == 2
        assert stats["protocol_counts"]["TCP"] == 1
        assert stats["protocol_counts"]["UDP"] == 1

    def test_max_entries(self):
        """测试最大连接数限制"""
        table = StateTable(max_entries=3)

        # 创建超过限制的连接
        for i in range(5):
            info = self._create_packet_info(src_port=10000 + i)
            table.create_connection(info)

        # 应该清理过期连接或移除最旧的连接
        assert table.get_connection_count() <= 3

    def test_cleanup_expired(self):
        """测试清理过期连接"""
        table = StateTable()

        # 创建连接
        info = self._create_packet_info()
        entry = table.create_connection(info)

        # 模拟过期
        entry.last_seen = time.time() - 1000

        # 清理
        table._cleanup_expired()

        assert table.get_connection_count() == 0


class TestConnectionTracker:
    """连接跟踪器测试"""

    def _create_packet_info(self, src_ip: str = "192.168.1.1",
                           dst_ip: str = "10.0.0.1",
                           src_port: int = 12345,
                           dst_port: int = 80,
                           protocol: Protocol = Protocol.TCP,
                           tcp_flags: int = None) -> PacketInfo:
        """创建测试用数据包信息"""
        return PacketInfo(
            timestamp=time.time(),
            src_ip=src_ip,
            dst_ip=dst_ip,
            protocol=protocol,
            src_port=src_port,
            dst_port=dst_port,
            tcp_flags=tcp_flags,
        )

    def test_new_connection(self):
        """测试新连接"""
        tracker = ConnectionTracker()
        info = self._create_packet_info(tcp_flags=TCPFlag.SYN.value)

        state, entry = tracker.process_packet(info)
        assert state == ConnectionState.NEW
        assert entry is not None

    def test_established_connection(self):
        """测试已建立连接"""
        tracker = ConnectionTracker()

        # SYN
        syn_info = self._create_packet_info(tcp_flags=TCPFlag.SYN.value)
        tracker.process_packet(syn_info, is_outgoing=True)

        # SYN-ACK
        syn_ack_info = self._create_packet_info(
            src_ip="10.0.0.1", dst_ip="192.168.1.1",
            src_port=80, dst_port=12345,
            tcp_flags=TCPFlag.SYN.value | TCPFlag.ACK.value
        )
        state, entry = tracker.process_packet(syn_ack_info, is_outgoing=False)

        # 应该建立连接
        assert entry.state == ConnectionState.ESTABLISHED

    def test_is_established(self):
        """测试检查已建立连接"""
        tracker = ConnectionTracker()

        # 未建立的连接
        info = self._create_packet_info()
        assert tracker.is_established(info) is False

    def test_callbacks(self):
        """测试回调函数"""
        tracker = ConnectionTracker()

        new_connections = []
        closed_connections = []

        def on_new(entry):
            new_connections.append(entry)

        def on_closed(entry):
            closed_connections.append(entry)

        tracker.set_callbacks(on_new=on_new, on_closed=closed_connections)

        # 创建新连接
        info = self._create_packet_info(tcp_flags=TCPFlag.SYN.value)
        tracker.process_packet(info)

        assert len(new_connections) == 1

    def test_statistics(self):
        """测试统计信息"""
        tracker = ConnectionTracker()

        # 创建连接
        info = self._create_packet_info()
        tracker.process_packet(info)

        stats = tracker.get_statistics()
        assert stats["total_connections"] >= 1

    def test_get_connection_info(self):
        """测试获取连接信息"""
        tracker = ConnectionTracker()

        info = self._create_packet_info()
        tracker.process_packet(info)

        conn_info = tracker.get_connection_info(info)
        assert conn_info is not None
        assert conn_info["src_ip"] == "192.168.1.1"

    def test_cleanup(self):
        """测试清理"""
        tracker = ConnectionTracker()

        # 创建连接
        info = self._create_packet_info()
        entry = tracker.process_packet(info)[1]

        # 模拟过期
        entry.last_seen = time.time() - 1000

        # 清理
        tracker.cleanup()

        assert tracker.get_statistics()["total_connections"] == 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
