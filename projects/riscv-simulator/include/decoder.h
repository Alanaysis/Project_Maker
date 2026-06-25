#ifndef DECODER_H
#define DECODER_H

#include "riscv.h"

/* ============================================================
 * 指令解码器
 *
 * 将 32 位原始指令解码为结构化的 DecodedInsn
 * 支持 RV32I 基本指令集
 * ============================================================ */

/* 解码指令 */
SimError decode_insn(u32 raw, DecodedInsn* out);

/* 获取指令格式 */
InsnFormat get_insn_format(Opcode opcode);

/* 获取指令名称 */
const char* get_insn_name(const DecodedInsn* insn);

/* 格式化指令为汇编字符串 */
int format_insn(const DecodedInsn* insn, char* buf, size_t buf_size);

/* 打印解码后的指令 */
void dump_insn(const DecodedInsn* insn);

#endif /* DECODER_H */
