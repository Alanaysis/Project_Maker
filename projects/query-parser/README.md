# 查询解析器 (Query Parser)

一个用 Python 实现的完整 SQL 查询解析器，支持 SELECT、INSERT、UPDATE、DELETE 语句。

## 项目概述

本项目实现了一个完整的 SQL 查询解析器，展示了数据库查询处理的核心流程：

```
SQL 字符串 → 词法分析 → 语法分析 → AST → 查询优化 → 执行 → 结果
```

## 核心功能

### 1. 词法分析
- Token 定义：关键字、标识符、字面量、运算符
- 关键字识别：SELECT、FROM、WHERE 等 SQL 关键字
- 注释支持：单行 (-- 注释) 和多行 (/* 注释 */)

### 2. 语法分析
- SQL 语句解析：SELECT、INSERT、UPDATE、DELETE
- AST 构建：完整的抽象语法树
- 运算符优先级：正确的优先级处理

### 3. 查询类型
- **SELECT**：数据查询，支持 DISTINCT、别名
- **INSERT**：数据插入，支持批量插入
- **UPDATE**：数据更新
- **DELETE**：数据删除

### 4. 子句解析
- **WHERE**：条件过滤（=、<>、<、>、<=、>=、IN、BETWEEN、LIKE、IS NULL）
- **JOIN**：表连接（INNER、LEFT、RIGHT、FULL、CROSS）
- **GROUP BY**：分组聚合
- **ORDER BY**：排序（ASC、DESC）
- **HAVING**：分组条件
- **LIMIT/OFFSET**：分页

### 5. 高级功能
- 聚合函数：COUNT、SUM、AVG、MIN、MAX
- 子查询：IN 子查询、EXISTS 子查询
- 查询优化：常量折叠、表达式简化、谓词下推

## 项目结构

```
query-parser/
├── src/                        # 源代码
│   ├── __init__.py            # 包初始化
│   ├── lexer.py               # 词法分析器
│   ├── parser.py              # 语法分析器
│   ├── ast_nodes.py           # AST 节点定义
│   ├── optimizer.py           # 查询优化器
│   └── executor.py            # 查询执行器
├── tests/                      # 测试代码
│   ├── __init__.py
│   ├── test_lexer.py          # 词法分析器测试
│   ├── test_parser.py         # 语法分析器测试
│   └── test_executor.py       # 执行器测试
├── examples/                   # 示例代码
│   └── queries.py             # 查询示例
├── docs/                       # 文档
│   ├── 01_RESEARCH.md         # 研究文档
│   ├── 02_REQUIREMENTS.md     # 需求文档
│   ├── 03_DESIGN.md           # 设计文档
│   ├── 04_PRODUCT.md          # 产品文档
│   └── 05_DEVELOPMENT.md      # 开发文档
├── requirements.txt            # 依赖
└── README.md                   # 项目说明
```

## 快速开始

### 环境要求

- Python 3.8+
- pytest (测试)

### 安装和运行

```bash
# 进入项目目录
cd projects/query-parser

# 安装依赖
pip install -r requirements.txt

# 运行示例
python examples/queries.py
```

### 基本使用

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

### 运行测试

```bash
# 运行所有测试
pytest

# 运行特定测试
pytest tests/test_lexer.py
pytest tests/test_parser.py
pytest tests/test_executor.py

# 显示详细输出
pytest -v

# 显示覆盖率
pytest --cov=src
```

## SQL 语法

### SELECT 语句

```sql
-- 基本查询
SELECT * FROM users
SELECT id, name FROM users

-- 条件查询
SELECT * FROM users WHERE age > 25
SELECT * FROM users WHERE status IN (1, 2, 3)
SELECT * FROM users WHERE name LIKE 'A%'
SELECT * FROM users WHERE email IS NOT NULL

-- JOIN 查询
SELECT users.name, orders.amount
FROM users
INNER JOIN orders ON users.id = orders.user_id

-- 聚合查询
SELECT department, COUNT(*) AS count
FROM employees
GROUP BY department
HAVING COUNT(*) > 5

-- 排序和分页
SELECT * FROM users ORDER BY name ASC, id DESC
SELECT * FROM users LIMIT 10 OFFSET 20

-- 子查询
SELECT * FROM users WHERE id IN (SELECT user_id FROM orders)
SELECT * FROM users WHERE EXISTS (SELECT 1 FROM orders WHERE orders.user_id = users.id)
```

### INSERT 语句

```sql
-- 单行插入
INSERT INTO users (id, name, age) VALUES (1, 'Alice', 25)

-- 批量插入
INSERT INTO users (id, name, age) VALUES
    (1, 'Alice', 25),
    (2, 'Bob', 30),
    (3, 'Charlie', 35)

-- 子查询插入
INSERT INTO archive SELECT * FROM users WHERE active = 0
```

### UPDATE 语句

```sql
-- 更新单列
UPDATE users SET name = 'Jane' WHERE id = 1

-- 更新多列
UPDATE users SET name = 'Jane', age = 26 WHERE id = 1
```

### DELETE 语句

```sql
-- 条件删除
DELETE FROM users WHERE id = 1

-- 删除所有
DELETE FROM users
```

## 核心组件

### 1. Lexer（词法分析器）

将 SQL 字符串转换为 token 序列：

```python
from src.lexer import tokenize

tokens = tokenize("SELECT * FROM users WHERE id = 1")
# [SELECT, *, FROM, users, WHERE, id, =, 1, EOF]
```

### 2. Parser（语法分析器）

将 token 序列转换为 AST：

```python
from src.parser import parse_sql

ast = parse_sql("SELECT * FROM users WHERE id = 1")
# SelectStatement(
#   columns=SelectColumns(columns=[Star()]),
#   from_clause=FromClause(tables=[TableRef(table_name="users")]),
#   where_clause=WhereClause(condition=CompareExpr(op="=", ...))
# )
```

### 3. Executor（执行器）

执行查询并返回结果：

```python
from src.executor import Executor, Column

executor = Executor()
users = executor.create_table("users", [Column("id", "integer"), Column("name", "text")])
users.add_row({"id": 1, "name": "Alice"})

result = executor.execute(ast)
print(result.columns)  # ['id', 'name']
print(result.rows)     # [[1, 'Alice']]
```

### 4. Optimizer（查询优化器）

优化查询 AST：

```python
from src.optimizer import optimize_query

ast = parse_sql("SELECT * FROM t WHERE 1 + 2 = 3")
optimized = optimize_query(ast)
# 常量折叠：1 + 2 → 3
```

## 运算符优先级

| 优先级 | 操作符 | 描述 |
|--------|--------|------|
| 1 (最高) | `()` | 括号 |
| 2 | `-`, `NOT` | 一元运算 |
| 3 | `*`, `/`, `%` | 乘除模 |
| 4 | `+`, `-` | 加减 |
| 5 | `=`, `<>`, `<`, `>`, `<=`, `>=` | 比较 |
| 6 | `AND` | 逻辑与 |
| 7 (最低) | `OR` | 逻辑或 |

## 测试覆盖

### 单元测试

- Lexer 测试：token 解析、关键字识别、注释处理
- Parser 测试：AST 构建、运算符优先级、错误处理
- Executor 测试：CRUD 操作、JOIN、聚合、排序

### 集成测试

- 完整查询流程测试
- 复杂查询组合测试
- 错误处理测试

## 学习要点

### 1. 词法分析
- 理解 Token 类型和关键字识别
- 掌握字符串解析和转义处理
- 学会处理注释

### 2. 语法分析
- 理解递归下降解析技术
- 掌握运算符优先级处理
- 学会构建 AST

### 3. 查询优化
- 理解常量折叠原理
- 掌握表达式简化技术
- 学会谓词下推优化

### 4. 查询执行
- 理解内存表存储
- 掌握 JOIN 执行策略
- 学会聚合函数实现

## 扩展阅读

1. [SQLite Parser](https://www.sqlite.org/arch.html)
2. [PostgreSQL Parser](https://www.postgresql.org/docs/current/parser-stage.html)
3. [Compilers: Principles, Techniques, and Tools](https://en.wikipedia.org/wiki/Compilers:_Principles,_Techniques,_and_Tools)
4. [Crafting Interpreters](https://craftinginterpreters.com/)

## 许可证

MIT License
