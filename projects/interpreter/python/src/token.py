"""
Token类型定义

定义语言中所有可能的词法单元（Token）类型。
Token是词法分析的输出，语法分析的输入。
"""

from enum import Enum, auto
from dataclasses import dataclass
from typing import Any


class TokenType(Enum):
    """Token类型枚举"""

    # 特殊
    EOF = auto()
    ILLEGAL = auto()

    # 字面量
    NUMBER = auto()      # 42, 3.14
    STRING = auto()      # "hello"
    TRUE = auto()        # true
    FALSE = auto()       # false
    NULL = auto()        # null

    # 标识符
    IDENT = auto()       # 变量名、函数名

    # 运算符
    PLUS = auto()        # +
    MINUS = auto()       # -
    STAR = auto()        # *
    SLASH = auto()       # /
    PERCENT = auto()     # %
    POWER = auto()       # **

    # 赋值
    ASSIGN = auto()      # =
    PLUS_ASSIGN = auto() # +=
    MINUS_ASSIGN = auto()# -=

    # 比较
    EQ = auto()          # ==
    NOT_EQ = auto()      # !=
    LT = auto()          # <
    GT = auto()          # >
    LTE = auto()         # <=
    GTE = auto()         # >=

    # 逻辑
    AND = auto()         # and / &&
    OR = auto()          # or / ||
    NOT = auto()         # not / !

    # 分隔符
    LPAREN = auto()      # (
    RPAREN = auto()      # )
    LBRACE = auto()      # {
    RBRACE = auto()      # }
    LBRACKET = auto()    # [
    RBRACKET = auto()    # ]
    COMMA = auto()       # ,
    SEMICOLON = auto()   # ;
    COLON = auto()       # :
    DOT = auto()         # .

    # 关键字
    LET = auto()         # let
    IF = auto()          # if
    ELSE = auto()        # else
    WHILE = auto()       # while
    FOR = auto()         # for
    IN = auto()          # in
    FN = auto()          # fn
    RETURN = auto()      # return
    BREAK = auto()       # break
    CONTINUE = auto()    # continue
    ELIF = auto()        # elif


# 关键字映射
KEYWORDS: dict[str, TokenType] = {
    "let": TokenType.LET,
    "if": TokenType.IF,
    "else": TokenType.ELSE,
    "elif": TokenType.ELIF,
    "while": TokenType.WHILE,
    "for": TokenType.FOR,
    "in": TokenType.IN,
    "fn": TokenType.FN,
    "return": TokenType.RETURN,
    "break": TokenType.BREAK,
    "continue": TokenType.CONTINUE,
    "true": TokenType.TRUE,
    "false": TokenType.FALSE,
    "null": TokenType.NULL,
    "and": TokenType.AND,
    "or": TokenType.OR,
    "not": TokenType.NOT,
}


@dataclass(frozen=True)
class Token:
    """
    Token数据类

    Attributes:
        type: Token类型
        literal: Token的原始文本
        line: 所在行号
        column: 所在列号
    """

    type: TokenType
    literal: str
    line: int = 1
    column: int = 1

    def __repr__(self) -> str:
        return f"Token({self.type.name}, {self.literal!r}, {self.line}:{self.column})"

    def is_type(self, *types: TokenType) -> bool:
        """检查Token是否为指定类型之一"""
        return self.type in types

    @staticmethod
    def lookup_ident(ident: str) -> TokenType:
        """查找标识符是否为关键字"""
        return KEYWORDS.get(ident, TokenType.IDENT)
