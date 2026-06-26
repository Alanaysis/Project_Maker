"""
ARM CPU Simulator Core Module
===============================

The main CPU simulator that ties together:
- Register file (registers.py)
- ALU (alu.py)
- Memory (memory.py)
- Decoder (decoder.py)
- Thumb support (thumb.py)
- Exception handling (exception.py)

Core Loop:
    指令读取 -> 条件检查 -> 指令执行 -> 状态更新
    (Fetch -> Condition Check -> Execute -> State Update)

ARM Architecture Background:
ARM processors implement a Load/Store architecture with:
- 16 general-purpose registers (R0-R15)
- CPSR (Current Program Status Register) for flags
- Condition execution (most instructions can be conditional)
- ARM/Thumb dual instruction set
- Pipeline stages: Fetch, Decode, Execute, Memory, Write-back

This simulator implements a simplified single-cycle model for educational purposes.
A real ARM processor has a multi-stage pipeline (ARM7: 3-stage, ARM9: 5-stage).
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.registers import RegisterFile, CPSR
from src.alu import ALU
from src.memory import Memory
from src.decoder import Decoder, Instruction
from src.thumb import ThumbDecoder, ThumbInstruction
from src.exception import ExceptionHandler, ExceptionType


class ARMCore:
    """
    ARM CPU Simulator Core

    Implements the core ARM processor functionality:
    - Register management
    - Instruction fetch and decode
    - Execution of ARM and Thumb instructions
    - Memory access
    - Exception handling
    - Execution tracing
    """

    def __init__(self, memory_size=0x10000):
        # Initialize components
        self.regs = RegisterFile()
        self.alu = ALU()
        self.memory = Memory(memory_size)
        self.decoder = Decoder()
        self.thumb_decoder = ThumbDecoder()
        self.exception_handler = ExceptionHandler()

        # Execution state
        self.running = False
        self.step_count = 0
        self.max_steps = 100000  # Safety limit
        self.trace_enabled = False
        self.trace_log = []

        # Instruction stream (for loading programs)
        self.instructions = []  # List of (address, instruction_word) tuples

    def reset(self):
        """Reset the CPU to initial state"""
        # Clear registers
        self.regs = RegisterFile()

        # Reset state
        self.running = False
        self.step_count = 0
        self.trace_log = []
        self.exception_handler.clear_exception_log()

        # Set initial PC
        self.regs.set_pc(0x00000000)

    def enable_trace(self):
        """Enable execution tracing"""
        self.trace_enabled = True

    def disable_trace(self):
        """Disable execution tracing"""
        self.trace_enabled = False

    def load_program(self, address, data):
        """
        Load a program into memory.

        Args:
            address: Starting address
            data: List of 32-bit instruction words
        """
        for i, word in enumerate(data):
            self.memory.write_word(address + (i * 4), word)

    def load_thumb_program(self, address, thumb_data):
        """
        Load a Thumb program into memory.

        Args:
            address: Starting address (must be 2-aligned)
            thumb_data: List of 16-bit Thumb instruction words
        """
        for i, word in enumerate(thumb_data):
            self.memory.write_byte(address + (i * 2), word & 0xFF)
            self.memory.write_byte(address + (i * 2) + 1, (word >> 8) & 0xFF)

    def run(self, max_steps=None):
        """
        Run the CPU until halted or max_steps reached.

        Args:
            max_steps: Maximum number of steps to execute

        Returns:
            Number of steps executed
        """
        if max_steps is None:
            max_steps = self.max_steps

        self.running = True
        steps = 0

        while self.running and steps < max_steps:
            steps += 1
            self.step_count += 1

            # Execute one instruction
            try:
                executed = self._execute_one()
                if not executed:
                    break
            except Exception as e:
                print(f"Error at step {steps}: {e}")
                break

        self.running = False
        return steps

    def step(self):
        """Execute a single instruction"""
        self.step_count += 1
        return self._execute_one()

    def halt(self):
        """Halt execution"""
        self.running = False

    def _execute_one(self):
        """
        Execute one instruction (the core of the simulator).

        Core loop:
        1. Fetch instruction from PC
        2. Decode instruction
        3. Check condition
        4. Execute instruction
        5. Update PC
        """
        # Get current PC
        pc = self.regs.get_pc()

        # Determine instruction state (ARM or Thumb)
        is_thumb = self.regs.cpsr.t

        if is_thumb:
            # Fetch Thumb instruction (16-bit, little-endian)
            instr_byte1 = self.memory.read_byte(pc)
            instr_byte2 = self.memory.read_byte(pc + 1)
            thumb_instr = instr_byte1 | (instr_byte2 << 8)

            # Decode Thumb instruction
            decoded = self.thumb_decoder.decode(thumb_instr)
            instr_width = 2

            # Execute Thumb instruction
            return self._execute_thumb(decoded)
        else:
            # Fetch ARM instruction (32-bit, little-endian)
            instr_word = self.memory.read_word(pc)

            # Decode ARM instruction
            decoded = self.decoder.decode(instr_word)
            instr_width = 4

            # Update PC before execution (ARM architecture: PC = current + 8)
            pc_aligned = pc & ~0x3  # Align to 4 bytes

            # Check condition
            if not self.regs.cpsr.check_condition(decoded.condition):
                # Condition not met, skip instruction
                self.regs.set_pc(pc + instr_width)
                return True

            # Execute instruction
            return self._execute(decoded, pc_aligned)

    def _execute(self, instr, pc):
        """Execute a decoded ARM instruction"""
        # Log trace
        if self.trace_enabled:
            self._log_trace(instr, pc)

        # Execute based on instruction type
        if instr.type == Instruction.DATA_PROCESSING:
            return self._execute_data_processing(instr, pc)
        elif instr.type == Instruction.LOAD_STORE:
            return self._execute_load_store(instr, pc)
        elif instr.type == Instruction.BRANCH:
            return self._execute_branch(instr, pc)
        elif instr.type == Instruction.MULTIPLY:
            return self._execute_multiply(instr, pc)
        elif instr.type == Instruction.UNDEFINED:
            return self.exception_handler.handle_exception(
                self, ExceptionType.UNDEFINED_INSTRUCTION, pc, instr
            )
        else:
            # Unknown instruction type, skip
            self.regs.set_pc(pc + 4)
            return True

    def _execute_thumb(self, instr):
        """Execute a decoded Thumb instruction"""
        pc = self.regs.get_pc()

        # Log trace
        if self.trace_enabled:
            self._log_trace_thumb(instr, pc)

        # Execute based on instruction type
        if instr.type == ThumbInstruction.DATA_PROCESSING:
            return self._execute_thumb_data_processing(instr, pc)
        elif instr.type == ThumbInstruction.LOAD_STORE:
            return self._execute_thumb_load_store(instr, pc)
        elif instr.type == ThumbInstruction.LONG_BRANCH:
            return self._execute_thumb_branch(instr, pc)
        elif instr.type == ThumbInstruction.SPECIAL:
            return self._execute_thumb_special(instr, pc)
        else:
            # Undefined, handle as exception
            self.regs.set_pc(pc + 2)
            return True

    def _execute_data_processing(self, instr, pc):
        """Execute a data processing instruction"""
        rd = instr.rd
        rn = instr.rn
        operand2 = instr.operand2
        operand2_type = instr.operand2_type
        update_flags = instr.update_flags

        # Get Rn value
        rn_val = self.regs.read_reg(rn)

        # Get operand2 value (with shift if needed)
        if operand2_type == 'immediate':
            op2 = operand2['value']
            shift_result = op2
        elif operand2_type == 'register':
            rm = operand2['reg']
            rm_val = self.regs.read_reg(rm)
            shift = operand2['shift']
            shift_reg = operand2['shift_reg']
            shift_amount = self.regs.read_reg(shift_reg) & 0x1F
            shift_result = self._shift_value(rm_val, shift, shift_amount)
        elif operand2_type == 'shifted_register':
            rm = operand2['reg']
            rm_val = self.regs.read_reg(rm)
            shift = operand2['shift']
            amount = operand2['amount']
            shift_result = self._shift_value(rm_val, shift, amount)
        else:
            shift_result = operand2['value']

        # Execute the operation
        mnemonic = instr.mnemonic
        result = 0
        n, z, c, v = 0, 0, 0, 0

        if mnemonic == Instruction.ADD:
            result, n, z, c, v = self.alu.add(rn_val, shift_result, set_flags=update_flags)
        elif mnemonic == Instruction.SUB:
            result, n, z, c, v = self.alu.subtract(rn_val, shift_result, set_flags=update_flags)
        elif mnemonic == Instruction.MOV:
            result, n, z, c, v = self.alu.move(shift_result, set_flags=update_flags)
        elif mnemonic == Instruction.MVN:
            result, n, z, c, v = self.alu.move_not(shift_result, set_flags=update_flags)
        elif mnemonic == Instruction.AND:
            result, n, z, c, v = self.alu.logical_and(rn_val, shift_result, set_flags=update_flags)
        elif mnemonic == Instruction.ORR:
            result, n, z, c, v = self.alu.logical_orr(rn_val, shift_result, set_flags=update_flags)
        elif mnemonic == Instruction.EOR:
            result, n, z, c, v = self.alu.logical_eor(rn_val, shift_result, set_flags=update_flags)
        elif mnemonic == Instruction.BIC:
            result, n, z, c, v = self.alu.logical_bic(rn_val, shift_result, set_flags=update_flags)
        elif mnemonic == Instruction.CMP:
            # CMP is SUB without destination
            result, n, z, c, v = self.alu.compare(rn_val, shift_result)
            result = shift_result  # For tracing
        elif mnemonic == Instruction.CMN:
            result, n, z, c, v = self.alu.compare_negated(rn_val, shift_result)
            result = shift_result
        elif mnemonic == Instruction.TST:
            n, z = self.alu.test(rn_val, shift_result)
            result = rn_val & shift_result
        elif mnemonic == Instruction.TEQ:
            n, z = self.alu.test_equal(rn_val, shift_result)
            result = rn_val ^ shift_result

        # Write result to destination register
        if rd is not None and mnemonic not in (Instruction.CMP, Instruction.CMN, Instruction.TST, Instruction.TEQ):
            self.regs.write_reg(rd, result)

        # Update CPSR flags
        if update_flags:
            self.regs.cpsr.set_condition(n, z, c, v)

        # Update PC
        self.regs.set_pc(pc + 4)
        return True

    def _execute_load_store(self, instr, pc):
        """Execute a load/store instruction"""
        mnemonic = instr.mnemonic
        rn = instr.rn
        rd = instr.rd
        offset = instr.offset
        write_back = instr.write_back
        rn_val = self.regs.read_reg(rn)

        # Calculate effective address
        if rn == 15:  # PC-relative
            effective_addr = pc + offset
        else:
            effective_addr = rn_val + offset

        if mnemonic in (Instruction.STR, Instruction.STRB):
            # Store instruction
            value = self.regs.read_reg(rd)
            if mnemonic == Instruction.STRB:
                self.memory.write_byte(effective_addr, value & 0xFF)
            else:
                self.memory.write_word(effective_addr, value)
        elif mnemonic in (Instruction.LDR, Instruction.LDRB):
            # Load instruction
            if mnemonic == Instruction.LDRB:
                value = self.memory.read_byte(effective_addr)
            else:
                value = self.memory.read_word(effective_addr)
            self.regs.write_reg(rd, value)
        elif mnemonic == Instruction.STM:
            # Store Multiple
            reg_list = instr.register_list
            sp = self.regs.get_sp()
            for i in range(16):
                if reg_list & (1 << i):
                    if write_back:
                        addr = sp + (i * 4)
                    else:
                        addr = sp + ((i + 1) * 4) if instr.up else sp - ((16 - i) * 4)
                    self.memory.write_word(addr, self.regs.read_reg(i))
            if write_back:
                self.regs.set_sp(sp + 64)  # All 16 registers
        elif mnemonic == Instruction.LDM:
            # Load Multiple
            reg_list = instr.register_list
            sp = self.regs.get_sp()
            for i in range(16):
                if reg_list & (1 << i):
                    value = self.memory.read_word(sp + (i * 4))
                    self.regs.write_reg(i, value)
            if write_back:
                self.regs.set_sp(sp + 64)

        # Write-back to base register
        if write_back and rn != 15:
            self.regs.write_reg(rn, effective_addr)

        # Update PC
        self.regs.set_pc(pc + 4)
        return True

    def _execute_branch(self, instr, pc):
        """Execute a branch instruction"""
        mnemonic = instr.mnemonic
        target = instr.target

        if mnemonic == Instruction.B:
            # Unconditional branch
            self.regs.set_pc(pc + target)
        elif mnemonic == Instruction.BL:
            # Branch with Link (save return address)
            lr = pc + 4
            self.regs.set_lr(lr)
            self.regs.set_pc(pc + target)
        elif mnemonic == Instruction.BX:
            # Branch and exchange
            target_reg = self.regs.read_reg(instr.rd)
            self.regs.set_pc(target_reg & ~0x1)  # Clear thumb bit from target
        elif mnemonic == Instruction.BLX:
            # Branch with Link and exchange
            lr = pc + 4
            self.regs.set_lr(lr)
            target_reg = self.regs.read_reg(instr.rd)
            self.regs.set_pc(target_reg)

        return True

    def _execute_multiply(self, instr, pc):
        """Execute a multiply instruction"""
        rd = instr.rd
        rn = instr.rn
        rm = instr.rm
        rn_val = self.regs.read_reg(rn)
        rm_val = self.regs.read_reg(rm)

        if instr.mnemonic == Instruction.MUL:
            result = self.alu.multiply(rn_val, rm_val)
            self.regs.write_reg(rd, result)
        elif instr.mnemonic == Instruction.MLA:
            ra = self.regs.read_reg(instr.ra)
            result = self.alu.multiply_accumulate(rn_val, rm_val, ra)
            self.regs.write_reg(rd, result)

        self.regs.set_pc(pc + 4)
        return True

    def _execute_thumb_data_processing(self, instr, pc):
        """Execute a Thumb data processing instruction"""
        rd = instr.rd
        rn = instr.rn
        op2 = instr.operand2
        rm = instr.rm if instr.rm is not None else op2

        rn_val = self.regs.read_reg(rn)

        if rm is not None:
            rm_val = self.regs.read_reg(rm)
            result = self.alu.add(rn_val, rm_val)
            self.regs.write_reg(rd, result)
        else:
            # Immediate operand
            result = self.alu.add(rn_val, op2)
            self.regs.write_reg(rd, result)

        self.regs.set_pc(pc + 2)
        return True

    def _execute_thumb_load_store(self, instr, pc):
        """Execute a Thumb load/store instruction"""
        rd = instr.rd
        rn = instr.rn
        offset = instr.operand2
        rn_val = self.regs.read_reg(rn)

        if rn == 15:  # PC-relative
            effective_addr = pc + offset
        else:
            effective_addr = rn_val + offset

        if instr.mnemonic == "STR":
            self.memory.write_word(effective_addr, self.regs.read_reg(rd))
        elif instr.mnemonic == "LDR":
            value = self.memory.read_word(effective_addr)
            self.regs.write_reg(rd, value)
        elif instr.mnemonic == "PUSH":
            # Push registers onto stack
            sp = self.regs.get_sp()
            reg_list = instr.register_list
            for i in range(16):
                if reg_list & (1 << i):
                    sp -= 4
                    self.memory.write_word(sp, self.regs.read_reg(i))
            self.regs.set_sp(sp)
        elif instr.mnemonic == "POP":
            # Pop registers from stack
            sp = self.regs.get_sp()
            reg_list = instr.register_list
            for i in range(16):
                if reg_list & (1 << i):
                    value = self.memory.read_word(sp)
                    self.regs.write_reg(i, value)
                    sp += 4
            self.regs.set_sp(sp)
            if reg_list & (1 << 15):  # POP PC
                self.regs.set_pc(self.regs.read_reg(15))

        self.regs.set_pc(pc + 2)
        return True

    def _execute_thumb_branch(self, instr, pc):
        """Execute a Thumb branch instruction"""
        if instr.mnemonic == "BX":
            target = self.regs.read_reg(instr.rd)
            # Check if target LSB is set (switch to ARM mode)
            if target & 0x1:
                self.regs.cpsr.value |= self.regs.cpsr.T_FLAG
                self.regs.set_pc(target & ~0x1)
            else:
                self.regs.cpsr.value &= ~self.regs.cpsr.T_FLAG
                self.regs.set_pc(target)
        else:
            # B (long branch)
            target = pc + instr.target
            self.regs.set_pc(target)

        return True

    def _execute_thumb_special(self, instr, pc):
        """Execute a Thumb special instruction"""
        if instr.mnemonic == "NOP":
            pass  # Do nothing
        elif instr.mnemonic == "ADD_SP":
            sp = self.regs.get_sp() + instr.operand2
            self.regs.set_sp(sp)
        elif instr.mnemonic == "SUB_SP":
            sp = self.regs.get_sp() - instr.operand2
            self.regs.set_sp(sp)

        self.regs.set_pc(pc + 2)
        return True

    def _shift_value(self, value, shift_type, amount):
        """
        Apply a shift operation to a value.

        Args:
            value: 32-bit value to shift
            shift_type: 'LSL', 'LSR', 'ASR', 'ROR'
            amount: Shift amount

        Returns:
            Shifted value
        """
        if amount == 0:
            return value & 0xFFFFFFFF

        if shift_type == "LSL":
            return (value << amount) & 0xFFFFFFFF
        elif shift_type == "LSR":
            return (value >> amount) & 0xFFFFFFFF
        elif shift_type == "ASR":
            # Arithmetic shift: preserve sign
            if value & 0x80000000:
                value = -(0x100000000 - value)
            result = value >> amount
            return result & 0xFFFFFFFF
        elif shift_type == "ROR":
            return ((value >> amount) | (value << (32 - amount))) & 0xFFFFFFFF

        return value & 0xFFFFFFFF

    def _log_trace(self, instr, pc):
        """Log execution trace for ARM instruction"""
        trace_entry = {
            'step': self.step_count,
            'pc': pc,
            'instruction': instr.mnemonic,
            'condition': instr.condition,
            'regs_before': self.regs.regs[:],
        }
        self.trace_log.append(trace_entry)

    def _log_trace_thumb(self, instr, pc):
        """Log execution trace for Thumb instruction"""
        trace_entry = {
            'step': self.step_count,
            'pc': pc,
            'instruction': instr.mnemonic,
            'condition': 'AL',
            'regs_before': self.regs.regs[:],
        }
        self.trace_log.append(trace_entry)

    def get_trace(self):
        """Get the execution trace log"""
        return self.trace_log

    def clear_trace(self):
        """Clear the execution trace log"""
        self.trace_log = []

    def get_state_summary(self):
        """Get a summary of the current CPU state"""
        summary = {
            'step': self.step_count,
            'pc': self.regs.get_pc(),
            'sp': self.regs.get_sp(),
            'lr': self.regs.get_lr(),
            'cpsr': str(self.regs.cpsr),
            'thumb_mode': self.regs.cpsr.t,
            'running': self.running,
        }
        return summary
