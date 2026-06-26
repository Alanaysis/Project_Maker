/*
 * example_string.c - String manipulation demo
 *
 * This example demonstrates string instructions:
 *   MOVSB - Move string byte (copy from ESI to EDI)
 *   STOSB - Store string byte (copy EAX to [EDI])
 *   CMPSB - Compare string bytes
 *   LODSB - Load string byte (copy [ESI] to EAX)
 *
 * x86 Architecture Notes:
 *   - String instructions use ESI as source index and EDI as destination
 *   - Direction flag (DF in EFLAGS) controls increment/decrement:
 *     DF=0: ESI/EDI increment (forward)
 *     DF=1: ESI/EDI decrement (backward)
 *   - Default segment: DS for source, ES for destination
 *   - REP prefix repeats string instruction ECX times
 *   - String instructions work on bytes (SB), words (SW), or dwords (SD)
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "x86_types.h"
#include "x86_cpu.h"
#include "x86_memory.h"
#include "x86_decode.h"
#include "x86_execute.h"

static void load_byte(x86_memory_t *mem, uint32_t addr, uint8_t byte) {
    x86_mem_write_byte(mem, addr, byte);
}

static void load_word(x86_memory_t *mem, uint32_t addr, uint16_t word) {
    x86_mem_write_byte(mem, addr, (uint8_t)(word & 0xFF));
    x86_mem_write_byte(mem, addr + 1, (uint8_t)((word >> 8) & 0xFF));
}

static void load_dword(x86_memory_t *mem, uint32_t addr, uint32_t dword) {
    x86_mem_write_byte(mem, addr, (uint8_t)(dword & 0xFF));
    x86_mem_write_byte(mem, addr + 1, (uint8_t)((dword >> 8) & 0xFF));
    x86_mem_write_byte(mem, addr + 2, (uint8_t)((dword >> 16) & 0xFF));
    x86_mem_write_byte(mem, addr + 3, (uint8_t)((dword >> 24) & 0xFF));
}

/*
 * Program: String copy using MOVSB
 *
 * Assembly:
 *   CLD               ; Clear direction flag (forward)
 *   MOV ESI, src      ; Source pointer
 *   MOV EDI, dst      ; Destination pointer
 *   MOV ECX, len      ; Count
 *   REP MOVSB         ; Copy ECX bytes from [ESI] to [EDI]
 *   MOV EAX, 0        ; Success
 */
int run_string_demo(void) {
    x86_cpu_t cpu;
    x86_memory_t mem;

    x86_cpu_init(&cpu);
    x86_mem_init(&mem);

    /* Set up protected mode */
    cpu.mode = MODE_PROTECTED;
    cpu.cr0 = 0x80000001;
    cpu.seg_regs[X86_SEG_CS] = 0x0008;
    cpu.seg_state[X86_SEG_CS].base = 0;
    cpu.seg_state[X86_SEG_CS].limit = 0xFFFFF;
    cpu.seg_state[X86_SEG_CS].present = 1;
    cpu.seg_state[X86_SEG_CS].executable = 1;
    cpu.seg_state[X86_SEG_CS].db = 1;

    cpu.seg_regs[X86_SEG_DS] = 0x0010;
    cpu.seg_state[X86_SEG_DS].base = 0;
    cpu.seg_state[X86_SEG_DS].limit = 0xFFFFF;
    cpu.seg_state[X86_SEG_DS].present = 1;
    cpu.seg_state[X86_SEG_DS].writable = 1;
    cpu.seg_state[X86_SEG_DS].db = 1;

    cpu.seg_regs[X86_SEG_ES] = 0x0010; /* ES = DS for string ops */
    cpu.seg_state[X86_SEG_ES] = cpu.seg_state[X86_SEG_DS];

    cpu.idtr_base = 0x100;
    cpu.idtr_limit = 0xFF;

    /* Source string */
    const char *source = "Hello, x86 Simulator!";
    uint32_t src_addr = 0x1000;
    uint32_t len = (uint32_t)strlen(source);
    for (uint32_t i = 0; i < len; i++) {
        x86_mem_write_byte(&mem, src_addr + i, (uint8_t)source[i]);
    }

    /* Destination buffer at 0x2000 */
    uint32_t dst_addr = 0x2000;

    /* Write program at 0x3000 */
    uint32_t pc = 0x3000;

    /* CLD - Clear direction flag */
    load_byte(&mem, pc++, 0xFC);

    /* MOV ESI, src_addr */
    load_byte(&mem, pc++, 0xBE);
    load_dword(&mem, pc, src_addr); pc += 4;

    /* MOV EDI, dst_addr */
    load_byte(&mem, pc++, 0xBF);
    load_dword(&mem, pc, dst_addr); pc += 4;

    /* MOV ECX, len */
    load_byte(&mem, pc++, 0xB9);
    load_dword(&mem, pc, len); pc += 4;

    /* REP MOVSB - Move string byte */
    load_byte(&mem, pc++, 0xF3); /* REP prefix */
    load_byte(&mem, pc++, 0xA4); /* MOVSB */

    /* MOV EAX, 0 (success) */
    load_byte(&mem, pc++, 0xB8);
    load_dword(&mem, pc, 0); pc += 4;

    /* INT3 (halt) */
    load_byte(&mem, pc++, 0xCC);

    cpu.eip = 0x3000;

    printf("=== String Manipulation Demo ===\n\n");
    printf("Source string (at 0x%04X): \"%s\"\n", src_addr, source);
    printf("Destination (at 0x%04X): [before copy]\n", dst_addr);
    printf("Instructions: CLD -> MOV ESI,src -> MOV EDI,dst -> MOV ECX,len\n");
    printf("              -> REP MOVSB -> MOV EAX,0 -> HLT\n\n");

    /* Run just the string copy */
    cpu.running = true;
    int step = 0;
    for (step = 0; step < 50; step++) {
        execute_one(&cpu, &mem);
        if (cpu.halted) break;
    }

    printf("Destination (at 0x%04X): \"", dst_addr);
    for (uint32_t i = 0; i < len && (dst_addr + i) < mem.size; i++) {
        uint8_t c = x86_mem_read_byte(&mem, dst_addr + i);
        if (c >= 0x20 && c < 0x7F) {
            putchar(c);
        } else {
            putchar('.');
        }
    }
    printf("\"\n\n");

    printf("ESI = 0x%08X (should be 0x%08X = src + len)\n",
           cpu.regs[X86_REG_ESI], src_addr + len);
    printf("EDI = 0x%08X (should be 0x%08X = dst + len)\n",
           cpu.regs[X86_REG_EDI], dst_addr + len);
    printf("ECX = 0x%08X (should be 0x%08X = len - len = 0)\n",
           cpu.regs[X86_REG_ECX], 0);
    printf("EAX = 0x%08X (should be 0x%08X = success)\n",
           cpu.regs[X86_REG_EAX], 0);

    return 0;
}

int main(void) {
    return run_string_demo();
}
