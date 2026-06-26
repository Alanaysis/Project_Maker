#!/usr/bin/env python3
"""
组合逻辑电路 - 单元测试
Combinational Logic Circuit - Unit Tests
"""

import unittest
from src.gates import AND, OR, NOT, XOR, NAND, NOR, XNOR
from src.adders import HalfAdder, FullAdder, RippleCarryAdder, Subtracter
from src.multiplier import DirectMultiplier, WallaceTreeMultiplier
from src.mux_demux import Multiplexer2to1, Multiplexer4to1, Multiplexer8to1
from src.mux_demux import Demultiplexer1to2, Demultiplexer1to8
from src.encoder_decoder import BinaryEncoder, BCDToBinaryEncoder
from src.encoder_decoder import BinaryDecoder, BCDDecoder, SevenSegmentDecoder
from src.comparator import Comparator1Bit, Comparator4Bit, ComparatorNBit
from src.tri_state import TriStateBuffer, BusDriver
from src.logic_synthesis import MuxLogicSynthesizer


class TestGates(unittest.TestCase):
    """测试基本逻辑门"""

    def test_and_gate(self):
        gate = AND()
        self.assertEqual(gate.evaluate(0, 0), 0)
        self.assertEqual(gate.evaluate(0, 1), 0)
        self.assertEqual(gate.evaluate(1, 0), 0)
        self.assertEqual(gate.evaluate(1, 1), 1)

    def test_or_gate(self):
        gate = OR()
        self.assertEqual(gate.evaluate(0, 0), 0)
        self.assertEqual(gate.evaluate(0, 1), 1)
        self.assertEqual(gate.evaluate(1, 0), 1)
        self.assertEqual(gate.evaluate(1, 1), 1)

    def test_not_gate(self):
        gate = NOT()
        self.assertEqual(gate.evaluate(0), 1)
        self.assertEqual(gate.evaluate(1), 0)

    def test_xor_gate(self):
        gate = XOR()
        self.assertEqual(gate.evaluate(0, 0), 0)
        self.assertEqual(gate.evaluate(0, 1), 1)
        self.assertEqual(gate.evaluate(1, 0), 1)
        self.assertEqual(gate.evaluate(1, 1), 0)

    def test_nand_gate(self):
        gate = NAND()
        self.assertEqual(gate.evaluate(0, 0), 1)
        self.assertEqual(gate.evaluate(0, 1), 1)
        self.assertEqual(gate.evaluate(1, 0), 1)
        self.assertEqual(gate.evaluate(1, 1), 0)

    def test_nor_gate(self):
        gate = NOR()
        self.assertEqual(gate.evaluate(0, 0), 1)
        self.assertEqual(gate.evaluate(0, 1), 0)
        self.assertEqual(gate.evaluate(1, 0), 0)
        self.assertEqual(gate.evaluate(1, 1), 0)

    def test_xnor_gate(self):
        gate = XNOR()
        self.assertEqual(gate.evaluate(0, 0), 1)
        self.assertEqual(gate.evaluate(0, 1), 0)
        self.assertEqual(gate.evaluate(1, 0), 0)
        self.assertEqual(gate.evaluate(1, 1), 1)


class TestHalfAdder(unittest.TestCase):
    """测试半加器"""

    def test_all_combinations(self):
        ha = HalfAdder()
        # (A, B) -> (Sum, Carry)
        self.assertEqual(ha.add(0, 0), (0, 0))
        self.assertEqual(ha.add(0, 1), (1, 0))
        self.assertEqual(ha.add(1, 0), (1, 0))
        self.assertEqual(ha.add(1, 1), (0, 1))

    def test_invalid_input(self):
        ha = HalfAdder()
        with self.assertRaises(ValueError):
            ha.add(2, 0)


class TestFullAdder(unittest.TestCase):
    """测试全加器"""

    def test_all_combinations(self):
        fa = FullAdder()
        # (A, B, Cin) -> (Sum, Cout)
        self.assertEqual(fa.add(0, 0, 0), (0, 0))
        self.assertEqual(fa.add(1, 0, 0), (1, 0))
        self.assertEqual(fa.add(0, 1, 0), (1, 0))
        self.assertEqual(fa.add(1, 1, 0), (0, 1))
        self.assertEqual(fa.add(0, 0, 1), (1, 0))
        self.assertEqual(fa.add(1, 0, 1), (0, 1))
        self.assertEqual(fa.add(0, 1, 1), (0, 1))
        self.assertEqual(fa.add(1, 1, 1), (1, 1))

    def test_carry_chain(self):
        """测试进位链: 1 + 1 + 1 = 1 (进位1)"""
        fa = FullAdder()
        sum_out, carry_out = fa.add(1, 1, 1)
        self.assertEqual(sum_out, 1)
        self.assertEqual(carry_out, 1)


class TestRippleCarryAdder(unittest.TestCase):
    """测试行波进位加法器"""

    def test_basic_addition(self):
        adder = RippleCarryAdder(4)
        self.assertEqual(adder.add(0, 0), (0, 0))
        self.assertEqual(adder.add(1, 0), (1, 0))
        self.assertEqual(adder.add(0, 1), (1, 0))
        self.assertEqual(adder.add(1, 1), (2, 0))

    def test_4bit_addition(self):
        adder = RippleCarryAdder(4)
        # 5 + 3 = 8
        self.assertEqual(adder.add(5, 3), (8, 0))
        # 7 + 8 = 15
        self.assertEqual(adder.add(7, 8), (15, 0))
        # 15 + 1 = 0 (溢出)
        self.assertEqual(adder.add(15, 1), (0, 1))

    def test_signed_addition(self):
        adder = RippleCarryAdder(4)
        # 3 + 2 = 5
        result, _, overflow = adder.add_signed(3, 2)
        self.assertEqual(result, 5)
        self.assertEqual(overflow, False)
        # -3 + 2 = -1
        result, _, overflow = adder.add_signed(-3, 2)
        self.assertEqual(result, -1)
        self.assertEqual(overflow, False)

    def test_overflow_detection(self):
        adder = RippleCarryAdder(4)
        # 7 + 1 = overflow (positive + positive = negative in 4-bit)
        _, _, overflow = adder.add_signed(7, 1)
        self.assertEqual(overflow, True)


class TestSubtracter(unittest.TestCase):
    """测试减法器"""

    def test_basic_subtraction(self):
        sub = Subtracter(4)
        self.assertEqual(sub.subtract(5, 3), 2)
        self.assertEqual(sub.subtract(7, 0), 7)
        self.assertEqual(sub.subtract(10, 5), 5)

    def test_negative_result_unsigned(self):
        sub = Subtracter(4)
        with self.assertRaises(ValueError):
            sub.subtract(3, 5)

    def test_signed_subtraction(self):
        sub = Subtracter(4)
        self.assertEqual(sub.subtract_signed(3, 2), 1)
        self.assertEqual(sub.subtract_signed(-3, 2), -5)
        self.assertEqual(sub.subtract_signed(3, -2), 5)


class TestMultiplier(unittest.TestCase):
    """测试乘法器"""

    def test_basic_multiplication(self):
        mult = DirectMultiplier(4, 4)
        self.assertEqual(mult.multiply(0, 0), 0)
        self.assertEqual(mult.multiply(1, 1), 1)
        self.assertEqual(mult.multiply(5, 3), 15)
        self.assertEqual(mult.multiply(7, 8), 56)
        self.assertEqual(mult.multiply(15, 15), 225)

    def test_partial_products(self):
        mult = DirectMultiplier(4, 4)
        pp = mult.get_partial_products(5, 3)  # 5 * 3
        # 3 = 0011, so partial products are: 5<<0=5, 5<<1=10
        self.assertEqual(pp, [5, 10, 0, 0])

    def test_wallace_mult(self):
        wmult = WallaceTreeMultiplier(4, 4)
        self.assertEqual(wmult.multiply(5, 3), 15)
        self.assertEqual(wmult.multiply(7, 8), 56)


class TestMultiplexer(unittest.TestCase):
    """测试多路选择器"""

    def test_mux2to1(self):
        mux = Multiplexer2to1()
        self.assertEqual(mux.select(0, 1, 0), 0)
        self.assertEqual(mux.select(0, 1, 1), 1)
        self.assertEqual(mux.select(1, 0, 0), 1)
        self.assertEqual(mux.select(1, 0, 1), 0)

    def test_mux4to1(self):
        mux = Multiplexer4to1()
        # I0=1, I1=0, I2=1, I3=1
        self.assertEqual(mux.select(1, 0, 1, 1, 0, 0), 1)  # select I0
        self.assertEqual(mux.select(1, 0, 1, 1, 0, 1), 0)  # select I1
        self.assertEqual(mux.select(1, 0, 1, 1, 1, 0), 1)  # select I2
        self.assertEqual(mux.select(1, 0, 1, 1, 1, 1), 1)  # select I3

    def test_mux8to1(self):
        mux = Multiplexer8to1()
        inputs = [0, 1, 1, 0, 1, 0, 0, 1]
        # Select input 5 (binary 101)
        self.assertEqual(mux.select(inputs, 1, 0, 1), 0)
        # Select input 0 (binary 000)
        self.assertEqual(mux.select(inputs, 0, 0, 0), 0)
        # Select input 1 (binary 001)
        self.assertEqual(mux.select(inputs, 0, 0, 1), 1)


class TestDemultiplexer(unittest.TestCase):
    """测试解复用器"""

    def test_demux1to2(self):
        demux = Demultiplexer1to2()
        self.assertEqual(demux.distribute(1, 0, 0), 0)
        self.assertEqual(demux.distribute(1, 0, 1), 1)
        self.assertEqual(demux.distribute(0, 0, 1), 0)
        # 禁用时输出为0
        self.assertEqual(demux.distribute(1, 1, 0), 0)

    def test_demux1to8(self):
        demux = Demultiplexer1to8()
        # 数据=1, sel=3 -> 只有第3位为1
        outputs = demux.distribute(1, 0, 3)
        self.assertEqual(outputs, [0, 0, 0, 1, 0, 0, 0, 0])
        # 数据=0 -> 所有输出为0
        outputs = demux.distribute(0, 0, 5)
        self.assertEqual(outputs, [0, 0, 0, 0, 0, 0, 0, 0])
        # 禁用 -> 所有输出为0
        outputs = demux.distribute(1, 1, 3)
        self.assertEqual(outputs, [0, 0, 0, 0, 0, 0, 0, 0])


class TestEncoder(unittest.TestCase):
    """测试编码器"""

    def test_binary_encoder(self):
        encoder = BinaryEncoder()
        # I0有效 (inputs[7]=1)
        self.assertEqual(encoder.encode([0, 0, 0, 0, 0, 0, 0, 1]), 0)
        # I3有效 (inputs[4]=1)
        self.assertEqual(encoder.encode([0, 0, 0, 0, 1, 0, 0, 0]), 3)
        # I7有效（最高优先级）(inputs[0]=1)
        self.assertEqual(encoder.encode([1, 0, 0, 0, 0, 0, 0, 0]), 7)
        # 多个有效，最高优先级响应
        self.assertEqual(encoder.encode([1, 1, 1, 1, 1, 1, 1, 1]), 7)
        # 所有输入为0
        self.assertEqual(encoder.encode([0, 0, 0, 0, 0, 0, 0, 0]), 0)

    def test_bcd_encoder(self):
        encoder = BCDToBinaryEncoder()
        self.assertEqual(encoder.encode(0), 0)
        self.assertEqual(encoder.encode(5), 5)
        self.assertEqual(encoder.encode(9), 9)


class TestDecoder(unittest.TestCase):
    """测试译码器"""

    def test_binary_decoder(self):
        decoder = BinaryDecoder()
        # 输入000 -> 输出[1,0,0,0,0,0,0,0]
        self.assertEqual(decoder.decode([0, 0, 0]), [1, 0, 0, 0, 0, 0, 0, 0])
        # 输入101 -> 输出[0,0,0,0,0,1,0,0]
        self.assertEqual(decoder.decode([1, 0, 1]), [0, 0, 0, 0, 0, 1, 0, 0])
        # 输入111 -> 输出[0,0,0,0,0,0,0,1]
        self.assertEqual(decoder.decode([1, 1, 1]), [0, 0, 0, 0, 0, 0, 0, 1])

    def test_bcd_decoder(self):
        decoder = BCDDecoder()
        self.assertEqual(decoder.decode(0), [1, 0, 0, 0, 0, 0, 0, 0, 0, 0])
        self.assertEqual(decoder.decode(5), [0, 0, 0, 0, 0, 1, 0, 0, 0, 0])
        self.assertEqual(decoder.decode(9), [0, 0, 0, 0, 0, 0, 0, 0, 0, 1])

    def test_seven_segment_decoder(self):
        decoder = SevenSegmentDecoder()
        # 0: a,b,c,d,e,f on (dp=0)
        self.assertEqual(decoder.decode(0), [1, 1, 1, 1, 1, 1, 0, 0])
        # 1: b,c on (dp=0)
        self.assertEqual(decoder.decode(1), [0, 1, 1, 0, 0, 0, 0, 0])
        # 8: all on (dp=0)
        self.assertEqual(decoder.decode(8), [1, 1, 1, 1, 1, 1, 1, 0])

    def test_seven_segment_with_dp(self):
        decoder = SevenSegmentDecoder()
        result = decoder.decode(5, dp=1)
        self.assertEqual(result, [1, 0, 1, 1, 0, 1, 1, 1])


class TestComparator(unittest.TestCase):
    """测试数值比较器"""

    def test_comparator_1bit(self):
        comp = Comparator1Bit()
        # 0 vs 0
        gt, eq, lt = comp.compare(0, 0)
        self.assertEqual(gt, 0)
        self.assertEqual(eq, 1)
        self.assertEqual(lt, 0)
        # 1 vs 0
        gt, eq, lt = comp.compare(1, 0)
        self.assertEqual(gt, 1)
        self.assertEqual(eq, 0)
        self.assertEqual(lt, 0)
        # 0 vs 1
        gt, eq, lt = comp.compare(0, 1)
        self.assertEqual(gt, 0)
        self.assertEqual(eq, 0)
        self.assertEqual(lt, 1)

    def test_comparator_4bit(self):
        comp = Comparator4Bit()
        # 10 vs 10
        gt, eq, lt = comp.compare(10, 10)
        self.assertEqual(eq, 1)
        # 15 vs 10
        gt, eq, lt = comp.compare(15, 10)
        self.assertEqual(gt, 1)
        # 10 vs 15
        gt, eq, lt = comp.compare(10, 15)
        self.assertEqual(lt, 1)

    def test_comparator_nbit(self):
        comp = ComparatorNBit(8)
        gt, eq, lt = comp.compare(255, 0)
        self.assertEqual(gt, 1)
        gt, eq, lt = comp.compare(128, 128)
        self.assertEqual(eq, 1)

    def test_comparison_string(self):
        comp = Comparator4Bit()
        self.assertEqual(comp.to_string(10, 10), "10 == 10")
        self.assertEqual(comp.to_string(15, 10), "15 > 10")
        self.assertEqual(comp.to_string(10, 15), "10 < 15")


class TestTriStateBuffer(unittest.TestCase):
    """测试三态缓冲器"""

    def test_active_high(self):
        buf = TriStateBuffer(active_high=True)
        self.assertEqual(buf.output(1, 1), 1)
        self.assertEqual(buf.output(0, 1), 0)
        self.assertIsNone(buf.output(1, 0))  # 高阻态

    def test_active_low(self):
        buf = TriStateBuffer(active_high=False)
        self.assertEqual(buf.output(1, 0), 1)
        self.assertEqual(buf.output(0, 0), 0)
        self.assertIsNone(buf.output(1, 1))  # 高阻态

    def test_output_z_str(self):
        buf = TriStateBuffer()
        self.assertEqual(buf.output_z_str(1, 1), "1")
        self.assertEqual(buf.output_z_str(0, 1), "0")
        self.assertEqual(buf.output_z_str(1, 0), "Z")


class TestBusDriver(unittest.TestCase):
    """测试总线驱动器"""

    def test_single_buffer(self):
        driver = BusDriver(4)
        self.assertEqual(driver.drive(0, 1, 1), 1)
        self.assertEqual(driver.get_bus_value(), 1)

    def test_bus_conflict(self):
        driver = BusDriver(4)
        self.assertTrue(driver.check_bus_conflict([1, 1, 0, 0]))
        self.assertFalse(driver.check_bus_conflict([1, 0, 0, 0]))
        self.assertFalse(driver.check_bus_conflict([0, 0, 0, 0]))


class TestLogicSynthesis(unittest.TestCase):
    """测试逻辑综合"""

    def test_implement_from_truth_table(self):
        synth = MuxLogicSynthesizer()
        # AND function: [0, 0, 0, 1]
        func = synth.implement_from_truth_table(2, [0, 0, 0, 1])
        self.assertEqual(func(0, 0), 0)
        self.assertEqual(func(0, 1), 0)
        self.assertEqual(func(1, 0), 0)
        self.assertEqual(func(1, 1), 1)

    def test_get_truth_table(self):
        synth = MuxLogicSynthesizer()

        def and_func(a, b):
            return a & b

        tt = synth.get_truth_table(and_func, 2)
        self.assertEqual(tt, [0, 0, 0, 1])

    def test_simplify_with_mux(self):
        synth = MuxLogicSynthesizer()

        def xor_func(a, b):
            return a ^ b

        info = synth.simplify_with_mux(xor_func, 2)
        self.assertEqual(info['num_variables'], 2)
        self.assertEqual(info['mux_type'], '4:1')
        self.assertEqual(info['truth_table'], [0, 1, 1, 0])

    def test_3var_function(self):
        synth = MuxLogicSynthesizer()
        # F(A,B,C) = A XOR B XOR C
        truth_table = [0] * 8
        for i in range(8):
            bits = bin(i).count('1')
            truth_table[i] = bits % 2

        func = synth.implement_from_truth_table(3, truth_table)
        self.assertEqual(func(0, 0, 0), 0)
        self.assertEqual(func(1, 0, 0), 1)
        self.assertEqual(func(1, 1, 0), 0)
        self.assertEqual(func(1, 1, 1), 1)


if __name__ == "__main__":
    unittest.main()
