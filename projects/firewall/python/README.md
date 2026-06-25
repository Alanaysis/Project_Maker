# 防火墙 - Python 实现

一个完整的网络防火墙系统，使用 Python 实现，支持包过滤、状态检测、规则管理和入侵检测。

## 项目概述

本项目是一个从零实现的网络防火墙系统，使用纯 Python 开发。通过本项目，你将深入理解：

- 网络协议和数据包结构
- 防火墙规则匹配算法
- 状态检测和连接跟踪
- 入侵检测技术

## 核心功能

### 1. 包过滤 (Packet Filtering)
- 基于源/目的 IP 地址过滤
- 基于源/目的端口过滤
- 基于协议类型过滤 (TCP/UDP/ICMP)
- 支持 CIDR 表示法

### 2. 状态检测 (Stateful Inspection)
- TCP 连接状态跟踪 (SYN, SYN-ACK, ESTABLISHED, FIN)
- UDP "连接" 跟踪
- ICMP 请求/响应匹配
- 连接超时管理

### 3. 规则管理 (Rule Management)
- 规则添加、删除、更新
- 规则优先级管理
- 规则启用/禁用
- 临时规则（支持过期时间）

### 4. 日志记录 (Logging)
- 流量日志
- 告警日志
- 规则匹配日志
- 多种输出格式（文本、JSON）

### 5. 入侵检测 (Intrusion Detection)
- 连接频率异常检测
- 端口扫描检测
- SYN Flood 攻击检测
- 实时告警

## 项目结构

```
python/
├── README.md                    # 项目说明
├── requirements.txt             # 依赖列表
├── src/                         # 源代码
│   ├── __init__.py
│   ├── packet.py               # 数据包解析
│   ├── rules.py                # 规则引擎
│   ├── state.py                # 状态检测
│   ├── logger.py               # 日志记录
│   ├── config.py               # 配置管理
│   └── firewall.py             # 防火墙主引擎
├── tests/                       # 测试代码
│   ├── test_packet.py
│   ├── test_rules.py
│   ├── test_state.py
│   └── test_firewall.py
├── examples/                    # 示例程序
│   ├── basic_firewall.py       # 基本防火墙示例
│   ├── rule_management.py      # 规则管理示例
│   └── ids_example.py          # 入侵检测示例
└── configs/                     # 配置文件
    ├── firewall.yaml            # 防火墙配置
    └── rules.json               # 规则配置
```

## 快速开始

### 安装依赖

```bash
cd projects/firewall/python
pip install -r requirements.txt
```

### 运行测试

```bash
cd projects/firewall/python
pytest tests/ -v
```

### 运行示例

```bash
cd projects/firewall/python

# 基本防火墙示例
python examples/basic_firewall.py

# 规则管理示例
python examples/rule_management.py

# 入侵检测示例
python examples/ids_example.py
```

## 使用示例

### 基本使用

```python
from src import Firewall, FirewallConfig, Rule, RuleAction, Protocol

# 创建防火墙
config = FirewallConfig(
    name="MyFirewall",
    log_dir="logs",
    enable_stateful=True,
    enable_ids=True,
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

# 启动防火墙
fw.start()

# 处理数据包
packet = Packet.from_ip(raw_data)
action = fw.process_packet(packet)

# 停止防火墙
fw.stop()
```

### 使用上下文管理器

```python
with Firewall(config) as fw:
    fw.add_rule(...)
    action = fw.process_packet(packet)
```

### 使用规则构建器

```python
from src import RuleBuilder, RuleAction, Protocol

rule = (RuleBuilder("web-allow", "允许 Web 流量")
       .priority(10)
       .action(RuleAction.ACCEPT)
       .protocol(Protocol.TCP)
       .dst_port("80,443")
       .description("允许 HTTP 和 HTTPS 流量")
       .tags("web", "allow")
       .build())

fw.add_rule(rule)
```

## 核心算法

### 规则匹配

规则按优先级排序匹配，找到第一个匹配的规则后立即返回：

```
数据包 → 按优先级遍历规则 → 匹配成功 → 执行动作
                              ↓
                         无匹配 → 执行默认动作
```

### 状态检测

TCP 状态机跟踪：

```
CLOSED → SYN_SENT → ESTABLISHED → FIN_WAIT → TIME_WAIT → CLOSED
```

### 入侵检测

基于阈值的异常检测：

1. 连接频率检测：每分钟连接数超过阈值
2. 端口扫描检测：扫描端口数超过阈值
3. SYN Flood 检测：SYN 包数量超过阈值

## 配置说明

### 防火墙配置 (firewall.yaml)

```yaml
name: PythonFirewall
log_dir: logs
log_level: info
max_connections: 10000
enable_stateful: true
enable_ids: true
default_action: drop

timeouts:
  tcp: 300
  udp: 60
  icmp: 30

ids:
  max_connections_per_minute: 100
  max_ports_per_minute: 20
  syn_flood_threshold: 1000
```

### 规则配置 (rules.json)

```json
{
  "rules": [
    {
      "id": "http-allow",
      "name": "允许 HTTP",
      "priority": 10,
      "action": "accept",
      "protocol": 6,
      "dst_port": "80",
      "description": "允许 HTTP 流量"
    }
  ]
}
```

## 测试覆盖率

运行测试并生成覆盖率报告：

```bash
pytest tests/ -v --cov=src --cov-report=html
```

## 性能考虑

本项目是学习目的的实现，性能不如 C 语言实现。主要性能瓶颈：

1. Python 解释器开销
2. 数据包解析的 Python 实现
3. 规则匹配的线性扫描

生产环境建议使用：
- iptables/nftables（Linux 内核防火墙）
- Suricata/ Snort（专业 IDS/IPS）

## 学习资源

- [Netfilter 官方文档](https://www.netfilter.org/documentation.html)
- [TCP/IP 详解](https://www.pearson.com/en-us/subject-catalog/p/tcp-ip-illustrated-volume-1-the-protocols/P200000003236)
- [Linux 防火墙](https://www.oreilly.com/library/view/linux-firewalls/9781593271411/)

## 许可证

MIT License

## 作者

学习项目 - 用于理解防火墙原理和实现
