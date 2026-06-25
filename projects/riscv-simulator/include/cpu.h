#ifndef CPU_H
#define CPU_H

#include "riscv.h"
#include "memory.h"

/* ============================================================
 * CPU 模型
 *
 * 包含:
 * - 32 个通用寄存器 (x0-x31)
 * - 程序计数器 (PC)
 * - 内存引用
 * - 运行状态
 * ============================================================ */

/* CPU 状态 */
typedef enum {
    CPU_STOPPED = 0,   /* 已停止 */
    CPU_RUNNING,       /* 运行中 */
    CPU_HALTED,        /* 已停机 */
    CPU_ERROR,         /* 错误状态 */
} CpuState;

/* CPU 结构 */
typedef struct {
    u32       regs[NUM_REGS];  /* 32 个通用寄存器 */
    u32       pc;              /* 程序计数器 */
    Memory*   memory;          /* 内存引用 */
    CpuState  state;           /* CPU 状态 */
    u64       insn_count;      /* 已执行指令数 */
    u64       cycle_count;     /* 周期计数 */
    DebugLevel debug;          /* 调试级别 */
} CPU;

/* ============================================================
 * CPU 操作 API
 * ============================================================ */

/* 创建 CPU */
CPU* cpu_create(Memory* mem);

/* 销毁 CPU */
void cpu_destroy(CPU* cpu);

/* 重置 CPU */
void cpu_reset(CPU* cpu);

/* 设置 PC */
void cpu_set_pc(CPU* cpu, u32 pc);

/* 读取寄存器 */
u32 cpu_read_reg(CPU* cpu, u8 reg);

/* 写入寄存器 (x0 始终为 0) */
void cpu_write_reg(CPU* cpu, u8 reg, u32 val);

/* 执行单步 */
SimError cpu_step(CPU* cpu);

/* 运行直到停止 */
SimError cpu_run(CPU* cpu, u64 max_cycles);

/* 打印寄存器状态 */
void cpu_dump_regs(CPU* cpu);

/* 打印 CPU 状态 */
void cpu_dump_state(CPU* cpu);

#endif /* CPU_H */
