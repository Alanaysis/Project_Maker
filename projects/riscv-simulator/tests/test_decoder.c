/* ============================================================
 * 指令解码器测试
 * ============================================================ */

#include "riscv.h"
#include "decoder.h"
#include <stdio.h>
#include <string.h>
#include <assert.h>

static int tests_passed = 0;
static int tests_failed = 0;

#define TEST(name) printf("  TEST: %-40s ", name)
#define PASS()     do { printf("[PASS]\n"); tests_passed++; } while(0)
#define FAIL(msg)  do { printf("[FAIL] %s\n", msg); tests_failed++; } while(0)

/* 测试 R-type 指令解码 (ADD x1, x2, x3) */
static void test_decode_r_type(void) {
    TEST("R-type decode (ADD x1, x2, x3)");

    /* ADD x1, x2, x3
     * funct7=0000000, rs2=00011, rs1=00010, funct3=000, rd=00001, opcode=0110011
     * 0000000 00011 00010 000 00001 0110011
     * = 0x003100B3
     */
    u32 raw = 0x003100B3;
    DecodedInsn insn;
    SimError err = decode_insn(raw, &insn);

    if (err != ERR_OK) { FAIL("decode error"); return; }
    if (insn.format != FMT_R) { FAIL("wrong format"); return; }
    if (insn.opcode != OP_OP) { FAIL("wrong opcode"); return; }
    if (insn.rd != 1) { FAIL("wrong rd"); return; }
    if (insn.rs1 != 2) { FAIL("wrong rs1"); return; }
    if (insn.rs2 != 3) { FAIL("wrong rs2"); return; }
    if (insn.funct3 != 0) { FAIL("wrong funct3"); return; }
    if (insn.funct7 != 0) { FAIL("wrong funct7"); return; }

    PASS();
}

/* 测试 I-type 指令解码 (ADDI x1, x2, 100) */
static void test_decode_i_type(void) {
    TEST("I-type decode (ADDI x1, x2, 100)");

    /* ADDI x1, x2, 100
     * imm[11:0]=000001100100, rs1=00010, funct3=000, rd=00001, opcode=0010011
     * = 0x06410093
     */
    u32 raw = 0x06410093;
    DecodedInsn insn;
    SimError err = decode_insn(raw, &insn);

    if (err != ERR_OK) { FAIL("decode error"); return; }
    if (insn.format != FMT_I) { FAIL("wrong format"); return; }
    if (insn.rd != 1) { FAIL("wrong rd"); return; }
    if (insn.rs1 != 2) { FAIL("wrong rs1"); return; }
    if (insn.imm != 100) { FAIL("wrong imm"); return; }

    PASS();
}

/* 测试 I-type 负立即数 (ADDI x1, x2, -1) */
static void test_decode_i_type_negative(void) {
    TEST("I-type decode negative imm (ADDI x1, x2, -1)");

    /* ADDI x1, x2, -1
     * imm[11:0]=111111111111, rs1=00010, funct3=000, rd=00001, opcode=0010011
     * = 0xFFF10093
     */
    u32 raw = 0xFFF10093;
    DecodedInsn insn;
    SimError err = decode_insn(raw, &insn);

    if (err != ERR_OK) { FAIL("decode error"); return; }
    if (insn.imm != -1) { FAIL("wrong imm"); return; }

    PASS();
}

/* 测试 S-type 指令解码 (SW x3, 8(x2)) */
static void test_decode_s_type(void) {
    TEST("S-type decode (SW x3, 8(x2))");

    /* SW x3, 8(x2)
     * imm[11:5]=0000000, rs2=00011, rs1=00010, funct3=010, imm[4:0]=01000, opcode=0100011
     * = 0x00312423
     */
    u32 raw = 0x00312423;
    DecodedInsn insn;
    SimError err = decode_insn(raw, &insn);

    if (err != ERR_OK) { FAIL("decode error"); return; }
    if (insn.format != FMT_S) { FAIL("wrong format"); return; }
    if (insn.rs1 != 2) { FAIL("wrong rs1"); return; }
    if (insn.rs2 != 3) { FAIL("wrong rs2"); return; }
    if (insn.imm != 8) { FAIL("wrong imm"); return; }
    if (insn.funct3 != MEM_WORD) { FAIL("wrong funct3"); return; }

    PASS();
}

/* 测试 B-type 指令解码 (BEQ x1, x2, 16) */
static void test_decode_b_type(void) {
    TEST("B-type decode (BEQ x1, x2, 16)");

    /* BEQ x1, x2, 16
     * imm[12|10:5]=0000000, rs2=00010, rs1=00001, funct3=000,
     * imm[4:1|11]=10000, opcode=1100011
     * imm = 16 = 0b000000010000
     */
    u32 raw = 0x00208863;
    DecodedInsn insn;
    SimError err = decode_insn(raw, &insn);

    if (err != ERR_OK) { FAIL("decode error"); return; }
    if (insn.format != FMT_B) { FAIL("wrong format"); return; }
    if (insn.rs1 != 1) { FAIL("wrong rs1"); return; }
    if (insn.rs2 != 2) { FAIL("wrong rs2"); return; }
    if (insn.imm != 16) { FAIL("wrong imm"); return; }

    PASS();
}

/* 测试 U-type 指令解码 (LUI x1, 0x12345) */
static void test_decode_u_type(void) {
    TEST("U-type decode (LUI x1, 0x12345)");

    /* LUI x1, 0x12345
     * imm[31:12]=00010010001101000101, rd=00001, opcode=0110111
     * = 0x123450B7
     */
    u32 raw = 0x123450B7;
    DecodedInsn insn;
    SimError err = decode_insn(raw, &insn);

    if (err != ERR_OK) { FAIL("decode error"); return; }
    if (insn.format != FMT_U) { FAIL("wrong format"); return; }
    if (insn.rd != 1) { FAIL("wrong rd"); return; }
    if (insn.imm != (i32)0x12345000) { FAIL("wrong imm"); return; }

    PASS();
}

/* 测试 J-type 指令解码 (JAL x1, 256) */
static void test_decode_j_type(void) {
    TEST("J-type decode (JAL x1, 256)");

    /* JAL x1, 256
     * imm = 256 = 0x100
     * imm[20]=0, imm[10:1]=1000000000, imm[11]=0, imm[19:12]=00000000
     */
    u32 raw = 0x100000EF;
    DecodedInsn insn;
    SimError err = decode_insn(raw, &insn);

    if (err != ERR_OK) { FAIL("decode error"); return; }
    if (insn.format != FMT_J) { FAIL("wrong format"); return; }
    if (insn.rd != 1) { FAIL("wrong rd"); return; }
    if (insn.imm != 256) { FAIL("wrong imm"); return; }

    PASS();
}

/* 测试 Load 指令解码 (LW x5, 0(x10)) */
static void test_decode_load(void) {
    TEST("Load decode (LW x5, 0(x10))");

    /* LW x5, 0(x10)
     * imm[11:0]=000000000000, rs1=01010, funct3=010, rd=00101, opcode=0000011
     * = 0x00052283
     */
    u32 raw = 0x00052283;
    DecodedInsn insn;
    SimError err = decode_insn(raw, &insn);

    if (err != ERR_OK) { FAIL("decode error"); return; }
    if (insn.format != FMT_I) { FAIL("wrong format"); return; }
    if (insn.opcode != OP_LOAD) { FAIL("wrong opcode"); return; }
    if (insn.rd != 5) { FAIL("wrong rd"); return; }
    if (insn.rs1 != 10) { FAIL("wrong rs1"); return; }
    if (insn.imm != 0) { FAIL("wrong imm"); return; }

    PASS();
}

/* 测试 ECALL 指令 */
static void test_decode_ecall(void) {
    TEST("System decode (ECALL)");

    /* ECALL = 0x00000073 */
    u32 raw = 0x00000073;
    DecodedInsn insn;
    SimError err = decode_insn(raw, &insn);

    if (err != ERR_OK) { FAIL("decode error"); return; }
    if (insn.opcode != OP_SYSTEM) { FAIL("wrong opcode"); return; }
    if (insn.imm != 0) { FAIL("wrong imm"); return; }

    PASS();
}

/* 测试 EBREAK 指令 */
static void test_decode_ebreak(void) {
    TEST("System decode (EBREAK)");

    /* EBREAK = 0x00100073 */
    u32 raw = 0x00100073;
    DecodedInsn insn;
    SimError err = decode_insn(raw, &insn);

    if (err != ERR_OK) { FAIL("decode error"); return; }
    if (insn.opcode != OP_SYSTEM) { FAIL("wrong opcode"); return; }
    if (insn.imm != 1) { FAIL("wrong imm"); return; }

    PASS();
}

/* 测试指令名称 */
static void test_insn_names(void) {
    TEST("instruction names");

    struct { u32 raw; const char* name; } tests[] = {
        {0x003100B3, "ADD"},
        {0x403100B3, "SUB"},
        {0x06410093, "ADDI"},
        {0x00312423, "SW"},
        {0x00052283, "LW"},
        {0x00208863, "BEQ"},
        {0x123450B7, "LUI"},
        {0x00000073, "ECALL"},
        {0x00100073, "EBREAK"},
    };

    int n = sizeof(tests) / sizeof(tests[0]);
    for (int i = 0; i < n; i++) {
        DecodedInsn insn;
        if (decode_insn(tests[i].raw, &insn) != ERR_OK) {
            FAIL("decode error");
            return;
        }
        if (strcmp(insn.name, tests[i].name) != 0) {
            char msg[64];
            snprintf(msg, sizeof(msg), "expected '%s', got '%s'",
                     tests[i].name, insn.name);
            FAIL(msg);
            return;
        }
    }

    PASS();
}

int main(void) {
    printf("\n=== Decoder Module Tests ===\n\n");

    test_decode_r_type();
    test_decode_i_type();
    test_decode_i_type_negative();
    test_decode_s_type();
    test_decode_b_type();
    test_decode_u_type();
    test_decode_j_type();
    test_decode_load();
    test_decode_ecall();
    test_decode_ebreak();
    test_insn_names();

    printf("\n=== Results: %d passed, %d failed ===\n\n",
           tests_passed, tests_failed);

    return tests_failed > 0 ? 1 : 0;
}
