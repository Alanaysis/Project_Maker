# 真值表生成器

"""
真值表生成器模块

本模块提供真值表的生成功能。
"""

from typing import List, Tuple, Dict

from .gates import Gate
from .circuit import Circuit


class TruthTableGenerator:
    """真值表生成器

    用于生成和格式化真值表。

    Examples:
        >>> from logic_gates import AndGate, TruthTableGenerator
        >>> gate = AndGate()
        >>> print(TruthTableGenerator.generate(gate))
        AND Gate Truth Table
        --------------------
        | IN0 | IN1 | OUT |
        --------------------
        |  0  |  0  |  0  |
        |  0  |  1  |  0  |
        |  1  |  0  |  0  |
        |  1  |  1  |  1  |
        --------------------
    """

    @staticmethod
    def generate(gate: Gate) -> str:
        """生成格式化的真值表

        Args:
            gate: 逻辑门实例

        Returns:
            str: 格式化的真值表字符串

        Examples:
            >>> gate = AndGate()
            >>> table = TruthTableGenerator.generate(gate)
            >>> "AND" in table
            True
        """
        table = gate.truth_table()
        return TruthTableGenerator.format_table(table, f"{gate.name} Gate Truth Table")

    @staticmethod
    def format_table(table: List[Tuple[List[int], int]], name: str = "") -> str:
        """格式化真值表

        Args:
            table: 真值表数据，每个元素为([输入组合], 输出)
            name: 表名称

        Returns:
            str: 格式化的字符串

        Examples:
            >>> table = [([0, 0], 0), ([0, 1], 0), ([1, 0], 0), ([1, 1], 1)]
            >>> print(TruthTableGenerator.format_table(table, "AND"))
            AND
            --------------------
            | IN0 | IN1 | OUT |
            --------------------
            |  0  |  0  |  0  |
            |  0  |  1  |  0  |
            |  1  |  0  |  0  |
            |  1  |  1  |  1  |
            --------------------
        """
        if not table:
            return ""

        # 计算列数
        num_inputs = len(table[0][0])

        # 计算列宽
        col_width = 4

        # 生成表头
        headers = [f"IN{i}" for i in range(num_inputs)] + ["OUT"]
        header_line = "| " + " | ".join([f"{h:^{col_width}}" for h in headers]) + " |"

        # 生成分隔线
        separator = "-" * len(header_line)

        # 生成数据行
        rows = []
        for inputs, output in table:
            row_inputs = [f"{inp:^{col_width}}" for inp in inputs]
            row_output = f"{output:^{col_width}}"
            row = "| " + " | ".join(row_inputs + [row_output]) + " |"
            rows.append(row)

        # 组合结果
        result = [name, separator, header_line, separator]
        result.extend(rows)
        result.append(separator)

        return "\n".join(result)

    @staticmethod
    def generate_circuit_table(circuit: Circuit) -> str:
        """生成电路真值表

        Args:
            circuit: 电路实例

        Returns:
            str: 格式化的真值表字符串

        Examples:
            >>> circuit = Circuit("Test")
            >>> circuit.add_gate(AndGate(), "AND1")
            >>> table = TruthTableGenerator.generate_circuit_table(circuit)
        """
        table = circuit.get_truth_table()
        return TruthTableGenerator.format_circuit_table(table, f"{circuit.name} Truth Table")

    @staticmethod
    def format_circuit_table(table: List[Dict], name: str = "") -> str:
        """格式化电路真值表

        Args:
            table: 真值表数据
            name: 表名称

        Returns:
            str: 格式化的字符串
        """
        if not table:
            return ""

        # 获取输入和输出名称
        first_row = table[0]
        input_names = list(first_row["inputs"].keys())
        output_names = list(first_row["outputs"].keys())

        # 计算列宽
        all_names = input_names + output_names
        col_width = max(len(name) for name in all_names) + 2

        # 生成表头
        header_line = "| " + " | ".join([f"{n:^{col_width}}" for n in all_names]) + " |"

        # 生成分隔线
        separator = "-" * len(header_line)

        # 生成数据行
        rows = []
        for row in table:
            input_values = [f"{row['inputs'][n]:^{col_width}}" for n in input_names]
            output_values = [f"{row['outputs'][n]:^{col_width}}" for n in output_names]
            row_line = "| " + " | ".join(input_values + output_values) + " |"
            rows.append(row_line)

        # 组合结果
        result = [name, separator, header_line, separator]
        result.extend(rows)
        result.append(separator)

        return "\n".join(result)

    @staticmethod
    def to_dict(table: List[Tuple[List[int], int]]) -> List[Dict]:
        """将真值表转换为字典格式

        Args:
            table: 真值表数据

        Returns:
            List[Dict]: 字典格式的真值表
        """
        result = []
        for inputs, output in table:
            row = {
                "inputs": {f"IN{i}": v for i, v in enumerate(inputs)},
                "output": output
            }
            result.append(row)
        return result

    @staticmethod
    def to_csv(table: List[Tuple[List[int], int]], name: str = "") -> str:
        """将真值表转换为CSV格式

        Args:
            table: 真值表数据
            name: 表名称

        Returns:
            str: CSV格式的字符串
        """
        if not table:
            return ""

        num_inputs = len(table[0][0])

        # 生成表头
        headers = [f"IN{i}" for i in range(num_inputs)] + ["OUT"]
        lines = [",".join(headers)]

        # 生成数据行
        for inputs, output in table:
            row = ",".join([str(v) for v in inputs] + [str(output)])
            lines.append(row)

        return "\n".join(lines)

    @staticmethod
    def to_json(table: List[Tuple[List[int], int]]) -> List[Dict]:
        """将真值表转换为JSON格式

        Args:
            table: 真值表数据

        Returns:
            List[Dict]: JSON格式的真值表
        """
        result = []
        for inputs, output in table:
            row = {
                "inputs": list(inputs),
                "output": output
            }
            result.append(row)
        return result
