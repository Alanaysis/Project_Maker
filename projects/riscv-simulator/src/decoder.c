#include "decoder.h"
#include <stdio.h>
#include <string.h>

/* ============================================================
 * 指令解码器实现
 *
 * RISC-V 指令格式:
 *   R-type: [funct7 | rs2 | rs1 | funct3 | rd | opcode]
 *   I-type: [imm[11:0]       | rs1 | funct3 | rd | opcode]
 *   S-type: [imm[11:5] | rs2 | rs1 | funct3 | imm[4:0] | opcode]
 *   B-type: [imm[12|10:5] | rs2 | rs1 | funct3 | imm[4:1|11] | opcode]
 *   U-type: [imm[31:12]                           | rd | opcode]
 *   J-type: [imm[20|10:1|11|19:12]                | rd | opcode]
 * ============================================================ */

/* 提取位域 */
#define BITS(val, hi, lo)  (((val) >> (lo)) & ((1u << ((hi) - (lo) + 1)) - 1))
#define BIT(val, n)        (((val) >> (n)) & 1u)

/* 符号扩展 */
static i32 sign_extend(u32 val, int bits) {
    u32 mask = 1u << (bits - 1);
    return (i32)((val ^ mask) - mask);
}

/* 获取指令格式 */
InsnFormat get_insn_format(Opcode opcode) {
    switch (opcode) {
        case OP_OP:    return FMT_R;
        case OP_LOAD:
        case OP_OP_IMM:
        case OP_JALR:
        case OP_SYSTEM: return FMT_I;
        case OP_STORE:  return FMT_S;
        case OP_BRANCH: return FMT_B;
        case OP_LUI:
        case OP_AUIPC:  return FMT_U;
        case OP_JAL:    return FMT_J;
        default:        return FMT_UNKNOWN;
    }
}

/* 解码指令 */
SimError decode_insn(u32 raw, DecodedInsn* out) {
    if (!out) return ERR_INVALID_INSN;

    memset(out, 0, sizeof(DecodedInsn));
    out->raw = raw;

    /* 提取公共字段 */
    u8 opcode = BITS(raw, 6, 0);
    out->opcode = (Opcode)opcode;
    out->rd     = BITS(raw, 11, 7);
    out->funct3 = BITS(raw, 14, 12);
    out->rs1    = BITS(raw, 19, 15);
    out->rs2    = BITS(raw, 24, 20);
    out->funct7 = BITS(raw, 31, 25);

    /* 根据格式解码立即数 */
    out->format = get_insn_format(out->opcode);

    switch (out->format) {
        case FMT_R:
            /* R-type 无立即数 */
            out->imm = 0;
            break;

        case FMT_I: {
            /* I-type: imm[11:0] = bits[31:20] */
            u32 imm = BITS(raw, 31, 20);
            out->imm = sign_extend(imm, 12);
            break;
        }

        case FMT_S: {
            /* S-type: imm[11:5] = bits[31:25], imm[4:0] = bits[11:7] */
            u32 imm = (BITS(raw, 31, 25) << 5) | BITS(raw, 11, 7);
            out->imm = sign_extend(imm, 12);
            break;
        }

        case FMT_B: {
            /* B-type:
             * imm[12]   = bit[31]
             * imm[10:5] = bits[30:25]
             * imm[4:1]  = bits[11:8]
             * imm[11]   = bit[7]
             * (imm[0] = 0, 隐含)
             */
            u32 imm = (BIT(raw, 31) << 12)
                    | (BIT(raw, 7)  << 11)
                    | (BITS(raw, 30, 25) << 5)
                    | (BITS(raw, 11, 8) << 1);
            out->imm = sign_extend(imm, 13);
            break;
        }

        case FMT_U: {
            /* U-type: imm[31:12] = bits[31:12] (低 12 位为 0) */
            out->imm = (i32)(BITS(raw, 31, 12) << 12);
            break;
        }

        case FMT_J: {
            /* J-type:
             * imm[20]    = bit[31]
             * imm[10:1]  = bits[30:21]
             * imm[11]    = bit[20]
             * imm[19:12] = bits[19:12]
             * (imm[0] = 0, 隐含)
             */
            u32 imm = (BIT(raw, 31) << 20)
                    | (BITS(raw, 19, 12) << 12)
                    | (BIT(raw, 20) << 11)
                    | (BITS(raw, 30, 21) << 1);
            out->imm = sign_extend(imm, 21);
            break;
        }

        default:
            return ERR_INVALID_INSN;
    }

    /* 设置指令名称 */
    out->name = get_insn_name(out);
    return ERR_OK;
}

/* 获取指令名称 (助记符) */
const char* get_insn_name(const DecodedInsn* insn) {
    if (!insn) return "???";

    switch (insn->opcode) {
        case OP_LUI:    return "LUI";
        case OP_AUIPC:  return "AUIPC";
        case OP_JAL:    return "JAL";
        case OP_JALR:   return "JALR";

        case OP_BRANCH:
            switch (insn->funct3) {
                case BRANCH_BEQ:  return "BEQ";
                case BRANCH_BNE:  return "BNE";
                case BRANCH_BLT:  return "BLT";
                case BRANCH_BGE:  return "BGE";
                case BRANCH_BLTU: return "BLTU";
                case BRANCH_BGEU: return "BGEU";
                default: return "BRANCH?";
            }

        case OP_LOAD:
            switch (insn->funct3) {
                case MEM_BYTE:  return "LB";
                case MEM_HALF:  return "LH";
                case MEM_WORD:  return "LW";
                case MEM_UBYTE: return "LBU";
                case MEM_UHALF: return "LHU";
                default: return "LOAD?";
            }

        case OP_STORE:
            switch (insn->funct3) {
                case MEM_BYTE: return "SB";
                case MEM_HALF: return "SH";
                case MEM_WORD: return "SW";
                default: return "STORE?";
            }

        case OP_OP_IMM:
            switch (insn->funct3) {
                case 0x0: return "ADDI";
                case 0x1: return "SLLI";
                case 0x2: return "SLTI";
                case 0x3: return "SLTIU";
                case 0x4: return "XORI";
                case 0x5: return (insn->funct7 & 0x20) ? "SRAI" : "SRLI";
                case 0x6: return "ORI";
                case 0x7: return "ANDI";
                default: return "OPIMM?";
            }

        case OP_OP:
            switch (insn->funct3) {
                case 0x0: return (insn->funct7 & 0x20) ? "SUB" : "ADD";
                case 0x1: return "SLL";
                case 0x2: return "SLT";
                case 0x3: return "SLTU";
                case 0x4: return "XOR";
                case 0x5: return (insn->funct7 & 0x20) ? "SRA" : "SRL";
                case 0x6: return "OR";
                case 0x7: return "AND";
                default: return "OP?";
            }

        case OP_SYSTEM:
            if (insn->funct3 == 0) {
                if (insn->imm == 0) return "ECALL";
                if (insn->imm == 1) return "EBREAK";
            }
            return "SYSTEM?";

        default: return "???";
    }
}

/* 格式化指令为汇编字符串 */
int format_insn(const DecodedInsn* insn, char* buf, size_t buf_size) {
    if (!insn || !buf || buf_size == 0) return -1;

    const char* name = insn->name;
    if (!name) name = "???";

    switch (insn->format) {
        case FMT_R:
            return snprintf(buf, buf_size, "%s %s, %s, %s",
                name,
                REG_ABI_NAMES[insn->rd],
                REG_ABI_NAMES[insn->rs1],
                REG_ABI_NAMES[insn->rs2]);

        case FMT_I:
            /* 特殊处理 JALR */
            if (insn->opcode == OP_JALR) {
                return snprintf(buf, buf_size, "%s %s, %s, %d",
                    name,
                    REG_ABI_NAMES[insn->rd],
                    REG_ABI_NAMES[insn->rs1],
                    insn->imm);
            }
            /* Load 指令: offset(rs1) */
            if (insn->opcode == OP_LOAD) {
                return snprintf(buf, buf_size, "%s %s, %d(%s)",
                    name,
                    REG_ABI_NAMES[insn->rd],
                    insn->imm,
                    REG_ABI_NAMES[insn->rs1]);
            }
            /* ECALL/EBREAK */
            if (insn->opcode == OP_SYSTEM && insn->funct3 == 0) {
                return snprintf(buf, buf_size, "%s", name);
            }
            /* I-type ALU */
            return snprintf(buf, buf_size, "%s %s, %s, %d",
                name,
                REG_ABI_NAMES[insn->rd],
                REG_ABI_NAMES[insn->rs1],
                insn->imm);

        case FMT_S:
            return snprintf(buf, buf_size, "%s %s, %d(%s)",
                name,
                REG_ABI_NAMES[insn->rs2],
                insn->imm,
                REG_ABI_NAMES[insn->rs1]);

        case FMT_B:
            return snprintf(buf, buf_size, "%s %s, %s, %d",
                name,
                REG_ABI_NAMES[insn->rs1],
                REG_ABI_NAMES[insn->rs2],
                insn->imm);

        case FMT_U:
            return snprintf(buf, buf_size, "%s %s, 0x%X",
                name,
                REG_ABI_NAMES[insn->rd],
                (u32)insn->imm >> 12);

        case FMT_J:
            return snprintf(buf, buf_size, "%s %s, %d",
                name,
                REG_ABI_NAMES[insn->rd],
                insn->imm);

        default:
            return snprintf(buf, buf_size, "??? (0x%08X)", insn->raw);
    }
}

void dump_insn(const DecodedInsn* insn) {
    if (!insn) return;

    char buf[128];
    format_insn(insn, buf, sizeof(buf));
    printf("0x%08X: %-30s  [raw=0x%08X]\n", insn->raw, buf, insn->raw);
}
