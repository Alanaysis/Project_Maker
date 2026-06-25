"""
语法分析器测试
"""

import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.parser import Parser, ParserError
from src.ast_nodes import (
    Program, LetStatement, ReturnStatement, ExpressionStatement,
    IfStatement, WhileStatement, ForStatement,
    NumberLiteral, StringLiteral, BooleanLiteral, NullLiteral,
    ArrayLiteral, Identifier, PrefixExpression, InfixExpression,
    AssignExpression, CallExpression, FunctionLiteral,
)


class TestParser:
    """语法分析器测试"""

    def _parse(self, source: str) -> Program:
        """辅助方法：解析源代码"""
        parser = Parser(source)
        return parser.parse()

    def _parse_expr(self, source: str):
        """辅助方法：解析单个表达式"""
        program = self._parse(source)
        assert len(program.statements) == 1
        stmt = program.statements[0]
        assert isinstance(stmt, ExpressionStatement)
        return stmt.expression

    # ============================================================
    # 字面量
    # ============================================================

    def test_number_literal(self):
        """测试数字字面量"""
        expr = self._parse_expr("42;")
        assert isinstance(expr, NumberLiteral)
        assert expr.value == 42.0

    def test_string_literal(self):
        """测试字符串字面量"""
        expr = self._parse_expr('"hello";')
        assert isinstance(expr, StringLiteral)
        assert expr.value == "hello"

    def test_boolean_literal(self):
        """测试布尔字面量"""
        expr = self._parse_expr("true;")
        assert isinstance(expr, BooleanLiteral)
        assert expr.value is True

        program = self._parse("false;")
        expr = program.statements[0].expression
        assert isinstance(expr, BooleanLiteral)
        assert expr.value is False

    def test_null_literal(self):
        """测试null字面量"""
        expr = self._parse_expr("null;")
        assert isinstance(expr, NullLiteral)

    def test_identifier(self):
        """测试标识符"""
        expr = self._parse_expr("x;")
        assert isinstance(expr, Identifier)
        assert expr.value == "x"

    # ============================================================
    # 前缀表达式
    # ============================================================

    def test_prefix_minus(self):
        """测试负号前缀"""
        expr = self._parse_expr("-5;")
        assert isinstance(expr, PrefixExpression)
        assert expr.operator == "-"
        assert isinstance(expr.right, NumberLiteral)
        assert expr.right.value == 5.0

    def test_prefix_not(self):
        """测试not前缀"""
        expr = self._parse_expr("not true;")
        assert isinstance(expr, PrefixExpression)
        assert expr.operator == "not"

    # ============================================================
    # 中缀表达式
    # ============================================================

    def test_infix_arithmetic(self):
        """测试算术中缀表达式"""
        expr = self._parse_expr("5 + 3;")
        assert isinstance(expr, InfixExpression)
        assert expr.operator == "+"
        assert isinstance(expr.left, NumberLiteral)
        assert isinstance(expr.right, NumberLiteral)

    def test_operator_precedence(self):
        """测试运算符优先级"""
        expr = self._parse_expr("5 + 3 * 2;")
        assert isinstance(expr, InfixExpression)
        assert expr.operator == "+"
        assert isinstance(expr.right, InfixExpression)
        assert expr.right.operator == "*"

    def test_operator_precedence_complex(self):
        """测试复杂运算符优先级"""
        expr = self._parse_expr("2 + 3 * 4 - 5;")
        # 应该解析为 (2 + (3 * 4)) - 5
        assert isinstance(expr, InfixExpression)
        assert expr.operator == "-"
        assert isinstance(expr.left, InfixExpression)
        assert expr.left.operator == "+"

    def test_power_operator(self):
        """测试幂运算符"""
        expr = self._parse_expr("2 ** 3;")
        assert isinstance(expr, InfixExpression)
        assert expr.operator == "**"

    def test_comparison_operators(self):
        """测试比较运算符"""
        for op in ["==", "!=", "<", ">", "<=", ">="]:
            expr = self._parse_expr(f"x {op} 5;")
            assert isinstance(expr, InfixExpression)
            assert expr.operator == op

    def test_logical_operators(self):
        """测试逻辑运算符"""
        expr = self._parse_expr("true and false;")
        assert isinstance(expr, InfixExpression)
        assert expr.operator == "and"

        expr = self._parse_expr("true or false;")
        assert isinstance(expr, InfixExpression)
        assert expr.operator == "or"

    def test_grouped_expression(self):
        """测试括号表达式"""
        expr = self._parse_expr("(5 + 3) * 2;")
        assert isinstance(expr, InfixExpression)
        assert expr.operator == "*"
        assert isinstance(expr.left, InfixExpression)
        assert expr.left.operator == "+"

    # ============================================================
    # 语句
    # ============================================================

    def test_let_statement(self):
        """测试变量声明"""
        program = self._parse("let x = 5;")
        assert len(program.statements) == 1
        stmt = program.statements[0]
        assert isinstance(stmt, LetStatement)
        assert stmt.name.value == "x"
        assert isinstance(stmt.value, NumberLiteral)
        assert stmt.value.value == 5.0

    def test_return_statement(self):
        """测试return语句"""
        program = self._parse("return 5;")
        assert len(program.statements) == 1
        stmt = program.statements[0]
        assert isinstance(stmt, ReturnStatement)
        assert isinstance(stmt.value, NumberLiteral)

    def test_return_no_value(self):
        """测试无返回值的return"""
        program = self._parse("return;")
        assert len(program.statements) == 1
        stmt = program.statements[0]
        assert isinstance(stmt, ReturnStatement)
        assert stmt.value is None

    def test_expression_statement(self):
        """测试表达式语句"""
        program = self._parse("5 + 3;")
        assert len(program.statements) == 1
        stmt = program.statements[0]
        assert isinstance(stmt, ExpressionStatement)

    # ============================================================
    # 控制流
    # ============================================================

    def test_if_statement(self):
        """测试if语句"""
        program = self._parse("if x > 5 { let y = 10; }")
        stmt = program.statements[0]
        assert isinstance(stmt, IfStatement)
        assert isinstance(stmt.condition, InfixExpression)
        assert len(stmt.consequence.statements) == 1
        assert stmt.alternative is None

    def test_if_else_statement(self):
        """测试if-else语句"""
        program = self._parse("if x > 5 { let y = 10; } else { let y = 0; }")
        stmt = program.statements[0]
        assert isinstance(stmt, IfStatement)
        assert stmt.alternative is not None
        assert len(stmt.alternative.statements) == 1

    def test_while_statement(self):
        """测试while循环"""
        program = self._parse("while x > 0 { x = x - 1; }")
        stmt = program.statements[0]
        assert isinstance(stmt, WhileStatement)
        assert isinstance(stmt.condition, InfixExpression)
        assert len(stmt.body.statements) == 1

    def test_for_statement(self):
        """测试for循环"""
        program = self._parse("for x in arr { print(x); }")
        stmt = program.statements[0]
        assert isinstance(stmt, ForStatement)
        assert stmt.var_name.value == "x"
        assert isinstance(stmt.iterable, Identifier)

    # ============================================================
    # 函数
    # ============================================================

    def test_function_literal(self):
        """测试函数字面量"""
        expr = self._parse_expr("fn(x, y) { return x + y; }")
        assert isinstance(expr, FunctionLiteral)
        assert len(expr.parameters) == 2
        assert expr.parameters[0].value == "x"
        assert expr.parameters[1].value == "y"

    def test_function_call(self):
        """测试函数调用"""
        expr = self._parse_expr("add(1, 2);")
        assert isinstance(expr, CallExpression)
        assert isinstance(expr.function, Identifier)
        assert expr.function.value == "add"
        assert len(expr.arguments) == 2

    def test_function_no_params(self):
        """测试无参数函数"""
        expr = self._parse_expr("fn() { return 42; }")
        assert isinstance(expr, FunctionLiteral)
        assert len(expr.parameters) == 0

    # ============================================================
    # 数组
    # ============================================================

    def test_array_literal(self):
        """测试数组字面量"""
        expr = self._parse_expr("[1, 2, 3];")
        assert isinstance(expr, ArrayLiteral)
        assert len(expr.elements) == 3

    def test_empty_array(self):
        """测试空数组"""
        expr = self._parse_expr("[];")
        assert isinstance(expr, ArrayLiteral)
        assert len(expr.elements) == 0

    # ============================================================
    # 赋值
    # ============================================================

    def test_assign_expression(self):
        """测试赋值表达式"""
        expr = self._parse_expr("x = 5;")
        assert isinstance(expr, AssignExpression)
        assert expr.name.value == "x"

    # ============================================================
    # 多语句
    # ============================================================

    def test_multiple_statements(self):
        """测试多语句程序"""
        source = """
        let x = 5;
        let y = 10;
        let z = x + y;
        """
        program = self._parse(source)
        assert len(program.statements) == 3

    def test_error_on_invalid_syntax(self):
        """测试语法错误"""
        with pytest.raises(ParserError):
            Parser("let = 5;").parse()

    def test_error_on_missing_semicolon(self):
        """测试缺少分号（可选分号设计中不应报错）"""
        # 我们的语言支持可选分号
        program = self._parse("let x = 5")
        assert len(program.statements) == 1
