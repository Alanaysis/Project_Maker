#ifndef X86_TYPES_H
#define X86_TYPES_H

#include <stdint.h>
#include <stdbool.h>

/* ============================================================
 * x86-simulator: x86 Instruction Set Simulator
 *
 * This project implements a 32-bit x86 instruction set simulator
 * for educational purposes. It covers:
 *   - Real mode and protected mode
 *   - Variable-length x86 instruction encoding
 *   - Segment translation (linear/physical address)
 *   - Interrupt handling
 *   - Core instruction categories:
 *     Data movement (MOV, PUSH, POP, XCHG)
 *     Arithmetic (ADD, SUB, MUL, DIV, INC, DEC, CMP)
 *     Logic (AND, OR, XOR, NOT, SHL, SHR, SAR, ROL, ROR)
 *     Control flow (JMP, JE, JNE, JL, JG, CALL, RET)
 *     String instructions (MOVSB, CMPSB, LODSB, STOSB)
 *     Interrupt (INT, INT3, IRET)
 *
 * x86 Architecture Background:
 *   - x86 is a CISC (Complex Instruction Set Computer) architecture
 *   - Instructions are variable-length (1-15 bytes)
 *   - Real mode: 20-bit addresses (segment << 4 + offset), 1MB limit
 *   - Protected mode: 32-bit linear addresses with segment translation
 *   - Segment registers (CS, DS, SS, ES, FS, GS) provide base addresses
 * ============================================================ */

/* ---- Data width constants ---- */
#define X86_BIT   0
#define X86_BYTE  1
#define X86_WORD  2
#define X86_DWORD 3
#define X86_QWORD 4

/* ---- Register indices (eip, eax, ecx, edx, ebx, esp, ebp, esi, edi) ---- */
#define X86_REG_EIP  0
#define X86_REG_EAX  1
#define X86_REG_ECX  2
#define X86_REG_EDX  3
#define X86_REG_EBX  4
#define X86_REG_ESP  5
#define X86_REG_EBP  6
#define X86_REG_ESI  7
#define X86_REG_EDI  8
#define X86_REG_MAX  9

/* ---- Segment register indices ---- */
#define X86_SEG_CS 0
#define X86_SEG_DS 1
#define X86_SEG_SS 2
#define X86_SEG_ES 3
#define X86_SEG_FS 4
#define X86_SEG_GS 5
#define X86_SEG_MAX 6

/* ---- EFLAGS bits ---- */
#define X86_EFLAGS_CF  0  /* Carry flag */
#define X86_EFLAGS_PF  2  /* Parity flag */
#define X86_EFLAGS_AF  4  /* Auxiliary carry flag */
#define X86_EFLAGS_ZF  6  /* Zero flag */
#define X86_EFLAGS_SF  7  /* Sign flag */
#define X86_EFLAGS_DF  10 /* Direction flag (0=forward, 1=backward) */
#define X86_EFLAGS_OF  11 /* Overflow flag */
#define X86_EFLAGS_IF  9  /* Interrupt enable flag */

/* ---- EFLAGS masks ---- */
#define X86_EFLAGS_CF_MASK  (1U << 0)
#define X86_EFLAGS_PF_MASK  (1U << 2)
#define X86_EFLAGS_AF_MASK  (1U << 4)
#define X86_EFLAGS_ZF_MASK  (1U << 6)
#define X86_EFLAGS_SF_MASK  (1U << 7)
#define X86_EFLAGS_DF_MASK  (1U << 10)
#define X86_EFLAGS_OF_MASK  (1U << 11)
#define X86_EFLAGS_IF_MASK  (1U << 9)

/* ---- Segment selector bits ---- */
#define X86_SEG_RPL_MASK 0x03
#define X86_SEG_TI_MASK  0x04
#define X86_SEG_TI_LDT   0x04
#define X86_SEG_TI_GDT   0x00

/* ---- Interrupt vectors ---- */
#define X86_INT_VECTOR_MAX 256
#define X86_INT3_VECTOR    3
#define X86_BOUND_VECTOR   5
#define X86_OVERFLOW_VECTOR 4

/* ---- Memory size ---- */
#define MEM_SIZE (1024 * 1024) /* 1 MB simulated physical memory */

/* ---- Mode ---- */
typedef enum {
    MODE_REAL,       /* Real mode: 20-bit addresses */
    MODE_PROTECTED   /* Protected mode: 32-bit linear addresses */
} x86_mode_t;

/* ---- Addressing mode for instruction decoding ---- */
typedef enum {
    ADDR_REG,       /* Register direct: e.g., [eax] */
    ADDR_IMM,       /* Immediate value */
    ADDR_MEM,       /* Memory operand */
    ADDR_SEG,       /* Segment override */
    ADDR_NONE
} addr_type_t;

/* ---- Operand type ---- */
typedef enum {
    OP_REG,         /* General purpose register */
    OP_IMM,         /* Immediate value */
    OP_MEM,         /* Memory operand */
    OP_SEG,         /* Segment register */
    OP_EFLAGS,      /* EFLAGS register */
    OP_NONE
} operand_type_t;

/* ---- Segment register state ---- */
typedef struct {
    uint16_t selector;    /* Selector value (from software) */
    uint32_t base;        /* Segment base address */
    uint32_t limit;       /* Segment limit */
    uint8_t  dpl;         /* Descriptor privilege level */
    bool     present;     /* Segment present in memory */
    bool     writable;    /* Segment is writable */
    bool     executable;  /* Segment is executable (code segment) */
    bool     db;          /* Default operation size (0=16-bit, 1=32-bit) */
} x86_segment_t;

/* ---- GDT/IDT descriptor ---- */
typedef struct {
    uint32_t base_low;
    uint16_t limit_low;
    uint16_t limit_base;
    uint8_t  type;
    uint8_t  dpl;
    uint8_t  present;
    uint32_t base_high;
} x86_descriptor_t;

/* ---- CPU state (the "register file") ---- */
typedef struct {
    /* General purpose registers (32-bit) */
    uint32_t regs[X86_REG_MAX];

    /* Segment registers */
    uint16_t seg_regs[X86_SEG_MAX];  /* Visible selector values */
    x86_segment_t seg_state[X86_SEG_MAX]; /* Hidden descriptor cache */

    /* Special registers */
    uint32_t eflags;       /* 32-bit flags register */
    uint32_t eip;          /* Instruction pointer */
    uint32_t gdtr_base;    /* GDT base address */
    uint16_t gdtr_limit;   /* GDT limit */
    uint32_t idtr_base;    /* IDT base address */
    uint16_t idtr_limit;   /* IDT limit */
    uint32_t cr0;          /* Control register 0 */

    /* Mode */
    x86_mode_t mode;

    /* Interrupt state */
    bool     interrupt_pending;
    uint8_t  interrupt_vector;
    bool     interrupt_masked; /* If IF=0, maskable interrupts blocked */

    /* Execution state */
    bool     running;
    bool     halted;
    uint32_t instruction_count;
} x86_cpu_t;

/* ---- Memory interface ---- */
typedef struct {
    uint8_t data[MEM_SIZE];
    uint32_t size;
} x86_memory_t;

/* ---- Operand representation ---- */
typedef struct {
    operand_type_t type;
    uint32_t       reg_index;  /* For register operands */
    int32_t        value;      /* For immediate/sign-extended values */
    uint32_t       mem_addr;   /* For memory operands (linear address) */
    uint8_t        size;       /* Operand size in bytes (1, 2, 4) */
    uint16_t       segment;    /* Segment override (0 = none) */
} x86_operand_t;

/* ---- Decoded instruction ---- */
typedef struct {
    uint8_t opcode;        /* Primary opcode byte */
    uint8_t modrm;         /* MOD/RM byte (if present) */
    uint8_t sib;           /* SIB byte (if present) */
    uint8_t has_modrm;
    uint8_t has_sib;
    uint8_t has_disp;      /* Displacement size: 0, 1, 2, or 4 bytes */
    int32_t displacement;
    uint8_t has_imm;       /* Immediate size: 0 (none), 1, 2, or 4 */
    uint32_t immediate;
    uint8_t operand_size;  /* Default operand size (16 or 32 bit) */
    uint8_t addr_size;     /* Address size (16 or 32 bit) */
    uint8_t operand_bits;  /* 16 or 32 */

    /* Prefixes */
    uint8_t has_seg_override;
    uint16_t seg_override;

    /* Instruction category */
    uint8_t category;      /* Arithmetic, Logic, DataMovement, etc. */

    /* Pointer to execution function */
    void (*execute)(x86_cpu_t *cpu, x86_memory_t *mem, x86_operand_t *operands);
} x86_instruction_t;

/* ---- Instruction categories ---- */
#define INSTR_CATEGORY_NONE        0
#define INSTR_CATEGORY_ARITHMETIC  1
#define INSTR_CATEGORY_LOGIC       2
#define INSTR_CATEGORY_DATA_MOV    3
#define INSTR_CATEGORY_CONTROL_FLOW 4
#define INSTR_CATEGORY_STRING      5
#define INSTR_CATEGORY_INTERRUPT   6
#define INSTR_CATEGORY_SYSTEM      7

/* ---- Return codes ---- */
#define X86_OK           0
#define X86_ERROR        -1
#define X86_INVALID_OP   -2
#define X86_FAULT        -3
#define X86_TRAP         -4

#endif /* X86_TYPES_H */
