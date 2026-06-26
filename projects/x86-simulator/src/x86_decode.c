#include "x86_decode.h"
#include <string.h>
#include <stdio.h>

/* ============================================================
 * x86_decode.c - x86 instruction decoder implementation
 *
 * x86 Variable-Length Instruction Encoding:
 *
 * The x86 instruction format is highly variable:
 *
 *   [Prefixes] Opcode [MOD/RM] [SIB] [Displacement] [Immediate]
 *
 * Prefixes (optional, up to 15):
 *   F0h: LOCK prefix (atomic operations)
 *   F2h: REPNE/REPNZ prefix
 *   F3h: REPE/REPZ prefix
 *   2Eh: CS segment override
 *   3Eh: DS segment override
 *   36h: SS segment override
 *   3Eh: ES segment override
 *   64h: FS segment override
 *   65h: GS segment override
 *   66h: Operand size override (16-bit in 32-bit mode)
 *   67h: Address size override (16-bit in 32-bit mode)
 *
 * Opcode (1-2 bytes):
 *   Most instructions: 1 byte
 *   Two-byte opcode: 0x0F followed by second byte
 *
 * MOD/RM (1 byte, if required):
 *   Specifies register or memory operand
 *
 * SIB (1 byte, if MOD/RM R/M field = 100b):
 *   Scale, Index, Base for complex addressing
 *
 * Displacement (0/1/2/4 bytes):
 *   Memory offset, signed
 *
 * Immediate (0/1/2/4 bytes):
 *   Constant operand value
 * ============================================================ */

/*
 * Decode one x86 instruction.
 *
 * This function parses the instruction stream and populates the
 * x86_instruction_t structure with all decoded fields.
 *
 * Returns X86_OK on success, X86_ERROR on failure.
 */
int x86_decode(x86_cpu_t *cpu, x86_instr_stream_t *stream,
               x86_instruction_t *instr) {
    memset(instr, 0, sizeof(x86_instruction_t));

    /* Default operand and address sizes based on mode */
    if (cpu->mode == MODE_REAL) {
        instr->operand_size = 2;  /* 16-bit in real mode */
        instr->addr_size    = 2;  /* 16-bit in real mode */
        instr->operand_bits = 16;
    } else {
        instr->operand_size = 4;  /* 32-bit in protected mode */
        instr->addr_size    = 4;  /* 32-bit in protected mode */
        instr->operand_bits = 32;
    }

    /* Step 1: Parse prefixes */
    while (1) {
        uint8_t prefix = x86_instr_read_byte(stream);
        if (prefix == 0x00) break; /* Invalid/no more prefixes */

        switch (prefix) {
            case 0xF0: /* LOCK */
                break;
            case 0xF2: /* REPNE */
                break;
            case 0xF3: /* REPE */
                break;
            case 0x2E: /* CS override */
            case 0x36: /* SS override */
            case 0x3E: /* DS override */
            case 0x26: /* ES override */
            case 0x64: /* FS override */
            case 0x65: /* GS override */
                instr->has_seg_override = 1;
                instr->seg_override = prefix;
                break;
            case 0x66: /* Operand size override */
                instr->operand_size = (instr->operand_size == 4) ? 2 : 4;
                instr->operand_bits = (instr->operand_size == 4) ? 32 : 16;
                break;
            case 0x67: /* Address size override */
                instr->addr_size = (instr->addr_size == 4) ? 2 : 4;
                break;
            default:
                /* Unknown prefix, treat as opcode start */
                stream->pos--; /* Put byte back */
                goto parse_opcode;
        }
    }

parse_opcode:
    /* Step 2: Read opcode */
    instr->opcode = x86_instr_read_byte(stream);

    /* Two-byte opcode prefix: 0x0F */
    if (instr->opcode == 0x0F) {
        instr->opcode = x86_instr_read_byte(stream) | 0x100;
    }

    /* Step 3: Determine if MOD/RM byte is needed */
    /* Instructions that need MOD/RM: most instructions with register/memory operands */
    int need_modrm = 0;

    /* Check if opcode is in the two-byte opcode table */
    uint8_t primary_opcode = (instr->opcode < 0x100) ? instr->opcode : 0;
    uint8_t secondary_opcode = (instr->opcode >= 0x100) ?
                                (uint8_t)(instr->opcode - 0x100) : 0;

    /* Primary opcode table: which opcodes need MOD/RM */
    if (instr->opcode < 0x100) {
        /* Group 1: ADD, OR, ADC, SBB, AND, SUB, XOR, CMP */
        if (primary_opcode >= 0x00 && primary_opcode <= 0x05) need_modrm = 1;
        /* PUSH, POP, MOV */
        else if (primary_opcode >= 0x50 && primary_opcode <= 0x57) need_modrm = 1;
        else if (primary_opcode == 0x58) need_modrm = 1;  /* POP reg */
        else if (primary_opcode == 0x88 || primary_opcode == 0x89) need_modrm = 1;
        else if (primary_opcode == 0x8A || primary_opcode == 0x8B) need_modrm = 1;
        else if (primary_opcode >= 0xC0 && primary_opcode <= 0xFF) need_modrm = 1;
        else if (primary_opcode == 0xA0 || primary_opcode == 0xA1) need_modrm = 1;
        else if (primary_opcode == 0xA2 || primary_opcode == 0xA3) need_modrm = 1;
        /* CMPXCHG */
        else if (primary_opcode == 0xA8 || primary_opcode == 0xA9) need_modrm = 1;
        /* TEST */
        else if (primary_opcode == 0xA8 || primary_opcode == 0xA9) need_modrm = 1;
        /* INC, DEC */
        else if (primary_opcode >= 0x40 && primary_opcode <= 0x45) need_modrm = 1;
        /* MOV AL/AX/mem */
        else if (primary_opcode == 0xB0 || primary_opcode == 0xB1) need_modrm = 0;
        else if (primary_opcode >= 0xB2 && primary_opcode <= 0xBF) need_modrm = 0;
        /* MOV r/m, imm */
        else if (primary_opcode >= 0xC6 && primary_opcode <= 0xC7) need_modrm = 1;
        /* MOV reg, imm */
        else if (primary_opcode >= 0xB0 && primary_opcode <= 0xBF) need_modrm = 0;
        /* MOVZX/MOVSX */
        else if (primary_opcode == 0xB6 || primary_opcode == 0xB7) need_modrm = 1;
        /* NOP through XCHG group */
        else if (primary_opcode == 0x90) need_modrm = 0; /* NOP */
        /* RET */
        else if (primary_opcode == 0xC2 || primary_opcode == 0xC3) need_modrm = 0;
        /* INT */
        else if (primary_opcode == 0xCD) need_modrm = 0;
        /* JMP */
        else if (primary_opcode == 0xE9 || primary_opcode == 0xEB) need_modrm = 0;
        /* CALL */
        else if (primary_opcode == 0xE8) need_modrm = 0;
        /* PUSH */
        else if (primary_opcode >= 0x60 && primary_opcode <= 0x6F) need_modrm = 0;
        /* LEA */
        else if (primary_opcode == 0x8D) need_modrm = 1;
        /* NOP through XCHG */
        else if (primary_opcode == 0x90) need_modrm = 0;
        /* INC/DEC reg (no modrm) */
        else if (primary_opcode >= 0x40 && primary_opcode <= 0x47) need_modrm = 0;
        /* PUSH reg (no modrm) */
        else if (primary_opcode >= 0x50 && primary_opcode <= 0x57) need_modrm = 0;
        /* POP reg (no modrm) */
        else if (primary_opcode >= 0x58 && primary_opcode <= 0x5F) need_modrm = 0;
        /* RET imm16 */
        else if (primary_opcode == 0xC2) need_modrm = 0;
        /* RET (no operand) */
        else if (primary_opcode == 0xC3) need_modrm = 0;
        /* INT imm8 */
        else if (primary_opcode == 0xCD) need_modrm = 0;
        /* INTO */
        else if (primary_opcode == 0xCE) need_modrm = 0;
        /* INT3 */
        else if (primary_opcode == 0xCC) need_modrm = 0;
        /* IRET */
        else if (primary_opcode == 0xCF) need_modrm = 0;
        /* AAM/AAD */
        else if (primary_opcode == 0xD4) need_modrm = 0;
        else if (primary_opcode == 0xD5) need_modrm = 0;
        /* SHL/SAR/SHR/ROL/ROR */
        else if (primary_opcode >= 0xD0 && primary_opcode <= 0xD3) need_modrm = 1;
        else if (primary_opcode == 0xD3) need_modrm = 1;
        /* SHL/SAR/SHR/ROL/ROR reg */
        else if (primary_opcode >= 0xC0 && primary_opcode <= 0xC1) need_modrm = 1;
        /* MOVSX/MOVZX with modrm */
        else if (primary_opcode == 0xB6 || primary_opcode == 0xB7) need_modrm = 1;
        /* SETcc */
        else if (primary_opcode >= 0x90 && primary_opcode <= 0x9F) need_modrm = 1;
        /* JMP rel16/32 or LEA */
        else if (primary_opcode == 0x8D) need_modrm = 1;
        /* MOV r16/m16, s16 */
        else if (primary_opcode == 0x8C) need_modrm = 1;
        /* MOV s16, r/m16 */
        else if (primary_opcode == 0x8E) need_modrm = 1;
        /* CMPSB/W */
        else if (primary_opcode == 0xA6 || primary_opcode == 0xA7) need_modrm = 0;
        /* SCASB/W */
        else if (primary_opcode == 0xAE || primary_opcode == 0xAF) need_modrm = 0;
        /* LODSB/W */
        else if (primary_opcode == 0xAC || primary_opcode == 0xAD) need_modrm = 0;
        /* STOSB/W */
        else if (primary_opcode == 0xAE || primary_opcode == 0xAF) need_modrm = 0;
        /* MOVSB/W */
        else if (primary_opcode == 0xA4 || primary_opcode == 0xA5) need_modrm = 0;
        /* CMPSW */
        else if (primary_opcode == 0xA7) need_modrm = 0;
        /* TEST */
        else if (primary_opcode == 0xF6 || primary_opcode == 0xF7) need_modrm = 1;
        /* DIV/IDIV */
        else if (primary_opcode == 0xF6 || primary_opcode == 0xF7) need_modrm = 1;
        /* IMUL */
        else if (primary_opcode == 0x0F && secondary_opcode == 0xAF) need_modrm = 1;
        /* SHLD/SHRD */
        else if (secondary_opcode == 0xA4 || secondary_opcode == 0xA5) need_modrm = 1;
        /* ARPL */
        else if (secondary_opcode == 0x00) need_modrm = 1;
        /* LGDT/LIDT */
        else if (secondary_opcode == 0x01) need_modrm = 1;
        /* LSL */
        else if (secondary_opcode == 0x02) need_modrm = 1;
        /* SYSCALL/SYSRET */
        else if (secondary_opcode == 0x05 || secondary_opcode == 0x07) need_modrm = 0;
        /* CLD/STC */
        else if (secondary_opcode == 0x18 || secondary_opcode == 0x19) need_modrm = 0;
        /* CMOVcc */
        else if (secondary_opcode >= 0x40 && secondary_opcode <= 0x4F) need_modrm = 1;
        /* PUSH/POP FS/GS */
        else if (secondary_opcode >= 0xA0 && secondary_opcode <= 0xA1) need_modrm = 0;
        /* BSF/BSR/LEA */
        else if (secondary_opcode == 0xBC || secondary_opcode == 0xBD) need_modrm = 1;
        /* PUSHA/POPAD */
        else if (secondary_opcode >= 0xB8 && secondary_opcode <= 0xBF) need_modrm = 0;
        /* BT/BTC/BTR/BTS */
        else if (secondary_opcode >= 0xA3 && secondary_opcode <= 0xA7) need_modrm = 1;
        /* MUL/IMUL/ADD/SUB/CMP/AND/OR/XOR/SBB/ADC */
        else if (primary_opcode >= 0x00 && primary_opcode <= 0x05) need_modrm = 1;
        else if (primary_opcode >= 0x20 && primary_opcode <= 0x25) need_modrm = 1;
        else if (primary_opcode >= 0x80 && primary_opcode <= 0x8F) need_modrm = 1;
        else if (primary_opcode >= 0xA0 && primary_opcode <= 0xA3) need_modrm = 1;
        /* Default: need modrm for most group instructions */
        else need_modrm = 0;
    }

    /* Two-byte opcode table */
    if (instr->opcode >= 0x100) {
        switch (secondary_opcode) {
            case 0x00: need_modrm = 1; break; /* ARPL */
            case 0x01: need_modrm = 1; break; /* LGDT/LIDT */
            case 0x02: need_modrm = 1; break; /* LSL */
            case 0x05: need_modrm = 0; break; /* SYSCALL */
            case 0x07: need_modrm = 0; break; /* SYSENTER */
            case 0x18: need_modrm = 0; break; /* CLFLUSH */
            case 0x19: need_modrm = 0; break; /* CLTS */
            case 0xA3: need_modrm = 1; break; /* BT */
            case 0xA4: need_modrm = 1; break; /* SHLD */
            case 0xA5: need_modrm = 1; break; /* SHRD */
            case 0xA7: need_modrm = 1; break; /* CMPXCHG */
            case 0xAF: need_modrm = 1; break; /* IMUL */
            case 0xB6: need_modrm = 1; break; /* MOVZX */
            case 0xB7: need_modrm = 1; break; /* MOVSX */
            case 0xBC: need_modrm = 1; break; /* BSF */
            case 0xBD: need_modrm = 1; break; /* BSR */
            default:   need_modrm = 1; break;  /* Default for most two-byte opcodes */
        }
    }

    instr->has_modrm = need_modrm;

    /* Step 4: Read MOD/RM byte if needed */
    if (need_modrm) {
        instr->modrm = x86_instr_read_byte(stream);
        x86_decode_modrm(cpu, instr, stream, instr->modrm);
    }

    /* Step 5: Read immediate operand if needed */
    /* This is simplified - actual x86 has complex rules for immediate sizes */
    uint8_t imm_size = 0;

    if (instr->opcode == 0xCD) {
        /* INT imm8 */
        imm_size = 1;
    } else if (instr->opcode == 0xC2) {
        /* RET imm16 */
        imm_size = 2;
    } else if (instr->opcode == 0xE9) {
        /* JMP rel16/32 */
        imm_size = instr->operand_size;
    } else if (instr->opcode == 0xEB) {
        /* JMP rel8 */
        imm_size = 1;
    } else if (instr->opcode == 0xE8) {
        /* CALL rel16/32 */
        imm_size = instr->operand_size;
    } else if (instr->opcode >= 0xB0 && instr->opcode <= 0xBF) {
        /* MOV reg, imm8/imm32 */
        imm_size = 1;
    } else if (instr->opcode == 0x6A) {
        /* PUSH imm8 */
        imm_size = 1;
    } else if (instr->opcode == 0x68) {
        /* PUSH imm16/imm32 */
        imm_size = instr->operand_size;
    } else if (instr->opcode == 0x6B) {
        /* IMUL imm8 */
        imm_size = 1;
    } else if (instr->opcode == 0x05 || instr->opcode == 0x01) {
        /* ADD/SUB with immediate */
        imm_size = instr->operand_size;
    } else if (instr->opcode == 0x83) {
        /* OP r/m, imm8 */
        imm_size = 1;
    } else if (instr->opcode == 0x80 || instr->opcode == 0x82 || instr->opcode == 0x81) {
        /* OP r/m, imm8/imm32 */
        imm_size = (instr->opcode == 0x80 || instr->opcode == 0x82) ? 1 :
                   (instr->opcode == 0x81 ? instr->operand_size : 0);
    } else if (instr->opcode == 0xC6) {
        /* MOV r/m, imm8 */
        imm_size = 1;
    } else if (instr->opcode == 0xC7) {
        /* MOV r/m, imm16/imm32 */
        imm_size = instr->operand_size;
    } else if (instr->opcode == 0xF6) {
        /* TEST/ DIV/IMUL with imm8 */
        imm_size = 1;
    } else if (instr->opcode == 0xF7) {
        /* TEST/ DIV/IMUL with imm16/imm32 */
        imm_size = instr->operand_size;
    } else if (instr->opcode == 0xA8) {
        /* TEST AL, imm8 */
        imm_size = 1;
    } else if (instr->opcode == 0xA9) {
        /* TEST AX/EAX, imm16/imm32 */
        imm_size = instr->operand_size;
    } else if (instr->opcode == 0x50) {
        /* PUSH reg - no immediate */
        imm_size = 0;
    } else if (instr->opcode == 0x90) {
        /* NOP */
        imm_size = 0;
    } else if (instr->opcode == 0xCC) {
        /* INT3 */
        imm_size = 0;
    } else if (instr->opcode == 0xCF) {
        /* IRET */
        imm_size = 0;
    } else if (instr->opcode == 0xC3) {
        /* RET */
        imm_size = 0;
    } else if (instr->opcode == 0x40) {
        /* INC EAX */
        imm_size = 0;
    } else if (instr->opcode == 0x0F) {
        /* Two-byte opcode - handle specific cases */
        switch (secondary_opcode) {
            case 0x82: imm_size = 1; break; /* JMP rel8 */
            default:   imm_size = 0; break;
        }
    }

    if (imm_size > 0) {
        instr->has_imm = imm_size;
        if (imm_size == 1) {
            instr->immediate = x86_instr_read_byte(stream);
        } else if (imm_size == 2) {
            instr->immediate = x86_instr_read_word(stream);
        } else {
            instr->immediate = x86_instr_read_dword(stream);
        }
    }

    return X86_OK;
}

/*
 * Decode the MOD/RM byte.
 *
 * MOD/RM format:
 *   Bits 7-6: MOD (mod addressing mode)
 *   Bits 5-3: REG (register field / opcode extension)
 *   Bits 2-0: R/M (register or memory addressing)
 */
void x86_decode_modrm(x86_cpu_t *cpu, x86_instruction_t *instr,
                       x86_instr_stream_t *stream, uint8_t modrm) {
    instr->modrm = modrm;
    instr->has_modrm = 1;

    uint8_t mod = (modrm >> 6) & 0x03;
    uint8_t rm  = modrm & 0x07;

    /* Determine displacement size based on MOD and R/M */
    if (mod == 0) {
        /* No displacement, unless R/M = 6 (in 32-bit mode) */
        if (instr->addr_size == 4 && rm == 6) {
            instr->has_disp = 4;
            instr->displacement = (int32_t)x86_instr_read_dword(stream);
        }
    } else if (mod == 1) {
        /* 8-bit displacement */
        instr->has_disp = 1;
        instr->displacement = (int8_t)x86_instr_read_byte(stream);
    } else if (mod == 2) {
        /* 16/32-bit displacement based on address size */
        if (instr->addr_size == 2) {
            instr->has_disp = 2;
            instr->displacement = (int16_t)x86_instr_read_word(stream);
        } else {
            instr->has_disp = 4;
            instr->displacement = (int32_t)x86_instr_read_dword(stream);
        }
    }

    /* If MOD = 11, it's a register operand, not memory */
    if (mod == 3) {
        instr->has_disp = 0;
    }

    /* SIB byte if R/M = 4 and MOD != 3 */
    if (rm == 4 && mod != 3) {
        instr->has_sib = 1;
        instr->sib = x86_instr_read_byte(stream);
        x86_decode_sib(cpu, instr, stream, instr->sib);
    }
}

/*
 * Decode the SIB (Scale-Index-Base) byte.
 *
 * SIB format:
 *   Bits 7-6: SCALE (1, 2, 4, or 8)
 *   Bits 5-3: INDEX (register index)
 *   Bits 2-0: BASE (register base)
 *
 * Special cases:
 *   INDEX = 4 (100b): no index register (ESP is not used as index)
 *   BASE = 5 (101b) with MOD=0: no base register (EIP-relative)
 */
void x86_decode_sib(x86_cpu_t *cpu, x86_instruction_t *instr,
                     x86_instr_stream_t *stream, uint8_t sib) {
    (void)cpu;
    (void)stream;

    uint8_t scale = (sib >> 6) & 0x03;
    uint8_t index = (sib >> 3) & 0x07;
    uint8_t base  = sib & 0x07;

    /* Scale factor: 2^scale */
    (void)scale;
    (void)index;
    (void)base;
}

/* Print decoded instruction for debugging */
void x86_instr_dump(x86_instruction_t *instr) {
    printf("[DECODE] opcode=0x%02X", instr->opcode);
    if (instr->opcode >= 0x100) {
        printf("+0F", instr->opcode - 0x100);
    }
    if (instr->has_modrm) {
        printf(" MOD/RM=0x%02X", instr->modrm);
        if (instr->has_sib) {
            printf(" SIB=0x%02X", instr->sib);
        }
    }
    if (instr->has_disp) {
        printf(" disp=%d", instr->displacement);
    }
    if (instr->has_imm) {
        printf(" imm=0x%X", instr->immediate);
    }
    printf("\n");
}
