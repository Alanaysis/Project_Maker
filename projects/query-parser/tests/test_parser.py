"""
语法分析器测试
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.parser import Parser, parse_sql, ParseError
from src.ast_nodes import *


class TestParser:
    """语法分析器测试"""

    def test_simple_select(self):
        """测试简单 SELECT"""
        ast = parse_sql("SELECT * FROM users")
        assert isinstance(ast, SelectStatement)
        assert isinstance(ast.columns.columns[0], Star)
        assert ast.from_clause is not None
        assert ast.from_clause.tables[0].table_name == "users"

    def test_select_with_columns(self):
        """测试带列名的 SELECT"""
        ast = parse_sql("SELECT id, name, email FROM users")
        assert isinstance(ast, SelectStatement)
        assert len(ast.columns.columns) == 3
        assert isinstance(ast.columns.columns[0], ColumnRef)
        assert ast.columns.columns[0].column == "id"

    def test_select_with_alias(self):
        """测试带别名的 SELECT"""
        ast = parse_sql("SELECT id AS user_id, name AS user_name FROM users")
        assert isinstance(ast, SelectStatement)
        assert ast.columns.columns[0].alias == "user_id"
        assert ast.columns.columns[1].alias == "user_name"

    def test_select_distinct(self):
        """测试 DISTINCT"""
        ast = parse_sql("SELECT DISTINCT department FROM employees")
        assert isinstance(ast, SelectStatement)
        assert ast.columns.distinct is True

    def test_select_with_where(self):
        """测试 WHERE 子句"""
        ast = parse_sql("SELECT * FROM users WHERE id = 1")
        assert isinstance(ast, SelectStatement)
        assert ast.where_clause is not None
        assert isinstance(ast.where_clause.condition, CompareExpr)
        assert ast.where_clause.condition.op == '='

    def test_where_and(self):
        """测试 WHERE AND"""
        ast = parse_sql("SELECT * FROM t WHERE a = 1 AND b = 2")
        assert isinstance(ast.where_clause.condition, AndExpr)

    def test_where_or(self):
        """测试 WHERE OR"""
        ast = parse_sql("SELECT * FROM t WHERE a = 1 OR b = 2")
        assert isinstance(ast.where_clause.condition, OrExpr)

    def test_where_not(self):
        """测试 WHERE NOT"""
        ast = parse_sql("SELECT * FROM t WHERE NOT active")
        assert isinstance(ast.where_clause.condition, NotExpr)

    def test_where_in(self):
        """测试 WHERE IN"""
        ast = parse_sql("SELECT * FROM t WHERE status IN (1, 2, 3)")
        assert isinstance(ast.where_clause.condition, InExpr)
        assert len(ast.where_clause.condition.values) == 3

    def test_where_between(self):
        """测试 WHERE BETWEEN"""
        ast = parse_sql("SELECT * FROM t WHERE age BETWEEN 18 AND 65")
        assert isinstance(ast.where_clause.condition, BetweenExpr)

    def test_where_like(self):
        """测试 WHERE LIKE"""
        ast = parse_sql("SELECT * FROM t WHERE name LIKE '%john%'")
        assert isinstance(ast.where_clause.condition, LikeExpr)

    def test_where_is_null(self):
        """测试 WHERE IS NULL"""
        ast = parse_sql("SELECT * FROM t WHERE email IS NULL")
        assert isinstance(ast.where_clause.condition, IsNullExpr)
        assert ast.where_clause.condition.is_null is True

    def test_where_is_not_null(self):
        """测试 WHERE IS NOT NULL"""
        ast = parse_sql("SELECT * FROM t WHERE email IS NOT NULL")
        assert isinstance(ast.where_clause.condition, IsNullExpr)
        assert ast.where_clause.condition.is_null is False

    def test_select_with_join(self):
        """测试 JOIN"""
        ast = parse_sql("SELECT * FROM users u INNER JOIN orders o ON u.id = o.user_id")
        assert isinstance(ast, SelectStatement)
        assert ast.from_clause is not None
        assert len(ast.from_clause.joins) == 1
        join = ast.from_clause.joins[0]
        assert join.join_type == JoinType.INNER
        assert join.table.table_name == "orders"

    def test_left_join(self):
        """测试 LEFT JOIN"""
        ast = parse_sql("SELECT * FROM users LEFT JOIN orders ON users.id = orders.user_id")
        join = ast.from_clause.joins[0]
        assert join.join_type == JoinType.LEFT

    def test_right_join(self):
        """测试 RIGHT JOIN"""
        ast = parse_sql("SELECT * FROM users RIGHT JOIN orders ON users.id = orders.user_id")
        join = ast.from_clause.joins[0]
        assert join.join_type == JoinType.RIGHT

    def test_multiple_joins(self):
        """测试多表 JOIN"""
        sql = """SELECT * FROM users u
                 INNER JOIN orders o ON u.id = o.user_id
                 INNER JOIN products p ON o.product_id = p.id"""
        ast = parse_sql(sql)
        assert len(ast.from_clause.joins) == 2

    def test_group_by(self):
        """测试 GROUP BY"""
        ast = parse_sql("SELECT department, COUNT(*) FROM employees GROUP BY department")
        assert ast.group_by is not None
        assert len(ast.group_by.columns) == 1

    def test_group_by_multiple(self):
        """测试多列 GROUP BY"""
        ast = parse_sql("SELECT a, b, COUNT(*) FROM t GROUP BY a, b")
        assert len(ast.group_by.columns) == 2

    def test_having(self):
        """测试 HAVING"""
        ast = parse_sql("SELECT dept, COUNT(*) FROM emp GROUP BY dept HAVING COUNT(*) > 5")
        assert ast.having is not None
        assert isinstance(ast.having.condition, CompareExpr)

    def test_order_by(self):
        """测试 ORDER BY"""
        ast = parse_sql("SELECT * FROM users ORDER BY name")
        assert ast.order_by is not None
        assert len(ast.order_by.items) == 1
        assert ast.order_by.items[0].direction == SortDirection.ASC

    def test_order_by_desc(self):
        """测试 ORDER BY DESC"""
        ast = parse_sql("SELECT * FROM users ORDER BY name DESC")
        assert ast.order_by.items[0].direction == SortDirection.DESC

    def test_order_by_multiple(self):
        """测试多列 ORDER BY"""
        ast = parse_sql("SELECT * FROM users ORDER BY name ASC, id DESC")
        assert len(ast.order_by.items) == 2
        assert ast.order_by.items[0].direction == SortDirection.ASC
        assert ast.order_by.items[1].direction == SortDirection.DESC

    def test_limit(self):
        """测试 LIMIT"""
        ast = parse_sql("SELECT * FROM users LIMIT 10")
        assert ast.limit is not None
        assert ast.limit.limit == 10

    def test_limit_offset(self):
        """测试 LIMIT OFFSET"""
        ast = parse_sql("SELECT * FROM users LIMIT 10 OFFSET 20")
        assert ast.limit.limit == 10
        assert ast.limit.offset == 20

    def test_insert_values(self):
        """测试 INSERT VALUES"""
        ast = parse_sql("INSERT INTO users (id, name) VALUES (1, 'John')")
        assert isinstance(ast, InsertStatement)
        assert ast.table.table_name == "users"
        assert len(ast.columns) == 2
        assert ast.values is not None
        assert len(ast.values.values) == 1

    def test_insert_multiple_values(self):
        """测试 INSERT 多行 VALUES"""
        ast = parse_sql("INSERT INTO users (id, name) VALUES (1, 'John'), (2, 'Jane')")
        assert len(ast.values.values) == 2

    def test_insert_select(self):
        """测试 INSERT SELECT"""
        ast = parse_sql("INSERT INTO archive SELECT * FROM users WHERE active = 0")
        assert isinstance(ast, InsertStatement)
        assert ast.select is not None

    def test_update(self):
        """测试 UPDATE"""
        ast = parse_sql("UPDATE users SET name = 'Jane' WHERE id = 1")
        assert isinstance(ast, UpdateStatement)
        assert ast.table.table_name == "users"
        assert ast.set_clause is not None
        assert len(ast.set_clause.assignments) == 1
        assert ast.where_clause is not None

    def test_update_multiple_set(self):
        """测试 UPDATE 多列 SET"""
        ast = parse_sql("UPDATE users SET name = 'Jane', email = 'jane@example.com' WHERE id = 1")
        assert len(ast.set_clause.assignments) == 2

    def test_delete(self):
        """测试 DELETE"""
        ast = parse_sql("DELETE FROM users WHERE id = 1")
        assert isinstance(ast, DeleteStatement)
        assert ast.table.table_name == "users"
        assert ast.where_clause is not None

    def test_delete_all(self):
        """测试 DELETE 全部"""
        ast = parse_sql("DELETE FROM users")
        assert isinstance(ast, DeleteStatement)
        assert ast.where_clause is None

    def test_aggregate_functions(self):
        """测试聚合函数"""
        ast = parse_sql("SELECT COUNT(*), SUM(amount), AVG(price), MIN(age), MAX(score) FROM t")
        assert isinstance(ast, SelectStatement)
        funcs = [c for c in ast.columns.columns if isinstance(c, FuncCall)]
        assert len(funcs) == 5

    def test_count_distinct(self):
        """测试 COUNT DISTINCT"""
        ast = parse_sql("SELECT COUNT(DISTINCT department) FROM employees")
        func = ast.columns.columns[0]
        assert isinstance(func, FuncCall)
        assert func.distinct is True

    def test_subquery_in_where(self):
        """测试子查询 IN"""
        ast = parse_sql("SELECT * FROM users WHERE id IN (SELECT user_id FROM orders)")
        assert isinstance(ast.where_clause.condition, InExpr)
        assert ast.where_clause.condition.subquery is not None

    def test_exists_subquery(self):
        """测试 EXISTS 子查询"""
        ast = parse_sql("SELECT * FROM users WHERE EXISTS (SELECT 1 FROM orders WHERE orders.user_id = users.id)")
        assert isinstance(ast.where_clause.condition, ExistsExpr)

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
        ast = parse_sql(sql)
        assert isinstance(ast, SelectStatement)
        assert ast.from_clause is not None
        assert len(ast.from_clause.joins) == 1
        assert ast.where_clause is not None
        assert ast.group_by is not None
        assert ast.having is not None
        assert ast.order_by is not None
        assert ast.limit is not None

    def test_parenthesized_expression(self):
        """测试括号表达式"""
        ast = parse_sql("SELECT * FROM t WHERE (a = 1 OR b = 2) AND c = 3")
        condition = ast.where_clause.condition
        assert isinstance(condition, AndExpr)
        assert isinstance(condition.left, OrExpr)

    def test_arithmetic_expression(self):
        """测试算术表达式"""
        ast = parse_sql("SELECT price * 1.1 + 10 FROM products")
        col = ast.columns.columns[0]
        assert isinstance(col, BinaryOp)

    def test_table_alias(self):
        """测试表别名"""
        ast = parse_sql("SELECT u.name FROM users u")
        assert ast.from_clause.tables[0].alias == "u"

    def test_table_with_schema(self):
        """测试带 schema 的表"""
        ast = parse_sql("SELECT * FROM public.users")
        assert ast.from_clause.tables[0].schema == "public"
        assert ast.from_clause.tables[0].table_name == "users"

    def test_column_with_table_prefix(self):
        """测试带表前缀的列"""
        ast = parse_sql("SELECT users.name FROM users")
        col = ast.columns.columns[0]
        assert isinstance(col, ColumnRef)
        assert col.table == "users"
        assert col.column == "name"

    def test_star_with_table_prefix(self):
        """测试表.*"""
        ast = parse_sql("SELECT users.* FROM users")
        star = ast.columns.columns[0]
        assert isinstance(star, Star)
        assert star.table == "users"

    def test_not_in(self):
        """测试 NOT IN"""
        ast = parse_sql("SELECT * FROM t WHERE status NOT IN (1, 2, 3)")
        assert isinstance(ast.where_clause.condition, InExpr)
        assert ast.where_clause.condition.not_in is True

    def test_not_between(self):
        """测试 NOT BETWEEN"""
        ast = parse_sql("SELECT * FROM t WHERE age NOT BETWEEN 18 AND 65")
        assert isinstance(ast.where_clause.condition, BetweenExpr)
        assert ast.where_clause.condition.not_between is True

    def test_not_like(self):
        """测试 NOT LIKE"""
        ast = parse_sql("SELECT * FROM t WHERE name NOT LIKE '%test%'")
        assert isinstance(ast.where_clause.condition, LikeExpr)
        assert ast.where_clause.condition.not_like is True

    def test_cross_join(self):
        """测试 CROSS JOIN"""
        ast = parse_sql("SELECT * FROM a CROSS JOIN b")
        join = ast.from_clause.joins[0]
        assert join.join_type == JoinType.CROSS

    def test_full_join(self):
        """测试 FULL JOIN"""
        ast = parse_sql("SELECT * FROM a FULL JOIN b ON a.id = b.id")
        join = ast.from_clause.joins[0]
        assert join.join_type == JoinType.FULL

    def test_semicolon_handling(self):
        """测试分号处理"""
        ast = parse_sql("SELECT * FROM users;")
        assert isinstance(ast, SelectStatement)

    def test_empty_query_error(self):
        """测试空查询错误"""
        with pytest.raises(ParseError):
            parse_sql("")

    def test_invalid_syntax_error(self):
        """测试语法错误"""
        with pytest.raises(ParseError):
            parse_sql("SELECT FROM")  # 缺少列名

    def test_missing_from_error(self):
        """测试缺少 FROM"""
        with pytest.raises(ParseError):
            parse_sql("SELECT * users")  # 缺少 FROM

    def test_where_comparison_operators(self):
        """测试各种比较运算符"""
        for op in ['=', '<>', '<', '>', '<=', '>=']:
            ast = parse_sql(f"SELECT * FROM t WHERE a {op} 1")
            condition = ast.where_clause.condition
            assert isinstance(condition, CompareExpr)
            assert condition.op == op


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
