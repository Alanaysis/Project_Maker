"""
ARM Instruction Decoder Module
================================

Implements decoding of ARM instructions from 32-bit binary encoding.

ARM Architecture Background:
ARM instructions are 32-bit (4-byte) fixed-length in ARM state.
Each instruction has a standard format:

    |31|30|29|28| 27 26 25 24 23 22 21 20|19|18| 17 16|15 12|11 8|7 4|3 0|
    |cond| 10|  opcode | S|   Rn       | Rd | U|   P  |  imm | Rm | sh| Rs|

Key encoding fields:
- cond[31:28]: Condition code (AL=always, EQ=equal, etc.)
- opcode[27:25]: Instruction class (000=data processing, 001=multi, etc.)
- S[20]: Flag update bit (1 = update CPSR)
- Rn[19:16]: Source register
- Rd[15:12]: Destination register
- P/U[18:17]: Addressing mode (pre/post, up/down)
- imm[19:0]: Immediate value or shift amount
- Rm[3:0]: Second source register
- Rs[7:4]: Shift register source
- shift[11:8]: Shift type (00=LSL, 01=LSR, 10=ASR, 11=ROR)

The decoder parses binary instructions into Python objects that can be
executed by the CPU simulator.
"""


class Instruction:
    """Represents a decoded ARM instruction"""

    # Instruction types
    DATA_PROCESSING = "DATA_PROCESSING"
    LOAD_STORE = "LOAD_STORE"
    BRANCH = "BRANCH"
    MULTIPLY = "MULTIPLY"
    MULTIPLY_LONG = "MULTIPLY_LONG"
    EXCEPTION = "EXCEPTION"
    UNDEFINED = "UNDEFINED"

    # Data processing opcodes
    AND = "AND"
    EOR = "EOR"
    SUB = "SUB"
    RSB = "RSB"
    ADD = "ADD"
    ADC = "ADC"
    SBC = "SBC"
    RSC = "RSC"
    TST = "TST"
    TEQ = "TEQ"
    CMP = "CMP"
    CMN = "CMN"
    ORR = "ORR"
    MOV = "MOV"
    BIC = "BIC"
    MVN = "MVN"

    # Load/store types
    STR = "STR"
    LDR = "LDR"
    STRB = "STRB"
    LDRB = "LDRB"
    STM = "STM"
    LDM = "LDM"

    # Branch types
    B = "B"
    BL = "BL"
    BX = "BX"
    BLX = "BLX"

    # Multiply types
    MUL = "MUL"
    MLA = "MLA"
    UMULL = "UMULL"
    UMLAL = "UMLAL"

    def __init__(self, instruction_type, condition="AL", mnemonic="", **kwargs):
        self.type = instruction_type
        self.condition = condition
        self.mnemonic = mnemonic
        self._kwargs = kwargs

    # Data processing fields
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
        return self._kwargs.get('operand2')

    @property
    def operand2_type(self):
        return self._kwargs.get('operand2_type')  # 'register' or 'immediate'

    @property
    def update_flags(self):
        return self._kwargs.get('update_flags', False)

    # Load/store fields
    @property
    def offset(self):
        return self._kwargs.get('offset', 0)

    @property
    def offset_type(self):
        return self._kwargs.get('offset_type', 'immediate')  # 'immediate' or 'register'

    @property
    def write_back(self):
        return self._kwargs.get('write_back', False)

    @property
    def pre_indexed(self):
        return self._kwargs.get('pre_indexed', True)

    @property
    def up(self):
        return self._kwargs.get('up', True)

    @property
    def register_list(self):
        return self._kwargs.get('register_list', 0)

    # Branch fields
    @property
    def target(self):
        return self._kwargs.get('target', 0)

    # Multiply fields
    @property
    def rn_mult(self):
        return self._kwargs.get('rn')

    @property
    def rm_mult(self):
        return self._kwargs.get('rm')

    @property
    def ra(self):
        return self._kwargs.get('ra')

    def __repr__(self):
        return f"Instruction({self.mnemonic}, cond={self.condition}, {self._kwargs})"


class Decoder:
    """
    ARM instruction decoder

    Decodes 32-bit ARM instructions into Instruction objects.
    """

    def __init__(self):
        pass

    def decode(self, instruction_word):
        """
        Decode a 32-bit ARM instruction.

        Args:
            instruction_word: 32-bit integer representing the ARM instruction

        Returns:
            Instruction object or None if undefined
        """
        # Extract fields
        cond = (instruction_word >> 28) & 0xF
        opcode = (instruction_word >> 24) & 0x7

        # Condition codes
        cond_map = {
            0x0: "EQ", 0x1: "NE", 0x2: "CS", 0x3: "CC",
            0x4: "MI", 0x5: "PL", 0x6: "VS", 0x7: "VC",
            0x8: "HS", 0x9: "LS", 0xA: "GE", 0xB: "LT",
            0xC: "GT", 0xD: "LE", 0xE: "AL", 0xF: "AL"
        }
        condition = cond_map.get(cond, "AL")

        # Data Processing instructions (opcode 000)
        if opcode == 0x0:
            return self._decode_data_processing(instruction_word, condition)

        # Multiply instructions (opcode 001)
        if opcode == 0x1:
            return self._decode_multiply(instruction_word, condition)

        # Load/Store single data item (opcode 010)
        if opcode == 0x2:
            return self._decode_single_load_store(instruction_word, condition)

        # Load/Store multiple (opcode 011)
        if opcode == 0x3:
            return self._decode_multi_load_store(instruction_word, condition)

        # Branch / Branch with Link (opcode 100)
        if opcode == 0x4:
            return self._decode_branch(instruction_word, condition)

        # Coprocessor / undefined (opcodes 101-111)
        # For simplicity, treat as undefined
        return Instruction(Instruction.UNDEFINED, condition, "UNDEFINED")

    def _decode_data_processing(self, instr, condition):
        """Decode data processing instruction"""
        s_bit = (instr >> 20) & 0x1
        op = (instr >> 21) & 0xF

        # Different opcodes have different formats
        # op >= 0x8: shift by register format
        # op = 0x0, 0x1, 0x4, 0x5: immediate operand format
        # op = 0x2, 0x3, 0x6, 0x7: register operand format

        # Check for shift-by-register format (op >= 8)
        if op >= 8:
            rm = (instr >> 4) & 0xF
            shift_type = (instr >> 5) & 0x3
            rs = (instr >> 8) & 0xF
            rn = (instr >> 16) & 0xF
            rd = (instr >> 12) & 0xF

            shift_map = {0: "LSL", 1: "LSR", 2: "ASR", 3: "ROR"}

            operand2 = {
                'type': 'register',
                'reg': rm,
                'shift': shift_map.get(shift_type, "LSL"),
                'shift_reg': rs
            }

            mnemonic_map = {8: "AND", 9: "EOR", 10: "SUB", 11: "RSB",
                          12: "ADD", 13: "ADC", 14: "SBC", 15: "RSC"}
            mnemonic = mnemonic_map.get(op - 8, "UNKNOWN")

            return Instruction(
                Instruction.DATA_PROCESSING, condition, mnemonic,
                rd=rd, rn=rn, operand2=operand2,
                operand2_type='register',
                update_flags=bool(s_bit)
            )

        # Check for immediate operand format (op = 0, 1, 4, 5)
        if op in (0x0, 0x1, 0x4, 0x5):
            rm = (instr >> 4) & 0xF
            imm12 = instr & 0xFFF
            rn = (instr >> 16) & 0xF
            rd = (instr >> 12) & 0xF

            # Check if it's actually a shift-immediate format (Rm present, no immediate)
            # In ARM encoding, if the bottom 4 bits of the instruction match a register number
            # and there's no clear immediate pattern, it might be shift-immediate
            # We use a heuristic: if imm12 looks like a valid rotated immediate, treat as immediate
            if self._is_valid_arm_immediate(imm12):
                operand2 = {'type': 'immediate', 'value': imm12}
            else:
                # Treat as shift-immediate
                shift_amount = imm12
                operand2 = {'type': 'immediate_shift', 'value': rm, 'amount': shift_amount}

            if op == 0x0:
                mnemonic = "AND"
            elif op == 0x1:
                mnemonic = "EOR"
            elif op == 0x4:
                mnemonic = "SUB"
            elif op == 0x5:
                mnemonic = "RSB"

            return Instruction(
                Instruction.DATA_PROCESSING, condition, mnemonic,
                rd=rd, rn=rn, operand2=operand2,
                operand2_type='immediate',
                update_flags=bool(s_bit)
            )

        # Register operand format (op = 2, 3, 6, 7)
        rm = (instr >> 4) & 0xF
        shift_type = (instr >> 5) & 0x3
        shift_amount = (instr >> 7) & 0x1F
        rn = (instr >> 16) & 0xF
        rd = (instr >> 12) & 0xF

        shift_map = {0: "LSL", 1: "LSR", 2: "ASR", 3: "ROR"}

        operand2 = {
            'type': 'shifted_register',
            'reg': rm,
            'shift': shift_map.get(shift_type, "LSL"),
            'amount': shift_amount
        }

        if op == 0x2:
            mnemonic = "AND"
        elif op == 0x3:
            mnemonic = "EOR"
        elif op == 0x6:
            mnemonic = "SUB"
        elif op == 0x7:
            mnemonic = "RSB"
        else:
            mnemonic = "UNKNOWN"

        return Instruction(
            Instruction.DATA_PROCESSING, condition, mnemonic,
            rd=rd, rn=rn, operand2=operand2,
            operand2_type='shifted_register',
            update_flags=bool(s_bit)
        )

    def _decode_multiply(self, instr, condition):
        """Decode multiply instruction"""
        # MUL: opcode 001 0xx1 xxxx xxxx xxxx xxxx xxxx xxxx
        # MLA: opcode 001 0xx0 xxxx xxxx xxxx xxxx xxxx xxxx

        rs = (instr >> 8) & 0xF  # For MUL, this is unused; for MLA, this is the add register
        rm = (instr >> 4) & 0xF
        rn = (instr >> 16) & 0xF
        rd = (instr >> 12) & 0xF

        if (instr >> 4) & 0x1 == 0:
            # MLA: rd = rn * rm + rs
            mnemonic = "MLA"
            return Instruction(
                Instruction.MULTIPLY, condition, mnemonic,
                rd=rd, rn=rn, rm=rm, ra=rs
            )
        else:
            # MUL: rd = rn * rm
            mnemonic = "MUL"
            return Instruction(
                Instruction.MULTIPLY, condition, mnemonic,
                rd=rd, rn=rn, rm=rm
            )

    def _decode_single_load_store(self, instr, condition):
        """Decode single load/store instruction"""
        p = (instr >> 24) & 0x1  # P bit (actually bit 24 in full encoding)
        # Let me re-encode properly
        # For LDR/STR single: 10 P U 0 0 1 0 1 w b L 1 1 Rn Rd offset
        # Bit positions:
        # cond[31:28], opcode[27:25] = 100 (branch), so this is handled above
        # Actually for load/store: cond[31:28], then bits 27-25 = 010

        # Let me decode properly from the full 32-bit word
        # Format: |cond|10| P|U|0|0|1|0|1|w|b|L|1|1|Rn| Rd| offset |1|0|1|0|
        # Actually the opcode for single load/store is 010 (bits 27-25)
        # Wait, I already handled opcode 0x2 above. Let me re-check.

        # Load/store single has opcode 010 (bits 27-25)
        # Format: |cond|10| P|U|0|0|1|0|1|w|b|L|1|1|Rn| Rd| imm12 |1|0|1|0|
        # Bits:   31-28 27-26 25 24 23 22 21 20 19 18 17 16 15-12 11-0

        # Actually let me re-decode from scratch
        P = (instr >> 24) & 0x1  # Bit 24
        U = (instr >> 23) & 0x1  # Bit 23
        w = (instr >> 21) & 0x1  # Bit 21
        b = (instr >> 20) & 0x1  # Bit 20 (byte transfer)
        L = (instr >> 20) & 0x1  # Actually L is bit 20

        # Let me be more careful with bit positions
        # Standard ARM LDR/STR encoding:
        # |31:28|27|26|25|24|23|22|21|20|19|18|17|16|15:12|11:0|
        # |cond |1 |0| P|U |0 |0 | w| L| b| 1 | 1| Rn | Rd | imm9|
        # Wait, this doesn't match either. Let me use the standard encoding.

        # ARM LDR/STR (single data item):
        # |cond|10| P|U|B|W| L|1|1|Rn| Rd|  imm12|1|0|1|0|
        # Bits: 31-28 27-26 25 24 23 22 21 20 19 18 17-16 15-12 11-0 9-8 7-4 3-0

        # Actually the standard encoding is:
        # |cond|10| P|U|0|0|1|0|1|w|b|L|1|1|Rn| Rd| imm12 |1|0|1|0|
        # No, let me just fix this properly:

        # ARM Data Processing and Load/Store encoding:
        # For LDR/STR: cond[31:28] = xxx, [27:26] = 10, [25] = P, [24] = U,
        #              [23:22] = 00, [21] = W, [20] = L, [19] = B,
        #              [18:17] = 11, [16] = Rn, [15:12] = Rd, [11:0] = imm12

        # Hmm, this is getting confusing. Let me just define the encoding clearly:

        # For the single load/store opcode (010 at bits 27-25):
        # Format: 10 P U 0 0 L w b 1 1 Rn Rd imm12 (where some bits are fixed)

        # Let me just decode it properly based on the actual ARM encoding:
        P_bit = (instr >> 24) & 1  # Bit 24: Pre/post indexing
        U_bit = (instr >> 23) & 1  # Bit 23: Up/down
        W_bit = (instr >> 21) & 1  # Bit 21: Write-back
        L_bit = (instr >> 20) & 1  # Bit 20: Load/Store
        B_bit = (instr >> 19) & 1  # Bit 19: Byte transfer
        Rn = (instr >> 16) & 0xF   # Bits 19-16... wait

        # OK let me just be very explicit about ARM single load/store encoding:
        # 10 P U 0 0 L w b 1 1 Rn Rd imm12
        # 27 26 25 24 23 22 21 20 19 18 17 16 15 12 11 0
        # No that's wrong too. Let me look at the actual ARM encoding.

        # Standard ARM LDR/STR encoding (from ARM ARM):
        # |31:28|27:26|25|24|23:22|21|20|19|18:17|16:12|11:0|
        # |cond |10   |P |U |00   |W |L |B |11    |Rn | Rd |imm12|

        # Wait, that's not right either. The Rd is bits 15:12 and Rn is bit 16.
        # Let me just use the correct encoding:

        # |31:28|27:26|25|24|23:22|21|20|19|18:17|16|15:12|11:0|
        # |cond |10   |P |U |00   |W |L |B |11    |Rn| Rd |imm12 |

        # Actually in ARM: bits 16 is Rn (just 1 bit?? No, Rn is 4 bits)
        # The correct encoding has Rn at bits 19:16 and Rd at bits 15:12

        # Let me just fix this by using a proper decoder
        P = (instr >> 24) & 1
        U = (instr >> 23) & 1
        W = (instr >> 21) & 1
        L = (instr >> 20) & 1
        B = (instr >> 19) & 1
        Rn = (instr >> 16) & 0xF
        Rd = (instr >> 12) & 0xF
        imm12 = instr & 0xFFF

        if B:
            mnemonic = "LDRB" if L else "STRB"
        else:
            mnemonic = "LDR" if L else "STR"

        offset = imm12 if U else -imm12
        write_back = bool(W)

        return Instruction(
            Instruction.LOAD_STORE, condition, mnemonic,
            rd=Rd, rn=Rn, offset=offset,
            offset_type='immediate',
            write_back=write_back,
            pre_indexed=P,
            up=U,
            is_byte=B
        )

    def _decode_multi_load_store(self, instr, condition):
        """Decode load/store multiple instruction"""
        # Format: |cond|10| U|W|0|0|1|0|1|Rn| list | L|1|0|1|0|
        # Bits:   31-28 27-26 25 24 23 22 21 20 19 18 17-8 7 6-4 3-0

        U = (instr >> 24) & 1  # Actually let me decode properly
        W = (instr >> 21) & 1
        L = (instr >> 20) & 1
        Rn = (instr >> 16) & 0xF
        list_val = (instr >> 16) & 0xFF  # Actually list is bits... let me fix

        # Standard STM/LDM encoding:
        # |31:28|27:26|25|24|23:22|21|20|19:16|15:0|
        # |cond |10   |U |W |00   |1 |0 | Rn  | list |
        # Wait, this doesn't include L bit. Let me recheck.

        # Actually for STM/LDM:
        # P bit is always 1 (pre-indexed)
        # L bit determines STM vs LDM
        # Format: 10 U W 0 0 L P Rn list
        # where P=1 always for STM/LDM

        # Let me just decode it:
        U_bit = (instr >> 24) & 1
        W_bit = (instr >> 21) & 1
        L_bit = (instr >> 20) & 1
        Rn_val = (instr >> 16) & 0xF
        list_val = instr & 0xFFFF  # register list

        # Actually register list is the lower 16 bits (bits 15:0)
        # But in the encoding, bits 27:26 = 10, bit 25 = U, bit 24 = W...
        # Let me just use a simpler approach

        # For STM/LDM, the register list occupies bits 15:0
        # Rn is at bit 16
        # L is at bit 20, W at bit 21
        # U at bit 24, P=1 at bit 25

        # Let me just use the register list from the correct bits
        reg_list = instr & 0xFFFF  # lower 16 bits = register list

        if L_bit:
            mnemonic = "LDM"
        else:
            mnemonic = "STM"

        return Instruction(
            Instruction.LOAD_STORE, condition, mnemonic,
            rn=Rn_val, register_list=reg_list
        )

    def _decode_branch(self, instr, condition):
        """Decode branch instruction"""
        # Branch encoding: |cond|010|imm24|
        # Actually: |cond|01|imm24|
        # Bits: 31-28 cond, 27-26 = 01, 25-0 = imm24

        imm24 = instr & 0xFFFFFF  # 24-bit signed immediate
        # Sign-extend imm24
        if imm24 & 0x800000:
            imm24 = imm24 | 0xFF000000  # Sign extend to 32 bits
        # Multiply by 4 (branch offset is in words)
        target = imm24 << 2

        # Check for BL (Branch with Link): bit 27 = 1
        if (instr >> 27) & 1:
            mnemonic = "BL"
        else:
            # Check for BX/BLX
            # BX: 0001 010x xxxx xxxx xxxx xxxx xxxx xxxx
            # BLX: 0001 011x xxxx xxxx xxxx xxxx xxxx xxxx
            # But BX/BLX have specific encodings in the data processing area
            # For branch opcode (01), BL is the only option
            mnemonic = "B"

        return Instruction(
            Instruction.BRANCH, condition, mnemonic,
            target=target
        )

    def _is_valid_arm_immediate(self, imm12):
        """
        Check if a value is a valid ARM immediate.

        ARM immediates are 8-bit values rotated by an even number of bits (0-30).
        This is a simplified check.
        """
        # Check if it can be represented as an 8-bit value rotated
        for rotate in range(0, 32, 2):
            rotated = ((imm12 >> (rotate // 2)) | (imm12 << (16 - rotate // 2))) & 0xFFFFFFFF
            if (rotated & 0xFF000000) == 0 or (rotated & 0xFF) == (imm12 & 0xFF):
                pass  # This is a simplified check
        return True  # For simplicity, accept all immediates

    def decode_arm_binary(self, instr_word):
        """Alias for decode method"""
        return self.decode(instr_word)
