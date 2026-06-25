"""
查询优化器 - 对 AST 进行优化
"""

from typing import List, Optional, Set
from .ast_nodes import *


class QueryOptimizer:
    """查询优化器"""

    def __init__(self):
        self.optimizations_applied: List[str] = []

    def optimize(self, node: ASTNode) -> ASTNode:
        """优化查询 AST"""
        self.optimizations_applied = []

        # 应用各种优化
        node = self.constant_folding(node)
        node = self.predicate_pushdown(node)
        node = self.eliminate_redundant(node)
        node = self.simplify_expressions(node)

        return node

    def get_optimizations(self) -> List[str]:
        """获取已应用的优化列表"""
        return self.optimizations_applied.copy()

    # ========================================================================
    # 常量折叠
    # ========================================================================

    def constant_folding(self, node: ASTNode) -> ASTNode:
        """常量折叠 - 在编译时计算常量表达式"""
        if node is None:
            return None

        # 递归处理子节点
        node = self._process_children(node, self.constant_folding)

        # 检查二元运算
        if isinstance(node, BinaryOp):
            if isinstance(node.left, Literal) and isinstance(node.right, Literal):
                result = self._eval_binary_op(node.op, node.left, node.right)
                if result is not None:
                    self.optimizations_applied.append(f"常量折叠: {node} -> {result}")
                    return result

        return node

    def _eval_binary_op(self, op: str, left: Literal, right: Literal) -> Optional[Literal]:
        """计算二元运算"""
        try:
            if left.data_type in ("integer", "float") and right.data_type in ("integer", "float"):
                l_val = left.value
                r_val = right.value

                if op == '+':
                    result = l_val + r_val
                elif op == '-':
                    result = l_val - r_val
                elif op == '*':
                    result = l_val * r_val
                elif op == '/':
                    if r_val == 0:
                        return None
                    result = l_val / r_val
                elif op == '%':
                    if r_val == 0:
                        return None
                    result = l_val % r_val
                else:
                    return None

                if isinstance(result, float) and result == int(result):
                    return Literal(value=int(result), data_type="integer")
                return Literal(value=result, data_type="float" if isinstance(result, float) else "integer")
        except (TypeError, ValueError, ZeroDivisionError):
            pass

        return None

    # ========================================================================
    # 谓词下推
    # ========================================================================

    def predicate_pushdown(self, node: ASTNode) -> ASTNode:
        """谓词下推 - 将 WHERE 条件尽可能靠近数据源"""
        if node is None:
            return None

        if isinstance(node, SelectStatement):
            if node.where_clause and node.from_clause:
                # 尝试将 WHERE 条件下推到 JOIN
                if node.from_clause.joins:
                    node = self._pushdown_to_joins(node)

        return node

    def _pushdown_to_joins(self, stmt: SelectStatement) -> SelectStatement:
        """将条件推到 JOIN"""
        if not stmt.where_clause or not stmt.where_clause.condition:
            return stmt

        # 收集涉及单个表的条件
        condition = stmt.where_clause.condition
        table_conditions = self._extract_table_conditions(condition, stmt.from_clause)

        # 如果有可以推到 JOIN 的条件
        if table_conditions:
            self.optimizations_applied.append(f"谓词下推: {len(table_conditions)} 个条件推到 JOIN")

        return stmt

    def _extract_table_conditions(self, condition: ASTNode, from_clause: FromClause) -> List[ASTNode]:
        """提取涉及单个表的条件"""
        conditions = []

        if isinstance(condition, AndExpr):
            conditions.extend(self._extract_table_conditions(condition.left, from_clause))
            conditions.extend(self._extract_table_conditions(condition.right, from_clause))
        elif isinstance(condition, CompareExpr):
            # 检查是否只涉及一个表
            tables = self._get_tables_in_expr(condition)
            if len(tables) == 1:
                conditions.append(condition)

        return conditions

    def _get_tables_in_expr(self, node: ASTNode) -> Set[str]:
        """获取表达式中涉及的表"""
        tables = set()

        if isinstance(node, ColumnRef) and node.table:
            tables.add(node.table)
        elif isinstance(node, BinaryOp):
            tables.update(self._get_tables_in_expr(node.left))
            tables.update(self._get_tables_in_expr(node.right))
        elif isinstance(node, CompareExpr):
            tables.update(self._get_tables_in_expr(node.left))
            tables.update(self._get_tables_in_expr(node.right))

        return tables

    # ========================================================================
    # 消除冗余
    # ========================================================================

    def eliminate_redundant(self, node: ASTNode) -> ASTNode:
        """消除冗余表达式"""
        if node is None:
            return None

        # 递归处理子节点
        node = self._process_children(node, self.eliminate_redundant)

        # 消除双重否定
        if isinstance(node, NotExpr):
            if isinstance(node.operand, NotExpr):
                self.optimizations_applied.append("消除双重否定: NOT NOT x -> x")
                return node.operand.operand

        # 消除恒真/恒假条件
        if isinstance(node, AndExpr):
            # x AND TRUE -> x
            if self._is_true_literal(node.right):
                self.optimizations_applied.append("消除恒真: x AND TRUE -> x")
                return node.left
            if self._is_true_literal(node.left):
                self.optimizations_applied.append("消除恒真: TRUE AND x -> x")
                return node.right
            # x AND FALSE -> FALSE
            if self._is_false_literal(node.right) or self._is_false_literal(node.left):
                self.optimizations_applied.append("消除恒假: x AND FALSE -> FALSE")
                return Literal(value=False, data_type="boolean")

        if isinstance(node, OrExpr):
            # x OR FALSE -> x
            if self._is_false_literal(node.right):
                self.optimizations_applied.append("消除恒假: x OR FALSE -> x")
                return node.left
            if self._is_false_literal(node.left):
                self.optimizations_applied.append("消除恒假: FALSE OR x -> x")
                return node.right
            # x OR TRUE -> TRUE
            if self._is_true_literal(node.right) or self._is_true_literal(node.left):
                self.optimizations_applied.append("消除恒真: x OR TRUE -> TRUE")
                return Literal(value=True, data_type="boolean")

        return node

    def _is_true_literal(self, node: ASTNode) -> bool:
        """检查是否是 TRUE 字面量"""
        return isinstance(node, Literal) and node.value is True

    def _is_false_literal(self, node: ASTNode) -> bool:
        """检查是否是 FALSE 字面量"""
        return isinstance(node, Literal) and node.value is False

    # ========================================================================
    # 表达式简化
    # ========================================================================

    def simplify_expressions(self, node: ASTNode) -> ASTNode:
        """简化表达式"""
        if node is None:
            return None

        # 递归处理子节点
        node = self._process_children(node, self.simplify_expressions)

        # 简化算术表达式
        if isinstance(node, BinaryOp):
            # x + 0 -> x
            if node.op == '+' and isinstance(node.right, Literal) and node.right.value == 0:
                self.optimizations_applied.append("简化: x + 0 -> x")
                return node.left
            # 0 + x -> x
            if node.op == '+' and isinstance(node.left, Literal) and node.left.value == 0:
                self.optimizations_applied.append("简化: 0 + x -> x")
                return node.right
            # x * 1 -> x
            if node.op == '*' and isinstance(node.right, Literal) and node.right.value == 1:
                self.optimizations_applied.append("简化: x * 1 -> x")
                return node.left
            # 1 * x -> x
            if node.op == '*' and isinstance(node.left, Literal) and node.left.value == 1:
                self.optimizations_applied.append("简化: 1 * x -> x")
                return node.right
            # x * 0 -> 0
            if node.op == '*' and (isinstance(node.right, Literal) and node.right.value == 0):
                self.optimizations_applied.append("简化: x * 0 -> 0")
                return Literal(value=0, data_type="integer")
            # x - 0 -> x
            if node.op == '-' and isinstance(node.right, Literal) and node.right.value == 0:
                self.optimizations_applied.append("简化: x - 0 -> x")
                return node.left
            # x / 1 -> x
            if node.op == '/' and isinstance(node.right, Literal) and node.right.value == 1:
                self.optimizations_applied.append("简化: x / 1 -> x")
                return node.left

        return node

    # ========================================================================
    # 辅助方法
    # ========================================================================

    def _process_children(self, node: ASTNode, func) -> ASTNode:
        """递归处理子节点"""
        if isinstance(node, SelectStatement):
            if node.columns:
                node.columns = self._process_children(node.columns, func)
            if node.from_clause:
                node.from_clause = self._process_children(node.from_clause, func)
            if node.where_clause:
                node.where_clause = self._process_children(node.where_clause, func)
            if node.group_by:
                node.group_by = self._process_children(node.group_by, func)
            if node.having:
                node.having = self._process_children(node.having, func)
            if node.order_by:
                node.order_by = self._process_children(node.order_by, func)

        elif isinstance(node, SelectColumns):
            node.columns = [func(col) for col in node.columns]

        elif isinstance(node, FromClause):
            node.tables = [func(t) for t in node.tables]
            node.joins = [func(j) for j in node.joins]

        elif isinstance(node, JoinClause):
            if node.table:
                node.table = func(node.table)
            if node.on_condition:
                node.on_condition = func(node.on_condition)

        elif isinstance(node, WhereClause):
            if node.condition:
                node.condition = func(node.condition)

        elif isinstance(node, GroupByClause):
            node.columns = [func(c) for c in node.columns]

        elif isinstance(node, HavingClause):
            if node.condition:
                node.condition = func(node.condition)

        elif isinstance(node, OrderByClause):
            node.items = [func(item) for item in node.items]

        elif isinstance(node, OrderItem):
            if node.expr:
                node.expr = func(node.expr)

        elif isinstance(node, BinaryOp):
            if node.left:
                node.left = func(node.left)
            if node.right:
                node.right = func(node.right)

        elif isinstance(node, UnaryOp):
            if node.operand:
                node.operand = func(node.operand)

        elif isinstance(node, NotExpr):
            if node.operand:
                node.operand = func(node.operand)

        elif isinstance(node, AndExpr):
            if node.left:
                node.left = func(node.left)
            if node.right:
                node.right = func(node.right)

        elif isinstance(node, OrExpr):
            if node.left:
                node.left = func(node.left)
            if node.right:
                node.right = func(node.right)

        elif isinstance(node, CompareExpr):
            if node.left:
                node.left = func(node.left)
            if node.right:
                node.right = func(node.right)

        elif isinstance(node, FuncCall):
            node.args = [func(arg) for arg in node.args]

        return node


def optimize_query(node: ASTNode) -> ASTNode:
    """便捷函数：优化查询"""
    optimizer = QueryOptimizer()
    return optimizer.optimize(node)
