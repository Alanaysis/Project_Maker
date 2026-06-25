#include "assembler.h"
#include "decoder.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <ctype.h>
#include <errno.h>

/* ============================================================
 * 简单汇编器实现
 * 支持标签 (labels) 和两遍汇编
 * ============================================================ */

/* 标签符号表 */
#define MAX_LABELS 256

typedef struct {
    char name[64];
    u32  addr;
} Label;

typedef struct {
    Label labels[MAX_LABELS];
    int   count;
} SymbolTable;

/* 跳过空白 */
static const char* skip_ws(const char* s) {
    while (*s && isspace((unsigned char)*s)) s++;
    return s;
}

/* 解析寄存器名称 */
int asm_parse_register(const char* name) {
    while (*name && isspace((unsigned char)*name)) name++;

    if (name[0] == 'x' && isdigit((unsigned char)name[1])) {
        int num = atoi(name + 1);
        if (num >= 0 && num <= 31) return num;
    }

    for (int i = 0; i < 32; i++) {
        if (strncmp(name, REG_ABI_NAMES[i], strlen(REG_ABI_NAMES[i])) == 0) {
            char next = name[strlen(REG_ABI_NAMES[i])];
            if (next == '\0' || next == ',' || next == ' ' || next == '\t' ||
                next == '(' || next == ')') {
                return i;
            }
        }
    }

    return -1;
}

/* 解析立即数 */
SimError asm_parse_imm(const char* str, i32* out) {
    if (!str || !out) return ERR_INVALID_INSN;

    str = skip_ws(str);
    if (*str == '\0') return ERR_INVALID_INSN;

    char* end;
    long val;

    if (str[0] == '0' && (str[1] == 'x' || str[1] == 'X')) {
        val = strtol(str, &end, 16);
    } else {
        val = strtol(str, &end, 10);
    }

    if (end == str) return ERR_INVALID_INSN;
    *out = (i32)val;
    return ERR_OK;
}

/* 在符号表中查找标签 */
static bool find_label(const SymbolTable* st, const char* name, u32* out_addr) {
    for (int i = 0; i < st->count; i++) {
        if (strcmp(st->labels[i].name, name) == 0) {
            *out_addr = st->labels[i].addr;
            return true;
        }
    }
    return false;
}

/* 编码指令 */
static u32 encode_r(u8 funct7, u8 rs2, u8 rs1, u8 funct3, u8 rd, u8 opcode) {
    return ((u32)funct7 << 25) | ((u32)rs2 << 20) | ((u32)rs1 << 15) |
           ((u32)funct3 << 12) | ((u32)rd << 7)   | opcode;
}

static u32 encode_i(i32 imm, u8 rs1, u8 funct3, u8 rd, u8 opcode) {
    return (((u32)imm & 0xFFF) << 20) | ((u32)rs1 << 15) |
           ((u32)funct3 << 12) | ((u32)rd << 7) | opcode;
}

static u32 encode_s(i32 imm, u8 rs2, u8 rs1, u8 funct3, u8 opcode) {
    u32 imm11_5 = ((u32)imm >> 5) & 0x7F;
    u32 imm4_0  = (u32)imm & 0x1F;
    return (imm11_5 << 25) | ((u32)rs2 << 20) | ((u32)rs1 << 15) |
           ((u32)funct3 << 12) | (imm4_0 << 7) | opcode;
}

static u32 encode_b(i32 imm, u8 rs2, u8 rs1, u8 funct3, u8 opcode) {
    u32 imm12   = ((u32)imm >> 12) & 1;
    u32 imm10_5 = ((u32)imm >> 5)  & 0x3F;
    u32 imm4_1  = ((u32)imm >> 1)  & 0xF;
    u32 imm11   = ((u32)imm >> 11) & 1;
    return (imm12 << 31) | (imm10_5 << 25) | ((u32)rs2 << 20) |
           ((u32)rs1 << 15) | ((u32)funct3 << 12) |
           (imm4_1 << 8) | (imm11 << 7) | opcode;
}

static u32 encode_u(i32 imm, u8 rd, u8 opcode) {
    return ((u32)imm & 0xFFFFF000) | ((u32)rd << 7) | opcode;
}

static u32 encode_j(i32 imm, u8 rd, u8 opcode) {
    u32 imm20    = ((u32)imm >> 20) & 1;
    u32 imm10_1  = ((u32)imm >> 1)  & 0x3FF;
    u32 imm11    = ((u32)imm >> 11) & 1;
    u32 imm19_12 = ((u32)imm >> 12) & 0xFF;
    return (imm20 << 31) | (imm10_1 << 21) | (imm11 << 20) |
           (imm19_12 << 12) | ((u32)rd << 7) | opcode;
}

/* 解析 "offset(rs1)" 格式 */
static SimError parse_mem_operand(const char* str, i32* offset, int* rs1) {
    const char* p = skip_ws(str);

    char* end;
    long val = strtol(p, &end, 10);
    if (end == p) {
        val = 0;
        end = (char*)p;
    }

    *offset = (i32)val;

    end = (char*)skip_ws(end);
    if (*end != '(') return ERR_INVALID_INSN;
    end++;

    char reg_buf[16];
    int ri = 0;
    while (*end && *end != ')' && ri < 15) {
        reg_buf[ri++] = *end++;
    }
    reg_buf[ri] = '\0';

    if (*end != ')') return ERR_INVALID_INSN;

    *rs1 = asm_parse_register(reg_buf);
    if (*rs1 < 0) return ERR_INVALID_REG;

    return ERR_OK;
}

/* 解析操作数 (可能是立即数或标签) */
static SimError parse_operand(const char* str, const SymbolTable* st, u32 pc, i32* out) {
    str = skip_ws(str);
    if (*str == '\0') return ERR_INVALID_INSN;

    /* 尝试解析为立即数 */
    i32 imm;
    if (asm_parse_imm(str, &imm) == ERR_OK) {
        *out = imm;
        return ERR_OK;
    }

    /* 尝试解析为标签 */
    if (st) {
        char label[64];
        int i = 0;
        while (*str && !isspace((unsigned char)*str) && *str != ',' && i < 63) {
            label[i++] = *str++;
        }
        label[i] = '\0';

        u32 addr;
        if (find_label(st, label, &addr)) {
            /* 返回相对于当前 PC 的偏移 */
            *out = (i32)(addr - pc);
            return ERR_OK;
        }
    }

    return ERR_INVALID_INSN;
}

/* 汇编单条指令 */
static SimError asm_assemble_one(const char* line, u32 pc, u32* out,
                                  const SymbolTable* st) {
    if (!line || !out) return ERR_INVALID_INSN;

    const char* p = skip_ws(line);
    if (*p == '\0' || *p == '#' || *p == ';') return ERR_INVALID_INSN;

    /* 检查是否是标签 (包含 ':') */
    const char* colon = strchr(p, ':');
    if (colon) {
        /* 跳过标签行 */
        return ERR_INVALID_INSN;
    }

    char upper[256];
    int i = 0;
    while (*p && !isspace((unsigned char)*p) && i < 255) {
        upper[i++] = toupper((unsigned char)*p);
        p++;
    }
    upper[i] = '\0';
    p = skip_ws(p);

    /* ---- U-type: LUI / AUIPC ---- */
    if (strcmp(upper, "LUI") == 0) {
        int rd; i32 imm;
        char rd_buf[16], imm_buf[32];
        if (sscanf(p, " %15[^,], %31s", rd_buf, imm_buf) != 2)
            return ERR_INVALID_INSN;
        rd = asm_parse_register(rd_buf);
        if (rd < 0) return ERR_INVALID_REG;
        if (asm_parse_imm(imm_buf, &imm) != ERR_OK) return ERR_INVALID_INSN;
        *out = encode_u(imm << 12, rd, OP_LUI);
        return ERR_OK;
    }
    if (strcmp(upper, "AUIPC") == 0) {
        int rd; i32 imm;
        char rd_buf[16], imm_buf[32];
        if (sscanf(p, " %15[^,], %31s", rd_buf, imm_buf) != 2)
            return ERR_INVALID_INSN;
        rd = asm_parse_register(rd_buf);
        if (rd < 0) return ERR_INVALID_REG;
        if (asm_parse_imm(imm_buf, &imm) != ERR_OK) return ERR_INVALID_INSN;
        *out = encode_u(imm << 12, rd, OP_AUIPC);
        return ERR_OK;
    }

    /* ---- J-type: JAL ---- */
    if (strcmp(upper, "JAL") == 0) {
        int rd; i32 imm;
        char buf1[16], buf2[32];
        int n = sscanf(p, " %15[^,], %31s", buf1, buf2);
        if (n == 2) {
            rd = asm_parse_register(buf1);
            if (rd < 0) return ERR_INVALID_INSN;
            if (parse_operand(buf2, st, pc, &imm) != ERR_OK) return ERR_INVALID_INSN;
        } else if (n == 1) {
            rd = 1;
            if (parse_operand(buf1, st, pc, &imm) != ERR_OK) return ERR_INVALID_INSN;
        } else {
            return ERR_INVALID_INSN;
        }
        *out = encode_j(imm, rd, OP_JAL);
        return ERR_OK;
    }

    /* ---- I-type jump: JALR ---- */
    if (strcmp(upper, "JALR") == 0) {
        int rd, rs1; i32 imm;
        char buf1[16], buf2[16], buf3[32];
        int n = sscanf(p, " %15[^,], %15[^,], %31s", buf1, buf2, buf3);
        if (n == 3) {
            rd = asm_parse_register(buf1);
            rs1 = asm_parse_register(buf2);
            if (asm_parse_imm(buf3, &imm) != ERR_OK) return ERR_INVALID_INSN;
        } else if (n == 2) {
            rd = 1;
            rs1 = asm_parse_register(buf1);
            if (asm_parse_imm(buf2, &imm) != ERR_OK) return ERR_INVALID_INSN;
        } else {
            return ERR_INVALID_INSN;
        }
        if (rd < 0 || rs1 < 0) return ERR_INVALID_REG;
        *out = encode_i(imm, rs1, 0, rd, OP_JALR);
        return ERR_OK;
    }

    /* ---- B-type: BEQ/BNE/BLT/BGE/BLTU/BGEU ---- */
    {
        int br_funct3 = -1;
        if (strcmp(upper, "BEQ")  == 0) br_funct3 = BRANCH_BEQ;
        if (strcmp(upper, "BNE")  == 0) br_funct3 = BRANCH_BNE;
        if (strcmp(upper, "BLT")  == 0) br_funct3 = BRANCH_BLT;
        if (strcmp(upper, "BGE")  == 0) br_funct3 = BRANCH_BGE;
        if (strcmp(upper, "BLTU") == 0) br_funct3 = BRANCH_BLTU;
        if (strcmp(upper, "BGEU") == 0) br_funct3 = BRANCH_BGEU;

        if (br_funct3 >= 0) {
            int rs1, rs2; i32 imm;
            char buf1[16], buf2[16], buf3[32];
            if (sscanf(p, " %15[^,], %15[^,], %31s", buf1, buf2, buf3) != 3)
                return ERR_INVALID_INSN;
            rs1 = asm_parse_register(buf1);
            rs2 = asm_parse_register(buf2);
            if (rs1 < 0 || rs2 < 0) return ERR_INVALID_REG;
            if (parse_operand(buf3, st, pc, &imm) != ERR_OK) return ERR_INVALID_INSN;
            *out = encode_b(imm, rs2, rs1, (u8)br_funct3, OP_BRANCH);
            return ERR_OK;
        }
    }

    /* ---- Load: LB/LH/LW/LBU/LHU ---- */
    {
        int ld_funct3 = -1;
        if (strcmp(upper, "LB")  == 0) ld_funct3 = MEM_BYTE;
        if (strcmp(upper, "LH")  == 0) ld_funct3 = MEM_HALF;
        if (strcmp(upper, "LW")  == 0) ld_funct3 = MEM_WORD;
        if (strcmp(upper, "LBU") == 0) ld_funct3 = MEM_UBYTE;
        if (strcmp(upper, "LHU") == 0) ld_funct3 = MEM_UHALF;

        if (ld_funct3 >= 0) {
            int rd, rs1; i32 offset;
            char rd_buf[16], mem_buf[64];
            if (sscanf(p, " %15[^,], %63s", rd_buf, mem_buf) != 2)
                return ERR_INVALID_INSN;
            rd = asm_parse_register(rd_buf);
            if (rd < 0) return ERR_INVALID_REG;
            if (parse_mem_operand(mem_buf, &offset, &rs1) != ERR_OK)
                return ERR_INVALID_INSN;
            *out = encode_i(offset, rs1, (u8)ld_funct3, rd, OP_LOAD);
            return ERR_OK;
        }
    }

    /* ---- Store: SB/SH/SW ---- */
    {
        int st_funct3 = -1;
        if (strcmp(upper, "SB") == 0) st_funct3 = MEM_BYTE;
        if (strcmp(upper, "SH") == 0) st_funct3 = MEM_HALF;
        if (strcmp(upper, "SW") == 0) st_funct3 = MEM_WORD;

        if (st_funct3 >= 0) {
            int rs2, rs1; i32 offset;
            char rs2_buf[16], mem_buf[64];
            if (sscanf(p, " %15[^,], %63s", rs2_buf, mem_buf) != 2)
                return ERR_INVALID_INSN;
            rs2 = asm_parse_register(rs2_buf);
            if (rs2 < 0) return ERR_INVALID_REG;
            if (parse_mem_operand(mem_buf, &offset, &rs1) != ERR_OK)
                return ERR_INVALID_INSN;
            *out = encode_s(offset, rs2, rs1, (u8)st_funct3, OP_STORE);
            return ERR_OK;
        }
    }

    /* ---- I-type ALU ---- */
    {
        int i_funct3 = -1;
        bool is_shift = false;
        if (strcmp(upper, "ADDI")  == 0) i_funct3 = 0x0;
        if (strcmp(upper, "SLTI")  == 0) i_funct3 = 0x2;
        if (strcmp(upper, "SLTIU") == 0) i_funct3 = 0x3;
        if (strcmp(upper, "XORI")  == 0) i_funct3 = 0x4;
        if (strcmp(upper, "ORI")   == 0) i_funct3 = 0x6;
        if (strcmp(upper, "ANDI")  == 0) i_funct3 = 0x7;
        if (strcmp(upper, "SLLI")  == 0) { i_funct3 = 0x1; is_shift = true; }
        if (strcmp(upper, "SRLI")  == 0) { i_funct3 = 0x5; is_shift = true; }
        if (strcmp(upper, "SRAI")  == 0) { i_funct3 = 0x5; is_shift = true; }

        if (i_funct3 >= 0) {
            int rd, rs1; i32 imm;
            char buf1[16], buf2[16], buf3[32];
            if (sscanf(p, " %15[^,], %15[^,], %31s", buf1, buf2, buf3) != 3)
                return ERR_INVALID_INSN;
            rd  = asm_parse_register(buf1);
            rs1 = asm_parse_register(buf2);
            if (rd < 0 || rs1 < 0) return ERR_INVALID_REG;
            if (asm_parse_imm(buf3, &imm) != ERR_OK) return ERR_INVALID_INSN;

            u8 funct7 = 0;
            if (strcmp(upper, "SRAI") == 0) funct7 = 0x20;

            if (is_shift) {
                *out = encode_i((i32)(((u32)funct7 << 5) | (imm & 0x1F)),
                               rs1, (u8)i_funct3, rd, OP_OP_IMM);
            } else {
                *out = encode_i(imm, rs1, (u8)i_funct3, rd, OP_OP_IMM);
            }
            return ERR_OK;
        }
    }

    /* ---- R-type ---- */
    {
        u8 r_funct3 = 0;
        u8 r_funct7 = 0;
        bool is_r = false;

        if (strcmp(upper, "ADD")  == 0) { r_funct3 = 0x0; r_funct7 = 0x00; is_r = true; }
        if (strcmp(upper, "SUB")  == 0) { r_funct3 = 0x0; r_funct7 = 0x20; is_r = true; }
        if (strcmp(upper, "SLL")  == 0) { r_funct3 = 0x1; r_funct7 = 0x00; is_r = true; }
        if (strcmp(upper, "SLT")  == 0) { r_funct3 = 0x2; r_funct7 = 0x00; is_r = true; }
        if (strcmp(upper, "SLTU") == 0) { r_funct3 = 0x3; r_funct7 = 0x00; is_r = true; }
        if (strcmp(upper, "XOR")  == 0) { r_funct3 = 0x4; r_funct7 = 0x00; is_r = true; }
        if (strcmp(upper, "SRL")  == 0) { r_funct3 = 0x5; r_funct7 = 0x00; is_r = true; }
        if (strcmp(upper, "SRA")  == 0) { r_funct3 = 0x5; r_funct7 = 0x20; is_r = true; }
        if (strcmp(upper, "OR")   == 0) { r_funct3 = 0x6; r_funct7 = 0x00; is_r = true; }
        if (strcmp(upper, "AND")  == 0) { r_funct3 = 0x7; r_funct7 = 0x00; is_r = true; }

        if (is_r) {
            int rd, rs1, rs2;
            char buf1[16], buf2[16], buf3[16];
            if (sscanf(p, " %15[^,], %15[^,], %15s", buf1, buf2, buf3) != 3)
                return ERR_INVALID_INSN;
            rd  = asm_parse_register(buf1);
            rs1 = asm_parse_register(buf2);
            rs2 = asm_parse_register(buf3);
            if (rd < 0 || rs1 < 0 || rs2 < 0) return ERR_INVALID_REG;
            *out = encode_r(r_funct7, (u8)rs2, (u8)rs1, r_funct3, (u8)rd, OP_OP);
            return ERR_OK;
        }
    }

    /* ---- System: ECALL / EBREAK ---- */
    if (strcmp(upper, "ECALL") == 0) {
        *out = encode_i(0, 0, 0, 0, OP_SYSTEM);
        return ERR_OK;
    }
    if (strcmp(upper, "EBREAK") == 0) {
        *out = encode_i(1, 0, 0, 0, OP_SYSTEM);
        return ERR_OK;
    }

    fprintf(stderr, "Unknown mnemonic: '%s'\n", upper);
    return ERR_INVALID_INSN;
}

/* 提取一行 */
static const char* extract_line(const char* p, char* line, int max_len) {
    int li = 0;
    while (*p && *p != '\n' && li < max_len - 1) {
        line[li++] = *p++;
    }
    line[li] = '\0';
    if (*p == '\n') p++;

    /* 去掉行内注释 */
    for (int i = 0; line[i]; i++) {
        if (line[i] == '#' || line[i] == ';') {
            line[i] = '\0';
            break;
        }
    }

    return p;
}

/* 判断是否是标签行 */
static bool is_label_line(const char* line) {
    const char* p = skip_ws(line);
    if (*p == '\0' || *p == '#' || *p == ';') return false;
    return strchr(p, ':') != NULL;
}

/* 提取标签名 */
static void extract_label(const char* line, char* name, int max_len) {
    const char* p = skip_ws(line);
    int i = 0;
    while (*p && *p != ':' && !isspace((unsigned char)*p) && i < max_len - 1) {
        name[i++] = *p++;
    }
    name[i] = '\0';
}

AsmContext* asm_create(u32 start_pc) {
    AsmContext* ctx = (AsmContext*)calloc(1, sizeof(AsmContext));
    if (!ctx) return NULL;

    ctx->pc = start_pc;
    ctx->code_capacity = 4096;
    ctx->code = (u32*)calloc(ctx->code_capacity / 4, sizeof(u32));
    if (!ctx->code) {
        free(ctx);
        return NULL;
    }
    ctx->code_size = 0;
    return ctx;
}

void asm_destroy(AsmContext* ctx) {
    if (ctx) {
        free(ctx->code);
        free(ctx);
    }
}

SimError asm_assemble(AsmContext* ctx, const char* text) {
    if (!ctx || !text) return ERR_INVALID_INSN;

    SymbolTable st;
    st.count = 0;

    const char* p = text;
    u32 start_pc = ctx->pc - ctx->code_size;  /* 保存起始 PC */

    /* ===== 第一遍: 收集标签 ===== */
    u32 scan_pc = start_pc;
    const char* scan_p = text;

    while (*scan_p) {
        scan_p = skip_ws(scan_p);
        if (*scan_p == '\0') break;

        if (*scan_p == '#' || *scan_p == ';') {
            while (*scan_p && *scan_p != '\n') scan_p++;
            continue;
        }

        char line[256];
        scan_p = extract_line(scan_p, line, 256);

        /* 跳过空行 */
        const char* lp = skip_ws(line);
        if (*lp == '\0') continue;

        if (is_label_line(line)) {
            /* 记录标签 */
            if (st.count < MAX_LABELS) {
                extract_label(line, st.labels[st.count].name, 64);
                st.labels[st.count].addr = scan_pc;
                st.count++;
            }
            /* 标签行不占用指令空间 */
        } else {
            scan_pc += 4;  /* 每条指令 4 字节 */
        }
    }

    /* ===== 第二遍: 汇编指令 ===== */
    ctx->pc = start_pc;
    ctx->code_size = 0;

    while (*p) {
        p = skip_ws(p);
        if (*p == '\0') break;

        if (*p == '#' || *p == ';') {
            while (*p && *p != '\n') p++;
            continue;
        }

        char line[256];
        p = extract_line(p, line, 256);

        const char* lp = skip_ws(line);
        if (*lp == '\0') continue;

        /* 跳过标签行 */
        if (is_label_line(line)) continue;

        /* 汇编指令 */
        u32 insn;
        SimError err = asm_assemble_one(line, ctx->pc, &insn, &st);
        if (err != ERR_OK) continue;

        /* 存入代码缓冲区 */
        u32 idx = ctx->code_size / 4;
        if (ctx->code_size + 4 > ctx->code_capacity) {
            u32 new_cap = ctx->code_capacity * 2;
            u32* new_code = (u32*)realloc(ctx->code, new_cap);
            if (!new_code) return ERR_MEMORY_FAULT;
            ctx->code = new_code;
            ctx->code_capacity = new_cap;
        }
        ctx->code[idx] = insn;
        ctx->code_size += 4;
        ctx->pc += 4;
    }

    return ERR_OK;
}

SimError asm_assemble_one_wrapper(const char* line, u32 pc, u32* out) {
    return asm_assemble_one(line, pc, out, NULL);
}

void asm_dump(AsmContext* ctx) {
    if (!ctx) return;

    printf("=== Assembler Output ===\n");
    printf("  Code size: %u bytes\n", ctx->code_size);
    printf("  Start PC: 0x%08X\n", ctx->pc - ctx->code_size);

    u32 pc = ctx->pc - ctx->code_size;
    for (u32 i = 0; i < ctx->code_size / 4; i++) {
        DecodedInsn decoded;
        if (decode_insn(ctx->code[i], &decoded) == ERR_OK) {
            char buf[128];
            format_insn(&decoded, buf, sizeof(buf));
            printf("  0x%08X: 0x%08X  %s\n", pc, ctx->code[i], buf);
        }
        pc += 4;
    }
}
