"""
AST节点定义

定义抽象语法树（AST）的所有节点类型。
AST是语法分析的输出，解释执行的输入。

节点层次：
- Node（基类）
  ├── Statement（语句）
  │   ├── Program          - 程序（语句列表）
  │   ├── LetStatement     - 变量声明
  │   ├── ReturnStatement  - return语句
  │   ├── ExpressionStatement - 表达式语句
  │   ├── BlockStatement   - 代码块
  │   ├── IfStatement      - if/elif/else
  │   ├── WhileStatement   - while循环
  │   ├── ForStatement     - for循环
  │   ├── BreakStatement   - break
  │   └── ContinueStatement- continue
  └── Expression（表达式）
      ├── NumberLiteral    - 数字字面量
      ├── StringLiteral    - 字符串字面量
      ├── BooleanLiteral   - 布尔字面量
      ├── NullLiteral      - null字面量
      ├── ArrayLiteral     - 数组字面量
      ├── Identifier       - 标识符
      ├── PrefixExpression - 前缀表达式（-x, !x）
      ├── InfixExpression  - 中缀表达式（x + y）
      ├── AssignExpression - 赋值表达式
      ├── CallExpression   - 函数调用
      ├── IndexExpression  - 索引访问（arr[i]）
      └── FunctionLiteral  - 函数字面量
"""

from dataclasses import dataclass, field
from abc import ABC, abstractmethod


class Node(ABC):
    """AST节点基类"""

    @abstractmethod
    def token_literal(self) -> str:
        """返回节点对应的token字面量"""
        pass

    @abstractmethod
    def __str__(self) -> str:
        """返回节点的字符串表示"""
        pass


class Statement(Node):
    """语句基类"""
    pass


class Expression(Node):
    """表达式基类"""
    pass


# ============================================================
# 程序和语句节点
# ============================================================

@dataclass
class Program(Node):
    """程序节点 - 整个程序的根节点"""
    statements: list[Statement] = field(default_factory=list)

    def token_literal(self) -> str:
        if self.statements:
            return self.statements[0].token_literal()
        return ""

    def __str__(self) -> str:
        return "\n".join(str(s) for s in self.statements)


@dataclass
class LetStatement(Statement):
    """变量声明: let x = expr;"""
    name: "Identifier"
    value: Expression
    line: int = 0

    def token_literal(self) -> str:
        return "let"

    def __str__(self) -> str:
        return f"let {self.name} = {self.value};"


@dataclass
class ReturnStatement(Statement):
    """return语句: return expr;"""
    value: Expression | None
    line: int = 0

    def token_literal(self) -> str:
        return "return"

    def __str__(self) -> str:
        return f"return {self.value};" if self.value else "return;"


@dataclass
class ExpressionStatement(Statement):
    """表达式语句: expr;"""
    expression: Expression
    line: int = 0

    def token_literal(self) -> str:
        return self.expression.token_literal()

    def __str__(self) -> str:
        return str(self.expression)


@dataclass
class BlockStatement(Statement):
    """代码块: { stmt1; stmt2; ... }"""
    statements: list[Statement] = field(default_factory=list)
    line: int = 0

    def token_literal(self) -> str:
        return "{"

    def __str__(self) -> str:
        body = "; ".join(str(s) for s in self.statements)
        return f"{{ {body} }}"


@dataclass
class IfStatement(Statement):
    """
    if语句:
    if cond { ... } elif cond { ... } else { ... }
    """
    condition: Expression
    consequence: BlockStatement
    elifs: list[tuple[Expression, BlockStatement]] = field(default_factory=list)
    alternative: BlockStatement | None = None
    line: int = 0

    def token_literal(self) -> str:
        return "if"

    def __str__(self) -> str:
        result = f"if {self.condition} {self.consequence}"
        for cond, body in self.elifs:
            result += f" elif {cond} {body}"
        if self.alternative:
            result += f" else {self.alternative}"
        return result


@dataclass
class WhileStatement(Statement):
    """while循环: while cond { ... }"""
    condition: Expression
    body: BlockStatement
    line: int = 0

    def token_literal(self) -> str:
        return "while"

    def __str__(self) -> str:
        return f"while {self.condition} {self.body}"


@dataclass
class ForStatement(Statement):
    """for循环: for x in expr { ... }"""
    var_name: "Identifier"
    iterable: Expression
    body: BlockStatement
    line: int = 0

    def token_literal(self) -> str:
        return "for"

    def __str__(self) -> str:
        return f"for {self.var_name} in {self.iterable} {self.body}"


@dataclass
class BreakStatement(Statement):
    """break语句"""
    line: int = 0

    def token_literal(self) -> str:
        return "break"

    def __str__(self) -> str:
        return "break;"


@dataclass
class ContinueStatement(Statement):
    """continue语句"""
    line: int = 0

    def token_literal(self) -> str:
        return "continue"

    def __str__(self) -> str:
        return "continue;"


# ============================================================
# 表达式节点
# ============================================================

@dataclass
class NumberLiteral(Expression):
    """数字字面量"""
    value: float
    line: int = 0

    def token_literal(self) -> str:
        return str(self.value)

    def __str__(self) -> str:
        if self.value == int(self.value):
            return str(int(self.value))
        return str(self.value)


@dataclass
class StringLiteral(Expression):
    """字符串字面量"""
    value: str
    line: int = 0

    def token_literal(self) -> str:
        return self.value

    def __str__(self) -> str:
        return f'"{self.value}"'


@dataclass
class BooleanLiteral(Expression):
    """布尔字面量"""
    value: bool
    line: int = 0

    def token_literal(self) -> str:
        return str(self.value).lower()

    def __str__(self) -> str:
        return str(self.value).lower()


@dataclass
class NullLiteral(Expression):
    """null字面量"""
    line: int = 0

    def token_literal(self) -> str:
        return "null"

    def __str__(self) -> str:
        return "null"


@dataclass
class ArrayLiteral(Expression):
    """数组字面量: [1, 2, 3]"""
    elements: list[Expression] = field(default_factory=list)
    line: int = 0

    def token_literal(self) -> str:
        return "["

    def __str__(self) -> str:
        elems = ", ".join(str(e) for e in self.elements)
        return f"[{elems}]"


@dataclass
class MapLiteral(Expression):
    """映射字面量: {"key": value}"""
    pairs: list[tuple[Expression, Expression]] = field(default_factory=list)
    line: int = 0

    def token_literal(self) -> str:
        return "{"

    def __str__(self) -> str:
        pairs = ", ".join(f"{k}: {v}" for k, v in self.pairs)
        return f"{{{pairs}}}"


@dataclass
class Identifier(Expression):
    """标识符"""
    value: str
    line: int = 0

    def token_literal(self) -> str:
        return self.value

    def __str__(self) -> str:
        return self.value


@dataclass
class PrefixExpression(Expression):
    """前缀表达式: op expr"""
    operator: str
    right: Expression
    line: int = 0

    def token_literal(self) -> str:
        return self.operator

    def __str__(self) -> str:
        return f"({self.operator}{self.right})"


@dataclass
class InfixExpression(Expression):
    """中缀表达式: left op right"""
    left: Expression
    operator: str
    right: Expression
    line: int = 0

    def token_literal(self) -> str:
        return self.operator

    def __str__(self) -> str:
        return f"({self.left} {self.operator} {self.right})"


@dataclass
class AssignExpression(Expression):
    """赋值表达式: name = value 或 arr[i] = value"""
    name: Expression  # Identifier 或 IndexExpression
    value: Expression
    line: int = 0

    def token_literal(self) -> str:
        return "="

    def __str__(self) -> str:
        return f"{self.name} = {self.value}"


@dataclass
class CallExpression(Expression):
    """函数调用: func(arg1, arg2)"""
    function: Expression
    arguments: list[Expression] = field(default_factory=list)
    line: int = 0

    def token_literal(self) -> str:
        return "("

    def __str__(self) -> str:
        args = ", ".join(str(a) for a in self.arguments)
        return f"{self.function}({args})"


@dataclass
class IndexExpression(Expression):
    """索引访问: expr[expr]"""
    left: Expression
    index: Expression
    line: int = 0

    def token_literal(self) -> str:
        return "["

    def __str__(self) -> str:
        return f"({self.left}[{self.index}])"


@dataclass
class FunctionLiteral(Expression):
    """函数字面量: fn(params) { body }"""
    parameters: list["Identifier"] = field(default_factory=list)
    body: BlockStatement = field(default_factory=BlockStatement)
    name: str = ""  # 可选的函数名（用于命名函数表达式）
    line: int = 0

    def token_literal(self) -> str:
        return "fn"

    def __str__(self) -> str:
        params = ", ".join(str(p) for p in self.parameters)
        name_part = f" {self.name}" if self.name else ""
        return f"fn{name_part}({params}) {self.body}"
