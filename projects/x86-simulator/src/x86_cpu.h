#ifndef X86_CPU_H
#define X86_CPU_H

#include "x86_types.h"

/*
 * x86_cpu.h - CPU state management
 *
 * Functions to initialize, reset, and manage the CPU register file.
 * The x86 register file includes:
 *   - 8 general-purpose 32-bit registers (EAX, ECX, EDX, EBX, ESP, EBP, ESI, EDI)
 *   - 6 segment registers (CS, DS, SS, ES, FS, GS)
 *   - EFLAGS register with condition codes
 *   - Control registers (CR0) for mode switching
 *
 * In real mode, segment registers hold segment bases directly.
 * In protected mode, segment selectors index into the GDT.
 */

/* Initialize CPU to real mode state (power-on reset state) */
void x86_cpu_init(x86_cpu_t *cpu);

/* Reset CPU to initial state */
void x86_cpu_reset(x86_cpu_t *cpu);

/* Set a general-purpose register */
static inline void x86_reg_write(x86_cpu_t *cpu, uint8_t reg, uint32_t value) {
    if (reg < X86_REG_MAX) {
        cpu->regs[reg] = value & 0xFFFFFFFF;
    }
}

/* Get a general-purpose register */
static inline uint32_t x86_reg_read(x86_cpu_t *cpu, uint8_t reg) {
    if (reg < X86_REG_MAX) {
        return cpu->regs[reg];
    }
    return 0;
}

/* Get 16-bit register value (for 16-bit mode compatibility) */
uint16_t x86_reg16_read(x86_cpu_t *cpu, uint8_t reg);

/* Set 16-bit register value */
static inline void x86_reg16_write(x86_cpu_t *cpu, uint8_t reg, uint16_t value) {
    if (reg < X86_REG_MAX) {
        uint32_t old = cpu->regs[reg];
        cpu->regs[reg] = (old & 0xFFFF0000) | (value & 0xFFFF);
    }
}

/* Set EFLAGS bits */
static inline void x86_eflags_set(x86_cpu_t *cpu, uint32_t flags) {
    cpu->eflags |= flags;
}

/* Clear EFLAGS bits */
static inline void x86_eflags_clear(x86_cpu_t *cpu, uint32_t flags) {
    cpu->eflags &= ~flags;
}

/* Toggle EFLAGS bits */
static inline void x86_eflags_toggle(x86_cpu_t *cpu, uint32_t flags) {
    cpu->eflags ^= flags;
}

/* Check if an EFLAGS bit is set */
static inline bool x86_eflags_get(x86_cpu_t *cpu, uint32_t flag) {
    return (cpu->eflags & flag) != 0;
}

/* Get the direction flag value (for string instructions) */
static inline int x86_dir_flag(x86_cpu_t *cpu) {
    return x86_eflags_get(cpu, X86_EFLAGS_DF_MASK) ? -1 : 1;
}

/* Set the direction flag */
static inline void x86_dir_set(x86_cpu_t *cpu) {
    x86_eflags_set(cpu, X86_EFLAGS_DF_MASK);
}

static inline void x86_dir_clear(x86_cpu_t *cpu) {
    x86_eflags_clear(cpu, X86_EFLAGS_DF_MASK);
}

/* Interrupt flag access */
static inline bool x86_if_get(x86_cpu_t *cpu) {
    return x86_eflags_get(cpu, X86_EFLAGS_IF_MASK);
}

static inline void x86_if_set(x86_cpu_t *cpu) {
    x86_eflags_set(cpu, X86_EFLAGS_IF_MASK);
}

static inline void x86_if_clear(x86_cpu_t *cpu) {
    x86_eflags_clear(cpu, X86_EFLAGS_IF_MASK);
}

/* Set condition flags based on a 32-bit result */
void x86_set_flags_from_result(x86_cpu_t *cpu, uint32_t result, uint8_t size);

/* Set flags for a signed comparison (a - b) */
void x86_set_flags_signed(x86_cpu_t *cpu, int32_t a, int32_t b, uint8_t size);

/* Set flags for an unsigned comparison (a - b) */
void x86_set_flags_unsigned(x86_cpu_t *cpu, uint32_t a, uint32_t b, uint8_t size);

/* Check condition codes (for conditional jumps) */
bool x86_check_condition(x86_cpu_t *cpu, uint8_t condition);

/* Print CPU state for debugging */
void x86_cpu_dump(x86_cpu_t *cpu);

/* Print register values */
void x86_cpu_dump_registers(x86_cpu_t *cpu);

/* Print EFLAGS */
void x86_cpu_dump_eflags(x86_cpu_t *cpu);

#endif /* X86_CPU_H */
