"""
数据包解析模块

实现网络数据包的解析，支持以太网、IP、TCP、UDP、ICMP 协议。
"""

import struct
import socket
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Optional, Tuple


class Protocol(Enum):
    """网络协议类型"""
    TCP = 6
    UDP = 17
    ICMP = 1
    IGMP = 2
    GRE = 47
    ESP = 50
    AH = 51
    UNKNOWN = 0


class TCPFlag(Enum):
    """TCP 标志位"""
    FIN = 0x01
    SYN = 0x02
    RST = 0x04
    PSH = 0x08
    ACK = 0x10
    URG = 0x20
    ECE = 0x40
    CWR = 0x80


class ICMPType(Enum):
    """ICMP 类型"""
    ECHO_REPLY = 0
    DEST_UNREACHABLE = 3
    SOURCE_QUENCH = 4
    REDIRECT = 5
    ECHO_REQUEST = 8
    TIME_EXCEEDED = 11


@dataclass
class EthernetHeader:
    """以太网帧头"""
    dst_mac: str
    src_mac: str
    ethertype: int

    @staticmethod
    def parse(data: bytes) -> Optional['EthernetHeader']:
        """解析以太网帧头"""
        if len(data) < 14:
            return None
        dst_mac = ':'.join(f'{b:02x}' for b in data[0:6])
        src_mac = ':'.join(f'{b:02x}' for b in data[6:12])
        ethertype = struct.unpack('!H', data[12:14])[0]
        return EthernetHeader(dst_mac=dst_mac, src_mac=src_mac, ethertype=ethertype)


@dataclass
class IPHeader:
    """IP 数据包头"""
    version: int
    header_length: int
    tos: int
    total_length: int
    identification: int
    flags: int
    fragment_offset: int
    ttl: int
    protocol: Protocol
    checksum: int
    src_ip: str
    dst_ip: str
    options: bytes = b''

    @staticmethod
    def parse(data: bytes) -> Optional['IPHeader']:
        """解析 IP 数据包头"""
        if len(data) < 20:
            return None

        version_ihl = data[0]
        version = (version_ihl >> 4) & 0xF
        ihl = (version_ihl & 0xF) * 4

        if version != 4 or len(data) < ihl:
            return None

        tos = data[1]
        total_length = struct.unpack('!H', data[2:4])[0]
        identification = struct.unpack('!H', data[4:6])[0]
        flags_fragment = struct.unpack('!H', data[6:8])[0]
        flags = (flags_fragment >> 13) & 0x7
        fragment_offset = flags_fragment & 0x1FFF
        ttl = data[8]
        protocol_num = data[9]
        checksum = struct.unpack('!H', data[10:12])[0]
        src_ip = socket.inet_ntoa(data[12:16])
        dst_ip = socket.inet_ntoa(data[16:20])

        try:
            protocol = Protocol(protocol_num)
        except ValueError:
            protocol = Protocol.UNKNOWN

        options = data[20:ihl] if ihl > 20 else b''

        return IPHeader(
            version=version,
            header_length=ihl,
            tos=tos,
            total_length=total_length,
            identification=identification,
            flags=flags,
            fragment_offset=fragment_offset,
            ttl=ttl,
            protocol=protocol,
            checksum=checksum,
            src_ip=src_ip,
            dst_ip=dst_ip,
            options=options,
        )


@dataclass
class TCPHeader:
    """TCP 数据包头"""
    src_port: int
    dst_port: int
    sequence: int
    ack_number: int
    data_offset: int
    flags: int
    window: int
    checksum: int
    urgent_pointer: int

    @property
    def flag_list(self) -> list:
        """获取标志位列表"""
        result = []
        for flag in TCPFlag:
            if self.flags & flag.value:
                result.append(flag)
        return result

    @property
    def is_syn(self) -> bool:
        return bool(self.flags & TCPFlag.SYN.value)

    @property
    def is_ack(self) -> bool:
        return bool(self.flags & TCPFlag.ACK.value)

    @property
    def is_fin(self) -> bool:
        return bool(self.flags & TCPFlag.FIN.value)

    @property
    def is_rst(self) -> bool:
        return bool(self.flags & TCPFlag.RST.value)

    @property
    def is_syn_ack(self) -> bool:
        return self.is_syn and self.is_ack

    @staticmethod
    def parse(data: bytes) -> Optional['TCPHeader']:
        """解析 TCP 数据包头"""
        if len(data) < 20:
            return None

        src_port = struct.unpack('!H', data[0:2])[0]
        dst_port = struct.unpack('!H', data[2:4])[0]
        sequence = struct.unpack('!I', data[4:8])[0]
        ack_number = struct.unpack('!I', data[8:12])[0]
        data_offset = ((data[12] >> 4) & 0xF) * 4
        flags = data[13]
        window = struct.unpack('!H', data[14:16])[0]
        checksum = struct.unpack('!H', data[16:18])[0]
        urgent_pointer = struct.unpack('!H', data[18:20])[0]

        return TCPHeader(
            src_port=src_port,
            dst_port=dst_port,
            sequence=sequence,
            ack_number=ack_number,
            data_offset=data_offset,
            flags=flags,
            window=window,
            checksum=checksum,
            urgent_pointer=urgent_pointer,
        )


@dataclass
class UDPHeader:
    """UDP 数据包头"""
    src_port: int
    dst_port: int
    length: int
    checksum: int

    @staticmethod
    def parse(data: bytes) -> Optional['UDPHeader']:
        """解析 UDP 数据包头"""
        if len(data) < 8:
            return None

        src_port = struct.unpack('!H', data[0:2])[0]
        dst_port = struct.unpack('!H', data[2:4])[0]
        length = struct.unpack('!H', data[4:6])[0]
        checksum = struct.unpack('!H', data[6:8])[0]

        return UDPHeader(
            src_port=src_port,
            dst_port=dst_port,
            length=length,
            checksum=checksum,
        )


@dataclass
class ICMPHeader:
    """ICMP 数据包头"""
    type: int
    code: int
    checksum: int
    identifier: int = 0
    sequence: int = 0

    @property
    def icmp_type(self) -> Optional[ICMPType]:
        """获取 ICMP 类型枚举"""
        try:
            return ICMPType(self.type)
        except ValueError:
            return None

    @staticmethod
    def parse(data: bytes) -> Optional['ICMPHeader']:
        """解析 ICMP 数据包头"""
        if len(data) < 8:
            return None

        icmp_type = data[0]
        code = data[1]
        checksum = struct.unpack('!H', data[2:4])[0]
        identifier = struct.unpack('!H', data[4:6])[0]
        sequence = struct.unpack('!H', data[6:8])[0]

        return ICMPHeader(
            type=icmp_type,
            code=code,
            checksum=checksum,
            identifier=identifier,
            sequence=sequence,
        )


@dataclass
class PacketInfo:
    """数据包信息摘要"""
    timestamp: float
    src_ip: str
    dst_ip: str
    protocol: Protocol
    src_port: Optional[int] = None
    dst_port: Optional[int] = None
    length: int = 0
    tcp_flags: Optional[int] = None
    icmp_type: Optional[int] = None
    icmp_code: Optional[int] = None

    @property
    def is_tcp(self) -> bool:
        return self.protocol == Protocol.TCP

    @property
    def is_udp(self) -> bool:
        return self.protocol == Protocol.UDP

    @property
    def is_icmp(self) -> bool:
        return self.protocol == Protocol.ICMP

    def __str__(self) -> str:
        parts = [
            f"[{self.protocol.name}]",
            f"{self.src_ip}:{self.src_port or '*'}",
            "->",
            f"{self.dst_ip}:{self.dst_port or '*'}",
        ]
        if self.tcp_flags is not None:
            flags = []
            for flag in TCPFlag:
                if self.tcp_flags & flag.value:
                    flags.append(flag.name)
            if flags:
                parts.append(f"[{','.join(flags)}]")
        return " ".join(parts)


@dataclass
class Packet:
    """完整的网络数据包"""
    raw_data: bytes
    ethernet: Optional[EthernetHeader] = None
    ip: Optional[IPHeader] = None
    tcp: Optional[TCPHeader] = None
    udp: Optional[UDPHeader] = None
    icmp: Optional[ICMPHeader] = None

    @property
    def info(self) -> PacketInfo:
        """获取数据包信息摘要"""
        import time

        info = PacketInfo(
            timestamp=time.time(),
            src_ip=self.ip.src_ip if self.ip else "0.0.0.0",
            dst_ip=self.ip.dst_ip if self.ip else "0.0.0.0",
            protocol=self.ip.protocol if self.ip else Protocol.UNKNOWN,
            length=len(self.raw_data),
        )

        if self.tcp:
            info.src_port = self.tcp.src_port
            info.dst_port = self.tcp.dst_port
            info.tcp_flags = self.tcp.flags
        elif self.udp:
            info.src_port = self.udp.src_port
            info.dst_port = self.udp.dst_port
        elif self.icmp:
            info.icmp_type = self.icmp.type
            info.icmp_code = self.icmp.code

        return info

    @staticmethod
    def parse(data: bytes, include_ethernet: bool = True) -> Optional['Packet']:
        """解析网络数据包

        Args:
            data: 原始数据包数据
            include_ethernet: 是否包含以太网帧头（pcap 捕获时为 True）

        Returns:
            解析后的 Packet 对象，解析失败返回 None
        """
        packet = Packet(raw_data=data)
        offset = 0

        # 解析以太网帧头
        if include_ethernet:
            packet.ethernet = EthernetHeader.parse(data)
            if packet.ethernet is None:
                return None
            offset = 14

            # 处理 VLAN 标签
            if packet.ethernet.ethertype == 0x8100:
                offset += 4
                if len(data) < offset + 20:
                    return None

        # 解析 IP 数据包
        ip_data = data[offset:]
        packet.ip = IPHeader.parse(ip_data)
        if packet.ip is None:
            return None

        # 解析传输层协议
        transport_offset = packet.ip.header_length
        transport_data = ip_data[transport_offset:]

        if packet.ip.protocol == Protocol.TCP:
            packet.tcp = TCPHeader.parse(transport_data)
        elif packet.ip.protocol == Protocol.UDP:
            packet.udp = UDPHeader.parse(transport_data)
        elif packet.ip.protocol == Protocol.ICMP:
            packet.icmp = ICMPHeader.parse(transport_data)

        return packet

    @staticmethod
    def from_ip(data: bytes) -> Optional['Packet']:
        """从 IP 层开始解析（用于 raw socket）

        Args:
            data: 从 IP 层开始的数据

        Returns:
            解析后的 Packet 对象
        """
        return Packet.parse(data, include_ethernet=False)


def parse_ip_cidr(cidr: str) -> Tuple[str, int]:
    """解析 CIDR 表示法

    Args:
        cidr: CIDR 表示法，如 "192.168.1.0/24"

    Returns:
        (ip_address, prefix_length) 元组
    """
    if '/' in cidr:
        ip, prefix = cidr.split('/')
        return ip, int(prefix)
    return cidr, 32


def ip_in_cidr(ip: str, cidr: str) -> bool:
    """检查 IP 地址是否在 CIDR 范围内

    Args:
        ip: IP 地址
        cidr: CIDR 表示法

    Returns:
        是否在范围内
    """
    network, prefix = parse_ip_cidr(cidr)

    ip_int = struct.unpack('!I', socket.inet_aton(ip))[0]
    network_int = struct.unpack('!I', socket.inet_aton(network))[0]

    mask = (0xFFFFFFFF << (32 - prefix)) & 0xFFFFFFFF
    return (ip_int & mask) == (network_int & mask)


def port_in_range(port: int, port_range: str) -> bool:
    """检查端口是否在端口范围内

    Args:
        port: 端口号
        port_range: 端口范围，如 "80", "80-443", "80,443,8080"

    Returns:
        是否在范围内
    """
    if '-' in port_range:
        start, end = port_range.split('-')
        return int(start) <= port <= int(end)
    elif ',' in port_range:
        ports = [int(p.strip()) for p in port_range.split(',')]
        return port in ports
    else:
        return port == int(port_range)
