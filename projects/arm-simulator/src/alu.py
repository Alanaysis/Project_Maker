"""
ARM ALU (Arithmetic Logic Unit) Module
========================================

Implements the ARM ALU operations including:
- Arithmetic: ADD, SUB, ADC, SBC, RSB
- Logical: AND, ORR, EOR, BIC, MOV, MVN
- Shifts: LSL, LSR, ASR, ROR, RRX
- Compare: CMP, CMN
- Test: TST, TEQ

ARM Architecture Background:
The ALU is the core of ARM's data processing. Unlike CISC processors,
ARM's ALU only operates on registers (Load/Store architecture).
All results can optionally update the CPSR flags.

Key ARM ALU features:
1. Shifting is built into the operand encoding
2. Flags can be suppressed (S suffix)
3. Results are always 32-bit (with carry out for shifts)
"""


class ALU:
    """ARM Arithmetic Logic Unit"""

    def __init__(self):
        pass

    def add(self, operand1, operand2, carry=0, set_flags=True):
        """
        Addition: result = operand1 + operand2 + carry

        Returns:
            (result, n, z, c, v) - result and condition flags
        """
        # Use unsigned arithmetic for correct carry behavior
        result = (operand1 + operand2 + carry) & 0xFFFFFFFF

        # Compute flags
        n = bool(result & 0x80000000)
        z = (result == 0)
        c = result >= 0x100000000  # unsigned carry

        # Signed overflow: adding two positives gives negative, or two negatives gives positive
        # In unsigned: (operand1 ^ result) & (operand2 ^ result) & 0x80000000
        v = ((operand1 ^ result) & (operand2 ^ result) & 0x80000000) != 0

        if set_flags:
            return result, n, z, c, v
        return result

    def subtract(self, operand1, operand2, borrow=0, set_flags=True):
        """
        Subtraction: result = operand1 - operand2 - borrow

        Returns:
            (result, n, z, c, v) - result and condition flags
        """
        # Convert to unsigned for proper carry/borrow handling
        result = (operand1 - operand2 - borrow) & 0xFFFFFFFF

        # Compute flags
        n = bool(result & 0x80000000)
        z = (result == 0)

        # Carry in subtraction: C = NOT borrow
        # Borrow occurs when operand2 > operand1 (unsigned)
        c = (operand1 >= operand2 + borrow)

        # Signed overflow: subtracting negative from positive gives negative, or vice versa
        # In unsigned: (operand1 ^ operand2) & (operand1 ^ result) & 0x80000000
        v = ((operand1 ^ operand2) & (operand1 ^ result) & 0x80000000) != 0

        if set_flags:
            return result, n, z, c, v
        return result

    def logical_and(self, operand1, operand2, set_flags=True):
        """Bitwise AND"""
        result = operand1 & operand2
        n = bool(result & 0x80000000)
        z = (result == 0)
        c = 0  # C flag unchanged by AND
        v = 0  # V flag unchanged by AND

        if set_flags:
            return result, n, z, c, v
        return result

    def logical_orr(self, operand1, operand2, set_flags=True):
        """Bitwise ORR (OR Register)"""
        result = operand1 | operand2
        n = bool(result & 0x80000000)
        z = (result == 0)
        c = 0  # C flag unchanged by ORR
        v = 0  # V flag unchanged by ORR

        if set_flags:
            return result, n, z, c, v
        return result

    def logical_eor(self, operand1, operand2, set_flags=True):
        """Bitwise EOR (Exclusive OR)"""
        result = operand1 ^ operand2
        n = bool(result & 0x80000000)
        z = (result == 0)
        c = 0  # C flag unchanged by EOR
        v = 0  # V flag unchanged by EOR

        if set_flags:
            return result, n, z, c, v
        return result

    def logical_bic(self, operand1, operand2, set_flags=True):
        """
        Bit Clear: result = operand1 AND NOT operand2

        ARM specific: BIC clears bits in the first operand where
        the corresponding bit in the second operand is set.
        """
        result = operand1 & (~operand2) & 0xFFFFFFFF
        n = bool(result & 0x80000000)
        z = (result == 0)
        c = 0  # C flag unchanged by BIC
        v = 0  # V flag unchanged by BIC

        if set_flags:
            return result, n, z, c, v
        return result

    def move(self, operand, set_flags=True):
        """
        MOV: result = operand (move value to register)

        ARM behavior: MOV and MVN do NOT update C and V flags.
        Only N and Z flags are updated.
        """
        result = operand & 0xFFFFFFFF
        n = bool(result & 0x80000000)
        z = (result == 0)

        if set_flags:
            return result, n, z, 0, 0  # C and V unchanged
        return result

    def move_not(self, operand, set_flags=True):
        """
        MVN: result = NOT operand (move not)

        ARM behavior: MVN does NOT update C and V flags.
        """
        result = (~operand) & 0xFFFFFFFF
        n = bool(result & 0x80000000)
        z = (result == 0)

        if set_flags:
            return result, n, z, 0, 0  # C and V unchanged
        return result

    def compare(self, operand1, operand2):
        """
        CMP: Compare two values (internal: operand1 - operand2)

        Used to set flags for conditional execution.
        """
        return self.subtract(operand1, operand2, set_flags=True)

    def compare_negated(self, operand1, operand2):
        """
        CMN: Compare with negative (internal: operand1 + operand2)

        Used to set flags for conditional execution.
        Useful for testing if the sum of two registers would overflow.
        """
        return self.add(operand1, operand2, set_flags=True)

    def test(self, operand1, operand2):
        """
        TST: Test bits (internal: operand1 AND operand2)

        Sets flags based on the result of AND without storing the result.
        Used to test if specific bits are set.
        """
        result = operand1 & operand2
        n = bool(result & 0x80000000)
        z = (result == 0)
        return n, z  # C and V unchanged

    def test_equal(self, operand1, operand2):
        """
        TEQ: Test equality (internal: operand1 EOR operand2)

        Sets flags based on the result of EOR without storing the result.
        Used to test if two values are equal.
        """
        result = operand1 ^ operand2
        n = bool(result & 0x80000000)
        z = (result == 0)
        return n, z  # C and V unchanged

    def shift_left(self, operand, amount, set_flags=True):
        """Logical Shift Left: result = operand << amount"""
        if amount == 0:
            result = operand & 0xFFFFFFFF
            c_out = 0
        else:
            result = (operand << amount) & 0xFFFFFFFF
            c_out = (operand >> (32 - amount)) & 0x1
        n = bool(result & 0x80000000)
        z = (result == 0)
        if set_flags:
            return result, n, z, c_out, 0
        return result, c_out

    def shift_right_logical(self, operand, amount, set_flags=True):
        """Logical Shift Right: result = operand >> amount"""
        if amount == 0:
            result = operand & 0xFFFFFFFF
            c_out = 0
        else:
            result = (operand >> amount) & 0xFFFFFFFF
            c_out = (operand >> (amount - 1)) & 0x1
        n = bool(result & 0x80000000)
        z = (result == 0)
        if set_flags:
            return result, n, z, c_out, 0
        return result, c_out

    def shift_right_arithmetic(self, operand, amount, set_flags=True):
        """
        Arithmetic Shift Right: result = operand >> amount

        Preserves the sign bit (MSB). For signed numbers.
        """
        operand = operand & 0xFFFFFFFF
        # Convert to signed for proper sign extension
        if operand & 0x80000000:
            operand_signed = -(0x100000000 - operand)
        else:
            operand_signed = operand

        if amount == 0:
            result = operand_signed & 0xFFFFFFFF
            c_out = 0
        else:
            result = operand_signed >> amount
            result = result & 0xFFFFFFFF
            # C flag = last bit shifted out
            c_out = (operand >> (amount - 1)) & 0x1

        n = bool(result & 0x80000000)
        z = (result == 0)
        if set_flags:
            return result, n, z, c_out, 0
        return result, c_out

    def rotate_right(self, operand, amount):
        """
        Rotate Right: result = operand rotated right by amount bits

        For amount > 0 and <= 32.
        The last bit rotated out becomes the carry flag.
        """
        if amount == 0:
            amount = 32
        operand = operand & 0xFFFFFFFF
        result = ((operand >> amount) | (operand << (32 - amount))) & 0xFFFFFFFF
        c_out = (operand >> (amount - 1)) & 0x1
        return result, c_out

    def multiply(self, operand1, operand2):
        """
        Multiply: result = operand1 * operand2

        ARM MUL: 32-bit x 32-bit -> 32-bit result.
        Only the lower 32 bits are stored.
        """
        # Use Python's arbitrary precision and truncate
        result = (operand1 * operand2) & 0xFFFFFFFF
        return result

    def multiply_accumulate(self, operand1, operand2, addend):
        """
        Multiply and Accumulate (MLA): result = operand1 * operand2 + addend

        ARM MLA: 32-bit x 32-bit -> 32-bit result (with 32-bit addend).
        """
        result = ((operand1 * operand2) + addend) & 0xFFFFFFFF
        return result

    def unsigned_multiply_long(self, operand1, operand2):
        """
        Unsigned Multiply Long: result = operand1 * operand2 (64-bit result)

        Returns:
            (low32, high32) - 64-bit result split into two 32-bit parts
        """
        full = (operand1 & 0xFFFFFFFF) * (operand2 & 0xFFFFFFFF)
        low = full & 0xFFFFFFFF
        high = (full >> 32) & 0xFFFFFFFF
        return low, high

    def unsigned_multiply_long_accumulate(self, operand1, operand2, high_in, low_in):
        """
        Unsigned Multiply Long Accumulate: result = (high_in << 32 | low_in) + operand1 * operand2

        Returns:
            (low32, high32) - 64-bit result
        """
        full = ((high_in << 32) | low_in) + ((operand1 & 0xFFFFFFFF) * (operand2 & 0xFFFFFFFF))
        low = full & 0xFFFFFFFF
        high = (full >> 32) & 0xFFFFFFFF
        return low, high
