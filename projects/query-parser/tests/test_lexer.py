"""
词法分析器测试
"""

import pytest
import sys
import os

# 添加 src 目录到 Python 路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.lexer import Lexer, TokenType, tokenize


class TestLexer:
    """词法分析器测试"""

    def test_basic_select(self):
        """测试基本 SELECT 语句"""
        tokens = tokenize("SELECT * FROM users")
        assert tokens[0].type == TokenType.SELECT
        assert tokens[1].type == TokenType.STAR
        assert tokens[2].type == TokenType.FROM
        assert tokens[3].type == TokenType.IDENTIFIER
        assert tokens[3].value == "users"
        assert tokens[4].type == TokenType.EOF

    def test_select_with_columns(self):
        """测试带列名的 SELECT"""
        tokens = tokenize("SELECT id, name, email FROM users")
        assert tokens[0].type == TokenType.SELECT
        assert tokens[1].type == TokenType.IDENTIFIER
        assert tokens[1].value == "id"
        assert tokens[2].type == TokenType.COMMA
        assert tokens[3].type == TokenType.IDENTIFIER
        assert tokens[3].value == "name"
        assert tokens[4].type == TokenType.COMMA
        assert tokens[5].type == TokenType.IDENTIFIER
        assert tokens[5].value == "email"
        assert tokens[6].type == TokenType.FROM
        assert tokens[7].type == TokenType.IDENTIFIER
        assert tokens[7].value == "users"

    def test_where_clause(self):
        """测试 WHERE 子句"""
        tokens = tokenize("SELECT * FROM users WHERE id = 1")
        where_idx = next(i for i, t in enumerate(tokens) if t.type == TokenType.WHERE)
        assert tokens[where_idx + 1].type == TokenType.IDENTIFIER
        assert tokens[where_idx + 1].value == "id"
        assert tokens[where_idx + 2].type == TokenType.EQ
        assert tokens[where_idx + 3].type == TokenType.NUMBER
        assert tokens[where_idx + 3].value == "1"

    def test_comparison_operators(self):
        """测试比较运算符"""
        tokens = tokenize("SELECT * FROM t WHERE a = 1 AND b <> 2 AND c < 3 AND d > 4 AND e <= 5 AND f >= 6")
        # 查找所有比较运算符
        ops = [t for t in tokens if t.type in (TokenType.EQ, TokenType.NEQ, TokenType.LT,
                                                TokenType.GT, TokenType.LTE, TokenType.GTE)]
        assert len(ops) == 6
        assert ops[0].value == '='
        assert ops[1].value == '<>'
        assert ops[2].value == '<'
        assert ops[3].value == '>'
        assert ops[4].value == '<='
        assert ops[5].value == '>='

    def test_string_literal(self):
        """测试字符串字面量"""
        tokens = tokenize("SELECT * FROM users WHERE name = 'John'")
        string_tokens = [t for t in tokens if t.type == TokenType.STRING]
        assert len(string_tokens) == 1
        assert string_tokens[0].value == "John"

    def test_string_with_quotes(self):
        """测试带转义引号的字符串"""
        tokens = tokenize("SELECT * FROM users WHERE name = 'O''Brien'")
        string_tokens = [t for t in tokens if t.type == TokenType.STRING]
        assert len(string_tokens) == 1
        assert string_tokens[0].value == "O'Brien"

    def test_float_number(self):
        """测试浮点数"""
        tokens = tokenize("SELECT * FROM products WHERE price = 19.99")
        float_tokens = [t for t in tokens if t.type == TokenType.FLOAT]
        assert len(float_tokens) == 1
        assert float_tokens[0].value == "19.99"

    def test_insert_statement(self):
        """测试 INSERT 语句"""
        tokens = tokenize("INSERT INTO users (id, name) VALUES (1, 'John')")
        assert tokens[0].type == TokenType.INSERT
        assert tokens[1].type == TokenType.INTO
        assert tokens[2].type == TokenType.IDENTIFIER
        assert tokens[2].value == "users"
        assert tokens[3].type == TokenType.LPAREN
        # ... 继续验证

    def test_update_statement(self):
        """测试 UPDATE 语句"""
        tokens = tokenize("UPDATE users SET name = 'Jane' WHERE id = 1")
        assert tokens[0].type == TokenType.UPDATE
        assert tokens[1].type == TokenType.IDENTIFIER
        assert tokens[1].value == "users"
        assert tokens[2].type == TokenType.SET

    def test_delete_statement(self):
        """测试 DELETE 语句"""
        tokens = tokenize("DELETE FROM users WHERE id = 1")
        assert tokens[0].type == TokenType.DELETE
        assert tokens[1].type == TokenType.FROM
        assert tokens[2].type == TokenType.IDENTIFIER
        assert tokens[2].value == "users"

    def test_join_keywords(self):
        """测试 JOIN 关键字"""
        tokens = tokenize("SELECT * FROM a INNER JOIN b ON a.id = b.id")
        join_types = [t.type for t in tokens if t.type in (TokenType.INNER, TokenType.JOIN, TokenType.ON)]
        assert TokenType.INNER in join_types
        assert TokenType.JOIN in join_types
        assert TokenType.ON in join_types

    def test_left_join(self):
        """测试 LEFT JOIN"""
        tokens = tokenize("SELECT * FROM a LEFT JOIN b ON a.id = b.id")
        assert tokens[0].type == TokenType.SELECT
        # 找到 LEFT
        left_idx = next(i for i, t in enumerate(tokens) if t.type == TokenType.LEFT)
        assert tokens[left_idx + 1].type == TokenType.JOIN

    def test_group_by(self):
        """测试 GROUP BY"""
        tokens = tokenize("SELECT department, COUNT(*) FROM employees GROUP BY department")
        group_idx = next(i for i, t in enumerate(tokens) if t.type == TokenType.GROUP)
        assert tokens[group_idx + 1].type == TokenType.BY

    def test_order_by(self):
        """测试 ORDER BY"""
        tokens = tokenize("SELECT * FROM users ORDER BY name ASC, id DESC")
        order_idx = next(i for i, t in enumerate(tokens) if t.type == TokenType.ORDER)
        assert tokens[order_idx + 1].type == TokenType.BY
        # 找到 ASC 和 DESC
        assert any(t.type == TokenType.ASC for t in tokens)
        assert any(t.type == TokenType.DESC for t in tokens)

    def test_limit_offset(self):
        """测试 LIMIT 和 OFFSET"""
        tokens = tokenize("SELECT * FROM users LIMIT 10 OFFSET 20")
        limit_idx = next(i for i, t in enumerate(tokens) if t.type == TokenType.LIMIT)
        assert tokens[limit_idx + 1].type == TokenType.NUMBER
        assert tokens[limit_idx + 1].value == "10"
        offset_idx = next(i for i, t in enumerate(tokens) if t.type == TokenType.OFFSET)
        assert tokens[offset_idx + 1].type == TokenType.NUMBER
        assert tokens[offset_idx + 1].value == "20"

    def test_aggregate_functions(self):
        """测试聚合函数"""
        tokens = tokenize("SELECT COUNT(*), SUM(amount), AVG(price), MIN(age), MAX(score) FROM t")
        func_types = [t.type for t in tokens if t.type in (TokenType.COUNT, TokenType.SUM,
                                                           TokenType.AVG, TokenType.MIN, TokenType.MAX)]
        assert len(func_types) == 5

    def test_between(self):
        """测试 BETWEEN"""
        tokens = tokenize("SELECT * FROM t WHERE age BETWEEN 18 AND 65")
        between_idx = next(i for i, t in enumerate(tokens) if t.type == TokenType.BETWEEN)
        assert tokens[between_idx + 1].type == TokenType.NUMBER
        assert tokens[between_idx + 2].type == TokenType.AND
        assert tokens[between_idx + 3].type == TokenType.NUMBER

    def test_in_clause(self):
        """测试 IN"""
        tokens = tokenize("SELECT * FROM t WHERE status IN (1, 2, 3)")
        in_idx = next(i for i, t in enumerate(tokens) if t.type == TokenType.IN)
        assert tokens[in_idx - 1].type == TokenType.IDENTIFIER
        assert tokens[in_idx + 1].type == TokenType.LPAREN

    def test_like(self):
        """测试 LIKE"""
        tokens = tokenize("SELECT * FROM t WHERE name LIKE '%john%'")
        like_idx = next(i for i, t in enumerate(tokens) if t.type == TokenType.LIKE)
        assert tokens[like_idx - 1].type == TokenType.IDENTIFIER
        assert tokens[like_idx + 1].type == TokenType.STRING

    def test_is_null(self):
        """测试 IS NULL"""
        tokens = tokenize("SELECT * FROM t WHERE email IS NULL")
        is_idx = next(i for i, t in enumerate(tokens) if t.type == TokenType.IS)
        assert tokens[is_idx + 1].type == TokenType.NULL

    def test_is_not_null(self):
        """测试 IS NOT NULL"""
        tokens = tokenize("SELECT * FROM t WHERE email IS NOT NULL")
        is_idx = next(i for i, t in enumerate(tokens) if t.type == TokenType.IS)
        assert tokens[is_idx + 1].type == TokenType.NOT
        assert tokens[is_idx + 2].type == TokenType.NULL

    def test_distinct(self):
        """测试 DISTINCT"""
        tokens = tokenize("SELECT DISTINCT department FROM employees")
        assert tokens[0].type == TokenType.SELECT
        assert tokens[1].type == TokenType.DISTINCT

    def test_alias(self):
        """测试别名"""
        tokens = tokenize("SELECT name AS user_name FROM users u")
        as_tokens = [t for t in tokens if t.type == TokenType.AS]
        assert len(as_tokens) >= 1

    def test_comments(self):
        """测试注释"""
        sql = """-- 这是注释
        SELECT * FROM users
        /* 多行
           注释 */
        WHERE id = 1"""
        tokens = tokenize(sql)
        # 注释应该被跳过
        assert tokens[0].type == TokenType.SELECT
        assert not any(t.value == '--' for t in tokens)

    def test_complex_query(self):
        """测试复杂查询"""
        sql = """
        SELECT u.name, COUNT(o.id) AS order_count
        FROM users u
        LEFT JOIN orders o ON u.id = o.user_id
        WHERE u.status = 'active'
        GROUP BY u.name
        HAVING COUNT(o.id) > 5
        ORDER BY order_count DESC
        LIMIT 10
        """
        tokens = tokenize(sql)
        # 验证关键 token 存在
        token_types = [t.type for t in tokens]
        assert TokenType.SELECT in token_types
        assert TokenType.FROM in token_types
        assert TokenType.LEFT in token_types
        assert TokenType.JOIN in token_types
        assert TokenType.ON in token_types
        assert TokenType.WHERE in token_types
        assert TokenType.GROUP in token_types
        assert TokenType.HAVING in token_types
        assert TokenType.ORDER in token_types
        assert TokenType.LIMIT in token_types

    def test_semicolon(self):
        """测试分号"""
        tokens = tokenize("SELECT * FROM users;")
        assert tokens[-2].type == TokenType.SEMICOLON
        assert tokens[-1].type == TokenType.EOF

    def test_multiple_statements(self):
        """测试多语句（只解析第一个）"""
        tokens = tokenize("SELECT * FROM users; SELECT * FROM orders;")
        # 第一个语句后有分号
        semicolon_idx = next(i for i, t in enumerate(tokens) if t.type == TokenType.SEMICOLON)
        assert semicolon_idx > 0

    def test_quoted_identifier(self):
        """测试双引号标识符"""
        tokens = tokenize('SELECT "user name" FROM "user table"')
        id_tokens = [t for t in tokens if t.type == TokenType.IDENTIFIER]
        assert any(t.value == "user name" for t in id_tokens)
        assert any(t.value == "user table" for t in id_tokens)

    def test_arithmetic_operators(self):
        """测试算术运算符"""
        tokens = tokenize("SELECT price * 1.1 + 10 - 5 / 2 % 3 FROM products")
        ops = [t.type for t in tokens if t.type in (TokenType.STAR, TokenType.PLUS,
                                                     TokenType.MINUS, TokenType.DIVIDE, TokenType.MODULO)]
        assert len(ops) == 5

    def test_not_operator(self):
        """测试 NOT 运算符"""
        tokens = tokenize("SELECT * FROM t WHERE NOT active")
        not_idx = next(i for i, t in enumerate(tokens) if t.type == TokenType.NOT)
        assert tokens[not_idx + 1].type == TokenType.IDENTIFIER

    def test_exists(self):
        """测试 EXISTS"""
        tokens = tokenize("SELECT * FROM t WHERE EXISTS (SELECT 1 FROM orders)")
        exists_idx = next(i for i, t in enumerate(tokens) if t.type == TokenType.EXISTS)
        assert tokens[exists_idx + 1].type == TokenType.LPAREN
        assert tokens[exists_idx + 2].type == TokenType.SELECT

    def test_subquery(self):
        """测试子查询"""
        tokens = tokenize("SELECT * FROM (SELECT id FROM users) AS sub")
        # 子查询在括号中
        lparens = [i for i, t in enumerate(tokens) if t.type == TokenType.LPAREN]
        assert len(lparens) >= 1

    def test_empty_input(self):
        """测试空输入"""
        tokens = tokenize("")
        assert len(tokens) == 1
        assert tokens[0].type == TokenType.EOF

    def test_whitespace_only(self):
        """测试只有空白"""
        tokens = tokenize("   \t\n  ")
        assert len(tokens) == 1
        assert tokens[0].type == TokenType.EOF


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
