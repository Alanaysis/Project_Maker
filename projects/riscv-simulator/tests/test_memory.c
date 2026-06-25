/* ============================================================
 * 内存模块测试
 * ============================================================ */

#include "riscv.h"
#include "memory.h"
#include <stdio.h>
#include <string.h>
#include <assert.h>

/* 测试计数 */
static int tests_passed = 0;
static int tests_failed = 0;

#define TEST(name) printf("  TEST: %-40s ", name)
#define PASS()     do { printf("[PASS]\n"); tests_passed++; } while(0)
#define FAIL(msg)  do { printf("[FAIL] %s\n", msg); tests_failed++; } while(0)

/* 测试内存创建和销毁 */
static void test_memory_create(void) {
    TEST("memory_create/destroy");

    Memory* mem = memory_create(1024, 0x80000000);
    if (!mem) { FAIL("create returned NULL"); return; }

    if (mem->size != 1024) { FAIL("wrong size"); return; }
    if (mem->base_addr != 0x80000000) { FAIL("wrong base"); return; }
    if (!mem->data) { FAIL("data is NULL"); return; }

    memory_destroy(mem);
    PASS();
}

/* 测试字节读写 */
static void test_memory_byte(void) {
    TEST("memory byte read/write");

    Memory* mem = memory_create(1024, 0x0);
    if (!mem) { FAIL("create failed"); return; }

    SimError err;
    u8 val;

    /* 写入 */
    err = memory_write_byte(mem, 0x100, 0xAB);
    if (err != ERR_OK) { FAIL("write failed"); return; }

    /* 读取 */
    err = memory_read_byte(mem, 0x100, &val);
    if (err != ERR_OK) { FAIL("read failed"); return; }
    if (val != 0xAB) { FAIL("wrong value"); return; }

    memory_destroy(mem);
    PASS();
}

/* 测试半字读写 (小端序) */
static void test_memory_half(void) {
    TEST("memory half read/write (little-endian)");

    Memory* mem = memory_create(1024, 0x0);
    if (!mem) { FAIL("create failed"); return; }

    SimError err;
    u16 val;

    /* 写入 0x1234 */
    err = memory_write_half(mem, 0x100, 0x1234);
    if (err != ERR_OK) { FAIL("write failed"); return; }

    /* 读取半字 */
    err = memory_read_half(mem, 0x100, &val);
    if (err != ERR_OK) { FAIL("read failed"); return; }
    if (val != 0x1234) { FAIL("wrong value"); return; }

    /* 验证小端序: 低字节 0x34, 高字节 0x12 */
    u8 b0, b1;
    memory_read_byte(mem, 0x100, &b0);
    memory_read_byte(mem, 0x101, &b1);
    if (b0 != 0x34 || b1 != 0x12) {
        FAIL("little-endian order wrong");
        return;
    }

    memory_destroy(mem);
    PASS();
}

/* 测试字读写 (小端序) */
static void test_memory_word(void) {
    TEST("memory word read/write (little-endian)");

    Memory* mem = memory_create(1024, 0x0);
    if (!mem) { FAIL("create failed"); return; }

    SimError err;
    u32 val;

    /* 写入 0xDEADBEEF */
    err = memory_write_word(mem, 0x100, 0xDEADBEEF);
    if (err != ERR_OK) { FAIL("write failed"); return; }

    /* 读取 */
    err = memory_read_word(mem, 0x100, &val);
    if (err != ERR_OK) { FAIL("read failed"); return; }
    if (val != 0xDEADBEEF) { FAIL("wrong value"); return; }

    /* 验证小端序 */
    u8 b0, b1, b2, b3;
    memory_read_byte(mem, 0x100, &b0);
    memory_read_byte(mem, 0x101, &b1);
    memory_read_byte(mem, 0x102, &b2);
    memory_read_byte(mem, 0x103, &b3);
    if (b0 != 0xEF || b1 != 0xBE || b2 != 0xAD || b3 != 0xDE) {
        FAIL("little-endian order wrong");
        return;
    }

    memory_destroy(mem);
    PASS();
}

/* 测试未对齐访问 */
static void test_memory_alignment(void) {
    TEST("memory alignment check");

    Memory* mem = memory_create(1024, 0x0);
    if (!mem) { FAIL("create failed"); return; }

    u32 val;
    SimError err;

    /* 半字必须 2 字节对齐 */
    err = memory_read_half(mem, 0x101, (u16*)&val);
    if (err != ERR_UNALIGNED_ACCESS) { FAIL("should reject unaligned half"); return; }

    /* 字必须 4 字节对齐 */
    err = memory_read_word(mem, 0x102, &val);
    if (err != ERR_UNALIGNED_ACCESS) { FAIL("should reject unaligned word"); return; }

    memory_destroy(mem);
    PASS();
}

/* 测试越界访问 */
static void test_memory_bounds(void) {
    TEST("memory bounds check");

    Memory* mem = memory_create(256, 0x0);
    if (!mem) { FAIL("create failed"); return; }

    u8 val;
    SimError err;

    /* 范围内 */
    err = memory_read_byte(mem, 0xFF, &val);
    if (err != ERR_OK) { FAIL("should accept 0xFF"); return; }

    /* 越界 */
    err = memory_read_byte(mem, 0x100, &val);
    if (err != ERR_MEMORY_FAULT) { FAIL("should reject 0x100"); return; }

    memory_destroy(mem);
    PASS();
}

/* 测试批量加载 */
static void test_memory_load(void) {
    TEST("memory_load batch");

    Memory* mem = memory_create(1024, 0x0);
    if (!mem) { FAIL("create failed"); return; }

    u8 data[] = {0x12, 0x34, 0x56, 0x78};
    SimError err = memory_load(mem, 0x100, data, 4);
    if (err != ERR_OK) { FAIL("load failed"); return; }

    u32 val;
    err = memory_read_word(mem, 0x100, &val);
    if (err != ERR_OK) { FAIL("read failed"); return; }
    /* 小端序: 0x78563412 */
    if (val != 0x78563412) { FAIL("wrong value"); return; }

    memory_destroy(mem);
    PASS();
}

int main(void) {
    printf("\n=== Memory Module Tests ===\n\n");

    test_memory_create();
    test_memory_byte();
    test_memory_half();
    test_memory_word();
    test_memory_alignment();
    test_memory_bounds();
    test_memory_load();

    printf("\n=== Results: %d passed, %d failed ===\n\n",
           tests_passed, tests_failed);

    return tests_failed > 0 ? 1 : 0;
}
