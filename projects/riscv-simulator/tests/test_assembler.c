/* ============================================================
 * 汇编器测试
 * ============================================================ */

#include "riscv.h"
#include "assembler.h"
#include "decoder.h"
#include <stdio.h>
#include <string.h>

static int tests_passed = 0;
static int tests_failed = 0;

#define TEST(name) printf("  TEST: %-40s ", name)
#define PASS()     do { printf("[PASS]\n"); tests_passed++; } while(0)
#define FAIL(msg)  do { printf("[FAIL] %s\n", msg); tests_failed++; } while(0)

/* 测试寄存器解析 */
static void test_parse_register(void) {
    TEST("register name parsing");

    /* 数字格式 */
    if (asm_parse_register("x0") != 0) { FAIL("x0"); return; }
    if (asm_parse_register("x31") != 31) { FAIL("x31"); return; }
    if (asm_parse_register("x15") != 15) { FAIL("x15"); return; }

    /* ABI 名称 */
    if (asm_parse_register("zero") != 0) { FAIL("zero"); return; }
    if (asm_parse_register("ra") != 1) { FAIL("ra"); return; }
    if (asm_parse_register("sp") != 2) { FAIL("sp"); return; }
    if (asm_parse_register("a0") != 10) { FAIL("a0"); return; }
    if (asm_parse_register("a7") != 17) { FAIL("a7"); return; }
    if (asm_parse_register("t0") != 5) { FAIL("t0"); return; }
    if (asm_parse_register("s0") != 8) { FAIL("s0"); return; }
    if (asm_parse_register("t6") != 31) { FAIL("t6"); return; }

    /* 无效寄存器 */
    if (asm_parse_register("x32") != -1) { FAIL("x32 should be invalid"); return; }
    if (asm_parse_register("foo") != -1) { FAIL("foo should be invalid"); return; }

    PASS();
}

/* 测试立即数解析 */
static void test_parse_imm(void) {
    TEST("immediate parsing");

    i32 val;

    /* 十进制 */
    if (asm_parse_imm("0", &val) != ERR_OK || val != 0) { FAIL("0"); return; }
    if (asm_parse_imm("42", &val) != ERR_OK || val != 42) { FAIL("42"); return; }
    if (asm_parse_imm("-1", &val) != ERR_OK || val != -1) { FAIL("-1"); return; }

    /* 十六进制 */
    if (asm_parse_imm("0xFF", &val) != ERR_OK || val != 255) { FAIL("0xFF"); return; }
    if (asm_parse_imm("0x1000", &val) != ERR_OK || val != 4096) { FAIL("0x1000"); return; }

    PASS();
}

/* 测试 R-type 汇编 */
static void test_asm_r_type(void) {
    TEST("R-type assembly");

    u32 code;

    /* ADD x1, x2, x3 */
    if (asm_assemble_one_wrapper("add x1, x2, x3", 0, &code) != ERR_OK) {
        FAIL("ADD parse error");
        return;
    }
    /* 验证: 0x003100B3 */
    if (code != 0x003100B3) {
        char msg[64];
        snprintf(msg, sizeof(msg), "ADD: expected 0x003100B3, got 0x%08X", code);
        FAIL(msg);
        return;
    }

    /* SUB x5, x6, x7 */
    if (asm_assemble_one_wrapper("sub x5, x6, x7", 0, &code) != ERR_OK) {
        FAIL("SUB parse error");
        return;
    }
    if (code != 0x407302B3) {
        char msg[64];
        snprintf(msg, sizeof(msg), "SUB: expected 0x407302B3, got 0x%08X", code);
        FAIL(msg);
        return;
    }

    PASS();
}

/* 测试 I-type 汇编 */
static void test_asm_i_type(void) {
    TEST("I-type assembly");

    u32 code;

    /* ADDI x1, x2, 100 */
    if (asm_assemble_one_wrapper("addi x1, x2, 100", 0, &code) != ERR_OK) {
        FAIL("ADDI parse error");
        return;
    }
    if (code != 0x06410093) {
        char msg[64];
        snprintf(msg, sizeof(msg), "ADDI: expected 0x06410093, got 0x%08X", code);
        FAIL(msg);
        return;
    }

    /* ADDI with ABI names */
    if (asm_assemble_one_wrapper("addi a0, zero, 0", 0, &code) != ERR_OK) {
        FAIL("ADDI ABI parse error");
        return;
    }
    if (code != 0x00000513) {
        char msg[64];
        snprintf(msg, sizeof(msg), "ADDI ABI: expected 0x00000513, got 0x%08X", code);
        FAIL(msg);
        return;
    }

    PASS();
}

/* 测试 Load 汇编 */
static void test_asm_load(void) {
    TEST("Load assembly");

    u32 code;

    /* LW x5, 0(x10) */
    if (asm_assemble_one_wrapper("lw x5, 0(x10)", 0, &code) != ERR_OK) {
        FAIL("LW parse error");
        return;
    }
    if (code != 0x00052283) {
        char msg[64];
        snprintf(msg, sizeof(msg), "LW: expected 0x00052283, got 0x%08X", code);
        FAIL(msg);
        return;
    }

    /* LW a0, 4(sp) */
    if (asm_assemble_one_wrapper("lw a0, 4(sp)", 0, &code) != ERR_OK) {
        FAIL("LW sp parse error");
        return;
    }
    if (code != 0x00412503) {
        char msg[64];
        snprintf(msg, sizeof(msg), "LW sp: expected 0x00412503, got 0x%08X", code);
        FAIL(msg);
        return;
    }

    PASS();
}

/* 测试 Store 汇编 */
static void test_asm_store(void) {
    TEST("Store assembly");

    u32 code;

    /* SW x3, 8(x2) */
    if (asm_assemble_one_wrapper("sw x3, 8(x2)", 0, &code) != ERR_OK) {
        FAIL("SW parse error");
        return;
    }
    if (code != 0x00312423) {
        char msg[64];
        snprintf(msg, sizeof(msg), "SW: expected 0x00312423, got 0x%08X", code);
        FAIL(msg);
        return;
    }

    PASS();
}

/* 测试 Branch 汇编 */
static void test_asm_branch(void) {
    TEST("Branch assembly");

    u32 code;

    /* BEQ x1, x2, 16 */
    if (asm_assemble_one_wrapper("beq x1, x2, 16", 0, &code) != ERR_OK) {
        FAIL("BEQ parse error");
        return;
    }
    if (code != 0x00208863) {
        char msg[64];
        snprintf(msg, sizeof(msg), "BEQ: expected 0x00208863, got 0x%08X", code);
        FAIL(msg);
        return;
    }

    /* BNE */
    if (asm_assemble_one_wrapper("bne x1, x2, 8", 0, &code) != ERR_OK) {
        FAIL("BNE parse error");
        return;
    }

    PASS();
}

/* 测试 U-type 汇编 */
static void test_asm_u_type(void) {
    TEST("U-type assembly");

    u32 code;

    /* LUI x1, 0x12345 */
    if (asm_assemble_one_wrapper("lui x1, 0x12345", 0, &code) != ERR_OK) {
        FAIL("LUI parse error");
        return;
    }
    if (code != 0x123450B7) {
        char msg[64];
        snprintf(msg, sizeof(msg), "LUI: expected 0x123450B7, got 0x%08X", code);
        FAIL(msg);
        return;
    }

    PASS();
}

/* 测试 System 指令 */
static void test_asm_system(void) {
    TEST("System assembly");

    u32 code;

    /* ECALL */
    if (asm_assemble_one_wrapper("ecall", 0, &code) != ERR_OK) {
        FAIL("ECALL parse error");
        return;
    }
    if (code != 0x00000073) {
        FAIL("ECALL wrong code");
        return;
    }

    /* EBREAK */
    if (asm_assemble_one_wrapper("ebreak", 0, &code) != ERR_OK) {
        FAIL("EBREAK parse error");
        return;
    }
    if (code != 0x00100073) {
        FAIL("EBREAK wrong code");
        return;
    }

    PASS();
}

/* 测试多行汇编 */
static void test_asm_multi_line(void) {
    TEST("multi-line assembly");

    AsmContext* ctx = asm_create(0x80000000);
    if (!ctx) { FAIL("create failed"); return; }

    const char* code =
        "addi a0, zero, 0\n"
        "addi t0, zero, 10\n"
        "add a0, a0, t0\n"
        "ebreak\n";

    SimError err = asm_assemble(ctx, code);
    if (err != ERR_OK) { FAIL("assemble error"); return; }

    /* 应该生成 4 条指令 = 16 字节 */
    if (ctx->code_size != 16) {
        char msg[64];
        snprintf(msg, sizeof(msg), "expected 16 bytes, got %u", ctx->code_size);
        FAIL(msg);
        return;
    }

    /* 验证第一条: ADDI a0, zero, 0 = 0x00000513 */
    if (ctx->code[0] != 0x00000513) {
        FAIL("first insn wrong");
        return;
    }

    /* 验证最后一条: EBREAK = 0x00100073 */
    if (ctx->code[3] != 0x00100073) {
        FAIL("last insn wrong");
        return;
    }

    asm_destroy(ctx);
    PASS();
}

int main(void) {
    printf("\n=== Assembler Module Tests ===\n\n");

    test_parse_register();
    test_parse_imm();
    test_asm_r_type();
    test_asm_i_type();
    test_asm_load();
    test_asm_store();
    test_asm_branch();
    test_asm_u_type();
    test_asm_system();
    test_asm_multi_line();

    printf("\n=== Results: %d passed, %d failed ===\n\n",
           tests_passed, tests_failed);

    return tests_failed > 0 ? 1 : 0;
}
