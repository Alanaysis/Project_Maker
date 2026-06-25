"""
查询执行器测试
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.parser import parse_sql
from src.executor import Executor, Column, Table, QueryResult, ExecutionError
from src.ast_nodes import *


class TestExecutor:
    """查询执行器测试"""

    def setup_method(self):
        """测试前准备"""
        self.executor = Executor()

        # 创建 users 表
        users_table = self.executor.create_table("users", [
            Column("id", "integer"),
            Column("name", "text"),
            Column("email", "text"),
            Column("age", "integer"),
            Column("active", "boolean"),
        ])
        users_table.add_row({"id": 1, "name": "Alice", "email": "alice@example.com", "age": 25, "active": True})
        users_table.add_row({"id": 2, "name": "Bob", "email": "bob@example.com", "age": 30, "active": True})
        users_table.add_row({"id": 3, "name": "Charlie", "email": "charlie@example.com", "age": 35, "active": False})
        users_table.add_row({"id": 4, "name": "David", "email": None, "age": 28, "active": True})

        # 创建 orders 表
        orders_table = self.executor.create_table("orders", [
            Column("id", "integer"),
            Column("user_id", "integer"),
            Column("amount", "float"),
            Column("status", "text"),
        ])
        orders_table.add_row({"id": 1, "user_id": 1, "amount": 100.0, "status": "completed"})
        orders_table.add_row({"id": 2, "user_id": 1, "amount": 200.0, "status": "completed"})
        orders_table.add_row({"id": 3, "user_id": 2, "amount": 150.0, "status": "pending"})
        orders_table.add_row({"id": 4, "user_id": 3, "amount": 300.0, "status": "completed"})

    def test_select_all(self):
        """测试 SELECT *"""
        ast = parse_sql("SELECT * FROM users")
        result = self.executor.execute(ast)
        assert len(result.rows) == 4
        assert "id" in result.columns
        assert "name" in result.columns

    def test_select_columns(self):
        """测试 SELECT 指定列"""
        ast = parse_sql("SELECT id, name FROM users")
        result = self.executor.execute(ast)
        assert len(result.rows) == 4
        assert result.columns == ["id", "name"]

    def test_select_where_eq(self):
        """测试 WHERE ="""
        ast = parse_sql("SELECT * FROM users WHERE id = 1")
        result = self.executor.execute(ast)
        assert len(result.rows) == 1
        assert result.rows[0][0] == 1

    def test_select_where_neq(self):
        """测试 WHERE <>"""
        ast = parse_sql("SELECT * FROM users WHERE id <> 1")
        result = self.executor.execute(ast)
        assert len(result.rows) == 3

    def test_select_where_lt(self):
        """测试 WHERE <"""
        ast = parse_sql("SELECT * FROM users WHERE age < 30")
        result = self.executor.execute(ast)
        assert len(result.rows) == 2

    def test_select_where_gt(self):
        """测试 WHERE >"""
        ast = parse_sql("SELECT * FROM users WHERE age > 30")
        result = self.executor.execute(ast)
        assert len(result.rows) == 1

    def test_select_where_and(self):
        """测试 WHERE AND"""
        ast = parse_sql("SELECT * FROM users WHERE age > 25 AND active = true")
        result = self.executor.execute(ast)
        assert len(result.rows) == 2

    def test_select_where_or(self):
        """测试 WHERE OR"""
        ast = parse_sql("SELECT * FROM users WHERE age < 26 OR age > 34")
        result = self.executor.execute(ast)
        assert len(result.rows) == 2

    def test_select_where_in(self):
        """测试 WHERE IN"""
        ast = parse_sql("SELECT * FROM users WHERE id IN (1, 3)")
        result = self.executor.execute(ast)
        assert len(result.rows) == 2

    def test_select_where_between(self):
        """测试 WHERE BETWEEN"""
        ast = parse_sql("SELECT * FROM users WHERE age BETWEEN 25 AND 30")
        result = self.executor.execute(ast)
        assert len(result.rows) == 3

    def test_select_where_like(self):
        """测试 WHERE LIKE"""
        ast = parse_sql("SELECT * FROM users WHERE name LIKE 'A%'")
        result = self.executor.execute(ast)
        assert len(result.rows) == 1
        assert result.rows[0][1] == "Alice"

    def test_select_where_is_null(self):
        """测试 WHERE IS NULL"""
        ast = parse_sql("SELECT * FROM users WHERE email IS NULL")
        result = self.executor.execute(ast)
        assert len(result.rows) == 1
        assert result.rows[0][0] == 4

    def test_select_where_is_not_null(self):
        """测试 WHERE IS NOT NULL"""
        ast = parse_sql("SELECT * FROM users WHERE email IS NOT NULL")
        result = self.executor.execute(ast)
        assert len(result.rows) == 3

    def test_select_inner_join(self):
        """测试 INNER JOIN"""
        ast = parse_sql("""
            SELECT users.name, orders.amount
            FROM users
            INNER JOIN orders ON users.id = orders.user_id
        """)
        result = self.executor.execute(ast)
        assert len(result.rows) == 4

    def test_select_left_join(self):
        """测试 LEFT JOIN"""
        ast = parse_sql("""
            SELECT users.name, orders.amount
            FROM users
            LEFT JOIN orders ON users.id = orders.user_id
        """)
        result = self.executor.execute(ast)
        # 所有用户都应出现，包括没有订单的
        assert len(result.rows) >= 4

    def test_select_group_by(self):
        """测试 GROUP BY"""
        ast = parse_sql("""
            SELECT user_id, COUNT(*) AS order_count
            FROM orders
            GROUP BY user_id
        """)
        result = self.executor.execute(ast)
        assert len(result.rows) == 3  # 3 个不同的 user_id

    def test_select_group_by_sum(self):
        """测试 GROUP BY SUM"""
        ast = parse_sql("""
            SELECT user_id, SUM(amount) AS total
            FROM orders
            GROUP BY user_id
        """)
        result = self.executor.execute(ast)
        assert len(result.rows) == 3

    def test_select_order_by_asc(self):
        """测试 ORDER BY ASC"""
        ast = parse_sql("SELECT * FROM users ORDER BY age ASC")
        result = self.executor.execute(ast)
        ages = [row[3] for row in result.rows]
        assert ages == sorted(ages)

    def test_select_order_by_desc(self):
        """测试 ORDER BY DESC"""
        ast = parse_sql("SELECT * FROM users ORDER BY age DESC")
        result = self.executor.execute(ast)
        ages = [row[3] for row in result.rows]
        assert ages == sorted(ages, reverse=True)

    def test_select_limit(self):
        """测试 LIMIT"""
        ast = parse_sql("SELECT * FROM users LIMIT 2")
        result = self.executor.execute(ast)
        assert len(result.rows) == 2

    def test_select_limit_offset(self):
        """测试 LIMIT OFFSET"""
        ast = parse_sql("SELECT * FROM users ORDER BY id LIMIT 2 OFFSET 1")
        result = self.executor.execute(ast)
        assert len(result.rows) == 2
        assert result.rows[0][0] == 2  # 从第 2 条开始

    def test_select_distinct(self):
        """测试 DISTINCT"""
        ast = parse_sql("SELECT DISTINCT age FROM users")
        result = self.executor.execute(ast)
        ages = [row[0] for row in result.rows]
        assert len(ages) == len(set(ages))

    def test_insert_values(self):
        """测试 INSERT VALUES"""
        ast = parse_sql("INSERT INTO users (id, name, email, age, active) VALUES (5, 'Eve', 'eve@example.com', 22, true)")
        result = self.executor.execute(ast)
        assert result.affected_rows == 1

        # 验证插入成功
        ast2 = parse_sql("SELECT * FROM users WHERE id = 5")
        result2 = self.executor.execute(ast2)
        assert len(result2.rows) == 1

    def test_insert_multiple_values(self):
        """测试 INSERT 多行"""
        ast = parse_sql("""
            INSERT INTO users (id, name, email, age, active)
            VALUES (6, 'Frank', 'frank@example.com', 40, true),
                   (7, 'Grace', 'grace@example.com', 29, false)
        """)
        result = self.executor.execute(ast)
        assert result.affected_rows == 2

    def test_update(self):
        """测试 UPDATE"""
        ast = parse_sql("UPDATE users SET name = 'Alice Updated' WHERE id = 1")
        result = self.executor.execute(ast)
        assert result.affected_rows == 1

        # 验证更新成功
        ast2 = parse_sql("SELECT name FROM users WHERE id = 1")
        result2 = self.executor.execute(ast2)
        assert result2.rows[0][0] == "Alice Updated"

    def test_update_multiple_columns(self):
        """测试 UPDATE 多列"""
        ast = parse_sql("UPDATE users SET name = 'Bob Updated', age = 31 WHERE id = 2")
        result = self.executor.execute(ast)
        assert result.affected_rows == 2  # 2 个字段被更新

    def test_delete(self):
        """测试 DELETE"""
        ast = parse_sql("DELETE FROM users WHERE id = 3")
        result = self.executor.execute(ast)
        assert result.affected_rows == 1

        # 验证删除成功
        ast2 = parse_sql("SELECT * FROM users WHERE id = 3")
        result2 = self.executor.execute(ast2)
        assert len(result2.rows) == 0

    def test_delete_all(self):
        """测试 DELETE 全部"""
        ast = parse_sql("DELETE FROM users")
        result = self.executor.execute(ast)
        assert result.affected_rows == 4

    def test_select_no_from(self):
        """测试没有 FROM 的 SELECT"""
        ast = parse_sql("SELECT 1")
        result = self.executor.execute(ast)
        assert len(result.rows) == 1

    def test_select_alias(self):
        """测试 SELECT 别名"""
        ast = parse_sql("SELECT name AS user_name FROM users")
        result = self.executor.execute(ast)
        assert "user_name" in result.columns

    def test_select_table_alias(self):
        """测试表别名"""
        ast = parse_sql("SELECT u.name FROM users u WHERE u.id = 1")
        result = self.executor.execute(ast)
        assert len(result.rows) == 1

    def test_subquery_in(self):
        """测试子查询 IN"""
        ast = parse_sql("""
            SELECT * FROM users
            WHERE id IN (SELECT user_id FROM orders WHERE amount > 150)
        """)
        result = self.executor.execute(ast)
        assert len(result.rows) >= 1

    def test_create_table(self):
        """测试创建表"""
        table = self.executor.create_table("test_table", [
            Column("id", "integer"),
            Column("value", "text"),
        ])
        assert table.name == "test_table"
        assert len(table.columns) == 2

    def test_create_duplicate_table(self):
        """测试创建重复表"""
        with pytest.raises(ExecutionError):
            self.executor.create_table("users", [Column("id", "integer")])

    def test_get_nonexistent_table(self):
        """测试获取不存在的表"""
        with pytest.raises(ExecutionError):
            self.executor.get_table("nonexistent")

    def test_complex_query(self):
        """测试复杂查询"""
        ast = parse_sql("""
            SELECT u.name, COUNT(o.id) AS order_count, SUM(o.amount) AS total_amount
            FROM users u
            LEFT JOIN orders o ON u.id = o.user_id
            WHERE u.active = true
            GROUP BY u.name
            HAVING COUNT(o.id) >= 1
            ORDER BY total_amount DESC
            LIMIT 10
        """)
        result = self.executor.execute(ast)
        assert len(result.columns) == 3
        assert len(result.rows) >= 1

    def test_result_format(self):
        """测试结果格式化"""
        ast = parse_sql("SELECT id, name FROM users LIMIT 2")
        result = self.executor.execute(ast)
        formatted = str(result)
        assert "id" in formatted
        assert "name" in formatted

    def test_empty_result(self):
        """测试空结果"""
        ast = parse_sql("SELECT * FROM users WHERE id = 999")
        result = self.executor.execute(ast)
        assert len(result.rows) == 0
        assert str(result) == "Empty result set"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
