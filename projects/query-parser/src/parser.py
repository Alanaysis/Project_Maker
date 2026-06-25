"""
语法分析器 - 将 Token 序列解析为 AST
"""

from typing import List, Optional
from .lexer import Token, TokenType, Lexer, LexerError
from .ast_nodes import *


class ParseError(Exception):
    """语法解析错误"""
    def __init__(self, message: str, token: Optional[Token] = None):
        self.token = token
        if token:
            super().__init__(f"Parse error at {token.line}:{token.column}: {message}")
        else:
            super().__init__(f"Parse error: {message}")


class Parser:
    """SQL 语法分析器 - 递归下降解析"""

    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.pos = 0

    @classmethod
    def from_sql(cls, sql: str) -> 'Parser':
        """从 SQL 字符串创建解析器"""
        lexer = Lexer(sql)
        tokens = lexer.tokenize()
        return cls(tokens)

    def error(self, message: str) -> ParseError:
        """创建解析错误"""
        token = self.current_token()
        return ParseError(message, token)

    def current_token(self) -> Token:
        """获取当前 token"""
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        return Token(TokenType.EOF, '', 0, 0)

    def peek(self, offset: int = 0) -> Token:
        """查看前方的 token（不消耗）"""
        pos = self.pos + offset
        if pos < len(self.tokens):
            return self.tokens[pos]
        return Token(TokenType.EOF, '', 0, 0)

    def advance(self) -> Token:
        """消耗并返回当前 token"""
        token = self.current_token()
        self.pos += 1
        return token

    def expect(self, token_type: TokenType) -> Token:
        """期望指定类型的 token，否则报错"""
        token = self.current_token()
        if token.type != token_type:
            raise self.error(f"期望 {token_type.name}，得到 {token.type.name} ('{token.value}')")
        return self.advance()

    def match(self, *token_types: TokenType) -> bool:
        """检查当前 token 是否匹配指定类型之一"""
        return self.current_token().type in token_types

    def match_keyword(self, keyword: str) -> bool:
        """检查当前 token 是否是指定关键字"""
        token = self.current_token()
        return token.type.name == keyword.upper()

    def skip_semicolon(self) -> None:
        """跳过分号"""
        while self.match(TokenType.SEMICOLON):
            self.advance()

    def read_alias(self) -> str:
        """读取别名（可以是标识符或关键字）"""
        token = self.current_token()
        # 别名可以是标识符或任何关键字
        if token.type == TokenType.IDENTIFIER or token.type.name in ('COUNT', 'SUM', 'AVG', 'MIN', 'MAX',
                                                                       'SELECT', 'FROM', 'WHERE', 'GROUP',
                                                                       'ORDER', 'HAVING', 'LIMIT', 'OFFSET',
                                                                       'INSERT', 'UPDATE', 'DELETE', 'CREATE',
                                                                       'TABLE', 'DROP', 'ALTER', 'JOIN', 'INNER',
                                                                       'LEFT', 'RIGHT', 'FULL', 'CROSS', 'ON',
                                                                       'BY', 'AS', 'DISTINCT', 'ALL', 'ASC', 'DESC',
                                                                       'AND', 'OR', 'NOT', 'IN', 'BETWEEN', 'LIKE',
                                                                       'IS', 'NULL', 'EXISTS', 'ANY', 'SOME',
                                                                       'TRUE', 'FALSE', 'OUTER', 'SET', 'INTO',
                                                                       'VALUES', 'DELETE'):
            return self.advance().value
        raise self.error(f"期望别名，得到 {token.type.name} ('{token.value}')")

    # ========================================================================
    # 主入口
    # ========================================================================

    def parse(self) -> ASTNode:
        """解析 SQL 语句"""
        self.skip_semicolon()

        if self.match(TokenType.EOF):
            raise self.error("空查询")

        token = self.current_token()
        stmt = None

        if token.type == TokenType.SELECT:
            stmt = self.parse_select()
        elif token.type == TokenType.INSERT:
            stmt = self.parse_insert()
        elif token.type == TokenType.UPDATE:
            stmt = self.parse_update()
        elif token.type == TokenType.DELETE:
            stmt = self.parse_delete()
        else:
            raise self.error(f"不支持的语句类型: {token.value}")

        self.skip_semicolon()

        if not self.match(TokenType.EOF):
            raise self.error(f"意外的 token: {self.current_token().value}")

        return stmt

    # ========================================================================
    # SELECT 语句
    # ========================================================================

    def parse_select(self) -> SelectStatement:
        """解析 SELECT 语句"""
        stmt = SelectStatement()

        # SELECT [DISTINCT | ALL] columns
        self.expect(TokenType.SELECT)
        stmt.columns = self.parse_select_columns()

        # [FROM ...]
        if self.match(TokenType.FROM):
            stmt.from_clause = self.parse_from()

        # [WHERE ...]
        if self.match(TokenType.WHERE):
            stmt.where_clause = self.parse_where()

        # [GROUP BY ...]
        if self.match(TokenType.GROUP):
            stmt.group_by = self.parse_group_by()

        # [HAVING ...]
        if self.match(TokenType.HAVING):
            stmt.having = self.parse_having()

        # [ORDER BY ...]
        if self.match(TokenType.ORDER):
            stmt.order_by = self.parse_order_by()

        # [LIMIT ...]
        if self.match(TokenType.LIMIT):
            stmt.limit = self.parse_limit()

        return stmt

    def parse_select_columns(self) -> SelectColumns:
        """解析 SELECT 列列表"""
        node = SelectColumns()

        # 检查 DISTINCT
        if self.match(TokenType.DISTINCT):
            self.advance()
            node.distinct = True

        # 解析列列表
        while True:
            col = self.parse_select_item()
            node.columns.append(col)

            if not self.match(TokenType.COMMA):
                break
            self.advance()  # 跳过逗号

        return node

    def parse_select_item(self) -> ASTNode:
        """解析 SELECT 列项"""
        # 检查 *
        if self.match(TokenType.STAR):
            self.advance()
            return Star()

        # 检查 table.*
        if self.match(TokenType.IDENTIFIER) and self.peek(1).type == TokenType.DOT and self.peek(2).type == TokenType.STAR:
            table = self.advance().value
            self.advance()  # 跳过 .
            self.advance()  # 跳过 *
            return Star(table=table)

        # 解析表达式
        expr = self.parse_expression()

        # 检查别名
        if self.match(TokenType.AS):
            self.advance()
            alias = self.read_alias()
            if isinstance(expr, ColumnRef):
                expr.alias = alias
            elif isinstance(expr, FuncCall):
                expr.alias = alias
            else:
                # 创建一个带别名的列引用
                expr = ColumnRef(column=str(expr), alias=alias)
        elif self.match(TokenType.IDENTIFIER) or self.current_token().type.name in ('COUNT', 'SUM', 'AVG', 'MIN', 'MAX'):
            # 隐式别名
            alias = self.advance().value
            if isinstance(expr, ColumnRef):
                expr.alias = alias
            elif isinstance(expr, FuncCall):
                expr.alias = alias
            else:
                expr = ColumnRef(column=str(expr), alias=alias)

        return expr

    # ========================================================================
    # FROM 子句
    # ========================================================================

    def parse_from(self) -> FromClause:
        """解析 FROM 子句"""
        self.expect(TokenType.FROM)
        node = FromClause()

        # 解析表引用
        table = self.parse_table_ref()
        node.tables.append(table)

        # 多表用逗号分隔
        while self.match(TokenType.COMMA):
            self.advance()
            table = self.parse_table_ref()
            node.tables.append(table)

        # 解析 JOIN
        while self.is_join_keyword():
            join = self.parse_join()
            node.joins.append(join)

        return node

    def parse_table_ref(self) -> TableRef:
        """解析表引用"""
        name = self.expect(TokenType.IDENTIFIER).value
        node = TableRef(table_name=name)

        # 检查 schema.table
        if self.match(TokenType.DOT):
            self.advance()
            node.schema = node.table_name
            node.table_name = self.expect(TokenType.IDENTIFIER).value

        # 检查别名
        if self.match(TokenType.AS):
            self.advance()
            node.alias = self.expect(TokenType.IDENTIFIER).value
        elif self.match(TokenType.IDENTIFIER):
            node.alias = self.advance().value

        return node

    def is_join_keyword(self) -> bool:
        """检查是否是 JOIN 关键字"""
        token = self.current_token()
        if token.type == TokenType.JOIN:
            return True
        if token.type in (TokenType.INNER, TokenType.LEFT, TokenType.RIGHT,
                          TokenType.FULL, TokenType.CROSS):
            # 查看下一个 token 是否是 JOIN
            return self.peek(1).type == TokenType.JOIN
        return False

    def parse_join(self) -> JoinClause:
        """解析 JOIN 子句"""
        node = JoinClause()

        # 解析 JOIN 类型
        if self.match(TokenType.INNER):
            self.advance()
            node.join_type = JoinType.INNER
        elif self.match(TokenType.LEFT):
            self.advance()
            if self.match(TokenType.OUTER):
                self.advance()
            node.join_type = JoinType.LEFT
        elif self.match(TokenType.RIGHT):
            self.advance()
            if self.match(TokenType.OUTER):
                self.advance()
            node.join_type = JoinType.RIGHT
        elif self.match(TokenType.FULL):
            self.advance()
            if self.match(TokenType.OUTER):
                self.advance()
            node.join_type = JoinType.FULL
        elif self.match(TokenType.CROSS):
            self.advance()
            node.join_type = JoinType.CROSS
        else:
            node.join_type = JoinType.INNER

        self.expect(TokenType.JOIN)

        # 解析表
        node.table = self.parse_table_ref()

        # 解析 ON 条件
        if self.match(TokenType.ON):
            self.advance()
            node.on_condition = self.parse_or_expression()

        return node

    # ========================================================================
    # WHERE 子句
    # ========================================================================

    def parse_where(self) -> WhereClause:
        """解析 WHERE 子句"""
        self.expect(TokenType.WHERE)
        condition = self.parse_or_expression()
        return WhereClause(condition=condition)

    # ========================================================================
    # GROUP BY 子句
    # ========================================================================

    def parse_group_by(self) -> GroupByClause:
        """解析 GROUP BY 子句"""
        self.expect(TokenType.GROUP)
        self.expect(TokenType.BY)
        node = GroupByClause()

        while True:
            col = self.parse_expression()
            node.columns.append(col)

            if not self.match(TokenType.COMMA):
                break
            self.advance()

        return node

    # ========================================================================
    # HAVING 子句
    # ========================================================================

    def parse_having(self) -> HavingClause:
        """解析 HAVING 子句"""
        self.expect(TokenType.HAVING)
        condition = self.parse_or_expression()
        return HavingClause(condition=condition)

    # ========================================================================
    # ORDER BY 子句
    # ========================================================================

    def parse_order_by(self) -> OrderByClause:
        """解析 ORDER BY 子句"""
        self.expect(TokenType.ORDER)
        self.expect(TokenType.BY)
        node = OrderByClause()

        while True:
            item = self.parse_order_item()
            node.items.append(item)

            if not self.match(TokenType.COMMA):
                break
            self.advance()

        return node

    def parse_order_item(self) -> OrderItem:
        """解析 ORDER BY 项"""
        expr = self.parse_expression()
        direction = SortDirection.ASC

        if self.match(TokenType.ASC):
            self.advance()
            direction = SortDirection.ASC
        elif self.match(TokenType.DESC):
            self.advance()
            direction = SortDirection.DESC

        return OrderItem(expr=expr, direction=direction)

    # ========================================================================
    # LIMIT 子句
    # ========================================================================

    def parse_limit(self) -> LimitClause:
        """解析 LIMIT 子句"""
        self.expect(TokenType.LIMIT)
        node = LimitClause()

        # LIMIT count
        limit_token = self.expect(TokenType.NUMBER)
        node.limit = int(limit_token.value)

        # [OFFSET offset]
        if self.match(TokenType.OFFSET):
            self.advance()
            offset_token = self.expect(TokenType.NUMBER)
            node.offset = int(offset_token.value)
        # 或者 LIMIT offset, count 形式
        elif self.match(TokenType.COMMA):
            self.advance()
            count_token = self.expect(TokenType.NUMBER)
            node.offset = node.limit
            node.limit = int(count_token.value)

        return node

    # ========================================================================
    # INSERT 语句
    # ========================================================================

    def parse_insert(self) -> InsertStatement:
        """解析 INSERT 语句"""
        self.expect(TokenType.INSERT)
        self.expect(TokenType.INTO)

        stmt = InsertStatement()
        stmt.table = self.parse_table_ref()

        # 可选的列列表
        if self.match(TokenType.LPAREN):
            self.advance()
            while True:
                col = self.expect(TokenType.IDENTIFIER).value
                stmt.columns.append(col)
                if not self.match(TokenType.COMMA):
                    break
                self.advance()
            self.expect(TokenType.RPAREN)

        # VALUES 或 SELECT
        if self.match(TokenType.VALUES):
            stmt.values = self.parse_insert_values()
        elif self.match(TokenType.SELECT):
            stmt.select = self.parse_select()
        else:
            raise self.error("期望 VALUES 或 SELECT")

        return stmt

    def parse_insert_values(self) -> InsertValues:
        """解析 INSERT VALUES"""
        self.expect(TokenType.VALUES)
        node = InsertValues()

        while True:
            self.expect(TokenType.LPAREN)
            row = []
            while True:
                expr = self.parse_expression()
                row.append(expr)
                if not self.match(TokenType.COMMA):
                    break
                self.advance()
            self.expect(TokenType.RPAREN)
            node.values.append(row)

            if not self.match(TokenType.COMMA):
                break
            self.advance()

        return node

    # ========================================================================
    # UPDATE 语句
    # ========================================================================

    def parse_update(self) -> UpdateStatement:
        """解析 UPDATE 语句"""
        self.expect(TokenType.UPDATE)

        stmt = UpdateStatement()
        stmt.table = self.parse_table_ref()

        # SET 子句
        stmt.set_clause = self.parse_update_set()

        # WHERE 子句
        if self.match(TokenType.WHERE):
            stmt.where_clause = self.parse_where()

        return stmt

    def parse_update_set(self) -> UpdateSet:
        """解析 UPDATE SET 子句"""
        self.expect(TokenType.SET)
        node = UpdateSet()

        while True:
            col = self.expect(TokenType.IDENTIFIER).value
            self.expect(TokenType.EQ)
            value = self.parse_expression()
            node.assignments.append((col, value))

            if not self.match(TokenType.COMMA):
                break
            self.advance()

        return node

    # ========================================================================
    # DELETE 语句
    # ========================================================================

    def parse_delete(self) -> DeleteStatement:
        """解析 DELETE 语句"""
        self.expect(TokenType.DELETE)
        self.expect(TokenType.FROM)

        stmt = DeleteStatement()
        stmt.table = self.parse_table_ref()

        # WHERE 子句
        if self.match(TokenType.WHERE):
            stmt.where_clause = self.parse_where()

        return stmt

    # ========================================================================
    # 表达式解析 (运算符优先级)
    # ========================================================================

    def parse_expression(self) -> ASTNode:
        """解析表达式"""
        return self.parse_or_expression()

    def parse_or_expression(self) -> ASTNode:
        """解析 OR 表达式（最低优先级）"""
        left = self.parse_and_expression()

        while self.match(TokenType.OR):
            self.advance()
            right = self.parse_and_expression()
            left = OrExpr(left=left, right=right)

        return left

    def parse_and_expression(self) -> ASTNode:
        """解析 AND 表达式"""
        left = self.parse_not_expression()

        while self.match(TokenType.AND):
            self.advance()
            right = self.parse_not_expression()
            left = AndExpr(left=left, right=right)

        return left

    def parse_not_expression(self) -> ASTNode:
        """解析 NOT 表达式"""
        if self.match(TokenType.NOT):
            self.advance()
            operand = self.parse_comparison()
            return NotExpr(operand=operand)

        return self.parse_comparison()

    def parse_comparison(self) -> ASTNode:
        """解析比较表达式"""
        left = self.parse_addition()

        # 比较运算符
        if self.match(TokenType.EQ, TokenType.NEQ, TokenType.LT, TokenType.GT,
                      TokenType.LTE, TokenType.GTE):
            op_token = self.advance()
            right = self.parse_addition()
            return CompareExpr(op=op_token.value, left=left, right=right)

        # IS [NOT] NULL
        if self.match(TokenType.IS):
            self.advance()
            is_null = True
            if self.match(TokenType.NOT):
                self.advance()
                is_null = False
            self.expect(TokenType.NULL)
            return IsNullExpr(operand=left, is_null=is_null)

        # [NOT] IN
        if self.match(TokenType.IN):
            return self.parse_in_expression(left, not_in=False)
        if self.match(TokenType.NOT) and self.peek(1).type == TokenType.IN:
            self.advance()  # 跳过 NOT
            return self.parse_in_expression(left, not_in=True)

        # [NOT] BETWEEN
        if self.match(TokenType.BETWEEN):
            return self.parse_between_expression(left, not_between=False)
        if self.match(TokenType.NOT) and self.peek(1).type == TokenType.BETWEEN:
            self.advance()  # 跳过 NOT
            return self.parse_between_expression(left, not_between=True)

        # [NOT] LIKE
        if self.match(TokenType.LIKE):
            return self.parse_like_expression(left, not_like=False)
        if self.match(TokenType.NOT) and self.peek(1).type == TokenType.LIKE:
            self.advance()  # 跳过 NOT
            return self.parse_like_expression(left, not_like=True)

        return left

    def parse_in_expression(self, operand: ASTNode, not_in: bool) -> InExpr:
        """解析 IN 表达式"""
        self.expect(TokenType.IN)
        self.expect(TokenType.LPAREN)

        # 检查子查询
        if self.match(TokenType.SELECT):
            subquery = self.parse_select()
            self.expect(TokenType.RPAREN)
            return InExpr(operand=operand, not_in=not_in, subquery=subquery)

        # 值列表
        values = []
        while True:
            expr = self.parse_expression()
            values.append(expr)
            if not self.match(TokenType.COMMA):
                break
            self.advance()

        self.expect(TokenType.RPAREN)
        return InExpr(operand=operand, values=values, not_in=not_in)

    def parse_between_expression(self, operand: ASTNode, not_between: bool) -> BetweenExpr:
        """解析 BETWEEN 表达式"""
        self.expect(TokenType.BETWEEN)
        low = self.parse_addition()
        self.expect(TokenType.AND)
        high = self.parse_addition()
        return BetweenExpr(operand=operand, low=low, high=high, not_between=not_between)

    def parse_like_expression(self, operand: ASTNode, not_like: bool) -> LikeExpr:
        """解析 LIKE 表达式"""
        self.expect(TokenType.LIKE)
        pattern = self.parse_primary()
        return LikeExpr(operand=operand, pattern=pattern, not_like=not_like)

    def parse_addition(self) -> ASTNode:
        """解析加减表达式"""
        left = self.parse_multiplication()

        while self.match(TokenType.PLUS, TokenType.MINUS):
            op_token = self.advance()
            right = self.parse_multiplication()
            left = BinaryOp(op=op_token.value, left=left, right=right)

        return left

    def parse_multiplication(self) -> ASTNode:
        """解析乘除表达式"""
        left = self.parse_unary()

        while self.match(TokenType.STAR, TokenType.DIVIDE, TokenType.MODULO):
            op_token = self.advance()
            right = self.parse_unary()
            left = BinaryOp(op=op_token.value, left=left, right=right)

        return left

    def parse_unary(self) -> ASTNode:
        """解析一元表达式"""
        if self.match(TokenType.MINUS):
            self.advance()
            operand = self.parse_primary()
            return UnaryOp(op='-', operand=operand)

        if self.match(TokenType.NOT):
            self.advance()
            operand = self.parse_primary()
            return NotExpr(operand=operand)

        return self.parse_primary()

    def parse_primary(self) -> ASTNode:
        """解析基本表达式"""
        token = self.current_token()

        # 数字
        if self.match(TokenType.NUMBER):
            self.advance()
            return Literal(value=int(token.value), data_type="integer")

        # 浮点数
        if self.match(TokenType.FLOAT):
            self.advance()
            return Literal(value=float(token.value), data_type="float")

        # 字符串
        if self.match(TokenType.STRING):
            self.advance()
            return Literal(value=token.value, data_type="string")

        # NULL
        if self.match(TokenType.NULL):
            self.advance()
            return Literal(value=None, data_type="null")

        # TRUE/FALSE
        if self.match(TokenType.TRUE):
            self.advance()
            return Literal(value=True, data_type="boolean")

        if self.match(TokenType.FALSE):
            self.advance()
            return Literal(value=False, data_type="boolean")

        # * (星号)
        if self.match(TokenType.STAR):
            self.advance()
            return Star()

        # ? (参数)
        if self.match(TokenType.PARAM):
            self.advance()
            return Param()

        # 标识符
        if self.match(TokenType.IDENTIFIER):
            name = self.advance().value

            # 检查 table.column
            if self.match(TokenType.DOT):
                self.advance()
                if self.match(TokenType.STAR):
                    self.advance()
                    return Star(table=name)
                col = self.expect(TokenType.IDENTIFIER).value
                return ColumnRef(table=name, column=col)

            # 检查函数调用
            if self.match(TokenType.LPAREN):
                return self.parse_function_call(name)

            return ColumnRef(column=name)

        # 聚合函数关键字
        if self.match(TokenType.COUNT, TokenType.SUM, TokenType.AVG,
                      TokenType.MIN, TokenType.MAX):
            func_name = self.advance().value
            return self.parse_function_call(func_name)

        # 括号表达式
        if self.match(TokenType.LPAREN):
            self.advance()
            # 检查子查询
            if self.match(TokenType.SELECT):
                subquery = self.parse_select()
                self.expect(TokenType.RPAREN)
                return Subquery(query=subquery)
            expr = self.parse_expression()
            self.expect(TokenType.RPAREN)
            return expr

        # EXISTS
        if self.match(TokenType.EXISTS):
            self.advance()
            self.expect(TokenType.LPAREN)
            subquery = self.parse_select()
            self.expect(TokenType.RPAREN)
            return ExistsExpr(subquery=subquery)

        raise self.error(f"意外的 token: {token.value}")

    def parse_function_call(self, func_name: str) -> FuncCall:
        """解析函数调用"""
        self.expect(TokenType.LPAREN)

        node = FuncCall(func_name=func_name.upper())

        # 检查 DISTINCT
        if self.match(TokenType.DISTINCT):
            self.advance()
            node.distinct = True

        # 检查 *
        if self.match(TokenType.STAR):
            self.advance()
            node.args.append(Star())
        elif not self.match(TokenType.RPAREN):
            # 解析参数
            while True:
                arg = self.parse_expression()
                node.args.append(arg)
                if not self.match(TokenType.COMMA):
                    break
                self.advance()

        self.expect(TokenType.RPAREN)

        # 检查别名
        if self.match(TokenType.AS):
            self.advance()
            node.alias = self.read_alias()
        elif self.match(TokenType.IDENTIFIER) or self.current_token().type.name in ('COUNT', 'SUM', 'AVG', 'MIN', 'MAX'):
            node.alias = self.advance().value

        return node


def parse_sql(sql: str) -> ASTNode:
    """便捷函数：解析 SQL 字符串"""
    parser = Parser.from_sql(sql)
    return parser.parse()
