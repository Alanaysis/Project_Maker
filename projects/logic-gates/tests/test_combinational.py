"""
组合电路测试模块

测试组合逻辑电路的功能。
"""

import pytest
from src.combinational.multiplexer import Multiplexer, Demultiplexer
from src.combinational.decoder import Decoder, Encoder
from src.combinational.adder import HalfAdder, FullAdder, RippleCarryAdder
from src.combinational.comparator import Comparator
from src.combinational.alu import ALU


class TestMultiplexer:
    """多路选择器测试"""

    def test_2to1_mux(self):
        """测试2选1多路选择器"""
        mux = Multiplexer(1)  # 2:1
        assert mux.evaluate([0, 1], [0]) == 0
        assert mux.evaluate([0, 1], [1]) == 1

    def test_4to1_mux(self):
        """测试4选1多路选择器"""
        mux = Multiplexer(2)  # 4:1
        # select_inputs: [S0, S1] where S0 is LSB
        # [0,0]=0, [1,0]=1, [0,1]=2, [1,1]=3
        data = [1, 0, 1, 0]

        assert mux.evaluate(data, [0, 0]) == data[0]  # 1
        assert mux.evaluate(data, [1, 0]) == data[1]  # 0
        assert mux.evaluate(data, [0, 1]) == data[2]  # 1
        assert mux.evaluate(data, [1, 1]) == data[3]  # 0

    def test_8to1_mux(self):
        """测试8选1多路选择器"""
        mux = Multiplexer(3)  # 8:1
        data = [1, 0, 1, 0, 1, 0, 1, 0]

        for i in range(8):
            # select_inputs: [S0, S1, S2] where S0 is LSB
            select = [i & 1, (i >> 1) & 1, (i >> 2) & 1]
            result = mux.evaluate(data, select)
            assert result == data[i]

    def test_invalid_inputs(self):
        """测试无效输入"""
        mux = Multiplexer(2)

        with pytest.raises(ValueError):
            mux.evaluate([0, 1], [0])  # 数据输入数量错误

        with pytest.raises(ValueError):
            mux.evaluate([0, 1, 0, 1], [0])  # 选择输入数量错误


class TestDemultiplexer:
    """多路分配器测试"""

    def test_1to2_demux(self):
        """测试1:2多路分配器"""
        demux = Demultiplexer(1)

        outputs = demux.evaluate(1, [0])
        assert outputs == [1, 0]

        outputs = demux.evaluate(1, [1])
        assert outputs == [0, 1]

    def test_1to4_demux(self):
        """测试1:4多路分配器"""
        demux = Demultiplexer(2)

        for i in range(4):
            # select_inputs: [S0, S1] where S0 is LSB
            select = [i & 1, (i >> 1) & 1]
            outputs = demux.evaluate(1, select)
            assert sum(outputs) == 1
            assert outputs[i] == 1


class TestDecoder:
    """解码器测试"""

    def test_2to4_decoder(self):
        """测试2:4解码器"""
        decoder = Decoder(2)

        # inputs: [I0, I1] where I0 is LSB
        # [0,0]=0, [1,0]=1, [0,1]=2, [1,1]=3
        assert decoder.evaluate([0, 0]) == [1, 0, 0, 0]
        assert decoder.evaluate([1, 0]) == [0, 1, 0, 0]
        assert decoder.evaluate([0, 1]) == [0, 0, 1, 0]
        assert decoder.evaluate([1, 1]) == [0, 0, 0, 1]

    def test_3to8_decoder(self):
        """测试3:8解码器"""
        decoder = Decoder(3)

        for i in range(8):
            # inputs: [I0, I1, I2] where I0 is LSB
            inputs = [i & 1, (i >> 1) & 1, (i >> 2) & 1]
            outputs = decoder.evaluate(inputs)
            assert sum(outputs) == 1
            assert outputs[i] == 1

    def test_invalid_inputs(self):
        """测试无效输入"""
        decoder = Decoder(2)

        with pytest.raises(ValueError):
            decoder.evaluate([0])  # 输入数量错误


class TestEncoder:
    """编码器测试"""

    def test_4to2_encoder(self):
        """测试4:2编码器"""
        encoder = Encoder(4)
        
        assert encoder.evaluate([1, 0, 0, 0]) == [0, 0]
        assert encoder.evaluate([0, 1, 0, 0]) == [0, 1]
        assert encoder.evaluate([0, 0, 1, 0]) == [1, 0]
        assert encoder.evaluate([0, 0, 0, 1]) == [1, 1]

    def test_no_input(self):
        """测试无输入"""
        encoder = Encoder(4)
        assert encoder.evaluate([0, 0, 0, 0]) == [0, 0]


class TestHalfAdder:
    """半加器测试"""

    def test_all_inputs(self):
        """测试所有输入组合"""
        ha = HalfAdder()
        
        sum_val, carry = ha.evaluate(0, 0)
        assert sum_val == 0 and carry == 0
        
        sum_val, carry = ha.evaluate(0, 1)
        assert sum_val == 1 and carry == 0
        
        sum_val, carry = ha.evaluate(1, 0)
        assert sum_val == 1 and carry == 0
        
        sum_val, carry = ha.evaluate(1, 1)
        assert sum_val == 0 and carry == 1


class TestFullAdder:
    """全加器测试"""

    def test_all_inputs(self):
        """测试所有输入组合"""
        fa = FullAdder()
        
        # 0 + 0 + 0 = 0, carry = 0
        sum_val, carry = fa.evaluate(0, 0, 0)
        assert sum_val == 0 and carry == 0
        
        # 0 + 0 + 1 = 1, carry = 0
        sum_val, carry = fa.evaluate(0, 0, 1)
        assert sum_val == 1 and carry == 0
        
        # 0 + 1 + 0 = 1, carry = 0
        sum_val, carry = fa.evaluate(0, 1, 0)
        assert sum_val == 1 and carry == 0
        
        # 0 + 1 + 1 = 0, carry = 1
        sum_val, carry = fa.evaluate(0, 1, 1)
        assert sum_val == 0 and carry == 1
        
        # 1 + 0 + 0 = 1, carry = 0
        sum_val, carry = fa.evaluate(1, 0, 0)
        assert sum_val == 1 and carry == 0
        
        # 1 + 0 + 1 = 0, carry = 1
        sum_val, carry = fa.evaluate(1, 0, 1)
        assert sum_val == 0 and carry == 1
        
        # 1 + 1 + 0 = 0, carry = 1
        sum_val, carry = fa.evaluate(1, 1, 0)
        assert sum_val == 0 and carry == 1
        
        # 1 + 1 + 1 = 1, carry = 1
        sum_val, carry = fa.evaluate(1, 1, 1)
        assert sum_val == 1 and carry == 1


class TestRippleCarryAdder:
    """纹波进位加法器测试"""

    def test_4bit_adder(self):
        """测试4位加法器"""
        adder = RippleCarryAdder(4)

        # 5 + 3 = 8
        # 5 = 0101 (high bit first) = 1010 (low bit first)
        # 3 = 0011 (high bit first) = 1100 (low bit first)
        a = [1, 0, 1, 0]  # 5 (低位在前)
        b = [1, 1, 0, 0]  # 3 (低位在前)
        result, carry = adder.evaluate(a, b)
        # 8 = 1000 (high bit first) = 0001 (low bit first)
        assert result == [0, 0, 0, 1]  # 8 (低位在前)
        assert carry == 0

        # 7 + 9 = 16
        # 7 = 0111 (high bit first) = 1110 (low bit first)
        # 9 = 1001 (high bit first) = 1001 (low bit first)
        a = [1, 1, 1, 0]  # 7 (低位在前)
        b = [1, 0, 0, 1]  # 9 (低位在前)
        result, carry = adder.evaluate(a, b)
        assert result == [0, 0, 0, 0]  # 0 (溢出)
        assert carry == 1

    def test_add_method(self):
        """测试add方法"""
        adder = RippleCarryAdder(4)

        result, carry = adder.add(5, 3)
        assert result == 8
        assert carry == 0

        result, carry = adder.add(15, 1)
        assert result == 0
        assert carry == 1


class TestComparator:
    """比较器测试"""

    def test_4bit_comparator(self):
        """测试4位比较器"""
        comp = Comparator(4)
        
        # 10 > 5
        result = comp.compare(10, 5)
        assert result['gt'] == 1
        assert result['eq'] == 0
        assert result['lt'] == 0
        
        # 5 < 10
        result = comp.compare(5, 10)
        assert result['gt'] == 0
        assert result['eq'] == 0
        assert result['lt'] == 1
        
        # 7 == 7
        result = comp.compare(7, 7)
        assert result['gt'] == 0
        assert result['eq'] == 1
        assert result['lt'] == 0

    def test_helper_methods(self):
        """测试辅助方法"""
        comp = Comparator(4)
        
        assert comp.is_greater(10, 5) == True
        assert comp.is_greater(5, 10) == False
        assert comp.is_equal(7, 7) == True
        assert comp.is_equal(7, 8) == False
        assert comp.is_less(5, 10) == True
        assert comp.is_less(10, 5) == False


class TestALU:
    """ALU测试"""

    def _bits_to_int(self, bits):
        """将二进制列表转换为整数（高位在前）"""
        val = 0
        for i, bit in enumerate(bits):
            val |= bit << (len(bits) - 1 - i)
        return val

    def test_add(self):
        """测试加法"""
        alu = ALU(4)

        result = alu.add(5, 3)
        assert self._bits_to_int(result['result']) == 8
        assert result['carry'] == 0

    def test_sub(self):
        """测试减法"""
        alu = ALU(4)

        result = alu.sub(8, 3)
        assert self._bits_to_int(result['result']) == 5

    def test_and(self):
        """测试按位与"""
        alu = ALU(4)

        result = alu.and_op(0b1010, 0b1100)
        assert self._bits_to_int(result['result']) == 0b1000

    def test_or(self):
        """测试按位或"""
        alu = ALU(4)

        result = alu.or_op(0b1010, 0b1100)
        assert self._bits_to_int(result['result']) == 0b1110

    def test_xor(self):
        """测试按位异或"""
        alu = ALU(4)

        result = alu.xor_op(0b1010, 0b1100)
        assert self._bits_to_int(result['result']) == 0b0110

    def test_zero_flag(self):
        """测试零标志"""
        alu = ALU(4)

        result = alu.sub(5, 5)
        assert result['zero'] == 1

    def test_negative_flag(self):
        """测试负数标志"""
        alu = ALU(4)

        result = alu.sub(3, 5)  # 3 - 5 = -2 (补码)
        assert result['negative'] == 1
