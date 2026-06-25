"""
应用模块测试模块

测试数字电路应用的功能。
"""

import pytest
from src.applications.cpu import SimpleCPU
from src.applications.memory import MemoryUnit, ROM, CacheLine


class TestSimpleCPU:
    """简单CPU测试"""

    def test_load_program(self):
        """测试加载程序"""
        cpu = SimpleCPU()

        program = [
            0b00010001,  # LOAD R0, 1
            0b00010101,  # LOAD R1, 5
            0b10110000,  # HALT
        ]

        cpu.load_program(program)
        assert cpu.get_pc() == 0

    def test_run_program(self):
        """测试运行程序"""
        cpu = SimpleCPU()

        # 简单程序：加载两个数并相加
        # 指令格式: [opcode(4)] [reg1(2)] [reg2/imm(2)]
        # LOAD R0, 1: 0b00010001 (opcode=0001, reg1=00, imm=01)
        # LOAD R1, 1: 0b00010101 (opcode=0001, reg1=01, imm=01)
        # ADD R0, R1: 0b00100001 (opcode=0010, reg1=00, reg2=01)
        program = [
            0b00010001,  # LOAD R0, 1
            0b00010101,  # LOAD R1, 1
            0b00100001,  # ADD R0, R1
            0b10110000,  # HALT
        ]

        cpu.load_program(program)
        cpu.run()

        assert cpu.is_halted()
        assert cpu.get_register(0) == 2  # 1 + 1 = 2

    def test_subtraction(self):
        """测试减法"""
        cpu = SimpleCPU()

        # LOAD R0, 3: 0b00010011 (opcode=0001, reg1=00, imm=11=3)
        # LOAD R1, 1: 0b00010101 (opcode=0001, reg1=01, imm=01=1)
        program = [
            0b00010011,  # LOAD R0, 3
            0b00010101,  # LOAD R1, 1
            0b00110001,  # SUB R0, R1
            0b10110000,  # HALT
        ]

        cpu.load_program(program)
        cpu.run()

        assert cpu.get_register(0) == 2  # 3 - 1 = 2

    def test_and_operation(self):
        """测试AND运算"""
        cpu = SimpleCPU()

        # LOAD R0, 3: 0b00010011 (opcode=0001, reg1=00, imm=11=3)
        # LOAD R1, 2: 0b00010110 (opcode=0001, reg1=01, imm=10=2)
        program = [
            0b00010011,  # LOAD R0, 3
            0b00010110,  # LOAD R1, 2
            0b01000001,  # AND R0, R1
            0b10110000,  # HALT
        ]

        cpu.load_program(program)
        cpu.run()

        assert cpu.get_register(0) == 2  # 3 & 2 = 2

    def test_or_operation(self):
        """测试OR运算"""
        cpu = SimpleCPU()

        # LOAD R0, 3: 0b00010011 (opcode=0001, reg1=00, imm=11=3)
        # LOAD R1, 1: 0b00010101 (opcode=0001, reg1=01, imm=01=1)
        program = [
            0b00010011,  # LOAD R0, 3
            0b00010101,  # LOAD R1, 1
            0b01010001,  # OR R0, R1
            0b10110000,  # HALT
        ]

        cpu.load_program(program)
        cpu.run()

        assert cpu.get_register(0) == 3  # 3 | 1 = 3

    def test_xor_operation(self):
        """测试XOR运算"""
        cpu = SimpleCPU()

        # LOAD R0, 3: 0b00010011 (opcode=0001, reg1=00, imm=11=3)
        # LOAD R1, 1: 0b00010101 (opcode=0001, reg1=01, imm=01=1)
        program = [
            0b00010011,  # LOAD R0, 3
            0b00010101,  # LOAD R1, 1
            0b01100001,  # XOR R0, R1
            0b10110000,  # HALT
        ]

        cpu.load_program(program)
        cpu.run()

        assert cpu.get_register(0) == 2  # 3 ^ 1 = 2

    def test_not_operation(self):
        """测试NOT运算"""
        cpu = SimpleCPU()

        program = [
            0b00010011,  # LOAD R0, 3 (0011)
            0b01110000,  # NOT R0
            0b10110000,  # HALT
        ]

        cpu.load_program(program)
        cpu.run()

        assert cpu.get_register(0) == 12  # NOT 3 = 12 (4位)

    def test_jump(self):
        """测试跳转"""
        cpu = SimpleCPU()

        program = [
            0b00010001,  # LOAD R0, 1
            0b10010011,  # JMP 3
            0b00010100,  # LOAD R1, 0 (跳过)
            0b00010010,  # LOAD R0, 2
            0b10110000,  # HALT
        ]

        cpu.load_program(program)
        cpu.run()

        assert cpu.get_register(0) == 2

    def test_halt(self):
        """测试停机"""
        cpu = SimpleCPU()

        # HALT指令: opcode=1111 (0xF)
        program = [
            0b11110000,  # HALT (opcode=1111)
        ]

        cpu.load_program(program)
        cpu.step()

        assert cpu.is_halted()

    def test_get_state(self):
        """测试获取状态"""
        cpu = SimpleCPU()

        # LOAD R0, 1: 0b00010001 (opcode=0001, reg1=00, imm=01=1)
        # HALT: 0b11110000 (opcode=1111)
        program = [
            0b00010001,  # LOAD R0, 1
            0b11110000,  # HALT
        ]

        cpu.load_program(program)
        cpu.run()

        state = cpu.get_state()
        assert state['halted'] == True
        assert state['registers'][0] == 1

    def test_disassemble(self):
        """测试反汇编"""
        cpu = SimpleCPU()

        program = [
            0b00010001,  # LOAD R0, 1
            0b00100001,  # ADD R0, R1
            0b11110000,  # HALT
        ]

        cpu.load_program(program)
        disassembly = cpu.disassemble()

        assert len(disassembly) == 3
        assert "LOAD" in disassembly[0]
        assert "ADD" in disassembly[1]
        assert "HALT" in disassembly[2]

    def test_reset(self):
        """测试重置"""
        cpu = SimpleCPU()

        # LOAD R0, 1: 0b00010001 (opcode=0001, reg1=00, imm=01=1)
        # HALT: 0b11110000 (opcode=1111)
        program = [
            0b00010001,  # LOAD R0, 1
            0b11110000,  # HALT
        ]

        cpu.load_program(program)
        cpu.run()

        cpu.reset()

        assert cpu.get_register(0) == 0
        assert cpu.get_pc() == 0
        assert not cpu.is_halted()


class TestMemoryUnit:
    """存储单元测试"""

    def test_write_read(self):
        """测试写入和读取"""
        memory = MemoryUnit(4, 8)  # 16个地址，8位宽
        
        data = [1, 0, 1, 0, 1, 0, 1, 0]
        memory.write(0, data)
        
        assert memory.read(0) == data

    def test_multiple_addresses(self):
        """测试多个地址"""
        memory = MemoryUnit(4, 8)
        
        data1 = [1, 0, 1, 0, 1, 0, 1, 0]
        data2 = [0, 1, 0, 1, 0, 1, 0, 1]
        
        memory.write(0, data1)
        memory.write(1, data2)
        
        assert memory.read(0) == data1
        assert memory.read(1) == data2

    def test_clear(self):
        """测试清零"""
        memory = MemoryUnit(4, 8)
        
        memory.write(0, [1, 0, 1, 0, 1, 0, 1, 0])
        memory.clear()
        
        assert memory.read(0) == [0, 0, 0, 0, 0, 0, 0, 0]

    def test_dump(self):
        """测试转储"""
        memory = MemoryUnit(4, 8)
        
        memory.write(0, [1, 0, 1, 0, 1, 0, 1, 0])
        memory.write(5, [0, 1, 0, 1, 0, 1, 0, 1])
        
        dump = memory.dump()
        assert 0 in dump
        assert 5 in dump
        assert len(dump) == 2

    def test_get_size(self):
        """测试获取大小"""
        memory = MemoryUnit(4, 8)
        
        assert memory.get_size() == 128  # 16 * 8

    def test_invalid_address(self):
        """测试无效地址"""
        memory = MemoryUnit(4, 8)
        
        with pytest.raises(ValueError):
            memory.write(16, [1, 0, 1, 0, 1, 0, 1, 0])  # 地址超出范围

    def test_invalid_data(self):
        """测试无效数据"""
        memory = MemoryUnit(4, 8)
        
        with pytest.raises(ValueError):
            memory.write(0, [1, 0, 1])  # 数据位数不匹配


class TestROM:
    """ROM测试"""

    def test_program_read(self):
        """测试编程和读取"""
        rom = ROM(4, 8)
        
        data = [1, 0, 1, 0, 1, 0, 1, 0]
        rom.program(0, data)
        
        assert rom.read(0) == data

    def test_load_program(self):
        """测试加载程序"""
        rom = ROM(4, 8)
        
        program = [
            [1, 0, 1, 0, 1, 0, 1, 0],
            [0, 1, 0, 1, 0, 1, 0, 1],
            [1, 1, 1, 1, 0, 0, 0, 0],
        ]
        
        rom.load_program(program)
        
        assert rom.read(0) == program[0]
        assert rom.read(1) == program[1]
        assert rom.read(2) == program[2]


class TestCacheLine:
    """缓存行测试"""

    def test_write_read(self):
        """测试写入和读取"""
        line = CacheLine(4, 8)
        
        data = [1, 0, 1, 0, 1, 0, 1, 0]
        line.write(0, data)
        
        assert line.read(0) == data

    def test_valid(self):
        """测试有效位"""
        line = CacheLine(4, 8)
        
        assert line.is_valid(0) == False
        
        line.write(0, [1, 0, 1, 0, 1, 0, 1, 0])
        assert line.is_valid(0) == True

    def test_dirty(self):
        """测试脏位"""
        line = CacheLine(4, 8)
        
        assert line.is_dirty(0) == False
        
        line.write(0, [1, 0, 1, 0, 1, 0, 1, 0])
        assert line.is_dirty(0) == True

    def test_invalidate(self):
        """测试使无效"""
        line = CacheLine(4, 8)
        
        line.write(0, [1, 0, 1, 0, 1, 0, 1, 0])
        line.invalidate(0)
        
        assert line.is_valid(0) == False

    def test_clear(self):
        """测试清零"""
        line = CacheLine(4, 8)
        
        line.write(0, [1, 0, 1, 0, 1, 0, 1, 0])
        line.clear()
        
        assert line.read(0) == [0, 0, 0, 0, 0, 0, 0, 0]
        assert line.is_valid(0) == False
        assert line.is_dirty(0) == False
