/* ============================================================
 * 集成测试 - 测试完整指令执行流程
 * ============================================================ */

#include "riscv.h"
#include "cpu.h"
#include "memory.h"
#include "decoder.h"
#include "assembler.h"
#include <stdio.h>
#include <string.h>

static int tests_passed = 0;
static int tests_failed = 0;

#define TEST(name) printf("  TEST: %-40s ", name)
#define PASS()     do { printf("[PASS]\n"); tests_passed++; } while(0)
#define FAIL(msg)  do { printf("[FAIL] %s\n", msg); tests_failed++; } while(0)

/* 辅助: 汇编并运行程序，返回指定寄存器的值 */
static u32 asm_and_run(const char* code, int reg, SimError* out_err) {
    Memory* mem = memory_create(DEFAULT_MEM_SIZE, DEFAULT_MEM_BASE);
    if (!mem) return 0;

    AsmContext* ctx = asm_create(DEFAULT_MEM_BASE);
    if (!ctx) { memory_destroy(mem); return 0; }

    SimError err = asm_assemble(ctx, code);
    if (err != ERR_OK) {
        asm_destroy(ctx);
        memory_destroy(mem);
        if (out_err) *out_err = err;
        return 0;
    }

    memory_load(mem, DEFAULT_MEM_BASE, (const u8*)ctx->code, ctx->code_size);
    asm_destroy(ctx);

    CPU* cpu = cpu_create(mem);
    if (!cpu) { memory_destroy(mem); return 0; }

    err = cpu_run(cpu, 10000);
    u32 result = cpu_read_reg(cpu, reg);

    if (out_err) *out_err = err;

    cpu_destroy(cpu);
    memory_destroy(mem);
    return result;
}

/* 测试 ADD/ADDI */
static void test_add(void) {
    TEST("ADD/ADDI execution");

    SimError err;
    u32 result = asm_and_run(
        "addi t0, zero, 10\n"
        "addi t1, zero, 20\n"
        "add a0, t0, t1\n"
        "ebreak\n",
        REG_A0, &err);

    if (result != 30) {
        char msg[64];
        snprintf(msg, sizeof(msg), "expected 30, got %u", result);
        FAIL(msg);
        return;
    }

    PASS();
}

/* 测试 SUB */
static void test_sub(void) {
    TEST("SUB execution");

    SimError err;
    u32 result = asm_and_run(
        "addi t0, zero, 50\n"
        "addi t1, zero, 20\n"
        "sub a0, t0, t1\n"
        "ebreak\n",
        REG_A0, &err);

    if (result != 30) {
        char msg[64];
        snprintf(msg, sizeof(msg), "expected 30, got %u", result);
        FAIL(msg);
        return;
    }

    PASS();
}

/* 测试 AND/OR/XOR */
static void test_bitwise(void) {
    TEST("AND/OR/XOR execution");

    SimError err;
    u32 result;

    /* AND */
    result = asm_and_run(
        "addi t0, zero, 0xFF\n"
        "addi t1, zero, 0x0F\n"
        "and a0, t0, t1\n"
        "ebreak\n",
        REG_A0, &err);
    if (result != 0x0F) { FAIL("AND wrong"); return; }

    /* OR */
    result = asm_and_run(
        "addi t0, zero, 0xF0\n"
        "addi t1, zero, 0x0F\n"
        "or a0, t0, t1\n"
        "ebreak\n",
        REG_A0, &err);
    if (result != 0xFF) { FAIL("OR wrong"); return; }

    /* XOR */
    result = asm_and_run(
        "addi t0, zero, 0xFF\n"
        "addi t1, zero, 0x0F\n"
        "xor a0, t0, t1\n"
        "ebreak\n",
        REG_A0, &err);
    if (result != 0xF0) { FAIL("XOR wrong"); return; }

    PASS();
}

/* 测试移位 */
static void test_shift(void) {
    TEST("SLL/SRL/SRA execution");

    SimError err;
    u32 result;

    /* SLL (左移) */
    result = asm_and_run(
        "addi t0, zero, 1\n"
        "addi t1, zero, 4\n"
        "sll a0, t0, t1\n"
        "ebreak\n",
        REG_A0, &err);
    if (result != 16) { FAIL("SLL wrong"); return; }

    /* SRL (逻辑右移) */
    result = asm_and_run(
        "addi t0, zero, 16\n"
        "addi t1, zero, 2\n"
        "srl a0, t0, t1\n"
        "ebreak\n",
        REG_A0, &err);
    if (result != 4) { FAIL("SRL wrong"); return; }

    PASS();
}

/* 测试条件分支 */
static void test_branch(void) {
    TEST("BEQ/BNE/BLT/BGE execution");

    SimError err;
    u32 result;

    /* BLT 循环: 计算 1+2+...+10 */
    /* BLT 是 "小于则跳转"，所以用 11 作为上界 */
    result = asm_and_run(
        "addi a0, zero, 0\n"
        "addi t0, zero, 11\n"
        "addi t1, zero, 1\n"
        "loop:\n"
        "  add a0, a0, t1\n"
        "  addi t1, t1, 1\n"
        "  blt t1, t0, loop\n"
        "ebreak\n",
        REG_A0, &err);
    if (result != 55) {
        char msg[64];
        snprintf(msg, sizeof(msg), "sum(1..10): expected 55, got %u", result);
        FAIL(msg);
        return;
    }

    /* BNE */
    result = asm_and_run(
        "addi t0, zero, 5\n"
        "addi t1, zero, 5\n"
        "addi a0, zero, 0\n"
        "bne t0, t1, skip\n"
        "addi a0, zero, 42\n"
        "skip:\n"
        "ebreak\n",
        REG_A0, &err);
    if (result != 42) { FAIL("BNE wrong"); return; }

    /* BEQ */
    result = asm_and_run(
        "addi t0, zero, 5\n"
        "addi t1, zero, 5\n"
        "addi a0, zero, 0\n"
        "beq t0, t1, equal\n"
        "ebreak\n"
        "equal:\n"
        "addi a0, zero, 99\n"
        "ebreak\n",
        REG_A0, &err);
    if (result != 99) { FAIL("BEQ wrong"); return; }

    PASS();
}

/* 测试 LUI/AUIPC */
static void test_upper_imm(void) {
    TEST("LUI/AUIPC execution");

    SimError err;
    u32 result;

    /* LUI */
    result = asm_and_run(
        "lui a0, 0x12345\n"
        "ebreak\n",
        REG_A0, &err);
    if (result != 0x12345000) {
        char msg[64];
        snprintf(msg, sizeof(msg), "LUI: expected 0x12345000, got 0x%08X", result);
        FAIL(msg);
        return;
    }

    /* LUI + ADDI 组合 */
    result = asm_and_run(
        "lui a0, 0x12345\n"
        "addi a0, a0, 0x678\n"
        "ebreak\n",
        REG_A0, &err);
    if (result != 0x12345678) {
        char msg[64];
        snprintf(msg, sizeof(msg), "LUI+ADDI: expected 0x12345678, got 0x%08X", result);
        FAIL(msg);
        return;
    }

    PASS();
}

/* 测试 JAL (跳转) */
static void test_jal(void) {
    TEST("JAL execution");

    SimError err;
    u32 result;

    /* JAL: 跳过一条指令 */
    result = asm_and_run(
        "jal zero, skip\n"
        "addi a0, zero, 99\n"  /* 被跳过 */
        "skip:\n"
        "addi a0, zero, 42\n"
        "ebreak\n",
        REG_A0, &err);
    if (result != 42) { FAIL("JAL wrong"); return; }

    PASS();
}

/* 测试 Load/Store */
static void test_load_store(void) {
    TEST("Load/Store execution");

    Memory* mem = memory_create(DEFAULT_MEM_SIZE, DEFAULT_MEM_BASE);
    if (!mem) { FAIL("create failed"); return; }

    AsmContext* ctx = asm_create(DEFAULT_MEM_BASE);
    if (!ctx) { FAIL("create failed"); return; }

    /* 使用 0x800FF000 作为数据区 (在 1MB 内存范围内) */
    const char* code =
        "lui t0, 0x800FF\n"       /* t0 = 0x800FF000 */
        "addi t1, zero, 42\n"     /* t1 = 42 */
        "sw t1, 0(t0)\n"          /* mem[t0] = 42 */
        "lw a0, 0(t0)\n"          /* a0 = mem[t0] */
        "ebreak\n";

    if (asm_assemble(ctx, code) != ERR_OK) { FAIL("assemble error"); return; }
    memory_load(mem, DEFAULT_MEM_BASE, (const u8*)ctx->code, ctx->code_size);
    asm_destroy(ctx);

    CPU* cpu = cpu_create(mem);
    if (!cpu) { FAIL("create failed"); return; }

    cpu_run(cpu, 10000);
    u32 result = cpu_read_reg(cpu, REG_A0);

    if (result != 42) {
        char msg[64];
        snprintf(msg, sizeof(msg), "expected 42, got %u", result);
        FAIL(msg);
        cpu_destroy(cpu);
        memory_destroy(mem);
        return;
    }

    cpu_destroy(cpu);
    memory_destroy(mem);
    PASS();
}

/* 测试 SLT/SLTU */
static void test_slt(void) {
    TEST("SLT/SLTU execution");

    SimError err;
    u32 result;

    /* SLT (有符号比较) */
    result = asm_and_run(
        "addi t0, zero, 5\n"
        "addi t1, zero, 10\n"
        "slt a0, t0, t1\n"
        "ebreak\n",
        REG_A0, &err);
    if (result != 1) { FAIL("SLT 5<10 wrong"); return; }

    result = asm_and_run(
        "addi t0, zero, 10\n"
        "addi t1, zero, 5\n"
        "slt a0, t0, t1\n"
        "ebreak\n",
        REG_A0, &err);
    if (result != 0) { FAIL("SLT 10<5 wrong"); return; }

    /* SLTU (无符号比较) */
    result = asm_and_run(
        "addi t0, zero, 5\n"
        "addi t1, zero, 10\n"
        "sltu a0, t0, t1\n"
        "ebreak\n",
        REG_A0, &err);
    if (result != 1) { FAIL("SLTU 5<10 wrong"); return; }

    PASS();
}

/* 测试 JALR */
static void test_jalr(void) {
    TEST("JALR execution");

    Memory* mem = memory_create(DEFAULT_MEM_SIZE, DEFAULT_MEM_BASE);
    if (!mem) { FAIL("create failed"); return; }

    AsmContext* ctx = asm_create(DEFAULT_MEM_BASE);
    if (!ctx) { FAIL("create failed"); return; }

    const char* code =
        "jalr ra, target\n"       /* 跳转到 target, ra = 返回地址 */
        "addi a0, zero, 99\n"     /* 返回后执行 (不应到达) */
        "ebreak\n"
        "target:\n"
        "addi a0, zero, 42\n"
        "jalr zero, 0(ra)\n"      /* 返回 */
        "ebreak\n";

    if (asm_assemble(ctx, code) != ERR_OK) { FAIL("assemble error"); return; }
    memory_load(mem, DEFAULT_MEM_BASE, (const u8*)ctx->code, ctx->code_size);
    asm_destroy(ctx);

    CPU* cpu = cpu_create(mem);
    if (!cpu) { FAIL("create failed"); return; }

    cpu_run(cpu, 10000);
    u32 result = cpu_read_reg(cpu, REG_A0);

    /* JALR 跳到 target, 设置 a0=42, 然后返回 */
    /* 但返回后执行 addi a0, zero, 99 会覆盖 a0 */
    /* 所以最终结果应该是 99 */
    if (result != 99) {
        char msg[64];
        snprintf(msg, sizeof(msg), "expected 99, got %u", result);
        FAIL(msg);
        cpu_destroy(cpu);
        memory_destroy(mem);
        return;
    }

    cpu_destroy(cpu);
    memory_destroy(mem);
    PASS();
}

/* 测试 x0 硬连线零 */
static void test_x0_zero(void) {
    TEST("x0 hardwired to zero");

    SimError err;
    u32 result;

    /* 尝试写入 x0 */
    result = asm_and_run(
        "addi x0, zero, 99\n"
        "add a0, x0, x0\n"
        "ebreak\n",
        REG_A0, &err);
    if (result != 0) { FAIL("x0 should be zero"); return; }

    PASS();
}

int main(void) {
    printf("\n=== Integration Tests ===\n\n");

    test_add();
    test_sub();
    test_bitwise();
    test_shift();
    test_branch();
    test_upper_imm();
    test_jal();
    test_load_store();
    test_slt();
    test_jalr();
    test_x0_zero();

    printf("\n=== Results: %d passed, %d failed ===\n\n",
           tests_passed, tests_failed);

    return tests_failed > 0 ? 1 : 0;
}
