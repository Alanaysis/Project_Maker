# 查询解析器设计文档

## 1. 系统架构

### 1.1 整体架构

```
┌─────────────────────────────────────────────────────────────┐
│                      查询解析器系统                           │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │  词法    │→│  语法    │→│  优化    │→│  执行    │   │
│  │  分析器  │  │  分析器  │  │  器      │  │  器      │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
│       ↓             ↓             ↓             ↓           │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │  Token   │  │   AST    │  │ 优化后   │  │  查询    │   │
│  │  序列    │  │  节点    │  │   AST    │  │  结果    │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
└─────────────────────────────────────────────────────────────┘
```

### 1.2 模块划分

```
src/
├── __init__.py          # 包初始化
├── lexer.py             # 词法分析器
├── parser.py            # 语法分析器
├── ast_nodes.py         # AST 节点定义
├── optimizer.py         # 查询优化器
└── executor.py          # 查询执行器
```

## 2. 词法分析器设计

### 2.1 Token 类型设计

```python
class TokenType(Enum):
    # 字面量
    IDENTIFIER = auto()      # 标识符
    NUMBER = auto()          # 整数
    FLOAT = auto()           # 浮点数
    STRING = auto()          # 字符串

    # SQL 关键字
    SELECT = auto()
    FROM = auto()
    WHERE = auto()
    # ... 更多关键字

    # 运算符
    EQ = auto()              # =
    NEQ = auto()             # <> 或 !=
    LT = auto()              # <
    GT = auto()              # >
    # ... 更多运算符

    # 分隔符
    LPAREN = auto()          # (
    RPAREN = auto()          # )
    COMMA = auto()           # ,
    SEMICOLON = auto()       # ;

    # 特殊
    EOF = auto()
```

### 2.2 Token 数据结构

```python
@dataclass
class Token:
    type: TokenType
    value: str
    line: int
    column: int
```

### 2.3 词法分析流程

```
输入字符串
    ↓
跳过空白
    ↓
检查字符类型
    ├─ 数字 → 读取数字
    ├─ 字母 → 读取标识符/关键字
    ├─ 引号 → 读取字符串
    ├─ 运算符 → 读取运算符
    └─ 分隔符 → 读取分隔符
    ↓
生成 Token
    ↓
重复直到输入结束
    ↓
添加 EOF Token
```

## 3. 语法分析器设计

### 3.1 AST 节点层次

```
ASTNode (基类)
├── 语句节点
│   ├── SelectStatement
│   ├── InsertStatement
│   ├── UpdateStatement
│   └── DeleteStatement
├── 子句节点
│   ├── SelectColumns
│   ├── FromClause
│   ├── WhereClause
│   ├── JoinClause
│   ├── GroupByClause
│   ├── OrderByClause
│   ├── HavingClause
│   └── LimitClause
└── 表达式节点
    ├── ColumnRef
    ├── Literal
    ├── BinaryOp
    ├── UnaryOp
    ├── FuncCall
    ├── CompareExpr
    ├── AndExpr
    ├── OrExpr
    ├── NotExpr
    ├── InExpr
    ├── BetweenExpr
    ├── LikeExpr
    └── IsNullExpr
```

### 3.2 递归下降解析

使用递归下降解析法，每个语法规则对应一个解析方法：

```python
class Parser:
    def parse(self) -> ASTNode:
        """解析入口"""
        return self.parse_statement()

    def parse_statement(self) -> ASTNode:
        """解析语句"""
        if self.match(TokenType.SELECT):
            return self.parse_select()
        elif self.match(TokenType.INSERT):
            return self.parse_insert()
        # ...

    def parse_select(self) -> SelectStatement:
        """解析 SELECT 语句"""
        # SELECT columns FROM table [WHERE ...]
        # ...

    def parse_expression(self) -> ASTNode:
        """解析表达式"""
        return self.parse_or_expression()

    def parse_or_expression(self) -> ASTNode:
        """解析 OR 表达式"""
        left = self.parse_and_expression()
        while self.match(TokenType.OR):
            self.advance()
            right = self.parse_and_expression()
            left = OrExpr(left=left, right=right)
        return left
```

### 3.3 运算符优先级处理

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

## 4. AST 节点设计

### 4.1 基类设计

```python
@dataclass
class ASTNode:
    """AST 节点基类"""
    node_type: NodeType
    line: int = 0
    column: int = 0
```

### 4.2 语句节点

```python
@dataclass
class SelectStatement(ASTNode):
    """SELECT 语句"""
    node_type: NodeType = NodeType.SELECT_STMT
    columns: SelectColumns = None
    from_clause: FromClause = None
    where_clause: WhereClause = None
    group_by: GroupByClause = None
    having: HavingClause = None
    order_by: OrderByClause = None
    limit: LimitClause = None
```

### 4.3 表达式节点

```python
@dataclass
class CompareExpr(ASTNode):
    """比较表达式"""
    node_type: NodeType = NodeType.COMPARE_EXPR
    op: str = ""
    left: ASTNode = None
    right: ASTNode = None
```

## 5. 查询优化器设计

### 5.1 优化流程

```
输入 AST
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
┌──────────────┐
│ 消除冗余     │
└──────────────┘
    ↓
输出优化后 AST
```

### 5.2 优化规则

#### 常量折叠
```python
# 输入: BinaryOp('+', Literal(1), Literal(2))
# 输出: Literal(3)
```

#### 表达式简化
```python
# 输入: BinaryOp('+', ColumnRef('x'), Literal(0))
# 输出: ColumnRef('x')
```

#### 消除冗余
```python
# 输入: NotExpr(NotExpr(expr))
# 输出: expr
```

## 6. 查询执行器设计

### 6.1 数据存储

```python
@dataclass
class Table:
    """内存表"""
    name: str
    columns: List[Column]
    rows: List[Dict[str, Any]]
```

### 6.2 执行流程

```
AST 节点
    ↓
判断语句类型
├─ SELECT → execute_select
├─ INSERT → execute_insert
├─ UPDATE → execute_update
└─ DELETE → execute_delete
    ↓
执行并返回结果
```

### 6.3 SELECT 执行流程

```
SelectStatement
    ↓
解析 FROM → 获取数据源
    ↓
应用 WHERE → 过滤行
    ↓
应用 GROUP BY → 分组
    ↓
应用 HAVING → 过滤组
    ↓
应用 ORDER BY → 排序
    ↓
应用 LIMIT → 分页
    ↓
构建结果集
```

### 6.4 JOIN 执行

```python
def _apply_join(self, rows, join, column_map):
    """应用 JOIN"""
    join_table = self.get_table(join.table.table_name)

    if join.join_type == JoinType.CROSS:
        # 笛卡尔积
        return [combine(row, join_row) for row in rows for join_row in join_table.rows]

    # INNER/LEFT/RIGHT/FULL JOIN
    new_rows = []
    for row in rows:
        matched = False
        for join_row in join_table.rows:
            if evaluate_condition(row, join.on_condition):
                new_rows.append(combine(row, join_row))
                matched = True

        # LEFT JOIN: 保留左表行
        if not matched and join.join_type == JoinType.LEFT:
            new_rows.append(combine_with_null(row))

    return new_rows
```

## 7. 错误处理设计

### 7.1 错误类型

```python
class LexerError(Exception):
    """词法分析错误"""
    def __init__(self, message, line, column):

class ParseError(Exception):
    """语法解析错误"""
    def __init__(self, message, token):

class ExecutionError(Exception):
    """执行错误"""
```

### 7.2 错误信息格式

```
Lexer error at line:column: message
Parse error at line:column: message
Execution error: message
```

## 8. 接口设计

### 8.1 公共接口

```python
# 词法分析
from src.lexer import tokenize
tokens = tokenize("SELECT * FROM users")

# 语法分析
from src.parser import parse_sql
ast = parse_sql("SELECT * FROM users")

# 查询执行
from src.executor import Executor, Column
executor = Executor()
executor.create_table("users", [Column("id", "integer"), Column("name", "text")])
result = executor.execute(ast)

# 查询优化
from src.optimizer import optimize_query
optimized_ast = optimize_query(ast)
```

## 9. 测试策略

### 9.1 单元测试

- 词法分析器：Token 识别、关键字识别、错误处理
- 语法分析器：各种 SQL 语句解析、表达式解析
- 执行器：CRUD 操作、JOIN、聚合、排序

### 9.2 集成测试

- 完整查询流程
- 复杂查询组合
- 性能测试

## 10. 扩展性设计

### 10.1 添加新语句

1. 在 `TokenType` 中添加新关键字
2. 在 `KEYWORDS` 中添加映射
3. 在 `NodeType` 中添加新节点类型
4. 在 `ast_nodes.py` 中定义新节点类
5. 在 `Parser` 中添加解析方法
6. 在 `Executor` 中添加执行方法

### 10.2 添加新优化规则

1. 在 `QueryOptimizer` 中添加新方法
2. 在 `optimize` 方法中调用新方法

### 10.3 添加新数据源

1. 实现 `Table` 接口
2. 在 `Executor` 中注册新数据源
