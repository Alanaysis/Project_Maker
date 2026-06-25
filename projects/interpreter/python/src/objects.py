"""
运行时对象定义

定义解释器运行时的所有值类型。
每种值类型都有统一的接口，支持类型检查和转换。
"""

from dataclasses import dataclass, field
from abc import ABC, abstractmethod
from enum import Enum, auto
from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from .ast_nodes import Identifier, BlockStatement
    from .environment import Environment


class ObjectType(Enum):
    """对象类型枚举"""
    NUMBER = auto()
    STRING = auto()
    BOOLEAN = auto()
    NULL = auto()
    ARRAY = auto()
    MAP = auto()
    FUNCTION = auto()
    BUILTIN = auto()
    RETURN_VALUE = auto()
    BREAK_SIGNAL = auto()
    CONTINUE_SIGNAL = auto()


class Obj(ABC):
    """运行时对象基类"""

    @abstractmethod
    def type(self) -> ObjectType:
        pass

    @abstractmethod
    def inspect(self) -> str:
        """返回对象的可读字符串表示"""
        pass

    def is_truthy(self) -> bool:
        """返回对象的布尔值"""
        return True

    def __repr__(self) -> str:
        return self.inspect()


@dataclass
class Number(Obj):
    """数字对象"""
    value: float

    def type(self) -> ObjectType:
        return ObjectType.NUMBER

    def inspect(self) -> str:
        if self.value == int(self.value):
            return str(int(self.value))
        return str(self.value)

    def is_truthy(self) -> bool:
        return self.value != 0

    def __eq__(self, other):
        if isinstance(other, Number):
            return self.value == other.value
        return False

    def __hash__(self):
        return hash(self.value)


@dataclass
class String(Obj):
    """字符串对象"""
    value: str

    def type(self) -> ObjectType:
        return ObjectType.STRING

    def inspect(self) -> str:
        return self.value

    def is_truthy(self) -> bool:
        return len(self.value) > 0

    def __eq__(self, other):
        if isinstance(other, String):
            return self.value == other.value
        return False

    def __hash__(self):
        return hash(self.value)


@dataclass
class Boolean(Obj):
    """布尔对象"""
    value: bool

    def type(self) -> ObjectType:
        return ObjectType.BOOLEAN

    def inspect(self) -> str:
        return str(self.value).lower()

    def is_truthy(self) -> bool:
        return self.value

    def __eq__(self, other):
        if isinstance(other, Boolean):
            return self.value == other.value
        return False

    def __hash__(self):
        return hash(self.value)


@dataclass
class Null(Obj):
    """null对象"""
    _instance = None

    def type(self) -> ObjectType:
        return ObjectType.NULL

    def inspect(self) -> str:
        return "null"

    def is_truthy(self) -> bool:
        return False

    def __eq__(self, other):
        return isinstance(other, Null)

    def __hash__(self):
        return hash(None)


@dataclass
class Array(Obj):
    """数组对象"""
    elements: list[Obj] = field(default_factory=list)

    def type(self) -> ObjectType:
        return ObjectType.ARRAY

    def inspect(self) -> str:
        elems = ", ".join(e.inspect() for e in self.elements)
        return f"[{elems}]"

    def is_truthy(self) -> bool:
        return len(self.elements) > 0

    def __eq__(self, other):
        if isinstance(other, Array):
            return self.elements == other.elements
        return False

    def __hash__(self):
        return id(self)


@dataclass
class Map(Obj):
    """映射对象"""
    pairs: dict[str, Obj] = field(default_factory=dict)

    def type(self) -> ObjectType:
        return ObjectType.MAP

    def inspect(self) -> str:
        items = ", ".join(f'"{k}": {v.inspect()}' for k, v in self.pairs.items())
        return f"{{{items}}}"

    def is_truthy(self) -> bool:
        return len(self.pairs) > 0

    def __eq__(self, other):
        if isinstance(other, Map):
            return self.pairs == other.pairs
        return False

    def __hash__(self):
        return id(self)


@dataclass
class Function(Obj):
    """函数对象"""
    parameters: list["Identifier"]
    body: "BlockStatement"
    env: "Environment"
    name: str = ""

    def type(self) -> ObjectType:
        return ObjectType.FUNCTION

    def inspect(self) -> str:
        params = ", ".join(p.value for p in self.parameters)
        name = self.name if self.name else "<lambda>"
        return f"fn {name}({params}) {{ ... }}"

    def is_truthy(self) -> bool:
        return True

    def __eq__(self, other):
        return self is other

    def __hash__(self):
        return id(self)


class BuiltinFunction(Obj):
    """内置函数对象"""

    def __init__(self, name: str, fn: Any):
        self._name = name
        self._fn = fn

    def type(self) -> ObjectType:
        return ObjectType.BUILTIN

    def inspect(self) -> str:
        return f"builtin({self._name})"

    def is_truthy(self) -> bool:
        return True

    def __call__(self, *args: Obj) -> Obj:
        return self._fn(*args)

    def __eq__(self, other):
        return self is other

    def __hash__(self):
        return id(self)


@dataclass
class ReturnValue(Obj):
    """return值包装器（用于实现return语句）"""
    value: Obj

    def type(self) -> ObjectType:
        return ObjectType.RETURN_VALUE

    def inspect(self) -> str:
        return self.value.inspect()

    def is_truthy(self) -> bool:
        return self.value.is_truthy()

    def __eq__(self, other):
        if isinstance(other, ReturnValue):
            return self.value == other.value
        return False

    def __hash__(self):
        return hash(self.value)


@dataclass
class BreakSignal(Obj):
    """break信号（用于实现break语句）"""

    def type(self) -> ObjectType:
        return ObjectType.BREAK_SIGNAL

    def inspect(self) -> str:
        return "break"

    def is_truthy(self) -> bool:
        return False

    def __eq__(self, other):
        return isinstance(other, BreakSignal)

    def __hash__(self):
        return hash("break")


@dataclass
class ContinueSignal(Obj):
    """continue信号（用于实现continue语句）"""

    def type(self) -> ObjectType:
        return ObjectType.CONTINUE_SIGNAL

    def inspect(self) -> str:
        return "continue"

    def is_truthy(self) -> bool:
        return False

    def __eq__(self, other):
        return isinstance(other, ContinueSignal)

    def __hash__(self):
        return hash("continue")


# 单例
TRUE = Boolean(True)
FALSE = Boolean(False)
NULL = Null()
BREAK = BreakSignal()
CONTINUE = ContinueSignal()
