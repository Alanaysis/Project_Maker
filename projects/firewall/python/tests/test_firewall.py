"""
防火墙主引擎测试
"""

import time
import socket
import struct
import pytest
from src.packet import Packet, PacketInfo, Protocol, TCPFlag
from src.rules import Rule, RuleAction, RuleDirection
from src.firewall import Firewall, FirewallState, FirewallConfig


class TestFirewallConfig:
    """防火墙配置测试"""

    def test_default_config(self):
        """测试默认配置"""
        config = FirewallConfig()

        assert config.name == "PythonFirewall"
        assert config.max_connections == 10000
        assert config.enable_stateful is True
        assert config.enable_ids is True
        assert config.default_action == "drop"

    def test_config_to_dict(self):
        """测试配置转字典"""
        config = FirewallConfig()
        data = config.to_dict()

        assert data["name"] == "PythonFirewall"
        assert "timeouts" in data
        assert "ids" in data

    def test_config_from_dict(self):
        """测试从字典创建配置"""
        data = {
            "name": "TestFirewall",
            "max_connections": 5000,
            "enable_stateful": False,
            "timeouts": {
                "tcp": 600,
                "udp": 120,
            },
        }

        config = FirewallConfig.from_dict(data)
        assert config.name == "TestFirewall"
        assert config.max_connections == 5000
        assert config.enable_stateful is False
        assert config.tcp_timeout == 600
        assert config.udp_timeout == 120


class TestFirewall:
    """防火墙主引擎测试"""

    def _create_tcp_packet(self, src_ip: str = "192.168.1.1",
                          dst_ip: str = "10.0.0.1",
                          src_port: int = 12345,
                          dst_port: int = 80,
                          flags: int = TCPFlag.SYN.value) -> bytes:
        """创建 TCP 数据包"""
        # IP 头
        version_ihl = (4 << 4) | 5
        tos = 0
        total_length = 40
        identification = 0
        flags_fragment = 0
        ttl = 64
        protocol_num = Protocol.TCP.value
        checksum = 0
        src = socket.inet_aton(src_ip)
        dst = socket.inet_aton(dst_ip)

        ip_header = struct.pack('!BBHHHBBH4s4s',
                               version_ihl, tos, total_length,
                               identification, flags_fragment,
                               ttl, protocol_num, checksum,
                               src, dst)

        # TCP 头
        sequence = 0
        ack_number = 0
        data_offset = (5 << 4)
        window = 65535
        tcp_checksum = 0
        urgent_pointer = 0

        tcp_header = struct.pack('!HHIIBBHHH',
                                src_port, dst_port, sequence, ack_number,
                                data_offset, flags, window, tcp_checksum, urgent_pointer)

        return ip_header + tcp_header

    def test_firewall_initialization(self):
        """测试防火墙初始化"""
        fw = Firewall()

        assert fw.state == FirewallState.STOPPED
        assert fw.is_running is False
        assert fw.statistics.packets_processed == 0

    def test_firewall_start_stop(self):
        """测试防火墙启动和停止"""
        fw = Firewall()

        # 启动
        fw.start()
        assert fw.state == FirewallState.RUNNING
        assert fw.is_running is True

        # 停止
        fw.stop()
        assert fw.state == FirewallState.STOPPED
        assert fw.is_running is False

    def test_context_manager(self):
        """测试上下文管理器"""
        config = FirewallConfig(log_dir="")  # 不创建日志目录

        with Firewall(config) as fw:
            assert fw.is_running is True

        assert fw.is_running is False

    def test_process_packet_accept(self):
        """测试处理允许的数据包"""
        config = FirewallConfig(log_dir="", enable_ids=False)
        fw = Firewall(config)
        fw.start()

        # 添加允许规则
        fw.add_rule(Rule(
            id="http-allow",
            name="HTTP Allow",
            priority=10,
            action=RuleAction.ACCEPT,
            protocol=Protocol.TCP,
            dst_port="80",
        ))

        # 创建 HTTP 数据包
        data = self._create_tcp_packet(dst_port=80)
        action = fw.process_raw_packet(data)

        assert action == RuleAction.ACCEPT
        assert fw.statistics.packets_accepted == 1

        fw.stop()

    def test_process_packet_drop(self):
        """测试处理丢弃的数据包"""
        config = FirewallConfig(log_dir="", enable_ids=False)
        fw = Firewall(config)
        fw.start()

        # 创建非 HTTP 数据包（默认丢弃）
        data = self._create_tcp_packet(dst_port=12345)
        action = fw.process_raw_packet(data)

        assert action == RuleAction.DROP
        assert fw.statistics.packets_dropped == 1

        fw.stop()

    def test_rule_priority(self):
        """测试规则优先级"""
        config = FirewallConfig(log_dir="", enable_ids=False)
        fw = Firewall(config)
        fw.start()

        # 添加低优先级允许规则
        fw.add_rule(Rule(
            id="allow-all",
            name="Allow All",
            priority=100,
            action=RuleAction.ACCEPT,
        ))

        # 添加高优先级丢弃规则
        fw.add_rule(Rule(
            id="drop-port",
            name="Drop Port 80",
            priority=10,
            action=RuleAction.DROP,
            dst_port="80",
        ))

        # 创建 HTTP 数据包（应该被高优先级规则丢弃）
        data = self._create_tcp_packet(dst_port=80)
        action = fw.process_raw_packet(data)

        assert action == RuleAction.DROP

        fw.stop()

    def test_add_remove_rule(self):
        """测试添加和删除规则"""
        fw = Firewall()

        rule = Rule(
            id="test-rule",
            name="Test Rule",
            action=RuleAction.ACCEPT,
        )

        # 添加规则
        assert fw.add_rule(rule) is True
        assert fw.rule_set.get_rule("test-rule") is not None

        # 删除规则
        assert fw.remove_rule("test-rule") is True
        assert fw.rule_set.get_rule("test-rule") is None

    def test_update_rule(self):
        """测试更新规则"""
        fw = Firewall()

        rule = Rule(
            id="test-rule",
            name="Test Rule",
            priority=100,
            action=RuleAction.ACCEPT,
        )
        fw.add_rule(rule)

        # 更新规则
        rule.priority = 50
        assert fw.update_rule(rule) is True

        updated = fw.rule_set.get_rule("test-rule")
        assert updated.priority == 50

    def test_enable_disable_rule(self):
        """测试启用/禁用规则"""
        fw = Firewall()

        rule = Rule(
            id="test-rule",
            name="Test Rule",
            action=RuleAction.ACCEPT,
        )
        fw.add_rule(rule)

        # 禁用规则
        assert fw.disable_rule("test-rule") is True

        # 启用规则
        assert fw.enable_rule("test-rule") is True

    def test_set_rule_priority(self):
        """测试设置规则优先级"""
        fw = Firewall()

        rule = Rule(
            id="test-rule",
            name="Test Rule",
            priority=100,
            action=RuleAction.ACCEPT,
        )
        fw.add_rule(rule)

        assert fw.set_rule_priority("test-rule", 50) is True
        assert rule.priority == 50

    def test_statistics(self):
        """测试统计信息"""
        config = FirewallConfig(log_dir="", enable_ids=False)
        fw = Firewall(config)
        fw.start()

        # 处理一些数据包
        for i in range(10):
            data = self._create_tcp_packet(dst_port=80 + i)
            fw.process_raw_packet(data)

        stats = fw.get_statistics()
        assert stats["firewall"]["packets_processed"] == 10
        assert "rules" in stats
        assert "connections" in stats

        fw.stop()

    def test_get_connections(self):
        """测试获取连接列表"""
        config = FirewallConfig(log_dir="", enable_ids=False)
        fw = Firewall(config)
        fw.start()

        # 创建连接
        data = self._create_tcp_packet()
        fw.process_raw_packet(data)

        connections = fw.get_connections()
        assert len(connections) >= 1

        fw.stop()

    def test_get_rules(self):
        """测试获取规则列表"""
        fw = Firewall()

        # 添加规则
        fw.add_rule(Rule(id="r1", name="R1", action=RuleAction.ACCEPT))
        fw.add_rule(Rule(id="r2", name="R2", action=RuleAction.DROP))

        rules = fw.get_rules()
        assert len(rules) >= 2

    def test_packet_callback(self):
        """测试数据包回调"""
        config = FirewallConfig(log_dir="", enable_ids=False)
        fw = Firewall(config)
        fw.start()

        processed_packets = []

        def on_packet(info, action):
            processed_packets.append((info, action))

        fw.add_packet_callback(on_packet)

        # 处理数据包
        data = self._create_tcp_packet()
        fw.process_raw_packet(data)

        assert len(processed_packets) == 1

        fw.stop()

    def test_not_running(self):
        """测试未运行时处理数据包"""
        fw = Firewall()

        data = self._create_tcp_packet()
        action = fw.process_raw_packet(data)

        # 未运行时应该丢弃
        assert action == RuleAction.DROP

    def test_reset_statistics(self):
        """测试重置统计信息"""
        config = FirewallConfig(log_dir="", enable_ids=False)
        fw = Firewall(config)
        fw.start()

        # 处理一些数据包
        data = self._create_tcp_packet()
        fw.process_raw_packet(data)

        # 重置统计
        fw.reset_statistics()

        assert fw.statistics.packets_processed == 0
        assert fw.statistics.packets_accepted == 0
        assert fw.statistics.packets_dropped == 0

        fw.stop()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
