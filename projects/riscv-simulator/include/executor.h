#ifndef EXECUTOR_H
#define EXECUTOR_H

#include "riscv.h"
#include "cpu.h"

/* ============================================================
 * 指令执行器
 *
 * 执行解码后的指令，更新 CPU 状态
 * ============================================================ */

/* 执行解码后的指令 */
SimError execute_insn(CPU* cpu, const DecodedInsn* insn);

/* R-type ALU 指令 */
SimError execute_r_type(CPU* cpu, const DecodedInsn* insn);

/* I-type ALU 指令 */
SimError execute_i_type(CPU* cpu, const DecodedInsn* insn);

/* Load 指令 */
SimError execute_load(CPU* cpu, const DecodedInsn* insn);

/* Store 指令 */
SimError execute_store(CPU* cpu, const DecodedInsn* insn);

/* Branch 指令 */
SimError execute_branch(CPU* cpu, const DecodedInsn* insn);

/* Jump 指令 (JAL / JALR) */
SimError execute_jump(CPU* cpu, const DecodedInsn* insn);

/* U-type 指令 (LUI / AUIPC) */
SimError execute_u_type(CPU* cpu, const DecodedInsn* insn);

/* System 指令 (ECALL / EBREAK) */
SimError execute_system(CPU* cpu, const DecodedInsn* insn);

#endif /* EXECUTOR_H */
