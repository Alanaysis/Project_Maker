/**
 * 测试运行器 (run_tests.c)
 * 功能: 运行所有单元测试
 */

#include "../include/types.h"
#include "../include/screen.h"

// 外部测试函数声明
extern void run_memory_tests();
extern void run_process_tests();
extern void run_fs_tests();

// 运行所有测试
void run_all_tests() {
    screen_set_color(COLOR_LIGHT_CYAN, COLOR_BLACK);
    screen_puts("\n");
    screen_puts("╔══════════════════════════════════════════╗\n");
    screen_puts("║         Simple OS Test Suite             ║\n");
    screen_puts("╚══════════════════════════════════════════╝\n");
    screen_set_color(COLOR_LIGHT_GREY, COLOR_BLACK);

    // 运行内存管理测试
    run_memory_tests();

    // 运行进程管理测试
    run_process_tests();

    // 运行文件系统测试
    run_fs_tests();

    // 显示总结
    screen_set_color(COLOR_LIGHT_CYAN, COLOR_BLACK);
    screen_puts("\n");
    screen_puts("╔══════════════════════════════════════════╗\n");
    screen_puts("║           Test Suite Complete            ║\n");
    screen_puts("╚══════════════════════════════════════════╝\n");
    screen_set_color(COLOR_LIGHT_GREY, COLOR_BLACK);
}
