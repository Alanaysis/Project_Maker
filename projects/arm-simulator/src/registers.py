"""
ARM Register File Module
========================

Implements the ARM register file including:
- 16 general-purpose registers (R0-R15)
- CPSR (Current Program Status Register)
- SPSR (Saved Program Status Register) for exception modes

ARM Architecture Background:
- R0-R12: General purpose registers
- R13 (SP): Stack Pointer
- R14 (LR): Link Register (stores return address for branches)
- R15 (PC): Program Counter
- CPSR: Contains condition flags (N, Z, C, V) and control bits
- SPSR: Saved copy of CPSR used in exception modes

In ARM state, there are actually 37 registers (16 per mode x ~2 modes + banked registers).
This simulator implements a simplified model with the common registers.
"""


class CPSR:
    """
    CPSR - Current Program Status Register

    The CPSR in ARM architecture contains:
    - N (Negative): Set to the MSB of the result
    - Z (Zero): Set if the result is zero
    - C (Carry): Set on unsigned overflow
    - V (Overflow): Set on signed overflow
    - Q: Saturation flag (Thumb-2)
    - I: IRQ disable bit
    - F: FIQ disable bit
    - T: Thumb bit (1 = Thumb mode)
    - M[3:0]: Mode bits

    Condition flags are used by conditional instructions:
    - EQ (Z=1): Equal
    - NE (Z=0): Not equal
    - CS/HS (C=1): Unsigned higher or same
    - CC/LO (C=0): Unsigned lower
    - MI (N=1): Minus (negative)
    - PL (N=0): Plus (positive or zero)
    - VS (V=1): Overflow
    - VC (V=0): No overflow
    - HI (C=1 and Z=0): Unsigned higher
    - LS (C=0 or Z=1): Unsigned lower or same
    - GE (N=V): Greater or equal (signed)
    - LT (N!=V): Less than (signed)
    - GT (Z=0 and N=V): Greater than (signed)
    - LE (Z=1 or N!=V): Less or equal (signed)
    - AL (always): Always executed (default)
    """

    # Mode bits
    USER_MODE = 0x10
    FIQ_MODE = 0x11
    IRQ_MODE = 0x12
    SUPERVISOR_MODE = 0x13
    ABORT_MODE = 0x17
    UNDEFINED_MODE = 0x1B
    SYSTEM_MODE = 0x1F

    # Flag masks
    N_FLAG = 0x80000000
    Z_FLAG = 0x40000000
    C_FLAG = 0x20000000
    V_FLAG = 0x10000000
    Q_FLAG = 0x08000000
    I_FLAG = 0x00000080
    F_FLAG = 0x00000040
    T_FLAG = 0x00000020
    MODE_MASK = 0x0000001F

    def __init__(self):
        self.value = self.T_FLAG | self.USER_MODE  # Start in Thumb mode (for demo purposes)
        self._carry_out = None  # Internal: carry out for ADC/SBC
        self._borrow_out = None  # Internal: borrow out for SBC

    @property
    def n(self):
        """Negative flag: MSB of result"""
        return bool(self.value & self.N_FLAG)

    @property
    def z(self):
        """Zero flag: result is zero"""
        return bool(self.value & self.Z_FLAG)

    @property
    def c(self):
        """Carry flag: unsigned borrow/carry"""
        return bool(self.value & self.C_FLAG)

    @property
    def v(self):
        """Overflow flag: signed overflow"""
        return bool(self.value & self.V_FLAG)

    @property
    def t(self):
        """Thumb bit: 1 = Thumb mode, 0 = ARM mode"""
        return bool(self.value & self.T_FLAG)

    @property
    def mode(self):
        """Current processor mode"""
        return self.value & self.MODE_MASK

    @property
    def carry_out(self):
        return self._carry_out

    @property
    def borrow_out(self):
        return self._borrow_out

    def set_flags_from_result(self, result, is_subtraction=False, set_carry=True):
        """
        Update CPSR flags based on a computation result.

        Args:
            result: The computation result (32-bit signed integer)
            is_subtraction: If True, compute carry as borrow for subtraction
            set_carry: Whether to update the carry flag
        """
        # Mask result to 32 bits
        result = result & 0xFFFFFFFF

        # Clear all flag bits
        self.value &= ~(self.N_FLAG | self.Z_FLAG | self.C_FLAG | self.V_FLAG)

        # Set N flag (negative): check MSB
        if result & 0x80000000:
            self.value |= self.N_FLAG

        # Set Z flag (zero): check if result is zero
        if result == 0:
            self.value |= self.Z_FLAG

        # Set C flag (carry/borrow)
        if set_carry:
            if is_subtraction:
                # For subtraction, carry = NOT borrow
                # Borrow occurs when result > operand (unsigned)
                self._carry_out = result >= 0x80000000  # borrow detected
                if not self._carry_out:
                    self.value |= self.C_FLAG
                else:
                    self.value &= ~self.C_FLAG
            else:
                # For addition, carry = overflow beyond 32 bits
                self._carry_out = result >= 0x100000000
                if self._carry_out:
                    self.value |= self.C_FLAG
                else:
                    self.value &= ~self.C_FLAG

        # Set V flag (signed overflow)
        # Overflow occurs when adding two positives gives negative, or two negatives gives positive
        if not is_subtraction:
            # Addition: overflow if operands have same sign but result has different sign
            if result >= -2147483648 and result <= 2147483647:
                pass  # result fits in signed 32-bit
        else:
            # Subtraction: overflow if operands have different signs and result sign != minuend
            pass

    def set_flags_from_value(self, value, instruction_type="MOV"):
        """
        Set CPSR flags for a given value (used by MOV, MOVN, etc.)

        For MOV instructions:
        - N and Z flags are set from the result
        - C and V flags are NOT updated (per ARM architecture spec)
        """
        value = value & 0xFFFFFFFF

        # Clear flag bits
        self.value &= ~(self.N_FLAG | self.Z_FLAG | self.C_FLAG | self.V_FLAG)

        # Set N flag
        if value & 0x80000000:
            self.value |= self.N_FLAG

        # Set Z flag
        if value == 0:
            self.value |= self.Z_FLAG

        # C and V flags are NOT affected by MOV instructions

    def save_to_spsr(self):
        """Save current CPSR to SPSR (called before mode change)"""
        return self.value & 0xFFFFFFFF  # Don't save T bit to SPSR

    def restore_from_spsr(self, spsr_value):
        """Restore CPSR from SPSR (called after exception return)"""
        self.value = (spsr_value & 0xFFFFFFFF) | (self.value & self.T_FLAG)

    def set_condition(self, condition, n, z, c, v):
        """Set condition flags based on N, Z, C, V values"""
        if n:
            self.value |= self.N_FLAG
        else:
            self.value &= ~self.N_FLAG

        if z:
            self.value |= self.Z_FLAG
        else:
            self.value &= ~self.Z_FLAG

        if c:
            self.value |= self.C_FLAG
        else:
            self.value &= ~self.C_FLAG

        if v:
            self.value |= self.V_FLAG
        else:
            self.value &= ~self.V_FLAG

    def check_condition(self, condition):
        """
        Check if a condition code is met.

        Args:
            condition: Condition code string (e.g., 'EQ', 'NE', 'GT', 'AL')

        Returns:
            True if condition is met, False otherwise
        """
        if condition == "AL":
            return True

        n = self.n
        z = self.z
        c = self.c
        v = self.v

        # Note: For unsigned comparisons, we use the unsigned interpretation of C flag
        # The C flag from subtraction represents borrow (inverted)
        # So for unsigned comparisons after subtraction, we need to invert C

        cond_map = {
            "EQ": z,       # Equal
            "NE": not z,   # Not equal
            "CS": c,       # Unsigned higher or same (carry set)
            "HS": c,       # Unsigned higher or same (carry set)
            "CC": not c,   # Unsigned lower (carry clear)
            "LO": not c,   # Unsigned lower (carry clear)
            "MI": n,       # Minus (negative)
            "PL": not n,   # Plus (positive or zero)
            "VS": v,       # Overflow
            "VC": not v,   # No overflow
            "HI": c and not z,  # Unsigned higher
            "LS": not c or z,     # Unsigned lower or same
            "GE": n == v,  # Greater or equal (signed)
            "LT": n != v,  # Less than (signed)
            "GT": not z and (n == v),  # Greater than (signed)
            "LE": z or (n != v),     # Less or equal (signed)
        }

        return cond_map.get(condition, False)

    def __repr__(self):
        return (f"CPSR(N={self.n}, Z={self.z}, C={self.c}, V={self.v}, "
                f"T={self.t}, M={self.mode:#04x})")


class RegisterFile:
    """
    ARM Register File

    Implements the ARM register model:
    - R0-R15: General purpose registers (32-bit each)
    - CPSR: Current Program Status Register
    - SPSR: Saved Program Status Register (per exception mode)

    Special registers:
    - R13 (SP): Stack Pointer
    - R14 (LR): Link Register
    - R15 (PC): Program Counter
    """

    def __init__(self):
        # General purpose registers R0-R15 (32-bit)
        self.regs = [0] * 16

        # CPSR and SPSR
        self.cpsr = CPSR()

        # SPSR per mode (simplified: just store one for demo)
        self.spsr = {}
        for mode_name in ["USER", "FIQ", "IRQ", "SVC", "ABT", "UND", "SYS"]:
            self.spsr[mode_name] = 0

        # Banked registers for FIQ mode (R8_fiq-R14_fiq)
        self.fiq_regs = [0] * 7

        # Additional registers (not in R0-R15)
        self.spsr_banked = {}

    def read_reg(self, reg_num):
        """Read a general-purpose register (R0-R15)"""
        if 0 <= reg_num <= 15:
            return self.regs[reg_num]
        raise IndexError(f"Register R{reg_num} out of range (R0-R15)")

    def write_reg(self, reg_num, value):
        """Write to a general-purpose register (R0-R15)"""
        if 0 <= reg_num <= 15:
            self.regs[reg_num] = value & 0xFFFFFFFF
        else:
            raise IndexError(f"Register R{reg_num} out of range (R0-R15)")

    def write_reg_signed(self, reg_num, value):
        """Write signed value to register (for sign extension)"""
        self.write_reg(reg_num, value)

    def get_sp(self):
        """Get the stack pointer (R13)"""
        return self.regs[13]

    def set_sp(self, value):
        """Set the stack pointer (R13)"""
        self.write_reg(13, value)

    def get_lr(self):
        """Get the link register (R14)"""
        return self.regs[14]

    def set_lr(self, value):
        """Set the link register (R14)"""
        self.write_reg(14, value)

    def get_pc(self):
        """Get the program counter (R15)"""
        return self.regs[15]

    def set_pc(self, value):
        """Set the program counter (R15)"""
        self.write_reg(15, value)

    def set_pc_thumb(self, value):
        """Set PC for Thumb mode (address must be 2-aligned)"""
        self.set_pc(value | 1)  # Set thumb bit

    def get_pc_aligned(self):
        """Get PC aligned to instruction boundary"""
        pc = self.get_pc()
        if self.cpsr.t:
            return pc & ~0x1  # Thumb: 2-byte aligned
        return pc & ~0x3  # ARM: 4-byte aligned

    def save_spsr(self, mode="SVC"):
        """Save CPSR to SPSR before mode change"""
        self.spsr[mode] = self.cpsr.save_to_spsr()

    def restore_spsr(self, mode="SVC"):
        """Restore CPSR from SPSR after exception return"""
        if mode in self.spsr:
            self.cpsr.restore_from_spsr(self.spsr[mode])

    def dump(self):
        """Dump register state for debugging"""
        lines = ["=== ARM Register State ==="]
        for i in range(16):
            lines.append(f"  R{i:2d}: 0x{self.regs[i]:08X} ({self.regs[i]:10d})")
        lines.append(f"  SP : 0x{self.regs[13]:08X}")
        lines.append(f"  LR : 0x{self.regs[14]:08X}")
        lines.append(f"  PC : 0x{self.regs[15]:08X}")
        lines.append(f"  CPSR: {self.cpsr}")
        return "\n".join(lines)

    def __repr__(self):
        return self.dump()
