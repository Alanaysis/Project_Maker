#include "x86_cpu.h"
#include <string.h>
#include <stdio.h>

/* ============================================================
 * x86_cpu.c - CPU register file implementation
 *
 * x86 Architecture Notes:
 *   - The 8 general-purpose registers (GPRs) are 32-bit in protected mode
 *   - AL/AH = low/high byte of EAX, BL/BH = low/high byte of EBX, etc.
 *   - AX/BX/CX/DX = 16-bit views, AL/BL/CL/DL = low 8-bit, AH/BH/CH/DH = high 8-bit
 *   - EFLAGS contains condition codes (ZF, SF, CF, OF) used by conditional instructions
 *   - Direction flag (DF) controls string instruction direction
 * ============================================================ */

void x86_cpu_init(x86_cpu_t *cpu) {
    memset(cpu, 0, sizeof(x86_cpu_t));

    /* Power-on reset state for real mode: */
    cpu->regs[X86_REG_EIP]  = 0xFFFF0;    /* Reset vector: near end of 1MB */
    cpu->regs[X86_REG_EAX]  = 0;
    cpu->regs[X86_REG_ECX]  = 0;
    cpu->regs[X86_REG_EDX]  = 0;
    cpu->regs[X86_REG_EBX]  = 0;
    cpu->regs[X86_REG_ESP]  = 0xFFFE;     /* Stack pointer near top of segment */
    cpu->regs[X86_REG_EBP]  = 0;
    cpu->regs[X86_REG_ESI]  = 0;
    cpu->regs[X86_REG_EDI]  = 0;

    /* Segment registers in real mode: base = selector << 4 */
    cpu->seg_regs[X86_SEG_CS] = 0xF000;
    cpu->seg_regs[X86_SEG_DS] = 0;
    cpu->seg_regs[X86_SEG_SS] = 0;
    cpu->seg_regs[X86_SEG_ES] = 0;
    cpu->seg_regs[X86_SEG_FS] = 0;
    cpu->seg_regs[X86_SEG_GS] = 0;

    /* Initialize segment state for real mode */
    for (int i = 0; i < X86_SEG_MAX; i++) {
        cpu->seg_state[i].selector = cpu->seg_regs[i];
        cpu->seg_state[i].base     = (uint32_t)cpu->seg_regs[i] << 4;
        cpu->seg_state[i].limit    = 0xFFFFF; /* 1MB in real mode */
        cpu->seg_state[i].dpl      = 0;
        cpu->seg_state[i].present  = true;
        cpu->seg_state[i].writable = true;
        cpu->seg_state[i].executable = (i == X86_SEG_CS);
        cpu->seg_state[i].db       = false; /* 16-bit default in real mode */
    }

    /* EFLAGS: bits 1, 5, and others are reserved/always 1 */
    cpu->eflags = 0x00000002; /* Bit 1 is always 1 */

    /* Control registers */
    cpu->cr0 = 0; /* PE=0 means real mode */

    /* GDT/IDT */
    cpu->gdtr_base = 0;
    cpu->gdtr_limit = 0;
    cpu->idtr_base = 0;
    cpu->idtr_limit = 0;

    cpu->mode = MODE_REAL;
    cpu->running = false;
    cpu->halted = false;
    cpu->instruction_count = 0;
    cpu->interrupt_pending = false;
    cpu->interrupt_masked = false;
}

void x86_cpu_reset(x86_cpu_t *cpu) {
    x86_cpu_init(cpu);
}

uint16_t x86_reg16_read(x86_cpu_t *cpu, uint8_t reg) {
    if (reg < X86_REG_MAX) {
        return (uint16_t)(cpu->regs[reg] & 0xFFFF);
    }
    return 0;
}

/*
 * Set condition flags based on an arithmetic/logic result.
 *
 * EFLAGS update rules:
 *   CF (Carry Flag):  Set if unsigned overflow occurred
 *   OF (Overflow Flag): Set if signed overflow occurred
 *   ZF (Zero Flag):   Set if result is zero
 *   SF (Sign Flag):   Set to MSB of result
 *   PF (Parity Flag): Set if low byte has even number of 1 bits
 *   AF (Auxiliary Flag): Set if carry/borrow from bit 3 to bit 4
 */
void x86_set_flags_from_result(x86_cpu_t *cpu, uint32_t result, uint8_t size) {
    uint32_t mask;

    /* Clear all condition flag bits */
    cpu->eflags &= ~(X86_EFLAGS_CF_MASK | X86_EFLAGS_OF_MASK |
                     X86_EFLAGS_ZF_MASK | X86_EFLAGS_SF_MASK |
                     X86_EFLAGS_PF_MASK | X86_EFLAGS_AF_MASK);

    if (size == X86_BYTE) {
        mask = 0xFF;
    } else if (size == X86_WORD) {
        mask = 0xFFFF;
    } else {
        mask = 0xFFFFFFFF;
    }

    uint32_t truncated = result & mask;

    /* Zero flag */
    if (truncated == 0) {
        cpu->eflags |= X86_EFLAGS_ZF_MASK;
    }

    /* Sign flag (MSB of truncated result) */
    if (size == X86_BYTE) {
        if (truncated & 0x80) {
            cpu->eflags |= X86_EFLAGS_SF_MASK;
        }
    } else if (size == X86_WORD) {
        if (truncated & 0x8000) {
            cpu->eflags |= X86_EFLAGS_SF_MASK;
        }
    } else {
        if (truncated & 0x80000000) {
            cpu->eflags |= X86_EFLAGS_SF_MASK;
        }
    }

    /* Parity flag: even number of 1 bits in low byte */
    uint8_t low_byte = (uint8_t)truncated;
    int parity = 0;
    for (int i = 0; i < 8; i++) {
        parity += (low_byte >> i) & 1;
    }
    if (parity % 2 == 0) {
        cpu->eflags |= X86_EFLAGS_PF_MASK;
    }

    /* CF and OF are set by specific arithmetic instructions */
    /* AF is also set by specific instructions */
}

/* Set flags for signed comparison (a - b) */
void x86_set_flags_signed(x86_cpu_t *cpu, int32_t a, int32_t b, uint8_t size) {
    int32_t result = a - b;
    uint32_t mask;

    if (size == X86_BYTE) {
        mask = 0xFF;
    } else if (size == X86_WORD) {
        mask = 0xFFFF;
    } else {
        mask = 0xFFFFFFFF;
    }

    uint32_t u_result = (uint32_t)result;
    uint32_t u_a = (uint32_t)a;
    uint32_t u_b = (uint32_t)b;

    /* Zero flag */
    if ((u_result & mask) == 0) {
        cpu->eflags |= X86_EFLAGS_ZF_MASK;
    }

    /* Sign flag */
    if (size == X86_BYTE) {
        if ((u_result & mask) & 0x80) cpu->eflags |= X86_EFLAGS_SF_MASK;
    } else if (size == X86_WORD) {
        if ((u_result & mask) & 0x8000) cpu->eflags |= X86_EFLAGS_SF_MASK;
    } else {
        if ((u_result & mask) & 0x80000000) cpu->eflags |= X86_EFLAGS_SF_MASK;
    }

    /* Parity flag */
    uint8_t low_byte = (uint8_t)(u_result & mask);
    int parity = 0;
    for (int i = 0; i < 8; i++) parity += (low_byte >> i) & 1;
    if (parity % 2 == 0) cpu->eflags |= X86_EFLAGS_PF_MASK;

    /* Carry flag: unsigned borrow occurred */
    if (u_a < u_b) {
        cpu->eflags |= X86_EFLAGS_CF_MASK;
    }

    /* Overflow flag: signed overflow occurred */
    /* Overflow when: (a > 0 && b > 0 && result < 0) || (a < 0 && b < 0 && result >= 0) */
    if (a > 0 && b > 0 && result < 0) {
        cpu->eflags |= X86_EFLAGS_OF_MASK;
    } else if (a < 0 && b < 0 && result >= 0) {
        cpu->eflags |= X86_EFLAGS_OF_MASK;
    }
}

/* Set flags for unsigned comparison (a - b) */
void x86_set_flags_unsigned(x86_cpu_t *cpu, uint32_t a, uint32_t b, uint8_t size) {
    uint32_t result = a - b;
    uint32_t mask;

    if (size == X86_BYTE) mask = 0xFF;
    else if (size == X86_WORD) mask = 0xFFFF;
    else mask = 0xFFFFFFFF;

    /* Zero flag */
    if ((result & mask) == 0) cpu->eflags |= X86_EFLAGS_ZF_MASK;

    /* Sign flag */
    if (size == X86_BYTE) {
        if ((result & mask) & 0x80) cpu->eflags |= X86_EFLAGS_SF_MASK;
    } else if (size == X86_WORD) {
        if ((result & mask) & 0x8000) cpu->eflags |= X86_EFLAGS_SF_MASK;
    } else {
        if ((result & mask) & 0x80000000) cpu->eflags |= X86_EFLAGS_SF_MASK;
    }

    /* Parity flag */
    uint8_t low_byte = (uint8_t)(result & mask);
    int parity = 0;
    for (int i = 0; i < 8; i++) parity += (low_byte >> i) & 1;
    if (parity % 2 == 0) cpu->eflags |= X86_EFLAGS_PF_MASK;

    /* Carry flag */
    if (a < b) cpu->eflags |= X86_EFLAGS_CF_MASK;
    else cpu->eflags &= ~X86_EFLAGS_CF_MASK;

    /* OF is not typically set by CMP for unsigned, but we zero it */
    cpu->eflags &= ~X86_EFLAGS_OF_MASK;
}

/*
 * Check condition codes for conditional jumps.
 *
 * x86 conditional jumps use a 1-byte predicate encoded in the opcode:
 *   0 = JE/JZ (jump if equal/zero)       -> ZF == 1
 *   1 = JNE/JNZ (jump if not equal)      -> ZF == 0
 *   2 = JB/JNAE (jump below)              -> CF == 1
 *   3 = JNB/JAE (jump above or equal)     -> CF == 0
 *   4 = JNA (jump not above)              -> (ZF | CF) == 1
 *   5 = JA/JNBE (jump above)              -> (ZF | CF) == 0
 *   6 = JS (jump sign/负)                 -> SF == 1
 *   7 = JNS (jump not sign)               -> SF == 0
 *   8 = JBE/JNA (jump below or equal)     -> (ZF | CF) == 1
 *   9 = JA (jump above)                   -> (ZF | CF) == 0
 *  10 = JL (jump less)                    -> (SF ^ OF) == 1
 *  11 = JGE (jump greater or equal)       -> (SF ^ OF) == 0
 *  12 = JNG (jump not greater)            -> (SF ^ OF) == 1
 *  13 = JG (jump greater)                 -> (SF ^ OF) == 0
 *  14 = JNE (jump not equal)              -> ZF == 0
 *  15 = JE (jump equal)                   -> ZF == 1
 */
bool x86_check_condition(x86_cpu_t *cpu, uint8_t condition) {
    bool zf = x86_eflags_get(cpu, X86_EFLAGS_ZF_MASK);
    bool sf = x86_eflags_get(cpu, X86_EFLAGS_SF_MASK);
    bool of = x86_eflags_get(cpu, X86_EFLAGS_OF_MASK);
    bool cf = x86_eflags_get(cpu, X86_EFLAGS_CF_MASK);

    switch (condition) {
        case 0: return zf;                          /* JE/JZ */
        case 1: return !zf;                         /* JNE/JNZ */
        case 2: return cf;                          /* JB/JNAE */
        case 3: return !cf;                         /* JNB/JAE */
        case 4: return (zf || cf);                  /* JNA */
        case 5: return !(zf || cf);                 /* JA/JNBE */
        case 6: return sf;                          /* JS */
        case 7: return !sf;                         /* JNS */
        case 8: return (zf || cf);                  /* JBE */
        case 9: return !(zf || cf);                 /* JA (dup) */
        case 10: return (sf != of);                 /* JL */
        case 11: return (sf == of);                 /* JGE */
        case 12: return (sf != of);                 /* JNG */
        case 13: return (sf == of) && !zf;         /* JG */
        case 14: return !zf;                         /* JNE */
        case 15: return zf;                          /* JE */
        default: return false;
    }
}

void x86_cpu_dump(x86_cpu_t *cpu) {
    printf("=== CPU State ===\n");
    printf("Mode: %s\n", cpu->mode == MODE_REAL ? "REAL" : "PROTECTED");
    printf("EIP:  0x%08X\n", cpu->eip);
    x86_cpu_dump_registers(cpu);
    x86_cpu_dump_eflags(cpu);
    printf("Instructions executed: %u\n", cpu->instruction_count);
    printf("=================\n");
}

void x86_cpu_dump_registers(x86_cpu_t *cpu) {
    const char *names[] = {"EIP", "EAX", "ECX", "EDX", "EBX", "ESP", "EBP", "ESI", "EDI"};
    printf("\n--- General Purpose Registers ---\n");
    for (int i = 0; i < X86_REG_MAX; i++) {
        printf("  %s: 0x%08X  (%u / %d)\n", names[i],
               cpu->regs[i], cpu->regs[i], (int32_t)cpu->regs[i]);
    }

    const char *seg_names[] = {"CS", "DS", "SS", "ES", "FS", "GS"};
    printf("\n--- Segment Registers ---\n");
    for (int i = 0; i < X86_SEG_MAX; i++) {
        printf("  %s: selector=0x%04X base=0x%08X limit=0x%08X\n",
               seg_names[i], cpu->seg_regs[i],
               cpu->seg_state[i].base, cpu->seg_state[i].limit);
    }
    printf("\n");
}

void x86_cpu_dump_eflags(x86_cpu_t *cpu) {
    printf("--- EFLAGS ---\n");
    printf("  CF=%d  PF=%d  AF=%d  ZF=%d  SF=%d  DF=%d  OF=%d  IF=%d\n",
           x86_eflags_get(cpu, X86_EFLAGS_CF_MASK) ? 1 : 0,
           x86_eflags_get(cpu, X86_EFLAGS_PF_MASK) ? 1 : 0,
           x86_eflags_get(cpu, X86_EFLAGS_AF_MASK) ? 1 : 0,
           x86_eflags_get(cpu, X86_EFLAGS_ZF_MASK) ? 1 : 0,
           x86_eflags_get(cpu, X86_EFLAGS_SF_MASK) ? 1 : 0,
           x86_eflags_get(cpu, X86_EFLAGS_DF_MASK) ? 1 : 0,
           x86_eflags_get(cpu, X86_EFLAGS_OF_MASK) ? 1 : 0,
           x86_eflags_get(cpu, X86_EFLAGS_IF_MASK) ? 1 : 0);
    printf("  EFLAGS=0x%08X\n\n", cpu->eflags);
}
