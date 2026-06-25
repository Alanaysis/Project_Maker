"""
解释器/求值器（Interpreter）

遍历AST并执行，实现语言的核心执行逻辑。
使用递归求值，每个AST节点类型对应一个求值方法。

执行流程：
1. 接收AST（Program节点）
2. 递归遍历每个节点
3. 根据节点类型调用对应的求值方法
4. 返回执行结果
"""

from .ast_nodes import (
    Program, Statement, Expression,
    LetStatement, ReturnStatement, ExpressionStatement,
    BlockStatement, IfStatement, WhileStatement, ForStatement,
    BreakStatement, ContinueStatement,
    NumberLiteral, StringLiteral, BooleanLiteral, NullLiteral,
    ArrayLiteral, MapLiteral, Identifier,
    PrefixExpression, InfixExpression, AssignExpression,
    CallExpression, IndexExpression, FunctionLiteral,
)
from .objects import (
    Obj, Number, String, Boolean, Null, Array, Map,
    Function, BuiltinFunction, ReturnValue,
    BreakSignal, ContinueSignal,
    NULL, TRUE, FALSE, BREAK, CONTINUE,
)
from .environment import Environment
from .builtins import BUILTINS, BuiltinError


class RuntimeError(Exception):
    """运行时错误"""

    def __init__(self, message: str, line: int = 0):
        super().__init__(f"[行 {line}] 运行时错误: {message}")
        self.line = line


class Interpreter:
    """
    解释器

    遍历AST并执行，支持：
    - 变量声明和赋值
    - 算术和逻辑运算
    - 控制流（if/elif/else, while, for）
    - 函数定义和调用
    - 闭包
    - 内置函数
    """

    def __init__(self):
        self.global_env = Environment()
        self._register_builtins()

    def _register_builtins(self):
        """注册内置函数到全局环境"""
        for name, builtin in BUILTINS.items():
            self.global_env.set(name, builtin)

    def run(self, source: str) -> Obj:
        """
        执行源代码

        Args:
            source: 源代码字符串

        Returns:
            执行结果

        Raises:
            RuntimeError: 运行时错误
        """
        from .parser import Parser
        parser = Parser(source)
        program = parser.parse()
        return self.eval(program)

    def eval(self, node: Statement | Expression) -> Obj:
        """
        求值AST节点

        根据节点类型分派到对应的求值方法。

        Args:
            node: AST节点

        Returns:
            求值结果
        """
        match type(node).__name__:
            # 程序
            case "Program":
                return self._eval_program(node)
            # 语句
            case "LetStatement":
                return self._eval_let_statement(node)
            case "ReturnStatement":
                return self._eval_return_statement(node)
            case "ExpressionStatement":
                return self._eval_expression_statement(node)
            case "BlockStatement":
                return self._eval_block_statement(node)
            case "IfStatement":
                return self._eval_if_statement(node)
            case "WhileStatement":
                return self._eval_while_statement(node)
            case "ForStatement":
                return self._eval_for_statement(node)
            case "BreakStatement":
                return BREAK
            case "ContinueStatement":
                return CONTINUE
            # 表达式
            case "NumberLiteral":
                return Number(node.value)
            case "StringLiteral":
                return String(node.value)
            case "BooleanLiteral":
                return TRUE if node.value else FALSE
            case "NullLiteral":
                return NULL
            case "ArrayLiteral":
                return self._eval_array_literal(node)
            case "MapLiteral":
                return self._eval_map_literal(node)
            case "Identifier":
                return self._eval_identifier(node)
            case "PrefixExpression":
                return self._eval_prefix_expression(node)
            case "InfixExpression":
                return self._eval_infix_expression(node)
            case "AssignExpression":
                return self._eval_assign_expression(node)
            case "CallExpression":
                return self._eval_call_expression(node)
            case "IndexExpression":
                return self._eval_index_expression(node)
            case "FunctionLiteral":
                return self._eval_function_literal(node)
            case _:
                raise RuntimeError(f"未知的节点类型: {type(node).__name__}")

    # ============================================================
    # 程序和语句求值
    # ============================================================

    def _eval_program(self, program: Program) -> Obj:
        """求值整个程序"""
        result: Obj = NULL
        for stmt in program.statements:
            result = self.eval(stmt)
            # 如果遇到return/break/continue信号，直接返回
            if isinstance(result, (ReturnValue, BreakSignal, ContinueSignal)):
                return result
        return result

    def _eval_let_statement(self, stmt: LetStatement) -> Obj:
        """求值变量声明"""
        value = self.eval(stmt.value)
        self.global_env.set(stmt.name.value, value)
        return NULL

    def _eval_return_statement(self, stmt: ReturnStatement) -> ReturnValue:
        """求值return语句"""
        value = self.eval(stmt.value) if stmt.value else NULL
        return ReturnValue(value)

    def _eval_expression_statement(self, stmt: ExpressionStatement) -> Obj:
        """求值表达式语句"""
        return self.eval(stmt.expression)

    def _eval_block_statement(self, block: BlockStatement, env: Environment | None = None) -> Obj:
        """
        求值代码块

        Args:
            block: 代码块节点
            env: 可选的环境（用于函数调用）

        Returns:
            代码块的执行结果
        """
        result: Obj = NULL
        for stmt in block.statements:
            result = self.eval(stmt)
            if isinstance(result, (ReturnValue, BreakSignal, ContinueSignal)):
                return result
        return result

    def _eval_if_statement(self, stmt: IfStatement) -> Obj:
        """求值if语句"""
        condition = self.eval(stmt.condition)
        if condition.is_truthy():
            return self._eval_block_statement(stmt.consequence)

        for elif_cond, elif_body in stmt.elifs:
            if self.eval(elif_cond).is_truthy():
                return self._eval_block_statement(elif_body)

        if stmt.alternative:
            return self._eval_block_statement(stmt.alternative)

        return NULL

    def _eval_while_statement(self, stmt: WhileStatement) -> Obj:
        """求值while循环"""
        result: Obj = NULL
        while self.eval(stmt.condition).is_truthy():
            result = self._eval_block_statement(stmt.body)
            if isinstance(result, ReturnValue):
                return result
            if isinstance(result, BreakSignal):
                break
            # ContinueSignal 继续循环
        return NULL

    def _eval_for_statement(self, stmt: ForStatement) -> Obj:
        """求值for循环"""
        iterable = self.eval(stmt.iterable)
        result: Obj = NULL

        elements: list[Obj] = []
        if isinstance(iterable, Array):
            elements = iterable.elements
        elif isinstance(iterable, String):
            elements = [String(c) for c in iterable.value]
        elif isinstance(iterable, Map):
            elements = [String(k) for k in iterable.pairs.keys()]
        else:
            raise RuntimeError(f"for循环不支持 {iterable.type().name} 类型", stmt.line)

        for elem in elements:
            self.global_env.set(stmt.var_name.value, elem)
            result = self._eval_block_statement(stmt.body)
            if isinstance(result, ReturnValue):
                return result
            if isinstance(result, BreakSignal):
                break
            # ContinueSignal 继续循环

        return NULL

    # ============================================================
    # 表达式求值
    # ============================================================

    def _eval_array_literal(self, node: ArrayLiteral) -> Array:
        """求值数组字面量"""
        elements = [self.eval(elem) for elem in node.elements]
        return Array(elements)

    def _eval_map_literal(self, node: MapLiteral) -> Map:
        """求值映射字面量"""
        pairs: dict[str, Obj] = {}
        for key_node, value_node in node.pairs:
            key = self.eval(key_node)
            if not isinstance(key, String):
                raise RuntimeError("映射的键必须是字符串", node.line)
            value = self.eval(value_node)
            pairs[key.value] = value
        return Map(pairs)

    def _eval_identifier(self, node: Identifier) -> Obj:
        """求值标识符（变量查找）"""
        try:
            return self.global_env.get(node.value)
        except Exception:
            raise RuntimeError(f"未定义的变量: '{node.value}'", node.line)

    def _eval_prefix_expression(self, node: PrefixExpression) -> Obj:
        """求值前缀表达式"""
        right = self.eval(node.right)
        match node.operator:
            case "-":
                if isinstance(right, Number):
                    return Number(-right.value)
                raise RuntimeError(f"不能对 {right.type().name} 取负", node.line)
            case "!" | "not":
                if right.is_truthy():
                    return FALSE
                return TRUE
            case _:
                raise RuntimeError(f"未知的前缀运算符: {node.operator}", node.line)

    def _eval_infix_expression(self, node: InfixExpression) -> Obj:
        """求值中缀表达式"""
        left = self.eval(node.left)
        op = node.operator

        # 短路求值（在求值right之前检查）
        if op == "and":
            if not left.is_truthy():
                return left
            return self.eval(node.right)
        if op == "or":
            if left.is_truthy():
                return left
            return self.eval(node.right)

        right = self.eval(node.right)

        # 数字运算
        if isinstance(left, Number) and isinstance(right, Number):
            return self._eval_number_infix(op, left, right, node.line)

        # 字符串运算
        if isinstance(left, String) and isinstance(right, String):
            return self._eval_string_infix(op, left, right, node.line)

        # 数组运算
        if isinstance(left, Array) and isinstance(right, Array):
            if op == "+":
                return Array(left.elements + right.elements)

        # 相等性比较（跨类型）
        if op == "==":
            return TRUE if left == right else FALSE
        if op == "!=":
            return TRUE if left != right else FALSE

        raise RuntimeError(
            f"类型不匹配: {left.type().name} {op} {right.type().name}",
            node.line
        )

    def _eval_number_infix(self, op: str, left: Number, right: Number, line: int) -> Obj:
        """数字中缀运算"""
        match op:
            case "+":
                return Number(left.value + right.value)
            case "-":
                return Number(left.value - right.value)
            case "*":
                return Number(left.value * right.value)
            case "/":
                if right.value == 0:
                    raise RuntimeError("除以零", line)
                return Number(left.value / right.value)
            case "%":
                if right.value == 0:
                    raise RuntimeError("模运算除以零", line)
                return Number(left.value % right.value)
            case "**":
                return Number(left.value ** right.value)
            case "<":
                return TRUE if left.value < right.value else FALSE
            case ">":
                return TRUE if left.value > right.value else FALSE
            case "<=":
                return TRUE if left.value <= right.value else FALSE
            case ">=":
                return TRUE if left.value >= right.value else FALSE
            case "==":
                return TRUE if left.value == right.value else FALSE
            case "!=":
                return TRUE if left.value != right.value else FALSE
            case _:
                raise RuntimeError(f"未知的数字运算符: {op}", line)

    def _eval_string_infix(self, op: str, left: String, right: String, line: int) -> Obj:
        """字符串中缀运算"""
        match op:
            case "+":
                return String(left.value + right.value)
            case "<":
                return TRUE if left.value < right.value else FALSE
            case ">":
                return TRUE if left.value > right.value else FALSE
            case "<=":
                return TRUE if left.value <= right.value else FALSE
            case ">=":
                return TRUE if left.value >= right.value else FALSE
            case "==":
                return TRUE if left.value == right.value else FALSE
            case "!=":
                return TRUE if left.value != right.value else FALSE
            case _:
                raise RuntimeError(f"未知的字符串运算符: {op}", line)

    def _eval_assign_expression(self, node: AssignExpression) -> Obj:
        """求值赋值表达式"""
        value = self.eval(node.value)

        # 索引赋值: arr[i] = value 或 map["key"] = value
        if isinstance(node.name, IndexExpression):
            container = self.eval(node.name.left)
            index = self.eval(node.name.index)

            if isinstance(container, Array):
                if not isinstance(index, Number):
                    raise RuntimeError("数组索引必须是数字", node.line)
                idx = int(index.value)
                if idx < 0:
                    idx += len(container.elements)
                if idx < 0 or idx >= len(container.elements):
                    raise RuntimeError(f"数组索引越界: {int(index.value)}", node.line)
                container.elements[idx] = value
                return value

            if isinstance(container, Map):
                if not isinstance(index, String):
                    raise RuntimeError("映射的键必须是字符串", node.line)
                container.pairs[index.value] = value
                return value

            raise RuntimeError(
                f"不支持对 {container.type().name} 类型进行索引赋值",
                node.line
            )

        # 普通变量赋值
        if isinstance(node.name, Identifier):
            try:
                self.global_env.assign(node.name.value, value)
            except Exception:
                raise RuntimeError(f"未定义的变量: '{node.name.value}'", node.line)
            return value

        raise RuntimeError("赋值目标无效", node.line)

    def _eval_call_expression(self, node: CallExpression) -> Obj:
        """求值函数调用"""
        function = self.eval(node.function)
        args = [self.eval(arg) for arg in node.arguments]

        if isinstance(function, BuiltinFunction):
            try:
                return function(*args)
            except BuiltinError as e:
                raise RuntimeError(str(e), node.line)

        if isinstance(function, Function):
            return self._call_function(function, args, node.line)

        raise RuntimeError(
            f"不是可调用的函数: {function.type().name}",
            node.line
        )

    def _call_function(self, function: Function, args: list[Obj], line: int) -> Obj:
        """
        调用用户定义的函数

        1. 创建新的子环境
        2. 绑定参数
        3. 执行函数体
        4. 处理return值
        """
        # 检查参数数量
        if len(args) != len(function.parameters):
            raise RuntimeError(
                f"函数 {function.name or '<lambda>'} 需要 {len(function.parameters)} 个参数，"
                f"得到 {len(args)} 个",
                line
            )

        # 创建函数执行环境（闭包环境）
        func_env = function.env.create_child()

        # 绑定参数
        for param, arg in zip(function.parameters, args):
            func_env.set(param.value, arg)

        # 保存当前环境并切换到函数环境
        saved_env = self.global_env
        self.global_env = func_env

        try:
            # 执行函数体
            result = self._eval_block_statement(function.body)
            # 如果是ReturnValue，提取实际值
            if isinstance(result, ReturnValue):
                return result.value
            return result
        finally:
            # 恢复环境
            self.global_env = saved_env

    def _eval_function_literal(self, node: FunctionLiteral) -> Function:
        """求值函数字面量（创建闭包）"""
        # 捕获当前环境作为闭包环境
        func = Function(
            parameters=node.parameters,
            body=node.body,
            env=self.global_env,
            name=node.name,
        )
        # 如果函数有名字，绑定到环境
        if node.name:
            self.global_env.set(node.name, func)
        return func

    def _eval_index_expression(self, node: IndexExpression) -> Obj:
        """求值索引访问"""
        left = self.eval(node.left)
        index = self.eval(node.index)

        if isinstance(left, Array):
            if not isinstance(index, Number):
                raise RuntimeError("数组索引必须是数字", node.line)
            idx = int(index.value)
            if idx < 0:
                idx += len(left.elements)
            if idx < 0 or idx >= len(left.elements):
                raise RuntimeError(f"数组索引越界: {int(index.value)}", node.line)
            return left.elements[idx]

        if isinstance(left, String):
            if not isinstance(index, Number):
                raise RuntimeError("字符串索引必须是数字", node.line)
            idx = int(index.value)
            if idx < 0:
                idx += len(left.value)
            if idx < 0 or idx >= len(left.value):
                raise RuntimeError(f"字符串索引越界: {int(index.value)}", node.line)
            return String(left.value[idx])

        if isinstance(left, Map):
            if not isinstance(index, String):
                raise RuntimeError("映射的键必须是字符串", node.line)
            value = left.pairs.get(index.value)
            if value is None:
                return NULL
            return value

        raise RuntimeError(
            f"不支持对 {left.type().name} 类型进行索引访问",
            node.line
        )
