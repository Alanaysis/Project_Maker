/**
 * 内存管理测试 (test_memory.c)
 * 功能: 测试内存管理模块
 */

#include "../include/types.h"
#include "../include/memory.h"
#include "../include/screen.h"

// 测试结果统计
static int tests_passed = 0;
static int tests_failed = 0;

// 测试宏
#define TEST(name, condition) do { \
    if (condition) { \
        screen_puts("  PASS: "); \
        screen_puts(name); \
        screen_puts("\n"); \
        tests_passed++; \
    } else { \
        screen_set_color(COLOR_LIGHT_RED, COLOR_BLACK); \
        screen_puts("  FAIL: "); \
        screen_puts(name); \
        screen_puts("\n"); \
        screen_set_color(COLOR_LIGHT_GREY, COLOR_BLACK); \
        tests_failed++; \
    } \
} while(0)

// 测试 memset
void test_memset() {
    screen_puts("[TEST] memset\n");

    // 测试 1: 基本功能
    uint8_t buffer[16];
    memset(buffer, 0xAA, 16);
    int pass = 1;
    for (int i = 0; i < 16; i++) {
        if (buffer[i] != 0xAA) {
            pass = 0;
            break;
        }
    }
    TEST("memset fills memory correctly", pass);

    // 测试 2: 零长度
    memset(buffer, 0xFF, 0);
    TEST("memset with zero length", buffer[0] == 0xAA);  // 应该不变
}

// 测试 memcpy
void test_memcpy() {
    screen_puts("[TEST] memcpy\n");

    // 测试 1: 基本功能
    uint8_t src[] = {1, 2, 3, 4, 5};
    uint8_t dest[5];
    memcpy(dest, src, 5);
    int pass = 1;
    for (int i = 0; i < 5; i++) {
        if (dest[i] != src[i]) {
            pass = 0;
            break;
        }
    }
    TEST("memcpy copies correctly", pass);

    // 测试 2: 零长度
    uint8_t buffer[5] = {0};
    memcpy(buffer, src, 0);
    TEST("memcpy with zero length", buffer[0] == 0);  // 应该不变
}

// 测试 memcmp
void test_memcmp() {
    screen_puts("[TEST] memcmp\n");

    // 测试 1: 相等
    uint8_t buf1[] = {1, 2, 3};
    uint8_t buf2[] = {1, 2, 3};
    TEST("memcmp equal buffers", memcmp(buf1, buf2, 3) == 0);

    // 测试 2: 不相等
    uint8_t buf3[] = {1, 2, 4};
    TEST("memcmp different buffers", memcmp(buf1, buf3, 3) != 0);

    // 测试 3: 第一个字节不同
    uint8_t buf4[] = {0, 2, 3};
    TEST("memcmp first byte different", memcmp(buf1, buf4, 3) > 0);
}

// 测试物理内存分配
void test_physical_allocation() {
    screen_puts("[TEST] Physical Memory Allocation\n");

    // 测试 1: 分配页面
    uint32_t page1 = mm_alloc_page();
    TEST("alloc_page returns valid address", page1 != 0);
    TEST("alloc_page is page aligned", (page1 & 0xFFF) == 0);

    // 测试 2: 分配多个页面
    uint32_t page2 = mm_alloc_page();
    TEST("alloc_page returns different addresses", page1 != page2);

    // 测试 3: 释放页面
    mm_free_page(page1);
    uint32_t page3 = mm_alloc_page();
    TEST("free_page allows reuse", page3 != 0);

    // 清理
    mm_free_page(page2);
    mm_free_page(page3);
}

// 测试堆分配
void test_heap_allocation() {
    screen_puts("[TEST] Heap Allocation\n");

    // 测试 1: 分配小内存
    void *ptr1 = kmalloc(16);
    TEST("kmalloc small allocation", ptr1 != NULL);

    // 测试 2: 分配大内存
    void *ptr2 = kmalloc(4096);
    TEST("kmalloc large allocation", ptr2 != NULL);

    // 测试 3: 写入和读取
    memset(ptr1, 0xAB, 16);
    uint8_t *byte_ptr = (uint8_t *)ptr1;
    TEST("kmalloc memory is writable", byte_ptr[0] == 0xAB);

    // 测试 4: 释放后重新分配
    kfree(ptr1);
    void *ptr3 = kmalloc(16);
    TEST("kfree allows reuse", ptr3 != NULL);

    // 测试 5: realloc
    void *ptr4 = kmalloc(32);
    memset(ptr4, 0xCD, 32);
    void *ptr5 = krealloc(ptr4, 64);
    uint8_t *byte_ptr2 = (uint8_t *)ptr5;
    TEST("krealloc preserves data", byte_ptr2[0] == 0xCD);

    // 清理
    kfree(ptr2);
    kfree(ptr3);
    kfree(ptr5);
}

// 运行所有内存测试
void run_memory_tests() {
    screen_set_color(COLOR_LIGHT_CYAN, COLOR_BLACK);
    screen_puts("\n========================================\n");
    screen_puts("       Memory Management Tests\n");
    screen_puts("========================================\n\n");
    screen_set_color(COLOR_LIGHT_GREY, COLOR_BLACK);

    tests_passed = 0;
    tests_failed = 0;

    // 运行测试
    test_memset();
    test_memcpy();
    test_memcmp();
    test_physical_allocation();
    test_heap_allocation();

    // 显示结果
    screen_puts("\n========================================\n");
    screen_puts("Test Results: ");
    screen_put_int(tests_passed);
    screen_puts(" passed, ");
    screen_put_int(tests_failed);
    screen_puts(" failed\n");
    screen_puts("========================================\n");

    if (tests_failed == 0) {
        screen_set_color(COLOR_LIGHT_GREEN, COLOR_BLACK);
        screen_puts("All tests PASSED!\n");
    } else {
        screen_set_color(COLOR_LIGHT_RED, COLOR_BLACK);
        screen_puts("Some tests FAILED!\n");
    }
    screen_set_color(COLOR_LIGHT_GREY, COLOR_BLACK);
}
