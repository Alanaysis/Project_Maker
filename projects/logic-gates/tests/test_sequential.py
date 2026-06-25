"""
时序电路测试模块

测试时序逻辑电路的功能。
"""

import pytest
from src.sequential.latch import SRLatch, DLatch
from src.sequential.flipflop import DFlipFlop, JKFlipFlop, TFlipFlop
from src.sequential.counter import Counter, DecadeCounter, RingCounter
from src.sequential.register import Register, ShiftRegister, UniversalShiftRegister


class TestSRLatch:
    """SR锁存器测试"""

    def test_set(self):
        """测试置位"""
        latch = SRLatch()
        result = latch.evaluate(1, 0)
        assert result['Q'] == 1
        assert result['Q_bar'] == 0

    def test_reset(self):
        """测试复位"""
        latch = SRLatch()
        latch.set()
        result = latch.evaluate(0, 1)
        assert result['Q'] == 0
        assert result['Q_bar'] == 1

    def test_hold(self):
        """测试保持"""
        latch = SRLatch()
        latch.set()
        result = latch.evaluate(0, 0)
        assert result['Q'] == 1
        assert result['Q_bar'] == 0

    def test_forbidden_state(self):
        """测试禁止状态"""
        latch = SRLatch()
        with pytest.raises(ValueError):
            latch.evaluate(1, 1)


class TestDLatch:
    """D锁存器测试"""

    def test_transparent(self):
        """测试透明模式"""
        latch = DLatch()
        result = latch.evaluate(1, 1)
        assert result['Q'] == 1
        assert result['Q_bar'] == 0

    def test_hold(self):
        """测试保持模式"""
        latch = DLatch()
        latch.evaluate(1, 1)  # 设置为1
        result = latch.evaluate(0, 0)  # CLK=0，保持
        assert result['Q'] == 1
        assert result['Q_bar'] == 0

    def test_data_change(self):
        """测试数据变化"""
        latch = DLatch()
        
        # CLK=1，跟随D
        latch.evaluate(0, 1)
        assert latch.get_state()['Q'] == 0
        
        latch.evaluate(1, 1)
        assert latch.get_state()['Q'] == 1


class TestDFlipFlop:
    """D触发器测试"""

    def test_rising_edge(self):
        """测试上升沿触发"""
        ff = DFlipFlop()
        
        # 设置数据
        ff.set_data(1)
        
        # 上升沿
        result = ff.clock(0)
        assert result['Q'] == 0  # 还没触发
        
        result = ff.clock(1)
        assert result['Q'] == 1  # 触发

    def test_hold_on_falling_edge(self):
        """测试下降沿保持"""
        ff = DFlipFlop()
        
        ff.set_data(1)
        ff.clock(1)  # 上升沿触发
        
        ff.set_data(0)
        result = ff.clock(0)  # 下降沿，保持
        assert result['Q'] == 1  # 保持

    def test_evaluate(self):
        """测试evaluate方法"""
        ff = DFlipFlop()
        
        result = ff.evaluate(1, 1)  # D=1, CLK上升沿
        assert result['Q'] == 1
        
        result = ff.evaluate(0, 0)  # D=0, CLK低电平
        assert result['Q'] == 1  # 保持


class TestJKFlipFlop:
    """JK触发器测试"""

    def test_set(self):
        """测试置位"""
        ff = JKFlipFlop()
        # 上升沿触发
        ff.evaluate(1, 0, 0)  # 准备
        result = ff.evaluate(1, 0, 1)  # J=1, K=0, CLK上升沿
        assert result['Q'] == 1

    def test_reset(self):
        """测试复位"""
        ff = JKFlipFlop()
        # 先置位
        ff.evaluate(1, 0, 0)  # 准备
        ff.evaluate(1, 0, 1)  # 置位

        # 再复位
        ff.evaluate(0, 1, 0)  # 准备
        result = ff.evaluate(0, 1, 1)  # J=0, K=1, CLK上升沿
        assert result['Q'] == 0

    def test_toggle(self):
        """测试翻转"""
        ff = JKFlipFlop()

        # 第一次翻转
        ff.evaluate(1, 1, 0)  # 准备
        ff.evaluate(1, 1, 1)  # 翻转
        assert ff.get_state()['Q'] == 1

        # 第二次翻转
        ff.evaluate(1, 1, 0)  # 准备
        ff.evaluate(1, 1, 1)  # 翻转
        assert ff.get_state()['Q'] == 0

    def test_hold(self):
        """测试保持"""
        ff = JKFlipFlop()
        # 置位
        ff.evaluate(1, 0, 0)  # 准备
        ff.evaluate(1, 0, 1)  # 置位

        # 保持
        ff.evaluate(0, 0, 0)  # 准备
        result = ff.evaluate(0, 0, 1)  # J=0, K=0, 保持
        assert result['Q'] == 1


class TestTFlipFlop:
    """T触发器测试"""

    def test_toggle(self):
        """测试翻转"""
        ff = TFlipFlop()
        
        result = ff.evaluate(1, 1)  # T=1, CLK上升沿
        assert result['Q'] == 1
        
        result = ff.evaluate(1, 0)  # T=1, CLK下降沿
        assert result['Q'] == 1  # 保持
        
        result = ff.evaluate(1, 1)  # T=1, CLK上升沿
        assert result['Q'] == 0  # 翻转

    def test_hold(self):
        """测试保持"""
        ff = TFlipFlop()
        
        result = ff.evaluate(0, 1)  # T=0, CLK上升沿
        assert result['Q'] == 0  # 保持


class TestCounter:
    """计数器测试"""

    def test_increment(self):
        """测试递增"""
        counter = Counter(4)
        
        assert counter.get_count() == 0
        
        counter.increment()
        assert counter.get_count() == 1
        
        counter.increment()
        assert counter.get_count() == 2

    def test_overflow(self):
        """测试溢出"""
        counter = Counter(4)
        
        for _ in range(15):
            counter.increment()
        assert counter.get_count() == 15
        
        counter.increment()
        assert counter.get_count() == 0  # 溢出

    def test_decrement(self):
        """测试递减"""
        counter = Counter(4)
        counter.set_count(5)
        
        counter.decrement()
        assert counter.get_count() == 4

    def test_reset(self):
        """测试重置"""
        counter = Counter(4)
        counter.set_count(10)
        
        counter.reset()
        assert counter.get_count() == 0

    def test_set_count(self):
        """测试设置计数值"""
        counter = Counter(4)
        counter.set_count(7)
        assert counter.get_count() == 7


class TestDecadeCounter:
    """十进制计数器测试"""

    def test_counting(self):
        """测试计数"""
        counter = DecadeCounter()
        
        for i in range(10):
            assert counter.get_count() == i
            counter.increment()
        
        assert counter.get_count() == 0  # 回到0


class TestRingCounter:
    """环形计数器测试"""

    def test_cycling(self):
        """测试循环"""
        counter = RingCounter(4)
        
        assert counter.get_pattern() == [1, 0, 0, 0]
        
        counter.clock()
        assert counter.get_pattern() == [0, 1, 0, 0]
        
        counter.clock()
        assert counter.get_pattern() == [0, 0, 1, 0]
        
        counter.clock()
        assert counter.get_pattern() == [0, 0, 0, 1]
        
        counter.clock()
        assert counter.get_pattern() == [1, 0, 0, 0]  # 回到初始状态


class TestRegister:
    """寄存器测试"""

    def test_load_read(self):
        """测试加载和读取"""
        reg = Register(4)
        
        reg.load([1, 0, 1, 0])
        assert reg.read() == [1, 0, 1, 0]

    def test_clear(self):
        """测试清零"""
        reg = Register(4)
        reg.load([1, 0, 1, 0])
        
        reg.clear()
        assert reg.read() == [0, 0, 0, 0]

    def test_get_set_value(self):
        """测试整数值操作"""
        reg = Register(4)
        
        reg.set_value(10)  # 1010
        assert reg.get_value() == 10

    def test_invalid_input(self):
        """测试无效输入"""
        reg = Register(4)
        
        with pytest.raises(ValueError):
            reg.load([1, 0])  # 位数不匹配


class TestShiftRegister:
    """移位寄存器测试"""

    def test_shift_right(self):
        """测试右移"""
        sr = ShiftRegister(4)
        
        sr.load([1, 0, 1, 0])
        result = sr.shift_right(1)
        assert result == [1, 1, 0, 1]

    def test_shift_left(self):
        """测试左移"""
        sr = ShiftRegister(4)
        
        sr.load([1, 0, 1, 0])
        result = sr.shift_left(1)
        assert result == [0, 1, 0, 1]

    def test_serial_in_out(self):
        """测试串行输入输出"""
        sr = ShiftRegister(4)
        
        sr.serial_in(1)
        sr.serial_in(0)
        sr.serial_in(1)
        sr.serial_in(1)
        
        assert sr.read() == [1, 1, 0, 1]
        assert sr.serial_out() == 1  # 最低位

    def test_parallel_load(self):
        """测试并行加载"""
        sr = ShiftRegister(4)
        
        sr.parallel_load([1, 0, 1, 0])
        assert sr.read() == [1, 0, 1, 0]


class TestUniversalShiftRegister:
    """通用移位寄存器测试"""

    def test_hold_mode(self):
        """测试保持模式"""
        usr = UniversalShiftRegister(4)
        # 先并行加载数据
        usr.set_mode(UniversalShiftRegister.MODE_PARALLEL_LOAD)
        usr.clock([1, 0, 1, 0])

        # 切换到保持模式
        usr.set_mode(UniversalShiftRegister.MODE_HOLD)
        result = usr.clock()
        assert result == [1, 0, 1, 0]

    def test_shift_right_mode(self):
        """测试右移模式"""
        usr = UniversalShiftRegister(4)
        # 先并行加载数据
        usr.set_mode(UniversalShiftRegister.MODE_PARALLEL_LOAD)
        usr.clock([1, 0, 1, 0])

        # 切换到右移模式
        usr.set_mode(UniversalShiftRegister.MODE_SHIFT_RIGHT)
        usr.set_serial_inputs(right=1)
        result = usr.clock()
        assert result == [1, 1, 0, 1]

    def test_shift_left_mode(self):
        """测试左移模式"""
        usr = UniversalShiftRegister(4)
        # 先并行加载数据
        usr.set_mode(UniversalShiftRegister.MODE_PARALLEL_LOAD)
        usr.clock([1, 0, 1, 0])

        # 切换到左移模式
        usr.set_mode(UniversalShiftRegister.MODE_SHIFT_LEFT)
        usr.set_serial_inputs(left=1)
        result = usr.clock()
        assert result == [0, 1, 0, 1]

    def test_parallel_load_mode(self):
        """测试并行加载模式"""
        usr = UniversalShiftRegister(4)

        usr.set_mode(UniversalShiftRegister.MODE_PARALLEL_LOAD)
        result = usr.clock([1, 1, 0, 0])
        assert result == [1, 1, 0, 0]
