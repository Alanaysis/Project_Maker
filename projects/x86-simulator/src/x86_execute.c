#include "x86_execute.h"
#include <stdio.h>

/* ============================================================
 * x86_execute.c - Instruction execution implementation
 *
 * This module implements the execution of all supported x86
 * instruction categories:
 *
 * 1. Data Movement: MOV, PUSH, POP, XCHG
 * 2. Arithmetic: ADD, SUB, MUL, DIV, INC, DEC, CMP
 * 3. Logic: AND, OR, XOR, NOT, SHL, SHR, SAR, ROL, ROR
 * 4. Control Flow: JMP, JE, JNE, JL, JG, CALL, RET
 * 5. String: MOVSB, CMPSB, LODSB, STOSB
 * 6. Interrupt: INT, INT3, IRET
 *
 * Each instruction has an execute function that takes the CPU
 * state, memory, and operands as parameters.
 * ============================================================ */

/* ============================================================
 * DATA MOVEMENT INSTRUCTIONS
 * ============================================================ */

/*
 * MOV - Move data between registers, memory, and immediates
 *
 * x86 MOV encoding:
 *   88h r/m8, r8       : MOV r/m8, r8
 *   89h r/m16/32, r    : MOV r/m16/32, r16/32
 *   8Ah r8, r/m8       : MOV r8, r/m8
 *   8Bh r16/32, r/m    : MOV r16/32, r/m16/32
 *   A0h AL, moffs8     : MOV AL, mem
 *   A1h AX/EAX, moffs  : MOV AX/EAX, mem
 *   A2h moffs8, AL     : MOV mem, AL
 *   A3h moffs16/32, AX/EAX : MOV mem, AX/EAX
 *   B0h+reg r8, imm8   : MOV reg, imm8
 *   C6h r/m8, imm8     : MOV r/m8, imm8
 *   C7h r/m16/32, imm  : MOV r/m16/32, imm
 *   8Ch r/m16, s16     : MOV r/m16, segment
 *   8Eh s16, r/m16     : MOV segment, r/m16
 */
static void exec_mov(x86_cpu_t *cpu, x86_memory_t *mem,
                     x86_instruction_t *instr) {
    uint8_t mod = (instr->modrm >> 6) & 0x03;
    uint8_t reg = (instr->modrm >> 3) & 0x07;
    uint8_t rm  = instr->modrm & 0x07;

    if (mod == 3) {
        /* Register to register or immediate to register */
        if (instr->has_imm) {
            /* MOV reg, immediate */
            uint32_t val = instr->immediate;
            if (instr->operand_size == 1) {
                val = (uint8_t)val;
            } else if (instr->operand_size == 2) {
                val = (uint16_t)val;
            }
            x86_reg_write(cpu, reg, val);
        } else {
            /* MOV r/m, r */
            uint32_t src = x86_reg_read(cpu, reg);
            if (instr->operand_size == 1) {
                /* Low byte of source register */
                src = (uint8_t)src;
            }
            uint32_t phys = x86_get_linear_address(cpu, instr, instr->modrm,
                                                      instr->sib, instr->addr_size);
            if (instr->operand_size == 1) {
                x86_mem_write_byte(mem, phys, (uint8_t)src);
            } else if (instr->operand_size == 2) {
                x86_mem_write_word(mem, phys, (uint16_t)src);
            } else {
                x86_mem_write_dword(mem, phys, src);
            }
        }
    } else {
        /* Memory operand */
        uint32_t phys = x86_get_linear_address(cpu, instr, instr->modrm,
                                                  instr->sib, instr->addr_size);
        uint32_t val;

        if (instr->has_imm) {
            /* MOV r/m, immediate */
            val = instr->immediate;
            if (instr->operand_size == 1) {
                x86_mem_write_byte(mem, phys, (uint8_t)val);
            } else if (instr->operand_size == 2) {
                x86_mem_write_word(mem, phys, (uint16_t)val);
            } else {
                x86_mem_write_dword(mem, phys, val);
            }
        } else {
            /* MOV r, r/m */
            if (instr->operand_size == 1) {
                val = x86_mem_read_byte(mem, phys);
            } else if (instr->operand_size == 2) {
                val = x86_mem_read_word(mem, phys);
            } else {
                val = x86_mem_read_dword(mem, phys);
            }
            x86_reg_write(cpu, reg, val);
        }
    }
}

/*
 * PUSH - Push value onto the stack
 *
 * Encoding:
 *   50h+reg : PUSH reg16/32
 *   68h imm : PUSH imm16/32
 *   6Ah imm : PUSH imm8 (sign-extended)
 */
static void exec_push(x86_cpu_t *cpu, x86_memory_t *mem,
                      x86_instruction_t *instr) {
    uint32_t val;

    if (instr->has_modrm && (instr->modrm >> 6) & 0x03 == 3) {
        /* PUSH reg */
        uint8_t reg = (instr->modrm >> 3) & 0x07;
        val = x86_reg_read(cpu, reg);
        if (instr->operand_size == 2) {
            val = (uint16_t)val;
        }
    } else if (instr->has_imm) {
        /* PUSH imm */
        val = instr->immediate;
        if (instr->operand_size == 1) {
            val = (int8_t)val; /* Sign-extend */
        } else if (instr->operand_size == 2) {
            val = (uint16_t)val;
        }
    } else {
        return;
    }

    x86_stack_push(cpu, mem, val);
}

/*
 * POP - Pop value from the stack
 *
 * Encoding:
 *   58h+reg : POP reg16/32
 */
static void exec_pop(x86_cpu_t *cpu, x86_memory_t *mem,
                     x86_instruction_t *instr) {
    uint8_t reg = (instr->modrm >> 3) & 0x07;
    uint32_t val = x86_stack_pop(cpu, mem);

    if (instr->operand_size == 2) {
        val = (uint16_t)val;
    }
    x86_reg_write(cpu, reg, val);
}

/*
 * XCHG - Exchange values between two operands
 *
 * Encoding:
 *   87h r/m16/32, r16/32 : XCHG r/m, r
 *   90h+reg               : XCHG EAX, reg (or NOP for EAX,EAX)
 */
static void exec_xchg(x86_cpu_t *cpu, x86_memory_t *mem,
                      x86_instruction_t *instr) {
    uint8_t mod = (instr->modrm >> 6) & 0x03;
    uint8_t reg = (instr->modrm >> 3) & 0x07;

    if (mod == 3) {
        /* Register to register exchange */
        uint32_t r1 = x86_reg_read(cpu, reg);
        uint32_t r2 = x86_reg_read(cpu, X86_REG_EAX);

        if (instr->operand_size == 2) {
            r1 = (uint16_t)r1;
            r2 = (uint16_t)r2;
        }

        x86_reg_write(cpu, reg, r2);
        x86_reg_write(cpu, X86_REG_EAX, r1);
    } else {
        /* Memory-register exchange */
        uint32_t phys = x86_get_linear_address(cpu, instr, instr->modrm,
                                                  instr->sib, instr->addr_size);
        uint32_t r1 = x86_reg_read(cpu, reg);
        uint32_t r2;

        if (instr->operand_size == 1) {
            r2 = x86_mem_read_byte(mem, phys);
            x86_mem_write_byte(mem, phys, (uint8_t)r1);
        } else if (instr->operand_size == 2) {
            r2 = x86_mem_read_word(mem, phys);
            x86_mem_write_word(mem, phys, (uint16_t)r1);
        } else {
            r2 = x86_mem_read_dword(mem, phys);
            x86_mem_write_dword(mem, phys, r1);
        }
        x86_reg_write(cpu, reg, r2);
    }
}

/* ============================================================
 * ARITHMETIC INSTRUCTIONS
 * ============================================================ */

/*
 * ADD - Addition
 *
 * Encoding:
 *   00h r/m8, r8     : ADD r/m8, r8
 *   01h r/m16/32, r  : ADD r/m16/32, r
 *   80h/81h r/m, imm : ADD r/m, immediate
 *   83h r/m, imm8    : ADD r/m, sign-extended imm8
 *   04h imm          : ADD AL, imm8
 *   05h imm          : ADD AX/EAX, imm16/32
 */
static void exec_add(x86_cpu_t *cpu, x86_memory_t *mem,
                     x86_instruction_t *instr) {
    uint8_t mod = (instr->modrm >> 6) & 0x03;
    uint8_t reg = (instr->modrm >> 3) & 0x07;
    uint8_t size = instr->operand_size;

    uint32_t src, dst;

    if (mod == 3) {
        /* Register operands */
        src = x86_reg_read(cpu, reg);
        dst = x86_reg_read(cpu, instr->modrm & 0x07);
    } else {
        /* Memory operand */
        uint32_t phys = x86_get_linear_address(cpu, instr, instr->modrm,
                                                  instr->sib, instr->addr_size);
        if (size == 1) src = x86_mem_read_byte(mem, phys);
        else if (size == 2) src = x86_mem_read_word(mem, phys);
        else src = x86_mem_read_dword(mem, phys);
        dst = x86_reg_read(cpu, reg);
    }

    if (size == 1) {
        uint8_t result = (uint8_t)(src + dst);
        x86_set_flags_from_result(cpu, result, X86_BYTE);
        if (mod == 3) {
            x86_reg_write(cpu, instr->modrm & 0x07, result);
        } else {
            x86_mem_write_byte(mem, x86_get_linear_address(cpu, instr, instr->modrm,
                                                              instr->sib, instr->addr_size), result);
        }
    } else if (size == 2) {
        uint16_t result = (uint16_t)(src + dst);
        x86_set_flags_from_result(cpu, result, X86_WORD);
        if (mod == 3) {
            x86_reg16_write(cpu, instr->modrm & 0x07, result);
        } else {
            x86_mem_write_word(mem, x86_get_linear_address(cpu, instr, instr->modrm,
                                                              instr->sib, instr->addr_size), result);
        }
    } else {
        uint32_t result = src + dst;
        x86_set_flags_from_result(cpu, result, X86_DWORD);
        if (mod == 3) {
            x86_reg_write(cpu, instr->modrm & 0x07, result);
        } else {
            x86_mem_write_dword(mem, x86_get_linear_address(cpu, instr, instr->modrm,
                                                              instr->sib, instr->addr_size), result);
        }
    }
}

/*
 * SUB - Subtraction
 *
 * Encoding:
 *   28h r/m8, r8     : SUB r/m8, r8
 *   29h r/m16/32, r  : SUB r/m16/32, r
 *   80h/81h r/m, imm : SUB r/m, immediate
 *   83h r/m, imm8    : SUB r/m, sign-extended imm8
 *   2Ah imm          : SUB AL, imm8
 *   2Bh imm          : SUB AX/EAX, imm16/32
 */
static void exec_sub(x86_cpu_t *cpu, x86_memory_t *mem,
                     x86_instruction_t *instr) {
    uint8_t mod = (instr->modrm >> 6) & 0x03;
    uint8_t reg = (instr->modrm >> 3) & 0x07;
    uint8_t size = instr->operand_size;

    uint32_t src, dst;

    if (mod == 3) {
        src = x86_reg_read(cpu, reg);
        dst = x86_reg_read(cpu, instr->modrm & 0x07);
    } else {
        uint32_t phys = x86_get_linear_address(cpu, instr, instr->modrm,
                                                  instr->sib, instr->addr_size);
        if (size == 1) src = x86_mem_read_byte(mem, phys);
        else if (size == 2) src = x86_mem_read_word(mem, phys);
        else src = x86_mem_read_dword(mem, phys);
        dst = x86_reg_read(cpu, reg);
    }

    if (size == 1) {
        uint8_t result = (uint8_t)(dst - src);
        x86_set_flags_from_result(cpu, result, X86_BYTE);
        if (mod == 3) {
            x86_reg_write(cpu, instr->modrm & 0x07, result);
        } else {
            x86_mem_write_byte(mem, x86_get_linear_address(cpu, instr, instr->modrm,
                                                              instr->sib, instr->addr_size), result);
        }
    } else if (size == 2) {
        uint16_t result = (uint16_t)(dst - src);
        x86_set_flags_from_result(cpu, result, X86_WORD);
        if (mod == 3) {
            x86_reg16_write(cpu, instr->modrm & 0x07, result);
        } else {
            x86_mem_write_word(mem, x86_get_linear_address(cpu, instr, instr->modrm,
                                                              instr->sib, instr->addr_size), result);
        }
    } else {
        uint32_t result = dst - src;
        x86_set_flags_from_result(cpu, result, X86_DWORD);
        if (mod == 3) {
            x86_reg_write(cpu, instr->modrm & 0x07, result);
        } else {
            x86_mem_write_dword(mem, x86_get_linear_address(cpu, instr, instr->modrm,
                                                              instr->sib, instr->addr_size), result);
        }
    }
}

/*
 * INC - Increment
 *
 * Encoding:
 *   40h+reg : INC reg16/32
 */
static void exec_inc(x86_cpu_t *cpu, x86_memory_t *mem,
                     x86_instruction_t *instr) {
    (void)mem;
    uint8_t reg = instr->opcode & 0x07;
    uint8_t size = instr->operand_size;

    uint32_t val;
    if (size == 1) {
        val = (uint8_t)x86_reg_read(cpu, reg) + 1;
        x86_set_flags_from_result(cpu, val, X86_BYTE);
        x86_reg_write(cpu, reg, val);
    } else if (size == 2) {
        uint16_t v16 = (uint16_t)x86_reg16_read(cpu, reg) + 1;
        x86_set_flags_from_result(cpu, v16, X86_WORD);
        x86_reg16_write(cpu, reg, v16);
    } else {
        uint32_t v32 = x86_reg_read(cpu, reg) + 1;
        x86_set_flags_from_result(cpu, v32, X86_DWORD);
        x86_reg_write(cpu, reg, v32);
    }
}

/*
 * DEC - Decrement
 *
 * Encoding:
 *   48h+reg : DEC reg16/32
 */
static void exec_dec(x86_cpu_t *cpu, x86_memory_t *mem,
                     x86_instruction_t *instr) {
    (void)mem;
    uint8_t reg = instr->opcode & 0x07;
    uint8_t size = instr->operand_size;

    if (size == 1) {
        uint8_t val = (uint8_t)x86_reg_read(cpu, reg) - 1;
        x86_set_flags_from_result(cpu, val, X86_BYTE);
        x86_reg_write(cpu, reg, val);
    } else if (size == 2) {
        uint16_t v16 = (uint16_t)x86_reg16_read(cpu, reg) - 1;
        x86_set_flags_from_result(cpu, v16, X86_WORD);
        x86_reg16_write(cpu, reg, v16);
    } else {
        uint32_t v32 = x86_reg_read(cpu, reg) - 1;
        x86_set_flags_from_result(cpu, v32, X86_DWORD);
        x86_reg_write(cpu, reg, v32);
    }
}

/*
 * MUL - Unsigned multiply
 *
 * Encoding:
 *   F6h/4 : MUL r/m8  -> DX:A = AL * r/m8
 *   F7h/4 : MUL r/m16/32 -> EDX:EAX = EAX * r/m
 */
static void exec_mul(x86_cpu_t *cpu, x86_memory_t *mem,
                     x86_instruction_t *instr) {
    (void)mem;
    uint8_t mod = (instr->modrm >> 6) & 0x03;
    uint8_t rm  = instr->modrm & 0x07;
    uint8_t size = instr->operand_size;

    uint32_t src;
    if (mod == 3) {
        src = x86_reg_read(cpu, rm);
    } else {
        uint32_t phys = x86_get_linear_address(cpu, instr, instr->modrm,
                                                  instr->sib, instr->addr_size);
        if (size == 1) src = x86_mem_read_byte(mem, phys);
        else if (size == 2) src = x86_mem_read_word(mem, phys);
        else src = x86_mem_read_dword(mem, phys);
    }

    if (size == 1) {
        /* 8-bit multiply: DX:A = AL * r/m8 */
        uint16_t product = (uint16_t)((uint8_t)x86_reg_read(cpu, X86_REG_EAX)) *
                           (uint16_t)src;
        x86_reg_write(cpu, X86_REG_EAX, (uint8_t)product);
        x86_reg_write(cpu, X86_REG_EDX, (uint8_t)(product >> 8));
    } else {
        /* 16/32-bit multiply */
        uint32_t val = x86_reg_read(cpu, X86_REG_EAX);
        if (size == 2) {
            uint64_t product = (uint64_t)((uint16_t)val) * (uint64_t)((uint16_t)src);
            x86_reg_write(cpu, X86_REG_EAX, (uint16_t)product);
            x86_reg_write(cpu, X86_REG_EDX, (uint16_t)(product >> 16));
        } else {
            uint64_t product = (uint64_t)val * (uint64_t)src;
            x86_reg_write(cpu, X86_REG_EAX, (uint32_t)product);
            x86_reg_write(cpu, X86_REG_EDX, (uint32_t)(product >> 32));
        }
    }

    /* CF and OF are set if high half is non-zero */
    if (size == 1) {
        uint16_t product = (uint16_t)((uint8_t)x86_reg_read(cpu, X86_REG_EAX)) *
                           (uint16_t)src;
        if (product > 0xFF) {
            x86_eflags_set(cpu, X86_EFLAGS_CF_MASK | X86_EFLAGS_OF_MASK);
        } else {
            x86_eflags_clear(cpu, X86_EFLAGS_CF_MASK | X86_EFLAGS_OF_MASK);
        }
    }
}

/*
 * DIV - Unsigned divide
 *
 * Encoding:
 *   F6h/6 : DIV r/m8  -> A = DX:A / r/m8, Q remainder = DX:A % r/m8
 *   F7h/6 : DIV r/m16/32 -> EAX = EDX:EAX / r/m, EDX = remainder
 */
static void exec_div(x86_cpu_t *cpu, x86_memory_t *mem,
                     x86_instruction_t *instr) {
    (void)mem;
    uint8_t mod = (instr->modrm >> 6) & 0x03;
    uint8_t rm  = instr->modrm & 0x07;
    uint8_t size = instr->operand_size;

    uint32_t src;
    if (mod == 3) {
        src = x86_reg_read(cpu, rm);
    } else {
        uint32_t phys = x86_get_linear_address(cpu, instr, instr->modrm,
                                                  instr->sib, instr->addr_size);
        if (size == 1) src = x86_mem_read_byte(mem, phys);
        else if (size == 2) src = x86_mem_read_word(mem, phys);
        else src = x86_mem_read_dword(mem, phys);
    }

    if (src == 0) {
        /* Divide by zero - trigger interrupt 0 */
        cpu->interrupt_pending = true;
        cpu->interrupt_vector = 0;
        return;
    }

    if (size == 1) {
        /* 8-bit divide: A = DX:A / src */
        uint16_t dividend = ((uint16_t)x86_reg_read(cpu, X86_REG_EDX) << 8) |
                             (uint16_t)x86_reg_read(cpu, X86_REG_EAX);
        uint8_t quotient = (uint8_t)(dividend / src);
        uint8_t remainder = (uint8_t)(dividend % src);
        x86_reg_write(cpu, X86_REG_EAX, quotient);
        x86_reg_write(cpu, X86_REG_EDX, remainder);
    } else {
        /* 16/32-bit divide */
        uint64_t dividend;
        if (size == 2) {
            dividend = ((uint64_t)x86_reg_read(cpu, X86_REG_EDX) << 16) |
                        (uint64_t)x86_reg_read(cpu, X86_REG_EAX);
            uint16_t quotient = (uint16_t)(dividend / src);
            uint16_t remainder = (uint16_t)(dividend % src);
            x86_reg_write(cpu, X86_REG_EAX, quotient);
            x86_reg_write(cpu, X86_REG_EDX, remainder);
        } else {
            dividend = ((uint64_t)x86_reg_read(cpu, X86_REG_EDX) << 32) |
                        (uint64_t)x86_reg_read(cpu, X86_REG_EAX);
            uint32_t quotient = (uint32_t)(dividend / src);
            uint32_t remainder = (uint32_t)(dividend % src);
            x86_reg_write(cpu, X86_REG_EAX, quotient);
            x86_reg_write(cpu, X86_REG_EDX, remainder);
        }
    }
}

/*
 * CMP - Compare (subtracts second from first, sets flags, discards result)
 *
 * Encoding:
 *   38h r/m8, r8     : CMP r/m8, r8
 *   39h r/m16/32, r  : CMP r/m16/32, r
 *   80h/81h r/m, imm : CMP r/m, immediate
 *   83h r/m, imm8    : CMP r/m, sign-extended imm8
 *   3Ah imm          : CMP AL, imm8
 *   3Bh imm          : CMP AX/EAX, imm16/32
 */
static void exec_cmp(x86_cpu_t *cpu, x86_memory_t *mem,
                     x86_instruction_t *instr) {
    uint8_t mod = (instr->modrm >> 6) & 0x03;
    uint8_t reg = (instr->modrm >> 3) & 0x07;
    uint8_t size = instr->operand_size;

    uint32_t src, dst;

    if (mod == 3) {
        src = x86_reg_read(cpu, reg);
        dst = x86_reg_read(cpu, instr->modrm & 0x07);
    } else {
        uint32_t phys = x86_get_linear_address(cpu, instr, instr->modrm,
                                                  instr->sib, instr->addr_size);
        if (size == 1) src = x86_mem_read_byte(mem, phys);
        else if (size == 2) src = x86_mem_read_word(mem, phys);
        else src = x86_mem_read_dword(mem, phys);
        dst = x86_reg_read(cpu, reg);
    }

    if (size == 1) {
        x86_set_flags_signed(cpu, (int8_t)src, (int8_t)dst, X86_BYTE);
    } else if (size == 2) {
        x86_set_flags_signed(cpu, (int16_t)src, (int16_t)dst, X86_WORD);
    } else {
        x86_set_flags_signed(cpu, (int32_t)src, (int32_t)dst, X86_DWORD);
    }
}

/* ============================================================
 * LOGIC INSTRUCTIONS
 * ============================================================ */

/*
 * AND - Bitwise AND
 *
 * Encoding:
 *   20h r/m8, r8     : AND r/m8, r8
 *   21h r/m16/32, r  : AND r/m16/32, r
 *   80h/81h r/m, imm : AND r/m, immediate
 *   83h r/m, imm8    : AND r/m, sign-extended imm8
 *   24h imm          : AND AL, imm8
 *   25h imm          : AND AX/EAX, imm16/32
 */
static void exec_and(x86_cpu_t *cpu, x86_memory_t *mem,
                     x86_instruction_t *instr) {
    uint8_t mod = (instr->modrm >> 6) & 0x03;
    uint8_t reg = (instr->modrm >> 3) & 0x07;
    uint8_t size = instr->operand_size;

    uint32_t src, dst;

    if (mod == 3) {
        src = x86_reg_read(cpu, reg);
        dst = x86_reg_read(cpu, instr->modrm & 0x07);
    } else {
        uint32_t phys = x86_get_linear_address(cpu, instr, instr->modrm,
                                                  instr->sib, instr->addr_size);
        if (size == 1) src = x86_mem_read_byte(mem, phys);
        else if (size == 2) src = x86_mem_read_word(mem, phys);
        else src = x86_mem_read_dword(mem, phys);
        dst = x86_reg_read(cpu, reg);
    }

    uint32_t result;
    if (size == 1) {
        result = (uint8_t)(src & dst);
        x86_set_flags_from_result(cpu, result, X86_BYTE);
        if (mod == 3) {
            x86_reg_write(cpu, instr->modrm & 0x07, result);
        } else {
            x86_mem_write_byte(mem, x86_get_linear_address(cpu, instr, instr->modrm,
                                                              instr->sib, instr->addr_size), result);
        }
    } else if (size == 2) {
        result = (uint16_t)(src & dst);
        x86_set_flags_from_result(cpu, result, X86_WORD);
        if (mod == 3) {
            x86_reg16_write(cpu, instr->modrm & 0x07, result);
        } else {
            x86_mem_write_word(mem, x86_get_linear_address(cpu, instr, instr->modrm,
                                                              instr->sib, instr->addr_size), result);
        }
    } else {
        result = src & dst;
        x86_set_flags_from_result(cpu, result, X86_DWORD);
        if (mod == 3) {
            x86_reg_write(cpu, instr->modrm & 0x07, result);
        } else {
            x86_mem_write_dword(mem, x86_get_linear_address(cpu, instr, instr->modrm,
                                                              instr->sib, instr->addr_size), result);
        }
    }
}

/*
 * OR - Bitwise OR
 *
 * Encoding:
 *   08h r/m8, r8     : OR r/m8, r8
 *   09h r/m16/32, r  : OR r/m16/32, r
 *   80h/81h r/m, imm : OR r/m, immediate
 *   83h r/m, imm8    : OR r/m, sign-extended imm8
 *   0Ah imm          : OR AX/EAX, imm16/32
 */
static void exec_or(x86_cpu_t *cpu, x86_memory_t *mem,
                    x86_instruction_t *instr) {
    uint8_t mod = (instr->modrm >> 6) & 0x03;
    uint8_t reg = (instr->modrm >> 3) & 0x07;
    uint8_t size = instr->operand_size;

    uint32_t src, dst;

    if (mod == 3) {
        src = x86_reg_read(cpu, reg);
        dst = x86_reg_read(cpu, instr->modrm & 0x07);
    } else {
        uint32_t phys = x86_get_linear_address(cpu, instr, instr->modrm,
                                                  instr->sib, instr->addr_size);
        if (size == 1) src = x86_mem_read_byte(mem, phys);
        else if (size == 2) src = x86_mem_read_word(mem, phys);
        else src = x86_mem_read_dword(mem, phys);
        dst = x86_reg_read(cpu, reg);
    }

    uint32_t result;
    if (size == 1) {
        result = (uint8_t)(src | dst);
        x86_set_flags_from_result(cpu, result, X86_BYTE);
        if (mod == 3) {
            x86_reg_write(cpu, instr->modrm & 0x07, result);
        } else {
            x86_mem_write_byte(mem, x86_get_linear_address(cpu, instr, instr->modrm,
                                                              instr->sib, instr->addr_size), result);
        }
    } else if (size == 2) {
        result = (uint16_t)(src | dst);
        x86_set_flags_from_result(cpu, result, X86_WORD);
        if (mod == 3) {
            x86_reg16_write(cpu, instr->modrm & 0x07, result);
        } else {
            x86_mem_write_word(mem, x86_get_linear_address(cpu, instr, instr->modrm,
                                                              instr->sib, instr->addr_size), result);
        }
    } else {
        result = src | dst;
        x86_set_flags_from_result(cpu, result, X86_DWORD);
        if (mod == 3) {
            x86_reg_write(cpu, instr->modrm & 0x07, result);
        } else {
            x86_mem_write_dword(mem, x86_get_linear_address(cpu, instr, instr->modrm,
                                                              instr->sib, instr->addr_size), result);
        }
    }
}

/*
 * XOR - Bitwise XOR
 *
 * Encoding:
 *   30h r/m8, r8     : XOR r/m8, r8
 *   31h r/m16/32, r  : XOR r/m16/32, r
 *   80h/81h r/m, imm : XOR r/m, immediate
 *   83h r/m, imm8    : XOR r/m, sign-extended imm8
 *   34h imm          : XOR AL, imm8
 *   35h imm          : XOR AX/EAX, imm16/32
 */
static void exec_xor(x86_cpu_t *cpu, x86_memory_t *mem,
                     x86_instruction_t *instr) {
    uint8_t mod = (instr->modrm >> 6) & 0x03;
    uint8_t reg = (instr->modrm >> 3) & 0x07;
    uint8_t size = instr->operand_size;

    uint32_t src, dst;

    if (mod == 3) {
        src = x86_reg_read(cpu, reg);
        dst = x86_reg_read(cpu, instr->modrm & 0x07);
    } else {
        uint32_t phys = x86_get_linear_address(cpu, instr, instr->modrm,
                                                  instr->sib, instr->addr_size);
        if (size == 1) src = x86_mem_read_byte(mem, phys);
        else if (size == 2) src = x86_mem_read_word(mem, phys);
        else src = x86_mem_read_dword(mem, phys);
        dst = x86_reg_read(cpu, reg);
    }

    uint32_t result;
    if (size == 1) {
        result = (uint8_t)(src ^ dst);
        x86_set_flags_from_result(cpu, result, X86_BYTE);
        if (mod == 3) {
            x86_reg_write(cpu, instr->modrm & 0x07, result);
        } else {
            x86_mem_write_byte(mem, x86_get_linear_address(cpu, instr, instr->modrm,
                                                              instr->sib, instr->addr_size), result);
        }
    } else if (size == 2) {
        result = (uint16_t)(src ^ dst);
        x86_set_flags_from_result(cpu, result, X86_WORD);
        if (mod == 3) {
            x86_reg16_write(cpu, instr->modrm & 0x07, result);
        } else {
            x86_mem_write_word(mem, x86_get_linear_address(cpu, instr, instr->modrm,
                                                              instr->sib, instr->addr_size), result);
        }
    } else {
        result = src ^ dst;
        x86_set_flags_from_result(cpu, result, X86_DWORD);
        if (mod == 3) {
            x86_reg_write(cpu, instr->modrm & 0x07, result);
        } else {
            x86_mem_write_dword(mem, x86_get_linear_address(cpu, instr, instr->modrm,
                                                              instr->sib, instr->addr_size), result);
        }
    }
}

/*
 * NOT - Bitwise NOT (one's complement)
 *
 * Encoding:
 *   F6h/2 : NOT r/m8
 *   F7h/2 : NOT r/m16/32
 */
static void exec_not(x86_cpu_t *cpu, x86_memory_t *mem,
                     x86_instruction_t *instr) {
    (void)cpu;
    uint8_t mod = (instr->modrm >> 6) & 0x03;
    uint8_t size = instr->operand_size;

    uint32_t phys = x86_get_linear_address(cpu, instr, instr->modrm,
                                              instr->sib, instr->addr_size);

    if (size == 1) {
        uint8_t val = ~x86_mem_read_byte(mem, phys);
        x86_mem_write_byte(mem, phys, val);
    } else if (size == 2) {
        uint16_t val = ~x86_mem_read_word(mem, phys);
        x86_mem_write_word(mem, phys, val);
    } else {
        uint32_t val = ~x86_mem_read_dword(mem, phys);
        x86_mem_write_dword(mem, phys, val);
    }
}

/*
 * SHL - Shift left
 *
 * Encoding:
 *   D0h/D1h/D3h r/m, 1/CL : SHL r/m, count
 *   C0h/C1h r/m, imm8     : SHL r/m, count
 */
static void exec_shl(x86_cpu_t *cpu, x86_memory_t *mem,
                     x86_instruction_t *instr) {
    uint8_t mod = (instr->modrm >> 6) & 0x03;
    uint8_t rm  = instr->modrm & 0x07;
    uint8_t size = instr->operand_size;

    uint32_t count;
    if (instr->modrm == 0xD2 || instr->modrm == 0xD3) {
        /* Shift by CL register */
        count = x86_reg_read(cpu, X86_REG_ECX) & 0x1F;
    } else if (instr->has_imm) {
        count = instr->immediate & 0x1F;
    } else {
        count = 1;
    }

    uint32_t val;
    if (mod == 3) {
        val = x86_reg_read(cpu, rm);
    } else {
        uint32_t phys = x86_get_linear_address(cpu, instr, instr->modrm,
                                                  instr->sib, instr->addr_size);
        if (size == 1) val = x86_mem_read_byte(mem, phys);
        else if (size == 2) val = x86_mem_read_word(mem, phys);
        else val = x86_mem_read_dword(mem, phys);
    }

    uint32_t result;
    if (size == 1) {
        result = ((uint8_t)val) << count;
        x86_set_flags_from_result(cpu, result, X86_BYTE);
    } else if (size == 2) {
        result = ((uint16_t)val) << count;
        x86_set_flags_from_result(cpu, result, X86_WORD);
    } else {
        result = val << count;
        x86_set_flags_from_result(cpu, result, X86_DWORD);
    }

    /* Set CF to last bit shifted out */
    if (count > 0) {
        if (size == 1) {
            if (((uint8_t)val >> (8 - count)) & 1) {
                x86_eflags_set(cpu, X86_EFLAGS_CF_MASK);
            } else {
                x86_eflags_clear(cpu, X86_EFLAGS_CF_MASK);
            }
        } else if (size == 2) {
            if (((uint16_t)val >> (16 - count)) & 1) {
                x86_eflags_set(cpu, X86_EFLAGS_CF_MASK);
            } else {
                x86_eflags_clear(cpu, X86_EFLAGS_CF_MASK);
            }
        } else {
            if ((val >> (32 - count)) & 1) {
                x86_eflags_set(cpu, X86_EFLAGS_CF_MASK);
            } else {
                x86_eflags_clear(cpu, X86_EFLAGS_CF_MASK);
            }
        }
    }

    if (mod == 3) {
        if (size == 1) x86_reg_write(cpu, rm, (uint8_t)result);
        else if (size == 2) x86_reg16_write(cpu, rm, (uint16_t)result);
        else x86_reg_write(cpu, rm, result);
    } else {
        uint32_t phys = x86_get_linear_address(cpu, instr, instr->modrm,
                                                  instr->sib, instr->addr_size);
        if (size == 1) x86_mem_write_byte(mem, phys, (uint8_t)result);
        else if (size == 2) x86_mem_write_word(mem, phys, (uint16_t)result);
        else x86_mem_write_dword(mem, phys, result);
    }
}

/*
 * SHR - Shift right (logical)
 *
 * Encoding:
 *   D0h/D1h/D3h r/m, 1/CL : SHR r/m, count
 *   C0h/C1h r/m, imm8     : SHR r/m, count
 */
static void exec_shr(x86_cpu_t *cpu, x86_memory_t *mem,
                     x86_instruction_t *instr) {
    uint8_t mod = (instr->modrm >> 6) & 0x03;
    uint8_t rm  = instr->modrm & 0x07;
    uint8_t size = instr->operand_size;

    uint32_t count;
    if (instr->modrm == 0xD2 || instr->modrm == 0xD3) {
        count = x86_reg_read(cpu, X86_REG_ECX) & 0x1F;
    } else if (instr->has_imm) {
        count = instr->immediate & 0x1F;
    } else {
        count = 1;
    }

    uint32_t val;
    if (mod == 3) {
        val = x86_reg_read(cpu, rm);
    } else {
        uint32_t phys = x86_get_linear_address(cpu, instr, instr->modrm,
                                                  instr->sib, instr->addr_size);
        if (size == 1) val = x86_mem_read_byte(mem, phys);
        else if (size == 2) val = x86_mem_read_word(mem, phys);
        else val = x86_mem_read_dword(mem, phys);
    }

    uint32_t result;
    if (size == 1) {
        result = ((uint8_t)val) >> count;
        x86_set_flags_from_result(cpu, result, X86_BYTE);
    } else if (size == 2) {
        result = ((uint16_t)val) >> count;
        x86_set_flags_from_result(cpu, result, X86_WORD);
    } else {
        result = val >> count;
        x86_set_flags_from_result(cpu, result, X86_DWORD);
    }

    /* CF = last bit shifted out */
    if (count > 0) {
        if (size == 1) {
            if (((uint8_t)val >> (count - 1)) & 1)
                x86_eflags_set(cpu, X86_EFLAGS_CF_MASK);
            else
                x86_eflags_clear(cpu, X86_EFLAGS_CF_MASK);
        } else if (size == 2) {
            if (((uint16_t)val >> (count - 1)) & 1)
                x86_eflags_set(cpu, X86_EFLAGS_CF_MASK);
            else
                x86_eflags_clear(cpu, X86_EFLAGS_CF_MASK);
        } else {
            if ((val >> (count - 1)) & 1)
                x86_eflags_set(cpu, X86_EFLAGS_CF_MASK);
            else
                x86_eflags_clear(cpu, X86_EFLAGS_CF_MASK);
        }
    }

    if (mod == 3) {
        if (size == 1) x86_reg_write(cpu, rm, (uint8_t)result);
        else if (size == 2) x86_reg16_write(cpu, rm, (uint16_t)result);
        else x86_reg_write(cpu, rm, result);
    } else {
        uint32_t phys = x86_get_linear_address(cpu, instr, instr->modrm,
                                                  instr->sib, instr->addr_size);
        if (size == 1) x86_mem_write_byte(mem, phys, (uint8_t)result);
        else if (size == 2) x86_mem_write_word(mem, phys, (uint16_t)result);
        else x86_mem_write_dword(mem, phys, result);
    }
}

/*
 * SAR - Shift right (arithmetic, preserves sign bit)
 *
 * Encoding:
 *   D0h/D1h/D3h r/m, 1/CL : SAR r/m, count
 *   C0h/C1h r/m, imm8     : SAR r/m, count
 */
static void exec_sar(x86_cpu_t *cpu, x86_memory_t *mem,
                     x86_instruction_t *instr) {
    uint8_t mod = (instr->modrm >> 6) & 0x03;
    uint8_t rm  = instr->modrm & 0x07;
    uint8_t size = instr->operand_size;

    uint32_t count;
    if (instr->modrm == 0xD2 || instr->modrm == 0xD3) {
        count = x86_reg_read(cpu, X86_REG_ECX) & 0x1F;
    } else if (instr->has_imm) {
        count = instr->immediate & 0x1F;
    } else {
        count = 1;
    }

    int32_t val;
    if (mod == 3) {
        val = (int32_t)x86_reg_read(cpu, rm);
    } else {
        uint32_t phys = x86_get_linear_address(cpu, instr, instr->modrm,
                                                  instr->sib, instr->addr_size);
        if (size == 1) val = (int8_t)x86_mem_read_byte(mem, phys);
        else if (size == 2) val = (int16_t)x86_mem_read_word(mem, phys);
        else val = (int32_t)x86_mem_read_dword(mem, phys);
    }

    int32_t result;
    if (size == 1) {
        result = (int8_t)val >> count;
        x86_set_flags_from_result(cpu, (uint32_t)result, X86_BYTE);
    } else if (size == 2) {
        result = (int16_t)val >> count;
        x86_set_flags_from_result(cpu, (uint32_t)result, X86_WORD);
    } else {
        result = (int32_t)val >> count;
        x86_set_flags_from_result(cpu, (uint32_t)result, X86_DWORD);
    }

    /* CF = last bit shifted out */
    if (count > 0) {
        if (size == 1) {
            if (((int8_t)val >> (count - 1)) & 1)
                x86_eflags_set(cpu, X86_EFLAGS_CF_MASK);
            else
                x86_eflags_clear(cpu, X86_EFLAGS_CF_MASK);
        } else if (size == 2) {
            if (((int16_t)val >> (count - 1)) & 1)
                x86_eflags_set(cpu, X86_EFLAGS_CF_MASK);
            else
                x86_eflags_clear(cpu, X86_EFLAGS_CF_MASK);
        } else {
            if (((int32_t)val >> (count - 1)) & 1)
                x86_eflags_set(cpu, X86_EFLAGS_CF_MASK);
            else
                x86_eflags_clear(cpu, X86_EFLAGS_CF_MASK);
        }
    }

    if (mod == 3) {
        if (size == 1) x86_reg_write(cpu, rm, (uint32_t)result);
        else if (size == 2) x86_reg16_write(cpu, rm, (uint16_t)result);
        else x86_reg_write(cpu, rm, (uint32_t)result);
    } else {
        uint32_t phys = x86_get_linear_address(cpu, instr, instr->modrm,
                                                  instr->sib, instr->addr_size);
        if (size == 1) x86_mem_write_byte(mem, phys, (uint8_t)result);
        else if (size == 2) x86_mem_write_word(mem, phys, (uint16_t)result);
        else x86_mem_write_dword(mem, phys, (uint32_t)result);
    }
}

/*
 * ROL - Rotate left
 *
 * Encoding:
 *   D0h/D1h/D3h r/m, 1/CL : ROL r/m, count
 */
static void exec_rol(x86_cpu_t *cpu, x86_memory_t *mem,
                     x86_instruction_t *instr) {
    uint8_t mod = (instr->modrm >> 6) & 0x03;
    uint8_t rm  = instr->modrm & 0x07;
    uint8_t size = instr->operand_size;

    uint32_t count;
    if (instr->modrm == 0xD2 || instr->modrm == 0xD3) {
        count = x86_reg_read(cpu, X86_REG_ECX) & 0x1F;
    } else if (instr->has_imm) {
        count = instr->immediate & 0x1F;
    } else {
        count = 1;
    }

    uint32_t val;
    if (mod == 3) {
        val = x86_reg_read(cpu, rm);
    } else {
        uint32_t phys = x86_get_linear_address(cpu, instr, instr->modrm,
                                                  instr->sib, instr->addr_size);
        if (size == 1) val = x86_mem_read_byte(mem, phys);
        else if (size == 2) val = x86_mem_read_word(mem, phys);
        else val = x86_mem_read_dword(mem, phys);
    }

    uint32_t result;
    if (size == 1) {
        result = ((uint8_t)val) << count | ((uint8_t)val) >> (8 - count);
        x86_set_flags_from_result(cpu, result, X86_BYTE);
    } else if (size == 2) {
        result = ((uint16_t)val) << count | ((uint16_t)val) >> (16 - count);
        x86_set_flags_from_result(cpu, result, X86_WORD);
    } else {
        result = val << count | val >> (32 - count);
        x86_set_flags_from_result(cpu, result, X86_DWORD);
    }

    /* CF = last bit rotated out */
    if (count > 0) {
        if (size == 1) {
            if (((uint8_t)val >> (8 - count)) & 1)
                x86_eflags_set(cpu, X86_EFLAGS_CF_MASK);
            else
                x86_eflags_clear(cpu, X86_EFLAGS_CF_MASK);
        } else if (size == 2) {
            if (((uint16_t)val >> (16 - count)) & 1)
                x86_eflags_set(cpu, X86_EFLAGS_CF_MASK);
            else
                x86_eflags_clear(cpu, X86_EFLAGS_CF_MASK);
        } else {
            if ((val >> (32 - count)) & 1)
                x86_eflags_set(cpu, X86_EFLAGS_CF_MASK);
            else
                x86_eflags_clear(cpu, X86_EFLAGS_CF_MASK);
        }
    }

    if (mod == 3) {
        if (size == 1) x86_reg_write(cpu, rm, (uint8_t)result);
        else if (size == 2) x86_reg16_write(cpu, rm, (uint16_t)result);
        else x86_reg_write(cpu, rm, result);
    } else {
        uint32_t phys = x86_get_linear_address(cpu, instr, instr->modrm,
                                                  instr->sib, instr->addr_size);
        if (size == 1) x86_mem_write_byte(mem, phys, (uint8_t)result);
        else if (size == 2) x86_mem_write_word(mem, phys, (uint16_t)result);
        else x86_mem_write_dword(mem, phys, result);
    }
}

/*
 * ROR - Rotate right
 *
 * Encoding:
 *   D0h/D1h/D3h r/m, 1/CL : ROR r/m, count
 */
static void exec_ror(x86_cpu_t *cpu, x86_memory_t *mem,
                     x86_instruction_t *instr) {
    uint8_t mod = (instr->modrm >> 6) & 0x03;
    uint8_t rm  = instr->modrm & 0x07;
    uint8_t size = instr->operand_size;

    uint32_t count;
    if (instr->modrm == 0xD2 || instr->modrm == 0xD3) {
        count = x86_reg_read(cpu, X86_REG_ECX) & 0x1F;
    } else if (instr->has_imm) {
        count = instr->immediate & 0x1F;
    } else {
        count = 1;
    }

    uint32_t val;
    if (mod == 3) {
        val = x86_reg_read(cpu, rm);
    } else {
        uint32_t phys = x86_get_linear_address(cpu, instr, instr->modrm,
                                                  instr->sib, instr->addr_size);
        if (size == 1) val = x86_mem_read_byte(mem, phys);
        else if (size == 2) val = x86_mem_read_word(mem, phys);
        else val = x86_mem_read_dword(mem, phys);
    }

    uint32_t result;
    if (size == 1) {
        result = ((uint8_t)val) >> count | ((uint8_t)val) << (8 - count);
        x86_set_flags_from_result(cpu, result, X86_BYTE);
    } else if (size == 2) {
        result = ((uint16_t)val) >> count | ((uint16_t)val) << (16 - count);
        x86_set_flags_from_result(cpu, result, X86_WORD);
    } else {
        result = val >> count | val << (32 - count);
        x86_set_flags_from_result(cpu, result, X86_DWORD);
    }

    /* CF = last bit rotated out */
    if (count > 0) {
        if (size == 1) {
            if (((uint8_t)val >> (count - 1)) & 1)
                x86_eflags_set(cpu, X86_EFLAGS_CF_MASK);
            else
                x86_eflags_clear(cpu, X86_EFLAGS_CF_MASK);
        } else if (size == 2) {
            if (((uint16_t)val >> (count - 1)) & 1)
                x86_eflags_set(cpu, X86_EFLAGS_CF_MASK);
            else
                x86_eflags_clear(cpu, X86_EFLAGS_CF_MASK);
        } else {
            if ((val >> (count - 1)) & 1)
                x86_eflags_set(cpu, X86_EFLAGS_CF_MASK);
            else
                x86_eflags_clear(cpu, X86_EFLAGS_CF_MASK);
        }
    }

    if (mod == 3) {
        if (size == 1) x86_reg_write(cpu, rm, (uint8_t)result);
        else if (size == 2) x86_reg16_write(cpu, rm, (uint16_t)result);
        else x86_reg_write(cpu, rm, result);
    } else {
        uint32_t phys = x86_get_linear_address(cpu, instr, instr->modrm,
                                                  instr->sib, instr->addr_size);
        if (size == 1) x86_mem_write_byte(mem, phys, (uint8_t)result);
        else if (size == 2) x86_mem_write_word(mem, phys, (uint16_t)result);
        else x86_mem_write_dword(mem, phys, result);
    }
}

/* ============================================================
 * CONTROL FLOW INSTRUCTIONS
 * ============================================================ */

/*
 * JMP - Unconditional jump
 *
 * Encoding:
 *   EB rel8  : JMP short (relative, -128 to +127)
 *   E9 rel16/32 : JMP near (relative)
 *   EA seg:off : JMP far
 */
static void exec_jmp(x86_cpu_t *cpu, x86_memory_t *mem,
                     x86_instruction_t *instr) {
    (void)mem;
    int32_t disp;

    if (instr->opcode == 0xEB) {
        /* Short jump: sign-extended 8-bit displacement */
        disp = (int8_t)instr->immediate;
    } else if (instr->opcode == 0xE9 || instr->opcode == 0x0F) {
        /* Near jump: sign-extended displacement */
        if (instr->opcode == 0x0F) {
            /* Two-byte opcode JMP */
            disp = (int32_t)(int8_t)instr->immediate;
        } else {
            disp = (int32_t)(int32_t)instr->immediate;
        }
    } else {
        return;
    }

    cpu->eip += disp;
}

/*
 * JE/JZ - Jump if equal/zero (ZF=1)
 * JNE/JNZ - Jump if not equal/zero (ZF=0)
 * JL/JNGE - Jump if less (SF != OF)
 * JG/JNLE - Jump if greater ((SF == OF) && ZF == 0)
 * JB/JC   - Jump if below/carry (CF=1)
 * JNB/JNC - Jump if not below/no carry (CF=0)
 *
 * These use the same encoding as JMP but with condition codes.
 */
static void exec_jcc(x86_cpu_t *cpu, x86_memory_t *mem,
                     x86_instruction_t *instr) {
    (void)mem;
    uint8_t condition = instr->opcode & 0x0F;
    int32_t disp;

    if (instr->opcode == 0xEB || (instr->opcode >= 0x0F && instr->opcode < 0x10)) {
        disp = (int8_t)instr->immediate;
    } else {
        disp = (int32_t)(int32_t)instr->immediate;
    }

    if (x86_check_condition(cpu, condition)) {
        cpu->eip += disp;
    }
}

/*
 * CALL - Call subroutine
 *
 * Encoding:
 *   E8 rel16/32 : CALL near (pushes return address, jumps relative)
 *   FFh/2       : CALL near (indirect)
 */
static void exec_call(x86_cpu_t *cpu, x86_memory_t *mem,
                      x86_instruction_t *instr) {
    (void)mem;
    uint32_t ret_addr = cpu->eip + (instr->has_imm ? instr->has_imm : 1);

    if (instr->opcode == 0xE8) {
        /* Relative call */
        int32_t disp = (int32_t)(int32_t)instr->immediate;
        x86_stack_push(cpu, mem, ret_addr);
        cpu->eip += disp;
    } else if (instr->opcode == 0xFF && ((instr->modrm >> 3) & 0x07) == 2) {
        /* Indirect call */
        uint8_t mod = (instr->modrm >> 6) & 0x03;
        uint8_t rm  = instr->modrm & 0x07;
        uint32_t target;

        if (mod == 3) {
            target = x86_reg_read(cpu, rm);
        } else {
            uint32_t phys = x86_get_linear_address(cpu, instr, instr->modrm,
                                                      instr->sib, instr->addr_size);
            target = x86_mem_read_dword(mem, phys);
        }
        x86_stack_push(cpu, mem, ret_addr);
        cpu->eip = target;
    }
}

/*
 * RET - Return from call
 *
 * Encoding:
 *   C3        : RET (near)
 *   C2 imm16  : RET imm16 (near, pop n bytes from stack)
 */
static void exec_ret(x86_cpu_t *cpu, x86_memory_t *mem,
                     x86_instruction_t *instr) {
    (void)mem;
    uint32_t ret_addr = x86_stack_pop(cpu, mem);
    cpu->eip = ret_addr;

    /* If there's an immediate operand, add to ESP (cleanup stack) */
    if (instr->has_imm) {
        cpu->regs[X86_REG_ESP] += instr->immediate;
    }
}

/* ============================================================
 * STRING INSTRUCTIONS
 * ============================================================ */

/*
 * MOVSB - Move string byte/word
 *   Copy from DS:ESI to ES:EDI, increment/decrement ESI/EDI
 *
 * Encoding:
 *   A4        : MOVSB (byte)
 *   A5        : MOVSW/MOVSD (word/dword)
 */
static void exec_movsb(x86_cpu_t *cpu, x86_memory_t *mem,
                       x86_instruction_t *instr) {
    (void)instr;
    int dir = x86_dir_flag(cpu);
    uint8_t size = instr->operand_size;

    uint32_t src_phys = x86_translate_address(cpu, cpu->seg_regs[X86_SEG_DS],
                                                cpu->regs[X86_REG_ESI]);
    uint32_t dst_phys = x86_translate_address(cpu, cpu->seg_regs[X86_SEG_ES],
                                                cpu->regs[X86_REG_EDI]);

    if (size == 1) {
        uint8_t val = x86_mem_read_byte(mem, src_phys);
        x86_mem_write_byte(mem, dst_phys, val);
    } else if (size == 2) {
        uint16_t val = x86_mem_read_word(mem, src_phys);
        x86_mem_write_word(mem, dst_phys, val);
    } else {
        uint32_t val = x86_mem_read_dword(mem, src_phys);
        x86_mem_write_dword(mem, dst_phys, val);
    }

    cpu->regs[X86_REG_ESI] += dir * (uint32_t)size;
    cpu->regs[X86_REG_EDI] += dir * (uint32_t)size;
}

/*
 * CMPSB - Compare string byte/word
 *   Compare DS:ESI with ES:EDI, set flags, increment/decrement
 *
 * Encoding:
 *   A6        : CMPSB (byte)
 *   A7        : CMPSW/CMPSD (word/dword)
 */
static void exec_cmpsb(x86_cpu_t *cpu, x86_memory_t *mem,
                       x86_instruction_t *instr) {
    (void)mem;
    int dir = x86_dir_flag(cpu);
    uint8_t size = instr->operand_size;

    uint32_t src_phys = x86_translate_address(cpu, cpu->seg_regs[X86_SEG_DS],
                                                cpu->regs[X86_REG_ESI]);
    uint32_t dst_phys = x86_translate_address(cpu, cpu->seg_regs[X86_SEG_ES],
                                                cpu->regs[X86_REG_EDI]);

    uint32_t val1, val2;
    if (size == 1) {
        val1 = x86_mem_read_byte(mem, src_phys);
        val2 = x86_mem_read_byte(mem, dst_phys);
    } else if (size == 2) {
        val1 = x86_mem_read_word(mem, src_phys);
        val2 = x86_mem_read_word(mem, dst_phys);
    } else {
        val1 = x86_mem_read_dword(mem, src_phys);
        val2 = x86_mem_read_dword(mem, dst_phys);
    }

    if (size == 1) {
        x86_set_flags_signed(cpu, (int8_t)val1, (int8_t)val2, X86_BYTE);
    } else if (size == 2) {
        x86_set_flags_signed(cpu, (int16_t)val1, (int16_t)val2, X86_WORD);
    } else {
        x86_set_flags_signed(cpu, (int32_t)val1, (int32_t)val2, X86_DWORD);
    }

    cpu->regs[X86_REG_ESI] += dir * (uint32_t)size;
    cpu->regs[X86_REG_EDI] += dir * (uint32_t)size;
}

/*
 * LODSB - Load string byte/word
 *   Copy from DS:ESI to AL/EAX, increment/decrement ESI
 *
 * Encoding:
 *   AC        : LODSB (byte)
 *   AD        : LODSW/LODSD (word/dword)
 */
static void exec_lodsb(x86_cpu_t *cpu, x86_memory_t *mem,
                       x86_instruction_t *instr) {
    (void)instr;
    int dir = x86_dir_flag(cpu);
    uint8_t size = instr->operand_size;

    uint32_t src_phys = x86_translate_address(cpu, cpu->seg_regs[X86_SEG_DS],
                                                cpu->regs[X86_REG_ESI]);

    if (size == 1) {
        x86_reg_write(cpu, X86_REG_EAX, x86_mem_read_byte(mem, src_phys));
    } else if (size == 2) {
        x86_reg16_write(cpu, X86_REG_EAX, x86_mem_read_word(mem, src_phys));
    } else {
        x86_reg_write(cpu, X86_REG_EAX, x86_mem_read_dword(mem, src_phys));
    }

    cpu->regs[X86_REG_ESI] += dir * (uint32_t)size;
}

/*
 * STOSB - Store string byte/word
 *   Copy AL/EAX to ES:EDI, increment/decrement EDI
 *
 * Encoding:
 *   AE        : STOSB (byte)
 *   AF        : STOSW/STOSD (word/dword)
 */
static void exec_stosb(x86_cpu_t *cpu, x86_memory_t *mem,
                       x86_instruction_t *instr) {
    (void)instr;
    int dir = x86_dir_flag(cpu);
    uint8_t size = instr->operand_size;

    uint32_t dst_phys = x86_translate_address(cpu, cpu->seg_regs[X86_SEG_ES],
                                                cpu->regs[X86_REG_EDI]);
    uint32_t val = x86_reg_read(cpu, X86_REG_EAX);

    if (size == 1) {
        x86_mem_write_byte(mem, dst_phys, (uint8_t)val);
    } else if (size == 2) {
        x86_mem_write_word(mem, dst_phys, (uint16_t)val);
    } else {
        x86_mem_write_dword(mem, dst_phys, val);
    }

    cpu->regs[X86_REG_EDI] += dir * (uint32_t)size;
}

/* ============================================================
 * INTERRUPT INSTRUCTIONS
 * ============================================================ */

/*
 * INT - Software interrupt
 *
 * Encoding:
 *   CD imm8 : INT imm8
 *
 * x86 interrupt handling:
 *   1. Push EFLAGS
 *   2. Clear IF and TF flags
 *   3. Push CS
 *   4. Push EIP
 *   5. Load EIP from interrupt vector table at vector * 4
 */
static void exec_int(x86_cpu_t *cpu, x86_memory_t *mem,
                     x86_instruction_t *instr) {
    uint8_t vector = instr->immediate;

    /* Push EFLAGS and clear IF, TF */
    x86_stack_push(cpu, mem, cpu->eflags);
    x86_eflags_clear(cpu, X86_EFLAGS_IF_MASK);
    x86_eflags_clear(cpu, 0x00000100); /* TF bit */

    /* Push CS */
    x86_stack_push(cpu, mem, cpu->seg_regs[X86_SEG_CS]);

    /* Push EIP (return address) */
    x86_stack_push(cpu, mem, cpu->eip);

    /* Get interrupt vector from IDT */
    uint32_t idt_entry = x86_mem_read_dword(mem, cpu->idtr_base + vector * 4);
    uint32_t idt_entry2 = x86_mem_read_dword(mem, cpu->idtr_base + vector * 4 + 4);
    uint32_t target = idt_entry | ((uint32_t)(idt_entry2 & 0xFFFF) << 16);

    cpu->eip = target;
}

/* INT3 - Breakpoint interrupt */
static void exec_int3(x86_cpu_t *cpu, x86_memory_t *mem,
                      x86_instruction_t *instr) {
    (void)mem;
    (void)instr;
    cpu->interrupt_pending = true;
    cpu->interrupt_vector = X86_INT3_VECTOR;
}

/* IRET - Interrupt return */
static void exec_iret(x86_cpu_t *cpu, x86_memory_t *mem,
                      x86_instruction_t *instr) {
    (void)mem;
    (void)instr;
    /* Pop EIP, CS, EFLAGS */
    uint32_t ret_eip = x86_stack_pop(cpu, mem);
    uint16_t ret_cs = (uint16_t)x86_stack_pop(cpu, mem);
    uint32_t ret_eflags = x86_stack_pop(cpu, mem);

    cpu->eip = ret_eip;
    cpu->seg_regs[X86_SEG_CS] = ret_cs;
    cpu->eflags = ret_eflags;
}

/* ============================================================
 * SYSTEM INSTRUCTIONS
 * ============================================================ */

/*
 * LGDT - Load GDT pointer
 *
 * Encoding:
 *   0F 01h/0 : LGDT r/m
 */
static void exec_lgdt(x86_cpu_t *cpu, x86_memory_t *mem,
                      x86_instruction_t *instr) {
    uint8_t mod = (instr->modrm >> 6) & 0x03;
    uint32_t phys;

    if (mod == 3) {
        /* From registers (not typical) */
        return;
    }

    phys = x86_get_linear_address(cpu, instr, instr->modrm,
                                   instr->sib, instr->addr_size);
    cpu->gdtr_limit = x86_mem_read_word(mem, phys);
    cpu->gdtr_base = x86_mem_read_dword(mem, phys + 2);
}

/*
 * LIDT - Load IDT pointer
 *
 * Encoding:
 *   0F 01h/1 : LIDT r/m
 */
static void exec_lidt(x86_cpu_t *cpu, x86_memory_t *mem,
                      x86_instruction_t *instr) {
    uint8_t mod = (instr->modrm >> 6) & 0x03;
    uint32_t phys;

    if (mod == 3) {
        return;
    }

    phys = x86_get_linear_address(cpu, instr, instr->modrm,
                                   instr->sib, instr->addr_size);
    cpu->idtr_limit = x86_mem_read_word(mem, phys);
    cpu->idtr_base = x86_mem_read_dword(mem, phys + 2);
}

/*
 * SETCC - Set byte on condition
 *
 * Encoding:
 *   90h+condition r/m8 : SETcc r/m8
 */
static void exec_setcc(x86_cpu_t *cpu, x86_memory_t *mem,
                       x86_instruction_t *instr) {
    uint8_t mod = (instr->modrm >> 6) & 0x03;
    uint8_t rm  = instr->modrm & 0x07;
    uint8_t condition = instr->opcode & 0x0F;
    uint8_t val = x86_check_condition(cpu, condition) ? 1 : 0;

    if (mod == 3) {
        x86_reg_write(cpu, rm, val);
    } else {
        uint32_t phys = x86_get_linear_address(cpu, instr, instr->modrm,
                                                  instr->sib, instr->addr_size);
        x86_mem_write_byte(mem, phys, val);
    }
}

/* NOP - No operation */
static void exec_nop(x86_cpu_t *cpu, x86_memory_t *mem,
                     x86_instruction_t *instr) {
    (void)cpu;
    (void)mem;
    (void)instr;
}

/*
 * Execute a decoded instruction.
 *
 * This is the main dispatch function that routes to the
 * appropriate execution function based on the opcode.
 */
int x86_execute_instruction(x86_cpu_t *cpu, x86_memory_t *mem,
                            x86_instruction_t *instr) {
    cpu->instruction_count++;

    if (!cpu->running) {
        return X86_ERROR;
    }

    /* Handle interrupt before executing next instruction */
    if (cpu->interrupt_pending) {
        /* Invoke the interrupt handler */
        uint32_t vec = cpu->interrupt_vector;
        uint32_t handler = x86_mem_read_dword(mem, cpu->idtr_base + vec * 4) |
                           ((uint32_t)(x86_mem_read_byte(mem, cpu->idtr_base + vec * 4 + 4)) << 8) |
                           ((uint32_t)(x86_mem_read_byte(mem, cpu->idtr_base + vec * 4 + 5)) << 16) |
                           ((uint32_t)(x86_mem_read_byte(mem, cpu->idtr_base + vec * 4 + 6)) << 24);
        cpu->eip = handler;
        cpu->interrupt_pending = false;
        return X86_TRAP;
    }

    /* Dispatch based on opcode */
    uint8_t opcode = instr->opcode;
    uint8_t modrm = instr->has_modrm ? instr->modrm : 0;
    uint8_t mod = (modrm >> 6) & 0x03;

    /* Two-byte opcode */
    if (opcode >= 0x100) {
        uint8_t secondary = (uint8_t)(opcode - 0x100);
        switch (secondary) {
            case 0x01: /* LGDT/LIDT */
                if ((modrm & 0x38) >> 3 == 0) exec_lgdt(cpu, mem, instr);
                else exec_lidt(cpu, mem, instr);
                break;
            case 0x40: /* CMOVcc */
                /* Not fully implemented in this basic simulator */
                break;
            case 0x82: /* JMP rel8 in two-byte table */
                exec_jmp(cpu, mem, instr);
                break;
            case 0xA3: /* BT */
                /* Bit test - not fully implemented */
                break;
            case 0xA4: /* SHLD */
                /* Shift left double - not fully implemented */
                break;
            case 0xA5: /* SHRD */
                /* Shift right double - not fully implemented */
                break;
            case 0xA7: /* CMPXCHG */
                /* Compare and exchange - not fully implemented */
                break;
            case 0xAF: /* IMUL */
                /* Integer multiply - not fully implemented */
                break;
            case 0xB6: /* MOVZX */
                /* Move with zero-extend - not fully implemented */
                break;
            case 0xB7: /* MOVSX */
                /* Move with sign-extend - not fully implemented */
                break;
            case 0xBC: /* BSF */
                /* Bit scan forward - not fully implemented */
                break;
            case 0xBD: /* BSR */
                /* Bit scan reverse - not fully implemented */
                break;
            default:
                break;
        }
        return X86_OK;
    }

    /* Primary opcode dispatch table */
    switch (opcode) {
        /* Group 1: ADD, OR, ADC, SBB, AND, SUB, XOR, CMP (00-05, 08-0D, 10-15, 20-25, 28-2D, 30-35) */
        case 0x00: case 0x01: /* ADD r/m, r */
            exec_add(cpu, mem, instr);
            break;
        case 0x08: case 0x09: /* OR r/m, r */
            exec_or(cpu, mem, instr);
            break;
        case 0x20: case 0x21: /* AND r/m, r */
            exec_and(cpu, mem, instr);
            break;
        case 0x28: case 0x29: /* SUB r/m, r */
            exec_sub(cpu, mem, instr);
            break;
        case 0x30: case 0x31: /* XOR r/m, r */
            exec_xor(cpu, mem, instr);
            break;
        case 0x38: case 0x39: /* CMP r/m, r */
            exec_cmp(cpu, mem, instr);
            break;

        /* PUSH group (50-57) */
        case 0x50: case 0x51: case 0x52: case 0x53:
        case 0x54: case 0x55: case 0x56: case 0x57:
            exec_push(cpu, mem, instr);
            break;

        /* POP group (58-5F) */
        case 0x58: case 0x59: case 0x5A: case 0x5B:
        case 0x5C: case 0x5D: case 0x5E: case 0x5F:
            exec_pop(cpu, mem, instr);
            break;

        /* INC/DEC reg (40-47, 48-4F) */
        case 0x40: case 0x41: case 0x42: case 0x43:
        case 0x44: case 0x45: case 0x46: case 0x47:
            exec_inc(cpu, mem, instr);
            break;
        case 0x48: case 0x49: case 0x4A: case 0x4B:
        case 0x4C: case 0x4D: case 0x4E: case 0x4F:
            exec_dec(cpu, mem, instr);
            break;

        /* MOV reg, imm8/imm32 (B0-BF) */
        case 0xB0: case 0xB1: case 0xB2: case 0xB3:
        case 0xB4: case 0xB5: case 0xB6: case 0xB7:
            /* MOV r8, imm8 */
            x86_reg_write(cpu, opcode & 0x07, (uint8_t)x86_instr_read_byte(
                (x86_instr_stream_t*)0)); /* placeholder */
            break;

        /* MOV r/m8, r8 (88) */
        case 0x88:
            exec_mov(cpu, mem, instr);
            break;
        /* MOV r/m16/32, r (89) */
        case 0x89:
            exec_mov(cpu, mem, instr);
            break;
        /* MOV r8, r/m8 (8A) */
        case 0x8A:
            exec_mov(cpu, mem, instr);
            break;
        /* MOV r16/32, r/m (8B) */
        case 0x8B:
            exec_mov(cpu, mem, instr);
            break;

        /* XCHG (90-97) */
        case 0x90: /* NOP or XCHG EAX, EAX */
            exec_nop(cpu, mem, instr);
            break;
        case 0x91: case 0x92: case 0x93: case 0x94:
        case 0x95: case 0x96: case 0x97:
            exec_xchg(cpu, mem, instr);
            break;

        /* MOV r/m, imm (C6-C7) */
        case 0xC6:
            exec_mov(cpu, mem, instr);
            break;
        case 0xC7:
            exec_mov(cpu, mem, instr);
            break;

        /* RET (C2, C3) */
        case 0xC2:
            exec_ret(cpu, mem, instr);
            break;
        case 0xC3:
            exec_ret(cpu, mem, instr);
            break;

        /* INT (CD) */
        case 0xCD:
            exec_int(cpu, mem, instr);
            break;

        /* INT3 (CC) */
        case 0xCC:
            exec_int3(cpu, mem, instr);
            break;

        /* IRET (CF) */
        case 0xCF:
            exec_iret(cpu, mem, instr);
            break;

        /* JMP short (EB) */
        case 0xEB:
            exec_jmp(cpu, mem, instr);
            break;

        /* JMP near (E9) */
        case 0xE9:
            exec_jmp(cpu, mem, instr);
            break;

        /* CALL near (E8) */
        case 0xE8:
            exec_call(cpu, mem, instr);
            break;

        /* SHL/SAR/SHR/ROL/ROR (C0, C1, D0-D3) */
        case 0xC0: case 0xC1:
            if ((modrm >> 3) & 0x07 == 4) exec_shl(cpu, mem, instr);
            else if ((modrm >> 3) & 0x07 == 5) exec_sar(cpu, mem, instr);
            else if ((modrm >> 3) & 0x07 == 6) exec_shr(cpu, mem, instr);
            else if ((modrm >> 3) & 0x07 == 0) exec_rol(cpu, mem, instr);
            else if ((modrm >> 3) & 0x07 == 1) exec_ror(cpu, mem, instr);
            else if ((modrm >> 3) & 0x07 == 2) exec_sar(cpu, mem, instr);
            else if ((modrm >> 3) & 0x07 == 3) exec_ror(cpu, mem, instr);
            else exec_shl(cpu, mem, instr);
            break;

        case 0xD0: case 0xD1: case 0xD2: case 0xD3:
            if ((modrm >> 3) & 0x07 == 4) exec_shl(cpu, mem, instr);
            else if ((modrm >> 3) & 0x07 == 5) exec_sar(cpu, mem, instr);
            else if ((modrm >> 3) & 0x07 == 6) exec_shr(cpu, mem, instr);
            else if ((modrm >> 3) & 0x07 == 0) exec_rol(cpu, mem, instr);
            else if ((modrm >> 3) & 0x07 == 1) exec_ror(cpu, mem, instr);
            else if ((modrm >> 3) & 0x07 == 2) exec_sar(cpu, mem, instr);
            else if ((modrm >> 3) & 0x07 == 3) exec_ror(cpu, mem, instr);
            else exec_shl(cpu, mem, instr);
            break;

        /* MUL (F6/4), DIV (F6/6) */
        case 0xF6:
            if ((modrm >> 3) & 0x07 == 4) exec_mul(cpu, mem, instr);
            else if ((modrm >> 3) & 0x07 == 5) exec_div(cpu, mem, instr);
            else if ((modrm >> 3) & 0x07 == 2) exec_not(cpu, mem, instr);
            else exec_and(cpu, mem, instr); /* TEST */
            break;

        /* MUL (F7/4), DIV (F7/6) */
        case 0xF7:
            if ((modrm >> 3) & 0x07 == 4) exec_mul(cpu, mem, instr);
            else if ((modrm >> 3) & 0x07 == 5) exec_div(cpu, mem, instr);
            else if ((modrm >> 3) & 0x07 == 2) exec_not(cpu, mem, instr);
            else exec_and(cpu, mem, instr); /* TEST */
            break;

        /* LEA (8D) */
        case 0x8D:
            /* Load effective address - not fully implemented */
            break;

        /* MOVSB/A4, CMPSB/A6, LODSB/AC, STOSB/AE */
        case 0xA4: exec_movsb(cpu, mem, instr); break;
        case 0xA5: exec_movsb(cpu, mem, instr); break;
        case 0xA6: exec_cmpsb(cpu, mem, instr); break;
        case 0xA7: exec_cmpsb(cpu, mem, instr); break;
        case 0xAC: exec_lodsb(cpu, mem, instr); break;
        case 0xAD: exec_lodsb(cpu, mem, instr); break;
        case 0xAE: exec_stosb(cpu, mem, instr); break;
        case 0xAF: exec_stosb(cpu, mem, instr); break;

        /* PUSH imm (68), PUSH imm8 (6A) */
        case 0x68:
            exec_push(cpu, mem, instr);
            break;
        case 0x6A:
            exec_push(cpu, mem, instr);
            break;

        /* Default: NOP for unimplemented instructions */
        default:
            exec_nop(cpu, mem, instr);
            break;
    }

    return X86_OK;
}
