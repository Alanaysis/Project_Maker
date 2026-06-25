# 查询解析器需求文档

## 1. 项目概述

### 1.1 项目目标

实现一个完整的 SQL 查询解析器，支持标准 SQL 的主要功能，包括：
- SELECT, INSERT, UPDATE, DELETE 语句
- WHERE, JOIN, GROUP BY, ORDER BY 子句
- 聚合函数和子查询
- 查询优化

### 1.2 技术栈

- **语言**：Python 3.8+
- **测试框架**：pytest
- **依赖**：无外部依赖（纯 Python 实现）

## 2. 功能需求

### 2.1 词法分析

#### 2.1.1 Token 类型

| 类别 | Token | 描述 |
|------|-------|------|
| 关键字 | SELECT, FROM, WHERE | SQL 关键字 |
| 标识符 | table_name, column_name | 表名、列名 |
| 数字 | 123, 3.14 | 整数和浮点数 |
| 字符串 | 'hello' | 字符串字面量 |
| 运算符 | =, <, >, +, -, *, / | 各种运算符 |
| 分隔符 | (, ), ,, ; | 分隔符 |

#### 2.1.2 支持的 SQL 关键字

- DQL: SELECT, FROM, WHERE, GROUP BY, HAVING, ORDER BY, LIMIT, OFFSET
- DML: INSERT, INTO, VALUES, UPDATE, SET, DELETE
- JOIN: INNER, LEFT, RIGHT, FULL, CROSS, JOIN, ON
- 条件: AND, OR, NOT, IN, BETWEEN, LIKE, IS, NULL, EXISTS
- 聚合: COUNT, SUM, AVG, MIN, MAX
- 其他: DISTINCT, AS, ASC, DESC, TRUE, FALSE

#### 2.1.3 词法分析功能

- 跳过空白字符（空格、制表符、换行符）
- 跳过注释（单行 -- 和多行 /* */）
- 识别关键字（不区分大小写）
- 识别标识符
- 识别数字（整数和浮点数）
- 识别字符串（单引号包围，支持转义）
- 识别运算符和分隔符
- 报告词法错误（位置信息）

### 2.2 语法分析

#### 2.2.1 支持的 SQL 语句

| 语句 | 语法 | 示例 |
|------|------|------|
| SELECT | SELECT columns FROM table [WHERE ...] | SELECT * FROM users |
| INSERT | INSERT INTO table (cols) VALUES (vals) | INSERT INTO users (id, name) VALUES (1, 'John') |
| UPDATE | UPDATE table SET col = val [WHERE ...] | UPDATE users SET name = 'Jane' WHERE id = 1 |
| DELETE | DELETE FROM table [WHERE ...] | DELETE FROM users WHERE id = 1 |

#### 2.2.2 支持的子句

| 子句 | 语法 | 示例 |
|------|------|------|
| WHERE | WHERE condition | WHERE age > 25 |
| JOIN | [INNER/LEFT/RIGHT/FULL/CROSS] JOIN table ON cond | LEFT JOIN orders ON users.id = orders.user_id |
| GROUP BY | GROUP BY columns | GROUP BY department |
| HAVING | HAVING condition | HAVING COUNT(*) > 5 |
| ORDER BY | ORDER BY columns [ASC/DESC] | ORDER BY name ASC, id DESC |
| LIMIT | LIMIT count [OFFSET offset] | LIMIT 10 OFFSET 20 |

#### 2.2.3 支持的表达式

- 列引用：column, table.column
- 字面量：数字、字符串、NULL
- 算术运算：+, -, *, /, %
- 比较运算：=, <>, <, >, <=, >=
- 逻辑运算：AND, OR, NOT
- 特殊运算：IN, BETWEEN, LIKE, IS NULL
- 函数调用：COUNT(), SUM(), AVG(), MIN(), MAX()
- 子查询：(SELECT ...)
- 别名：AS alias

### 2.3 AST 节点

#### 2.3.1 语句节点

- SelectStatement: SELECT 语句
- InsertStatement: INSERT 语句
- UpdateStatement: UPDATE 语句
- DeleteStatement: DELETE 语句

#### 2.3.2 子句节点

- SelectColumns: SELECT 列列表
- FromClause: FROM 子句
- WhereClause: WHERE 子句
- JoinClause: JOIN 子句
- GroupByClause: GROUP BY 子句
- OrderByClause: ORDER BY 子句
- HavingClause: HAVING 子句
- LimitClause: LIMIT 子句

#### 2.3.3 表达式节点

- ColumnRef: 列引用
- Literal: 字面量
- BinaryOp: 二元运算
- UnaryOp: 一元运算
- FuncCall: 函数调用
- CompareExpr: 比较表达式
- AndExpr/OrExpr/NotExpr: 逻辑表达式
- InExpr: IN 表达式
- BetweenExpr: BETWEEN 表达式
- LikeExpr: LIKE 表达式
- IsNullExpr: IS NULL 表达式

### 2.4 查询优化

#### 2.4.1 优化类型

1. **常量折叠**
   - 计算编译时常量表达式
   - 示例：`1 + 2` → `3`

2. **谓词下推**
   - 将 WHERE 条件推到 JOIN
   - 减少中间结果集

3. **表达式简化**
   - 消除冗余运算
   - `x + 0` → `x`
   - `x * 1` → `x`
   - `NOT NOT x` → `x`

4. **消除冗余**
   - 消除恒真/恒假条件
   - `x AND TRUE` → `x`
   - `x OR FALSE` → `x`

### 2.5 查询执行

#### 2.5.1 数据存储

- 内存表存储
- 支持创建表、添加数据
- 支持基本的数据类型（integer, float, text, boolean）

#### 2.5.2 执行功能

- SELECT 查询执行
- INSERT 数据插入
- UPDATE 数据更新
- DELETE 数据删除
- JOIN 连接查询
- GROUP BY 分组聚合
- ORDER BY 排序
- LIMIT/OFFSET 分页

## 3. 非功能需求

### 3.1 性能需求

- 单条查询解析时间 < 10ms
- 支持复杂查询（多表连接、子查询）
- 内存使用合理

### 3.2 可维护性

- 代码结构清晰
- 模块化设计
- 完整的注释和文档

### 3.3 可测试性

- 单元测试覆盖率 > 80%
- 集成测试覆盖主要功能
- 测试用例覆盖正常和异常情况

### 3.4 错误处理

- 提供清晰的错误信息
- 包含错误位置（行号、列号）
- 支持语法错误恢复

## 4. 接口设计

### 4.1 词法分析器接口

```python
class Lexer:
    def __init__(self, text: str)
    def tokenize(self) -> List[Token]

def tokenize(sql: str) -> List[Token]
```

### 4.2 语法分析器接口

```python
class Parser:
    def __init__(self, tokens: List[Token])
    def parse(self) -> ASTNode

def parse_sql(sql: str) -> ASTNode
```

### 4.3 查询执行器接口

```python
class Executor:
    def __init__(self)
    def create_table(self, name: str, columns: List[Column]) -> Table
    def execute(self, node: ASTNode) -> QueryResult
```

### 4.4 查询优化器接口

```python
class QueryOptimizer:
    def optimize(self, node: ASTNode) -> ASTNode
    def get_optimizations(self) -> List[str]
```

## 5. 测试需求

### 5.1 单元测试

- 词法分析器测试
  - Token 识别
  - 关键字识别
  - 错误处理

- 语法分析器测试
  - 各种 SQL 语句解析
  - 子句解析
  - 表达式解析
  - 错误处理

- 执行器测试
  - CRUD 操作
  - JOIN 查询
  - 聚合查询
  - 排序和分页

### 5.2 集成测试

- 完整查询流程测试
- 复杂查询测试
- 性能测试

## 6. 交付物

1. 源代码
   - src/lexer.py
   - src/parser.py
   - src/ast_nodes.py
   - src/optimizer.py
   - src/executor.py

2. 测试代码
   - tests/test_lexer.py
   - tests/test_parser.py
   - tests/test_executor.py

3. 文档
   - README.md
   - docs/01_RESEARCH.md ~ 05_DEVELOPMENT.md

4. 示例
   - examples/queries.py
