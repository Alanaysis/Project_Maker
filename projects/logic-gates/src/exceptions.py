# 异常定义

"""
逻辑门模拟器的异常类定义

本模块定义了所有自定义异常类，用于处理各种错误情况。
"""


class LogicGateError(Exception):
    """逻辑门基础异常

    所有逻辑门相关异常的基类。

    Examples:
        >>> try:
        ...     raise LogicGateError("Something went wrong")
        ... except LogicGateError as e:
        ...     print(e)
        Something went wrong
    """

    def __init__(self, message="Logic gate error"):
        self.message = message
        super().__init__(self.message)


class InvalidInputError(LogicGateError):
    """无效输入异常

    当输入信号无效时抛出（不是0或1）。

    Examples:
        >>> try:
        ...     raise InvalidInputError("Invalid signal: 2")
        ... except InvalidInputError as e:
        ...     print(e)
        Invalid signal: 2
    """

    def __init__(self, message="Invalid input signal"):
        super().__init__(message)


class ConnectionError(LogicGateError):
    """连接错误异常

    当连接无效时抛出。

    Examples:
        >>> try:
        ...     raise ConnectionError("Gate not found")
        ... except ConnectionError as e:
        ...     print(e)
        Gate not found
    """

    def __init__(self, message="Invalid connection"):
        super().__init__(message)


class CircuitError(LogicGateError):
    """电路错误异常

    当电路配置或执行错误时抛出。

    Examples:
        >>> try:
        ...     raise CircuitError("Circuit contains a cycle")
        ... except CircuitError as e:
        ...     print(e)
        Circuit contains a cycle
    """

    def __init__(self, message="Circuit error"):
        super().__init__(message)
