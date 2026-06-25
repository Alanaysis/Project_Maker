"""
网表解析测试
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.netlist import NetlistParser, NetlistData, AnalysisType, create_netlist_text


class TestNetlistParser:
    """网表解析器测试"""

    def setup_method(self):
        self.parser = NetlistParser()

    def test_simple_resistor_circuit(self):
        """测试简单电阻电路解析"""
        netlist = """
Simple Resistor Circuit
R1 1 2 1000
R2 2 0 2000
V1 0 1 DC 10
.dc V1 0 10 1
.end
"""
        result = self.parser.parse(netlist)

        assert result.title == "Simple Resistor Circuit"
        assert len(result.components) == 3
        assert len(result.analyses) == 1

        # 检查元件
        r1 = result.components[0]
        assert r1['name'] == 'R1'
        assert r1['node1'] == 1
        assert r1['node2'] == 2
        assert r1['value'] == 1000

        v1 = result.components[2]
        assert v1['name'] == 'V1'
        assert v1['value'] == 10

    def test_rc_circuit(self):
        """测试 RC 电路解析"""
        netlist = """
RC Low Pass Filter
R1 1 2 1000
C1 2 0 1e-6
V1 0 1 AC 1
.ac dec 100 1 1e6
.end
"""
        result = self.parser.parse(netlist)

        assert len(result.components) == 3
        assert len(result.analyses) == 1

        c1 = result.components[1]
        assert c1['name'] == 'C1'
        assert c1['value'] == 1e-6

        ac_cmd = result.analyses[0]
        assert ac_cmd.type == AnalysisType.AC
        assert ac_cmd.params['sweep_type'] == 'dec'
        assert ac_cmd.params['npoints'] == 100

    def test_rlc_circuit(self):
        """测试 RLC 电路解析"""
        netlist = """
RLC Series Circuit
R1 1 2 100
L1 2 3 1e-3
C1 3 0 1e-6
V1 0 1 SIN(0 5 1000)
.tran 1e-6 5e-3
.end
"""
        result = self.parser.parse(netlist)

        assert len(result.components) == 4
        assert len(result.analyses) == 1

        l1 = result.components[1]
        assert l1['name'] == 'L1'
        assert l1['value'] == 1e-3

        tran_cmd = result.analyses[0]
        assert tran_cmd.type == AnalysisType.TRANSIENT
        assert tran_cmd.params['tstep'] == 1e-6
        assert tran_cmd.params['tstop'] == 5e-3

    def test_value_parsing(self):
        """测试数值解析"""
        parser = NetlistParser()

        assert parser._parse_value("1000") == 1000
        assert parser._parse_value("1K") == 1000
        assert parser._parse_value("1k") == 1000
        assert parser._parse_value("1MEG") == 1e6
        assert parser._parse_value("1M") == 1e-3
        assert parser._parse_value("1U") == 1e-6
        assert parser._parse_value("1N") == 1e-9
        assert parser._parse_value("1P") == 1e-12

    def test_node_parsing(self):
        """测试节点解析"""
        parser = NetlistParser()

        assert parser._parse_node("0") == 0
        assert parser._parse_node("GND") == 0
        assert parser._parse_node("gnd") == 0
        assert parser._parse_node("1") == 1
        assert parser._parse_node("10") == 10

    def test_comments(self):
        """测试注释处理"""
        netlist = """
* This is a comment
Test Circuit
# Another comment
R1 1 2 1000
R2 2 0 2000
"""
        result = self.parser.parse(netlist)

        assert result.title == "Test Circuit"
        assert len(result.components) == 2

    def test_dc_sweep(self):
        """测试 DC 扫描命令"""
        netlist = """
DC Sweep Test
R1 1 2 1000
R2 2 0 2000
V1 0 1 DC 10
.dc V1 0 10 0.1
.end
"""
        result = self.parser.parse(netlist)

        assert len(result.analyses) == 1
        dc_cmd = result.analyses[0]
        assert dc_cmd.type == AnalysisType.DC
        assert dc_cmd.params['source'] == 'V1'
        assert dc_cmd.params['start'] == 0
        assert dc_cmd.params['stop'] == 10
        assert dc_cmd.params['step'] == 0.1

    def test_ac_decades(self):
        """测试 AC 十倍频扫描"""
        netlist = """
AC Decade Test
R1 1 2 1000
C1 2 0 1e-6
V1 0 1 AC 1
.ac dec 100 1 1e6
.end
"""
        result = self.parser.parse(netlist)

        ac_cmd = result.analyses[0]
        assert ac_cmd.params['sweep_type'] == 'dec'
        assert ac_cmd.params['npoints'] == 100
        assert ac_cmd.params['fstart'] == 1
        assert ac_cmd.params['fstop'] == 1e6

    def test_multiple_analyses(self):
        """测试多重分析命令"""
        netlist = """
Multiple Analyses
R1 1 2 1000
C1 2 0 1e-6
V1 0 1 DC 10
.dc V1 0 10 1
.ac dec 10 1 1e6
.tran 1e-6 1e-3
.end
"""
        result = self.parser.parse(netlist)

        assert len(result.analyses) == 3

    def test_create_netlist_text(self):
        """测试创建网表文本"""
        components = [
            {'name': 'R1', 'node1': 1, 'node2': 2, 'value': 1000},
            {'name': 'C1', 'node1': 2, 'node2': 0, 'value': 1e-6},
            {'name': 'V1', 'node1': 0, 'node2': 1, 'value': 10},
        ]

        analyses = [
            {'type': 'dc', 'params': {'source': 'V1', 'start': 0, 'stop': 10, 'step': 1}}
        ]

        netlist = create_netlist_text("Test Circuit", components, analyses)

        assert "Test Circuit" in netlist
        assert "R1 1 2 1000" in netlist
        assert "C1 2 0 1e-6" in netlist
        assert ".dc V1 0 10 1" in netlist
        assert ".end" in netlist


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
