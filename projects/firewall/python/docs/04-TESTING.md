# 防火墙测试文档

## 1. 测试策略

### 1.1 测试层次

```
┌─────────────────────────────────────┐
│          系统测试                    │
│    (防火墙引擎集成测试)              │
├─────────────────────────────────────┤
│          集成测试                    │
│    (模块间交互测试)                  │
├─────────────────────────────────────┤
│          单元测试                    │
│    (单个模块/函数测试)               │
└─────────────────────────────────────┘
```

### 1.2 测试覆盖率目标

| 模块 | 目标覆盖率 |
|------|-----------|
| packet.py | 90% |
| rules.py | 90% |
| state.py | 85% |
| logger.py | 80% |
| firewall.py | 85% |
| config.py | 80% |
| **总体** | **85%** |

### 1.3 测试工具

- **pytest**：测试框架
- **pytest-cov**：覆盖率报告
- **pytest-html**：HTML 测试报告

## 2. 单元测试

### 2.1 数据包解析测试 (test_packet.py)

#### 2.1.1 以太网帧头测试

```python
class TestEthernetHeader:
    def test_parse_valid(self):
        """测试有效以太网帧头解析"""
        # 构造以太网帧头
        dst_mac = bytes([0x00, 0x11, 0x22, 0x33, 0x44, 0x55])
        src_mac = bytes([0x66, 0x77, 0x88, 0x99, 0xaa, 0xbb])
        ethertype = struct.pack('!H', 0x0800)

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
```

#### 2.1.2 IP 数据包头测试

```python
class TestIPHeader:
    def test_parse_valid(self):
        """测试有效 IP 数据包头解析"""
        data = self._create_ip_header("192.168.1.1", "10.0.0.1", Protocol.TCP)
        header = IPHeader.parse(data)

        assert header is not None
        assert header.version == 4
        assert header.src_ip == "192.168.1.1"
        assert header.dst_ip == "10.0.0.1"
        assert header.protocol == Protocol.TCP

    def test_parse_wrong_version(self):
        """测试错误版本号"""
        data = b'\x60' + b'\x00' * 19  # IPv6
        header = IPHeader.parse(data)
        assert header is None
```

#### 2.1.3 TCP 数据包头测试

```python
class TestTCPHeader:
    def test_parse_syn(self):
        """测试 SYN 包解析"""
        data = self._create_tcp_header(12345, 80, TCPFlag.SYN.value)
        header = TCPHeader.parse(data)

        assert header is not None
        assert header.src_port == 12345
        assert header.dst_port == 80
        assert header.is_syn is True
        assert header.is_ack is False

    def test_parse_syn_ack(self):
        """测试 SYN-ACK 包解析"""
        flags = TCPFlag.SYN.value | TCPFlag.ACK.value
        data = self._create_tcp_header(80, 12345, flags)
        header = TCPHeader.parse(data)

        assert header is not None
        assert header.is_syn is True
        assert header.is_ack is True
        assert header.is_syn_ack is True
```

#### 2.1.4 CIDR 匹配测试

```python
class TestIPCIDR:
    def test_cidr_match(self):
        """测试 CIDR 匹配"""
        assert ip_in_cidr("192.168.1.100", "192.168.1.0/24") is True
        assert ip_in_cidr("192.168.2.1", "192.168.1.0/24") is False

    def test_loopback(self):
        """测试回环地址"""
        assert ip_in_cidr("127.0.0.1", "127.0.0.0/8") is True
        assert ip_in_cidr("128.0.0.1", "127.0.0.0/8") is False
```

### 2.2 规则引擎测试 (test_rules.py)

#### 2.2.1 规则匹配测试

```python
class TestRule:
    def test_rule_matches_protocol(self):
        """测试协议匹配"""
        rule = Rule(
            id="tcp-rule",
            name="TCP Rule",
            action=RuleAction.ACCEPT,
            protocol=Protocol.TCP,
        )

        # 匹配 TCP
        info = PacketInfo(
            timestamp=time.time(),
            src_ip="192.168.1.1",
            dst_ip="10.0.0.1",
            protocol=Protocol.TCP,
        )
        assert rule.matches(info) is True

        # 不匹配 UDP
        info.protocol = Protocol.UDP
        assert rule.matches(info) is False

    def test_rule_matches_ip(self):
        """测试 IP 匹配"""
        rule = Rule(
            id="ip-rule",
            name="IP Rule",
            action=RuleAction.DROP,
            src_ip="192.168.1.0/24",
        )

        # 匹配
        info = PacketInfo(
            timestamp=time.time(),
            src_ip="192.168.1.100",
            dst_ip="10.0.0.1",
            protocol=Protocol.TCP,
        )
        assert rule.matches(info) is True

        # 不匹配
        info.src_ip = "10.0.0.1"
        assert rule.matches(info) is False
```

#### 2.2.2 规则集测试

```python
class TestRuleSet:
    def test_priority_ordering(self):
        """测试优先级排序"""
        ruleset = RuleSet()

        ruleset.add_rule(Rule(id="low", name="Low", priority=100, action=RuleAction.DROP))
        ruleset.add_rule(Rule(id="high", name="High", priority=10, action=RuleAction.ACCEPT))
        ruleset.add_rule(Rule(id="mid", name="Mid", priority=50, action=RuleAction.LOG))

        rules = ruleset.rules
        assert rules[0].id == "high"
        assert rules[1].id == "mid"
        assert rules[2].id == "low"

    def test_match_first_rule(self):
        """测试匹配第一个规则"""
        ruleset = RuleSet()

        ruleset.add_rule(Rule(id="first", name="First", priority=10, action=RuleAction.ACCEPT))
        ruleset.add_rule(Rule(id="second", name="Second", priority=20, action=RuleAction.DROP))

        info = PacketInfo(
            timestamp=time.time(),
            src_ip="192.168.1.1",
            dst_ip="10.0.0.1",
            protocol=Protocol.TCP,
        )

        matched = ruleset.match(info)
        assert matched is not None
        assert matched.id == "first"
```

### 2.3 状态检测测试 (test_state.py)

#### 2.3.1 连接创建测试

```python
class TestStateTable:
    def test_create_connection(self):
        """测试创建连接"""
        table = StateTable()
        info = self._create_packet_info()

        entry = table.create_connection(info)
        assert entry is not None
        assert entry.state == ConnectionState.NEW
        assert entry.protocol == Protocol.TCP

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
```

#### 2.3.2 TCP 状态机测试

```python
class TestConnectionTracker:
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
```

### 2.4 防火墙引擎测试 (test_firewall.py)

#### 2.4.1 基本功能测试

```python
class TestFirewall:
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
```

#### 2.4.2 规则优先级测试

```python
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
```

## 3. 集成测试

### 3.1 配置加载测试

```python
class TestConfigIntegration:
    def test_load_yaml_config(self):
        """测试加载 YAML 配置"""
        config_content = """
        name: TestFirewall
        log_dir: logs
        enable_stateful: true
        """

        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(config_content)
            filepath = f.name

        try:
            manager = ConfigManager()
            config = manager.load_config(filepath)

            assert config.name == "TestFirewall"
            assert config.enable_stateful is True
        finally:
            os.unlink(filepath)

    def test_load_rules_json(self):
        """测试加载 JSON 规则"""
        rules_content = {
            "rules": [
                {
                    "id": "test",
                    "name": "Test Rule",
                    "priority": 10,
                    "action": "accept"
                }
            ]
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(rules_content, f)
            filepath = f.name

        try:
            manager = ConfigManager()
            ruleset = manager.load_rules(filepath)

            assert len(ruleset.rules) == 1
            assert ruleset.get_rule("test") is not None
        finally:
            os.unlink(filepath)
```

### 3.2 规则持久化测试

```python
class TestRulePersistence:
    def test_save_and_load_rules(self):
        """测试保存和加载规则"""
        # 创建规则集
        ruleset = RuleSet()
        ruleset.add_rule(Rule(
            id="test",
            name="Test Rule",
            priority=10,
            action=RuleAction.ACCEPT,
            protocol=Protocol.TCP,
            dst_port="80",
        ))

        # 保存到文件
        filepath = tempfile.mktemp(suffix='.json')
        try:
            ruleset.save_to_file(filepath)

            # 从文件加载
            new_ruleset = RuleSet()
            new_ruleset.load_from_file(filepath)

            assert len(new_ruleset.rules) == 1
            assert new_ruleset.get_rule("test") is not None
            assert new_ruleset.get_rule("test").dst_port == "80"
        finally:
            os.unlink(filepath)
```

## 4. 测试运行

### 4.1 运行所有测试

```bash
cd projects/firewall/python
pytest tests/ -v
```

### 4.2 运行特定测试

```bash
# 运行数据包测试
pytest tests/test_packet.py -v

# 运行规则测试
pytest tests/test_rules.py -v

# 运行状态测试
pytest tests/test_state.py -v

# 运行防火墙测试
pytest tests/test_firewall.py -v
```

### 4.3 生成覆盖率报告

```bash
# 生成终端报告
pytest tests/ --cov=src --cov-report=term

# 生成 HTML 报告
pytest tests/ --cov=src --cov-report=html

# 生成 XML 报告
pytest tests/ --cov=src --cov-report=xml
```

### 4.4 生成 HTML 测试报告

```bash
pytest tests/ --html=report.html --self-contained-html
```

## 5. 测试数据

### 5.1 测试数据包构造

```python
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
```

### 5.2 测试规则数据

```python
def create_test_rules():
    """创建测试规则"""
    return [
        Rule(id="http", name="HTTP", priority=10, action=RuleAction.ACCEPT,
             protocol=Protocol.TCP, dst_port="80"),
        Rule(id="https", name="HTTPS", priority=11, action=RuleAction.ACCEPT,
             protocol=Protocol.TCP, dst_port="443"),
        Rule(id="ssh", name="SSH", priority=20, action=RuleAction.ACCEPT,
             protocol=Protocol.TCP, dst_port="22"),
        Rule(id="block-telnet", name="Block Telnet", priority=30, action=RuleAction.DROP,
             protocol=Protocol.TCP, dst_port="23"),
        Rule(id="default", name="Default", priority=1000, action=RuleAction.DROP),
    ]
```

## 6. 测试报告示例

### 6.1 终端输出

```
============================= test session starts ==============================
platform linux -- Python 3.10.12, pytest-7.4.0
collected 50 items

tests/test_packet.py::TestEthernetHeader::test_parse_valid PASSED      [  2%]
tests/test_packet.py::TestEthernetHeader::test_parse_too_short PASSED  [  4%]
tests/test_packet.py::TestIPHeader::test_parse_valid PASSED            [  6%]
tests/test_packet.py::TestIPHeader::test_parse_udp PASSED              [  8%]
tests/test_packet.py::TestIPHeader::test_parse_icmp PASSED             [ 10%]
tests/test_packet.py::TestIPHeader::test_parse_too_short PASSED        [ 12%]
tests/test_packet.py::TestIPHeader::test_parse_wrong_version PASSED    [ 14%]
tests/test_packet.py::TestTCPHeader::test_parse_syn PASSED             [ 16%]
tests/test_packet.py::TestTCPHeader::test_parse_syn_ack PASSED         [ 18%]
tests/test_packet.py::TestTCPHeader::test_parse_fin PASSED             [ 20%]
tests/test_packet.py::TestTCPHeader::test_parse_rst PASSED             [ 22%]
tests/test_packet.py::TestTCPHeader::test_flag_list PASSED             [ 24%]
tests/test_packet.py::TestTCPHeader::test_parse_too_short PASSED       [ 26%]
tests/test_packet.py::TestUDPHeader::test_parse_valid PASSED            [ 28%]
tests/test_packet.py::TestUDPHeader::test_parse_too_short PASSED       [ 30%]
tests/test_packet.py::TestICMPHeader::test_parse_echo_request PASSED   [ 32%]
tests/test_packet.py::TestICMPHeader::test_parse_echo_reply PASSED     [ 34%]
tests/test_packet.py::TestICMPHeader::test_parse_too_short PASSED      [ 36%]
tests/test_packet.py::TestPacket::test_parse_tcp_packet PASSED         [ 38%]
tests/test_packet.py::TestPacket::test_packet_info PASSED              [ 40%]
tests/test_packet.py::TestPacket::test_packet_str PASSED               [ 42%]
tests/test_packet.py::TestIPCIDR::test_exact_match PASSED              [ 44%]
tests/test_packet.py::TestIPCIDR::test_cidr_match PASSED               [ 46%]
tests/test_packet.py::TestIPCIDR::test_loopback PASSED                 [ 48%]
tests/test_packet.py::TestIPCIDR::test_private_networks PASSED         [ 50%]
tests/test_rules.py::TestRule::test_create_rule PASSED                 [ 52%]
tests/test_rules.py::TestRule::test_rule_matches_protocol PASSED       [ 54%]
tests/test_rules.py::TestRule::test_rule_matches_ip PASSED             [ 56%]
tests/test_rules.py::TestRule::test_rule_matches_port PASSED           [ 58%]
tests/test_rules.py::TestRule::test_rule_disabled PASSED               [ 60%]
tests/test_rules.py::TestRule::test_rule_expired PASSED                [ 62%]
tests/test_rules.py::TestRule::test_rule_match_count PASSED            [ 64%]
tests/test_rules.py::TestRule::test_rule_to_dict PASSED                [ 66%]
tests/test_rules.py::TestRule::test_rule_from_dict PASSED              [ 68%]
tests/test_rules.py::TestRuleSet::test_add_rule PASSED                 [ 70%]
tests/test_rules.py::TestRuleSet::test_priority_ordering PASSED        [ 72%]
tests/test_rules.py::TestRuleSet::test_match_first_rule PASSED         [ 74%]
tests/test_state.py::TestConnectionEntry::test_create_entry PASSED     [ 76%]
tests/test_state.py::TestConnectionEntry::test_update_activity PASSED  [ 78%]
tests/test_state.py::TestStateTable::test_create_connection PASSED     [ 80%]
tests/test_state.py::TestStateTable::test_bidirectional_matching PASSED [ 82%]
tests/test_state.py::TestConnectionTracker::test_new_connection PASSED [ 84%]
tests/test_state.py::TestConnectionTracker::test_established_connection PASSED [ 86%]
tests/test_firewall.py::TestFirewall::test_firewall_initialization PASSED [ 88%]
tests/test_firewall.py::TestFirewall::test_firewall_start_stop PASSED  [ 90%]
tests/test_firewall.py::TestFirewall::test_process_packet_accept PASSED [ 92%]
tests/test_firewall.py::TestFirewall::test_process_packet_drop PASSED  [ 94%]
tests/test_firewall.py::TestFirewall::test_rule_priority PASSED        [ 96%]
tests/test_firewall.py::TestFirewall::test_statistics PASSED            [ 98%]
tests/test_firewall.py::TestFirewall::test_not_running PASSED           [100%]

============================== 50 passed in 0.45s ===============================
```

### 6.2 覆盖率报告

```
Name                    Stmts   Miss  Cover
-------------------------------------------
src/__init__.py            15      0   100%
src/packet.py             185     12    94%
src/rules.py              198     18    91%
src/state.py              165     22    87%
src/logger.py             178     28    84%
src/config.py             112     15    87%
src/firewall.py           195     25    87%
-------------------------------------------
TOTAL                    1048    120    89%
```
