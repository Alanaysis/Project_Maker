"""
查询执行器 - 执行 AST 并返回结果
"""

from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from .ast_nodes import *


@dataclass
class Column:
    """列定义"""
    name: str
    data_type: str = "text"  # "text", "integer", "float", "boolean"
    nullable: bool = True


@dataclass
class Table:
    """内存表"""
    name: str
    columns: List[Column]
    rows: List[Dict[str, Any]] = field(default_factory=list)

    def add_row(self, row: Dict[str, Any]) -> None:
        """添加一行数据"""
        self.rows.append(row)

    def get_column_names(self) -> List[str]:
        """获取所有列名"""
        return [col.name for col in self.columns]

    def get_column_index(self, name: str) -> int:
        """获取列索引"""
        for i, col in enumerate(self.columns):
            if col.name == name:
                return i
        return -1


@dataclass
class QueryResult:
    """查询结果"""
    columns: List[str]
    rows: List[List[Any]]
    affected_rows: int = 0

    def __repr__(self) -> str:
        if not self.rows:
            return "Empty result set"

        # 计算列宽
        widths = [len(col) for col in self.columns]
        for row in self.rows:
            for i, val in enumerate(row):
                widths[i] = max(widths[i], len(str(val)))

        # 构建表格
        header = " | ".join(col.ljust(widths[i]) for i, col in enumerate(self.columns))
        separator = "-+-".join("-" * w for w in widths)

        lines = [header, separator]
        for row in self.rows:
            line = " | ".join(str(val).ljust(widths[i]) for i, val in enumerate(row))
            lines.append(line)

        return "\n".join(lines)


class ExecutionError(Exception):
    """执行错误"""
    pass


class Executor:
    """查询执行器"""

    def __init__(self):
        self.tables: Dict[str, Table] = {}

    def create_table(self, name: str, columns: List[Column]) -> Table:
        """创建表"""
        if name in self.tables:
            raise ExecutionError(f"表已存在: {name}")
        table = Table(name=name, columns=columns)
        self.tables[name] = table
        return table

    def get_table(self, name: str) -> Table:
        """获取表"""
        if name not in self.tables:
            raise ExecutionError(f"表不存在: {name}")
        return self.tables[name]

    def execute(self, node: ASTNode) -> QueryResult:
        """执行查询"""
        if isinstance(node, SelectStatement):
            return self.execute_select(node)
        elif isinstance(node, InsertStatement):
            return self.execute_insert(node)
        elif isinstance(node, UpdateStatement):
            return self.execute_update(node)
        elif isinstance(node, DeleteStatement):
            return self.execute_delete(node)
        else:
            raise ExecutionError(f"不支持的语句类型: {type(node).__name__}")

    # ========================================================================
    # SELECT 执行
    # ========================================================================

    def execute_select(self, stmt: SelectStatement) -> QueryResult:
        """执行 SELECT 语句"""
        # 获取数据源
        if stmt.from_clause:
            rows, column_map = self._resolve_from(stmt.from_clause)
        else:
            # 没有 FROM 子句 (SELECT 1, SELECT NOW(), etc.)
            rows = [{}]
            column_map = {}

        # 应用 WHERE
        if stmt.where_clause:
            rows = self._apply_where(rows, stmt.where_clause.condition, column_map)

        # 应用 GROUP BY
        if stmt.group_by:
            rows = self._apply_group_by(rows, stmt.group_by, column_map, stmt.columns)

        # 应用 HAVING
        if stmt.having:
            rows = self._apply_having(rows, stmt.having.condition, column_map)

        # 应用 ORDER BY
        if stmt.order_by:
            rows = self._apply_order_by(rows, stmt.order_by, column_map)

        # 应用 LIMIT
        if stmt.limit:
            rows = self._apply_limit(rows, stmt.limit)

        # 构建结果
        result_columns, result_rows = self._build_select_result(rows, stmt.columns, column_map)

        return QueryResult(columns=result_columns, rows=result_rows)

    def _resolve_from(self, from_clause: FromClause) -> Tuple[List[Dict[str, Any]], Dict[str, str]]:
        """解析 FROM 子句，返回行数据和列映射"""
        if not from_clause.tables:
            return [{}], {}

        # 获取第一个表
        first_table_ref = from_clause.tables[0]
        table = self.get_table(first_table_ref.table_name)
        alias = first_table_ref.alias or first_table_ref.table_name

        # 构建列映射 (column_ref -> table_alias)
        column_map = {}
        for col in table.columns:
            column_map[col.name] = alias
            column_map[f"{alias}.{col.name}"] = alias

        # 构建行数据
        rows = []
        for row in table.rows:
            new_row = {}
            for key, value in row.items():
                new_row[f"{alias}.{key}"] = value
                new_row[key] = value
            rows.append(new_row)

        # 处理多表（笛卡尔积）
        for table_ref in from_clause.tables[1:]:
            other_table = self.get_table(table_ref.table_name)
            other_alias = other_table_ref.alias or table_ref.table_name

            # 更新列映射
            for col in other_table.columns:
                column_map[col.name] = other_alias
                column_map[f"{other_alias}.{col.name}"] = other_alias

            # 笛卡尔积
            new_rows = []
            for row in rows:
                for other_row in other_table.rows:
                    combined = row.copy()
                    for key, value in other_row.items():
                        combined[f"{other_alias}.{key}"] = value
                        combined[key] = value
                    new_rows.append(combined)
            rows = new_rows

        # 处理 JOIN
        for join in from_clause.joins:
            rows = self._apply_join(rows, join, column_map)

        return rows, column_map

    def _apply_join(self, rows: List[Dict[str, Any]], join: JoinClause,
                    column_map: Dict[str, str]) -> List[Dict[str, Any]]:
        """应用 JOIN"""
        join_table = self.get_table(join.table.table_name)
        join_alias = join.table.alias or join.table.table_name

        # 更新列映射
        for col in join_table.columns:
            column_map[col.name] = join_alias
            column_map[f"{join_alias}.{col.name}"] = join_alias

        if join.join_type == JoinType.CROSS:
            # 笛卡尔积
            new_rows = []
            for row in rows:
                for join_row in join_table.rows:
                    combined = row.copy()
                    for key, value in join_row.items():
                        combined[f"{join_alias}.{key}"] = value
                        combined[key] = value
                    new_rows.append(combined)
            return new_rows

        # INNER JOIN / LEFT JOIN / RIGHT JOIN / FULL JOIN
        new_rows = []
        matched_join_rows = set()

        for row in rows:
            matched = False
            for i, join_row in enumerate(join_table.rows):
                combined = row.copy()
                for key, value in join_row.items():
                    combined[f"{join_alias}.{key}"] = value
                    combined[key] = value

                # 检查 ON 条件
                if join.on_condition:
                    if self._evaluate_condition(combined, join.on_condition, column_map):
                        new_rows.append(combined)
                        matched = True
                        matched_join_rows.add(i)
                else:
                    new_rows.append(combined)
                    matched = True
                    matched_join_rows.add(i)

            # LEFT JOIN: 即使没有匹配也要保留左表行
            if not matched and join.join_type == JoinType.LEFT:
                combined = row.copy()
                for col in join_table.columns:
                    combined[f"{join_alias}.{col.name}"] = None
                    combined[col.name] = None
                new_rows.append(combined)

        # RIGHT JOIN: 添加未匹配的右表行
        if join.join_type == JoinType.RIGHT:
            for i, join_row in enumerate(join_table.rows):
                if i not in matched_join_rows:
                    combined = {}
                    for col in join_table.columns:
                        combined[f"{join_alias}.{col.name}"] = join_row.get(col.name)
                        combined[col.name] = join_row.get(col.name)
                    new_rows.append(combined)

        return new_rows

    def _apply_where(self, rows: List[Dict[str, Any]], condition: ASTNode,
                     column_map: Dict[str, str]) -> List[Dict[str, Any]]:
        """应用 WHERE 条件"""
        return [row for row in rows if self._evaluate_condition(row, condition, column_map)]

    def _apply_group_by(self, rows: List[Dict[str, Any]], group_by: GroupByClause,
                        column_map: Dict[str, str], select_columns: SelectColumns) -> List[Dict[str, Any]]:
        """应用 GROUP BY"""
        # 分组
        groups = {}
        for row in rows:
            key = tuple(self._get_column_value(row, col, column_map) for col in group_by.columns)
            if key not in groups:
                groups[key] = []
            groups[key].append(row)

        # 构建结果
        result_rows = []
        for key, group in groups.items():
            result_row = {}
            # 添加分组列
            for i, col in enumerate(group_by.columns):
                col_name = self._get_column_name(col)
                result_row[col_name] = key[i]

            # 计算聚合函数
            if select_columns:
                for col_expr in select_columns.columns:
                    if isinstance(col_expr, FuncCall):
                        agg_value = self._calculate_aggregate(col_expr, group, column_map)
                        # 存储到默认别名和显式别名
                        default_alias = f"{col_expr.func_name}()"
                        result_row[default_alias] = agg_value
                        if col_expr.alias:
                            result_row[col_expr.alias] = agg_value

            result_rows.append(result_row)

        return result_rows

    def _apply_having(self, rows: List[Dict[str, Any]], condition: ASTNode,
                      column_map: Dict[str, str]) -> List[Dict[str, Any]]:
        """应用 HAVING 条件"""
        return [row for row in rows if self._evaluate_condition(row, condition, column_map)]

    def _apply_order_by(self, rows: List[Dict[str, Any]], order_by: OrderByClause,
                        column_map: Dict[str, str]) -> List[Dict[str, Any]]:
        """应用 ORDER BY"""
        def sort_key(row):
            keys = []
            for item in order_by.items:
                value = self._evaluate_expression(row, item.expr, column_map)
                # 处理 None 值
                if value is None:
                    value = (1,)  # NULL 排在最后
                else:
                    value = (0, value)
                if item.direction == SortDirection.DESC:
                    # 降序：反转比较
                    if isinstance(value, tuple) and len(value) == 2:
                        value = (value[0], -value[1] if isinstance(value[1], (int, float)) else value[1])
                keys.append(value)
            return keys

        return sorted(rows, key=sort_key)

    def _apply_limit(self, rows: List[Dict[str, Any]], limit: LimitClause) -> List[Dict[str, Any]]:
        """应用 LIMIT"""
        start = limit.offset or 0
        end = start + limit.limit
        return rows[start:end]

    def _build_select_result(self, rows: List[Dict[str, Any]], select_columns: SelectColumns,
                             column_map: Dict[str, str]) -> Tuple[List[str], List[List[Any]]]:
        """构建 SELECT 结果"""
        if not select_columns or not select_columns.columns:
            return [], []

        result_columns = []
        result_rows = []

        # 处理 SELECT *
        if len(select_columns.columns) == 1 and isinstance(select_columns.columns[0], Star):
            star = select_columns.columns[0]
            if rows:
                # 获取所有列名（去重，只保留不带表前缀的列名）
                all_columns = []
                seen = set()
                for col in rows[0].keys():
                    # 只保留不带表前缀的列名
                    if '.' not in col:
                        if col not in seen:
                            all_columns.append(col)
                            seen.add(col)
                result_columns = all_columns
                for row in rows:
                    result_rows.append([row.get(col) for col in all_columns])
            return result_columns, result_rows

        # 处理具体列
        for col_expr in select_columns.columns:
            if isinstance(col_expr, ColumnRef):
                col_name = col_expr.alias or col_expr.column
                result_columns.append(col_name)
            elif isinstance(col_expr, FuncCall):
                col_name = col_expr.alias or f"{col_expr.func_name}()"
                result_columns.append(col_name)
            elif isinstance(col_expr, Star):
                if rows:
                    for key in rows[0].keys():
                        result_columns.append(key)
            else:
                result_columns.append(str(col_expr))

        # 构建行数据
        for row in rows:
            result_row = []
            for col_expr in select_columns.columns:
                # 检查是否是聚合函数且值已在行中
                if isinstance(col_expr, FuncCall):
                    col_name = col_expr.alias or f"{col_expr.func_name}()"
                    if col_name in row:
                        result_row.append(row[col_name])
                    else:
                        value = self._evaluate_expression(row, col_expr, column_map)
                        result_row.append(value)
                else:
                    value = self._evaluate_expression(row, col_expr, column_map)
                    result_row.append(value)
            result_rows.append(result_row)

        # 处理 DISTINCT
        if select_columns.distinct:
            seen = set()
            unique_rows = []
            for row in result_rows:
                key = tuple(row)
                if key not in seen:
                    seen.add(key)
                    unique_rows.append(row)
            result_rows = unique_rows

        return result_columns, result_rows

    # ========================================================================
    # INSERT 执行
    # ========================================================================

    def execute_insert(self, stmt: InsertStatement) -> QueryResult:
        """执行 INSERT 语句"""
        table = self.get_table(stmt.table.table_name)

        if stmt.values:
            # INSERT INTO ... VALUES ...
            count = 0
            for row_values in stmt.values.values:
                if len(row_values) != len(table.columns):
                    if stmt.columns:
                        # 指定了列名
                        if len(row_values) != len(stmt.columns):
                            raise ExecutionError(f"列数不匹配: 期望 {len(stmt.columns)}，得到 {len(row_values)}")
                    else:
                        raise ExecutionError(f"列数不匹配: 期望 {len(table.columns)}，得到 {len(row_values)}")

                row = {}
                if stmt.columns:
                    # 按指定列名插入
                    for i, col_name in enumerate(stmt.columns):
                        value = self._evaluate_literal(row_values[i])
                        row[col_name] = value
                    # 填充未指定的列
                    for col in table.columns:
                        if col.name not in row:
                            row[col.name] = None
                else:
                    # 按列顺序插入
                    for i, col in enumerate(table.columns):
                        value = self._evaluate_literal(row_values[i])
                        row[col.name] = value

                table.add_row(row)
                count += 1

            return QueryResult(columns=[], rows=[], affected_rows=count)

        elif stmt.select:
            # INSERT INTO ... SELECT ...
            select_result = self.execute_select(stmt.select)
            count = 0
            for row_data in select_result.rows:
                row = {}
                for i, col_name in enumerate(stmt.columns or table.get_column_names()):
                    if i < len(row_data):
                        row[col_name] = row_data[i]
                table.add_row(row)
                count += 1

            return QueryResult(columns=[], rows=[], affected_rows=count)

        return QueryResult(columns=[], rows=[], affected_rows=0)

    # ========================================================================
    # UPDATE 执行
    # ========================================================================

    def execute_update(self, stmt: UpdateStatement) -> QueryResult:
        """执行 UPDATE 语句"""
        table = self.get_table(stmt.table.table_name)
        count = 0

        for row in table.rows:
            # 检查 WHERE 条件
            if stmt.where_clause:
                if not self._evaluate_condition(row, stmt.where_clause.condition, {}):
                    continue

            # 应用 SET
            if stmt.set_clause:
                for col_name, value_expr in stmt.set_clause.assignments:
                    value = self._evaluate_expression(row, value_expr, {})
                    row[col_name] = value
                    count += 1

        return QueryResult(columns=[], rows=[], affected_rows=count)

    # ========================================================================
    # DELETE 执行
    # ========================================================================

    def execute_delete(self, stmt: DeleteStatement) -> QueryResult:
        """执行 DELETE 语句"""
        table = self.get_table(stmt.table.table_name)

        if stmt.where_clause:
            # 保留不满足条件的行
            original_count = len(table.rows)
            table.rows = [row for row in table.rows
                         if not self._evaluate_condition(row, stmt.where_clause.condition, {})]
            count = original_count - len(table.rows)
        else:
            # 删除所有行
            count = len(table.rows)
            table.rows = []

        return QueryResult(columns=[], rows=[], affected_rows=count)

    # ========================================================================
    # 条件求值
    # ========================================================================

    def _evaluate_condition(self, row: Dict[str, Any], condition: ASTNode,
                           column_map: Dict[str, str]) -> bool:
        """求值条件表达式"""
        if condition is None:
            return True

        if isinstance(condition, AndExpr):
            left = self._evaluate_condition(row, condition.left, column_map)
            right = self._evaluate_condition(row, condition.right, column_map)
            return left and right

        if isinstance(condition, OrExpr):
            left = self._evaluate_condition(row, condition.left, column_map)
            right = self._evaluate_condition(row, condition.right, column_map)
            return left or right

        if isinstance(condition, NotExpr):
            return not self._evaluate_condition(row, condition.operand, column_map)

        if isinstance(condition, CompareExpr):
            left_val = self._evaluate_expression(row, condition.left, column_map)
            right_val = self._evaluate_expression(row, condition.right, column_map)
            return self._compare(left_val, condition.op, right_val)

        if isinstance(condition, InExpr):
            operand_val = self._evaluate_expression(row, condition.operand, column_map)
            if condition.subquery:
                # 子查询 IN
                if isinstance(condition.subquery, Subquery):
                    sub_result = self.execute_select(condition.subquery.query)
                else:
                    sub_result = self.execute_select(condition.subquery)
                values = [row[0] for row in sub_result.rows]
            else:
                values = [self._evaluate_expression(row, v, column_map) for v in condition.values]
            result = operand_val in values
            return not result if condition.not_in else result

        if isinstance(condition, BetweenExpr):
            operand_val = self._evaluate_expression(row, condition.operand, column_map)
            low_val = self._evaluate_expression(row, condition.low, column_map)
            high_val = self._evaluate_expression(row, condition.high, column_map)
            result = low_val <= operand_val <= high_val
            return not result if condition.not_between else result

        if isinstance(condition, LikeExpr):
            operand_val = str(self._evaluate_expression(row, condition.operand, column_map))
            pattern_val = str(self._evaluate_expression(row, condition.pattern, column_map))
            result = self._like_match(operand_val, pattern_val)
            return not result if condition.not_like else result

        if isinstance(condition, IsNullExpr):
            operand_val = self._evaluate_expression(row, condition.operand, column_map)
            is_null = operand_val is None
            return is_null if condition.is_null else not is_null

        if isinstance(condition, ExistsExpr):
            sub_result = self.execute_select(condition.subquery.query)
            return len(sub_result.rows) > 0 if not condition.not_exists else len(sub_result.rows) == 0

        return True

    def _compare(self, left: Any, op: str, right: Any) -> bool:
        """比较操作"""
        if left is None or right is None:
            if op == '=':
                return left is None and right is None
            if op in ('<>', '!='):
                return not (left is None and right is None)
            return False

        if op == '=':
            return left == right
        elif op in ('<>', '!='):
            return left != right
        elif op == '<':
            return left < right
        elif op == '>':
            return left > right
        elif op == '<=':
            return left <= right
        elif op == '>=':
            return left >= right
        return False

    def _like_match(self, text: str, pattern: str) -> bool:
        """LIKE 模式匹配"""
        # 将 LIKE 模式转换为正则表达式
        import re
        regex = pattern.replace('%', '.*').replace('_', '.')
        regex = f'^{regex}$'
        return bool(re.match(regex, text, re.IGNORECASE))

    # ========================================================================
    # 表达式求值
    # ========================================================================

    def _evaluate_expression(self, row: Dict[str, Any], expr: ASTNode,
                            column_map: Dict[str, str]) -> Any:
        """求值表达式"""
        if expr is None:
            return None

        if isinstance(expr, Literal):
            return expr.value

        if isinstance(expr, ColumnRef):
            # 尝试不同的列名格式
            if expr.table:
                key = f"{expr.table}.{expr.column}"
                if key in row:
                    return row[key]
            # 尝试不带表前缀
            if expr.column in row:
                return row[expr.column]
            # 尝试带表前缀
            if expr.column in column_map:
                table_alias = column_map[expr.column]
                key = f"{table_alias}.{expr.column}"
                if key in row:
                    return row[key]
            raise ExecutionError(f"列不存在: {expr}")

        if isinstance(expr, Star):
            return None

        if isinstance(expr, BinaryOp):
            left = self._evaluate_expression(row, expr.left, column_map)
            right = self._evaluate_expression(row, expr.right, column_map)
            return self._eval_binary(expr.op, left, right)

        if isinstance(expr, UnaryOp):
            operand = self._evaluate_expression(row, expr.operand, column_map)
            if expr.op == '-':
                return -operand
            return operand

        if isinstance(expr, FuncCall):
            # 检查是否是聚合函数且值已在行中（GROUP BY 后）
            if expr.func_name in ('COUNT', 'SUM', 'AVG', 'MIN', 'MAX'):
                alias = expr.alias or f"{expr.func_name}()"
                if alias in row:
                    return row[alias]
            return self._eval_function(expr, row, column_map)

        if isinstance(expr, Literal):
            return expr.value

        return None

    def _eval_binary(self, op: str, left: Any, right: Any) -> Any:
        """计算二元运算"""
        if left is None or right is None:
            return None

        if op == '+':
            return left + right
        elif op == '-':
            return left - right
        elif op == '*':
            return left * right
        elif op == '/':
            if right == 0:
                return None
            return left / right
        elif op == '%':
            if right == 0:
                return None
            return left % right
        return None

    def _eval_function(self, func: FuncCall, row: Dict[str, Any],
                      column_map: Dict[str, str]) -> Any:
        """计算函数"""
        # 聚合函数需要特殊处理
        if func.func_name in ('COUNT', 'SUM', 'AVG', 'MIN', 'MAX'):
            # 这里返回 None，实际聚合在 GROUP BY 中处理
            return None

        # 标量函数
        if func.func_name == 'UPPER':
            val = self._evaluate_expression(row, func.args[0], column_map)
            return str(val).upper() if val else None
        elif func.func_name == 'LOWER':
            val = self._evaluate_expression(row, func.args[0], column_map)
            return str(val).lower() if val else None
        elif func.func_name == 'LENGTH':
            val = self._evaluate_expression(row, func.args[0], column_map)
            return len(str(val)) if val else 0
        elif func.func_name == 'COALESCE':
            for arg in func.args:
                val = self._evaluate_expression(row, arg, column_map)
                if val is not None:
                    return val
            return None

        return None

    def _calculate_aggregate(self, func: FuncCall, rows: List[Dict[str, Any]],
                            column_map: Dict[str, str]) -> Any:
        """计算聚合函数"""
        if func.func_name == 'COUNT':
            if isinstance(func.args[0], Star):
                return len(rows)
            count = 0
            for row in rows:
                val = self._evaluate_expression(row, func.args[0], column_map)
                if val is not None:
                    count += 1
            return count

        elif func.func_name == 'SUM':
            total = 0
            for row in rows:
                val = self._evaluate_expression(row, func.args[0], column_map)
                if val is not None:
                    total += val
            return total

        elif func.func_name == 'AVG':
            total = 0
            count = 0
            for row in rows:
                val = self._evaluate_expression(row, func.args[0], column_map)
                if val is not None:
                    total += val
                    count += 1
            return total / count if count > 0 else None

        elif func.func_name == 'MIN':
            values = []
            for row in rows:
                val = self._evaluate_expression(row, func.args[0], column_map)
                if val is not None:
                    values.append(val)
            return min(values) if values else None

        elif func.func_name == 'MAX':
            values = []
            for row in rows:
                val = self._evaluate_expression(row, func.args[0], column_map)
                if val is not None:
                    values.append(val)
            return max(values) if values else None

        return None

    # ========================================================================
    # 辅助方法
    # ========================================================================

    def _get_column_value(self, row: Dict[str, Any], col_expr: ASTNode,
                         column_map: Dict[str, str]) -> Any:
        """获取列值"""
        return self._evaluate_expression(row, col_expr, column_map)

    def _get_column_name(self, col_expr: ASTNode) -> str:
        """获取列名"""
        if isinstance(col_expr, ColumnRef):
            return col_expr.alias or col_expr.column
        elif isinstance(col_expr, FuncCall):
            return col_expr.alias or f"{col_expr.func_name}()"
        return str(col_expr)

    def _evaluate_literal(self, expr: ASTNode) -> Any:
        """求值字面量"""
        if isinstance(expr, Literal):
            return expr.value
        return None


def execute_query(node: ASTNode, executor: Executor) -> QueryResult:
    """便捷函数：执行查询"""
    return executor.execute(node)
