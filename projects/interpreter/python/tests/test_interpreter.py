"""
解释器测试
"""

import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.interpreter import Interpreter, RuntimeError
from src.objects import Number, String, Boolean, Null, Array, Map, Function


class TestInterpreter:
    """解释器测试"""

    def setup_method(self):
        """每个测试前创建新的解释器"""
        self.interp = Interpreter()

    def _eval(self, source: str):
        """辅助方法：执行并返回结果"""
        return self.interp.run(source)

    def _eval_value(self, source: str):
        """辅助方法：执行并返回原始值"""
        result = self._eval(source)
        if isinstance(result, Number):
            return result.value
        if isinstance(result, String):
            return result.value
        if isinstance(result, Boolean):
            return result.value
        if isinstance(result, Null):
            return None
        return result

    # ============================================================
    # 数字运算
    # ============================================================

    def test_number_literal(self):
        """测试数字字面量"""
        assert self._eval_value("42") == 42.0

    def test_float_literal(self):
        """测试浮点数字面量"""
        assert self._eval_value("3.14") == 3.14

    def test_addition(self):
        """测试加法"""
        assert self._eval_value("5 + 3") == 8.0

    def test_subtraction(self):
        """测试减法"""
        assert self._eval_value("10 - 3") == 7.0

    def test_multiplication(self):
        """测试乘法"""
        assert self._eval_value("5 * 3") == 15.0

    def test_division(self):
        """测试除法"""
        assert self._eval_value("10 / 2") == 5.0

    def test_modulo(self):
        """测试模运算"""
        assert self._eval_value("10 % 3") == 1.0

    def test_power(self):
        """测试幂运算"""
        assert self._eval_value("2 ** 10") == 1024.0

    def test_negative_number(self):
        """测试负数"""
        assert self._eval_value("-5") == -5.0

    def test_operator_precedence(self):
        """测试运算符优先级"""
        assert self._eval_value("5 + 3 * 2") == 11.0
        assert self._eval_value("(5 + 3) * 2") == 16.0
        assert self._eval_value("2 + 3 * 4 - 5") == 9.0

    def test_division_by_zero(self):
        """测试除以零"""
        with pytest.raises(RuntimeError):
            self._eval("1 / 0")

    # ============================================================
    # 字符串
    # ============================================================

    def test_string_literal(self):
        """测试字符串字面量"""
        assert self._eval_value('"hello"') == "hello"

    def test_string_concat(self):
        """测试字符串连接"""
        assert self._eval_value('"hello" + " " + "world"') == "hello world"

    def test_string_comparison(self):
        """测试字符串比较"""
        assert self._eval_value('"abc" < "def"') == True
        assert self._eval_value('"abc" == "abc"') == True

    # ============================================================
    # 布尔和逻辑
    # ============================================================

    def test_boolean_literal(self):
        """测试布尔字面量"""
        assert self._eval_value("true") == True
        assert self._eval_value("false") == False

    def test_comparison(self):
        """测试比较运算"""
        assert self._eval_value("5 > 3") == True
        assert self._eval_value("5 < 3") == False
        assert self._eval_value("5 == 5") == True
        assert self._eval_value("5 != 3") == True
        assert self._eval_value("5 >= 5") == True
        assert self._eval_value("5 <= 4") == False

    def test_logical_and(self):
        """测试逻辑与"""
        assert self._eval_value("true and true") == True
        assert self._eval_value("true and false") == False

    def test_logical_or(self):
        """测试逻辑或"""
        assert self._eval_value("false or true") == True
        assert self._eval_value("false or false") == False

    def test_logical_not(self):
        """测试逻辑非"""
        assert self._eval_value("not true") == False
        assert self._eval_value("not false") == True
        assert self._eval_value("!true") == False

    def test_short_circuit_and(self):
        """测试and短路求值"""
        # 如果and短路，不会执行右边的赋值
        self._eval("let x = 0;")
        self._eval("false and (x = 1);")
        assert self._eval_value("x") == 0.0

    def test_short_circuit_or(self):
        """测试or短路求值"""
        self._eval("let x = 0;")
        self._eval("true or (x = 1);")
        assert self._eval_value("x") == 0.0

    # ============================================================
    # 变量
    # ============================================================

    def test_let_statement(self):
        """测试变量声明"""
        assert self._eval_value("let x = 5; x") == 5.0

    def test_variable_assignment(self):
        """测试变量赋值"""
        self._eval("let x = 5;")
        assert self._eval_value("x = 10; x") == 10.0

    def test_plus_assign(self):
        """测试+=赋值"""
        self._eval("let x = 5;")
        assert self._eval_value("x += 3; x") == 8.0

    def test_minus_assign(self):
        """测试-=赋值"""
        self._eval("let x = 10;")
        assert self._eval_value("x -= 3; x") == 7.0

    def test_undefined_variable(self):
        """测试未定义变量"""
        with pytest.raises(RuntimeError):
            self._eval("x")

    # ============================================================
    # 控制流
    # ============================================================

    def test_if_true(self):
        """测试if为真"""
        assert self._eval_value("if true { 1 }") == 1.0

    def test_if_false(self):
        """测试if为假"""
        result = self._eval("if false { 1 }")
        assert result.type().name == "NULL"

    def test_if_else(self):
        """测试if-else"""
        assert self._eval_value("if false { 1 } else { 2 }") == 2.0

    def test_if_elif(self):
        """测试if-elif"""
        assert self._eval_value("if false { 1 } elif true { 2 } else { 3 }") == 2.0

    def test_if_elif_else(self):
        """测试if-elif-else"""
        assert self._eval_value("if false { 1 } elif false { 2 } else { 3 }") == 3.0

    def test_while_loop(self):
        """测试while循环"""
        source = """
        let sum = 0;
        let i = 1;
        while i <= 10 {
            sum += i;
            i += 1;
        }
        sum;
        """
        assert self._eval_value(source) == 55.0

    def test_while_break(self):
        """测试while中的break"""
        source = """
        let i = 0;
        while true {
            if i == 5 { break; }
            i += 1;
        }
        i;
        """
        assert self._eval_value(source) == 5.0

    def test_while_continue(self):
        """测试while中的continue"""
        source = """
        let sum = 0;
        let i = 0;
        while i < 10 {
            i += 1;
            if i % 2 == 0 { continue; }
            sum += i;
        }
        sum;
        """
        # 1+3+5+7+9 = 25
        assert self._eval_value(source) == 25.0

    def test_for_loop(self):
        """测试for循环"""
        source = """
        let sum = 0;
        for x in [1, 2, 3, 4, 5] {
            sum += x;
        }
        sum;
        """
        assert self._eval_value(source) == 15.0

    def test_for_string_iteration(self):
        """测试for循环遍历字符串"""
        source = """
        let result = "";
        for c in "abc" {
            result += c;
        }
        result;
        """
        assert self._eval_value(source) == "abc"

    # ============================================================
    # 函数
    # ============================================================

    def test_function_definition_and_call(self):
        """测试函数定义和调用"""
        source = """
        let add = fn(a, b) { return a + b; };
        add(3, 5);
        """
        assert self._eval_value(source) == 8.0

    def test_function_no_params(self):
        """测试无参数函数"""
        source = """
        let getFortyTwo = fn() { return 42; };
        getFortyTwo();
        """
        assert self._eval_value(source) == 42.0

    def test_function_implicit_return(self):
        """测试函数隐式返回"""
        source = """
        let add = fn(a, b) { a + b; };
        add(3, 5);
        """
        assert self._eval_value(source) == 8.0

    def test_recursive_function(self):
        """测试递归函数"""
        source = """
        let factorial = fn(n) {
            if n <= 1 { return 1; }
            return n * factorial(n - 1);
        };
        factorial(5);
        """
        assert self._eval_value(source) == 120.0

    def test_fibonacci(self):
        """测试斐波那契数列"""
        source = """
        let fib = fn(n) {
            if n <= 1 { return n; }
            return fib(n - 1) + fib(n - 2);
        };
        fib(10);
        """
        assert self._eval_value(source) == 55.0

    def test_higher_order_function(self):
        """测试高阶函数"""
        source = """
        let apply = fn(f, x) { return f(x); };
        let double = fn(x) { return x * 2; };
        apply(double, 5);
        """
        assert self._eval_value(source) == 10.0

    # ============================================================
    # 闭包
    # ============================================================

    def test_closure(self):
        """测试闭包"""
        source = """
        let makeCounter = fn() {
            let count = 0;
            fn() {
                count += 1;
                return count;
            }
        };
        let counter = makeCounter();
        let a = counter();
        let b = counter();
        let c = counter();
        c;
        """
        assert self._eval_value(source) == 3.0

    def test_closure_captures_variable(self):
        """测试闭包捕获变量"""
        source = """
        let x = 10;
        let getX = fn() { return x; };
        x = 20;
        getX();
        """
        assert self._eval_value(source) == 20.0

    def test_multiple_closures(self):
        """测试多个闭包独立"""
        source = """
        let makeAdder = fn(n) {
            fn(x) { return x + n; }
        };
        let add5 = makeAdder(5);
        let add10 = makeAdder(10);
        add5(3) + add10(3);
        """
        assert self._eval_value(source) == 21.0

    # ============================================================
    # 数组
    # ============================================================

    def test_array_literal(self):
        """测试数组字面量"""
        result = self._eval("[1, 2, 3]")
        assert isinstance(result, Array)
        assert len(result.elements) == 3

    def test_array_index(self):
        """测试数组索引"""
        assert self._eval_value("[1, 2, 3][0]") == 1.0
        assert self._eval_value("[1, 2, 3][2]") == 3.0

    def test_array_negative_index(self):
        """测试数组负索引"""
        assert self._eval_value("[1, 2, 3][-1]") == 3.0

    def test_array_index_out_of_bounds(self):
        """测试数组索引越界"""
        with pytest.raises(RuntimeError):
            self._eval("[1, 2, 3][10]")

    # ============================================================
    # 映射
    # ============================================================

    def test_map_literal(self):
        """测试映射字面量"""
        result = self._eval('{"name": "Alice", "age": 30}')
        assert isinstance(result, Map)

    def test_map_access(self):
        """测试映射访问"""
        assert self._eval_value('{"x": 5}["x"]') == 5.0

    def test_map_missing_key(self):
        """测试映射缺失键"""
        result = self._eval('{"x": 5}["y"]')
        assert result.type().name == "NULL"

    # ============================================================
    # 内置函数
    # ============================================================

    def test_builtin_len(self):
        """测试len函数"""
        assert self._eval_value('len("hello")') == 5.0
        assert self._eval_value("len([1, 2, 3])") == 3.0

    def test_builtin_str(self):
        """测试str函数"""
        assert self._eval_value("str(42)") == "42"
        assert self._eval_value("str(3.14)") == "3.14"

    def test_builtin_number(self):
        """测试number函数"""
        assert self._eval_value('number("42")') == 42.0
        assert self._eval_value('number("3.14")') == 3.14

    def test_builtin_abs(self):
        """测试abs函数"""
        assert self._eval_value("abs(-5)") == 5.0
        assert self._eval_value("abs(5)") == 5.0

    def test_builtin_sqrt(self):
        """测试sqrt函数"""
        assert self._eval_value("sqrt(16)") == 4.0

    def test_builtin_floor_ceil(self):
        """测试floor和ceil函数"""
        assert self._eval_value("floor(3.7)") == 3.0
        assert self._eval_value("ceil(3.2)") == 4.0

    def test_builtin_type(self):
        """测试type函数"""
        assert self._eval_value("type(42)") == "number"
        assert self._eval_value('type("hello")') == "string"
        assert self._eval_value("type(true)") == "boolean"
        assert self._eval_value("type(null)") == "null"
        assert self._eval_value("type([1,2,3])") == "array"

    def test_builtin_range(self):
        """测试range函数"""
        result = self._eval("range(5)")
        assert isinstance(result, Array)
        assert len(result.elements) == 5

    def test_builtin_upper_lower(self):
        """测试upper和lower函数"""
        assert self._eval_value('upper("hello")') == "HELLO"
        assert self._eval_value('lower("WORLD")') == "world"

    def test_builtin_contains(self):
        """测试contains函数"""
        assert self._eval_value('contains("hello world", "world")') == True
        assert self._eval_value('contains("hello", "xyz")') == False

    # ============================================================
    # 综合测试
    # ============================================================

    def test_complex_program(self):
        """测试复杂程序"""
        source = """
        let sum = fn(arr) {
            let total = 0;
            for x in arr {
                total += x;
            }
            return total;
        };

        let result = sum([1, 2, 3, 4, 5]);
        result;
        """
        assert self._eval_value(source) == 15.0

    def test_map_with_functions(self):
        """测试映射中存储函数"""
        source = """
        let ops = {
            "add": fn(a, b) { return a + b; },
            "sub": fn(a, b) { return a - b; }
        };
        ops["add"](5, 3);
        """
        assert self._eval_value(source) == 8.0

    def test_variable_scoping(self):
        """测试变量作用域"""
        source = """
        let x = 10;
        let f = fn() {
            let x = 20;
            return x;
        };
        f() + x;
        """
        assert self._eval_value(source) == 30.0

    def test_null_handling(self):
        """测试null处理"""
        assert self._eval_value("null") is None
        assert self._eval_value("null == null") == True
