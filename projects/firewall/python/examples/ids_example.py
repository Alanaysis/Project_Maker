#!/usr/bin/env python3
"""
入侵检测示例

演示防火墙的入侵检测功能。
"""

import sys
import os
import time
import random

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src import (
    Firewall, FirewallConfig,
    Rule, RuleAction, Protocol, TCPFlag,
    PacketInfo,
)


def create_syn_packet(src_ip: str, dst_ip: str, src_port: int, dst_port: int):
    """创建 SYN 数据包信息"""
    return PacketInfo(
        timestamp=time.time(),
        src_ip=src_ip,
        dst_ip=dst_ip,
        protocol=Protocol.TCP,
        src_port=src_port,
        dst_port=dst_port,
        tcp_flags=TCPFlag.SYN.value,
        length=60,
    )


def demo_connection_rate_detection():
    """演示连接频率检测"""
    print("\n=== 连接频率检测 ===")

    config = FirewallConfig(
        log_dir="",
        enable_stateful=True,
        enable_ids=True,
        max_connections_per_minute=10,  # 低阈值用于演示
    )

    fw = Firewall(config)
    fw.start()

    # 模拟高频连接
    src_ip = "192.168.1.100"
    print(f"模拟来自 {src_ip} 的高频连接...")

    for i in range(15):
        info = create_syn_packet(src_ip, "10.0.0.1", 10000 + i, 80)
        packet = PacketInfo(
            timestamp=time.time(),
            src_ip=info.src_ip,
            dst_ip=info.dst_ip,
            protocol=info.protocol,
            src_port=info.src_port,
            dst_port=info.dst_port,
            tcp_flags=info.tcp_flags,
            length=info.length,
        )
        # 直接使用 IDS 分析
        fw._ids.analyze_packet(packet, RuleAction.DROP)

    # 显示 IDS 统计
    ids_stats = fw._ids.get_statistics()
    print(f"\nIDS 统计:")
    print(f"  跟踪 IP 数: {ids_stats['tracked_ips']}")

    # 显示告警
    alerts = fw.get_alerts()
    if alerts:
        print(f"\n生成的告警:")
        for alert in alerts[:3]:  # 只显示前 3 条
            print(f"  [{alert['level']}] {alert['message']}")
    else:
        print(f"\n未生成告警（需要更多连接触发阈值）")

    fw.stop()


def demo_port_scan_detection():
    """演示端口扫描检测"""
    print("\n=== 端口扫描检测 ===")

    config = FirewallConfig(
        log_dir="",
        enable_stateful=True,
        enable_ids=True,
        max_ports_per_minute=5,  # 低阈值用于演示
    )

    fw = Firewall(config)
    fw.start()

    # 模拟端口扫描
    src_ip = "10.0.0.50"
    print(f"模拟来自 {src_ip} 的端口扫描...")

    # 扫描多个端口
    ports = [21, 22, 23, 25, 80, 443, 3306, 5432, 8080, 8443]
    for port in ports:
        info = create_syn_packet(src_ip, "192.168.1.1", 12345, port)
        fw._ids.analyze_packet(info, RuleAction.DROP)
        print(f"  扫描端口: {port}")

    # 显示 IDS 统计
    ids_stats = fw._ids.get_statistics()
    print(f"\nIDS 统计:")
    print(f"  端口扫描 IP 数: {ids_stats['port_scan_ips']}")

    # 显示告警
    alerts = fw.get_alerts()
    if alerts:
        print(f"\n生成的告警:")
        for alert in alerts[:3]:
            print(f"  [{alert['level']}] {alert['message']}")
    else:
        print(f"\n未生成告警")

    fw.stop()


def demo_syn_flood_detection():
    """演示 SYN Flood 检测"""
    print("\n=== SYN Flood 检测 ===")

    config = FirewallConfig(
        log_dir="",
        enable_stateful=True,
        enable_ids=True,
        syn_flood_threshold=20,  # 低阈值用于演示
    )

    fw = Firewall(config)
    fw.start()

    # 模拟 SYN Flood
    src_ip = "10.0.0.100"
    print(f"模拟来自 {src_ip} 的 SYN Flood 攻击...")

    for i in range(25):
        info = create_syn_packet(src_ip, "192.168.1.1", 12345, 80)
        fw._ids.analyze_packet(info, RuleAction.DROP)

    # 显示 IDS 统计
    ids_stats = fw._ids.get_statistics()
    print(f"\nIDS 统计:")
    print(f"  SYN Flood IP 数: {ids_stats['syn_flood_ips']}")

    # 显示告警
    alerts = fw.get_alerts()
    if alerts:
        print(f"\n生成的告警:")
        for alert in alerts[:3]:
            print(f"  [{alert['level']}] {alert['message']}")
    else:
        print(f"\n未生成告警")

    fw.stop()


def demo_stateful_tracking():
    """演示状态跟踪"""
    print("\n=== 状态跟踪演示 ===")

    config = FirewallConfig(
        log_dir="",
        enable_stateful=True,
        enable_ids=False,
    )

    fw = Firewall(config)
    fw.start()

    # 模拟完整的 TCP 连接
    print("模拟 TCP 三次握手...")

    # SYN
    syn = create_syn_packet("192.168.1.1", "10.0.0.1", 12345, 80)
    syn.flags = TCPFlag.SYN.value
    state, entry = fw.connection_tracker.process_packet(syn, is_outgoing=True)
    print(f"SYN: 状态 = {state.value}")

    # SYN-ACK
    syn_ack = create_syn_packet("10.0.0.1", "192.168.1.1", 80, 12345)
    syn_ack.flags = TCPFlag.SYN.value | TCPFlag.ACK.value
    syn_ack.src_ip = "10.0.0.1"
    syn_ack.dst_ip = "192.168.1.1"
    syn_ack.src_port = 80
    syn_ack.dst_port = 12345
    state, entry = fw.connection_tracker.process_packet(syn_ack, is_outgoing=False)
    print(f"SYN-ACK: 状态 = {state.value}")

    # ACK
    ack = create_syn_packet("192.168.1.1", "10.0.0.1", 12345, 80)
    ack.flags = TCPFlag.ACK.value
    state, entry = fw.connection_tracker.process_packet(ack, is_outgoing=True)
    print(f"ACK: 状态 = {state.value}")

    # 显示连接信息
    connections = fw.get_connections()
    print(f"\n活动连接数: {len(connections)}")
    if connections:
        conn = connections[0]
        print(f"连接详情:")
        print(f"  源 IP: {conn['src_ip']}:{conn['src_port']}")
        print(f"  目的 IP: {conn['dst_ip']}:{conn['dst_port']}")
        print(f"  协议: {conn['protocol']}")
        print(f"  状态: {conn['state']}")
        print(f"  TCP 状态: {conn['tcp_state']}")

    fw.stop()


def demo_alert_callbacks():
    """演示告警回调"""
    print("\n=== 告警回调演示 ===")

    config = FirewallConfig(
        log_dir="",
        enable_stateful=True,
        enable_ids=True,
        max_connections_per_minute=5,
    )

    fw = Firewall(config)

    # 添加告警回调
    alerts_received = []

    def on_alert(message, packet_info):
        alerts_received.append({
            "message": message,
            "src_ip": packet_info.src_ip if packet_info else None,
        })
        print(f"  [回调] 收到告警: {message}")

    fw.add_alert_callback(on_alert)

    fw.start()

    # 触发告警
    src_ip = "192.168.1.200"
    print(f"模拟来自 {src_ip} 的异常流量...")

    for i in range(10):
        info = create_syn_packet(src_ip, "10.0.0.1", 10000 + i, 80)
        fw._ids.analyze_packet(info, RuleAction.DROP)

    print(f"\n收到的告警数: {len(alerts_received)}")

    fw.stop()


def demo_comprehensive_ids():
    """演示综合入侵检测"""
    print("\n=== 综合入侵检测演示 ===")

    config = FirewallConfig(
        log_dir="",
        enable_stateful=True,
        enable_ids=True,
        max_connections_per_minute=50,
        max_ports_per_minute=10,
        syn_flood_threshold=100,
    )

    fw = Firewall(config)
    fw.start()

    # 添加规则
    fw.add_rule(Rule(
        id="http-allow",
        name="允许 HTTP",
        priority=10,
        action=RuleAction.ACCEPT,
        protocol=Protocol.TCP,
        dst_port="80",
    ))

    fw.add_rule(Rule(
        id="default-drop",
        name="默认丢弃",
        priority=1000,
        action=RuleAction.DROP,
    ))

    # 模拟正常流量
    print("模拟正常 HTTP 流量...")
    for i in range(5):
        info = PacketInfo(
            timestamp=time.time(),
            src_ip="192.168.1.1",
            dst_ip="10.0.0.1",
            protocol=Protocol.TCP,
            src_port=12345 + i,
            dst_port=80,
            tcp_flags=TCPFlag.SYN.value,
            length=60,
        )
        # 这里需要完整的 Packet 对象，简化处理
        fw._ids.analyze_packet(info, RuleAction.ACCEPT)

    # 模拟可疑流量
    print("\n模拟可疑流量...")
    suspicious_ip = "10.0.0.50"

    # 多端口扫描
    for port in [21, 22, 23, 25, 80, 443, 3306]:
        info = create_syn_packet(suspicious_ip, "192.168.1.1", 12345, port)
        fw._ids.analyze_packet(info, RuleAction.DROP)

    # 显示统计
    ids_stats = fw._ids.get_statistics()
    print(f"\nIDS 统计:")
    print(f"  跟踪 IP 数: {ids_stats['tracked_ips']}")
    print(f"  端口扫描 IP 数: {ids_stats['port_scan_ips']}")
    print(f"  SYN Flood IP 数: {ids_stats['syn_flood_ips']}")

    # 显示告警
    alerts = fw.get_alerts()
    if alerts:
        print(f"\n告警列表:")
        for alert in alerts:
            print(f"  [{alert['level']}] {alert['message']}")

    fw.stop()


def main():
    """主函数"""
    print("防火墙入侵检测示例")
    print("=" * 50)

    demo_connection_rate_detection()
    demo_port_scan_detection()
    demo_syn_flood_detection()
    demo_stateful_tracking()
    demo_alert_callbacks()
    demo_comprehensive_ids()

    print("\n" + "=" * 50)
    print("入侵检测示例完成！")


if __name__ == "__main__":
    main()
