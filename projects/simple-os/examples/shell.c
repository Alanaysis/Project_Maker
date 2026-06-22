/**
 * 简单 Shell 示例 (shell.c)
 * 功能: 实现一个简单的命令行 Shell
 */

#include "../include/types.h"
#include "../include/screen.h"
#include "../include/keyboard.h"
#include "../include/fs.h"

// 命令缓冲区
#define CMD_BUFFER_SIZE 256
static char cmd_buffer[CMD_BUFFER_SIZE];
static int cmd_pos = 0;

// 辅助函数: 字符串比较
static int strcmp(const char *s1, const char *s2) {
    while (*s1 && *s2) {
        if (*s1 != *s2) return *s1 - *s2;
        s1++;
        s2++;
    }
    return *s1 - *s2;
}

// 辅助函数: 字符串长度
static int strlen(const char *s) {
    int len = 0;
    while (*s++) len++;
    return len;
}

// 辅助函数: 复制字符串
static void strcpy(char *dest, const char *src) {
    while (*src) {
        *dest++ = *src++;
    }
    *dest = '\0';
}

// 显示提示符
void shell_prompt() {
    screen_set_color(COLOR_LIGHT_GREEN, COLOR_BLACK);
    screen_puts("simple-os> ");
    screen_set_color(COLOR_LIGHT_GREY, COLOR_BLACK);
}

// 清除命令缓冲区
void shell_clear_buffer() {
    memset(cmd_buffer, 0, CMD_BUFFER_SIZE);
    cmd_pos = 0;
}

// 帮助命令
void cmd_help() {
    screen_puts("Available commands:\n");
    screen_puts("  help     - Show this help\n");
    screen_puts("  clear    - Clear screen\n");
    screen_puts("  echo     - Echo text\n");
    screen_puts("  ls       - List files\n");
    screen_puts("  cat      - Show file contents\n");
    screen_puts("  create   - Create a file\n");
    screen_puts("  delete   - Delete a file\n");
    screen_puts("  about    - About Simple OS\n");
    screen_puts("  reboot   - Reboot system\n");
}

// 清屏命令
void cmd_clear() {
    screen_clear();
}

// echo 命令
void cmd_echo(const char *args) {
    if (args && strlen(args) > 0) {
        screen_puts(args);
        screen_puts("\n");
    }
}

// ls 命令
void cmd_ls() {
    screen_puts("Files in root directory:\n");

    // 简化实现: 显示一些示例文件
    screen_puts("  hello.txt\n");
    screen_puts("  readme.txt\n");
}

// cat 命令
void cmd_cat(const char *filename) {
    if (!filename || strlen(filename) == 0) {
        screen_puts("Usage: cat <filename>\n");
        return;
    }

    // 简化实现: 只能读取已知文件
    if (strcmp(filename, "hello.txt") == 0) {
        screen_puts("Hello, Simple OS!\n");
    } else if (strcmp(filename, "readme.txt") == 0) {
        screen_puts("This is a simple file system.\n");
    } else {
        screen_puts("File not found: ");
        screen_puts(filename);
        screen_puts("\n");
    }
}

// create 命令
void cmd_create(const char *filename) {
    if (!filename || strlen(filename) == 0) {
        screen_puts("Usage: create <filename>\n");
        return;
    }

    int ret = fs_create(filename, 0644);
    if (ret == SUCCESS) {
        screen_puts("File created: ");
        screen_puts(filename);
        screen_puts("\n");
    } else {
        screen_puts("Failed to create file: ");
        screen_puts(filename);
        screen_puts("\n");
    }
}

// delete 命令
void cmd_delete(const char *filename) {
    if (!filename || strlen(filename) == 0) {
        screen_puts("Usage: delete <filename>\n");
        return;
    }

    int ret = fs_delete(filename);
    if (ret == SUCCESS) {
        screen_puts("File deleted: ");
        screen_puts(filename);
        screen_puts("\n");
    } else {
        screen_puts("Failed to delete file: ");
        screen_puts(filename);
        screen_puts("\n");
    }
}

// about 命令
void cmd_about() {
    screen_set_color(COLOR_LIGHT_CYAN, COLOR_BLACK);
    screen_puts("Simple OS v0.1\n");
    screen_set_color(COLOR_LIGHT_GREY, COLOR_BLACK);
    screen_puts("A simple operating system for learning.\n");
    screen_puts("Features:\n");
    screen_puts("  - Boot loading\n");
    screen_puts("  - Protected mode\n");
    screen_puts("  - Memory management\n");
    screen_puts("  - Process management\n");
    screen_puts("  - Simple file system\n");
    screen_puts("  - Keyboard input\n");
}

// 处理命令
void shell_execute(const char *cmd) {
    if (!cmd || strlen(cmd) == 0) {
        return;
    }

    // 解析命令和参数
    char command[64];
    char args[192];
    memset(command, 0, 64);
    memset(args, 0, 192);

    int i = 0;
    int cmd_len = 0;

    // 提取命令
    while (cmd[i] && cmd[i] != ' ' && cmd_len < 63) {
        command[cmd_len++] = cmd[i++];
    }
    command[cmd_len] = '\0';

    // 跳过空格
    while (cmd[i] == ' ') i++;

    // 提取参数
    int arg_len = 0;
    while (cmd[i] && arg_len < 191) {
        args[arg_len++] = cmd[i++];
    }
    args[arg_len] = '\0';

    // 执行命令
    if (strcmp(command, "help") == 0) {
        cmd_help();
    } else if (strcmp(command, "clear") == 0) {
        cmd_clear();
    } else if (strcmp(command, "echo") == 0) {
        cmd_echo(args);
    } else if (strcmp(command, "ls") == 0) {
        cmd_ls();
    } else if (strcmp(command, "cat") == 0) {
        cmd_cat(args);
    } else if (strcmp(command, "create") == 0) {
        cmd_create(args);
    } else if (strcmp(command, "delete") == 0) {
        cmd_delete(args);
    } else if (strcmp(command, "about") == 0) {
        cmd_about();
    } else if (strcmp(command, "reboot") == 0) {
        screen_puts("Rebooting...\n");
        // 触发重启
        asm volatile("int $0x19");
    } else {
        screen_set_color(COLOR_LIGHT_RED, COLOR_BLACK);
        screen_puts("Unknown command: ");
        screen_puts(command);
        screen_puts("\n");
        screen_set_color(COLOR_LIGHT_GREY, COLOR_BLACK);
        screen_puts("Type 'help' for available commands.\n");
    }
}

// Shell 主循环
void shell_main() {
    // 初始化
    screen_clear();
    screen_set_color(COLOR_LIGHT_CYAN, COLOR_BLACK);
    screen_puts("===================================\n");
    screen_puts("       Simple OS Shell v0.1\n");
    screen_puts("===================================\n\n");
    screen_set_color(COLOR_LIGHT_GREY, COLOR_BLACK);
    screen_puts("Type 'help' for available commands.\n\n");

    // 主循环
    while (1) {
        // 显示提示符
        shell_prompt();

        // 清除命令缓冲区
        shell_clear_buffer();

        // 读取命令
        while (1) {
            char c = keyboard_getchar();

            if (c == '\n') {
                // 回车，执行命令
                screen_putchar('\n');
                shell_execute(cmd_buffer);
                break;
            } else if (c == '\b') {
                // 退格
                if (cmd_pos > 0) {
                    cmd_pos--;
                    cmd_buffer[cmd_pos] = '\0';
                    screen_backspace();
                }
            } else if (c >= 32 && c < 127) {
                // 可打印字符
                if (cmd_pos < CMD_BUFFER_SIZE - 1) {
                    cmd_buffer[cmd_pos++] = c;
                    cmd_buffer[cmd_pos] = '\0';
                    screen_putchar(c);
                }
            }
        }
    }
}
