"""
Thumb Mode Support Module
==========================

Implements basic Thumb-1 instruction support.

ARM Architecture Background:
Thumb is a 16-bit instruction encoding mode that reduces code size by ~30%
compared to 32-bit ARM instructions.

Key Thumb features:
- 16-bit instruction width (compressed)
- Limited register set (R0-R7)
- No conditional execution (but IT blocks in Thumb-2)
- Simpler addressing modes
- Fixed-length instructions (no variable-length like x86)

Common Thumb instructions:
- ADD, SUB, MOV, CMP, AND, XOR
- LDR, STR (PC-relative)
- PUSH, POP
- B (branch)
- BX (branch and exchange)

The Thumb encoding is fundamentally different from ARM encoding.
Instructions are 16 bits and use different bit layouts.
"""


class ThumbInstruction:
    """Represents a decoded Thumb instruction"""

    # Instruction types
    DATA_PROCESSING = "THUMB_DATA"
    LOAD_STORE = "THUMB_LOAD_STORE"
    SPECIAL = "THUMB_SPECIAL"
    LONG_BRANCH = "THUMB_LONG_BRANCH"
    UNDEFINED = "THUMB_UNDEFINED"

    def __init__(self, instr_type, mnemonic="", **kwargs):
        self.type = instr_type
        self.mnemonic = mnemonic
        self._kwargs = kwargs

    @property
    def rd(self):
        return self._kwargs.get('rd')

    @property
    def rn(self):
        return self._kwargs.get('rn')

    @property
    def rm(self):
        return self._kwargs.get('rm')

    @property
    def operand2(self):
        return self._kwargs.get('operand2', 0)

    @property
    def target(self):
        return self._kwargs.get('target', 0)

    @property
    def register_list(self):
        return self._kwargs.get('register_list', 0)

    @property
    def sp_offset(self):
        return self._kwargs.get('sp_offset', 0)

    def __repr__(self):
        return f"ThumbInstr({self.mnemonic}, {self._kwargs})"


class ThumbDecoder:
    """
    Thumb-1 instruction decoder

    Decodes 16-bit Thumb instructions into ThumbInstruction objects.
    """

    def __init__(self):
        pass

    def decode(self, thumb_instr):
        """
        Decode a 16-bit Thumb instruction.

        Args:
            thumb_instr: 16-bit integer representing the Thumb instruction

        Returns:
            ThumbInstruction object or None if undefined
        """
        # Check for 32-bit instruction (high bits pattern)
        if (thumb_instr >> 11) == 0xE:
            # This is the high word of a 32-bit Thumb instruction
            # For simplicity, handle common cases
            return self._decode_32bit_thumb(thumb_instr)

        # 16-bit instruction decoding
        op = (thumb_instr >> 10) & 0x1E  # Upper bits for opcode classification

        if op < 0x10:
            # ADD/SUB/MOV/CMP/AND family (encoding group 0-7)
            return self._decode_data_processing(thumb_instr)
        elif op < 0x18:
            # LDR/STR (PC-relative and register offset)
            return self._decode_load_store(thumb_instr)
        elif op < 0x1C:
            # Special instructions (PUSH, POP, etc.)
            return self._decode_special(thumb_instr)
        elif op < 0x1E:
            # Long branch (B with 8-bit immediate)
            return self._decode_long_branch(thumb_instr)
        else:
            # BX, NOP, and other special
            return self._decode_special_instructions(thumb_instr)

    def _decode_data_processing(self, instr):
        """Decode data processing instructions (ADD, SUB, MOV, CMP, AND, etc.)"""
        # Format: |op|0|0|Rn|Rm| Rd |imm3|
        # op[14:12]: operation class
        # Rn[9:7]: source register
        # Rm[6:4]: source register
        # Rd[2:0]: destination register
        # imm3[2:0]: immediate value

        op = (instr >> 11) & 0x7
        rn = (instr >> 8) & 0x7
        rm = (instr >> 5) & 0x7
        rd = instr & 0x7
        imm3 = (instr >> 6) & 0x7

        # Determine operation
        if op == 0x0:
            # ADD (Rn + Rm or Rn + imm3)
            if rm == 0 and rn == 0:
                # ADD Rd, Rp, Rn (register shift)
                mnemonic = "ADD"
                return ThumbInstruction(
                    ThumbInstruction.DATA_PROCESSING, mnemonic,
                    rd=rd, rn=rn, rm=rm, operand2=0
                )
            else:
                # ADD Rd, Rn, Rm
                mnemonic = "ADD"
                return ThumbInstruction(
                    ThumbInstruction.DATA_PROCESSING, mnemonic,
                    rd=rd, rn=rn, operand2=rm
                )
        elif op == 0x1:
            # CMP (Rn - imm3)
            mnemonic = "CMP"
            return ThumbInstruction(
                ThumbInstruction.DATA_PROCESSING, mnemonic,
                rd=0, rn=rn, operand2=imm3
            )
        elif op == 0x2:
            # ADD (Rn + imm3)
            mnemonic = "ADD"
            return ThumbInstruction(
                ThumbInstruction.DATA_PROCESSING, mnemonic,
                rd=rd, rn=rn, operand2=imm3
            )
        elif op == 0x3:
            # SUB (Rn - imm3)
            mnemonic = "SUB"
            return ThumbInstruction(
                ThumbInstruction.DATA_PROCESSING, mnemonic,
                rd=rd, rn=rn, operand2=imm3
            )
        elif op == 0x4:
            # ADD (Rd + Rn + Rm)
            mnemonic = "ADD"
            return ThumbInstruction(
                ThumbInstruction.DATA_PROCESSING, mnemonic,
                rd=rd, rn=rn, rm=rm, operand2=0
            )
        elif op == 0x5:
            # MOV Rd, Rn
            mnemonic = "MOV"
            return ThumbInstruction(
                ThumbInstruction.DATA_PROCESSING, mnemonic,
                rd=rd, rn=rn, operand2=0
            )
        elif op == 0x6:
            # CMP (Rn - imm3)
            mnemonic = "CMP"
            return ThumbInstruction(
                ThumbInstruction.DATA_PROCESSING, mnemonic,
                rd=0, rn=rn, operand2=imm3
            )
        elif op == 0x7:
            # ADD (Rn + imm3)
            mnemonic = "ADD"
            return ThumbInstruction(
                ThumbInstruction.DATA_PROCESSING, mnemonic,
                rd=rd, rn=rn, operand2=imm3
            )

        return ThumbInstruction(ThumbInstruction.UNDEFINED, "UNKNOWN")

    def _decode_load_store(self, instr):
        """Decode load/store instructions"""
        op = (instr >> 11) & 0x7
        op2 = (instr >> 9) & 0x3
        rn = (instr >> 6) & 0x7
        rd = instr & 0x7
        imm8 = instr & 0xFF

        if op == 0x2:
            # STR Rd, [Rn, #imm8]
            return ThumbInstruction(
                ThumbInstruction.LOAD_STORE, "STR",
                rd=rd, rn=rn, operand2=imm8
            )
        elif op == 0x3:
            # LDR Rd, [Rn, #imm8]
            return ThumbInstruction(
                ThumbInstruction.LOAD_STORE, "LDR",
                rd=rd, rn=rn, operand2=imm8
            )
        elif op == 0x4:
            # STR Rd, [Rn, Rm]
            rm = (instr >> 3) & 0x7
            return ThumbInstruction(
                ThumbInstruction.LOAD_STORE, "STR",
                rd=rd, rn=rn, rm=rm
            )
        elif op == 0x5:
            # LDR Rd, [Rn, Rm]
            rm = (instr >> 3) & 0x7
            return ThumbInstruction(
                ThumbInstruction.LOAD_STORE, "LDR",
                rd=rd, rn=rn, rm=rm
            )
        elif op == 0x6:
            # STR Rd, [PC, #imm8]
            return ThumbInstruction(
                ThumbInstruction.LOAD_STORE, "STR",
                rd=rd, rn=15, operand2=imm8
            )
        elif op == 0x7:
            # LDR Rd, [PC, #imm8]
            return ThumbInstruction(
                ThumbInstruction.LOAD_STORE, "LDR",
                rd=rd, rn=15, operand2=imm8
            )

        return ThumbInstruction(ThumbInstruction.UNDEFINED, "UNKNOWN")

    def _decode_special(self, instr):
        """Decode special instructions (PUSH, POP, etc.)"""
        op = (instr >> 10) & 0x3

        if op == 0x0:
            # ADD Sp, Sp, #imm8
            imm8 = instr & 0xFF
            return ThumbInstruction(
                ThumbInstruction.SPECIAL, "ADD_SP",
                rn=13, operand2=imm8
            )
        elif op == 0x1:
            # SUB Sp, Sp, #imm8
            imm8 = instr & 0xFF
            return ThumbInstruction(
                ThumbInstruction.SPECIAL, "SUB_SP",
                rn=13, operand2=imm8
            )
        elif op == 0x2:
            # PUSH (store multiple)
            reg_list = instr & 0xFF
            return ThumbInstruction(
                ThumbInstruction.LOAD_STORE, "PUSH",
                register_list=reg_list
            )
        elif op == 0x3:
            # POP (load multiple)
            reg_list = instr & 0xFF
            return ThumbInstruction(
                ThumbInstruction.LOAD_STORE, "POP",
                register_list=reg_list
            )

        return ThumbInstruction(ThumbInstruction.UNDEFINED, "UNKNOWN")

    def _decode_long_branch(self, instr):
        """Decode long branch (B with 8-bit signed immediate)"""
        imm8 = instr & 0xFF
        # Sign-extend
        if imm8 & 0x80:
            imm8 = imm8 | 0xFFFFFF00
        # Branch offset is imm8 * 2 (Thumb instructions are 16-bit)
        target = imm8 << 1
        return ThumbInstruction(
            ThumbInstruction.LONG_BRANCH, "B",
            target=target
        )

    def _decode_special_instructions(self, instr):
        """Decode BX, NOP, and other special instructions"""
        if (instr >> 8) == 0x10:
            op2 = (instr >> 3) & 0x1F
            if op2 == 0x05:
                # BX Rd
                rd = instr & 0x7
                return ThumbInstruction(
                    ThumbInstruction.LONG_BRANCH, "BX",
                    rd=rd
                )
            elif op2 == 0x0D:
                # NOP (in some encodings)
                return ThumbInstruction(
                    ThumbInstruction.SPECIAL, "NOP"
                )
            elif (op2 & 0x1F) == 0x10:
                # NOP (alternative encoding)
                return ThumbInstruction(
                    ThumbInstruction.SPECIAL, "NOP"
                )

        # Default: UNDEFINED
        return ThumbInstruction(ThumbInstruction.UNDEFINED, "UNKNOWN")

    def _decode_32bit_thumb(self, high_word):
        """Decode 32-bit Thumb instruction (two 16-bit words)"""
        # For simplicity, handle common 32-bit Thumb instructions
        # BLX/BL encoding and other complex instructions

        # BLX/BL (32-bit): 1111 0xx1 xxx1 xxxx | 1111 xxxx xxxx xxxx
        if (high_word >> 11) == 0x18:
            # BL (Branch with Link)
            imm11_h = (high_word >> 1) & 0x7FF
            imm10 = (high_word >> 12) & 0x3FF
            j1 = (high_word >> 10) & 1
            j2 = (high_word >> 11) & 1
            # Combine: sign_extended(imm11) << 12 | j2 << 11 | j1 << 10 | imm10 << 1
            # For simplicity, just extract the offset
            offset = ((high_word & 0x7FF) << 12) | ((high_word >> 12) & 0x3FF) << 1
            return ThumbInstruction(
                ThumbInstruction.LONG_BRANCH, "BL",
                target=offset << 1
            )

        return ThumbInstruction(ThumbInstruction.UNDEFINED, "UNKNOWN")
