# 防火墙技术设计

## 1. 系统架构

### 1.1 整体架构

```
┌─────────────────────────────────────────────────────────────┐
│                      防火墙引擎 (Firewall)                   │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│  │ 包解析器  │  │ 规则引擎  │  │ 状态检测  │  │ 日志记录  │  │
│  │ (Packet) │  │ (Rules)  │  │ (State)  │  │ (Logger) │  │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘  │
│                                                             │
│  ┌──────────┐  ┌──────────┐                                │
│  │ 入侵检测  │  │ 配置管理  │                                │
│  │  (IDS)   │  │ (Config) │                                │
│  └──────────┘  └──────────┘                                │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 1.2 模块依赖关系

```
Firewall
    ├── Packet (数据包解析)
    ├── RuleSet (规则管理)
    │   └── Rule (单条规则)
    ├── ConnectionTracker (连接跟踪)
    │   └── StateTable (状态表)
    ├── FirewallLogger (日志记录)
    │   └── LogBuffer (日志缓冲)
    ├── IntrusionDetector (入侵检测)
    └── ConfigManager (配置管理)
        └── FirewallConfig (配置对象)
```

### 1.3 数据流

```
输入数据包
    │
    ▼
┌─────────────────┐
│   包解析模块     │
│  (Packet.parse) │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   状态检测模块   │
│ (ConnectionTracker)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   规则匹配模块   │
│  (RuleSet.match)│
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   动作执行       │
│  (ACCEPT/DROP)  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   日志记录       │
│  (Logger.log)   │
└─────────────────┘
```

## 2. 模块设计

### 2.1 数据包解析模块 (packet.py)

#### 2.1.1 类设计

```python
class Protocol(Enum):
    """协议类型"""
    TCP = 6
    UDP = 17
    ICMP = 1

class TCPFlag(Enum):
    """TCP 标志位"""
    SYN = 0x02
    ACK = 0x10
    FIN = 0x01
    RST = 0x04

@dataclass
class PacketInfo:
    """数据包信息摘要"""
    timestamp: float
    src_ip: str
    dst_ip: str
    protocol: Protocol
    src_port: Optional[int]
    dst_port: Optional[int]
    length: int

class Packet:
    """完整数据包"""
    raw_data: bytes
    ip: Optional[IPHeader]
    tcp: Optional[TCPHeader]
    udp: Optional[UDPHeader]
    icmp: Optional[ICMPHeader]

    @staticmethod
    def parse(data: bytes) -> Optional['Packet']:
        """解析数据包"""

    @property
    def info(self) -> PacketInfo:
        """获取数据包信息"""
```

#### 2.1.2 解析流程

```
原始数据
    │
    ▼
解析以太网帧头 (14 字节)
    │
    ▼
解析 IP 数据包头 (20+ 字节)
    │
    ├── TCP → 解析 TCP 头 (20+ 字节)
    ├── UDP → 解析 UDP 头 (8 字节)
    └── ICMP → 解析 ICMP 头 (8 字节)
```

#### 2.1.3 关键算法

**IP 地址 CIDR 匹配**：

```python
def ip_in_cidr(ip: str, cidr: str) -> bool:
    network, prefix = cidr.split('/')
    ip_int = struct.unpack('!I', socket.inet_aton(ip))[0]
    network_int = struct.unpack('!I', socket.inet_aton(network))[0]
    mask = (0xFFFFFFFF << (32 - int(prefix))) & 0xFFFFFFFF
    return (ip_int & mask) == (network_int & mask)
```

**端口范围匹配**：

```python
def port_in_range(port: int, port_range: str) -> bool:
    if '-' in port_range:
        start, end = port_range.split('-')
        return int(start) <= port <= int(end)
    elif ',' in port_range:
        ports = [int(p) for p in port_range.split(',')]
        return port in ports
    else:
        return port == int(port_range)
```

### 2.2 规则引擎模块 (rules.py)

#### 2.2.1 类设计

```python
class RuleAction(Enum):
    """规则动作"""
    ACCEPT = "accept"
    DROP = "drop"
    REJECT = "reject"

class RuleDirection(Enum):
    """规则方向"""
    INCOMING = "incoming"
    OUTGOING = "outgoing"
    BOTH = "both"

@dataclass
class Rule:
    """防火墙规则"""
    id: str
    name: str
    priority: int
    action: RuleAction
    protocol: Optional[Protocol]
    src_ip: Optional[str]
    dst_ip: Optional[str]
    src_port: Optional[str]
    dst_port: Optional[str]
    enabled: bool

    def matches(self, packet_info: PacketInfo) -> bool:
        """检查是否匹配数据包"""

class RuleSet:
    """规则集"""
    _rules: Dict[str, Rule]

    def add_rule(self, rule: Rule) -> bool:
        """添加规则"""

    def remove_rule(self, rule_id: str) -> bool:
        """删除规则"""

    def match(self, packet_info: PacketInfo) -> Optional[Rule]:
        """匹配数据包"""
```

#### 2.2.2 匹配算法

```
输入: PacketInfo
    │
    ▼
按优先级排序规则列表
    │
    ▼
遍历规则列表
    │
    ├── 检查协议匹配
    ├── 检查源 IP 匹配
    ├── 检查目的 IP 匹配
    ├── 检查源端口匹配
    └── 检查目的端口匹配
    │
    ▼
返回第一个匹配的规则
```

#### 2.2.3 优先级设计

- 数值越小，优先级越高
- 默认优先级范围：1-1000
- 预留优先级：
  - 1-10: 系统规则（回环等）
  - 11-100: 业务规则
  - 101-500: 安全规则
  - 501-1000: 默认规则

### 2.3 状态检测模块 (state.py)

#### 2.3.1 类设计

```python
class ConnectionState(Enum):
    """连接状态"""
    NEW = "new"
    ESTABLISHED = "established"
    RELATED = "related"
    CLOSED = "closed"

class TCPState(Enum):
    """TCP 状态机"""
    CLOSED = auto()
    SYN_SENT = auto()
    SYN_RECEIVED = auto()
    ESTABLISHED = auto()
    FIN_WAIT_1 = auto()
    FIN_WAIT_2 = auto()
    CLOSE_WAIT = auto()
    LAST_ACK = auto()
    TIME_WAIT = auto()

@dataclass
class ConnectionEntry:
    """连接表项"""
    key: str
    state: ConnectionState
    protocol: Protocol
    src_ip: str
    src_port: Optional[int]
    dst_ip: str
    dst_port: Optional[int]
    created_at: float
    last_seen: float
    timeout: int

class StateTable:
    """状态表"""
    _entries: Dict[str, ConnectionEntry]

    def get_connection(self, packet_info: PacketInfo) -> Optional[ConnectionEntry]:
        """获取连接"""

    def create_connection(self, packet_info: PacketInfo) -> ConnectionEntry:
        """创建连接"""

    def update_connection(self, packet_info: PacketInfo) -> Optional[ConnectionEntry]:
        """更新连接"""

class ConnectionTracker:
    """连接跟踪器"""
    _state_table: StateTable

    def process_packet(self, packet_info: PacketInfo) -> Tuple[ConnectionState, ConnectionEntry]:
        """处理数据包"""
```

#### 2.3.2 连接键设计

使用双向匹配，将较小的 IP:Port 放在前面：

```python
def _make_key(self, protocol, src_ip, src_port, dst_ip, dst_port):
    src = f"{src_ip}:{src_port}"
    dst = f"{dst_ip}:{dst_port}"
    if (src_ip, src_port) > (dst_ip, dst_port):
        src, dst = dst, src
    return f"{protocol.name}:{src}-{dst}"
```

#### 2.3.3 TCP 状态机

```
         ┌─────────────────────────────────────┐
         │                                     │
         ▼                                     │
    ┌─────────┐    SYN     ┌───────────┐      │
    │ CLOSED  │ ──────────→│ SYN_SENT  │      │
    └─────────┘            └───────────┘      │
         │                        │            │
         │ SYN              SYN-ACK│            │
         ▼                        ▼            │
    ┌──────────────┐      ┌─────────────┐     │
    │ SYN_RECEIVED │ ────→│ ESTABLISHED │     │
    └──────────────┘ ACK  └─────────────┘     │
                              │    ▲           │
                        FIN   │    │ ACK       │
                              ▼    │           │
                        ┌───────────────┐     │
                        │  FIN_WAIT_1   │     │
                        └───────────────┘     │
                              │               │
                        ACK   │               │
                              ▼               │
                        ┌───────────────┐     │
                        │  FIN_WAIT_2   │     │
                        └───────────────┘     │
                              │               │
                        FIN   │               │
                              ▼               │
                        ┌───────────────┐     │
                        │  TIME_WAIT    │─────┘
                        └───────────────┘
```

#### 2.3.4 超时管理

```python
# 超时配置
TCP_TIMEOUT = 300       # TCP 连接超时 5 分钟
TCP_FIN_TIMEOUT = 30    # FIN_WAIT 超时 30 秒
UDP_TIMEOUT = 60        # UDP 超时 1 分钟
ICMP_TIMEOUT = 30       # ICMP 超时 30 秒
```

### 2.4 日志记录模块 (logger.py)

#### 2.4.1 类设计

```python
class LogLevel(Enum):
    """日志级别"""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    ALERT = "alert"

class LogType(Enum):
    """日志类型"""
    TRAFFIC = "traffic"
    RULE = "rule"
    ALERT = "alert"
    STATE = "state"
    SYSTEM = "system"

@dataclass
class LogEntry:
    """日志条目"""
    timestamp: float
    log_type: LogType
    level: LogLevel
    message: str
    packet_info: Optional[PacketInfo]
    rule: Optional[Rule]

class LogBuffer:
    """日志缓冲区（环形缓冲）"""
    _buffer: List[LogEntry]
    _max_size: int

class FirewallLogger:
    """日志记录器"""
    _buffer: LogBuffer
    _logger: logging.Logger

    def log_traffic(self, packet_info, action, rule=None):
        """记录流量日志"""

    def log_alert(self, message, packet_info=None):
        """记录告警日志"""
```

#### 2.4.2 日志格式

**文本格式**：

```
2024-01-15 10:30:45 | [INFO] | [traffic] | [TCP] 192.168.1.1:12345 -> 10.0.0.1:80 | rule=HTTP Allow | action=accept
```

**JSON 格式**：

```json
{
  "timestamp": 1705312245.123,
  "datetime": "2024-01-15T10:30:45.123",
  "log_type": "traffic",
  "level": "info",
  "packet": {
    "src_ip": "192.168.1.1",
    "dst_ip": "10.0.0.1",
    "protocol": "TCP",
    "src_port": 12345,
    "dst_port": 80
  },
  "rule": {
    "id": "http-allow",
    "name": "HTTP Allow"
  },
  "action": "accept"
}
```

### 2.5 入侵检测模块 (logger.py - IntrusionDetector)

#### 2.5.1 类设计

```python
class IntrusionDetector:
    """入侵检测器"""
    _connection_attempts: Dict[str, List[float]]
    _port_scan_tracker: Dict[str, set]
    _syn_flood_tracker: Dict[str, int]

    # 阈值配置
    _max_connections_per_minute: int = 100
    _max_ports_per_minute: int = 20
    _syn_flood_threshold: int = 1000

    def analyze_packet(self, packet_info: PacketInfo, action: RuleAction):
        """分析数据包"""

    def _check_connection_rate(self, packet_info, current_time):
        """检查连接频率"""

    def _check_port_scan(self, packet_info, current_time):
        """检查端口扫描"""

    def _check_syn_flood(self, packet_info, current_time):
        """检查 SYN Flood"""
```

#### 2.5.2 检测算法

**连接频率检测**：

```python
def _check_connection_rate(self, packet_info, current_time):
    src_ip = packet_info.src_ip

    # 清理 60 秒前的记录
    self._connection_attempts[src_ip] = [
        t for t in self._connection_attempts[src_ip]
        if current_time - t < 60
    ]

    # 添加新记录
    self._connection_attempts[src_ip].append(current_time)

    # 检查阈值
    if len(self._connection_attempts[src_ip]) > self._max_connections_per_minute:
        self._logger.log_alert(...)
```

**端口扫描检测**：

```python
def _check_port_scan(self, packet_info, current_time):
    src_ip = packet_info.src_ip
    dst_port = packet_info.dst_port

    # 记录访问的端口
    self._port_scan_tracker[src_ip].add(dst_port)

    # 检查阈值
    if len(self._port_scan_tracker[src_ip]) > self._max_ports_per_minute:
        self._logger.log_alert(...)
```

### 2.6 配置管理模块 (config.py)

#### 2.6.1 类设计

```python
@dataclass
class FirewallConfig:
    """防火墙配置"""
    name: str
    log_dir: str
    log_level: str
    max_connections: int
    enable_stateful: bool
    enable_ids: bool
    default_action: str
    tcp_timeout: int
    udp_timeout: int
    icmp_timeout: int

class ConfigManager:
    """配置管理器"""
    _config: FirewallConfig
    _ruleset: RuleSet

    def load_config(self, filepath: str) -> FirewallConfig:
        """加载配置"""

    def save_config(self, filepath: str):
        """保存配置"""

    def load_rules(self, filepath: str) -> RuleSet:
        """加载规则"""

    def save_rules(self, filepath: str):
        """保存规则"""
```

## 3. 数据结构设计

### 3.1 规则存储

使用字典存储规则，支持 O(1) 查找：

```python
class RuleSet:
    _rules: Dict[str, Rule]  # key: rule_id
    _sorted_rules: List[Rule]  # 按优先级排序
    _dirty: bool  # 是否需要重新排序
```

### 3.2 状态表存储

使用字典存储连接，支持 O(1) 查找：

```python
class StateTable:
    _entries: Dict[str, ConnectionEntry]  # key: connection_key
```

### 3.3 日志缓冲

使用列表作为环形缓冲区：

```python
class LogBuffer:
    _buffer: List[LogEntry]
    _max_size: int = 10000
```

## 4. 线程安全设计

### 4.1 锁策略

```python
class StateTable:
    _lock: threading.RLock

    def get_connection(self, packet_info):
        with self._lock:
            # 操作
```

### 4.2 回调机制

```python
class Firewall:
    _packet_callbacks: List[Callable[[PacketInfo, RuleAction], None]]
    _alert_callbacks: List[Callable[[str, PacketInfo], None]]
```

## 5. 错误处理设计

### 5.1 异常类型

```python
class FirewallError(Exception):
    """防火墙基础异常"""

class ConfigError(FirewallError):
    """配置错误"""

class RuleError(FirewallError):
    """规则错误"""

class PacketParseError(FirewallError):
    """数据包解析错误"""
```

### 5.2 错误处理策略

1. **数据包解析失败**：返回 None，记录警告日志
2. **规则匹配失败**：执行默认动作
3. **配置加载失败**：使用默认配置
4. **日志写入失败**：忽略错误，不影响主流程

## 6. 性能优化设计

### 6.1 规则匹配优化

1. **按协议分组**：先检查协议，减少匹配次数
2. **缓存排序结果**：规则修改时才重新排序
3. **早期退出**：匹配成功立即返回

### 6.2 状态表优化

1. **定期清理**：后台线程清理过期连接
2. **最大连接数限制**：防止内存溢出
3. **LRU 淘汰**：移除最旧的连接

### 6.3 日志优化

1. **异步写入**：使用缓冲区批量写入
2. **日志级别过滤**：减少不必要的日志
3. **环形缓冲**：自动清理旧日志

## 7. 测试设计

### 7.1 单元测试

- 数据包解析测试
- 规则匹配测试
- 状态检测测试
- 日志记录测试

### 7.2 集成测试

- 防火墙引擎测试
- 配置加载测试
- 规则持久化测试

### 7.3 性能测试

- 规则匹配性能
- 状态表查询性能
- 日志写入性能
