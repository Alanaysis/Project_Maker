# 查询解析器产品文档

## 1. 产品概述

### 1.1 产品定位

查询解析器是一个轻量级的 SQL 解析和执行引擎，用于：
- 学习 SQL 解析原理
- 快速原型开发
- 测试 SQL 语句
- 嵌入式应用

### 1.2 目标用户

- 数据库开发者
- SQL 学习者
- 应用开发者
- 测试工程师

### 1.3 产品特点

- **纯 Python 实现**：无外部依赖
- **模块化设计**：易于扩展和维护
- **完整功能**：支持主要 SQL 功能
- **易于集成**：简单的 API 接口

## 2. 功能清单

### 2.1 核心功能

| 功能 | 状态 | 说明 |
|------|------|------|
| 词法分析 | ✅ 完成 | Token 识别、关键字识别 |
| 语法分析 | ✅ 完成 | SQL 语句解析、AST 构建 |
| SELECT 查询 | ✅ 完成 | 基本查询、WHERE、JOIN |
| INSERT 操作 | ✅ 完成 | 单行和批量插入 |
| UPDATE 操作 | ✅ 完成 | 数据更新 |
| DELETE 操作 | ✅ 完成 | 数据删除 |
| GROUP BY | ✅ 完成 | 分组聚合 |
| ORDER BY | ✅ 完成 | 排序 |
| LIMIT | ✅ 完成 | 分页 |
| 查询优化 | ✅ 完成 | 常量折叠、表达式简化 |

### 2.2 扩展功能

| 功能 | 状态 | 说明 |
|------|------|------|
| 子查询 | ✅ 完成 | IN 子查询、EXISTS |
| 聚合函数 | ✅ 完成 | COUNT、SUM、AVG、MIN、MAX |
| DISTINCT | ✅ 完成 | 去重 |
| 别名 | ✅ 完成 | 表别名、列别名 |
| 注释 | ✅ 完成 | 单行和多行注释 |

## 3. 使用指南

### 3.1 安装

```bash
# 克隆项目
git clone <repository>

# 进入项目目录
cd projects/query-parser

# 安装依赖
pip install -r requirements.txt
```

### 3.2 基本使用

```python
from src.parser import parse_sql
from src.executor import Executor, Column

# 创建执行器
executor = Executor()

# 创建表
users = executor.create_table("users", [
    Column("id", "integer"),
    Column("name", "text"),
    Column("age", "integer"),
])

# 插入数据
users.add_row({"id": 1, "name": "Alice", "age": 25})
users.add_row({"id": 2, "name": "Bob", "age": 30})

# 执行查询
ast = parse_sql("SELECT * FROM users WHERE age > 25")
result = executor.execute(ast)

print(result)
```

### 3.3 API 参考

#### 词法分析器

```python
from src.lexer import tokenize, Lexer, TokenType

# 使用便捷函数
tokens = tokenize("SELECT * FROM users")

# 使用类
lexer = Lexer("SELECT * FROM users")
tokens = lexer.tokenize()

# Token 属性
for token in tokens:
    print(f"类型: {token.type}, 值: {token.value}, 位置: {token.line}:{token.column}")
```

#### 语法分析器

```python
from src.parser import parse_sql, Parser

# 使用便捷函数
ast = parse_sql("SELECT * FROM users")

# 使用类
parser = Parser.from_sql("SELECT * FROM users")
ast = parser.parse()

# AST 节点类型
print(type(ast))  # SelectStatement
```

#### 执行器

```python
from src.executor import Executor, Column, Table

# 创建执行器
executor = Executor()

# 创建表
table = executor.create_table("users", [
    Column("id", "integer"),
    Column("name", "text"),
])

# 添加数据
table.add_row({"id": 1, "name": "Alice"})

# 执行查询
result = executor.execute(ast)

# 结果属性
print(result.columns)  # 列名列表
print(result.rows)     # 行数据
print(result.affected_rows)  # 受影响行数
```

#### 查询优化器

```python
from src.optimizer import optimize_query, QueryOptimizer

# 使用便捷函数
optimized_ast = optimize_query(ast)

# 使用类
optimizer = QueryOptimizer()
optimized_ast = optimizer.optimize(ast)
optimizations = optimizer.get_optimizations()
```

## 4. 示例代码

### 4.1 基本查询

```python
# SELECT * FROM users
ast = parse_sql("SELECT * FROM users")
result = executor.execute(ast)

# SELECT id, name FROM users
ast = parse_sql("SELECT id, name FROM users")
result = executor.execute(ast)

# SELECT * FROM users WHERE age > 25
ast = parse_sql("SELECT * FROM users WHERE age > 25")
result = executor.execute(ast)
```

### 4.2 JOIN 查询

```python
# INNER JOIN
sql = """
    SELECT users.name, orders.amount
    FROM users
    INNER JOIN orders ON users.id = orders.user_id
"""
ast = parse_sql(sql)
result = executor.execute(ast)

# LEFT JOIN
sql = """
    SELECT users.name, orders.amount
    FROM users
    LEFT JOIN orders ON users.id = orders.user_id
"""
ast = parse_sql(sql)
result = executor.execute(ast)
```

### 4.3 聚合查询

```python
# GROUP BY
sql = """
    SELECT department, COUNT(*) AS count
    FROM employees
    GROUP BY department
"""
ast = parse_sql(sql)
result = executor.execute(ast)

# HAVING
sql = """
    SELECT department, COUNT(*) AS count
    FROM employees
    GROUP BY department
    HAVING COUNT(*) > 5
"""
ast = parse_sql(sql)
result = executor.execute(ast)
```

### 4.4 数据操作

```python
# INSERT
sql = "INSERT INTO users (id, name, age) VALUES (1, 'Alice', 25)"
ast = parse_sql(sql)
result = executor.execute(ast)
print(f"插入 {result.affected_rows} 行")

# UPDATE
sql = "UPDATE users SET name = 'Alice Updated' WHERE id = 1"
ast = parse_sql(sql)
result = executor.execute(ast)
print(f"更新 {result.affected_rows} 行")

# DELETE
sql = "DELETE FROM users WHERE id = 1"
ast = parse_sql(sql)
result = executor.execute(ast)
print(f"删除 {result.affected_rows} 行")
```

## 5. 最佳实践

### 5.1 性能优化

1. **使用索引**：为常用查询列创建索引
2. **限制结果集**：使用 LIMIT 减少数据传输
3. **避免 SELECT ***：只查询需要的列
4. **批量操作**：使用批量 INSERT 减少开销

### 5.2 错误处理

```python
from src.parser import parse_sql, ParseError
from src.executor import ExecutionError

try:
    ast = parse_sql("SELECT * FROM users")
    result = executor.execute(ast)
except ParseError as e:
    print(f"语法错误: {e}")
except ExecutionError as e:
    print(f"执行错误: {e}")
```

### 5.3 代码组织

```python
# 创建数据库管理类
class Database:
    def __init__(self):
        self.executor = Executor()

    def create_table(self, name, columns):
        return self.executor.create_table(name, columns)

    def query(self, sql):
        ast = parse_sql(sql)
        return self.executor.execute(ast)

# 使用
db = Database()
db.create_table("users", [Column("id", "integer"), Column("name", "text")])
result = db.query("SELECT * FROM users")
```

## 6. 常见问题

### 6.1 如何添加新表？

```python
# 创建表
table = executor.create_table("table_name", [
    Column("column1", "integer"),
    Column("column2", "text"),
    Column("column3", "float"),
])

# 添加数据
table.add_row({"column1": 1, "column2": "value", "column3": 3.14})
```

### 6.2 如何处理 NULL 值？

```python
# 插入 NULL
table.add_row({"id": 1, "name": None})

# 查询 NULL
ast = parse_sql("SELECT * FROM users WHERE name IS NULL")
result = executor.execute(ast)

# 查询非 NULL
ast = parse_sql("SELECT * FROM users WHERE name IS NOT NULL")
result = executor.execute(ast)
```

### 6.3 如何使用子查询？

```python
# IN 子查询
sql = """
    SELECT * FROM users
    WHERE id IN (SELECT user_id FROM orders WHERE amount > 100)
"""
ast = parse_sql(sql)
result = executor.execute(ast)

# EXISTS 子查询
sql = """
    SELECT * FROM users
    WHERE EXISTS (SELECT 1 FROM orders WHERE orders.user_id = users.id)
"""
ast = parse_sql(sql)
result = executor.execute(ast)
```

## 7. 版本历史

### v1.0.0 (当前版本)

- 完整的 SQL 解析功能
- 支持 SELECT, INSERT, UPDATE, DELETE
- 支持 WHERE, JOIN, GROUP BY, ORDER BY, LIMIT
- 支持聚合函数和子查询
- 基本的查询优化
- 完整的测试覆盖

## 8. 许可证

MIT License
