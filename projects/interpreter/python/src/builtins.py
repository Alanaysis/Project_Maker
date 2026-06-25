"""
内置函数

提供语言内置的标准函数。
包括：
- 类型转换：str, number, bool, type
- 字符串操作：len, upper, lower, trim, split, join, replace, contains, starts_with, ends_with
- 数组操作：push, pop, sort, reverse, range, map, filter, reduce
- 数学函数：abs, sqrt, floor, ceil, round, min, max
- 输出：print, println
- 输入：input
"""

import math
from .objects import (
    Obj, Number, String, Boolean, Null, Array, Map,
    BuiltinFunction, NULL, TRUE, FALSE,
)


class BuiltinError(Exception):
    """内置函数错误"""
    pass


def _check_args(name: str, args: list[Obj], expected: int):
    """检查参数数量"""
    if len(args) != expected:
        raise BuiltinError(f"{name}() 需要 {expected} 个参数，得到 {len(args)} 个")


def _check_args_range(name: str, args: list[Obj], min_args: int, max_args: int):
    """检查参数数量范围"""
    if len(args) < min_args or len(args) > max_args:
        raise BuiltinError(
            f"{name}() 需要 {min_args}-{max_args} 个参数，得到 {len(args)} 个"
        )


def _expect_number(name: str, arg: Obj, pos: int = 1) -> float:
    """期望参数为数字"""
    if not isinstance(arg, Number):
        raise BuiltinError(f"{name}() 的第 {pos} 个参数必须是数字，得到 {arg.type().name}")
    return arg.value


def _expect_string(name: str, arg: Obj, pos: int = 1) -> str:
    """期望参数为字符串"""
    if not isinstance(arg, String):
        raise BuiltinError(f"{name}() 的第 {pos} 个参数必须是字符串，得到 {arg.type().name}")
    return arg.value


def _expect_array(name: str, arg: Obj, pos: int = 1) -> list[Obj]:
    """期望参数为数组"""
    if not isinstance(arg, Array):
        raise BuiltinError(f"{name}() 的第 {pos} 个参数必须是数组，得到 {arg.type().name}")
    return arg.elements


# ============================================================
# 输出函数
# ============================================================

def builtin_print(*args: Obj) -> Obj:
    """print(value, ...) - 输出值（不换行）"""
    parts = []
    for arg in args:
        if isinstance(arg, String):
            parts.append(arg.value)
        else:
            parts.append(arg.inspect())
    print(" ".join(parts), end="")
    return NULL


def builtin_println(*args: Obj) -> Obj:
    """println(value, ...) - 输出值并换行"""
    parts = []
    for arg in args:
        if isinstance(arg, String):
            parts.append(arg.value)
        else:
            parts.append(arg.inspect())
    print(" ".join(parts))
    return NULL


def builtin_input(*args: Obj) -> Obj:
    """input(prompt?) - 读取用户输入"""
    if args:
        prompt = _expect_string("input", args[0])
        return String(input(prompt))
    return String(input())


# ============================================================
# 类型转换
# ============================================================

def builtin_str(*args: Obj) -> Obj:
    """str(value) - 转换为字符串"""
    _check_args("str", args, 1)
    if isinstance(args[0], String):
        return args[0]
    if isinstance(args[0], Number):
        v = args[0].value
        if v == int(v):
            return String(str(int(v)))
    return String(args[0].inspect())


def builtin_number(*args: Obj) -> Obj:
    """number(value) - 转换为数字"""
    _check_args("number", args, 1)
    if isinstance(args[0], Number):
        return args[0]
    if isinstance(args[0], String):
        try:
            return Number(float(args[0].value))
        except ValueError:
            raise BuiltinError(f"无法将 '{args[0].value}' 转换为数字")
    if isinstance(args[0], Boolean):
        return Number(1.0 if args[0].value else 0.0)
    raise BuiltinError(f"无法将 {args[0].type().name} 转换为数字")


def builtin_bool(*args: Obj) -> Obj:
    """bool(value) - 转换为布尔值"""
    _check_args("bool", args, 1)
    return TRUE if args[0].is_truthy() else FALSE


def builtin_type(*args: Obj) -> Obj:
    """type(value) - 返回值的类型名"""
    _check_args("type", args, 1)
    type_names = {
        "NUMBER": "number",
        "STRING": "string",
        "BOOLEAN": "boolean",
        "NULL": "null",
        "ARRAY": "array",
        "MAP": "map",
        "FUNCTION": "function",
        "BUILTIN": "builtin",
    }
    return String(type_names.get(args[0].type().name, "unknown"))


# ============================================================
# 字符串函数
# ============================================================

def builtin_len(*args: Obj) -> Obj:
    """len(value) - 返回字符串/数组/映射的长度"""
    _check_args("len", args, 1)
    arg = args[0]
    if isinstance(arg, String):
        return Number(float(len(arg.value)))
    if isinstance(arg, Array):
        return Number(float(len(arg.elements)))
    if isinstance(arg, Map):
        return Number(float(len(arg.pairs)))
    raise BuiltinError(f"len() 不支持 {arg.type().name} 类型")


def builtin_upper(*args: Obj) -> Obj:
    """upper(str) - 转换为大写"""
    _check_args("upper", args, 1)
    return String(_expect_string("upper", args[0]).upper())


def builtin_lower(*args: Obj) -> Obj:
    """lower(str) - 转换为小写"""
    _check_args("lower", args, 1)
    return String(_expect_string("lower", args[0]).lower())


def builtin_trim(*args: Obj) -> Obj:
    """trim(str) - 去除首尾空白"""
    _check_args("trim", args, 1)
    return String(_expect_string("trim", args[0]).strip())


def builtin_split(*args: Obj) -> Obj:
    """split(str, separator) - 分割字符串"""
    _check_args("split", args, 2)
    s = _expect_string("split", args[0])
    sep = _expect_string("split", args[1], 2)
    parts = s.split(sep)
    return Array([String(p) for p in parts])


def builtin_join(*args: Obj) -> Obj:
    """join(array, separator) - 连接数组元素"""
    _check_args("join", args, 2)
    arr = _expect_array("join", args[0])
    sep = _expect_string("join", args[1], 2)
    parts = []
    for elem in arr:
        if isinstance(elem, String):
            parts.append(elem.value)
        else:
            parts.append(elem.inspect())
    return String(sep.join(parts))


def builtin_replace(*args: Obj) -> Obj:
    """replace(str, old, new) - 替换字符串"""
    _check_args("replace", args, 3)
    s = _expect_string("replace", args[0])
    old = _expect_string("replace", args[1], 2)
    new = _expect_string("replace", args[2], 3)
    return String(s.replace(old, new))


def builtin_contains(*args: Obj) -> Obj:
    """contains(str, substr) - 检查是否包含子串"""
    _check_args("contains", args, 2)
    s = _expect_string("contains", args[0])
    sub = _expect_string("contains", args[1], 2)
    return TRUE if sub in s else FALSE


def builtin_starts_with(*args: Obj) -> Obj:
    """starts_with(str, prefix) - 检查是否以指定前缀开头"""
    _check_args("starts_with", args, 2)
    s = _expect_string("starts_with", args[0])
    prefix = _expect_string("starts_with", args[1], 2)
    return TRUE if s.startswith(prefix) else FALSE


def builtin_ends_with(*args: Obj) -> Obj:
    """ends_with(str, suffix) - 检查是否以指定后缀结尾"""
    _check_args("ends_with", args, 2)
    s = _expect_string("ends_with", args[0])
    suffix = _expect_string("ends_with", args[1], 2)
    return TRUE if s.endswith(suffix) else FALSE


# ============================================================
# 数组函数
# ============================================================

def builtin_push(*args: Obj) -> Obj:
    """push(array, value) - 向数组末尾添加元素"""
    _check_args("push", args, 2)
    arr = _expect_array("push", args[0])
    arr.append(args[1])
    return Array(arr)


def builtin_pop(*args: Obj) -> Obj:
    """pop(array) - 移除并返回数组末尾元素"""
    _check_args("pop", args, 1)
    arr = _expect_array("pop", args[0])
    if not arr:
        raise BuiltinError("pop() 不能操作空数组")
    return arr.pop()


def builtin_sort(*args: Obj) -> Obj:
    """sort(array) - 排序数组"""
    _check_args("sort", args, 1)
    arr = _expect_array("sort", args[0])
    # 只对数字和字符串排序
    sorted_arr = sorted(arr, key=lambda x: (
        x.value if isinstance(x, (Number, String)) else str(x.inspect())
    ))
    return Array(sorted_arr)


def builtin_reverse(*args: Obj) -> Obj:
    """reverse(array) - 反转数组"""
    _check_args("reverse", args, 1)
    arr = _expect_array("reverse", args[0])
    return Array(list(reversed(arr)))


def builtin_range(*args: Obj) -> Obj:
    """range(start?, end, step?) - 生成数字数组"""
    _check_args_range("range", args, 1, 3)

    if len(args) == 1:
        end = int(_expect_number("range", args[0]))
        return Array([Number(float(i)) for i in range(end)])
    elif len(args) == 2:
        start = int(_expect_number("range", args[0]))
        end = int(_expect_number("range", args[1], 2))
        return Array([Number(float(i)) for i in range(start, end)])
    else:
        start = int(_expect_number("range", args[0]))
        end = int(_expect_number("range", args[1], 2))
        step = int(_expect_number("range", args[2], 3))
        return Array([Number(float(i)) for i in range(start, end, step)])


# ============================================================
# 数学函数
# ============================================================

def builtin_abs(*args: Obj) -> Obj:
    """abs(number) - 绝对值"""
    _check_args("abs", args, 1)
    return Number(abs(_expect_number("abs", args[0])))


def builtin_sqrt(*args: Obj) -> Obj:
    """sqrt(number) - 平方根"""
    _check_args("sqrt", args, 1)
    v = _expect_number("sqrt", args[0])
    if v < 0:
        raise BuiltinError("sqrt() 不能对负数求平方根")
    return Number(math.sqrt(v))


def builtin_floor(*args: Obj) -> Obj:
    """floor(number) - 向下取整"""
    _check_args("floor", args, 1)
    return Number(math.floor(_expect_number("floor", args[0])))


def builtin_ceil(*args: Obj) -> Obj:
    """ceil(number) - 向上取整"""
    _check_args("ceil", args, 1)
    return Number(math.ceil(_expect_number("ceil", args[0])))


def builtin_round(*args: Obj) -> Obj:
    """round(number, digits?) - 四舍五入"""
    _check_args_range("round", args, 1, 2)
    v = _expect_number("round", args[0])
    digits = int(_expect_number("round", args[1], 2)) if len(args) > 1 else 0
    return Number(round(v, digits))


def builtin_min(*args: Obj) -> Obj:
    """min(a, b) - 返回较小值"""
    _check_args("min", args, 2)
    a = _expect_number("min", args[0])
    b = _expect_number("min", args[1], 2)
    return Number(min(a, b))


def builtin_max(*args: Obj) -> Obj:
    """max(a, b) - 返回较大值"""
    _check_args("max", args, 2)
    a = _expect_number("max", args[0])
    b = _expect_number("max", args[1], 2)
    return Number(max(a, b))


# ============================================================
# 内置函数注册表
# ============================================================

BUILTINS: dict[str, BuiltinFunction] = {
    # 输出
    "print": BuiltinFunction("print", builtin_print),
    "println": BuiltinFunction("println", builtin_println),
    "input": BuiltinFunction("input", builtin_input),

    # 类型转换
    "str": BuiltinFunction("str", builtin_str),
    "number": BuiltinFunction("number", builtin_number),
    "bool": BuiltinFunction("bool", builtin_bool),
    "type": BuiltinFunction("type", builtin_type),

    # 字符串
    "len": BuiltinFunction("len", builtin_len),
    "upper": BuiltinFunction("upper", builtin_upper),
    "lower": BuiltinFunction("lower", builtin_lower),
    "trim": BuiltinFunction("trim", builtin_trim),
    "split": BuiltinFunction("split", builtin_split),
    "join": BuiltinFunction("join", builtin_join),
    "replace": BuiltinFunction("replace", builtin_replace),
    "contains": BuiltinFunction("contains", builtin_contains),
    "starts_with": BuiltinFunction("starts_with", builtin_starts_with),
    "ends_with": BuiltinFunction("ends_with", builtin_ends_with),

    # 数组
    "push": BuiltinFunction("push", builtin_push),
    "pop": BuiltinFunction("pop", builtin_pop),
    "sort": BuiltinFunction("sort", builtin_sort),
    "reverse": BuiltinFunction("reverse", builtin_reverse),
    "range": BuiltinFunction("range", builtin_range),

    # 数学
    "abs": BuiltinFunction("abs", builtin_abs),
    "sqrt": BuiltinFunction("sqrt", builtin_sqrt),
    "floor": BuiltinFunction("floor", builtin_floor),
    "ceil": BuiltinFunction("ceil", builtin_ceil),
    "round": BuiltinFunction("round", builtin_round),
    "min": BuiltinFunction("min", builtin_min),
    "max": BuiltinFunction("max", builtin_max),
}
