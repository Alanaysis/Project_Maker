#include "cpu.h"
#include "decoder.h"
#include "executor.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

/* ============================================================
 * CPU 实现
 * ============================================================ */

CPU* cpu_create(Memory* mem) {
    if (!mem) return NULL;

    CPU* cpu = (CPU*)malloc(sizeof(CPU));
    if (!cpu) return NULL;

    memset(cpu->regs, 0, sizeof(cpu->regs));
    cpu->pc = mem->base_addr;
    cpu->memory = mem;
    cpu->state = CPU_STOPPED;
    cpu->insn_count = 0;
    cpu->cycle_count = 0;
    cpu->debug = DEBUG_NONE;

    return cpu;
}

void cpu_destroy(CPU* cpu) {
    free(cpu);
}

void cpu_reset(CPU* cpu) {
    if (!cpu) return;

    memset(cpu->regs, 0, sizeof(cpu->regs));
    cpu->pc = cpu->memory->base_addr;
    cpu->state = CPU_STOPPED;
    cpu->insn_count = 0;
    cpu->cycle_count = 0;
}

void cpu_set_pc(CPU* cpu, u32 pc) {
    if (cpu) cpu->pc = pc;
}

u32 cpu_read_reg(CPU* cpu, u8 reg) {
    if (!cpu || reg >= NUM_REGS) return 0;
    return cpu->regs[reg];
}

void cpu_write_reg(CPU* cpu, u8 reg, u32 val) {
    if (!cpu || reg >= NUM_REGS) return;
    /* x0 (zero) 始终为 0 */
    if (reg == REG_ZERO) return;
    cpu->regs[reg] = val;
}

/* 执行单步 */
SimError cpu_step(CPU* cpu) {
    if (!cpu || !cpu->memory) return ERR_MEMORY_FAULT;

    u32 pc = cpu->pc;

    /* 1. 指令读取 (Instruction Fetch) */
    u32 raw_insn;
    SimError err = memory_read_word(cpu->memory, pc, &raw_insn);
    if (err != ERR_OK) {
        fprintf(stderr, "Fetch error at PC=0x%08X\n", pc);
        cpu->state = CPU_ERROR;
        return err;
    }

    /* 2. 指令解码 (Instruction Decode) */
    DecodedInsn decoded;
    err = decode_insn(raw_insn, &decoded);
    if (err != ERR_OK) {
        fprintf(stderr, "Decode error at PC=0x%08X: 0x%08X\n", pc, raw_insn);
        cpu->state = CPU_ERROR;
        return err;
    }

    /* 3. PC 递增 (在执行前，这样分支/跳转可以覆盖) */
    cpu->pc += 4;

    /* 4. 执行 (Execute) */
    err = execute_insn(cpu, &decoded);

    /* 5. 更新统计 */
    cpu->insn_count++;
    cpu->cycle_count++;

    /* 6. 检查错误 */
    if (err == ERR_HALT) {
        cpu->state = CPU_HALTED;
    } else if (err == ERR_BREAKPOINT) {
        cpu->state = CPU_STOPPED;
        return ERR_OK;  /* 断点不是错误 */
    } else if (err != ERR_OK) {
        cpu->state = CPU_ERROR;
    }

    return err;
}

/* 运行直到停止 */
SimError cpu_run(CPU* cpu, u64 max_cycles) {
    if (!cpu) return ERR_MEMORY_FAULT;

    cpu->state = CPU_RUNNING;
    SimError err = ERR_OK;

    for (u64 i = 0; i < max_cycles; i++) {
        err = cpu_step(cpu);

        if (err != ERR_OK) break;
        if (cpu->state == CPU_HALTED) break;
        if (cpu->state == CPU_STOPPED) break;
    }

    return err;
}

/* 打印寄存器状态 */
void cpu_dump_regs(CPU* cpu) {
    if (!cpu) return;

    printf("=== Registers ===\n");
    for (int i = 0; i < NUM_REGS; i++) {
        printf("  x%-2d %-5s = 0x%08X (%d)\n",
               i, REG_ABI_NAMES[i], cpu->regs[i], (i32)cpu->regs[i]);
        if ((i + 1) % 4 == 0 && i < NUM_REGS - 1) {
            printf("\n");
        }
    }
    printf("\n  PC       = 0x%08X\n", cpu->pc);
}

/* 打印 CPU 完整状态 */
void cpu_dump_state(CPU* cpu) {
    if (!cpu) return;

    printf("\n=== CPU State ===\n");
    printf("  PC: 0x%08X\n", cpu->pc);
    printf("  State: %s\n",
           cpu->state == CPU_STOPPED ? "STOPPED" :
           cpu->state == CPU_RUNNING ? "RUNNING" :
           cpu->state == CPU_HALTED  ? "HALTED"  :
           cpu->state == CPU_ERROR   ? "ERROR"   : "UNKNOWN");
    printf("  Instructions: %lu\n", (unsigned long)cpu->insn_count);
    printf("  Cycles: %lu\n", (unsigned long)cpu->cycle_count);
    printf("\n");

    cpu_dump_regs(cpu);
}
