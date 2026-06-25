# 学习笔记：SQL 查询解析器

## 项目概述

本项目实现了一个完整的 SQL 查询解析器，支持 SELECT、INSERT、UPDATE、DELETE 语句。通过这个项目，我深入理解了数据库查询处理的核心流程。

## 核心概念学习

### 1. 查询解析流程

```
SQL 字符串 → 词法分析 → 语法分析 → AST → 查询优化 → 执行 → 结果
```

**学习要点**：
- 词法分析（Lexer）将字符串转换为 token 序列
- 语法分析（Parser）将 token 序列转换为 AST
- 查询优化器对 AST 进行优化
- 执行器遍历 AST 执行查询

### 2. 递归下降解析

递归下降是一种自顶向下的语法分析方法：

```python
def parse_or_expression(self) -> ASTNode:
    left = self.parse_and_expression()
    while self.match(TokenType.OR):
        self.advance()
        right = self.parse_and_expression()
        left = OrExpr(left=left, right=right)
    return left
```

**学习要点**：
- 每个语法规则对应一个方法
- 优先级通过方法调用层次体现
- 最低优先级的规则最先被解析

### 3. 运算符优先级

通过分层解析处理运算符优先级：

```
parse_expression
    ↓
parse_or_expression (最低优先级)
    ↓
parse_and_expression
    ↓
parse_not_expression
    ↓
parse_comparison
    ↓
parse_addition (+ -)
    ↓
parse_multiplication (* / %)
    ↓
parse_unary (- NOT)
    ↓
parse_primary (最高优先级)
```

**学习要点**：
- 优先级决定了表达式的解析方式
- `a OR b AND c` 解析为 `a OR (b AND c)`
- 括号可以改变默认优先级

### 4. SQL 语句类型

| 类型 | 语句 | 用途 |
|------|------|------|
| DQL | SELECT | 数据查询 |
| DML | INSERT, UPDATE, DELETE | 数据操作 |
| DDL | CREATE, ALTER, DROP | 数据定义 |

**学习要点**：
- SELECT 是最复杂的语句
- INSERT/UPDATE/DELETE 相对简单
- 每种语句需要不同的解析逻辑

### 5. JOIN 操作

JOIN 用于连接多个表：

```sql
SELECT users.name, orders.amount
FROM users
INNER JOIN orders ON users.id = orders.user_id
```

**学习要点**：
- INNER JOIN：返回两个表中匹配的行
- LEFT JOIN：返回左表所有行，右表匹配的行
- RIGHT JOIN：返回右表所有行，左表匹配的行
- FULL JOIN：返回两个表所有行

## 技术实现学习

### 1. Python 语言特性

#### 枚举类型

```python
class TokenType(Enum):
    IDENTIFIER = auto()
    NUMBER = auto()
    STRING = auto()
    SELECT = auto()
    # ...
```

**学习要点**：
- Enum 提供类型安全的常量
- auto() 自动生成值
- 提高代码可读性

#### 数据类

```python
@dataclass
class Token:
    type: TokenType
    value: str
    line: int = 1
    column: int = 1
```

**学习要点**：
- @dataclass 自动生成 __init__, __repr__ 等方法
- 支持默认值
- 减少样板代码

#### 类型注解

```python
def parse_expression(self) -> ASTNode:
    """解析表达式"""
    return self.parse_or_expression()
```

**学习要点**：
- 类型注解提高代码可读性
- 支持 IDE 自动补全
- 可用于静态类型检查

### 2. 数据结构设计

#### AST 节点

```python
@dataclass
class ASTNode:
    """AST 节点基类"""
    node_type: NodeType
    line: int = 0
    column: int = 0

@dataclass
class SelectStatement(ASTNode):
    """SELECT 语句"""
    node_type: NodeType = NodeType.SELECT_STMT
    columns: SelectColumns = None
    from_clause: FromClause = None
    where_clause: WhereClause = None
    # ...
```

**学习要点**：
- 继承关系表示节点层次
- 不同节点类型使用不同字段
- 灵活的设计支持多种查询类型

#### Token 设计

```python
@dataclass
class Token:
    type: TokenType
    value: str
    line: int = 1
    column: int = 1
```

**学习要点**：
- 类型和值的分离
- 支持多种 token 类型
- 保留位置信息用于错误报告

### 3. 算法实现

#### 常量折叠

```python
def constant_folding(self, node: ASTNode) -> ASTNode:
    if isinstance(node, BinaryOp):
        if isinstance(node.left, Literal) and isinstance(node.right, Literal):
            result = self._eval_binary_op(node.op, node.left, node.right)
            if result is not None:
                return result
    return node
```

**学习要点**：
- 在编译时计算常量表达式
- 减少运行时计算
- 简化 AST

#### 表达式简化

```python
def simplify_expressions(self, node: ASTNode) -> ASTNode:
    if isinstance(node, BinaryOp):
        # x + 0 → x
        if node.op == '+' and isinstance(node.right, Literal) and node.right.value == 0:
            return node.left
        # x * 1 → x
        if node.op == '*' and isinstance(node.right, Literal) and node.right.value == 1:
            return node.left
    return node
```

**学习要点**：
- 消除冗余运算
- 提高执行效率
- 简化查询逻辑

## 设计模式学习

### 1. 访问者模式

执行器遍历 AST 时使用了访问者模式的思想：

```python
def execute(self, node: ASTNode) -> QueryResult:
    if isinstance(node, SelectStatement):
        return self.execute_select(node)
    elif isinstance(node, InsertStatement):
        return self.execute_insert(node)
    elif isinstance(node, UpdateStatement):
        return self.execute_update(node)
    elif isinstance(node, DeleteStatement):
        return self.execute_delete(node)
```

**学习要点**：
- 根据节点类型执行不同操作
- 避免在节点中实现执行逻辑
- 提高代码的可扩展性

### 2. 工厂模式

创建节点使用 dataclass：

```python
@dataclass
class ColumnRef(ASTNode):
    """列引用节点"""
    node_type: NodeType = field(default=NodeType.COLUMN_REF, init=False)
    table: Optional[str] = None
    column: str = ""
    alias: Optional[str] = None
```

**学习要点**：
- 封装对象创建逻辑
- 提供清晰的 API
- 简化客户端代码

### 3. 策略模式

不同的查询类型可以看作不同的策略：

- SelectStatement：查询数据
- InsertStatement：插入数据
- UpdateStatement：更新数据
- DeleteStatement：删除数据

**学习要点**：
- 将算法封装为独立的策略
- 支持运行时切换策略
- 提高代码的灵活性

## 测试学习

### 1. 单元测试

```python
def test_simple_select(self):
    """测试简单 SELECT"""
    ast = parse_sql("SELECT * FROM users")
    assert isinstance(ast, SelectStatement)
    assert isinstance(ast.columns.columns[0], Star)
    assert ast.from_clause.tables[0].table_name == "users"
```

**学习要点**：
- 测试应该独立且可重复
- 使用有意义的断言信息
- 测试边界情况和错误处理

### 2. 参数化测试

```python
@pytest.mark.parametrize("sql,expected", [
    ("SELECT * FROM users", 4),
    ("SELECT * FROM users WHERE age > 25", 2),
    ("SELECT * FROM users WHERE age < 25", 1),
])
def test_select_where(self, sql, expected):
    ast = parse_sql(sql)
    result = executor.execute(ast)
    assert len(result.rows) == expected
```

**学习要点**：
- 参数化测试减少代码重复
- 使用 pytest.mark.parametrize
- 易于添加新的测试用例

### 3. 集成测试

```python
def test_complex_query(self):
    """测试复杂查询"""
    ast = parse_sql("""
        SELECT u.name, COUNT(o.id) AS order_count
        FROM users u
        LEFT JOIN orders o ON u.id = o.user_id
        WHERE u.active = true
        GROUP BY u.name
        HAVING COUNT(o.id) >= 1
        ORDER BY order_count DESC
        LIMIT 10
    """)
    result = executor.execute(ast)
    assert len(result.columns) == 2
    assert len(result.rows) >= 1
```

**学习要点**：
- 测试组件间的交互
- 验证完整的查询流程
- 发现集成问题

## 测试结果

```
============================= 125 passed in 0.04s ==============================
```

所有 125 个测试通过，包括：
- 词法分析器测试：28 个
- 语法分析器测试：57 个
- 执行器测试：40 个

## 常见问题解决

### 1. 关键字作为别名

**问题**：SQL 允许关键字作为别名，例如 `SELECT COUNT(*) AS count`

**原因**：词法分析器将 `count` 识别为 COUNT 关键字

**解决**：在解析别名时，允许任何 token 作为别名

```python
def read_alias(self) -> str:
    """读取别名（可以是标识符或关键字）"""
    token = self.current_token()
    # 别名可以是标识符或任何关键字
    if token.type == TokenType.IDENTIFIER or token.type.name in KEYWORDS:
        return self.advance().value
    raise self.error(f"期望别名，得到 {token.type.name}")
```

### 2. 聚合函数在 HAVING 中的使用

**问题**：HAVING 子句中的聚合函数无法正确评估

**原因**：聚合结果存储在行中使用别名，但 HAVING 条件使用原始表达式

**解决**：在 GROUP BY 后，将聚合结果存储到行中，使用默认别名和显式别名

```python
# 计算聚合函数
for col_expr in select_columns.columns:
    if isinstance(col_expr, FuncCall):
        agg_value = self._calculate_aggregate(col_expr, group, column_map)
        # 存储到默认别名和显式别名
        default_alias = f"{col_expr.func_name}()"
        result_row[default_alias] = agg_value
        if col_expr.alias:
            result_row[col_expr.alias] = agg_value
```

### 3. SELECT * 的列去重

**问题**：当使用 JOIN 时，SELECT * 会返回重复的列

**原因**：行中存储了带表前缀和不带表前缀的列名

**解决**：只返回不带表前缀的列名

```python
# 处理 SELECT *
if len(select_columns.columns) == 1 and isinstance(select_columns.columns[0], Star):
    if rows:
        # 获取所有列名（去重，只保留不带表前缀的列名）
        all_columns = []
        seen = set()
        for col in rows[0].keys():
            if '.' not in col:
                if col not in seen:
                    all_columns.append(col)
                    seen.add(col)
```

## 项目总结

### 成功实现

1. **词法分析器**：支持 SQL 关键字、标识符、字面量、运算符
2. **语法分析器**：递归下降实现，支持运算符优先级
3. **AST**：灵活的树形结构，支持任意复杂查询
4. **查询优化器**：常量折叠、表达式简化、谓词下推
5. **执行器**：支持 SELECT、INSERT、UPDATE、DELETE、JOIN、GROUP BY

### 学到的知识

1. **查询解析**：理解了数据库的查询处理流程
2. **递归下降解析**：掌握了语法分析的核心技术
3. **SQL 语法**：深入理解了 SQL 的各种语法结构
4. **查询优化**：学习了常量折叠、表达式简化等优化技术
5. **Python 语言**：深入理解了枚举、数据类、类型注解等特性

### 未来改进

1. 支持更多 SQL 语法（CREATE TABLE, ALTER TABLE, UNION）
2. 支持子查询优化
3. 实现更复杂的 JOIN 算法（哈希连接、排序归并连接）
4. 添加索引支持
5. 支持持久化存储

## 参考资源

1. **SQLite Parser**
   - 工业级 SQL 解析器参考
   - https://www.sqlite.org/arch.html

2. **PostgreSQL Parser**
   - 现代数据库解析器设计
   - https://www.postgresql.org/docs/current/parser-stage.html

3. **Crafting Interpreters**
   - 解释器实现经典教材
   - https://craftinginterpreters.com/

4. **Python 官方文档**
   - 学习 Python 语言特性
   - https://docs.python.org/3/
