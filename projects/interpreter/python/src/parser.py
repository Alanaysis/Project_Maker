"""
语法分析器（Parser）

将Token流转换为AST（抽象语法树）。
使用递归下降法实现，通过优先级爬升处理运算符优先级。

优先级（从低到高）：
  1. 赋值 (=, +=, -=)
  2. 逻辑OR (or)
  3. 逻辑AND (and)
  4. 比较 (==, !=, <, >, <=, >=)
  5. 加减 (+, -)
  6. 乘除 (*, /, %)
  7. 幂 (**)
  8. 前缀 (-, !, not)
  9. 调用和索引 (func(), arr[])
"""

from .token import Token, TokenType
from .lexer import Lexer, LexerError
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


class ParserError(Exception):
    """语法分析错误"""

    def __init__(self, message: str, line: int, column: int):
        super().__init__(f"[行 {line}, 列 {column}] 语法错误: {message}")
        self.line = line
        self.column = column


# 优先级常量
PREC_LOWEST = 0
PREC_ASSIGN = 1   # = += -=
PREC_OR = 2       # or
PREC_AND = 3      # and
PREC_COMPARE = 4  # == != < > <= >=
PREC_SUM = 5      # + -
PREC_PRODUCT = 6  # * / %
PREC_POWER = 7    # **
PREC_PREFIX = 8   # -x !x not x
PREC_CALL = 9     # func() arr[]
PREC_INDEX = 9    # arr[i]

# Token类型到优先级的映射
PRECEDENCES: dict[TokenType, int] = {
    TokenType.ASSIGN: PREC_ASSIGN,
    TokenType.PLUS_ASSIGN: PREC_ASSIGN,
    TokenType.MINUS_ASSIGN: PREC_ASSIGN,
    TokenType.OR: PREC_OR,
    TokenType.AND: PREC_AND,
    TokenType.EQ: PREC_COMPARE,
    TokenType.NOT_EQ: PREC_COMPARE,
    TokenType.LT: PREC_COMPARE,
    TokenType.GT: PREC_COMPARE,
    TokenType.LTE: PREC_COMPARE,
    TokenType.GTE: PREC_COMPARE,
    TokenType.PLUS: PREC_SUM,
    TokenType.MINUS: PREC_SUM,
    TokenType.STAR: PREC_PRODUCT,
    TokenType.SLASH: PREC_PRODUCT,
    TokenType.PERCENT: PREC_PRODUCT,
    TokenType.POWER: PREC_POWER,
    TokenType.LPAREN: PREC_CALL,
    TokenType.LBRACKET: PREC_INDEX,
}


class Parser:
    """
    递归下降语法分析器

    将Token流转换为AST。
    支持运算符优先级爬升、错误恢复等。
    """

    def __init__(self, source: str):
        self.source = source
        self.lexer = Lexer(source)
        self.tokens: list[Token] = []
        self.pos = 0
        self.errors: list[str] = []

    def parse(self) -> Program:
        """解析源代码，返回AST"""
        try:
            self.tokens = self.lexer.tokenize()
        except LexerError as e:
            raise ParserError(str(e), 1, 1)

        program = Program()
        while not self._current_is(TokenType.EOF):
            stmt = self._parse_statement()
            if stmt:
                program.statements.append(stmt)
        return program

    # ============================================================
    # 辅助方法
    # ============================================================

    def _current(self) -> Token:
        return self.tokens[self.pos]

    def _peek(self) -> Token:
        """查看下一个Token"""
        if self.pos + 1 < len(self.tokens):
            return self.tokens[self.pos + 1]
        return self.tokens[-1]  # EOF

    def _current_is(self, *types: TokenType) -> bool:
        return self._current().type in types

    def _expect(self, token_type: TokenType) -> Token:
        """消耗当前Token并返回，如果类型不匹配则报错"""
        token = self._current()
        if token.type != token_type:
            raise ParserError(
                f"期望 {token_type.name}，得到 {token.type.name} ({token.literal!r})",
                token.line, token.column
            )
        self._advance()
        return token

    def _advance(self) -> Token:
        """前进到下一个Token"""
        token = self._current()
        if self.pos < len(self.tokens) - 1:
            self.pos += 1
        return token

    def _expect_semicolon(self):
        """可选的分号消耗"""
        if self._current_is(TokenType.SEMICOLON):
            self._advance()

    def _current_precedence(self) -> int:
        return PRECEDENCES.get(self._current().type, PREC_LOWEST)

    def _peek_precedence(self) -> int:
        return PRECEDENCES.get(self._peek().type, PREC_LOWEST)

    # ============================================================
    # 语句解析
    # ============================================================

    def _parse_statement(self) -> Statement | None:
        """解析一条语句"""
        match self._current().type:
            case TokenType.LET:
                return self._parse_let_statement()
            case TokenType.RETURN:
                return self._parse_return_statement()
            case TokenType.IF:
                return self._parse_if_statement()
            case TokenType.WHILE:
                return self._parse_while_statement()
            case TokenType.FOR:
                return self._parse_for_statement()
            case TokenType.BREAK:
                return self._parse_break_statement()
            case TokenType.CONTINUE:
                return self._parse_continue_statement()
            case _:
                return self._parse_expression_statement()

    def _parse_let_statement(self) -> LetStatement:
        """解析 let 声明: let name = expr; 或 let name;"""
        line = self._current().line
        self._expect(TokenType.LET)
        name_token = self._expect(TokenType.IDENT)
        name = Identifier(name_token.literal, name_token.line)

        if self._current_is(TokenType.ASSIGN):
            self._advance()
            value = self._parse_expression(PREC_LOWEST)
        else:
            value = NullLiteral(line)

        self._expect_semicolon()

        return LetStatement(name, value, line)

    def _parse_return_statement(self) -> ReturnStatement:
        """解析 return 语句: return expr;"""
        line = self._current().line
        self._expect(TokenType.RETURN)

        value = None
        if not self._current_is(TokenType.SEMICOLON, TokenType.EOF, TokenType.RBRACE):
            value = self._parse_expression(PREC_LOWEST)

        self._expect_semicolon()
        return ReturnStatement(value, line)

    def _parse_if_statement(self) -> IfStatement:
        """
        解析 if 语句:
        if cond { ... } elif cond { ... } else { ... }
        """
        line = self._current().line
        self._expect(TokenType.IF)
        condition = self._parse_expression(PREC_LOWEST)
        consequence = self._parse_block_statement()

        elifs: list[tuple[Expression, BlockStatement]] = []
        while self._current_is(TokenType.ELIF):
            self._advance()
            elif_cond = self._parse_expression(PREC_LOWEST)
            elif_body = self._parse_block_statement()
            elifs.append((elif_cond, elif_body))

        alternative = None
        if self._current_is(TokenType.ELSE):
            self._advance()
            alternative = self._parse_block_statement()

        return IfStatement(condition, consequence, elifs, alternative, line)

    def _parse_while_statement(self) -> WhileStatement:
        """解析 while 循环: while cond { ... }"""
        line = self._current().line
        self._expect(TokenType.WHILE)
        condition = self._parse_expression(PREC_LOWEST)
        body = self._parse_block_statement()
        return WhileStatement(condition, body, line)

    def _parse_for_statement(self) -> ForStatement:
        """解析 for 循环: for x in expr { ... }"""
        line = self._current().line
        self._expect(TokenType.FOR)
        var_token = self._expect(TokenType.IDENT)
        var_name = Identifier(var_token.literal, var_token.line)
        self._expect(TokenType.IN)
        iterable = self._parse_expression(PREC_LOWEST)
        body = self._parse_block_statement()
        return ForStatement(var_name, iterable, body, line)

    def _parse_break_statement(self) -> BreakStatement:
        line = self._current().line
        self._expect(TokenType.BREAK)
        self._expect_semicolon()
        return BreakStatement(line)

    def _parse_continue_statement(self) -> ContinueStatement:
        line = self._current().line
        self._expect(TokenType.CONTINUE)
        self._expect_semicolon()
        return ContinueStatement(line)

    def _parse_block_statement(self) -> BlockStatement:
        """解析代码块: { stmt1; stmt2; ... }"""
        line = self._current().line
        self._expect(TokenType.LBRACE)
        statements: list[Statement] = []
        while not self._current_is(TokenType.RBRACE, TokenType.EOF):
            stmt = self._parse_statement()
            if stmt:
                statements.append(stmt)
        self._expect(TokenType.RBRACE)
        return BlockStatement(statements, line)

    def _parse_expression_statement(self) -> ExpressionStatement:
        """解析表达式语句"""
        line = self._current().line
        expression = self._parse_expression(PREC_LOWEST)
        self._expect_semicolon()
        return ExpressionStatement(expression, line)

    # ============================================================
    # 表达式解析（优先级爬升）
    # ============================================================

    def _parse_expression(self, precedence: int) -> Expression:
        """使用优先级爬升算法解析表达式"""
        left = self._parse_prefix()

        while (
            not self._current_is(TokenType.EOF, TokenType.SEMICOLON, TokenType.RBRACE)
            and precedence < self._current_precedence()
        ):
            left = self._parse_infix(left)

        return left

    def _parse_prefix(self) -> Expression:
        """解析前缀表达式"""
        token = self._current()
        match token.type:
            case TokenType.NUMBER:
                return self._parse_number_literal()
            case TokenType.STRING:
                return self._parse_string_literal()
            case TokenType.TRUE:
                return self._parse_boolean_literal(True)
            case TokenType.FALSE:
                return self._parse_boolean_literal(False)
            case TokenType.NULL:
                return self._parse_null_literal()
            case TokenType.IDENT:
                return self._parse_identifier()
            case TokenType.MINUS | TokenType.NOT:
                return self._parse_prefix_expression()
            case TokenType.LPAREN:
                return self._parse_grouped_expression()
            case TokenType.LBRACKET:
                return self._parse_array_literal()
            case TokenType.LBRACE:
                return self._parse_map_or_block()
            case TokenType.FN:
                return self._parse_function_literal()
            case _:
                raise ParserError(
                    f"无法解析前缀表达式: {token.literal!r}",
                    token.line, token.column
                )

    def _parse_infix(self, left: Expression) -> Expression:
        """解析中缀表达式"""
        token = self._current()
        match token.type:
            case (
                TokenType.PLUS | TokenType.MINUS | TokenType.STAR |
                TokenType.SLASH | TokenType.PERCENT | TokenType.POWER |
                TokenType.EQ | TokenType.NOT_EQ |
                TokenType.LT | TokenType.GT | TokenType.LTE | TokenType.GTE |
                TokenType.AND | TokenType.OR
            ):
                return self._parse_infix_expression(left)
            case TokenType.ASSIGN | TokenType.PLUS_ASSIGN | TokenType.MINUS_ASSIGN:
                return self._parse_assign_expression(left)
            case TokenType.LPAREN:
                return self._parse_call_expression(left)
            case TokenType.LBRACKET:
                return self._parse_index_expression(left)
            case _:
                return left

    def _parse_number_literal(self) -> NumberLiteral:
        token = self._advance()
        try:
            value = float(token.literal)
            # 如果是整数，保持为整数形式
            if "." not in token.literal:
                value = float(token.literal)
        except ValueError:
            raise ParserError(f"无效的数字: {token.literal}", token.line, token.column)
        return NumberLiteral(value, token.line)

    def _parse_string_literal(self) -> StringLiteral:
        token = self._advance()
        return StringLiteral(token.literal, token.line)

    def _parse_boolean_literal(self, value: bool) -> BooleanLiteral:
        token = self._advance()
        return BooleanLiteral(value, token.line)

    def _parse_null_literal(self) -> NullLiteral:
        token = self._advance()
        return NullLiteral(token.line)

    def _parse_identifier(self) -> Identifier:
        token = self._advance()
        return Identifier(token.literal, token.line)

    def _parse_prefix_expression(self) -> PrefixExpression:
        token = self._advance()
        right = self._parse_expression(PREC_PREFIX)
        return PrefixExpression(token.literal, right, token.line)

    def _parse_infix_expression(self, left: Expression) -> InfixExpression:
        token = self._advance()
        precedence = PRECEDENCES.get(token.type, PREC_LOWEST)
        right = self._parse_expression(precedence)
        return InfixExpression(left, token.literal, right, token.line)

    def _parse_assign_expression(self, left: Expression) -> AssignExpression:
        """解析赋值表达式"""
        token = self._advance()
        if not isinstance(left, (Identifier, IndexExpression)):
            raise ParserError("赋值左侧必须是标识符或索引表达式", token.line, token.column)

        value = self._parse_expression(PREC_ASSIGN - 1)

        # 处理 += 和 -=
        if token.type == TokenType.PLUS_ASSIGN:
            value = InfixExpression(left, "+", value, token.line)
        elif token.type == TokenType.MINUS_ASSIGN:
            value = InfixExpression(left, "-", value, token.line)

        return AssignExpression(left, value, token.line)

    def _parse_grouped_expression(self) -> Expression:
        """解析括号表达式: (expr)"""
        self._advance()  # 消耗 (
        expr = self._parse_expression(PREC_LOWEST)
        self._expect(TokenType.RPAREN)
        return expr

    def _parse_array_literal(self) -> ArrayLiteral:
        """解析数组字面量: [1, 2, 3]"""
        line = self._current().line
        self._advance()  # 消耗 [
        elements = self._parse_expression_list(TokenType.RBRACKET)
        return ArrayLiteral(elements, line)

    def _parse_map_or_block(self) -> Expression:
        """解析映射字面量或代码块"""
        line = self._current().line
        self._advance()  # 消耗 {

        pairs: list[tuple[Expression, Expression]] = []

        if self._current_is(TokenType.RBRACE):
            self._advance()
            return MapLiteral(pairs, line)

        # 解析第一对
        key = self._parse_expression(PREC_LOWEST)
        self._expect(TokenType.COLON)
        value = self._parse_expression(PREC_LOWEST)
        pairs.append((key, value))

        while self._current_is(TokenType.COMMA):
            self._advance()
            if self._current_is(TokenType.RBRACE):
                break
            key = self._parse_expression(PREC_LOWEST)
            self._expect(TokenType.COLON)
            value = self._parse_expression(PREC_LOWEST)
            pairs.append((key, value))

        self._expect(TokenType.RBRACE)
        return MapLiteral(pairs, line)

    def _parse_function_literal(self) -> FunctionLiteral:
        """解析函数字面量: fn(params) { body }"""
        line = self._current().line
        self._expect(TokenType.FN)

        # 可选的函数名（fn name(params) { ... }）
        name = ""
        if self._current_is(TokenType.IDENT):
            name = self._advance().literal

        self._expect(TokenType.LPAREN)
        parameters = self._parse_function_parameters()
        body = self._parse_block_statement()
        return FunctionLiteral(parameters, body, name, line)

    def _parse_function_parameters(self) -> list[Identifier]:
        """解析函数参数列表"""
        params: list[Identifier] = []

        if self._current_is(TokenType.RPAREN):
            self._advance()
            return params

        token = self._expect(TokenType.IDENT)
        params.append(Identifier(token.literal, token.line))

        while self._current_is(TokenType.COMMA):
            self._advance()
            token = self._expect(TokenType.IDENT)
            params.append(Identifier(token.literal, token.line))

        self._expect(TokenType.RPAREN)
        return params

    def _parse_call_expression(self, function: Expression) -> CallExpression:
        """解析函数调用: func(arg1, arg2)"""
        line = self._current().line
        self._advance()  # 消耗 (
        arguments = self._parse_expression_list(TokenType.RPAREN)
        return CallExpression(function, arguments, line)

    def _parse_index_expression(self, left: Expression) -> IndexExpression:
        """解析索引访问: expr[expr]"""
        line = self._current().line
        self._advance()  # 消耗 [
        index = self._parse_expression(PREC_LOWEST)
        self._expect(TokenType.RBRACKET)
        return IndexExpression(left, index, line)

    def _parse_expression_list(self, end: TokenType) -> list[Expression]:
        """解析以分隔符结尾的表达式列表"""
        args: list[Expression] = []

        if self._current_is(end):
            self._advance()
            return args

        args.append(self._parse_expression(PREC_LOWEST))
        while self._current_is(TokenType.COMMA):
            self._advance()
            args.append(self._parse_expression(PREC_LOWEST))

        self._expect(end)
        return args
