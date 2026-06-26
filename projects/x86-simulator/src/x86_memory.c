#include "x86_memory.h"
#include <string.h>
#include <stdio.h>

/* ============================================================
 * x86_memory.c - Memory management and address translation
 *
 * x86 uses segmented memory architecture:
 *
 * REAL MODE ADDRESS CALCULATION:
 *   Physical = (SegmentSelector << 4) + Offset
 *   This is because segment registers hold 20-bit base values
 *   shifted left by 4 bits (the "segment << 4" formula).
 *
 * PROTECTED MODE ADDRESS CALCULATION:
 *   Linear = SegmentBase + Offset (from GDT descriptor)
 *   Physical = Linear (if paging disabled)
 *
 * STACK:
 *   Stack grows downward. PUSH decrements ESP, POP increments ESP.
 *   Stack segment is SS (segment register index 2).
 *
 * ENDIANNESS:
 *   x86 is little-endian: least significant byte first.
 *   Word 0x1234 stored as: [low] 0x34, 0x12 [high]
 * ============================================================ */

void x86_mem_init(x86_memory_t *mem) {
    memset(mem->data, 0, MEM_SIZE);
    mem->size = MEM_SIZE;
}

/* Read a byte from physical memory */
uint8_t x86_mem_read_byte(x86_memory_t *mem, uint32_t address) {
    if (address < mem->size) {
        return mem->data[address];
    }
    printf("[WARN] Read out of bounds: 0x%08X (size=0x%X)\n", address, mem->size);
    return 0xFF;
}

/* Read a 16-bit word from physical memory (little-endian) */
uint16_t x86_mem_read_word(x86_memory_t *mem, uint32_t address) {
    if (address + 1 < mem->size) {
        return (uint16_t)(mem->data[address] |
                          (mem->data[address + 1] << 8));
    }
    printf("[WARN] Word read out of bounds: 0x%08X\n", address);
    return 0xFFFF;
}

/* Read a 32-bit dword from physical memory (little-endian) */
uint32_t x86_mem_read_dword(x86_memory_t *mem, uint32_t address) {
    if (address + 3 < mem->size) {
        return (uint32_t)(mem->data[address] |
                          (mem->data[address + 1] << 8) |
                          (mem->data[address + 2] << 16) |
                          (mem->data[address + 3] << 24));
    }
    printf("[WARN] DWord read out of bounds: 0x%08X\n", address);
    return 0xFFFFFFFF;
}

/* Write a byte to physical memory */
void x86_mem_write_byte(x86_memory_t *mem, uint32_t address, uint8_t value) {
    if (address < mem->size) {
        mem->data[address] = value;
    } else {
        printf("[WARN] Write out of bounds: 0x%08X = 0x%02X\n", address, value);
    }
}

/* Write a 16-bit word to physical memory (little-endian) */
void x86_mem_write_word(x86_memory_t *mem, uint32_t address, uint16_t value) {
    if (address + 1 < mem->size) {
        mem->data[address]     = (uint8_t)(value & 0xFF);
        mem->data[address + 1] = (uint8_t)((value >> 8) & 0xFF);
    } else {
        printf("[WARN] Word write out of bounds: 0x%08X = 0x%04X\n", address, value);
    }
}

/* Write a 32-bit dword to physical memory (little-endian) */
void x86_mem_write_dword(x86_memory_t *mem, uint32_t address, uint32_t value) {
    if (address + 3 < mem->size) {
        mem->data[address]     = (uint8_t)(value & 0xFF);
        mem->data[address + 1] = (uint8_t)((value >> 8) & 0xFF);
        mem->data[address + 2] = (uint8_t)((value >> 16) & 0xFF);
        mem->data[address + 3] = (uint8_t)((value >> 24) & 0xFF);
    } else {
        printf("[WARN] DWord write out of bounds: 0x%08X = 0x%08X\n", address, value);
    }
}

/*
 * Translate segment:offset to physical/linear address.
 *
 * In real mode: physical = (segment << 4) + offset
 * In protected mode: linear = segment_base + offset
 *
 * The segment base comes from the segment state (descriptor cache).
 */
uint32_t x86_translate_address(x86_cpu_t *cpu, uint16_t segment, uint32_t offset) {
    uint32_t base;

    if (cpu->mode == MODE_REAL) {
        /* Real mode: base = selector << 4 */
        base = (uint32_t)segment << 4;
    } else {
        /* Protected mode: look up segment base from descriptor cache */
        /* For simplicity, we use the selector as the index to find the segment */
        base = cpu->seg_state[segment & 0x07].base;
    }

    return base + offset;
}

/*
 * Get the effective linear address from MOD/RM/SIB byte decoding.
 *
 * MOD/RM byte format (80x86):
 *   Bits 7-6 (MOD):   Mod addressing mode
 *                      00 = memory, 01 = disp8+reg, 10 = disp16/32+reg, 11 = reg
 *   Bits 5-3 (REG):    Register field (opcode extension)
 *   Bits 2-0 (R/M):    Register or memory addressing mode
 *
 * SIB byte format (when R/M = 100):
 *   Bits 7-5 (SCALE):  Scale factor (1, 2, 4, 8)
 *   Bits 4-2 (INDEX):  Index register
 *   Bits 1-0 (BASE):   Base register
 *
 * Addressing modes (R/M field):
 *   000: [base + disp]  (or [eax] if MOD=11)
 *   001: [base + disp8]
 *   010: [base + disp16/32]
 *   011: [disp16/32]
 *   100: [base + index*scale + disp] (SIB byte follows)
 *   101: [disp16/32] (or EIP-relative in 32-bit mode)
 *   110: [base + disp16/32]
 *   111: register (not memory)
 */
uint32_t x86_get_linear_address(x86_cpu_t *cpu, x86_instruction_t *instr,
                                 uint8_t modrm, uint8_t sib, uint8_t addr_size) {
    uint8_t mod = (modrm >> 6) & 0x03;
    uint8_t rm  = modrm & 0x07;

    uint32_t disp = 0;
    uint32_t base_reg = 0;
    uint32_t index_reg = 0;
    uint8_t scale = 1;

    /* Determine default segment */
    uint16_t default_seg;
    if (addr_size == 32) {
        /* In 32-bit mode, default segment for [esp]/[ebp] is SS, others DS */
        if (rm == 4 && mod != 3) {
            /* SIB byte or [ebp] -> check base */
            if (sib & 0x07 == 5 && mod != 3) {
                /* [ebp + disp] -> DS */
                default_seg = cpu->seg_regs[X86_SEG_DS];
            } else {
                default_seg = cpu->seg_regs[X86_SEG_SS];
            }
        } else if (rm == 5 && mod != 3) {
            default_seg = cpu->seg_regs[X86_SEG_DS];
        } else {
            default_seg = cpu->seg_regs[X86_SEG_DS];
        }
    } else {
        default_seg = cpu->seg_regs[X86_SEG_DS];
    }

    /* Apply segment override if present */
    if (instr->has_seg_override) {
        default_seg = instr->seg_override;
    }

    if (mod == 3) {
        /* MOD=11: register mode, not memory */
        return 0;
    }

    if (addr_size == 32) {
        /* 32-bit addressing */
        if (rm == 4) {
            /* SIB byte follows */
            uint8_t sc = (sib >> 6) & 0x03;
            uint8_t idx = (sib >> 3) & 0x07;
            uint8_t bas = sib & 0x07;

            scale = (1 << sc);
            index_reg = idx;
            base_reg = bas;

            if (bas == 5 && mod == 0) {
                /* [index*scale + disp32] */
                disp = instr->displacement;
                base_reg = 0;
            } else if (bas == 5 && mod == 1) {
                /* [index*scale + disp8] - sign extended */
                disp = (int8_t)instr->displacement;
            } else if (bas == 5 && mod == 2) {
                disp = instr->displacement;
            }
        } else if (rm == 5) {
            /* [disp32] or EIP-relative */
            if (mod == 0) {
                disp = instr->displacement;
            } else if (mod == 1) {
                disp = (int8_t)(uint8_t)instr->displacement;
            } else {
                disp = instr->displacement;
            }
        } else {
            /* [base_reg] or [base_reg + disp] */
            base_reg = rm;
            if (mod == 1) {
                disp = (int8_t)(uint8_t)instr->displacement;
            } else if (mod == 2) {
                disp = instr->displacement;
            }
        }
    } else {
        /* 16-bit addressing */
        switch (rm) {
            case 0: base_reg = 0; break;   /* [bx + si] */
            case 1: base_reg = 1; break;   /* [bx + di] */
            case 2: base_reg = 2; break;   /* [bp + si] */
            case 3: base_reg = 3; break;   /* [bp + di] */
            case 4: base_reg = 4; break;   /* [si] */
            case 5: base_reg = 5; break;   /* [di] */
            case 6: base_reg = 6; break;   /* [bp] */
            case 7: base_reg = 7; break;   /* [bx] */
        }
        if (mod == 1) {
            disp = (int8_t)(uint8_t)instr->displacement;
        } else if (mod == 2) {
            disp = instr->displacement;
        }
    }

    uint32_t offset;
    if (addr_size == 32) {
        uint32_t base_val = (base_reg < X86_REG_MAX) ? x86_reg_read(cpu, base_reg) : 0;
        uint32_t idx_val  = (index_reg < X86_REG_MAX) ? x86_reg_read(cpu, index_reg) : 0;
        offset = base_val + (idx_val * scale) + disp;
    } else {
        uint16_t base_val = (base_reg < X86_REG_MAX) ? x86_reg16_read(cpu, base_reg) : 0;
        uint16_t idx_val  = (index_reg < X86_REG_MAX) ? x86_reg16_read(cpu, index_reg) : 0;
        offset = base_val + idx_val + (uint16_t)disp;
    }

    return x86_translate_address(cpu, default_seg, offset);
}

/* Read word from segment:offset */
uint16_t x86_mem_read_word_seg(x86_memory_t *mem, x86_cpu_t *cpu,
                                  uint16_t segment, uint16_t offset) {
    uint32_t phys = x86_translate_address(cpu, segment, (uint32_t)offset);
    return x86_mem_read_word(mem, phys);
}

/* Read dword from segment:offset */
uint32_t x86_mem_read_dword_seg(x86_cpu_t *cpu, x86_cpu_t *cpu2,
                                   uint16_t segment, uint32_t offset) {
    (void)cpu; /* avoid unused warning */
    uint32_t phys = x86_translate_address(cpu2, segment, offset);
    return 0; /* placeholder - would use mem */
}

/* Write word to segment:offset */
void x86_mem_write_word_seg(x86_memory_t *mem, x86_cpu_t *cpu,
                              uint16_t segment, uint16_t offset, uint16_t value) {
    uint32_t phys = x86_translate_address(cpu, segment, (uint32_t)offset);
    x86_mem_write_word(mem, phys, value);
}

/* Write dword to segment:offset */
void x86_mem_write_dword_seg(x86_memory_t *mem, x86_cpu_t *cpu,
                               uint16_t segment, uint32_t offset, uint32_t value) {
    uint32_t phys = x86_translate_address(cpu, segment, offset);
    x86_mem_write_dword(mem, phys, value);
}

/*
 * Stack push: decrement ESP, store value at SS:ESP
 * In real mode: stack is in SS segment
 * In protected mode: stack is in SS segment (base typically 0)
 */
uint32_t x86_stack_push(x86_cpu_t *cpu, x86_memory_t *mem, uint32_t value) {
    /* Stack grows down */
    if (cpu->mode == MODE_REAL) {
        cpu->regs[X86_REG_ESP] -= 2;
        uint32_t phys = x86_translate_address(cpu, cpu->seg_regs[X86_SEG_SS],
                                                cpu->regs[X86_REG_ESP]);
        x86_mem_write_word(mem, phys, (uint16_t)value);
    } else {
        cpu->regs[X86_REG_ESP] -= 4;
        uint32_t phys = x86_translate_address(cpu, cpu->seg_regs[X86_SEG_SS],
                                                cpu->regs[X86_REG_ESP]);
        x86_mem_write_dword(mem, phys, value);
    }
    return cpu->regs[X86_REG_ESP];
}

/*
 * Stack pop: read from SS:ESP, increment ESP
 * Returns the popped value
 */
uint32_t x86_stack_pop(x86_cpu_t *cpu, x86_memory_t *mem) {
    uint32_t value;
    if (cpu->mode == MODE_REAL) {
        uint32_t phys = x86_translate_address(cpu, cpu->seg_regs[X86_SEG_SS],
                                                cpu->regs[X86_REG_ESP]);
        value = x86_mem_read_word(mem, phys);
        cpu->regs[X86_REG_ESP] += 2;
    } else {
        uint32_t phys = x86_translate_address(cpu, cpu->seg_regs[X86_SEG_SS],
                                                cpu->regs[X86_REG_ESP]);
        value = x86_mem_read_dword(mem, phys);
        cpu->regs[X86_REG_ESP] += 4;
    }
    return value;
}

/* Memory dump for debugging */
void x86_mem_dump(x86_memory_t *mem, uint32_t start, uint32_t length) {
    uint32_t end = start + length;
    if (end > mem->size) end = mem->size;

    printf("\n--- Memory dump 0x%06X - 0x%06X ---\n", start, end);
    for (uint32_t addr = start; addr < end; addr += 16) {
        printf("  0x%06X: ", addr);
        for (int i = 0; i < 16 && addr + i < end; i++) {
            printf("%02X ", mem->data[addr + i]);
        }
        printf("  ");
        for (int i = 0; i < 16 && addr + i < end; i++) {
            uint8_t c = mem->data[addr + i];
            printf("%c", (c >= 0x20 && c < 0x7F) ? c : '.');
        }
        printf("\n");
    }
    printf("--------------------------------------\n\n");
}

/* Load binary data into memory at specified address */
int x86_mem_load_binary(x86_memory_t *mem, uint32_t addr,
                         const uint8_t *data, uint32_t length) {
    if (addr + length > mem->size) {
        printf("[ERROR] Binary too large for memory: needs %u bytes at 0x%08X\n",
               length, addr);
        return X86_ERROR;
    }
    memcpy(&mem->data[addr], data, length);
    return X86_OK;
}
