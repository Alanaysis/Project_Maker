"""
环境管理（Environment）

管理变量的作用域和生命周期。
使用作用域链实现词法作用域和闭包。

环境链：
  inner -> outer -> outer -> ... -> global

每个环境存储当前作用域的变量。
查找变量时，沿作用域链向上查找。
闭包通过捕获创建时的环境来实现。
"""

from .objects import Obj


class EnvironmentError(Exception):
    """环境错误"""
    pass


class Environment:
    """
    变量环境

    管理变量的存储和查找。
    支持嵌套作用域（通过outer链）。

    Attributes:
        store: 当前作用域的变量存储
        outer: 外层环境引用（作用域链）
    """

    def __init__(self, outer: "Environment | None" = None):
        self.store: dict[str, Obj] = {}
        self.outer = outer

    def get(self, name: str) -> Obj:
        """
        获取变量值

        先在当前作用域查找，找不到则沿作用域链向上查找。
        如果所有作用域都找不到，抛出异常。

        Args:
            name: 变量名

        Returns:
            变量值

        Raises:
            EnvironmentError: 变量未定义
        """
        obj = self.store.get(name)
        if obj is not None:
            return obj
        if self.outer is not None:
            return self.outer.get(name)
        raise EnvironmentError(f"未定义的变量: '{name}'")

    def set(self, name: str, value: Obj) -> Obj:
        """
        设置变量值（在当前作用域）

        Args:
            name: 变量名
            value: 变量值

        Returns:
            设置的值
        """
        self.store[name] = value
        return value

    def assign(self, name: str, value: Obj) -> Obj:
        """
        更新变量值（沿作用域链查找并更新）

        如果变量在当前作用域存在，更新它。
        否则沿作用域链查找并更新。
        如果找不到，抛出异常。

        Args:
            name: 变量名
            value: 新值

        Returns:
            更新后的值

        Raises:
            EnvironmentError: 变量未定义
        """
        if name in self.store:
            self.store[name] = value
            return value
        if self.outer is not None:
            return self.outer.assign(name, value)
        raise EnvironmentError(f"未定义的变量: '{name}'")

    def has(self, name: str) -> bool:
        """检查变量是否存在于当前作用域"""
        return name in self.store

    def has_in_chain(self, name: str) -> bool:
        """检查变量是否存在于整个作用域链中"""
        if name in self.store:
            return True
        if self.outer is not None:
            return self.outer.has_in_chain(name)
        return False

    def keys(self) -> list[str]:
        """返回当前作用域的所有变量名"""
        return list(self.store.keys())

    def all_keys(self) -> list[str]:
        """返回整个作用域链的所有变量名"""
        keys = set(self.store.keys())
        if self.outer is not None:
            keys.update(self.outer.all_keys())
        return sorted(keys)

    def create_child(self) -> "Environment":
        """创建子环境（进入新的作用域）"""
        return Environment(outer=self)

    def __repr__(self) -> str:
        names = ", ".join(self.store.keys())
        return f"Environment({names})"
