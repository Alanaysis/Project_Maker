#ifndef RISCV_H
#define RISCV_H

#include <stdint.h>
#include <stdbool.h>
#include <stddef.h>

/* ============================================================
 * RISC-V 指令集模拟器 - 主头文件
 * 支持 RV32I 基本整数指令集
 * ============================================================ */

/* 版本信息 */
#define RISCV_SIM_VERSION "1.0.0"
#define RISCV_SIM_NAME    "RISC-V Simulator"

/* ============================================================
 * 基础类型定义
 * ============================================================ */

/* RISC-V 类型 */
typedef uint64_t u64;
typedef int64_t  i64;
typedef uint32_t u32;
typedef int32_t  i32;
typedef uint16_t u16;
typedef int16_t  i16;
typedef uint8_t  u8;
typedef int8_t   i8;

/* ============================================================
 * 寄存器定义
 * ============================================================ */

/* 寄存器数量 */
#define NUM_REGS 32

/* 寄存器 ABI 名称 */
static const char* const REG_ABI_NAMES[32] = {
    "zero", "ra",  "sp",  "gp",  "tp", "t0", "t1", "t2",
    "s0",   "s1",  "a0",  "a1",  "a2", "a3", "a4", "a5",
    "a6",   "a7",  "s2",  "s3",  "s4", "s5", "s6", "s7",
    "s8",   "s9",  "s10", "s11", "t3", "t4", "t5", "t6"
};

/* 寄存器索引枚举 */
typedef enum {
    REG_ZERO = 0,   /* 硬连线零 */
    REG_RA   = 1,   /* 返回地址 */
    REG_SP   = 2,   /* 栈指针 */
    REG_GP   = 3,   /* 全局指针 */
    REG_TP   = 4,   /* 线程指针 */
    REG_T0   = 5,   /* 临时寄存器 */
    REG_T1   = 6,
    REG_T2   = 7,
    REG_S0   = 8,   /* 保存寄存器 / 帧指针 */
    REG_S1   = 9,
    REG_A0   = 10,  /* 参数/返回值 */
    REG_A1   = 11,
    REG_A2   = 12,
    REG_A3   = 13,
    REG_A4   = 14,
    REG_A5   = 15,
    REG_A6   = 16,
    REG_A7   = 17,
    REG_S2   = 18,
    REG_S3   = 19,
    REG_S4   = 20,
    REG_S5   = 21,
    REG_S6   = 22,
    REG_S7   = 23,
    REG_S8   = 24,
    REG_S9   = 25,
    REG_S10  = 26,
    REG_S11  = 27,
    REG_T3   = 28,
    REG_T4   = 29,
    REG_T5   = 30,
    REG_T6   = 31
} RegIndex;

/* ============================================================
 * 指令格式定义
 * ============================================================ */

/* RISC-V 指令格式类型 */
typedef enum {
    FMT_R,  /* R-type: 寄存器-寄存器运算 */
    FMT_I,  /* I-type: 立即数运算 / 加载 */
    FMT_S,  /* S-type: 存储 */
    FMT_B,  /* B-type: 条件分支 */
    FMT_U,  /* U-type: 高位立即数 */
    FMT_J,  /* J-type: 跳转 */
    FMT_UNKNOWN
} InsnFormat;

/* RV32I 操作码 (opcode) */
typedef enum {
    /* R-type */
    OP_LUI    = 0x37,  /* Load Upper Immediate */
    OP_AUIPC  = 0x17,  /* Add Upper Immediate to PC */
    OP_JAL    = 0x6F,  /* Jump and Link */
    OP_JALR   = 0x67,  /* Jump and Link Register */

    /* B-type (分支) */
    OP_BRANCH = 0x63,

    /* Load (I-type) */
    OP_LOAD   = 0x03,

    /* Store (S-type) */
    OP_STORE  = 0x23,

    /* I-type ALU */
    OP_OP_IMM = 0x13,

    /* R-type ALU */
    OP_OP     = 0x33,

    /* SYSTEM */
    OP_SYSTEM = 0x73,
} Opcode;

/* ALU 功能码 (funct7 << 3 | funct3) */
typedef enum {
    /* OP_OP / OP_OP_IMM 共用 */
    ALU_ADD  = 0x000,  /* ADD / ADDI  (funct7=0x00, funct3=0x0) */
    ALU_SLL  = 0x001,  /* SLL / SLLI  (funct7=0x00, funct3=0x1) */
    ALU_SLT  = 0x002,  /* SLT / SLTI  (funct7=0x00, funct3=0x2) */
    ALU_SLTU = 0x003,  /* SLTU / SLTIU (funct7=0x00, funct3=0x3) */
    ALU_XOR  = 0x004,  /* XOR / XORI  (funct7=0x00, funct3=0x4) */
    ALU_SRL  = 0x005,  /* SRL / SRLI  (funct7=0x00, funct3=0x5) */
    ALU_SRA  = 0x105,  /* SRA / SRAI  (funct7=0x20, funct3=0x5) */
    ALU_OR   = 0x006,  /* OR / ORI    (funct7=0x00, funct3=0x6) */
    ALU_AND  = 0x007,  /* AND / ANDI  (funct7=0x00, funct3=0x7) */
    ALU_SUB  = 0x100,  /* SUB         (funct7=0x20, funct3=0x0) */
} AluOp;

/* 分支功能码 */
typedef enum {
    BRANCH_BEQ  = 0x0,  /* 相等 */
    BRANCH_BNE  = 0x1,  /* 不等 */
    BRANCH_BLT  = 0x4,  /* 小于 (有符号) */
    BRANCH_BGE  = 0x5,  /* 大于等于 (有符号) */
    BRANCH_BLTU = 0x6,  /* 小于 (无符号) */
    BRANCH_BGEU = 0x7,  /* 大于等于 (无符号) */
} BranchFunc;

/* Load/Store 功能码 */
typedef enum {
    MEM_BYTE  = 0x0,  /* LB / SB */
    MEM_HALF  = 0x1,  /* LH / SH */
    MEM_WORD  = 0x2,  /* LW / SW */
    MEM_UBYTE = 0x4,  /* LBU */
    MEM_UHALF = 0x5,  /* LHU */
} MemFunc;

/* ============================================================
 * 解码后的指令结构
 * ============================================================ */

typedef struct {
    u32         raw;       /* 原始 32 位指令 */
    InsnFormat  format;    /* 指令格式 */
    Opcode      opcode;    /* 操作码 */
    u8          rd;        /* 目标寄存器 */
    u8          rs1;       /* 源寄存器 1 */
    u8          rs2;       /* 源寄存器 2 */
    u8          funct3;    /* 功能码 3 位 */
    u8          funct7;    /* 功能码 7 位 */
    i32         imm;       /* 立即数 (已符号扩展) */
    const char* name;      /* 助记符名称 */
} DecodedInsn;

/* ============================================================
 * 错误码
 * ============================================================ */

typedef enum {
    ERR_OK = 0,
    ERR_INVALID_INSN,      /* 无效指令 */
    ERR_INVALID_REG,       /* 无效寄存器 */
    ERR_MEMORY_FAULT,      /* 内存访问错误 */
    ERR_UNALIGNED_ACCESS,  /* 未对齐访问 */
    ERR_BREAKPOINT,        /* 断点 (EBREAK) */
    ERR_HALT,              /* 程序停止 */
} SimError;

/* ============================================================
 * 调试级别
 * ============================================================ */

typedef enum {
    DEBUG_NONE  = 0,
    DEBUG_ERROR = 1,
    DEBUG_WARN  = 2,
    DEBUG_INFO  = 3,
    DEBUG_TRACE = 4,
} DebugLevel;

#endif /* RISCV_H */
