# embedded-network / 嵌入式网络栈

A learning project implementing a TCP/IP network stack from scratch in C.
从零实现的 TCP/IP 网络栈学习项目。

## Project Description / 项目描述

This project implements a simplified but functional TCP/IP network stack in C,
designed for educational purposes. It covers all major layers of the TCP/IP
model and provides a Socket API for network programming.

本项目使用 C 语言实现了一个简化但功能完整的 TCP/IP 网络栈，旨在教学目的。
它涵盖 TCP/IP 模型的所有主要层次，并提供用于网络编程的 Socket API。

## Learning Objectives / 学习目标

### Understanding TCP/IP Protocol / 理解 TCP/IP 协议
- [x] Ethernet frame format and handling / 以太网帧格式与处理
- [x] ARP protocol (IP to MAC address resolution) / ARP 协议（IP 到 MAC 地址解析）
- [x] IPv4 packet format and checksum / IPv4 数据包格式与校验和
- [x] ICMP protocol (ping implementation) / ICMP 协议（ping 实现）
- [x] UDP datagram format and checksum / UDP 数据报格式与校验和
- [x] TCP segment format and checksum / TCP 段格式与校验和

### Protocol Implementation / 掌握协议实现
- [x] TCP state machine / TCP 状态机
- [x] TCP three-way handshake / TCP 三次握手
- [x] TCP connection termination / TCP 连接终止
- [x] TCP retransmission and timeout / TCP 重传与超时
- [x] Checksum calculation (Internet Checksum) / 校验和计算

### Socket Programming / Socket 编程
- [x] Socket creation and binding / 套接字创建与绑定
- [x] TCP client/server model / TCP 客户端/服务器模型
- [x] UDP client/server model / UDP 客户端/服务器模型
- [x] DHCP client implementation / DHCP 客户端实现

## Architecture / 架构

```
┌─────────────────────────────────────────────────────┐
│                  Application Layer                   │
│              Socket API (套接字 API)                  │
├─────────────────────────────────────────────────────┤
│                  Transport Layer                     │
│         TCP (可靠性传输)    UDP (数据报传输)           │
├─────────────────────────────────────────────────────┤
│                   Internet Layer                     │
│         IPv4 (路由)       ICMP (诊断)      ARP (解析) │
├─────────────────────────────────────────────────────┤
│                   Link Layer                         │
│              Ethernet Frame (以太网帧)                 │
└─────────────────────────────────────────────────────┘

Data Flow / 数据流:
  数据封装 → 协议处理 → 网络传输 → 数据接收
  Encapsulation → Protocol Processing → Transmission → Reception
```

## Source Files / 源文件

| File | Description / 描述 |
|------|-------------------|
| `include/embedded_net.h` | Core header with protocol definitions / 包含协议定义的核心头文件 |
| `src/embedded_net.c` | Network stack init, checksum, utilities / 网络栈初始化、校验和、工具函数 |
| `src/arp.c` | ARP protocol implementation / ARP 协议实现 |
| `src/ipv4.c` | IPv4 packet handling / IPv4 数据包处理 |
| `src/icmp.c` | ICMP (ping) implementation / ICMP (ping) 实现 |
| `src/udp.c` | UDP datagram handling / UDP 数据报处理 |
| `src/tcp.c` | TCP connection management / TCP 连接管理 |
| `src/socket_api.c` | Socket API (bind, connect, send, recv) / 套接字 API |
| `src/dhcp.c` | DHCP client implementation / DHCP 客户端实现 |

## Examples / 示例

| Example | Description / 描述 |
|---------|-------------------|
| `examples/ping_demo.c` | ICMP ping demonstration / ICMP ping 演示 |
| `examples/tcp_client_server_demo.c` | TCP client/server demo / TCP 客户端/服务器演示 |
| `examples/udp_demo.c` | UDP datagram demo / UDP 数据报演示 |
| `examples/socket_programming_demo.c` | Socket API demo / 套接字 API 演示 |

## Building / 构建

```bash
# Build all targets / 构建所有目标
make

# Build specific example / 构建特定示例
make ping_demo
make tcp_demo
make udp_demo
make socket_demo

# Build tests / 构建测试
make test

# Run all tests / 运行所有测试
make run-tests

# Clean / 清理
make clean
```

## Running Examples / 运行示例

```bash
# Ping/ICMP demo / ping/ICMP 演示
./build/ping_demo

# TCP client/server demo / TCP 客户端/服务器演示
./build/tcp_demo

# UDP demo / UDP 演示
./build/udp_demo

# Socket programming demo / 套接字编程演示
./build/socket_demo

# Run unit tests / 运行单元测试
./build/test_checksum
./build/test_ip_utils
./build/test_tcp_state_machine
```

## TCP/IP Protocol Reference / TCP/IP 协议参考

### Layer 1: Link Layer (链路层)
- **Ethernet**: Frame format, MAC addresses, broadcast
- **ARP**: Address resolution (IP → MAC)

### Layer 2: Internet Layer (网络层)
- **IPv4**: Packet format, fragmentation, TTL, checksum
- **ICMP**: Echo request/reply (ping), error messages
- **ARP**: Maps IP to MAC on local network

### Layer 3: Transport Layer (传输层)
- **TCP**: Reliable delivery, state machine, flow control
  - Three-way handshake: SYN → SYN-ACK → ACK
  - Connection termination: FIN → ACK → FIN → ACK
  - Retransmission: SRTT, RTTVAR, RTO calculation
- **UDP**: Connectionless datagrams, minimal overhead

### Layer 4: Application Layer (应用层)
- **Socket API**: Standard network programming interface
- **DHCP**: Dynamic IP address assignment

## Key Concepts / 核心概念

### Internet Checksum (互联网校验和)
```
1. Set checksum field to 0
2. Sum all 16-bit words using ones' complement addition
3. Fold carry bits back into the sum
4. Take ones' complement of the result
```

### TCP State Machine (TCP 状态机)
```
CLOSED → LISTEN → SYN_RECEIVED → ESTABLISHED
                                  → FIN_WAIT → TIME_WAIT → CLOSED
```

### TCP Three-Way Handshake (TCP 三次握手)
```
Client                    Server
------                    ------
[SYN, seq=I]    ------>
                    <---- [SYN-ACK, seq=J, ack=I+1]
[ACK, ack=J+1]  ------>
```

## Priority / 优先级
P1

## Estimated Time / 预计时间
10 hours

## Status / 状态
✅ Completed / 已完成

## License / 许可证
MIT License
