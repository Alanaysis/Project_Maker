"""变量模块 - CSP 变量定义"""

from __future__ import annotations
from typing import Any, Optional
from .domain import Domain


class Variable:
    """约束满足问题中的变量。

    Attributes:
        name: 变量名称
        domain: 变量的取值域
        value: 当前赋值 (未赋值时为 None)
    """

    def __init__(self, name: str, domain: Domain) -> None:
        self.name = name
        self.domain = domain
        self.value: Optional[Any] = None
        self._original_domain = domain.copy()

    def is_assigned(self) -> bool:
        """变量是否已赋值。"""
        return self.value is not None

    def assign(self, value: Any) -> None:
        """为变量赋值。"""
        if value not in self._original_domain:
            raise ValueError(
                f"值 {value} 不在变量 {self.name} 的原始域中"
            )
        self.value = value

    def unassign(self) -> None:
        """撤销赋值。"""
        self.value = None

    def reset(self) -> None:
        """重置变量到初始状态。"""
        self.value = None
        self.domain = self._original_domain.copy()

    def copy(self) -> Variable:
        """创建变量的深拷贝。"""
        v = Variable(self.name, self.domain.copy())
        v.value = self.value
        v._original_domain = self._original_domain.copy()
        return v

    def __repr__(self) -> str:
        if self.is_assigned():
            return f"Variable({self.name!r}, value={self.value})"
        return f"Variable({self.name!r}, domain={self.domain})"

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Variable):
            return self.name == other.name
        return NotImplemented

    def __hash__(self) -> int:
        return hash(self.name)
