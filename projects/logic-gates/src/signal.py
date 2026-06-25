# 信号定义

"""
数字信号定义模块

本模块定义了数字信号的基本常量和工具函数。
"""


class Signal:
    """数字信号类

    定义了数字电路中的高低电平信号。

    Constants:
        HIGH: 高电平，值为1
        LOW: 低电平，值为0

    Examples:
        >>> Signal.HIGH
        1
        >>> Signal.LOW
        0
        >>> Signal.validate(1)
        1
        >>> Signal.validate(0)
        0
    """

    HIGH = 1  # 高电平
    LOW = 0   # 低电平

    @staticmethod
    def validate(value):
        """验证信号值是否有效

        Args:
            value: 要验证的信号值

        Returns:
            int: 验证后的信号值（0或1）

        Raises:
            InvalidInputError: 如果信号值不是0或1

        Examples:
            >>> Signal.validate(0)
            0
            >>> Signal.validate(1)
            1
            >>> Signal.validate(2)  # doctest: +SKIP
            InvalidInputError: Invalid signal value: 2
        """
        from .exceptions import InvalidInputError

        if value not in (0, 1):
            raise InvalidInputError(f"Invalid signal value: {value}. Must be 0 or 1")
        return value

    @staticmethod
    def from_bool(value):
        """从布尔值转换为信号值

        Args:
            value: 布尔值

        Returns:
            int: 信号值（0或1）

        Examples:
            >>> Signal.from_bool(True)
            1
            >>> Signal.from_bool(False)
            0
        """
        return 1 if value else 0

    @staticmethod
    def to_bool(value):
        """将信号值转换为布尔值

        Args:
            value: 信号值（0或1）

        Returns:
            bool: 布尔值

        Raises:
            InvalidInputError: 如果信号值无效

        Examples:
            >>> Signal.to_bool(1)
        True
            >>> Signal.to_bool(0)
        False
        """
        Signal.validate(value)
        return bool(value)

    @staticmethod
    def negate(value):
        """对信号值取反

        Args:
            value: 信号值（0或1）

        Returns:
            int: 取反后的信号值

        Raises:
            InvalidInputError: 如果信号值无效

        Examples:
            >>> Signal.negate(0)
            1
            >>> Signal.negate(1)
            0
        """
        Signal.validate(value)
        return 1 - value

    @staticmethod
    def format_signal(value, style="binary"):
        """格式化信号值显示

        Args:
            value: 信号值（0或1）
            style: 显示样式（'binary', 'bool', 'logic'）

        Returns:
            str: 格式化后的字符串

        Raises:
            InvalidInputError: 如果信号值无效
            ValueError: 如果样式无效

        Examples:
            >>> Signal.format_signal(1, 'binary')
            '1'
            >>> Signal.format_signal(1, 'bool')
            'True'
            >>> Signal.format_signal(1, 'logic')
            'HIGH'
        """
        Signal.validate(value)

        if style == "binary":
            return str(value)
        elif style == "bool":
            return str(bool(value))
        elif style == "logic":
            return "HIGH" if value else "LOW"
        else:
            raise ValueError(f"Invalid style: {style}. Must be 'binary', 'bool', or 'logic'")

    def __repr__(self):
        return f"Signal(HIGH={self.HIGH}, LOW={self.LOW})"

    def __str__(self):
        return "Digital Signal (0 or 1)"
