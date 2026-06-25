# 状态机框架开发指南

## 1. 开发环境

### 1.1 环境要求

- Python 3.8+
- 推荐使用虚拟环境
- IDE：VS Code、PyCharm 或其他 Python IDE

### 1.2 项目结构

```
state-machine/
├── src/                    # 源代码
│   ├── __init__.py        # 包初始化
│   ├── state_machine.py   # 核心状态机
│   ├── hierarchical.py    # 层次状态机
│   ├── state.py           # 状态定义
│   ├── event.py           # 事件定义
│   ├── transition.py      # 转换定义
│   ├── guard.py           # 守卫条件
│   ├── action.py          # 动作定义
│   ├── history.py         # 历史记录
│   └── error.py           # 错误定义
├── examples/              # 示例代码
│   ├── traffic_light.py
│   ├── order_processing.py
│   ├── game_ai.py
│   └── workflow_engine.py
├── tests/                 # 测试代码
│   └── test_state_machine.py
├── docs/                  # 文档
│   ├── 01_RESEARCH.md
│   ├── 02_ARCHITECTURE.md
│   ├── 03_DESIGN.md
│   ├── 04_IMPLEMENTATION.md
│   └── 05_DEVELOPMENT.md
└── README.md              # 项目说明
```

## 2. 开发流程

### 2.1 需求分析

1. 明确功能需求
2. 确定技术约束
3. 设计API接口
4. 编写用例文档

### 2.2 设计阶段

1. 类图设计
2. 序列图设计
3. 接口定义
4. 错误处理策略

### 2.3 实现阶段

1. 实现核心模块
2. 实现扩展模块
3. 编写单元测试
4. 编写集成测试

### 2.4 测试阶段

1. 单元测试
2. 集成测试
3. 性能测试
4. 用户验收测试

## 3. 编码规范

### 3.1 命名规范

```python
# 类名：PascalCase
class StateMachine:
    pass

# 函数名：snake_case
def process_event():
    pass

# 常量：UPPER_SNAKE_CASE
MAX_ENTRIES = 1000

# 私有属性：前缀下划线
self._current_state = None

# 受保护属性：前缀单下划线
self._internal_data = None
```

### 3.2 文档规范

```python
def process_event(self, event: Event, context: Optional[Dict[str, Any]] = None) -> bool:
    """
    处理事件，触发状态转换。

    Args:
        event: 要处理的事件
        context: 可选的上下文数据

    Returns:
        如果发生转换返回True，否则返回False

    Raises:
        InvalidEventError: 如果没有定义转换
    """
    pass
```

### 3.3 类型提示

```python
from typing import Any, Callable, Dict, List, Optional, Set, Union

def add_transition(self, transition: Transition) -> None:
    """添加转换。"""
    pass

def process_event(self, event: Event, context: Optional[Dict[str, Any]] = None) -> bool:
    """处理事件。"""
    pass
```

### 3.4 错误处理

```python
try:
    # 执行操作
    pass
except SpecificException as e:
    # 处理特定异常
    logger.error(f"Operation failed: {e}")
    raise
except Exception as e:
    # 处理其他异常
    logger.error(f"Unexpected error: {e}")
    raise StateMachineError(f"Operation failed: {e}") from e
```

## 4. 测试指南

### 4.1 单元测试

```python
import unittest
from src import StateMachine, State, Event, Transition

class TestStateMachine(unittest.TestCase):
    def setUp(self):
        """测试前准备。"""
        self.sm = StateMachine(State("Initial"))
    
    def test_process_event(self):
        """测试事件处理。"""
        self.sm.add_transition(Transition(
            State("Initial"),
            State("Final"),
            Event("Test")
        ))
        result = self.sm.process_event(Event("Test"))
        self.assertTrue(result)
        self.assertEqual(self.sm.current_state, State("Final"))
    
    def test_guard_rejection(self):
        """测试守卫拒绝。"""
        self.sm.add_transition(Transition(
            State("Initial"),
            State("Final"),
            Event("Test"),
            guard=FunctionGuard(lambda f, t, e, c: False)
        ))
        result = self.sm.process_event(Event("Test"))
        self.assertFalse(result)
```

### 4.2 集成测试

```python
class TestOrderWorkflow(unittest.TestCase):
    def test_complete_workflow(self):
        """测试完整订单流程。"""
        sm = create_order_state_machine()
        context = {"items": [...], "payment": 100}
        
        # 验证订单
        sm.process_event(VALIDATE, context)
        self.assertEqual(sm.current_state, VALIDATED)
        
        # 请求支付
        sm.process_event(REQUEST_PAYMENT, context)
        self.assertEqual(sm.current_state, PAYMENT_PENDING)
        
        # 确认支付
        sm.process_event(CONFIRM_PAYMENT, context)
        self.assertEqual(sm.current_state, PAID)
```

### 4.3 性能测试

```python
import time

class TestPerformance(unittest.TestCase):
    def test_many_transitions(self):
        """测试大量转换性能。"""
        sm = StateMachine(State("S0"))
        
        # 添加1000个转换
        for i in range(1000):
            sm.add_transition(Transition(
                State(f"S{i}"),
                State(f"S{i+1}"),
                Event(f"E{i}")
            ))
        
        # 测量处理时间
        start = time.time()
        for i in range(1000):
            sm.process_event(Event(f"E{i}"))
        elapsed = time.time() - start
        
        self.assertLess(elapsed, 1.0)  # 应该在1秒内完成
```

### 4.4 测试覆盖率

```bash
# 安装coverage
pip install coverage

# 运行测试并生成覆盖率报告
coverage run -m pytest tests/
coverage report -m
coverage html  # 生成HTML报告
```

## 5. 调试技巧

### 5.1 日志记录

```python
import logging

# 配置日志
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def process_event(self, event, context=None):
    logger.debug(f"Processing event: {event}")
    logger.debug(f"Current state: {self._current_state}")
    
    # ... 处理逻辑
    
    logger.info(f"Transition: {from_state} -> {to_state}")
```

### 5.2 状态可视化

```python
def format_state_machine(self):
    """格式化状态机为可读字符串。"""
    lines = ["State Machine:"]
    lines.append(f"  Current State: {self._current_state}")
    lines.append(f"  States: {len(self._states)}")
    lines.append(f"  Transitions: {len(self._transitions)}")
    return "\n".join(lines)
```

### 5.3 断点调试

```python
# 在关键位置设置断点
import pdb; pdb.set_trace()

# 或使用IDE的调试器
# VS Code: F9 设置断点，F5 启动调试
# PyCharm: Ctrl+F8 设置断点，Shift+F9 启动调试
```

## 6. 性能优化

### 6.1 查找优化

```python
# 使用索引优化转换查找
self._transition_index = {}

def _build_index(self):
    for transition in self._transitions:
        key = (transition.from_state, transition.event)
        if key not in self._transition_index:
            self._transition_index[key] = []
        self._transition_index[key].append(transition)
```

### 6.2 内存优化

```python
# 使用__slots__减少内存占用
class State:
    __slots__ = ['_name', '_metadata', '_entry_actions', '_exit_actions']

# 使用生成器减少中间列表
def entries_reversed(self):
    return reversed(self._entries)
```

### 6.3 惰性计算

```python
# 延迟计算可能事件
def possible_events(self):
    return [
        t.event for t in self._transitions
        if t.from_state == self._current_state
    ]
```

## 7. 扩展开发

### 7.1 自定义守卫

```python
class CustomGuard(Guard):
    def __init__(self, param):
        self.param = param
    
    def check(self, from_state, to_state, event, context):
        # 自定义逻辑
        return context.get(self.param) is not None

# 使用
guard = CustomGuard("required_field")
```

### 7.2 自定义动作

```python
class CustomAction(Action):
    def __init__(self, service):
        self.service = service
    
    def execute(self, from_state, to_state, event, context):
        # 调用外部服务
        self.service.notify_transition(from_state, to_state, event)

# 使用
action = CustomAction(notification_service)
```

### 7.3 自定义序列化

```python
class JsonSerializer:
    def serialize(self, sm):
        return json.dumps({
            "state": str(sm.current_state),
            "context": sm.context
        })
    
    def deserialize(self, data):
        # 自定义反序列化
        pass
```

## 8. 部署指南

### 8.1 打包

```bash
# 创建setup.py
# 打包
python setup.py sdist bdist_wheel

# 或使用现代打包工具
pip install build
python -m build
```

### 8.2 发布

```bash
# 安装twine
pip install twine

# 上传到PyPI
twine upload dist/*
```

### 8.3 版本管理

```python
# 在__init__.py中定义版本
__version__ = "1.0.0"

# 使用语义化版本
# MAJOR.MINOR.PATCH
# 1.0.0 -> 1.0.1 (bug fix)
# 1.0.0 -> 1.1.0 (new feature)
# 1.0.0 -> 2.0.0 (breaking change)
```

## 9. 文档编写

### 9.1 API文档

```python
def process_event(self, event: Event, context: Optional[Dict[str, Any]] = None) -> bool:
    """
    处理事件，触发状态转换。

    这个方法会查找匹配的转换，检查守卫条件，执行动作，
    并更新当前状态。

    Args:
        event: 要处理的事件对象
        context: 可选的上下文数据，会与实例上下文合并

    Returns:
        bool: 如果发生转换返回True，否则返回False

    Examples:
        >>> sm = StateMachine(State("Off"))
        >>> sm.add_transition(Transition(State("Off"), State("On"), Event("TurnOn")))
        >>> sm.process_event(Event("TurnOn"))
        True
        >>> sm.current_state
        State('On')

    Notes:
        如果没有定义匹配的转换，不会抛出异常，而是返回False。
        可以通过on_transition_failed回调监听失败事件。

    See Also:
        add_transition: 添加转换
        can_process_event: 检查事件是否可处理
    """
    pass
```

### 9.2 示例文档

```python
# examples/traffic_light.py
"""
交通灯状态机示例

演示功能：
- 简单状态转换
- 进入/退出动作
- 定时器事件
- 紧急情况处理

运行方式：
    python traffic_light.py
"""
```

## 10. 常见问题

### 10.1 状态冲突

**问题**：多个转换匹配同一状态和事件

**解决**：
- 使用优先级系统
- 使用第一个匹配的转换
- 抛出配置错误

### 10.2 死锁

**问题**：状态机无法继续

**解决**：
- 添加超时机制
- 添加取消机制
- 检查守卫条件

### 10.3 内存泄漏

**问题**：历史记录无限增长

**解决**：
- 设置最大容量
- 自动淘汰旧记录
- 定期清理

### 10.4 性能问题

**问题**：大量转换时性能下降

**解决**：
- 使用索引优化查找
- 减少守卫和动作的复杂度
- 使用惰性计算

## 11. 最佳实践

### 11.1 状态设计

- 保持状态数量合理
- 使用有意义的名称
- 避免过度嵌套

### 11.2 事件设计

- 明确事件语义
- 避免歧义
- 使用数据传递信息

### 11.3 守卫设计

- 保持简单
- 避免副作用
- 提供有意义的名称

### 11.4 动作设计

- 单一职责
- 错误处理
- 幂等性（如果可能）

## 12. 工具推荐

### 12.1 IDE

- **VS Code**：轻量级，插件丰富
- **PyCharm**：功能强大，专业Python IDE

### 12.2 测试工具

- **pytest**：现代测试框架
- **coverage**：代码覆盖率
- **tox**：自动化测试

### 12.3 代码质量

- **flake8**：代码风格检查
- **black**：代码格式化
- **mypy**：类型检查

### 12.4 文档工具

- **Sphinx**：文档生成
- **pdoc**：API文档生成
- **MkDocs**：Markdown文档

## 13. 贡献指南

### 13.1 代码贡献

1. Fork项目
2. 创建功能分支
3. 编写代码和测试
4. 提交Pull Request

### 13.2 问题报告

1. 使用Issue模板
2. 提供复现步骤
3. 包含错误信息
4. 说明环境信息

### 13.3 文档贡献

1. 检查拼写和语法
2. 提供示例代码
3. 更新API文档
4. 翻译文档

## 14. 路线图

### 14.1 短期目标

- 完善单元测试
- 优化性能
- 添加更多示例

### 14.2 中期目标

- 支持并发状态机
- 添加可视化工具
- 实现序列化

### 14.3 长期目标

- 支持分布式状态机
- 添加监控和调试工具
- 建立生态系统

## 15. 资源链接

### 15.1 官方资源

- Python官方文档：https://docs.python.org/
- PyPI：https://pypi.org/

### 15.2 学习资源

- Real Python：https://realpython.com/
- Python Wiki：https://wiki.python.org/

### 15.3 社区资源

- Python Discord：https://pythondiscord.com/
- Reddit r/Python：https://www.reddit.com/r/Python/
