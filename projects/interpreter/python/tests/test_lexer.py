"""
词法分析器测试
"""

import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.lexer import Lexer, LexerError
from src.token import TokenType


class TestLexer:
    """词法分析器测试"""

    def _tokenize(self, source: str) -> list:
        """辅助方法：获取token类型列表"""
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        return [(t.type, t.literal) for t in tokens]

    def test_single_tokens(self):
        """测试单字符token"""
        source = "+-*/%(){}[],;:.="
        tokens = self._tokenize(source)
        expected = [
            (TokenType.PLUS, "+"),
            (TokenType.MINUS, "-"),
            (TokenType.STAR, "*"),
            (TokenType.SLASH, "/"),
            (TokenType.PERCENT, "%"),
            (TokenType.LPAREN, "("),
            (TokenType.RPAREN, ")"),
            (TokenType.LBRACE, "{"),
            (TokenType.RBRACE, "}"),
            (TokenType.LBRACKET, "["),
            (TokenType.RBRACKET, "]"),
            (TokenType.COMMA, ","),
            (TokenType.SEMICOLON, ";"),
            (TokenType.COLON, ":"),
            (TokenType.DOT, "."),
            (TokenType.ASSIGN, "="),
            (TokenType.EOF, ""),
        ]
        assert tokens == expected

    def test_double_tokens(self):
        """测试双字符token"""
        source = "== != <= >= += -= ** && ||"
        tokens = self._tokenize(source)
        expected = [
            (TokenType.EQ, "=="),
            (TokenType.NOT_EQ, "!="),
            (TokenType.LTE, "<="),
            (TokenType.GTE, ">="),
            (TokenType.PLUS_ASSIGN, "+="),
            (TokenType.MINUS_ASSIGN, "-="),
            (TokenType.POWER, "**"),
            (TokenType.AND, "&&"),
            (TokenType.OR, "||"),
            (TokenType.EOF, ""),
        ]
        assert tokens == expected

    def test_numbers(self):
        """测试数字字面量"""
        source = "42 3.14 0 100.0"
        tokens = self._tokenize(source)
        expected = [
            (TokenType.NUMBER, "42"),
            (TokenType.NUMBER, "3.14"),
            (TokenType.NUMBER, "0"),
            (TokenType.NUMBER, "100.0"),
            (TokenType.EOF, ""),
        ]
        assert tokens == expected

    def test_strings(self):
        """测试字符串字面量"""
        source = '"hello" "world" "escape\\"test"'
        tokens = self._tokenize(source)
        assert tokens[0] == (TokenType.STRING, "hello")
        assert tokens[1] == (TokenType.STRING, "world")
        assert tokens[2] == (TokenType.STRING, 'escape"test')

    def test_string_escape_sequences(self):
        """测试字符串转义序列"""
        source = '"line1\\nline2" "tab\\there"'
        tokens = self._tokenize(source)
        assert tokens[0] == (TokenType.STRING, "line1\nline2")
        assert tokens[1] == (TokenType.STRING, "tab\there")

    def test_keywords(self):
        """测试关键字"""
        source = "let if else elif while for in fn return break continue true false null and or not"
        tokens = self._tokenize(source)
        expected_types = [
            TokenType.LET, TokenType.IF, TokenType.ELSE, TokenType.ELIF,
            TokenType.WHILE, TokenType.FOR, TokenType.IN, TokenType.FN,
            TokenType.RETURN, TokenType.BREAK, TokenType.CONTINUE,
            TokenType.TRUE, TokenType.FALSE, TokenType.NULL,
            TokenType.AND, TokenType.OR, TokenType.NOT,
            TokenType.EOF,
        ]
        assert [t[0] for t in tokens] == expected_types

    def test_identifiers(self):
        """测试标识符"""
        source = "x foo_bar myVar count2"
        tokens = self._tokenize(source)
        expected = [
            (TokenType.IDENT, "x"),
            (TokenType.IDENT, "foo_bar"),
            (TokenType.IDENT, "myVar"),
            (TokenType.IDENT, "count2"),
            (TokenType.EOF, ""),
        ]
        assert tokens == expected

    def test_comments(self):
        """测试注释"""
        source = "5 // comment\n10"
        tokens = self._tokenize(source)
        assert tokens[0] == (TokenType.NUMBER, "5")
        assert tokens[1] == (TokenType.NUMBER, "10")

    def test_multiline_comments(self):
        """测试多行注释"""
        source = "5 /* this is\na comment */ 10"
        tokens = self._tokenize(source)
        assert tokens[0] == (TokenType.NUMBER, "5")
        assert tokens[1] == (TokenType.NUMBER, "10")

    def test_line_numbers(self):
        """测试行号跟踪"""
        source = "let\nx\n= 5;"
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        assert tokens[0].line == 1   # let
        assert tokens[1].line == 2   # x
        assert tokens[2].line == 3   # =
        assert tokens[3].line == 3   # 5

    def test_error_on_unterminated_string(self):
        """测试未终止字符串错误"""
        with pytest.raises(LexerError):
            Lexer('"unterminated').tokenize()

    def test_error_on_unexpected_char(self):
        """测试意外字符错误"""
        with pytest.raises(LexerError):
            Lexer("5 @ 3").tokenize()

    def test_complex_expression(self):
        """测试复杂表达式"""
        source = 'let result = (5 + 3) * 2;'
        tokens = self._tokenize(source)
        expected = [
            (TokenType.LET, "let"),
            (TokenType.IDENT, "result"),
            (TokenType.ASSIGN, "="),
            (TokenType.LPAREN, "("),
            (TokenType.NUMBER, "5"),
            (TokenType.PLUS, "+"),
            (TokenType.NUMBER, "3"),
            (TokenType.RPAREN, ")"),
            (TokenType.STAR, "*"),
            (TokenType.NUMBER, "2"),
            (TokenType.SEMICOLON, ";"),
            (TokenType.EOF, ""),
        ]
        assert tokens == expected
