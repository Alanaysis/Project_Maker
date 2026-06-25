"""
网表解析模块 - Netlist Parser

解析 SPICE 格式的网表文件，支持：
- 元件定义 (R, C, L, V, I)
- 节点定义
- 分析命令 (.dc, .ac, .tran)
- 注释和选项
"""

import re
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass, field
from enum import Enum

from .components import Resistor, Capacitor, Inductor, VoltageSource, CurrentSource


class AnalysisType(Enum):
    """分析类型"""
    DC = "dc"
    AC = "ac"
    TRANSIENT = "tran"


@dataclass
class AnalysisCommand:
    """分析命令"""
    type: AnalysisType
    params: Dict[str, any] = field(default_factory=dict)


@dataclass
class NetlistData:
    """解析后的网表数据"""
    title: str = ""
    components: List[Dict] = field(default_factory=list)
    analyses: List[AnalysisCommand] = field(default_factory=list)
    nodes: set = field(default_factory=set)
    ground_node: int = 0


class NetlistParser:
    """
    SPICE 网表解析器

    支持的元件格式：
    - Rname node1 node2 value
    - Cname node1 node2 value
    - Lname node1 node2 value
    - Vname node1 node2 DC value
    - Vname node1 node2 AC mag phase
    - Vname node1 node2 SIN(vo va freq)
    - Iname node1 node2 value

    支持的分析命令：
    - .dc V1 start stop step
    - .ac dec/lin/oct npoints fstart fstop
    - .tran tstep tstop [tstart]
    """

    def __init__(self):
        self.nodes = set()
        self.components = []
        self.analyses = []
        self.title = ""

    def parse(self, netlist_text: str) -> NetlistData:
        """
        解析网表文本

        Args:
            netlist_text: SPICE 格式的网表文本

        Returns:
            NetlistData: 解析后的网表数据
        """
        lines = netlist_text.strip().split('\n')
        self.nodes = set()
        self.components = []
        self.analyses = []
        self.title = ""

        for i, line in enumerate(lines):
            line = line.strip()

            # 跳过空行和注释
            if not line or line.startswith('*') or line.startswith('#'):
                continue

            # 标题行 (第一行非注释)
            if i == 0 and not line.startswith('.'):
                self.title = line
                continue

            # 分析命令
            if line.startswith('.'):
                self._parse_command(line)
                continue

            # 元件定义
            self._parse_component(line)

        return NetlistData(
            title=self.title,
            components=self.components,
            analyses=self.analyses,
            nodes=self.nodes,
            ground_node=0
        )

    def _parse_component(self, line: str):
        """解析元件定义"""
        parts = line.split()
        if len(parts) < 4:
            raise ValueError(f"元件定义格式错误: {line}")

        name = parts[0].upper()
        prefix = name[0]

        try:
            node1 = self._parse_node(parts[1])
            node2 = self._parse_node(parts[2])
        except ValueError as e:
            raise ValueError(f"节点解析错误: {e}")

        self.nodes.add(node1)
        self.nodes.add(node2)

        component = {
            'name': name,
            'type': prefix,
            'node1': node1,
            'node2': node2,
            'line': line
        }

        if prefix == 'R':
            component['value'] = self._parse_value(parts[3])
        elif prefix == 'C':
            component['value'] = self._parse_value(parts[3])
        elif prefix == 'L':
            component['value'] = self._parse_value(parts[3])
        elif prefix == 'V':
            self._parse_voltage_source(parts, component)
        elif prefix == 'I':
            self._parse_current_source(parts, component)
        else:
            raise ValueError(f"未知元件类型: {prefix}")

        self.components.append(component)

    def _parse_node(self, node_str: str) -> int:
        """解析节点号"""
        node_str = node_str.lower().strip()
        if node_str in ('0', 'gnd', 'ground'):
            return 0
        try:
            return int(node_str)
        except ValueError:
            # 尝试解析为节点名
            return hash(node_str) % 10000

    def _parse_value(self, value_str: str) -> float:
        """
        解析数值，支持工程单位

        支持单位:
        - T = 1e12, G = 1e9, MEG = 1e6
        - K = 1e3, M = 1e-3, U = 1e-6
        - N = 1e-9, P = 1e-12, F = 1e-15
        """
        value_str = value_str.strip().upper()

        # 单位映射
        units = {
            'T': 1e12, 'G': 1e9, 'MEG': 1e6,
            'K': 1e3, 'M': 1e-3, 'U': 1e-6,
            'N': 1e-9, 'P': 1e-12, 'F': 1e-15
        }

        for unit, multiplier in sorted(units.items(), key=lambda x: -len(x[0])):
            if value_str.endswith(unit):
                num_str = value_str[:-len(unit)]
                if num_str:
                    return float(num_str) * multiplier

        return float(value_str)

    def _parse_voltage_source(self, parts: List[str], component: Dict):
        """解析电压源定义"""
        if len(parts) >= 5:
            mode = parts[3].upper()

            if mode == 'DC':
                component['value'] = self._parse_value(parts[4])
                component['type'] = 'V'
                component['dc'] = True
            elif mode == 'AC':
                component['ac_mag'] = self._parse_value(parts[4])
                component['ac_phase'] = self._parse_value(parts[5]) if len(parts) > 5 else 0
                component['type'] = 'V'
                component['ac'] = True
            else:
                # 尝试解析为数值
                try:
                    component['value'] = self._parse_value(parts[3])
                except ValueError:
                    component['value'] = 0
        elif len(parts) >= 4:
            # 简单格式: Vname n1 n2 value
            try:
                component['value'] = self._parse_value(parts[3])
            except ValueError:
                component['value'] = 0
        else:
            component['value'] = 0

        # 检查 SIN 源
        full_line = ' '.join(parts)
        sin_match = re.search(r'SIN\s*\(\s*([^)]+)\s*\)', full_line, re.IGNORECASE)
        if sin_match:
            sin_params = sin_match.group(1).split()
            if len(sin_params) >= 3:
                component['sin'] = {
                    'offset': float(sin_params[0]),
                    'amplitude': float(sin_params[1]),
                    'frequency': float(sin_params[2])
                }

    def _parse_current_source(self, parts: List[str], component: Dict):
        """解析电流源定义"""
        if len(parts) >= 5:
            mode = parts[3].upper()
            if mode == 'DC':
                component['value'] = self._parse_value(parts[4])
            else:
                component['value'] = self._parse_value(parts[3])
        elif len(parts) >= 4:
            component['value'] = self._parse_value(parts[3])
        else:
            component['value'] = 0

    def _parse_command(self, line: str):
        """解析分析命令"""
        parts = line.split()
        cmd = parts[0].lower()

        if cmd == '.dc':
            self._parse_dc_command(parts)
        elif cmd == '.ac':
            self._parse_ac_command(parts)
        elif cmd == '.tran':
            self._parse_tran_command(parts)
        elif cmd == '.end':
            pass
        elif cmd == '.options':
            pass
        elif cmd == '.model':
            pass

    def _parse_dc_command(self, parts: List[str]):
        """
        解析 DC 分析命令
        .dc v1 start stop step
        """
        if len(parts) >= 5:
            self.analyses.append(AnalysisCommand(
                type=AnalysisType.DC,
                params={
                    'source': parts[1].upper(),
                    'start': self._parse_value(parts[2]),
                    'stop': self._parse_value(parts[3]),
                    'step': self._parse_value(parts[4])
                }
            ))

    def _parse_ac_command(self, parts: List[str]):
        """
        解析 AC 分析命令
        .ac dec/lin/oct npoints fstart fstop
        """
        if len(parts) >= 5:
            sweep_type = parts[1].lower()
            npoints = int(parts[2])
            fstart = self._parse_value(parts[3])
            fstop = self._parse_value(parts[4])

            self.analyses.append(AnalysisCommand(
                type=AnalysisType.AC,
                params={
                    'sweep_type': sweep_type,
                    'npoints': npoints,
                    'fstart': fstart,
                    'fstop': fstop
                }
            ))

    def _parse_tran_command(self, parts: List[str]):
        """
        解析瞬态分析命令
        .tran tstep tstop [tstart]
        """
        if len(parts) >= 3:
            tstep = self._parse_value(parts[1])
            tstop = self._parse_value(parts[2])
            tstart = self._parse_value(parts[3]) if len(parts) > 3 else 0

            self.analyses.append(AnalysisCommand(
                type=AnalysisType.TRANSIENT,
                params={
                    'tstep': tstep,
                    'tstop': tstop,
                    'tstart': tstart
                }
            ))

    def parse_file(self, filepath: str) -> NetlistData:
        """
        从文件解析网表

        Args:
            filepath: 网表文件路径

        Returns:
            NetlistData: 解析后的网表数据
        """
        with open(filepath, 'r') as f:
            content = f.read()
        return self.parse(content)


def create_netlist_text(title: str, components: List[Dict],
                       analyses: Optional[List[Dict]] = None) -> str:
    """
    创建网表文本

    Args:
        title: 电路标题
        components: 元件列表
        analyses: 分析命令列表

    Returns:
        str: SPICE 格式的网表文本
    """
    lines = [title]

    for comp in components:
        name = comp['name']
        node1 = comp['node1']
        node2 = comp['node2']
        value = comp.get('value', 0)

        if name.startswith('V'):
            if 'sin' in comp:
                sin = comp['sin']
                lines.append(f"{name} {node1} {node2} SIN({sin['offset']} {sin['amplitude']} {sin['frequency']})")
            else:
                lines.append(f"{name} {node1} {node2} DC {value}")
        elif name.startswith('I'):
            lines.append(f"{name} {node1} {node2} DC {value}")
        else:
            lines.append(f"{name} {node1} {node2} {value}")

    if analyses:
        for analysis in analyses:
            atype = analysis['type']
            params = analysis['params']

            if atype == 'dc':
                lines.append(f".dc {params['source']} {params['start']} {params['stop']} {params['step']}")
            elif atype == 'ac':
                lines.append(f".ac {params['sweep_type']} {params['npoints']} {params['fstart']} {params['fstop']}")
            elif atype == 'tran':
                lines.append(f".tran {params['tstep']} {params['tstop']}")

    lines.append(".end")
    return '\n'.join(lines)
