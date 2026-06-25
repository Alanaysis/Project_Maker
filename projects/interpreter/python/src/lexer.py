"""
词法分析器（Lexer）

将源代码字符流转换为Token流。
使用有限状态机逐字符扫描，识别关键字、标识符、数字、字符串等。
"""

from .token import Token, TokenType


class LexerError(Exception):
    """词法分析错误"""

    def __init__(self, message: str, line: int, column: int):
        super().__init__(f"[行 {line}, 列 {column}] 词法错误: {message}")
        self.line = line
        self.column = column


class Lexer:
    """
    词法分析器

    将源代码字符串转换为Token序列。
    支持：
    - 数字（整数和浮点数）
    - 字符串（双引号）
    - 标识符和关键字
    - 运算符和分隔符
    - 单行注释（//）和多行注释（/* */）
    """

    def __init__(self, source: str):
        self.source = source
        self.pos = 0           # 当前字符位置
        self.line = 1          # 当前行号
        self.column = 1        # 当前列号
        self.tokens: list[Token] = []

    def tokenize(self) -> list[Token]:
        """将源代码转换为Token列表"""
        while not self._is_at_end():
            self._skip_whitespace_and_comments()
            if self._is_at_end():
                break
            self._read_token()

        # 添加EOF token
        self.tokens.append(Token(TokenType.EOF, "", self.line, self.column))
        return self.tokens

    def _is_at_end(self) -> bool:
        return self.pos >= len(self.source)

    def _peek(self) -> str:
        """查看当前字符（不消耗）"""
        if self._is_at_end():
            return "\0"
        return self.source[self.pos]

    def _peek_next(self) -> str:
        """查看下一个字符"""
        if self.pos + 1 >= len(self.source):
            return "\0"
        return self.source[self.pos + 1]

    def _advance(self) -> str:
        """消耗并返回当前字符"""
        ch = self.source[self.pos]
        self.pos += 1
        if ch == "\n":
            self.line += 1
            self.column = 1
        else:
            self.column += 1
        return ch

    def _expect(self, expected: str) -> bool:
        """如果下一个字符匹配则消耗它"""
        if self._is_at_end() or self.source[self.pos] != expected:
            return False
        self._advance()
        return True

    def _add_token(self, token_type: TokenType, literal: str, line: int, column: int):
        """添加Token到列表"""
        self.tokens.append(Token(token_type, literal, line, column))

    def _skip_whitespace_and_comments(self):
        """跳过空白字符和注释"""
        while not self._is_at_end():
            ch = self._peek()
            if ch in (" ", "\t", "\r", "\n"):
                self._advance()
            elif ch == "/" and self._peek_next() == "/":
                # 单行注释
                while not self._is_at_end() and self._peek() != "\n":
                    self._advance()
            elif ch == "/" and self._peek_next() == "*":
                # 多行注释
                self._advance()  # /
                self._advance()  # *
                while not self._is_at_end():
                    if self._peek() == "*" and self._peek_next() == "/":
                        self._advance()  # *
                        self._advance()  # /
                        break
                    self._advance()
            else:
                break

    def _read_token(self):
        """读取下一个Token"""
        line, column = self.line, self.column
        ch = self._advance()

        match ch:
            # 单字符Token
            case "+":
                if self._expect("="):
                    self._add_token(TokenType.PLUS_ASSIGN, "+=", line, column)
                else:
                    self._add_token(TokenType.PLUS, "+", line, column)
            case "-":
                if self._expect("="):
                    self._add_token(TokenType.MINUS_ASSIGN, "-=", line, column)
                else:
                    self._add_token(TokenType.MINUS, "-", line, column)
            case "*":
                if self._expect("*"):
                    self._add_token(TokenType.POWER, "**", line, column)
                else:
                    self._add_token(TokenType.STAR, "*", line, column)
            case "/":
                self._add_token(TokenType.SLASH, "/", line, column)
            case "%":
                self._add_token(TokenType.PERCENT, "%", line, column)
            case "(":
                self._add_token(TokenType.LPAREN, "(", line, column)
            case ")":
                self._add_token(TokenType.RPAREN, ")", line, column)
            case "{":
                self._add_token(TokenType.LBRACE, "{", line, column)
            case "}":
                self._add_token(TokenType.RBRACE, "}", line, column)
            case "[":
                self._add_token(TokenType.LBRACKET, "[", line, column)
            case "]":
                self._add_token(TokenType.RBRACKET, "]", line, column)
            case ",":
                self._add_token(TokenType.COMMA, ",", line, column)
            case ";":
                self._add_token(TokenType.SEMICOLON, ";", line, column)
            case ":":
                self._add_token(TokenType.COLON, ":", line, column)
            case ".":
                self._add_token(TokenType.DOT, ".", line, column)

            # 可能是双字符的Token
            case "=":
                if self._expect("="):
                    self._add_token(TokenType.EQ, "==", line, column)
                else:
                    self._add_token(TokenType.ASSIGN, "=", line, column)
            case "!":
                if self._expect("="):
                    self._add_token(TokenType.NOT_EQ, "!=", line, column)
                else:
                    self._add_token(TokenType.NOT, "!", line, column)
            case "<":
                if self._expect("="):
                    self._add_token(TokenType.LTE, "<=", line, column)
                else:
                    self._add_token(TokenType.LT, "<", line, column)
            case ">":
                if self._expect("="):
                    self._add_token(TokenType.GTE, ">=", line, column)
                else:
                    self._add_token(TokenType.GT, ">", line, column)
            case "&":
                if self._expect("&"):
                    self._add_token(TokenType.AND, "&&", line, column)
                else:
                    raise LexerError(f"意外字符 '&'", line, column)
            case "|":
                if self._expect("|"):
                    self._add_token(TokenType.OR, "||", line, column)
                else:
                    raise LexerError(f"意外字符 '|'", line, column)

            # 字符串
            case '"':
                self._read_string(line, column)

            # 数字
            case _ if ch.isdigit():
                self._read_number(ch, line, column)

            # 标识符/关键字
            case _ if ch.isalpha() or ch == "_":
                self._read_identifier(ch, line, column)

            case _:
                raise LexerError(f"意外字符 '{ch}'", line, column)

    def _read_string(self, line: int, column: int):
        """读取字符串字面量"""
        parts: list[str] = []
        while not self._is_at_end() and self._peek() != '"':
            if self._peek() == "\\":
                self._advance()  # 跳过反斜杠
                escape = self._advance()
                escape_map = {
                    "n": "\n", "t": "\t", "r": "\r",
                    "\\": "\\", '"': '"',
                }
                parts.append(escape_map.get(escape, f"\\{escape}"))
            elif self._peek() == "\n":
                raise LexerError("未终止的字符串", line, column)
            else:
                parts.append(self._advance())

        if self._is_at_end():
            raise LexerError("未终止的字符串", line, column)

        self._advance()  # 消耗结束的 "
        self._add_token(TokenType.STRING, "".join(parts), line, column)

    def _read_number(self, first_char: str, line: int, column: int):
        """读取数字字面量"""
        num_chars = [first_char]
        is_float = False

        while not self._is_at_end() and (self._peek().isdigit() or self._peek() == "."):
            if self._peek() == ".":
                if is_float:
                    break  # 第二个点号停止
                is_float = True
            num_chars.append(self._advance())

        self._add_token(TokenType.NUMBER, "".join(num_chars), line, column)

    def _read_identifier(self, first_char: str, line: int, column: int):
        """读取标识符或关键字"""
        chars = [first_char]
        while not self._is_at_end() and (self._peek().isalnum() or self._peek() == "_"):
            chars.append(self._advance())

        literal = "".join(chars)
        token_type = Token.lookup_ident(literal)
        self._add_token(token_type, literal, line, column)
