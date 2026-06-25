# 防火墙开发手册

## 1. 开发环境

### 1.1 环境要求

- **Python**: 3.8+
- **操作系统**: Linux / macOS / Windows
- **依赖管理**: pip

### 1.2 安装依赖

```bash
cd projects/firewall/python
pip install -r requirements.txt
```

### 1.3 开发工具推荐

- **编辑器**: VS Code / PyCharm
- **测试框架**: pytest
- **代码格式**: black
- **代码检查**: flake8 / mypy

## 2. 项目结构

```
python/
├── README.md                    # 项目说明
├── requirements.txt             # 依赖列表
├── setup.py                     # 安装脚本
├── src/                         # 源代码
│   ├── __init__.py
│   ├── packet.py               # 数据包解析
│   ├── rules.py                # 规则引擎
│   ├── state.py                # 状态检测
│   ├── logger.py               # 日志记录
│   ├── config.py               # 配置管理
│   └── firewall.py             # 防火墙主引擎
├── tests/                       # 测试代码
│   ├── __init__.py
│   ├── test_packet.py
│   ├── test_rules.py
│   ├── test_state.py
│   └── test_firewall.py
├── examples/                    # 示例程序
│   ├── basic_firewall.py
│   ├── rule_management.py
│   └── ids_example.py
├── configs/                     # 配置文件
│   ├── firewall.yaml
│   └── rules.json
└── docs/                        # 文档
    ├── 01-RESEARCH.md
    ├── 02-REQUIREMENTS.md
    ├── 03-DESIGN.md
    ├── 04-TESTING.md
    └── 05-DEVELOPMENT.md
```

## 3. 编码规范

### 3.1 代码风格

遵循 PEP 8 规范：

```python
# 使用 4 空格缩进
def function_name(param1: str, param2: int) -> bool:
    """函数文档字符串"""
    # 代码
    return True

# 类名使用 CamelCase
class ClassName:
    """类文档字符串"""
    pass

# 常量使用 UPPER_CASE
MAX_CONNECTIONS = 10000
```

### 3.2 类型提示

使用类型提示提高代码可读性：

```python
from typing import Optional, List, Dict, Tuple

def process_packet(packet: Packet, is_outgoing: bool = False) -> RuleAction:
    """处理数据包"""
    pass

def get_connections() -> List[ConnectionEntry]:
    """获取连接列表"""
    pass
```

### 3.3 文档字符串

使用 Google 风格的文档字符串：

```python
def function_name(param1: str, param2: int) -> bool:
    """函数简短描述

    函数详细描述（可选）。

    Args:
        param1: 参数1描述
        param2: 参数2描述

    Returns:
        返回值描述

    Raises:
        ValueError: 异常描述
    """
    pass
```

### 3.4 命名规范

| 类型 | 规范 | 示例 |
|------|------|------|
| 模块名 | 小写下划线 | `packet.py` |
| 类名 | 大驼峰 | `PacketInfo` |
| 函数名 | 小写下划线 | `parse_packet` |
| 变量名 | 小写下划线 | `src_ip` |
| 常量名 | 大写下划线 | `MAX_SIZE` |
| 私有成员 | 前缀下划线 | `_internal_var` |

## 4. 开发流程

### 4.1 功能开发

1. **创建分支**

```bash
git checkout -b feature/new-feature
```

2. **编写代码**

```python
# src/new_module.py
class NewClass:
    """新功能类"""
    pass
```

3. **编写测试**

```python
# tests/test_new_module.py
class TestNewClass:
    def test_basic(self):
        """测试基本功能"""
        obj = NewClass()
        assert obj is not None
```

4. **运行测试**

```bash
pytest tests/test_new_module.py -v
```

5. **提交代码**

```bash
git add .
git commit -m "feat: add new feature"
```

### 4.2 Bug 修复

1. **重现 Bug**

```bash
pytest tests/test_module.py::test_case -v
```

2. **修复代码**

```python
# 修复 bug
def fixed_function():
    pass
```

3. **验证修复**

```bash
pytest tests/test_module.py::test_case -v
```

4. **提交修复**

```bash
git commit -m "fix: fix bug description"
```

### 4.3 代码审查清单

- [ ] 代码符合 PEP 8 规范
- [ ] 有完整的类型提示
- [ ] 有完整的文档字符串
- [ ] 有充分的单元测试
- [ ] 测试覆盖率达标
- [ ] 无明显性能问题
- [ ] 无安全隐患

## 5. 模块开发指南

### 5.1 添加新的数据包协议

1. **定义协议类型**

```python
# src/packet.py
class Protocol(Enum):
    TCP = 6
    UDP = 17
    ICMP = 1
    NEW_PROTOCOL = 99  # 新增
```

2. **实现解析器**

```python
@dataclass
class NewProtocolHeader:
    """新协议头"""
    field1: int
    field2: int

    @staticmethod
    def parse(data: bytes) -> Optional['NewProtocolHeader']:
        """解析协议头"""
        if len(data) < 8:
            return None
        # 解析逻辑
        return NewProtocolHeader(field1=field1, field2=field2)
```

3. **更新 Packet 类**

```python
@dataclass
class Packet:
    new_protocol: Optional[NewProtocolHeader] = None

    @staticmethod
    def parse(data: bytes) -> Optional['Packet']:
        # 解析逻辑
        if protocol == Protocol.NEW_PROTOCOL:
            packet.new_protocol = NewProtocolHeader.parse(transport_data)
```

4. **编写测试**

```python
class TestNewProtocolHeader:
    def test_parse_valid(self):
        """测试有效解析"""
        data = struct.pack('!II', 1, 2)
        header = NewProtocolHeader.parse(data)
        assert header is not None
        assert header.field1 == 1
```

### 5.2 添加新的规则匹配条件

1. **更新 Rule 类**

```python
@dataclass
class Rule:
    # 新增字段
    new_field: Optional[str] = None

    def matches(self, packet_info: PacketInfo) -> bool:
        # 新增匹配逻辑
        if self.new_field is not None:
            if not self._match_new_field(packet_info):
                return False
        return True
```

2. **更新 PacketInfo 类**

```python
@dataclass
class PacketInfo:
    # 新增字段
    new_attribute: Optional[int] = None
```

3. **更新规则构建器**

```python
class RuleBuilder:
    def new_field(self, value: str) -> 'RuleBuilder':
        """设置新字段"""
        self._rule.new_field = value
        return self
```

4. **编写测试**

```python
class TestNewMatching:
    def test_new_field_match(self):
        """测试新字段匹配"""
        rule = Rule(
            id="test",
            name="Test",
            action=RuleAction.ACCEPT,
            new_field="value",
        )
        info = PacketInfo(new_attribute=123)
        assert rule.matches(info) is True
```

### 5.3 添加新的入侵检测规则

1. **更新 IntrusionDetector 类**

```python
class IntrusionDetector:
    def __init__(self):
        # 新增跟踪器
        self._new_attack_tracker: Dict[str, int] = {}

    def analyze_packet(self, packet_info, action):
        # 新增检测逻辑
        self._check_new_attack(packet_info)

    def _check_new_attack(self, packet_info):
        """检测新攻击类型"""
        # 检测逻辑
        pass
```

2. **添加配置项**

```python
@dataclass
class FirewallConfig:
    # 新增配置
    new_attack_threshold: int = 100
```

3. **编写测试**

```python
class TestNewAttackDetection:
    def test_new_attack_detection(self):
        """测试新攻击检测"""
        detector = IntrusionDetector()
        # 测试逻辑
```

## 6. 调试技巧

### 6.1 使用日志调试

```python
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def debug_function():
    logger.debug("Debug message")
    logger.info("Info message")
    logger.warning("Warning message")
```

### 6.2 使用断点调试

```python
def function_to_debug():
    breakpoint()  # Python 3.7+
    # 代码
```

### 6.3 使用 pytest 调试

```bash
# 显示详细输出
pytest tests/ -v -s

# 只运行失败的测试
pytest tests/ --lf

# 在第一个失败时停止
pytest tests/ -x

# 显示本地变量
pytest tests/ -l
```

### 6.4 使用覆盖率定位问题

```bash
# 显示未覆盖的行
pytest tests/ --cov=src --cov-report=term-missing
```

## 7. 性能优化

### 7.1 性能分析

```python
import cProfile

def function_to_profile():
    pass

cProfile.run('function_to_profile()')
```

### 7.2 常见优化

1. **使用 __slots__**

```python
class OptimizedClass:
    __slots__ = ['field1', 'field2']

    def __init__(self, field1, field2):
        self.field1 = field1
        self.field2 = field2
```

2. **使用生成器**

```python
def get_items():
    for item in large_list:
        yield item
```

3. **缓存计算结果**

```python
from functools import lru_cache

@lru_cache(maxsize=128)
def expensive_function(param):
    # 复杂计算
    return result
```

4. **使用适当的数据结构**

```python
# 使用 set 而不是 list 进行查找
valid_ports = {80, 443, 8080}
if port in valid_ports:
    pass
```

## 8. 发布流程

### 8.1 版本管理

使用语义化版本：

```
MAJOR.MINOR.PATCH

MAJOR: 不兼容的 API 修改
MINOR: 向下兼容的功能性新增
PATCH: 向下兼容的问题修正
```

### 8.2 发布清单

- [ ] 所有测试通过
- [ ] 测试覆盖率达标
- [ ] 文档已更新
- [ ] 版本号已更新
- [ ] CHANGELOG 已更新

### 8.3 发布步骤

1. **更新版本号**

```python
# src/__init__.py
__version__ = "1.1.0"
```

2. **运行测试**

```bash
pytest tests/ -v
```

3. **生成文档**

```bash
# 如果使用 Sphinx
cd docs
make html
```

4. **提交发布**

```bash
git add .
git commit -m "release: v1.1.0"
git tag v1.1.0
```

## 9. 常见问题

### 9.1 测试失败

**问题**: 测试导入错误

```bash
ModuleNotFoundError: No module named 'src'
```

**解决**: 确保在正确的目录运行测试

```bash
cd projects/firewall/python
pytest tests/
```

### 9.2 性能问题

**问题**: 规则匹配慢

**解决**: 
- 使用优先级排序
- 减少规则数量
- 使用缓存

### 9.3 内存问题

**问题**: 内存占用高

**解决**:
- 限制最大连接数
- 定期清理过期连接
- 使用环形缓冲区

## 10. 参考资源

### 10.1 Python 文档

- [Python 官方文档](https://docs.python.org/3/)
- [typing 模块](https://docs.python.org/3/library/typing.html)
- [dataclasses 模块](https://docs.python.org/3/library/dataclasses.html)

### 10.2 测试框架

- [pytest 文档](https://docs.pytest.org/)
- [pytest-cov 文档](https://pytest-cov.readthedocs.io/)

### 10.3 网络编程

- [socket 模块](https://docs.python.org/3/library/socket.html)
- [struct 模块](https://docs.python.org/3/library/struct.html)

### 10.4 防火墙相关

- [Netfilter 文档](https://www.netfilter.org/documentation.html)
- [iptables 教程](https://www.booleanworld.com/depth-guide-iptables-linux-firewall/)
