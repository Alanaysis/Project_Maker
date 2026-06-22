/**
 * 文件系统测试 (test_fs.c)
 * 功能: 测试文件系统模块
 */

#include "../include/types.h"
#include "../include/fs.h"
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

// 辅助函数: 字符串比较
static int strcmp(const char *s1, const char *s2) {
    while (*s1 && *s2) {
        if (*s1 != *s2) return *s1 - *s2;
        s1++;
        s2++;
    }
    return *s1 - *s2;
}

// 测试文件创建
void test_file_creation() {
    screen_puts("[TEST] File Creation\n");

    // 测试 1: 创建文件
    int ret = fs_create("/test.txt", 0644);
    TEST("create file returns SUCCESS", ret == SUCCESS);

    // 测试 2: 文件存在
    TEST("file exists after creation", fs_exists("/test.txt"));

    // 测试 3: 重复创建
    ret = fs_create("/test.txt", 0644);
    TEST("duplicate creation returns ERROR_EXIST", ret == ERROR_EXIST);

    // 测试 4: 创建另一个文件
    ret = fs_create("/test2.txt", 0644);
    TEST("create second file", ret == SUCCESS);

    // 清理
    fs_delete("/test.txt");
    fs_delete("/test2.txt");
}

// 测试文件读写
void test_file_read_write() {
    screen_puts("[TEST] File Read/Write\n");

    // 创建测试文件
    fs_create("/rw_test.txt", 0644);
    int fd = fs_open("/rw_test.txt", 0);
    TEST("file opened for writing", fd >= 0);

    // 测试 1: 写入数据
    const char *data = "Hello, Simple OS!";
    int written = fs_write(fd, data, 18);
    TEST("write returns correct bytes", written == 18);

    // 关闭并重新打开
    fs_close(fd);
    fd = fs_open("/rw_test.txt", 0);
    TEST("file reopened for reading", fd >= 0);

    // 测试 2: 读取数据
    char buffer[32];
    memset(buffer, 0, 32);
    int read = fs_read(fd, buffer, 18);
    TEST("read returns correct bytes", read == 18);
    TEST("read data matches written data", strcmp(buffer, data) == 0);

    // 测试 3: 读取更多数据
    char buffer2[64];
    memset(buffer2, 0, 64);
    read = fs_read(fd, buffer2, 100);
    TEST("read returns 0 when no more data", read == 0);

    // 清理
    fs_close(fd);
    fs_delete("/rw_test.txt");
}

// 测试文件删除
void test_file_deletion() {
    screen_puts("[TEST] File Deletion\n");

    // 创建文件
    fs_create("/delete_test.txt", 0644);
    TEST("file exists before deletion", fs_exists("/delete_test.txt"));

    // 测试 1: 删除文件
    int ret = fs_delete("/delete_test.txt");
    TEST("delete returns SUCCESS", ret == SUCCESS);
    TEST("file does not exist after deletion", !fs_exists("/delete_test.txt"));

    // 测试 2: 删除不存在的文件
    ret = fs_delete("/nonexistent.txt");
    TEST("delete non-existent returns ERROR_NOENT", ret == ERROR_NOENT);
}

// 测试目录操作
void test_directory_operations() {
    screen_puts("[TEST] Directory Operations\n");

    // 测试 1: 创建目录
    int ret = fs_mkdir("/testdir", 0755);
    TEST("create directory returns SUCCESS", ret == SUCCESS);

    // 测试 2: 目录存在
    file_node_t *dir = fs_stat("/testdir");
    TEST("directory exists", dir != NULL);
    TEST("directory has correct type", dir->type == FILE_TYPE_DIRECTORY);

    // 测试 3: 在目录中创建文件
    ret = fs_create("/testdir/file.txt", 0644);
    TEST("create file in directory", ret == SUCCESS);

    // 测试 4: 删除目录
    ret = fs_rmdir("/testdir");
    TEST("remove directory returns SUCCESS", ret == SUCCESS);
}

// 测试文件信息
void test_file_info() {
    screen_puts("[TEST] File Information\n");

    // 创建文件
    fs_create("/info_test.txt", 0644);
    int fd = fs_open("/info_test.txt", 0);
    fs_write(fd, "test data", 9);
    fs_close(fd);

    // 测试 1: 获取文件信息
    file_node_t *info = fs_stat("/info_test.txt");
    TEST("stat returns valid pointer", info != NULL);
    TEST("file has correct name", strcmp(info->name, "info_test.txt") == 0);
    TEST("file has correct type", info->type == FILE_TYPE_REGULAR);
    TEST("file has correct size", info->size == 9);

    // 清理
    fs_delete("/info_test.txt");
}

// 运行所有文件系统测试
void run_fs_tests() {
    screen_set_color(COLOR_LIGHT_CYAN, COLOR_BLACK);
    screen_puts("\n========================================\n");
    screen_puts("       File System Tests\n");
    screen_puts("========================================\n\n");
    screen_set_color(COLOR_LIGHT_GREY, COLOR_BLACK);

    tests_passed = 0;
    tests_failed = 0;

    // 运行测试
    test_file_creation();
    test_file_read_write();
    test_file_deletion();
    test_directory_operations();
    test_file_info();

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
