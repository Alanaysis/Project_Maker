"""
仿真引擎测试模块

测试仿真引擎的功能。
"""

import pytest
from src.simulation.wire import Wire, Bus
from src.simulation.sim_circuit import Circuit as SimCircuit
from src.simulation.simulator import Simulator, ClockGenerator, StimulusGenerator
from src.simulation.trace import SignalTrace
from src.gates import AndGate, OrGate, NotGate


class TestWire:
    """连线测试"""

    def test_set_get_value(self):
        """测试设置和获取值"""
        wire = Wire("test")
        
        wire.set_value(1)
        assert wire.get_value() == 1
        
        wire.set_value(0)
        assert wire.get_value() == 0

    def test_delay(self):
        """测试延迟"""
        wire = Wire("test", delay=2)
        
        wire.set_value(1, time=0)
        assert wire.get_delayed_value(0) == 0  # 延迟2个时间单位
        assert wire.get_delayed_value(1) == 0
        assert wire.get_delayed_value(2) == 1

    def test_has_changed(self):
        """测试变化检测"""
        wire = Wire("test")
        
        wire.set_value(0)
        assert wire.has_changed() == False
        
        wire.set_value(1)
        assert wire.has_changed() == True

    def test_history(self):
        """测试历史记录"""
        wire = Wire("test")
        
        wire.set_value(0, time=0)
        wire.set_value(1, time=1)
        wire.set_value(0, time=2)
        
        history = wire.get_history()
        assert len(history) == 3
        assert history[0] == (0, 0)
        assert history[1] == (1, 1)
        assert history[2] == (2, 0)

    def test_reset(self):
        """测试重置"""
        wire = Wire("test")
        
        wire.set_value(1)
        wire.reset()
        
        assert wire.get_value() == 0
        assert len(wire.get_history()) == 0

    def test_invalid_value(self):
        """测试无效值"""
        wire = Wire("test")
        
        with pytest.raises(ValueError):
            wire.set_value(2)


class TestBus:
    """总线测试"""

    def test_set_get_value(self):
        """测试设置和获取值"""
        bus = Bus("data", width=4)
        
        bus.set_value([1, 0, 1, 0])
        assert bus.get_value() == [1, 0, 1, 0]

    def test_decimal_value(self):
        """测试十进制值"""
        bus = Bus("data", width=4)
        
        bus.set_decimal_value(10)  # 1010
        assert bus.get_decimal_value() == 10
        assert bus.get_value() == [1, 0, 1, 0]

    def test_invalid_input(self):
        """测试无效输入"""
        bus = Bus("data", width=4)
        
        with pytest.raises(ValueError):
            bus.set_value([1, 0])  # 位数不匹配


class TestSimCircuit:
    """仿真电路测试"""

    def test_add_wire(self):
        """测试添加连线"""
        circuit = SimCircuit("test")
        
        wire = circuit.add_wire("A")
        assert wire.name == "A"

    def test_add_component(self):
        """测试添加组件"""
        circuit = SimCircuit("test")
        
        and_gate = AndGate()
        comp = circuit.add_component(and_gate, "AND1")
        assert comp.name == "AND1"

    def test_connect(self):
        """测试连接"""
        circuit = SimCircuit("test")
        
        circuit.add_wire("A")
        circuit.add_wire("B")
        circuit.add_wire("OUT")
        circuit.add_component(AndGate(), "AND1")
        
        circuit.connect("A", "AND1", 0)
        circuit.connect("B", "AND1", 1)
        circuit.connect_output("AND1", "OUT")

    def test_simulate(self):
        """测试仿真"""
        circuit = SimCircuit("test")
        
        circuit.add_wire("A")
        circuit.add_wire("B")
        circuit.add_wire("OUT")
        circuit.add_component(AndGate(), "AND1", delay=1)
        
        circuit.connect("A", "AND1", 0)
        circuit.connect("B", "AND1", 1)
        circuit.connect_output("AND1", "OUT")
        
        # 设置输入
        circuit.set_wire("A", 1, time=0)
        circuit.set_wire("B", 1, time=0)
        
        # 运行仿真
        history = circuit.simulate(5)
        
        # 检查结果
        assert "A" in history
        assert "B" in history
        assert "OUT" in history


class TestSimulator:
    """仿真器测试"""

    def test_add_wire(self):
        """测试添加连线"""
        sim = Simulator()
        
        wire = sim.add_wire("A")
        assert wire.name == "A"

    def test_schedule_event(self):
        """测试调度事件"""
        sim = Simulator()
        sim.add_wire("A")
        
        sim.schedule_event(0, "A", 1)
        sim.schedule_event(5, "A", 0)

    def test_run(self):
        """测试运行"""
        sim = Simulator()
        sim.add_wire("A")
        
        sim.schedule_event(0, "A", 1)
        sim.schedule_event(5, "A", 0)
        
        sim.run(10)
        
        assert sim.get_wire_value("A") == 0

    def test_get_waveform(self):
        """测试获取波形"""
        sim = Simulator()
        sim.add_wire("A")
        
        sim.schedule_event(0, "A", 1)
        sim.schedule_event(5, "A", 0)
        
        sim.run(10)
        
        waveform = sim.get_waveform("A")
        assert len(waveform) == 10
        assert waveform[0] == 1
        assert waveform[5] == 0

    def test_clock_generator(self):
        """测试时钟生成器"""
        sim = Simulator()
        sim.add_wire("CLK")
        
        clock_gen = ClockGenerator(sim, "CLK", period=4)
        clock_gen.start(20)
        
        sim.run(20)
        
        waveform = sim.get_waveform("CLK")
        # 时钟应该在高电平和低电平之间交替
        assert waveform[0] == 1
        assert waveform[2] == 0


class TestStimulusGenerator:
    """激励生成器测试"""

    def test_add_signal(self):
        """测试添加信号"""
        sim = Simulator()
        sim.add_wire("A")
        
        stim = StimulusGenerator(sim)
        stim.add_signal("A", [(0, 1), (5, 0)])
        stim.apply()

    def test_add_pulse(self):
        """测试添加脉冲"""
        sim = Simulator()
        sim.add_wire("A")
        
        stim = StimulusGenerator(sim)
        stim.add_pulse("A", start_time=2, duration=3, value=1)
        stim.apply()


class TestSignalTrace:
    """信号追踪测试"""

    def test_add_signal(self):
        """测试添加信号"""
        trace = SignalTrace()
        
        trace.add_signal("CLK", [0, 1, 0, 1])
        trace.add_signal("DATA", [0, 0, 1, 1])

    def test_to_waveform(self):
        """测试生成波形"""
        trace = SignalTrace()
        
        trace.add_signal("CLK", [0, 1, 0, 1])
        trace.add_signal("DATA", [0, 0, 1, 1])
        
        waveform = trace.to_waveform()
        assert "CLK" in waveform
        assert "DATA" in waveform

    def test_get_transitions(self):
        """测试获取转换"""
        trace = SignalTrace()

        trace.add_signal("CLK", [0, 1, 0, 1])

        transitions = trace.get_transitions("CLK")
        assert len(transitions) == 3
        assert transitions[0] == (1, 0, 1)
        assert transitions[1] == (2, 1, 0)
        assert transitions[2] == (3, 0, 1)

    def test_export_csv(self):
        """测试导出CSV"""
        trace = SignalTrace()
        
        trace.add_signal("CLK", [0, 1, 0, 1])
        trace.add_signal("DATA", [0, 0, 1, 1])
        
        csv = trace.export_csv()
        assert "Time,CLK,DATA" in csv
        assert "0,0,0" in csv
        assert "1,1,0" in csv

    def test_export_vcd(self):
        """测试导出VCD"""
        trace = SignalTrace()
        
        trace.add_signal("CLK", [0, 1, 0, 1])
        trace.add_signal("DATA", [0, 0, 1, 1])
        
        vcd = trace.export_vcd()
        assert "$date" in vcd
        assert "$timescale" in vcd
        assert "CLK" in vcd
        assert "DATA" in vcd
