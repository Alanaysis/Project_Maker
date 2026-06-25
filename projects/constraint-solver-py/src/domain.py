"""域模块 - 变量取值域管理"""

from __future__ import annotations
from typing import Any, Iterable, Iterator, Optional


class Domain:
    """变量的取值域，用集合实现。

    支持集合的基本操作，用于约束传播中的域缩减。
    """

    def __init__(self, values: Optional[Iterable[Any]] = None) -> None:
        if values is None:
            self._values: set[Any] = set()
        else:
            self._values = set(values)

    @property
    def size(self) -> int:
        """域的大小。"""
        return len(self._values)

    def is_empty(self) -> bool:
        """域是否为空。"""
        return len(self._values) == 0

    def is_singleton(self) -> bool:
        """域是否只包含一个值。"""
        return len(self._values) == 1

    def contains(self, value: Any) -> bool:
        """检查值是否在域中。"""
        return value in self._values

    def add(self, value: Any) -> None:
        """向域中添加值。"""
        self._values.add(value)

    def remove(self, value: Any) -> bool:
        """从域中移除值，返回是否成功。"""
        if value in self._values:
            self._values.discard(value)
            return True
        return False

    def intersect(self, other: Domain) -> Domain:
        """返回两个域的交集。"""
        return Domain(self._values & other._values)

    def union(self, other: Domain) -> Domain:
        """返回两个域的并集。"""
        return Domain(self._values | other._values)

    def difference(self, other: Domain) -> Domain:
        """返回两个域的差集。"""
        return Domain(self._values - other._values)

    def copy(self) -> Domain:
        """创建域的深拷贝。"""
        return Domain(self._values.copy())

    def get_only_value(self) -> Any:
        """获取域中唯一的值 (域大小必须为1)。"""
        if not self.is_singleton():
            raise ValueError(f"域包含 {self.size} 个值，不是单值域")
        return next(iter(self._values))

    def __iter__(self) -> Iterator[Any]:
        return iter(sorted(self._values))

    def __len__(self) -> int:
        return len(self._values)

    def __contains__(self, value: Any) -> bool:
        return value in self._values

    def __bool__(self) -> bool:
        return len(self._values) > 0

    def __repr__(self) -> str:
        values = sorted(self._values)
        if len(values) <= 10:
            return f"Domain({values})"
        return f"Domain({values[:5]}...{values[-5:]}, size={len(values)})"

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Domain):
            return self._values == other._values
        return NotImplemented

    def __hash__(self) -> int:
        return hash(frozenset(self._values))
