#!/usr/bin/env python3
"""
查询解析器示例 - 演示各种 SQL 查询的解析和执行
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.parser import parse_sql
from src.executor import Executor, Column
from src.optimizer import QueryOptimizer


def demo_basic_queries():
    """演示基本查询"""
    print("=" * 60)
    print("基本查询演示")
    print("=" * 60)

    executor = Executor()

    # 创建 users 表
    users = executor.create_table("users", [
        Column("id", "integer"),
        Column("name", "text"),
        Column("email", "text"),
        Column("age", "integer"),
        Column("department", "text"),
    ])

    # 添加数据
    users.add_row({"id": 1, "name": "Alice", "email": "alice@example.com", "age": 25, "department": "Engineering"})
    users.add_row({"id": 2, "name": "Bob", "email": "bob@example.com", "age": 30, "department": "Marketing"})
    users.add_row({"id": 3, "name": "Charlie", "email": "charlie@example.com", "age": 35, "department": "Engineering"})
    users.add_row({"id": 4, "name": "David", "email": "david@example.com", "age": 28, "department": "Sales"})
    users.add_row({"id": 5, "name": "Eve", "email": "eve@example.com", "age": 22, "department": "Engineering"})

    queries = [
        "SELECT * FROM users",
        "SELECT id, name FROM users",
        "SELECT * FROM users WHERE age > 25",
        "SELECT * FROM users WHERE department = 'Engineering'",
        "SELECT * FROM users WHERE age BETWEEN 25 AND 30",
        "SELECT * FROM users WHERE name LIKE 'A%'",
        "SELECT * FROM users WHERE email IS NOT NULL",
    ]

    for sql in queries:
        print(f"\n查询: {sql}")
        ast = parse_sql(sql)
        result = executor.execute(ast)
        print(result)


def demo_joins():
    """演示 JOIN 查询"""
    print("\n" + "=" * 60)
    print("JOIN 查询演示")
    print("=" * 60)

    executor = Executor()

    # 创建 users 表
    users = executor.create_table("users", [
        Column("id", "integer"),
        Column("name", "text"),
    ])
    users.add_row({"id": 1, "name": "Alice"})
    users.add_row({"id": 2, "name": "Bob"})
    users.add_row({"id": 3, "name": "Charlie"})

    # 创建 orders 表
    orders = executor.create_table("orders", [
        Column("id", "integer"),
        Column("user_id", "integer"),
        Column("amount", "float"),
    ])
    orders.add_row({"id": 1, "user_id": 1, "amount": 100.0})
    orders.add_row({"id": 2, "user_id": 1, "amount": 200.0})
    orders.add_row({"id": 3, "user_id": 2, "amount": 150.0})

    queries = [
        """
        SELECT users.name, orders.amount
        FROM users
        INNER JOIN orders ON users.id = orders.user_id
        """,
        """
        SELECT users.name, orders.amount
        FROM users
        LEFT JOIN orders ON users.id = orders.user_id
        """,
    ]

    for sql in queries:
        print(f"\n查询: {sql.strip()}")
        ast = parse_sql(sql)
        result = executor.execute(ast)
        print(result)


def demo_aggregations():
    """演示聚合查询"""
    print("\n" + "=" * 60)
    print("聚合查询演示")
    print("=" * 60)

    executor = Executor()

    # 创建 sales 表
    sales = executor.create_table("sales", [
        Column("id", "integer"),
        Column("product", "text"),
        Column("category", "text"),
        Column("amount", "float"),
        Column("quantity", "integer"),
    ])

    sales.add_row({"id": 1, "product": "Laptop", "category": "Electronics", "amount": 999.99, "quantity": 1})
    sales.add_row({"id": 2, "product": "Phone", "category": "Electronics", "amount": 699.99, "quantity": 2})
    sales.add_row({"id": 3, "product": "Book", "category": "Education", "amount": 29.99, "quantity": 5})
    sales.add_row({"id": 4, "product": "Tablet", "category": "Electronics", "amount": 499.99, "quantity": 1})
    sales.add_row({"id": 5, "product": "Course", "category": "Education", "amount": 199.99, "quantity": 1})

    queries = [
        """
        SELECT category, COUNT(*) AS count, SUM(amount) AS total, AVG(amount) AS avg_amount
        FROM sales
        GROUP BY category
        """,
        """
        SELECT product, SUM(quantity) AS total_qty
        FROM sales
        GROUP BY product
        HAVING SUM(quantity) > 1
        """,
    ]

    for sql in queries:
        print(f"\n查询: {sql.strip()}")
        ast = parse_sql(sql)
        result = executor.execute(ast)
        print(result)


def demo_insert_update_delete():
    """演示 INSERT/UPDATE/DELETE"""
    print("\n" + "=" * 60)
    print("INSERT/UPDATE/DELETE 演示")
    print("=" * 60)

    executor = Executor()

    # 创建 products 表
    products = executor.create_table("products", [
        Column("id", "integer"),
        Column("name", "text"),
        Column("price", "float"),
        Column("stock", "integer"),
    ])

    # INSERT
    print("\n1. INSERT 数据")
    sql = "INSERT INTO products (id, name, price, stock) VALUES (1, 'Laptop', 999.99, 10)"
    ast = parse_sql(sql)
    result = executor.execute(ast)
    print(f"   插入: {result.affected_rows} 行")

    sql = """
        INSERT INTO products (id, name, price, stock)
        VALUES (2, 'Phone', 699.99, 20), (3, 'Tablet', 499.99, 15)
    """
    ast = parse_sql(sql)
    result = executor.execute(ast)
    print(f"   批量插入: {result.affected_rows} 行")

    # 查询验证
    ast = parse_sql("SELECT * FROM products")
    result = executor.execute(ast)
    print("\n   当前数据:")
    print(result)

    # UPDATE
    print("\n2. UPDATE 数据")
    sql = "UPDATE products SET price = 899.99 WHERE id = 1"
    ast = parse_sql(sql)
    result = executor.execute(ast)
    print(f"   更新: {result.affected_rows} 个字段")

    # 查询验证
    ast = parse_sql("SELECT * FROM products WHERE id = 1")
    result = executor.execute(ast)
    print("   更新后:")
    print(result)

    # DELETE
    print("\n3. DELETE 数据")
    sql = "DELETE FROM products WHERE id = 3"
    ast = parse_sql(sql)
    result = executor.execute(ast)
    print(f"   删除: {result.affected_rows} 行")

    # 查询验证
    ast = parse_sql("SELECT * FROM products")
    result = executor.execute(ast)
    print("\n   删除后:")
    print(result)


def demo_query_optimization():
    """演示查询优化"""
    print("\n" + "=" * 60)
    print("查询优化演示")
    print("=" * 60)

    optimizer = QueryOptimizer()

    queries = [
        "SELECT * FROM t WHERE 1 + 2 = 3",
        "SELECT * FROM t WHERE NOT NOT active",
        "SELECT * FROM t WHERE x + 0 = 10",
        "SELECT * FROM t WHERE y * 1 = 20",
        "SELECT * FROM t WHERE z * 0 = 0",
    ]

    for sql in queries:
        print(f"\n原始查询: {sql}")
        ast = parse_sql(sql)
        optimized = optimizer.optimize(ast)
        optimizations = optimizer.get_optimizations()
        print(f"优化后: {optimized}")
        if optimizations:
            print(f"应用的优化: {', '.join(optimizations)}")


def demo_parser_ast():
    """演示解析器 AST"""
    print("\n" + "=" * 60)
    print("AST 演示")
    print("=" * 60)

    queries = [
        "SELECT id, name FROM users WHERE age > 25",
        "INSERT INTO users (id, name) VALUES (1, 'John')",
        "UPDATE users SET name = 'Jane' WHERE id = 1",
        "DELETE FROM users WHERE id = 1",
        """
        SELECT u.name, COUNT(o.id)
        FROM users u
        LEFT JOIN orders o ON u.id = o.user_id
        WHERE u.active = true
        GROUP BY u.name
        HAVING COUNT(o.id) > 0
        ORDER BY u.name
        LIMIT 10
        """,
    ]

    for sql in queries:
        print(f"\nSQL: {sql.strip()}")
        ast = parse_sql(sql)
        print(f"类型: {type(ast).__name__}")
        print(f"AST: {ast}")


def main():
    """主函数"""
    print("查询解析器演示程序")
    print("=" * 60)

    demo_parser_ast()
    demo_basic_queries()
    demo_joins()
    demo_aggregations()
    demo_insert_update_delete()
    demo_query_optimization()

    print("\n" + "=" * 60)
    print("演示完成!")


if __name__ == "__main__":
    main()
