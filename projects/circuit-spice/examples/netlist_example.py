"""
网表解析示例

演示 SPICE 网表文件的解析
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.netlist import NetlistParser, create_netlist_text
from src.circuit import Circuit
from src.dc_analysis import DCAnalysis


def main():
    print("=" * 60)
    print("SPICE 网表解析示例")
    print("=" * 60)

    # 示例 1: 简单分压器
    print("\n示例 1: 分压器网表")
    print("-" * 40)

    netlist_text = """
Voltage Divider Circuit
R1 1 2 1K
R2 2 0 2K
V1 0 1 DC 12
.dc V1 0 12 1
.end
"""
    print("网表内容:")
    print(netlist_text)

    parser = NetlistParser()
    result = parser.parse(netlist_text)

    print("解析结果:")
    print(f"  标题: {result.title}")
    print(f"  元件数: {len(result.components)}")
    print(f"  节点: {result.nodes}")
    print(f"  分析命令: {len(result.analyses)}")

    # 从网表创建电路
    circuit = Circuit.from_netlist(result)
    print("\n电路信息:")
    print(circuit.summary())

    # 直流分析
    analyzer = DCAnalysis(circuit)
    dc_result = analyzer.solve()

    print("\n直流分析结果:")
    for node, voltage in sorted(dc_result.node_voltages.items()):
        print(f"  V({node}) = {voltage:.4f} V")

    # 示例 2: RC 低通滤波器
    print("\n" + "=" * 60)
    print("示例 2: RC 低通滤波器网表")
    print("-" * 40)

    rc_netlist = """
RC Low Pass Filter
R1 1 2 1K
C1 2 0 1U
V1 0 1 AC 1
.ac dec 100 1 1MEG
.end
"""
    print("网表内容:")
    print(rc_netlist)

    result_rc = parser.parse(rc_netlist)

    print("解析结果:")
    print(f"  标题: {result_rc.title}")
    print(f"  元件数: {len(result_rc.components)}")

    for comp in result_rc.components:
        print(f"  {comp['name']}: {comp['type']} = {comp.get('value', 'N/A')}")

    # 示例 3: 创建网表文本
    print("\n" + "=" * 60)
    print("示例 3: 创建网表文本")
    print("-" * 40)

    components = [
        {'name': 'R1', 'node1': 1, 'node2': 2, 'value': 1000},
        {'name': 'R2', 'node1': 2, 'node2': 0, 'value': 2000},
        {'name': 'R3', 'node1': 2, 'node2': 3, 'value': 3000},
        {'name': 'V1', 'node1': 0, 'node2': 1, 'value': 12},
    ]

    analyses = [
        {'type': 'dc', 'params': {'source': 'V1', 'start': 0, 'stop': 12, 'step': 0.1}}
    ]

    generated_netlist = create_netlist_text("Generated Circuit", components, analyses)

    print("生成的网表:")
    print(generated_netlist)

    # 解析生成的网表
    result_gen = parser.parse(generated_netlist)
    print(f"\n解析结果: {len(result_gen.components)} 个元件")


if __name__ == "__main__":
    main()
