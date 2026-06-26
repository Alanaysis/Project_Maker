#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "x86_types.h"
#include "x86_cpu.h"
#include "x86_memory.h"
#include "x86_decode.h"
#include "x86_execute.h"

/* ============================================================
 * x86-simulator: x86 Instruction Set Simulator
 *
 * Main entry point - the simulator core loop:
 *
 *   while (cpu.running) {
 *       1. Read instruction from CS:EIP
 *       2. Decode instruction (prefixes, opcode, MOD/RM, SIB, disp, imm)
 *       3. Execute instruction
 *       4. Update EIP
 *       5. Check for interrupts
 *   }
 *
 * This simulator supports:
 *   - Real mode (20-bit addresses)
 *   - Protected mode (32-bit linear addresses)
 *   - Core instruction set (data movement, arithmetic, logic,
 *     control flow, string instructions, interrupts)
 * ============================================================ */

/* Maximum instructions to execute before stopping */
#define MAX_INSTRUCTIONS 100000

/* Read instruction bytes from memory */
static int read_instruction(x86_cpu_t *cpu, x86_memory_t *mem,
                            x86_instruction_t *instr) {
    /* In real mode, instruction pointer = CS << 4 + EIP */
    uint32_t instr_addr;
    if (cpu->mode == MODE_REAL) {
        instr_addr = ((uint32_t)cpu->seg_regs[X86_SEG_CS] << 4) + cpu->eip;
    } else {
        instr_addr = cpu->eip; /* In protected mode, CS base is typically 0 */
    }

    /* Read up to X86_MAX_INSTR_SIZE bytes */
    uint32_t max_read = X86_MAX_INSTR_SIZE;
    if (instr_addr + max_read > mem->size) {
        max_read = mem->size - instr_addr;
    }

    for (uint32_t i = 0; i < max_read; i++) {
        instr->opcode = x86_mem_read_byte(mem, instr_addr + i);
        /* Store in a temporary buffer */
    }

    /* For simplicity, we'll read the opcode and let the decoder handle the rest */
    /* In a full implementation, we'd read all bytes into a buffer */
    return X86_OK;
}

/* Execute one instruction at CS:EIP */
static int execute_one(x86_cpu_t *cpu, x86_memory_t *mem) {
    x86_instruction_t instr;
    uint8_t buf[X86_MAX_INSTR_SIZE];

    /* Read instruction bytes from memory */
    uint32_t instr_addr;
    if (cpu->mode == MODE_REAL) {
        instr_addr = ((uint32_t)cpu->seg_regs[X86_SEG_CS] << 4) + cpu->eip;
    } else {
        instr_addr = cpu->eip;
    }

    uint32_t max_read = X86_MAX_INSTR_SIZE;
    if (instr_addr + max_read > mem->size) {
        max_read = mem->size - instr_addr;
    }

    for (uint32_t i = 0; i < max_read; i++) {
        buf[i] = x86_mem_read_byte(mem, instr_addr + i);
    }

    /* Initialize instruction stream */
    x86_instr_stream_t stream;
    x86_instr_init(&stream, buf, max_read);

    /* Decode the instruction */
    int ret = x86_decode(cpu, &stream, &instr);
    if (ret != X86_OK) {
        return ret;
    }

    /* Execute the instruction */
    ret = x86_execute_instruction(cpu, mem, &instr);
    if (ret != X86_OK) {
        return ret;
    }

    /* Update EIP to point past the instruction */
    cpu->eip += stream.pos;

    return X86_OK;
}

/* Main simulator loop */
int x86_simulate(x86_cpu_t *cpu, x86_memory_t *mem, int verbose) {
    cpu->running = true;
    cpu->instruction_count = 0;

    printf("=== x86 Instruction Simulator ===\n");
    printf("Mode: %s\n", cpu->mode == MODE_REAL ? "REAL" : "PROTECTED");
    printf("Starting at CS:0x%04X EIP:0x%08X\n\n",
           cpu->seg_regs[X86_SEG_CS], cpu->eip);

    while (cpu->running && cpu->instruction_count < MAX_INSTRUCTIONS) {
        /* Check for interrupt */
        if (cpu->interrupt_pending) {
            uint8_t vec = cpu->interrupt_vector;
            printf("[INT] Interrupt %d (vector %d)\n", vec, vec);

            /* Push EFLAGS, CS, EIP for IRET */
            x86_stack_push(cpu, mem, cpu->eflags);
            x86_eflags_clear(cpu, X86_EFLAGS_IF_MASK);
            x86_stack_push(cpu, mem, cpu->seg_regs[X86_SEG_CS]);
            x86_stack_push(cpu, mem, cpu->eip);

            /* Load handler address from IDT */
            if (vec * 4 + 3 < mem->size) {
                uint32_t handler = x86_mem_read_dword(mem, cpu->idtr_base + vec * 4);
                cpu->eip = handler;
            }
            cpu->interrupt_pending = false;
            continue;
        }

        /* Execute one instruction */
        int ret = execute_one(cpu, mem);
        if (ret != X86_OK) {
            printf("[ERROR] Execution failed at CS:0x%04X EIP:0x%08X\n",
                   cpu->seg_regs[X86_SEG_CS], cpu->eip);
            break;
        }

        /* Print state if verbose */
        if (verbose && cpu->instruction_count % 100 == 0) {
            printf("[STEP %u] EIP=0x%08X\n", cpu->instruction_count, cpu->eip);
        }
    }

    printf("\n=== Simulation Complete ===\n");
    printf("Instructions executed: %u\n", cpu->instruction_count);
    printf("Final EIP: 0x%08X\n", cpu->eip);
    printf("EAX: 0x%08X  ECX: 0x%08X  EDX: 0x%08X  EBX: 0x%08X\n",
           cpu->regs[X86_REG_EAX], cpu->regs[X86_REG_ECX],
           cpu->regs[X86_REG_EDX], cpu->regs[X86_REG_EBX]);
    printf("ESI: 0x%08X  EDI: 0x%08X  ESP: 0x%08X  EBP: 0x%08X\n",
           cpu->regs[X86_REG_ESI], cpu->regs[X86_REG_EDI],
           cpu->regs[X86_REG_ESP], cpu->regs[X86_REG_EBP]);
    printf("EFLAGS: 0x%08X\n", cpu->eflags);
    printf("Mode: %s\n", cpu->mode == MODE_REAL ? "REAL" : "PROTECTED");

    return 0;
}

/* Stop the simulator */
void x86_stop(x86_cpu_t *cpu) {
    cpu->running = false;
}

/* Halt the CPU */
void x86_halt(x86_cpu_t *cpu) {
    cpu->halted = true;
    cpu->running = false;
}

int main(int argc, char *argv[]) {
    x86_cpu_t cpu;
    x86_memory_t mem;

    /* Initialize CPU and memory */
    x86_cpu_init(&cpu);
    x86_mem_init(&mem);

    int verbose = 0;
    const char *binary_file = NULL;

    /* Parse command line */
    for (int i = 1; i < argc; i++) {
        if (strcmp(argv[i], "-v") == 0 || strcmp(argv[i], "--verbose") == 0) {
            verbose = 1;
        } else if (strcmp(argv[i], "-h") == 0 || strcmp(argv[i], "--help") == 0) {
            printf("x86-simulator: x86 Instruction Set Simulator\n");
            printf("Usage: %s [options] <binary_file>\n", argv[0]);
            printf("Options:\n");
            printf("  -v, --verbose  Verbose output\n");
            printf("  -h, --help     Show this help\n");
            return 0;
        } else {
            binary_file = argv[i];
        }
    }

    /* Load binary if provided */
    if (binary_file) {
        FILE *f = fopen(binary_file, "rb");
        if (f) {
            fseek(f, 0, SEEK_END);
            long size = ftell(f);
            fseek(f, 0, SEEK_SET);

            uint8_t *data = malloc(size);
            fread(data, 1, size, f);
            fclose(f);

            /* Load at address 0x1000 */
            x86_mem_load_binary(&mem, 0x1000, data, size);
            cpu.eip = 0x1000;
            cpu.seg_regs[X86_SEG_CS] = 0x0000;

            printf("Loaded binary: %s (%ld bytes) at 0x%04X:0x%08X\n",
                   binary_file, size, cpu.seg_regs[X86_SEG_CS], cpu.eip);
            free(data);
        } else {
            printf("Error: Cannot open file '%s'\n", binary_file);
            return 1;
        }
    } else {
        printf("No binary file specified. Running built-in demo.\n\n");
    }

    /* Run simulation */
    return x86_simulate(&cpu, &mem, verbose);
}
