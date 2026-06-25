#ifndef ASSEMBLER_H
#define ASSEMBLER_H

#include "riscv.h"

/* ============================================================
 * 简单汇编器
 *
 * 将 RISC-V 汇编文本转换为机器码
 * 支持 RV32I 基本指令集
 * ============================================================ */

/* 汇编上下文 */
typedef struct {
    u32   pc;              /* 当前 PC */
    u32*  code;            /* 输出代码缓冲区 */
    u32   code_capacity;   /* 缓冲区容量 */
    u32   code_size;       /* 已生成代码大小 (字节) */
} AsmContext;

/* 汇编单条指令 */
AsmContext* asm_create(u32 start_pc);

/* 销毁汇编上下文 */
void asm_destroy(AsmContext* ctx);

/* 汇编单条指令 (返回机器码, 无标签支持) */
SimError asm_assemble_one_wrapper(const char* line, u32 pc, u32* out);

/* 汇编多行文本 */
SimError asm_assemble(AsmContext* ctx, const char* text);

/* 获取寄存器索引 (名称 -> 编号) */
int asm_parse_register(const char* name);

/* 解析立即数 */
SimError asm_parse_imm(const char* str, i32* out);

/* 打印汇编上下文状态 */
void asm_dump(AsmContext* ctx);

#endif /* ASSEMBLER_H */
