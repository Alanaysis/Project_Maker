"""
AST 节点定义 - 查询解析树的节点类型
"""

from dataclasses import dataclass, field
from typing import List, Optional, Any
from enum import Enum, auto


class NodeType(Enum):
    """AST 节点类型"""
    # 语句节点
    SELECT_STMT = auto()
    INSERT_STMT = auto()
    UPDATE_STMT = auto()
    DELETE_STMT = auto()

    # 表达式节点
    COLUMN_REF = auto()       # 列引用 (table.column)
    TABLE_REF = auto()        # 表引用
    ALIAS = auto()            # 别名
    LITERAL = auto()          # 字面量 (数字、字符串)
    BINARY_OP = auto()        # 二元运算 (+, -, *, /, =, <, >, etc.)
    UNARY_OP = auto()         # 一元运算 (NOT, -)
    FUNC_CALL = auto()        # 函数调用 (COUNT, SUM, etc.)
    STAR = auto()             # *
    PARAM = auto()            # 参数 ?
    SUBQUERY = auto()         # 子查询

    # 条件节点
    AND_EXPR = auto()         # AND
    OR_EXPR = auto()          # OR
    NOT_EXPR = auto()         # NOT
    COMPARE_EXPR = auto()     # 比较 (=, <, >, etc.)
    IN_EXPR = auto()          # IN (...)
    BETWEEN_EXPR = auto()     # BETWEEN ... AND ...
    LIKE_EXPR = auto()        # LIKE
    IS_NULL_EXPR = auto()     # IS NULL / IS NOT NULL
    EXISTS_EXPR = auto()      # EXISTS (...)

    # 子句节点
    SELECT_COLUMNS = auto()   # SELECT 列列表
    FROM_CLAUSE = auto()      # FROM 子句
    WHERE_CLAUSE = auto()     # WHERE 子句
    JOIN_CLAUSE = auto()      # JOIN 子句
    GROUP_BY_CLAUSE = auto()  # GROUP BY 子句
    ORDER_BY_CLAUSE = auto()  # ORDER BY 子句
    HAVING_CLAUSE = auto()    # HAVING 子句
    LIMIT_CLAUSE = auto()     # LIMIT 子句

    # 其他
    INSERT_VALUES = auto()    # INSERT VALUES
    UPDATE_SET = auto()       # UPDATE SET
    ORDER_ITEM = auto()       # ORDER BY 项
    NULL_VALUE = auto()       # NULL 值


class JoinType(Enum):
    """JOIN 类型"""
    INNER = auto()
    LEFT = auto()
    RIGHT = auto()
    FULL = auto()
    CROSS = auto()


class SortDirection(Enum):
    """排序方向"""
    ASC = auto()
    DESC = auto()


class AggregateFunc(Enum):
    """聚合函数"""
    COUNT = auto()
    SUM = auto()
    AVG = auto()
    MIN = auto()
    MAX = auto()


@dataclass
class ASTNode:
    """AST 节点基类"""
    node_type: NodeType
    line: int = 0
    column: int = 0

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.node_type.name})"


# ============================================================================
# 表达式节点
# ============================================================================

@dataclass
class ColumnRef(ASTNode):
    """列引用节点"""
    node_type: NodeType = field(default=NodeType.COLUMN_REF, init=False)
    table: Optional[str] = None
    column: str = ""
    alias: Optional[str] = None

    def __repr__(self) -> str:
        ref = f"{self.table}.{self.column}" if self.table else self.column
        if self.alias:
            ref += f" AS {self.alias}"
        return ref


@dataclass
class TableRef(ASTNode):
    """表引用节点"""
    node_type: NodeType = field(default=NodeType.TABLE_REF, init=False)
    table_name: str = ""
    alias: Optional[str] = None
    schema: Optional[str] = None

    def __repr__(self) -> str:
        ref = f"{self.schema}.{self.table_name}" if self.schema else self.table_name
        if self.alias:
            ref += f" AS {self.alias}"
        return ref


@dataclass
class Literal(ASTNode):
    """字面量节点"""
    node_type: NodeType = field(default=NodeType.LITERAL, init=False)
    value: Any = None
    data_type: str = "unknown"  # "integer", "float", "string", "null"

    def __repr__(self) -> str:
        if self.data_type == "string":
            return f"'{self.value}'"
        return str(self.value)


@dataclass
class Star(ASTNode):
    """星号节点 (SELECT *)"""
    node_type: NodeType = field(default=NodeType.STAR, init=False)
    table: Optional[str] = None

    def __repr__(self) -> str:
        return f"{self.table}.*" if self.table else "*"


@dataclass
class BinaryOp(ASTNode):
    """二元运算节点"""
    node_type: NodeType = field(default=NodeType.BINARY_OP, init=False)
    op: str = ""
    left: Optional[ASTNode] = None
    right: Optional[ASTNode] = None

    def __repr__(self) -> str:
        return f"({self.left} {self.op} {self.right})"


@dataclass
class UnaryOp(ASTNode):
    """一元运算节点"""
    node_type: NodeType = field(default=NodeType.UNARY_OP, init=False)
    op: str = ""
    operand: Optional[ASTNode] = None

    def __repr__(self) -> str:
        return f"({self.op} {self.operand})"


@dataclass
class FuncCall(ASTNode):
    """函数调用节点"""
    node_type: NodeType = field(default=NodeType.FUNC_CALL, init=False)
    func_name: str = ""
    args: List[ASTNode] = field(default_factory=list)
    distinct: bool = False
    alias: Optional[str] = None

    def __repr__(self) -> str:
        args_str = ", ".join(str(a) for a in self.args)
        dist = "DISTINCT " if self.distinct else ""
        result = f"{self.func_name}({dist}{args_str})"
        if self.alias:
            result += f" AS {self.alias}"
        return result


@dataclass
class Param(ASTNode):
    """参数节点 (?)"""
    node_type: NodeType = field(default=NodeType.PARAM, init=False)
    index: int = 0

    def __repr__(self) -> str:
        return "?"


@dataclass
class Subquery(ASTNode):
    """子查询节点"""
    node_type: NodeType = field(default=NodeType.SUBQUERY, init=False)
    query: Optional[ASTNode] = None

    def __repr__(self) -> str:
        return f"({self.query})"


# ============================================================================
# 条件节点
# ============================================================================

@dataclass
class AndExpr(ASTNode):
    """AND 表达式节点"""
    node_type: NodeType = field(default=NodeType.AND_EXPR, init=False)
    left: Optional[ASTNode] = None
    right: Optional[ASTNode] = None

    def __repr__(self) -> str:
        return f"({self.left} AND {self.right})"


@dataclass
class OrExpr(ASTNode):
    """OR 表达式节点"""
    node_type: NodeType = field(default=NodeType.OR_EXPR, init=False)
    left: Optional[ASTNode] = None
    right: Optional[ASTNode] = None

    def __repr__(self) -> str:
        return f"({self.left} OR {self.right})"


@dataclass
class NotExpr(ASTNode):
    """NOT 表达式节点"""
    node_type: NodeType = field(default=NodeType.NOT_EXPR, init=False)
    operand: Optional[ASTNode] = None

    def __repr__(self) -> str:
        return f"(NOT {self.operand})"


@dataclass
class CompareExpr(ASTNode):
    """比较表达式节点"""
    node_type: NodeType = field(default=NodeType.COMPARE_EXPR, init=False)
    op: str = ""
    left: Optional[ASTNode] = None
    right: Optional[ASTNode] = None

    def __repr__(self) -> str:
        return f"({self.left} {self.op} {self.right})"


@dataclass
class InExpr(ASTNode):
    """IN 表达式节点"""
    node_type: NodeType = field(default=NodeType.IN_EXPR, init=False)
    operand: Optional[ASTNode] = None
    values: List[ASTNode] = field(default_factory=list)
    not_in: bool = False
    subquery: Optional[ASTNode] = None

    def __repr__(self) -> str:
        not_str = "NOT " if self.not_in else ""
        if self.subquery:
            return f"({self.operand} {not_str}IN {self.subquery})"
        values_str = ", ".join(str(v) for v in self.values)
        return f"({self.operand} {not_str}IN ({values_str}))"


@dataclass
class BetweenExpr(ASTNode):
    """BETWEEN 表达式节点"""
    node_type: NodeType = field(default=NodeType.BETWEEN_EXPR, init=False)
    operand: Optional[ASTNode] = None
    low: Optional[ASTNode] = None
    high: Optional[ASTNode] = None
    not_between: bool = False

    def __repr__(self) -> str:
        not_str = "NOT " if self.not_between else ""
        return f"({self.operand} {not_str}BETWEEN {self.low} AND {self.high})"


@dataclass
class LikeExpr(ASTNode):
    """LIKE 表达式节点"""
    node_type: NodeType = field(default=NodeType.LIKE_EXPR, init=False)
    operand: Optional[ASTNode] = None
    pattern: Optional[ASTNode] = None
    not_like: bool = False

    def __repr__(self) -> str:
        not_str = "NOT " if self.not_like else ""
        return f"({self.operand} {not_str}LIKE {self.pattern})"


@dataclass
class IsNullExpr(ASTNode):
    """IS NULL 表达式节点"""
    node_type: NodeType = field(default=NodeType.IS_NULL_EXPR, init=False)
    operand: Optional[ASTNode] = None
    is_null: bool = True

    def __repr__(self) -> str:
        not_str = " NOT" if not self.is_null else ""
        return f"({self.operand} IS{not_str} NULL)"


@dataclass
class ExistsExpr(ASTNode):
    """EXISTS 表达式节点"""
    node_type: NodeType = field(default=NodeType.EXISTS_EXPR, init=False)
    subquery: Optional[ASTNode] = None
    not_exists: bool = False

    def __repr__(self) -> str:
        not_str = "NOT " if self.not_exists else ""
        return f"({not_str}EXISTS {self.subquery})"


# ============================================================================
# 子句节点
# ============================================================================

@dataclass
class SelectColumns(ASTNode):
    """SELECT 列列表节点"""
    node_type: NodeType = field(default=NodeType.SELECT_COLUMNS, init=False)
    columns: List[ASTNode] = field(default_factory=list)
    distinct: bool = False

    def __repr__(self) -> str:
        dist = "DISTINCT " if self.distinct else ""
        cols = ", ".join(str(c) for c in self.columns)
        return f"SELECT {dist}{cols}"


@dataclass
class FromClause(ASTNode):
    """FROM 子句节点"""
    node_type: NodeType = field(default=NodeType.FROM_CLAUSE, init=False)
    tables: List[ASTNode] = field(default_factory=list)
    joins: List[ASTNode] = field(default_factory=list)

    def __repr__(self) -> str:
        tables = ", ".join(str(t) for t in self.tables)
        joins = " ".join(str(j) for j in self.joins)
        return f"FROM {tables} {joins}".strip()


@dataclass
class JoinClause(ASTNode):
    """JOIN 子句节点"""
    node_type: NodeType = field(default=NodeType.JOIN_CLAUSE, init=False)
    join_type: JoinType = JoinType.INNER
    table: Optional[ASTNode] = None
    on_condition: Optional[ASTNode] = None

    def __repr__(self) -> str:
        return f"{self.join_type.name} JOIN {self.table} ON {self.on_condition}"


@dataclass
class WhereClause(ASTNode):
    """WHERE 子句节点"""
    node_type: NodeType = field(default=NodeType.WHERE_CLAUSE, init=False)
    condition: Optional[ASTNode] = None

    def __repr__(self) -> str:
        return f"WHERE {self.condition}"


@dataclass
class GroupByClause(ASTNode):
    """GROUP BY 子句节点"""
    node_type: NodeType = field(default=NodeType.GROUP_BY_CLAUSE, init=False)
    columns: List[ASTNode] = field(default_factory=list)

    def __repr__(self) -> str:
        cols = ", ".join(str(c) for c in self.columns)
        return f"GROUP BY {cols}"


@dataclass
class OrderByClause(ASTNode):
    """ORDER BY 子句节点"""
    node_type: NodeType = field(default=NodeType.ORDER_BY_CLAUSE, init=False)
    items: List[ASTNode] = field(default_factory=list)

    def __repr__(self) -> str:
        items = ", ".join(str(i) for i in self.items)
        return f"ORDER BY {items}"


@dataclass
class OrderItem(ASTNode):
    """ORDER BY 项节点"""
    node_type: NodeType = field(default=NodeType.ORDER_ITEM, init=False)
    expr: Optional[ASTNode] = None
    direction: SortDirection = SortDirection.ASC

    def __repr__(self) -> str:
        return f"{self.expr} {self.direction.name}"


@dataclass
class HavingClause(ASTNode):
    """HAVING 子句节点"""
    node_type: NodeType = field(default=NodeType.HAVING_CLAUSE, init=False)
    condition: Optional[ASTNode] = None

    def __repr__(self) -> str:
        return f"HAVING {self.condition}"


@dataclass
class LimitClause(ASTNode):
    """LIMIT 子句节点"""
    node_type: NodeType = field(default=NodeType.LIMIT_CLAUSE, init=False)
    limit: int = 0
    offset: Optional[int] = None

    def __repr__(self) -> str:
        if self.offset is not None:
            return f"LIMIT {self.limit} OFFSET {self.offset}"
        return f"LIMIT {self.limit}"


# ============================================================================
# 语句节点
# ============================================================================

@dataclass
class InsertValues(ASTNode):
    """INSERT VALUES 节点"""
    node_type: NodeType = field(default=NodeType.INSERT_VALUES, init=False)
    values: List[List[ASTNode]] = field(default_factory=list)

    def __repr__(self) -> str:
        rows = []
        for row in self.values:
            vals = ", ".join(str(v) for v in row)
            rows.append(f"({vals})")
        return f"VALUES {', '.join(rows)}"


@dataclass
class UpdateSet(ASTNode):
    """UPDATE SET 节点"""
    node_type: NodeType = field(default=NodeType.UPDATE_SET, init=False)
    assignments: List[tuple] = field(default_factory=list)  # [(column, value), ...]

    def __repr__(self) -> str:
        assigns = ", ".join(f"{col} = {val}" for col, val in self.assignments)
        return f"SET {assigns}"


@dataclass
class SelectStatement(ASTNode):
    """SELECT 语句节点"""
    node_type: NodeType = field(default=NodeType.SELECT_STMT, init=False)
    columns: Optional[SelectColumns] = None
    from_clause: Optional[FromClause] = None
    where_clause: Optional[WhereClause] = None
    group_by: Optional[GroupByClause] = None
    having: Optional[HavingClause] = None
    order_by: Optional[OrderByClause] = None
    limit: Optional[LimitClause] = None

    def __repr__(self) -> str:
        parts = [str(self.columns)]
        if self.from_clause:
            parts.append(str(self.from_clause))
        if self.where_clause:
            parts.append(str(self.where_clause))
        if self.group_by:
            parts.append(str(self.group_by))
        if self.having:
            parts.append(str(self.having))
        if self.order_by:
            parts.append(str(self.order_by))
        if self.limit:
            parts.append(str(self.limit))
        return " ".join(parts)


@dataclass
class InsertStatement(ASTNode):
    """INSERT 语句节点"""
    node_type: NodeType = field(default=NodeType.INSERT_STMT, init=False)
    table: Optional[TableRef] = None
    columns: List[str] = field(default_factory=list)
    values: Optional[InsertValues] = None
    select: Optional[SelectStatement] = None

    def __repr__(self) -> str:
        cols = f"({', '.join(self.columns)})" if self.columns else ""
        if self.select:
            return f"INSERT INTO {self.table}{cols} {self.select}"
        return f"INSERT INTO {self.table}{cols} {self.values}"


@dataclass
class UpdateStatement(ASTNode):
    """UPDATE 语句节点"""
    node_type: NodeType = field(default=NodeType.UPDATE_SET, init=False)
    table: Optional[TableRef] = None
    set_clause: Optional[UpdateSet] = None
    where_clause: Optional[WhereClause] = None

    def __repr__(self) -> str:
        parts = [f"UPDATE {self.table}", str(self.set_clause)]
        if self.where_clause:
            parts.append(str(self.where_clause))
        return " ".join(parts)


@dataclass
class DeleteStatement(ASTNode):
    """DELETE 语句节点"""
    node_type: NodeType = field(default=NodeType.DELETE_STMT, init=False)
    table: Optional[TableRef] = None
    where_clause: Optional[WhereClause] = None

    def __repr__(self) -> str:
        parts = [f"DELETE FROM {self.table}"]
        if self.where_clause:
            parts.append(str(self.where_clause))
        return " ".join(parts)
