# 逻辑门注册表

"""
逻辑门注册表模块

本模块提供逻辑门的注册和管理功能。
"""

from typing import Dict, Optional, Type

from .gates import (
    Gate,
    AndGate,
    OrGate,
    NotGate,
    XorGate,
    NandGate,
    NorGate,
    XnorGate,
    Buffer,
    CustomGate,
)
from .exceptions import LogicGateError


class GateRegistry:
    """逻辑门注册表

    用于注册和管理逻辑门类型。

    Examples:
        >>> from logic_gates import GateRegistry
        >>> GateRegistry.list_gates()
        ['AND', 'OR', 'NOT', 'XOR', 'NAND', 'NOR']
        >>> gate = GateRegistry.create("AND")
        >>> gate.evaluate(1, 1)
        1
    """

    _gates: Dict[str, Type[Gate]] = {}
    _instances: Dict[str, Gate] = {}

    @classmethod
    def register(cls, name: str, gate_class: Type[Gate]):
        """注册逻辑门

        Args:
            name: 门名称
            gate_class: 门类

        Raises:
            LogicGateError: 名称已注册

        Examples:
            >>> GateRegistry.register("CUSTOM", CustomGate)
        """
        if name in cls._gates:
            raise LogicGateError(f"Gate '{name}' is already registered")
        cls._gates[name] = gate_class

    @classmethod
    def unregister(cls, name: str):
        """注销逻辑门

        Args:
            name: 门名称

        Examples:
            >>> GateRegistry.unregister("CUSTOM")
        """
        cls._gates.pop(name, None)
        cls._instances.pop(name, None)

    @classmethod
    def get(cls, name: str) -> Optional[Type[Gate]]:
        """获取逻辑门类

        Args:
            name: 门名称

        Returns:
            Optional[Type[Gate]]: 门类，如果不存在返回None

        Examples:
            >>> gate_class = GateRegistry.get("AND")
            >>> gate_class == AndGate
            True
        """
        return cls._gates.get(name)

    @classmethod
    def create(cls, name: str, *args, **kwargs) -> Gate:
        """创建逻辑门实例

        Args:
            name: 门名称
            *args, **kwargs: 传递给门构造函数的参数

        Returns:
            Gate: 门实例

        Raises:
            ValueError: 门类型不存在

        Examples:
            >>> gate = GateRegistry.create("AND")
            >>> gate.evaluate(1, 1)
            1
        """
        gate_class = cls.get(name)
        if gate_class is None:
            raise ValueError(f"Unknown gate type: {name}")
        return gate_class(*args, **kwargs)

    @classmethod
    def get_or_create(cls, name: str) -> Gate:
        """获取或创建单例门实例

        Args:
            name: 门名称

        Returns:
            Gate: 门实例

        Examples:
            >>> gate1 = GateRegistry.get_or_create("AND")
            >>> gate2 = GateRegistry.get_or_create("AND")
            >>> gate1 is gate2
            True
        """
        if name not in cls._instances:
            cls._instances[name] = cls.create(name)
        return cls._instances[name]

    @classmethod
    def list_gates(cls) -> list:
        """列出所有注册的门类型

        Returns:
            list: 门名称列表

        Examples:
            >>> gates = GateRegistry.list_gates()
            >>> "AND" in gates
            True
        """
        return list(cls._gates.keys())

    @classmethod
    def has(cls, name: str) -> bool:
        """检查门是否已注册

        Args:
            name: 门名称

        Returns:
            bool: 是否已注册

        Examples:
            >>> GateRegistry.has("AND")
            True
            >>> GateRegistry.has("UNKNOWN")
            False
        """
        return name in cls._gates

    @classmethod
    def clear(cls):
        """清除所有注册

        Examples:
            >>> GateRegistry.clear()
            >>> GateRegistry.list_gates()
            []
        """
        cls._gates.clear()
        cls._instances.clear()

    @classmethod
    def reset(cls):
        """重置为默认状态

        Examples:
            >>> GateRegistry.reset()
            >>> GateRegistry.list_gates()
            ['AND', 'OR', 'NOT', 'XOR', 'NAND', 'NOR']
        """
        cls.clear()
        register_default_gates()


def register_default_gates():
    """注册默认逻辑门

    注册所有内置的逻辑门类型。

    Examples:
        >>> register_default_gates()
        >>> 'AND' in GateRegistry.list_gates()
        True
    """
    GateRegistry.register("AND", AndGate)
    GateRegistry.register("OR", OrGate)
    GateRegistry.register("NOT", NotGate)
    GateRegistry.register("XOR", XorGate)
    GateRegistry.register("NAND", NandGate)
    GateRegistry.register("NOR", NorGate)
    GateRegistry.register("XNOR", XnorGate)
    GateRegistry.register("BUF", Buffer)


# 初始化时注册默认门
register_default_gates()
