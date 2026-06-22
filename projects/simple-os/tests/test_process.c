/**
 * 进程管理测试 (test_process.c)
 * 功能: 测试进程管理模块
 */

#include "../include/types.h"
#include "../include/process.h"
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

// 测试进程
static int test_process_1_ran = 0;
static int test_process_2_ran = 0;

// 测试进程函数
void test_process_func_1() {
    test_process_1_ran = 1;
    process_exit(0);
}

void test_process_func_2() {
    test_process_2_ran = 1;
    process_exit(0);
}

// 测试进程创建
void test_process_creation() {
    screen_puts("[TEST] Process Creation\n");

    // 重置测试标志
    test_process_1_ran = 0;
    test_process_2_ran = 0;

    // 测试 1: 创建进程
    process_t *proc1 = process_create(test_process_func_1);
    TEST("process_create returns valid pointer", proc1 != NULL);

    // 测试 2: PID 分配
    TEST("process has valid PID", proc1->pid > 0);

    // 测试 3: 进程状态
    TEST("process is in READY state", proc1->state == PROCESS_READY);

    // 测试 4: 进程名称
    TEST("process has default name", proc1->name[0] != '\0');

    // 让进程运行
    yield();
    yield();

    // 测试 5: 进程执行
    TEST("process function executed", test_process_1_ran == 1);

    // 清理
    process_destroy(proc1);
}

// 测试进程调度
void test_process_scheduling() {
    screen_puts("[TEST] Process Scheduling\n");

    // 重置测试标志
    test_process_1_ran = 0;
    test_process_2_ran = 0;

    // 创建多个进程
    process_t *proc1 = process_create(test_process_func_1);
    process_t *proc2 = process_create(test_process_func_2);

    TEST("multiple processes created", proc1 != NULL && proc2 != NULL);
    TEST("processes have different PIDs", proc1->pid != proc2->pid);

    // 让进程运行
    yield();
    yield();
    yield();

    // 测试进程是否都被调度
    TEST("process 1 was scheduled", test_process_1_ran == 1);
    TEST("process 2 was scheduled", test_process_2_ran == 1);

    // 清理
    process_destroy(proc1);
    process_destroy(proc2);
}

// 测试进程退出
void test_process_exit() {
    screen_puts("[TEST] Process Exit\n");

    // 创建进程
    process_t *proc = process_create(test_process_func_1);
    TEST("process created for exit test", proc != NULL);

    // 让进程运行并退出
    yield();

    // 检查进程状态
    TEST("process is in ZOMBIE state after exit", proc->state == PROCESS_ZOMBIE);
    TEST("process exit status is 0", proc->exit_status == 0);

    // 清理
    process_destroy(proc);
}

// 测试进程查找
void test_process_lookup() {
    screen_puts("[TEST] Process Lookup\n");

    // 创建进程
    process_t *proc = process_create(test_process_func_1);
    TEST("process created for lookup test", proc != NULL);

    // 通过 PID 查找
    process_t *found = process_get_by_pid(proc->pid);
    TEST("process found by PID", found == proc);

    // 查找不存在的 PID
    process_t *not_found = process_get_by_pid(9999);
    TEST("non-existent PID returns NULL", not_found == NULL);

    // 清理
    process_destroy(proc);
}

// 运行所有进程测试
void run_process_tests() {
    screen_set_color(COLOR_LIGHT_CYAN, COLOR_BLACK);
    screen_puts("\n========================================\n");
    screen_puts("       Process Management Tests\n");
    screen_puts("========================================\n\n");
    screen_set_color(COLOR_LIGHT_GREY, COLOR_BLACK);

    tests_passed = 0;
    tests_failed = 0;

    // 运行测试
    test_process_creation();
    test_process_scheduling();
    test_process_exit();
    test_process_lookup();

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
