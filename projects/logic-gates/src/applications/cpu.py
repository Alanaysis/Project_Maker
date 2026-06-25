"""
简单CPU模块

实现一个简单的CPU设计，展示数字电路在计算机中的应用。
"""

from typing import Dict, List, Optional
from ..combinational.alu import ALU
from ..sequential.register import Register
from ..sequential.counter import Counter


class SimpleCPU:
    """简单CPU

    一个简化的CPU设计，支持：
    - 4位数据宽度
    - 基本算术和逻辑运算
    - 简单的指令集
    - 程序计数器
    - 寄存器文件

    指令集：
    - 0000: NOP (空操作)
    - 0001: LOAD (加载立即数到寄存器)
    - 0010: ADD (寄存器加法)
    - 0011: SUB (寄存器减法)
    - 0100: AND (按位与)
    - 0101: OR  (按位或)
    - 0110: XOR (按位异或)
    - 0111: NOT (按位取反)
    - 1000: STORE (存储到内存)
    - 1001: JMP (无条件跳转)
    - 1010: JZ  (零跳转)
    - 1011: HALT (停机)

    Examples:
        >>> cpu = SimpleCPU()
        >>> program = [
        ...     0b00010001,  # LOAD R1, 1
        ...     0b00010010,  # LOAD R2, 2
        ...     0b00100110,  # ADD R1, R2 -> R1
        ...     0b10110000,  # HALT
        ... ]
        >>> cpu.load_program(program)
        >>> cpu.run()
        >>> cpu.get_register(0)
        3  # 1 + 2 = 3
    """

    # 指令定义
    OP_NOP = 0x0
    OP_LOAD = 0x1
    OP_ADD = 0x2
    OP_SUB = 0x3
    OP_AND = 0x4
    OP_OR = 0x5
    OP_XOR = 0x6
    OP_NOT = 0x7
    OP_STORE = 0x8
    OP_JMP = 0x9
    OP_JZ = 0xA
    OP_HALT = 0xF

    def __init__(self, data_width: int = 4, num_registers: int = 4, 
                 memory_size: int = 16):
        """初始化CPU

        Args:
            data_width: 数据宽度（位）
            num_registers: 寄存器数量
            memory_size: 内存大小
        """
        self.data_width = data_width
        self.num_registers = num_registers
        self.memory_size = memory_size

        # 组件
        self._alu = ALU(data_width)
        self._registers = [Register(data_width) for _ in range(num_registers)]
        self._pc = Counter(data_width)  # 程序计数器
        self._memory = [0] * memory_size  # 内存
        self._program = []  # 程序

        # 状态
        self._halted = False
        self._zero_flag = False
        self._step_count = 0

    def load_program(self, program: List[int]):
        """加载程序

        Args:
            program: 程序（指令列表）
        """
        self._program = program.copy()
        # 将程序加载到内存
        for i, instruction in enumerate(program):
            if i < self.memory_size:
                self._memory[i] = instruction
        self._pc.reset()

    def step(self) -> Dict:
        """执行一步

        Returns:
            Dict: 执行状态
        """
        if self._halted:
            return {"status": "halted", "step": self._step_count}

        # 获取当前PC
        pc_value = self._pc.get_count()

        # 检查PC是否超出范围
        if pc_value >= len(self._program):
            self._halted = True
            return {"status": "error", "message": "PC out of range", "step": self._step_count}

        # 获取指令
        instruction = self._program[pc_value]

        # 解码指令
        # 格式: [opcode(4)] [reg1(2)] [reg2/imm(2)]
        opcode = (instruction >> 4) & 0xF
        reg1 = (instruction >> 2) & 0x3
        reg2 = instruction & 0x3
        immediate = instruction & 0x3

        # 执行指令
        result = self._execute_instruction(opcode, reg1, reg2, immediate)

        # 更新PC
        if not result.get("jump", False):
            self._pc.increment()

        self._step_count += 1

        return {
            "status": "running" if not self._halted else "halted",
            "pc": pc_value,
            "instruction": instruction,
            "opcode": opcode,
            "result": result,
            "step": self._step_count
        }

    def _execute_instruction(self, opcode: int, reg1: int, reg2: int,
                            immediate: int) -> Dict:
        """执行指令

        Args:
            opcode: 操作码
            reg1: 寄存器1
            reg2: 寄存器2
            immediate: 立即数

        Returns:
            Dict: 执行结果
        """
        result = {"opcode": opcode, "jump": False}

        if opcode == self.OP_NOP:
            # 空操作
            pass

        elif opcode == self.OP_LOAD:
            # 加载立即数到寄存器
            self._registers[reg1].set_value(immediate)
            result["action"] = f"LOAD R{reg1}, {immediate}"

        elif opcode == self.OP_ADD:
            # 寄存器加法
            val1 = self._registers[reg1].get_value()
            val2 = self._registers[reg2].get_value()
            alu_result = self._alu.add(val1, val2)
            # 转换ALU结果从列表到整数
            result_value = self._bits_to_int(alu_result["result"])
            self._registers[reg1].set_value(result_value)
            self._zero_flag = alu_result["zero"]
            result["action"] = f"ADD R{reg1}, R{reg2}"
            result["value"] = result_value

        elif opcode == self.OP_SUB:
            # 寄存器减法
            val1 = self._registers[reg1].get_value()
            val2 = self._registers[reg2].get_value()
            alu_result = self._alu.sub(val1, val2)
            # 转换ALU结果从列表到整数
            result_value = self._bits_to_int(alu_result["result"])
            self._registers[reg1].set_value(result_value)
            self._zero_flag = alu_result["zero"]
            result["action"] = f"SUB R{reg1}, R{reg2}"
            result["value"] = result_value

        elif opcode == self.OP_AND:
            # 按位与
            val1 = self._registers[reg1].get_value()
            val2 = self._registers[reg2].get_value()
            alu_result = self._alu.and_op(val1, val2)
            # 转换ALU结果从列表到整数
            result_value = self._bits_to_int(alu_result["result"])
            self._registers[reg1].set_value(result_value)
            self._zero_flag = alu_result["zero"]
            result["action"] = f"AND R{reg1}, R{reg2}"
            result["value"] = result_value

        elif opcode == self.OP_OR:
            # 按位或
            val1 = self._registers[reg1].get_value()
            val2 = self._registers[reg2].get_value()
            alu_result = self._alu.or_op(val1, val2)
            # 转换ALU结果从列表到整数
            result_value = self._bits_to_int(alu_result["result"])
            self._registers[reg1].set_value(result_value)
            self._zero_flag = alu_result["zero"]
            result["action"] = f"OR R{reg1}, R{reg2}"
            result["value"] = result_value

        elif opcode == self.OP_XOR:
            # 按位异或
            val1 = self._registers[reg1].get_value()
            val2 = self._registers[reg2].get_value()
            alu_result = self._alu.xor_op(val1, val2)
            # 转换ALU结果从列表到整数
            result_value = self._bits_to_int(alu_result["result"])
            self._registers[reg1].set_value(result_value)
            self._zero_flag = alu_result["zero"]
            result["action"] = f"XOR R{reg1}, R{reg2}"
            result["value"] = result_value

        elif opcode == self.OP_NOT:
            # 按位取反
            val1 = self._registers[reg1].get_value()
            # NOT 操作
            not_result = ((1 << self.data_width) - 1) ^ val1
            self._registers[reg1].set_value(not_result)
            self._zero_flag = (not_result == 0)
            result["action"] = f"NOT R{reg1}"
            result["value"] = not_result

        elif opcode == self.OP_STORE:
            # 存储到内存
            val1 = self._registers[reg1].get_value()
            addr = self._registers[reg2].get_value()
            if addr < self.memory_size:
                self._memory[addr] = val1
                result["action"] = f"STORE R{reg1}, [R{reg2}]"
                result["address"] = addr
                result["value"] = val1

        elif opcode == self.OP_JMP:
            # 无条件跳转
            addr = immediate
            self._pc.set_count(addr)
            result["action"] = f"JMP {addr}"
            result["jump"] = True

        elif opcode == self.OP_JZ:
            # 零跳转
            if self._zero_flag:
                addr = immediate
                self._pc.set_count(addr)
                result["action"] = f"JZ {addr} (taken)"
                result["jump"] = True
            else:
                result["action"] = f"JZ {immediate} (not taken)"

        elif opcode == self.OP_HALT:
            # 停机
            self._halted = True
            result["action"] = "HALT"

        else:
            result["action"] = f"Unknown opcode: {opcode}"

        return result

    def _bits_to_int(self, bits: List[int]) -> int:
        """将二进制列表转换为整数（高位在前）

        Args:
            bits: 二进制列表

        Returns:
            int: 整数值
        """
        result = 0
        for i, bit in enumerate(bits):
            result |= bit << (len(bits) - 1 - i)
        return result

    def run(self, max_steps: int = 1000):
        """运行程序

        Args:
            max_steps: 最大步数
        """
        for _ in range(max_steps):
            result = self.step()
            if result["status"] in ("halted", "error"):
                break

    def get_register(self, index: int) -> int:
        """获取寄存器值

        Args:
            index: 寄存器索引

        Returns:
            int: 寄存器值
        """
        if index < 0 or index >= self.num_registers:
            raise ValueError(f"Register index out of range: {index}")
        return self._registers[index].get_value()

    def get_all_registers(self) -> List[int]:
        """获取所有寄存器值

        Returns:
            List[int]: 所有寄存器值
        """
        return [reg.get_value() for reg in self._registers]

    def get_pc(self) -> int:
        """获取程序计数器

        Returns:
            int: PC值
        """
        return self._pc.get_count()

    def get_memory(self, address: int) -> int:
        """获取内存值

        Args:
            address: 内存地址

        Returns:
            int: 内存值
        """
        if address < 0 or address >= self.memory_size:
            raise ValueError(f"Memory address out of range: {address}")
        return self._memory[address]

    def is_halted(self) -> bool:
        """检查是否停机

        Returns:
            bool: 是否停机
        """
        return self._halted

    def reset(self):
        """重置CPU"""
        for reg in self._registers:
            reg.clear()
        self._pc.reset()
        self._halted = False
        self._zero_flag = False
        self._step_count = 0

    def get_state(self) -> Dict:
        """获取CPU状态

        Returns:
            Dict: CPU状态
        """
        return {
            "pc": self.get_pc(),
            "registers": self.get_all_registers(),
            "halted": self.is_halted(),
            "zero_flag": self._zero_flag,
            "step_count": self._step_count
        }

    def disassemble(self) -> List[str]:
        """反汇编程序

        Returns:
            List[str]: 反汇编结果
        """
        result = []

        for i, instruction in enumerate(self._program):
            opcode = (instruction >> 4) & 0xF
            reg1 = (instruction >> 2) & 0x3
            reg2 = instruction & 0x3
            immediate = instruction & 0xF

            if opcode == self.OP_NOP:
                result.append(f"{i:04d}: NOP")
            elif opcode == self.OP_LOAD:
                result.append(f"{i:04d}: LOAD R{reg1}, {immediate}")
            elif opcode == self.OP_ADD:
                result.append(f"{i:04d}: ADD R{reg1}, R{reg2}")
            elif opcode == self.OP_SUB:
                result.append(f"{i:04d}: SUB R{reg1}, R{reg2}")
            elif opcode == self.OP_AND:
                result.append(f"{i:04d}: AND R{reg1}, R{reg2}")
            elif opcode == self.OP_OR:
                result.append(f"{i:04d}: OR R{reg1}, R{reg2}")
            elif opcode == self.OP_XOR:
                result.append(f"{i:04d}: XOR R{reg1}, R{reg2}")
            elif opcode == self.OP_NOT:
                result.append(f"{i:04d}: NOT R{reg1}")
            elif opcode == self.OP_STORE:
                result.append(f"{i:04d}: STORE R{reg1}, [R{reg2}]")
            elif opcode == self.OP_JMP:
                result.append(f"{i:04d}: JMP {immediate}")
            elif opcode == self.OP_JZ:
                result.append(f"{i:04d}: JZ {immediate}")
            elif opcode == self.OP_HALT:
                result.append(f"{i:04d}: HALT")
            else:
                result.append(f"{i:04d}: UNKNOWN ({instruction:08b})")

        return result
