/**
 * Hello World 示例 (hello.c)
 * 功能: 最简单的内核程序，在屏幕上输出 Hello World
 */

#include "../include/types.h"
#include "../include/screen.h"
#include "../include/gdt.h"
#include "../include/idt.h"

// 简化的内核入口
void hello_kernel_main() {
    // 初始化屏幕
    screen_init();
    screen_clear();

    // 输出欢迎信息
    screen_set_color(COLOR_LIGHT_GREEN, COLOR_BLACK);
    screen_puts("===================================\n");
    screen_puts("       Hello, Simple OS!\n");
    screen_puts("===================================\n\n");

    screen_set_color(COLOR_LIGHT_GREY, COLOR_BLACK);
    screen_puts("This is a simple operating system kernel.\n");
    screen_puts("It demonstrates basic OS concepts:\n\n");

    screen_puts("  - Boot loading\n");
    screen_puts("  - Protected mode\n");
    screen_puts("  - Screen output\n");
    screen_puts("  - Basic kernel initialization\n\n");

    // 输出不同颜色的文字
    screen_puts("Color demonstration:\n");

    screen_set_color(COLOR_RED, COLOR_BLACK);
    screen_puts("  Red text\n");

    screen_set_color(COLOR_GREEN, COLOR_BLACK);
    screen_puts("  Green text\n");

    screen_set_color(COLOR_BLUE, COLOR_BLACK);
    screen_puts("  Blue text\n");

    screen_set_color(COLOR_YELLOW, COLOR_BLACK);
    screen_puts("  Yellow text\n");

    screen_set_color(COLOR_CYAN, COLOR_BLACK);
    screen_puts("  Cyan text\n");

    screen_set_color(COLOR_MAGENTA, COLOR_BLACK);
    screen_puts("  Magenta text\n");

    screen_set_color(COLOR_WHITE, COLOR_BLACK);
    screen_puts("  White text\n");

    screen_set_color(COLOR_LIGHT_GREY, COLOR_BLACK);
    screen_puts("\n");

    // 输出数字
    screen_puts("Number demonstration:\n");
    screen_puts("  Decimal: ");
    screen_put_int(12345);
    screen_puts("\n");

    screen_puts("  Hexadecimal: ");
    screen_put_hex(0xDEADBEEF);
    screen_puts("\n\n");

    // 完成信息
    screen_set_color(COLOR_LIGHT_CYAN, COLOR_BLACK);
    screen_puts("Kernel halted. Press Ctrl+A, then X to exit QEMU.\n");

    // 停机
    while (1) {
        asm volatile("hlt");
    }
}
