#!/usr/bin/env python3
"""
基本防火墙示例

演示如何使用防火墙进行包过滤和规则管理。
"""

import sys
import os
import time

# 添加父目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src import (
    Firewall, FirewallConfig, FirewallState,
    Rule, RuleSet, RuleAction, RuleDirection,
    Packet, PacketInfo, Protocol, TCPFlag,
    RuleBuilder,
)


def create_test_packet(src_ip: str, dst_ip: str,
                      src_port: int, dst_port: int,
                      protocol: Protocol = Protocol.TCP,
                      flags: int = TCPFlag.SYN.value) -> Packet:
    """创建测试数据包"""
    import struct
    import socket

    # IP 头
    version_ihl = (4 << 4) | 5
    tos = 0
    total_length = 40
    identification = 0
    flags_fragment = 0
    ttl = 64
    protocol_num = protocol.value
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

    return Packet.from_ip(ip_header + tcp_header)


def example_basic_filtering():
    """示例 1: 基本包过滤"""
    print("\n=== 示例 1: 基本包过滤 ===")

    # 创建防火墙配置
    config = FirewallConfig(
        name="BasicFirewall",
        log_dir="",  # 不创建日志目录
        enable_stateful=False,
        enable_ids=False,
    )

    # 创建防火墙
    fw = Firewall(config)

    # 添加规则
    # 允许 HTTP 流量
    fw.add_rule(Rule(
        id="http-allow",
        name="允许 HTTP",
        priority=10,
        action=RuleAction.ACCEPT,
        protocol=Protocol.TCP,
        dst_port="80",
    ))

    # 允许 HTTPS 流量
    fw.add_rule(Rule(
        id="https-allow",
        name="允许 HTTPS",
        priority=11,
        action=RuleAction.ACCEPT,
        protocol=Protocol.TCP,
        dst_port="443",
    ))

    # 阻止 Telnet
    fw.add_rule(Rule(
        id="telnet-block",
        name="阻止 Telnet",
        priority=20,
        action=RuleAction.DROP,
        protocol=Protocol.TCP,
        dst_port="23",
    ))

    # 启动防火墙
    fw.start()

    # 测试数据包
    test_cases = [
        ("HTTP 请求", "192.168.1.1", "10.0.0.1", 12345, 80),
        ("HTTPS 请求", "192.168.1.1", "10.0.0.1", 12346, 443),
        ("Telnet 请求", "192.168.1.1", "10.0.0.1", 12347, 23),
        ("SSH 请求", "192.168.1.1", "10.0.0.1", 12348, 22),
    ]

    for name, src_ip, dst_ip, src_port, dst_port in test_cases:
        packet = create_test_packet(src_ip, dst_ip, src_port, dst_port)
        action = fw.process_packet(packet)
        print(f"{name}: {action.value}")

    # 显示统计信息
    stats = fw.get_statistics()
    print(f"\n统计信息:")
    print(f"  处理数据包: {stats['firewall']['packets_processed']}")
    print(f"  允许通过: {stats['firewall']['packets_accepted']}")
    print(f"  丢弃: {stats['firewall']['packets_dropped']}")

    # 停止防火墙
    fw.stop()


def example_stateful_inspection():
    """示例 2: 状态检测"""
    print("\n=== 示例 2: 状态检测 ===")

    config = FirewallConfig(
        name="StatefulFirewall",
        log_dir="",
        enable_stateful=True,
        enable_ids=False,
    )

    fw = Firewall(config)
    fw.start()

    # 模拟 TCP 三次握手
    print("模拟 TCP 三次握手...")

    # SYN
    syn = create_test_packet("192.168.1.1", "10.0.0.1", 12345, 80,
                            flags=TCPFlag.SYN.value)
    action = fw.process_packet(syn)
    print(f"SYN: {action.value}")

    # SYN-ACK
    syn_ack = create_test_packet("10.0.0.1", "192.168.1.1", 80, 12345,
                                flags=TCPFlag.SYN.value | TCPFlag.ACK.value)
    action = fw.process_packet(syn_ack)
    print(f"SYN-ACK: {action.value}")

    # ACK
    ack = create_test_packet("192.168.1.1", "10.0.0.1", 12345, 80,
                            flags=TCPFlag.ACK.value)
    action = fw.process_packet(ack)
    print(f"ACK: {action.value}")

    # 显示连接信息
    connections = fw.get_connections()
    print(f"\n活动连接数: {len(connections)}")
    if connections:
        conn = connections[0]
        print(f"连接状态: {conn['state']}")
        print(f"TCP 状态: {conn['tcp_state']}")

    fw.stop()


def example_rule_management():
    """示例 3: 规则管理"""
    print("\n=== 示例 3: 规则管理 ===")

    fw = Firewall()

    # 使用规则构建器
    rule = (RuleBuilder("web-allow", "允许 Web 流量")
           .priority(10)
           .action(RuleAction.ACCEPT)
           .protocol(Protocol.TCP)
           .dst_port("80,443")
           .description("允许 HTTP 和 HTTPS 流量")
           .tags("web", "allow")
           .build())

    fw.add_rule(rule)
    print(f"添加规则: {rule.name}")

    # 添加临时规则（1小时后过期）
    temp_rule = (RuleBuilder("temp-allow", "临时允许 SSH")
                .priority(5)
                .action(RuleAction.ACCEPT)
                .protocol(Protocol.TCP)
                .dst_port("22")
                .expires_in(3600)  # 1 小时
                .description("临时允许 SSH 访问")
                .build())

    fw.add_rule(temp_rule)
    print(f"添加临时规则: {temp_rule.name} (过期时间: {temp_rule.expires_at})")

    # 列出所有规则
    print("\n当前规则列表:")
    for rule in fw.get_rules():
        print(f"  - {rule['name']} (优先级: {rule['priority']}, 动作: {rule['action']})")

    # 修改规则优先级
    fw.set_rule_priority("web-allow", 5)
    print(f"\n修改规则优先级: web-allow -> 5")

    # 禁用规则
    fw.disable_rule("temp-allow")
    print(f"禁用规则: temp-allow")

    # 显示规则统计
    stats = fw.rule_set.get_statistics()
    print(f"\n规则统计:")
    print(f"  总规则数: {stats['total_rules']}")
    print(f"  活跃规则: {stats['active_rules']}")
    print(f"  禁用规则: {stats['disabled_rules']}")


def example_ip_filtering():
    """示例 4: IP 过滤"""
    print("\n=== 示例 4: IP 过滤 ===")

    config = FirewallConfig(log_dir="", enable_stateful=False, enable_ids=False)
    fw = Firewall(config)

    # 添加 IP 过滤规则
    # 允许内网流量
    fw.add_rule(Rule(
        id="lan-allow",
        name="允许内网",
        priority=10,
        action=RuleAction.ACCEPT,
        src_ip="192.168.0.0/16",
    ))

    # 阻止特定 IP
    fw.add_rule(Rule(
        id="block-ip",
        name="阻止恶意 IP",
        priority=5,
        action=RuleAction.DROP,
        src_ip="10.0.0.100",
    ))

    # 允许回环
    fw.add_rule(Rule(
        id="loopback",
        name="允许回环",
        priority=1,
        action=RuleAction.ACCEPT,
        src_ip="127.0.0.0/8",
        dst_ip="127.0.0.0/8",
    ))

    fw.start()

    # 测试不同 IP
    test_cases = [
        ("内网 IP", "192.168.1.100", "10.0.0.1"),
        ("恶意 IP", "10.0.0.100", "10.0.0.1"),
        ("外网 IP", "8.8.8.8", "10.0.0.1"),
        ("回环地址", "127.0.0.1", "127.0.0.1"),
    ]

    for name, src_ip, dst_ip in test_cases:
        packet = create_test_packet(src_ip, dst_ip, 12345, 80)
        action = fw.process_packet(packet)
        print(f"{name} ({src_ip}): {action.value}")

    fw.stop()


def example_protocol_filtering():
    """示例 5: 协议过滤"""
    print("\n=== 示例 5: 协议过滤 ===")

    config = FirewallConfig(log_dir="", enable_stateful=False, enable_ids=False)
    fw = Firewall(config)

    # 只允许 TCP
    fw.add_rule(Rule(
        id="tcp-only",
        name="只允许 TCP",
        priority=10,
        action=RuleAction.ACCEPT,
        protocol=Protocol.TCP,
    ))

    # 阻止 UDP
    fw.add_rule(Rule(
        id="block-udp",
        name="阻止 UDP",
        priority=5,
        action=RuleAction.DROP,
        protocol=Protocol.UDP,
    ))

    fw.start()

    # 测试不同协议
    tcp_packet = create_test_packet("192.168.1.1", "10.0.0.1", 12345, 80,
                                   protocol=Protocol.TCP)
    action = fw.process_packet(tcp_packet)
    print(f"TCP 数据包: {action.value}")

    # 注意：UDP 数据包需要不同的构造方式
    # 这里仅演示规则匹配逻辑
    print(f"规则统计: {fw.rule_set.get_statistics()}")

    fw.stop()


def example_logging():
    """示例 6: 日志记录"""
    print("\n=== 示例 6: 日志记录 ===")

    # 创建带日志目录的配置
    config = FirewallConfig(
        name="LoggingFirewall",
        log_dir="logs",
        log_level="debug",
        enable_stateful=False,
        enable_ids=False,
    )

    fw = Firewall(config)

    # 添加规则
    fw.add_rule(Rule(
        id="http-allow",
        name="允许 HTTP",
        priority=10,
        action=RuleAction.ACCEPT,
        protocol=Protocol.TCP,
        dst_port="80",
    ))

    fw.start()

    # 处理一些数据包
    for i in range(5):
        packet = create_test_packet("192.168.1.1", "10.0.0.1", 12345 + i, 80)
        fw.process_packet(packet)

    # 显示日志统计
    log_stats = fw.logger.get_statistics()
    print(f"日志统计:")
    print(f"  总日志数: {log_stats['total_logs']}")
    print(f"  流量日志: {log_stats['traffic_logs']}")
    print(f"  规则日志: {log_stats['rule_logs']}")

    # 获取最近的日志
    recent_logs = fw.get_recent_logs(count=5)
    print(f"\n最近日志:")
    for log in recent_logs:
        print(f"  [{log['level']}] {log['message']}")

    fw.stop()


def main():
    """主函数"""
    print("防火墙示例程序")
    print("=" * 50)

    # 运行示例
    example_basic_filtering()
    example_stateful_inspection()
    example_rule_management()
    example_ip_filtering()
    example_protocol_filtering()
    example_logging()

    print("\n" + "=" * 50)
    print("所有示例运行完成！")


if __name__ == "__main__":
    main()
