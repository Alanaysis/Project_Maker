"""
跨平台框架原理 - Cross-Platform Framework Principles

核心模块：Dart VM 模拟器
功能：模拟 Dart 虚拟机的字节码执行和垃圾回收机制

跨平台框架原理说明：
在 Flutter 中，Dart 代码会被编译成平台原生的机器码（AOT）或中间字节码（JIT/Interpreter）。
Dart VM 负责管理内存（垃圾回收）、执行 Dart 代码，并通过 Platform Channel 与原生平台通信。

本模块模拟以下核心概念：
1. Dart 字节码执行 - 将 Dart 源码编译为可执行的字节码指令
2. 垃圾回收 - 标记-清除算法的简化实现
3. 对象模型 - Dart 中一切皆对象的实现
"""

import time
import random
from enum import Enum
from typing import Any, Dict, List, Optional, Callable


# ============================================================
# 字节码指令集 (Bytecode Instruction Set)
# ============================================================
# Flutter 将 Dart 代码编译为紧凑的字节码格式
# 这些指令在 VM 中执行，与原生平台无关
class Opcode(Enum):
    """Dart 字节码指令类型"""
    # 常量加载
    LOAD_CONST = "LOAD_CONST"           # 将常量压入栈
    LOAD_GLOBAL = "LOAD_GLOBAL"         # 加载全局变量
    LOAD_LOCAL = "LOAD_LOCAL"           # 加载局部变量

    # 算术运算
    ADD = "ADD"                         # 加法
    SUB = "SUB"                         # 减法
    MUL = "MUL"                         # 乘法
    DIV = "DIV"                         # 除法

    # 控制流
    JUMP = "JUMP"                     # 无条件跳转
    JUMP_IF_FALSE = "JUMP_IF_FALSE"   # 条件跳转
    CALL = "CALL"                       # 函数调用
    RETURN = "RETURN"                   # 返回

    # 对象操作
    NEW_OBJECT = "NEW_OBJECT"           # 创建新对象
    SET_ATTR = "SET_ATTR"               # 设置对象属性
    GET_ATTR = "GET_ATTR"               # 获取对象属性
    NEW_LIST = "NEW_LIST"               # 创建列表

    # 平台通道
    PLATFORM_CHANNEL_CALL = "PLATFORM_CHANNEL_CALL"  # 调用平台通道
    PLATFORM_CHANNEL_RESPONSE = "PLATFORM_CHANNEL_RESPONSE"  # 平台通道响应


# ============================================================
# Dart 对象模型 (Object Model)
# ============================================================
class DartObject:
    """
    Dart 对象模型

    在 Dart 中，所有对象都继承自 Object。
    每个 Dart 对象都有：
    - 对象 ID（内存地址模拟）
    - 类型信息
    - 属性字典
    - 标记位（用于垃圾回收）
    """

    _next_id = 0

    def __init__(self, obj_type: str, **kwargs):
        DartObject._next_id += 1
        self._id = DartObject._next_id
        self._type = obj_type
        self._attrs: Dict[str, Any] = kwargs
        self._marked = False  # GC 标记位

    @property
    def id(self) -> int:
        return self._id

    @property
    def type(self) -> str:
        return self._type

    def get_attr(self, name: str) -> Any:
        """获取对象属性（模拟 Dart 的属性访问）"""
        return self._attrs.get(name)

    def set_attr(self, name: str, value: Any):
        """设置对象属性"""
        self._attrs[name] = value

    def mark(self):
        """标记对象（GC 使用）"""
        self._marked = True

    def is_marked(self) -> bool:
        return self._marked

    def clear_mark(self):
        """清除标记（GC 使用）"""
        self._marked = False

    def __repr__(self):
        return f"DartObject(id={self._id}, type={self._type}, attrs={self._attrs})"


class DartList(DartObject):
    """Dart List 的模拟实现"""

    def __init__(self, elements: Optional[List[Any]] = None):
        super().__init__("List")
        self._elements = elements or []

    @property
    def elements(self) -> List[Any]:
        return self._elements

    def append(self, element: Any):
        self._elements.append(element)

    def __len__(self):
        return len(self._elements)

    def __getitem__(self, index):
        return self._elements[index]

    def __repr__(self):
        return f"DartList(elements={self._elements})"


# ============================================================
# 垃圾回收器 (Garbage Collector)
# ============================================================
class GarbageCollector:
    """
    垃圾回收器 - 标记-清除算法 (Mark-Sweep GC)

    Dart 使用分代垃圾回收器（Generational GC）。
    本实现简化为单代标记-清除算法。

    工作原理：
    1. 标记（Mark）：从根对象（GC Roots）出发，标记所有可达对象
    2. 清除（Sweep）：清除所有未标记的对象

    GC Roots 包括：
    - 全局变量
    - 当前调用栈中的局部变量
    - 寄存器中的值
    """

    def __init__(self):
        self._objects: List[DartObject] = []
        self._collection_count = 0
        self._total_freed = 0

    def add_object(self, obj: DartObject):
        """VM 分配新对象时调用"""
        obj.clear_mark()
        self._objects.append(obj)

    def remove_object(self, obj: DartObject):
        """显式移除对象"""
        if obj in self._objects:
            self._objects.remove(obj)

    def collect(self) -> int:
        """
        执行一次垃圾回收

        Returns:
            回收的对象数量
        """
        self._collection_count += 1

        # Step 1: 标记阶段 (Mark Phase)
        # 从 GC Roots 开始，标记所有可达对象
        self._mark_phase()

        # Step 2: 清除阶段 (Sweep Phase)
        # 清除未标记的对象
        freed = self._sweep_phase()

        # 清理标记
        for obj in self._objects:
            obj.clear_mark()

        return freed

    def _mark_phase(self):
        """标记阶段：从 GC Roots 标记所有可达对象"""
        # 模拟 GC Roots：全局变量和当前活跃引用
        gc_roots = self._get_gc_roots()

        # 从根对象开始深度优先遍历
        visited = set()
        stack = list(gc_roots)

        while stack:
            obj = stack.pop()
            if obj.id in visited:
                continue
            visited.add(obj.id)
            obj.mark()

            # 追踪对象的所有属性引用
            for key, value in obj._attrs.items():
                if isinstance(value, DartObject) and value.id not in visited:
                    stack.append(value)
                elif isinstance(value, DartList):
                    for elem in value.elements:
                        if isinstance(elem, DartObject) and elem.id not in visited:
                            stack.append(elem)

    def _get_gc_roots(self) -> List[DartObject]:
        """获取 GC Roots（全局变量和活跃引用）"""
        # 简化实现：所有对象都可能是根对象
        # 在实际 VM 中，只有全局变量和栈上引用才是根
        return [obj for obj in self._objects if obj.id % 3 == 0]  # 模拟根对象

    def _sweep_phase(self) -> int:
        """清除阶段：移除未标记的对象"""
        original_count = len(self._objects)
        self._objects = [obj for obj in self._objects if obj.is_marked()]
        freed = original_count - len(self._objects)
        self._total_freed += freed
        return freed

    @property
    def stats(self) -> Dict[str, Any]:
        """GC 统计信息"""
        return {
            "collection_count": self._collection_count,
            "total_freed": self._total_freed,
            "live_objects": len(self._objects),
            "peak_objects": self._collection_count + len(self._objects),
        }


# ============================================================
# Dart VM (虚拟机)
# ============================================================
class DartVM:
    """
    Dart 虚拟机模拟器

    负责：
    1. 编译 Dart 源码为字节码
    2. 执行字节码
    3. 管理内存（通过垃圾回收器）
    4. 提供平台通道接口

    Flutter 架构中的位置：
    +------------------+     +------------------+
    |  Dart 源码       |     |  Platform Layer  |
    +------------------+     +------------------+
           |                        |
           v                        v
    +------------------+     +------------------+
    |  Dart Compiler   |---->|  Platform Channel |
    |  (AOT/JIT)       |     +------------------+
    +------------------+
           |
           v
    +------------------+
    |  Dart VM         |
    |  (Bytecode Exec) |
    +------------------+
    """

    def __init__(self):
        self._gc = GarbageCollector()
        self._globals: Dict[str, Any] = {}
        self._functions: Dict[str, Callable] = {}
        self._bytecode: List[Dict[str, Any]] = []
        self._call_stack: List[Dict[str, Any]] = []
        self._platform_channel: Optional['PlatformChannel'] = None
        self._execution_log: List[str] = []
        self._next_id = 1000  # VM 内部对象 ID 起始值

    def set_platform_channel(self, channel: 'PlatformChannel'):
        """绑定平台通道"""
        self._platform_channel = channel

    def register_function(self, name: str, func: Callable):
        """注册可调用函数到 VM"""
        self._functions[name] = func

    def set_global(self, name: str, value: Any):
        """设置全局变量"""
        self._globals[name] = value
        if isinstance(value, DartObject):
            self._gc.add_object(value)

    def get_global(self, name: str) -> Any:
        """获取全局变量"""
        return self._globals.get(name)

    def compile(self, source_code: str) -> List[Dict[str, Any]]:
        """
        将 Dart 源码编译为字节码

        这是简化的编译器实现，演示了：
        - 词法分析（tokenizer）
        - 字节码生成
        """
        instructions = []
        tokens = self._tokenize(source_code)

        i = 0
        while i < len(tokens):
            token = tokens[i]

            if token == 'def':
                # 函数定义
                i += 1
                func_name = tokens[i]
                self._functions[func_name] = None  # 占位
                instructions.append({'opcode': Opcode.CALL, 'target': func_name})
            elif token == 'return':
                instructions.append({'opcode': Opcode.RETURN})
            elif token in ('True', 'true'):
                instructions.append({'opcode': Opcode.LOAD_CONST, 'value': True})
            elif token in ('False', 'false'):
                instructions.append({'opcode': Opcode.LOAD_CONST, 'value': False})
            elif token.isdigit():
                instructions.append({'opcode': Opcode.LOAD_CONST, 'value': int(token)})
            elif token.startswith("'") and token.endswith("'"):
                instructions.append({'opcode': Opcode.LOAD_CONST, 'value': token[1:-1]})
            elif token == '+':
                instructions.append({'opcode': Opcode.ADD})
            elif token == '-':
                instructions.append({'opcode': Opcode.SUB})
            elif token == '*':
                instructions.append({'opcode': Opcode.MUL})
            elif token == '/':
                instructions.append({'opcode': Opcode.DIV})
            elif token == 'new':
                # 创建对象
                i += 1
                obj_type = tokens[i]
                obj = DartObject(obj_type)
                self._gc.add_object(obj)
                instructions.append({'opcode': Opcode.NEW_OBJECT, 'value': obj})
            elif token == 'new_list':
                lst = DartList()
                self._gc.add_object(lst)
                instructions.append({'opcode': Opcode.NEW_LIST, 'value': lst})
            elif token == 'print':
                instructions.append({'opcode': Opcode.LOAD_GLOBAL, 'value': 'print'})
            elif token == 'channel':
                # 平台通道调用
                i += 1
                method = tokens[i]
                instructions.append({
                    'opcode': Opcode.PLATFORM_CHANNEL_CALL,
                    'method': method
                })
            elif token.startswith('_') and token not in self._functions:
                # 局部变量
                instructions.append({'opcode': Opcode.LOAD_LOCAL, 'value': token})
            else:
                # 尝试作为变量名
                if token in self._globals:
                    instructions.append({'opcode': Opcode.LOAD_GLOBAL, 'value': token})
                elif token in self._functions:
                    instructions.append({'opcode': Opcode.LOAD_GLOBAL, 'value': token})

            i += 1

        self._bytecode = instructions
        return instructions

    def execute(self, bytecode: Optional[List[Dict]] = None) -> List[Any]:
        """
        执行字节码

        模拟 Dart VM 的字节码执行引擎：
        1. 维护操作数栈
        2. 按序执行指令
        3. 处理函数调用和返回
        """
        bc = bytecode or self._bytecode
        if not bc:
            return []

        stack = []
        result = []
        log = []

        i = 0
        while i < len(bc):
            instr = bc[i]
            opcode = instr['opcode']
            log.append(f"  [{i}] {opcode.value}")

            if opcode == Opcode.LOAD_CONST:
                stack.append(instr['value'])

            elif opcode == Opcode.LOAD_GLOBAL:
                name = instr['value']
                val = self._globals.get(name)
                stack.append(val)

            elif opcode == Opcode.LOAD_LOCAL:
                name = instr['value']
                # 从调用栈帧中查找局部变量
                for frame in reversed(self._call_stack):
                    if name in frame.get('locals', {}):
                        stack.append(frame['locals'][name])
                        break
                else:
                    stack.append(None)

            elif opcode == Opcode.ADD:
                b, a = stack.pop(), stack.pop()
                stack.append(a + b)

            elif opcode == Opcode.SUB:
                b, a = stack.pop(), stack.pop()
                stack.append(a - b)

            elif opcode == Opcode.MUL:
                b, a = stack.pop(), stack.pop()
                stack.append(a * b)

            elif opcode == Opcode.DIV:
                b, a = stack.pop(), stack.pop()
                stack.append(a / b if b != 0 else float('inf'))

            elif opcode == Opcode.NEW_OBJECT:
                obj = instr['value']
                stack.append(obj)

            elif opcode == Opcode.NEW_LIST:
                lst = instr['value']
                stack.append(lst)

            elif opcode == Opcode.RETURN:
                if stack:
                    result.append(stack.pop())
                log.append("  [RETURN]")

            elif opcode == Opcode.PLATFORM_CHANNEL_CALL:
                method = instr['method']
                if self._platform_channel:
                    response = self._platform_channel.invoke(method)
                    stack.append(response)
                    log.append(f"  [Channel: {method} -> {response}]")

            i += 1

        self._execution_log = log
        return result

    def trigger_gc(self) -> Dict[str, Any]:
        """触发垃圾回收"""
        freed = self._gc.collect()
        return self._gc.stats

    @property
    def gc_stats(self) -> Dict[str, Any]:
        return self._gc.stats

    @property
    def execution_log(self) -> List[str]:
        return self._execution_log

    def _tokenize(self, source: str) -> List[str]:
        """简化的词法分析器"""
        tokens = []
        current = ''
        in_string = False

        for char in source:
            if char in ("'", '"'):
                in_string = not in_string
                current += char
            elif in_string:
                current += char
            elif char in (' ', '\t', '\n', '\r', '(', ')', ':', ','):
                if current:
                    tokens.append(current)
                    current = ''
            else:
                current += char

        if current:
            tokens.append(current)

        return tokens
