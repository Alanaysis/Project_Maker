"""
词法分析器 - 将 SQL 字符串转换为 Token 序列
"""

from enum import Enum, auto
from dataclasses import dataclass
from typing import List, Optional


class TokenType(Enum):
    """Token 类型枚举"""
    # 字面量
    IDENTIFIER = auto()      # 标识符 (表名、列名等)
    NUMBER = auto()          # 数字
    STRING = auto()          # 字符串 'hello'
    FLOAT = auto()           # 浮点数

    # SQL 关键字
    SELECT = auto()
    FROM = auto()
    WHERE = auto()
    INSERT = auto()
    INTO = auto()
    VALUES = auto()
    UPDATE = auto()
    SET = auto()
    DELETE = auto()
    CREATE = auto()
    TABLE = auto()
    DROP = auto()
    ALTER = auto()

    # JOIN 关键字
    JOIN = auto()
    INNER = auto()
    LEFT = auto()
    RIGHT = auto()
    FULL = auto()
    CROSS = auto()
    ON = auto()

    # 子句关键字
    GROUP = auto()
    BY = auto()
    ORDER = auto()
    HAVING = auto()
    LIMIT = auto()
    OFFSET = auto()
    AS = auto()
    DISTINCT = auto()
    ALL = auto()

    # 排序方向
    ASC = auto()
    DESC = auto()

    # 聚合函数
    COUNT = auto()
    SUM = auto()
    AVG = auto()
    MIN = auto()
    MAX = auto()

    # 逻辑运算符
    AND = auto()
    OR = auto()
    NOT = auto()
    IN = auto()
    BETWEEN = auto()
    LIKE = auto()
    IS = auto()
    NULL = auto()
    EXISTS = auto()
    ANY = auto()
    SOME = auto()

    # 比较运算符
    EQ = auto()              # =
    NEQ = auto()             # <> 或 !=
    LT = auto()              # <
    GT = auto()              # >
    LTE = auto()             # <=
    GTE = auto()             # >=

    # 算术运算符
    PLUS = auto()            # +
    MINUS = auto()           # -
    MULTIPLY = auto()        # *
    DIVIDE = auto()          # /
    MODULO = auto()          # %

    # 分隔符
    LPAREN = auto()          # (
    RPAREN = auto()          # )
    COMMA = auto()           # ,
    SEMICOLON = auto()       # ;
    DOT = auto()             # .
    STAR = auto()            # *

    # 特殊
    PARAM = auto()           # ? 参数占位符
    TRUE = auto()            # TRUE
    FALSE = auto()           # FALSE
    OUTER = auto()           # OUTER (用于 LEFT/RIGHT/FULL OUTER JOIN)
    EOF = auto()
    UNKNOWN = auto()


# SQL 关键字映射
KEYWORDS = {
    'SELECT': TokenType.SELECT,
    'FROM': TokenType.FROM,
    'WHERE': TokenType.WHERE,
    'INSERT': TokenType.INSERT,
    'INTO': TokenType.INTO,
    'VALUES': TokenType.VALUES,
    'UPDATE': TokenType.UPDATE,
    'SET': TokenType.SET,
    'DELETE': TokenType.DELETE,
    'CREATE': TokenType.CREATE,
    'TABLE': TokenType.TABLE,
    'DROP': TokenType.DROP,
    'ALTER': TokenType.ALTER,
    'JOIN': TokenType.JOIN,
    'INNER': TokenType.INNER,
    'LEFT': TokenType.LEFT,
    'RIGHT': TokenType.RIGHT,
    'FULL': TokenType.FULL,
    'CROSS': TokenType.CROSS,
    'ON': TokenType.ON,
    'GROUP': TokenType.GROUP,
    'BY': TokenType.BY,
    'ORDER': TokenType.ORDER,
    'HAVING': TokenType.HAVING,
    'LIMIT': TokenType.LIMIT,
    'OFFSET': TokenType.OFFSET,
    'AS': TokenType.AS,
    'DISTINCT': TokenType.DISTINCT,
    'ALL': TokenType.ALL,
    'ASC': TokenType.ASC,
    'DESC': TokenType.DESC,
    'COUNT': TokenType.COUNT,
    'SUM': TokenType.SUM,
    'AVG': TokenType.AVG,
    'MIN': TokenType.MIN,
    'MAX': TokenType.MAX,
    'AND': TokenType.AND,
    'OR': TokenType.OR,
    'NOT': TokenType.NOT,
    'IN': TokenType.IN,
    'BETWEEN': TokenType.BETWEEN,
    'LIKE': TokenType.LIKE,
    'IS': TokenType.IS,
    'NULL': TokenType.NULL,
    'EXISTS': TokenType.EXISTS,
    'ANY': TokenType.ANY,
    'SOME': TokenType.SOME,
    'TRUE': TokenType.TRUE,
    'FALSE': TokenType.FALSE,
    'OUTER': TokenType.OUTER,
}


@dataclass
class Token:
    """Token 数据类"""
    type: TokenType
    value: str
    line: int = 1
    column: int = 1

    def __repr__(self) -> str:
        return f"Token({self.type.name}, '{self.value}', {self.line}:{self.column})"


class LexerError(Exception):
    """词法分析错误"""
    def __init__(self, message: str, line: int, column: int):
        self.line = line
        self.column = column
        super().__init__(f"Lexer error at {line}:{column}: {message}")


class Lexer:
    """SQL 词法分析器"""

    def __init__(self, text: str):
        self.text = text
        self.pos = 0
        self.line = 1
        self.column = 1
        self.tokens: List[Token] = []

    def error(self, message: str) -> LexerError:
        """创建词法错误"""
        return LexerError(message, self.line, self.column)

    def peek(self) -> Optional[str]:
        """查看当前字符（不消耗）"""
        if self.pos < len(self.text):
            return self.text[self.pos]
        return None

    def advance(self) -> str:
        """消耗并返回当前字符"""
        ch = self.text[self.pos]
        self.pos += 1
        if ch == '\n':
            self.line += 1
            self.column = 1
        else:
            self.column += 1
        return ch

    def skip_whitespace(self) -> None:
        """跳过空白字符"""
        while self.pos < len(self.text) and self.text[self.pos] in ' \t\n\r':
            self.advance()

    def skip_comment(self) -> bool:
        """跳过注释"""
        if self.pos + 1 < len(self.text):
            # 单行注释 --
            if self.text[self.pos:self.pos+2] == '--':
                while self.pos < len(self.text) and self.text[self.pos] != '\n':
                    self.advance()
                return True
            # 多行注释 /* */
            if self.text[self.pos:self.pos+2] == '/*':
                self.advance()  # 跳过 /
                self.advance()  # 跳过 *
                while self.pos + 1 < len(self.text):
                    if self.text[self.pos:self.pos+2] == '*/':
                        self.advance()  # 跳过 *
                        self.advance()  # 跳过 /
                        return True
                    self.advance()
                raise self.error("未闭合的多行注释")
        return False

    def read_number(self) -> Token:
        """读取数字"""
        start_col = self.column
        start_pos = self.pos
        has_dot = False

        while self.pos < len(self.text):
            ch = self.text[self.pos]
            if ch.isdigit():
                self.advance()
            elif ch == '.' and not has_dot:
                has_dot = True
                self.advance()
            else:
                break

        value = self.text[start_pos:self.pos]
        token_type = TokenType.FLOAT if has_dot else TokenType.NUMBER
        return Token(token_type, value, self.line, start_col)

    def read_string(self) -> Token:
        """读取字符串（单引号包围）"""
        start_col = self.column
        self.advance()  # 跳过开始的单引号
        result = []

        while self.pos < len(self.text):
            ch = self.text[self.pos]
            if ch == "'":
                # 检查是否是转义的单引号 ''
                if self.pos + 1 < len(self.text) and self.text[self.pos + 1] == "'":
                    result.append("'")
                    self.advance()
                    self.advance()
                else:
                    break
            elif ch == '\\':
                self.advance()
                if self.pos < len(self.text):
                    result.append(self.text[self.pos])
                    self.advance()
            else:
                result.append(ch)
                self.advance()

        if self.pos >= len(self.text):
            raise self.error("未闭合的字符串")

        value = ''.join(result)
        self.advance()  # 跳过结束的单引号
        return Token(TokenType.STRING, value, self.line, start_col)

    def read_identifier(self) -> Token:
        """读取标识符或关键字"""
        start_col = self.column
        start_pos = self.pos

        while self.pos < len(self.text):
            ch = self.text[self.pos]
            if ch.isalnum() or ch == '_':
                self.advance()
            else:
                break

        value = self.text[start_pos:self.pos]
        # 检查是否是关键字
        token_type = KEYWORDS.get(value.upper(), TokenType.IDENTIFIER)
        return Token(token_type, value.upper() if token_type != TokenType.IDENTIFIER else value,
                    self.line, start_col)

    def read_quoted_identifier(self) -> Token:
        """读取双引号包围的标识符"""
        start_col = self.column
        self.advance()  # 跳过开始的双引号
        start_pos = self.pos

        while self.pos < len(self.text):
            ch = self.text[self.pos]
            if ch == '"':
                break
            self.advance()

        if self.pos >= len(self.text):
            raise self.error("未闭合的引用标识符")

        value = self.text[start_pos:self.pos]
        self.advance()  # 跳过结束的双引号
        return Token(TokenType.IDENTIFIER, value, self.line, start_col)

    def tokenize(self) -> List[Token]:
        """将 SQL 字符串转换为 Token 序列"""
        self.tokens = []

        while self.pos < len(self.text):
            self.skip_whitespace()

            if self.pos >= len(self.text):
                break

            # 跳过注释
            if self.skip_comment():
                continue

            ch = self.text[self.pos]

            # 数字
            if ch.isdigit():
                self.tokens.append(self.read_number())
                continue

            # 字符串
            if ch == "'":
                self.tokens.append(self.read_string())
                continue

            # 双引号标识符
            if ch == '"':
                self.tokens.append(self.read_quoted_identifier())
                continue

            # 标识符或关键字
            if ch.isalpha() or ch == '_':
                self.tokens.append(self.read_identifier())
                continue

            # 运算符和分隔符
            start_col = self.column

            if ch == '=':
                self.advance()
                self.tokens.append(Token(TokenType.EQ, '=', self.line, start_col))
            elif ch == '!':
                self.advance()
                if self.pos < len(self.text) and self.text[self.pos] == '=':
                    self.advance()
                    self.tokens.append(Token(TokenType.NEQ, '!=', self.line, start_col))
                else:
                    raise self.error(f"意外字符: !")
            elif ch == '<':
                self.advance()
                if self.pos < len(self.text):
                    if self.text[self.pos] == '=':
                        self.advance()
                        self.tokens.append(Token(TokenType.LTE, '<=', self.line, start_col))
                    elif self.text[self.pos] == '>':
                        self.advance()
                        self.tokens.append(Token(TokenType.NEQ, '<>', self.line, start_col))
                    else:
                        self.tokens.append(Token(TokenType.LT, '<', self.line, start_col))
                else:
                    self.tokens.append(Token(TokenType.LT, '<', self.line, start_col))
            elif ch == '>':
                self.advance()
                if self.pos < len(self.text) and self.text[self.pos] == '=':
                    self.advance()
                    self.tokens.append(Token(TokenType.GTE, '>=', self.line, start_col))
                else:
                    self.tokens.append(Token(TokenType.GT, '>', self.line, start_col))
            elif ch == '+':
                self.advance()
                self.tokens.append(Token(TokenType.PLUS, '+', self.line, start_col))
            elif ch == '-':
                self.advance()
                self.tokens.append(Token(TokenType.MINUS, '-', self.line, start_col))
            elif ch == '*':
                self.advance()
                self.tokens.append(Token(TokenType.STAR, '*', self.line, start_col))
            elif ch == '/':
                self.advance()
                self.tokens.append(Token(TokenType.DIVIDE, '/', self.line, start_col))
            elif ch == '%':
                self.advance()
                self.tokens.append(Token(TokenType.MODULO, '%', self.line, start_col))
            elif ch == '(':
                self.advance()
                self.tokens.append(Token(TokenType.LPAREN, '(', self.line, start_col))
            elif ch == ')':
                self.advance()
                self.tokens.append(Token(TokenType.RPAREN, ')', self.line, start_col))
            elif ch == ',':
                self.advance()
                self.tokens.append(Token(TokenType.COMMA, ',', self.line, start_col))
            elif ch == ';':
                self.advance()
                self.tokens.append(Token(TokenType.SEMICOLON, ';', self.line, start_col))
            elif ch == '.':
                self.advance()
                self.tokens.append(Token(TokenType.DOT, '.', self.line, start_col))
            elif ch == '?':
                self.advance()
                self.tokens.append(Token(TokenType.PARAM, '?', self.line, start_col))
            else:
                raise self.error(f"意外字符: {ch}")

        self.tokens.append(Token(TokenType.EOF, '', self.line, self.column))
        return self.tokens


def tokenize(sql: str) -> List[Token]:
    """便捷函数：将 SQL 字符串转换为 Token 序列"""
    lexer = Lexer(sql)
    return lexer.tokenize()
