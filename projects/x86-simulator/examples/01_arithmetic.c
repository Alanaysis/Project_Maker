/*
 * example_arithmetic.c - Basic arithmetic program execution demo
 *
 * This example demonstrates the arithmetic instruction set:
 *   ADD, SUB, MUL, DIV, INC, DEC, CMP
 *
 * x86 Architecture Notes:
 *   - MUL uses implicit EAX register for 32-bit operands
 *   - DIV uses implicit EDX:EAX double-word dividend
 *   - CMP performs subtraction and sets flags without storing result
 *   - INC/DEC affect ZF, SF, OF, CF, PF but NOT AF
 *   - All arithmetic instructions update EFLAGS condition codes
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "x86_types.h"
#include "x86_cpu.h"
#include "x86_memory.h"
#include "x86_decode.h"
#include "x86_execute.h"

/* Helper to load a single byte */
static void load_byte(x86_memory_t *mem, uint32_t addr, uint8_t byte) {
    x86_mem_write_byte(mem, addr, byte);
}

/* Helper to load a 16-bit word (little-endian) */
static void load_word(x86_memory_t *mem, uint32_t addr, uint16_t word) {
    x86_mem_write_byte(mem, addr, (uint8_t)(word & 0xFF));
    x86_mem_write_byte(mem, addr + 1, (uint8_t)((word >> 8) & 0xFF));
}

/* Helper to load a 32-bit dword (little-endian) */
static void load_dword(x86_memory_t *mem, uint32_t addr, uint32_t dword) {
    x86_mem_write_byte(mem, addr, (uint8_t)(dword & 0xFF));
    x86_mem_write_byte(mem, addr + 1, (uint8_t)((dword >> 8) & 0xFF));
    x86_mem_write_byte(mem, addr + 2, (uint8_t)((dword >> 16) & 0xFF));
    x86_mem_write_byte(mem, addr + 3, (uint8_t)((dword >> 24) & 0xFF));
}

/*
 * Program: Basic arithmetic operations
 *
 * Assembly (32-bit protected mode):
 *   MOV EAX, 10       ; Load 10 into EAX
 *   MOV EBX, 20       ; Load 20 into EBX
 *   ADD EAX, EBX      ; EAX = EAX + EBX = 30
 *   SUB EAX, EBX      ; EAX = EAX - EBX = 10
 *   INC EAX           ; EAX = EAX + 1 = 11
 *   DEC EAX           ; EAX = EAX - 1 = 10
 *   MOV ECX, 5        ; Load 5 into ECX
 *   MUL ECX           ; EDX:EAX = EAX * ECX = 50
 *   MOV EBX, 2        ; Load 2 into EBX
 *   DIV EBX           ; EAX = EDX:EAX / EBX = 25
 *   CMP EAX, 25       ; Compare EAX with 25 (should be equal)
 *   JE equal          ; Jump if equal
 *   MOV EAX, 0        ; Not equal
 *   JMP done
 * equal:
 *   MOV EAX, 1        ; Equal!
 * done:
 *   HLT
 */
int run_arithmetic_demo(void) {
    x86_cpu_t cpu;
    x86_memory_t mem;

    x86_cpu_init(&cpu);
    x86_mem_init(&mem);

    /* Set up protected mode */
    cpu.mode = MODE_PROTECTED;
    cpu.cr0 = 0x80000001; /* PE=1, PG=0 */
    cpu.seg_regs[X86_SEG_CS] = 0x0008; /* Code segment selector */
    cpu.seg_state[X86_SEG_CS].base = 0;
    cpu.seg_state[X86_SEG_CS].limit = 0xFFFFF;
    cpu.seg_state[X86_SEG_CS].present = 1;
    cpu.seg_state[X86_SEG_CS].executable = 1;
    cpu.seg_state[X86_SEG_CS].db = 1; /* 32-bit default */

    cpu.seg_regs[X86_SEG_DS] = 0x0010; /* Data segment selector */
    cpu.seg_state[X86_SEG_DS].base = 0;
    cpu.seg_state[X86_SEG_DS].limit = 0xFFFFF;
    cpu.seg_state[X86_SEG_DS].present = 1;
    cpu.seg_state[X86_SEG_DS].writable = 1;
    cpu.seg_state[X86_SEG_DS].db = 1;

    /* Set up IDT for interrupts */
    cpu.idtr_base = 0x100;
    cpu.idtr_limit = 0xFF;

    /* Write program to memory at address 0x200 */
    uint32_t pc = 0x200;

    /* MOV EAX, 10 */
    load_byte(&mem, pc++, 0xB8);
    load_dword(&mem, pc, 10); pc += 4;

    /* MOV EBX, 20 */
    load_byte(&mem, pc++, 0xBB);
    load_dword(&mem, pc, 20); pc += 4;

    /* ADD EAX, EBX */
    load_byte(&mem, pc++, 0x01);
    load_byte(&mem, pc++, 0xC3); /* MOD=11, REG=EAX(0), R/M=EBX(3) */

    /* SUB EAX, EBX */
    load_byte(&mem, pc++, 0x29);
    load_byte(&mem, pc++, 0xC0); /* MOD=11, REG=EBX(3), R/M=EAX(0) */

    /* INC EAX */
    load_byte(&mem, pc++, 0x40); /* INC EAX */

    /* DEC EAX (to get back to 10) */
    load_byte(&mem, pc++, 0x48); /* DEC EAX */

    /* MOV ECX, 5 */
    load_byte(&mem, pc++, 0xB9);
    load_dword(&mem, pc, 5); pc += 4;

    /* MUL ECX (EDX:EAX = EAX * ECX) */
    load_byte(&mem, pc++, 0xF7);
    load_byte(&mem, pc++, 0xE1); /* MOD=11, REG=4(MUL), R/M=ECX(1) */

    /* MOV EBX, 2 */
    load_byte(&mem, pc++, 0xBB);
    load_dword(&mem, pc, 2); pc += 4;

    /* DIV EBX (EAX = EDX:EAX / EBX) */
    load_byte(&mem, pc++, 0xF7);
    load_byte(&mem, pc++, 0xE3); /* MOD=11, REG=6(DIV), R/M=EBX(3) */

    /* CMP EAX, 25 */
    load_byte(&mem, pc++, 0x83);
    load_byte(&mem, pc++, 0xF8); /* MOD=11, REG=7(CMP), R/M=EAX(0) */
    load_byte(&mem, pc++, 0x19); /* imm8 = 25 */

    /* JE equal */
    load_byte(&mem, pc++, 0x74); /* JE */
    load_byte(&mem, pc++, 0x0A); /* short displacement = 10 */

    /* MOV EAX, 0 (not equal path) */
    load_byte(&mem, pc++, 0xB8);
    load_dword(&mem, pc, 0); pc += 4;

    /* JMP done */
    load_byte(&mem, pc++, 0xEB); /* JMP short */
    load_byte(&mem, pc++, 0x06); /* displacement = 6 */

    /* equal: MOV EAX, 1 */
    load_byte(&mem, pc++, 0xB8);
    load_dword(&mem, pc, 1); pc += 4;

    /* done: HLT (INT 3 for halt) */
    load_byte(&mem, pc++, 0xCC); /* INT3 */

    /* Set EIP to start of program */
    cpu.eip = 0x200;

    printf("=== Arithmetic Operations Demo ===\n\n");
    printf("Program: MOV EAX,10 -> MOV EBX,20 -> ADD EAX,EBX -> SUB EAX,EBX\n");
    printf("         -> INC EAX -> DEC EAX -> MOV ECX,5 -> MUL ECX\n");
    printf("         -> MOV EBX,2 -> DIV EBX -> CMP EAX,25 -> JE equal\n");
    printf("         -> MOV EAX,1 on equal\n\n");

    x86_simulate(&cpu, &mem, 0);
    printf("\nExpected EAX = 1 (because 50/2 = 25, which equals 25)\n");

    return 0;
}

int main(void) {
    return run_arithmetic_demo();
}
