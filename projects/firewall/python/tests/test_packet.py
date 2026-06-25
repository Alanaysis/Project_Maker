"""
数据包解析测试
"""

import struct
import socket
import pytest
from src.packet import (
    Packet, PacketInfo, Protocol, TCPFlag, ICMPType,
    EthernetHeader, IPHeader, TCPHeader, UDPHeader, ICMPHeader,
    ip_in_cidr, port_in_range, parse_ip_cidr
)


class TestEthernetHeader:
    """以太网帧头测试"""

    def test_parse_valid(self):
        """测试有效以太网帧头解析"""
        # 构造以太网帧头
        dst_mac = bytes([0x00, 0x11, 0x22, 0x33, 0x44, 0x55])
        src_mac = bytes([0x66, 0x77, 0x88, 0x99, 0xaa, 0xbb])
        ethertype = struct.pack('!H', 0x0800)  # IPv4

        data = dst_mac + src_mac + ethertype
        header = EthernetHeader.parse(data)

        assert header is not None
        assert header.dst_mac == "00:11:22:33:44:55"
        assert header.src_mac == "66:77:88:99:aa:bb"
        assert header.ethertype == 0x0800

    def test_parse_too_short(self):
        """测试过短数据"""
        data = b'\x00' * 13
        header = EthernetHeader.parse(data)
        assert header is None


class TestIPHeader:
    """IP 数据包头测试"""

    def _create_ip_header(self, src_ip: str, dst_ip: str,
                         protocol: Protocol = Protocol.TCP) -> bytes:
        """创建 IP 数据包头"""
        version_ihl = (4 << 4) | 5  # IPv4, 20 bytes header
        tos = 0
        total_length = 40
        identification = 0
        flags_fragment = 0
        ttl = 64
        protocol_num = protocol.value
        checksum = 0
        src = socket.inet_aton(src_ip)
        dst = socket.inet_aton(dst_ip)

        return struct.pack('!BBHHHBBH4s4s',
                          version_ihl, tos, total_length,
                          identification, flags_fragment,
                          ttl, protocol_num, checksum,
                          src, dst)

    def test_parse_valid(self):
        """测试有效 IP 数据包头解析"""
        data = self._create_ip_header("192.168.1.1", "10.0.0.1", Protocol.TCP)
        header = IPHeader.parse(data)

        assert header is not None
        assert header.version == 4
        assert header.header_length == 20
        assert header.src_ip == "192.168.1.1"
        assert header.dst_ip == "10.0.0.1"
        assert header.protocol == Protocol.TCP
        assert header.ttl == 64

    def test_parse_udp(self):
        """测试 UDP 协议解析"""
        data = self._create_ip_header("192.168.1.1", "10.0.0.1", Protocol.UDP)
        header = IPHeader.parse(data)

        assert header is not None
        assert header.protocol == Protocol.UDP

    def test_parse_icmp(self):
        """测试 ICMP 协议解析"""
        data = self._create_ip_header("192.168.1.1", "10.0.0.1", Protocol.ICMP)
        header = IPHeader.parse(data)

        assert header is not None
        assert header.protocol == Protocol.ICMP

    def test_parse_too_short(self):
        """测试过短数据"""
        data = b'\x00' * 19
        header = IPHeader.parse(data)
        assert header is None

    def test_parse_wrong_version(self):
        """测试错误版本号"""
        data = b'\x60' + b'\x00' * 19  # IPv6
        header = IPHeader.parse(data)
        assert header is None


class TestTCPHeader:
    """TCP 数据包头测试"""

    def _create_tcp_header(self, src_port: int, dst_port: int,
                          flags: int = TCPFlag.SYN.value) -> bytes:
        """创建 TCP 数据包头"""
        sequence = 0
        ack_number = 0
        data_offset = (5 << 4)  # 20 bytes header
        window = 65535
        checksum = 0
        urgent_pointer = 0

        return struct.pack('!HHIIBBHHH',
                          src_port, dst_port, sequence, ack_number,
                          data_offset, flags, window, checksum, urgent_pointer)

    def test_parse_syn(self):
        """测试 SYN 包解析"""
        data = self._create_tcp_header(12345, 80, TCPFlag.SYN.value)
        header = TCPHeader.parse(data)

        assert header is not None
        assert header.src_port == 12345
        assert header.dst_port == 80
        assert header.is_syn is True
        assert header.is_ack is False
        assert header.is_fin is False

    def test_parse_syn_ack(self):
        """测试 SYN-ACK 包解析"""
        flags = TCPFlag.SYN.value | TCPFlag.ACK.value
        data = self._create_tcp_header(80, 12345, flags)
        header = TCPHeader.parse(data)

        assert header is not None
        assert header.is_syn is True
        assert header.is_ack is True
        assert header.is_syn_ack is True

    def test_parse_fin(self):
        """测试 FIN 包解析"""
        flags = TCPFlag.FIN.value | TCPFlag.ACK.value
        data = self._create_tcp_header(12345, 80, flags)
        header = TCPHeader.parse(data)

        assert header is not None
        assert header.is_fin is True
        assert header.is_ack is True

    def test_parse_rst(self):
        """测试 RST 包解析"""
        data = self._create_tcp_header(12345, 80, TCPFlag.RST.value)
        header = TCPHeader.parse(data)

        assert header is not None
        assert header.is_rst is True

    def test_flag_list(self):
        """测试标志位列表"""
        flags = TCPFlag.SYN.value | TCPFlag.ACK.value | TCPFlag.PSH.value
        data = self._create_tcp_header(12345, 80, flags)
        header = TCPHeader.parse(data)

        assert header is not None
        flag_list = header.flag_list
        assert TCPFlag.SYN in flag_list
        assert TCPFlag.ACK in flag_list
        assert TCPFlag.PSH in flag_list
        assert TCPFlag.FIN not in flag_list

    def test_parse_too_short(self):
        """测试过短数据"""
        data = b'\x00' * 19
        header = TCPHeader.parse(data)
        assert header is None


class TestUDPHeader:
    """UDP 数据包头测试"""

    def test_parse_valid(self):
        """测试有效 UDP 数据包头解析"""
        src_port = 12345
        dst_port = 53
        length = 8
        checksum = 0

        data = struct.pack('!HHHH', src_port, dst_port, length, checksum)
        header = UDPHeader.parse(data)

        assert header is not None
        assert header.src_port == 12345
        assert header.dst_port == 53
        assert header.length == 8

    def test_parse_too_short(self):
        """测试过短数据"""
        data = b'\x00' * 7
        header = UDPHeader.parse(data)
        assert header is None


class TestICMPHeader:
    """ICMP 数据包头测试"""

    def test_parse_echo_request(self):
        """测试 Echo Request 解析"""
        icmp_type = ICMPType.ECHO_REQUEST.value
        code = 0
        checksum = 0
        identifier = 1234
        sequence = 1

        data = struct.pack('!BBHHH', icmp_type, code, checksum, identifier, sequence)
        header = ICMPHeader.parse(data)

        assert header is not None
        assert header.type == 8
        assert header.code == 0
        assert header.identifier == 1234
        assert header.sequence == 1
        assert header.icmp_type == ICMPType.ECHO_REQUEST

    def test_parse_echo_reply(self):
        """测试 Echo Reply 解析"""
        icmp_type = ICMPType.ECHO_REPLY.value
        code = 0
        checksum = 0
        identifier = 1234
        sequence = 1

        data = struct.pack('!BBHHH', icmp_type, code, checksum, identifier, sequence)
        header = ICMPHeader.parse(data)

        assert header is not None
        assert header.icmp_type == ICMPType.ECHO_REPLY

    def test_parse_too_short(self):
        """测试过短数据"""
        data = b'\x00' * 7
        header = ICMPHeader.parse(data)
        assert header is None


class TestPacket:
    """完整数据包测试"""

    def _create_tcp_packet(self, src_ip: str, dst_ip: str,
                          src_port: int, dst_port: int,
                          flags: int = TCPFlag.SYN.value) -> bytes:
        """创建完整的 TCP 数据包"""
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

    def test_parse_tcp_packet(self):
        """测试 TCP 数据包解析"""
        data = self._create_tcp_packet("192.168.1.1", "10.0.0.1", 12345, 80)
        packet = Packet.from_ip(data)

        assert packet is not None
        assert packet.ip is not None
        assert packet.tcp is not None
        assert packet.ip.src_ip == "192.168.1.1"
        assert packet.ip.dst_ip == "10.0.0.1"
        assert packet.tcp.src_port == 12345
        assert packet.tcp.dst_port == 80

    def test_packet_info(self):
        """测试数据包信息"""
        data = self._create_tcp_packet("192.168.1.1", "10.0.0.1", 12345, 80,
                                       TCPFlag.SYN.value)
        packet = Packet.from_ip(data)
        info = packet.info

        assert info.src_ip == "192.168.1.1"
        assert info.dst_ip == "10.0.0.1"
        assert info.protocol == Protocol.TCP
        assert info.src_port == 12345
        assert info.dst_port == 80
        assert info.is_tcp is True

    def test_packet_str(self):
        """测试数据包字符串表示"""
        data = self._create_tcp_packet("192.168.1.1", "10.0.0.1", 12345, 80)
        packet = Packet.from_ip(data)
        info = packet.info

        str_repr = str(info)
        assert "TCP" in str_repr
        assert "192.168.1.1" in str_repr
        assert "10.0.0.1" in str_repr


class TestIPCIDR:
    """IP CIDR 测试"""

    def test_exact_match(self):
        """测试精确匹配"""
        assert ip_in_cidr("192.168.1.1", "192.168.1.1") is True
        assert ip_in_cidr("192.168.1.1", "192.168.1.2") is False

    def test_cidr_match(self):
        """测试 CIDR 匹配"""
        assert ip_in_cidr("192.168.1.100", "192.168.1.0/24") is True
        assert ip_in_cidr("192.168.2.1", "192.168.1.0/24") is False

    def test_loopback(self):
        """测试回环地址"""
        assert ip_in_cidr("127.0.0.1", "127.0.0.0/8") is True
        assert ip_in_cidr("127.255.255.255", "127.0.0.0/8") is True
        assert ip_in_cidr("128.0.0.1", "127.0.0.0/8") is False

    def test_private_networks(self):
        """测试私有网络"""
        assert ip_in_cidr("10.0.0.1", "10.0.0.0/8") is True
        assert ip_in_cidr("172.16.0.1", "172.16.0.0/12") is True
        assert ip_in_cidr("192.168.1.1", "192.168.0.0/16") is True


class TestPortRange:
    """端口范围测试"""

    def test_exact_port(self):
        """测试精确端口"""
        assert port_in_range(80, "80") is True
        assert port_in_range(81, "80") is False

    def test_port_range(self):
        """测试端口范围"""
        assert port_in_range(80, "80-443") is True
        assert port_in_range(443, "80-443") is True
        assert port_in_range(200, "80-443") is True
        assert port_in_range(79, "80-443") is False
        assert port_in_range(444, "80-443") is False

    def test_port_list(self):
        """测试端口列表"""
        assert port_in_range(80, "80,443,8080") is True
        assert port_in_range(443, "80,443,8080") is True
        assert port_in_range(8080, "80,443,8080") is True
        assert port_in_range(81, "80,443,8080") is False


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
