# 查询解析器研究文档

## 1. 项目背景

### 1.1 什么是查询解析器

查询解析器是数据库系统的核心组件之一，负责将用户输入的 SQL 语句转换为内部可执行的数据结构。它是数据库引擎的"翻译官"，将人类可读的 SQL 语言转换为机器可执行的操作序列。

### 1.2 为什么需要查询解析器

1. **用户接口**：提供标准化的数据查询语言
2. **语法验证**：确保查询语句的正确性
3. **语义分析**：理解查询的意图
4. **优化基础**：为查询优化提供结构化的表示

## 2. SQL 语言基础

### 2.1 SQL 语句分类

| 类型 | 语句 | 用途 |
|------|------|------|
| DQL | SELECT | 数据查询 |
| DML | INSERT, UPDATE, DELETE | 数据操作 |
| DDL | CREATE, ALTER, DROP | 数据定义 |
| DCL | GRANT, REVOKE | 数据控制 |

### 2.2 SELECT 语句结构

```sql
SELECT [DISTINCT] column_list
FROM table_list
[JOIN ... ON ...]
[WHERE condition]
[GROUP BY columns]
[HAVING condition]
[ORDER BY columns [ASC|DESC]]
[LIMIT count [OFFSET offset]]
```

### 2.3 运算符优先级

| 优先级 | 运算符 | 描述 |
|--------|--------|------|
| 1 | () | 括号 |
| 2 | NOT | 逻辑非 |
| 3 | *, /, % | 乘除模 |
| 4 | +, - | 加减 |
| 5 | =, <, >, <=, >=, <> | 比较 |
| 6 | AND | 逻辑与 |
| 7 | OR | 逻辑或 |

## 3. 解析技术

### 3.1 词法分析（Lexical Analysis）

词法分析器（Lexer/Tokenizer）将 SQL 字符串转换为 Token 序列。

**Token 类型**：
- 关键字：SELECT, FROM, WHERE, AND, OR, etc.
- 标识符：表名、列名
- 字面量：数字、字符串
- 运算符：=, <, >, +, -, *, /
- 分隔符：(, ), ,, ;

**示例**：
```
输入: SELECT id, name FROM users WHERE age > 25
输出: [SELECT, IDENT(id), COMMA, IDENT(name), FROM, IDENT(users), WHERE, IDENT(age), GT, NUMBER(25)]
```

### 3.2 语法分析（Syntax Analysis）

语法分析器（Parser）将 Token 序列转换为抽象语法树（AST）。

**常用方法**：
1. **递归下降解析**：简单直观，适合手工实现
2. **LL 解析**：自顶向下，易于理解
3. **LR 解析**：自底向上，功能强大
4. **Earley 解析**：处理所有上下文无关文法

### 3.3 抽象语法树（AST）

AST 是查询的结构化表示，树的每个节点代表一个语法结构。

**示例**：
```sql
SELECT name FROM users WHERE age > 25
```

对应的 AST：
```
SelectStatement
├── columns: [ColumnRef("name")]
├── from: TableRef("users")
└── where: CompareExpr(">")
    ├── left: ColumnRef("age")
    └── right: Literal(25)
```

## 4. 查询优化

### 4.1 优化类型

1. **常量折叠**：编译时计算常量表达式
   - `1 + 2` → `3`

2. **谓词下推**：将条件推到数据源
   - 减少中间结果集大小

3. **表达式简化**：消除冗余运算
   - `x + 0` → `x`
   - `x * 1` → `x`
   - `NOT NOT x` → `x`

4. **连接优化**：选择最优的连接顺序

### 4.2 优化器架构

```
原始 AST
    ↓
┌──────────────┐
│ 常量折叠     │
└──────────────┘
    ↓
┌──────────────┐
│ 谓词下推     │
└──────────────┘
    ↓
┌──────────────┐
│ 表达式简化   │
└──────────────┘
    ↓
优化后 AST
```

## 5. 执行模型

### 5.1 执行流程

```
SQL 字符串
    ↓
词法分析 → Token 序列
    ↓
语法分析 → AST
    ↓
查询优化 → 优化后 AST
    ↓
执行计划生成
    ↓
执行并返回结果
```

### 5.2 执行策略

1. **嵌套循环连接**：简单但效率低
2. **哈希连接**：适合等值连接
3. **排序归并连接**：适合已排序的数据

## 6. 参考资料

1. [SQLite Parser](https://www.sqlite.org/arch.html)
2. [PostgreSQL Parser](https://www.postgresql.org/docs/current/parser-stage.html)
3. [MySQL Parser](https://dev.mysql.com/doc/internals/en/parser.html)
4. [Compilers: Principles, Techniques, and Tools (Dragon Book)](https://en.wikipedia.org/wiki/Compilers:_Principles,_Techniques,_and_Tools)
5. [SQL-92 Standard](https://www.contrib.andrew.cmu.edu/~shadow/sql/sql1992.txt)
