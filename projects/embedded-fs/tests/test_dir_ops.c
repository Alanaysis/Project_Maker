/*
 * embedded-fs/tests/test_dir_ops.c
 *
 * Unit Tests for Directory Operations
 * 目录操作单元测试
 * ============================================================ */

#include <stdio.h>
#include <string.h>
#include "../include/efs_types.h"
#include "../include/efs_flash.h"
#include "../include/efs_block.h"
#include "../include/efs_dir.h"
#include "../include/efs_file.h"
#include "../include/efs_log.h"
#include "../include/efs_wear.h"
#include "../include/efs_recovery.h"

extern EFS_Result efs_format(void);

static int tests_run = 0;
static int tests_passed = 0;
static int tests_failed = 0;

#define TEST(name) printf("  TEST: %s ... ", name); tests_run++;
#define PASS()     printf("PASS\n"); tests_passed++
#define FAIL(msg)  printf("FAIL: %s\n", msg); tests_failed++
#define ASSERT(cond, msg) do { \
    if (!(cond)) { FAIL(msg); return; } \
} while(0)

static void test_mkdir(void) {
    TEST("create directory");

    efs_format();

    EFS_Result res = efs_mkdir("/mydir");
    ASSERT(res == EFS_OK, "mkdir should succeed");

    uint32_t ino;
    res = efs_path_exists("/mydir", &ino);
    ASSERT(res == EFS_OK, "directory should exist");

    EFS_Inode info;
    efs_inode_read(ino, &info);
    ASSERT(info.type == EFS_FILE_DIRECTORY, "type should be directory");

    PASS();
}

static void test_nested_dirs(void) {
    TEST("nested directories");

    efs_format();

    efs_mkdir("/a");
    efs_mkdir("/a/b");
    efs_mkdir("/a/b/c");

    uint32_t ino;
    ASSERT(efs_path_exists("/a", &ino) == EFS_OK, "/a exists");
    ASSERT(efs_path_exists("/a/b", &ino) == EFS_OK, "/a/b exists");
    ASSERT(efs_path_exists("/a/b/c", &ino) == EFS_OK, "/a/b/c exists");

    PASS();
}

static void test_file_in_dir(void) {
    TEST("file in directory");

    efs_format();

    efs_mkdir("/data");
    int fd = efs_open("/data/file.txt", EFS_O_WRONLY | EFS_O_CREAT);
    ASSERT(fd >= 0, "file in dir should open");

    efs_write(fd, "content", 7);
    efs_close(fd);

    uint32_t ino;
    ASSERT(efs_path_exists("/data/file.txt", &ino) == EFS_OK, "file exists");

    fd = efs_open("/data/file.txt", EFS_O_RDONLY);
    char buf[64];
    int n = efs_read(fd, buf, sizeof(buf));
    buf[n] = '\0';
    ASSERT(strcmp(buf, "content") == 0, "content match");
    efs_close(fd);

    PASS();
}

static void test_path_exists(void) {
    TEST("path exists check");

    efs_format();

    ASSERT(efs_path_exists("/nonexistent", &ino) != EFS_OK, "nonexistent should fail");

    efs_mkdir("/testdir");
    uint32_t ino;
    ASSERT(efs_path_exists("/testdir", &ino) == EFS_OK, "existing dir should pass");

    PASS();
}

static void test_dir_add_and_lookup(void) {
    TEST("dir add and lookup");

    efs_format();

    efs_mkdir("/logs");
    int fd = efs_open("/logs/app.log", EFS_O_WRONLY | EFS_O_CREAT);
    efs_write(fd, "log entry\n", 10);
    efs_close(fd);

    uint32_t ino;
    EFS_Result res = efs_path_exists("/logs/app.log", &ino);
    ASSERT(res == EFS_OK, "lookup should succeed");

    EFS_Inode info;
    efs_inode_read(ino, &info);
    ASSERT(info.size == 10, "size should match");
    ASSERT(info.type == EFS_FILE_REGULAR, "type should be regular");

    PASS();
}

int main(void) {
    printf("=== Embedded File System - Directory Tests ===\n");
    printf("===============================================\n\n");

    test_mkdir();
    test_nested_dirs();
    test_file_in_dir();
    test_path_exists();
    test_dir_add_and_lookup();

    printf("\n===============================================\n");
    printf("Results: %d/%d passed, %d failed\n",
           tests_passed, tests_run, tests_failed);
    printf("===============================================\n");

    return tests_failed > 0 ? 1 : 0;
}
