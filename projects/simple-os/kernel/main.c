/**
 * 内核主文件 (main.c)
 * 功能: 内核入口点，初始化各子系统
 */

#include "../include/types.h"
#include "../include/screen.h"
#include "../include/gdt.h"
#include "../include/idt.h"
#include "../include/memory.h"
#include "../include/process.h"
#include "../include/keyboard.h"
#include "../include/fs.h"

// 外部函数声明
extern void kernel_main();

// 内核主函数
void kernel_main() {
    // 初始化屏幕
    screen_init();
    screen_clear();
    screen_set_color(COLOR_LIGHT_GREEN, COLOR_BLACK);

    screen_puts("===================================\n");
    screen_puts("       Simple OS Kernel v0.1\n");
    screen_puts("===================================\n\n");

    // 初始化 GDT
    screen_puts("[INIT] Initializing GDT...\n");
    gdt_init();
    screen_puts("[INIT] GDT initialized.\n");

    // 初始化 IDT
    screen_puts("[INIT] Initializing IDT...\n");
    idt_init();
    screen_puts("[INIT] IDT initialized.\n");

    // 初始化内存管理
    screen_puts("[INIT] Initializing Memory Management...\n");
    mm_init(32 * 1024 * 1024);  // 假设 32MB 内存
    screen_puts("[INIT] Memory management initialized.\n");

    // 初始化进程管理
    screen_puts("[INIT] Initializing Process Management...\n");
    process_init();
    screen_puts("[INIT] Process management initialized.\n");

    // 初始化键盘驱动
    screen_puts("[INIT] Initializing Keyboard...\n");
    keyboard_init();
    screen_puts("[INIT] Keyboard initialized.\n");

    // 初始化文件系统
    screen_puts("[INIT] Initializing File System...\n");
    fs_init();
    screen_puts("[INIT] File system initialized.\n");

    screen_puts("\n[INIT] All systems initialized.\n");
    screen_puts("[INIT] Starting init process...\n\n");

    // 创建初始化进程
    process_create(init_process);

    // 启动调度器 (不应该返回)
    scheduler_start();

    // 如果到达这里，说明出错了
    screen_set_color(COLOR_LIGHT_RED, COLOR_BLACK);
    screen_puts("\n[ERROR] Scheduler returned unexpectedly!\n");
    while (1) {
        asm volatile("hlt");
    }
}

// 初始化进程
void init_process() {
    screen_set_color(COLOR_LIGHT_CYAN, COLOR_BLACK);
    screen_puts("[INIT] Init process started.\n");

    // 创建用户进程
    process_create(user_process_1);
    process_create(user_process_2);

    // 主循环
    while (1) {
        // 可以在这里处理僵尸进程
        yield();
    }
}

// 用户进程 1
void user_process_1() {
    screen_set_color(COLOR_YELLOW, COLOR_BLACK);
    screen_puts("[PROC1] User process 1 started.\n");

    int count = 0;
    while (1) {
        // 模拟工作
        for (volatile int i = 0; i < 1000000; i++) {
            asm volatile("nop");
        }

        count++;
        screen_set_color(COLOR_YELLOW, COLOR_BLACK);
        screen_puts("[PROC1] Working... (");
        screen_put_int(count);
        screen_puts(")\n");

        // 让出 CPU
        yield();
    }
}

// 用户进程 2
void user_process_2() {
    screen_set_color(COLOR_LIGHT_MAGENTA, COLOR_BLACK);
    screen_puts("[PROC2] User process 2 started.\n");

    int count = 0;
    while (1) {
        // 模拟工作
        for (volatile int i = 0; i < 1500000; i++) {
            asm volatile("nop");
        }

        count++;
        screen_set_color(COLOR_LIGHT_MAGENTA, COLOR_BLACK);
        screen_puts("[PROC2] Working... (");
        screen_put_int(count);
        screen_puts(")\n");

        // 让出 CPU
        yield();
    }
}
