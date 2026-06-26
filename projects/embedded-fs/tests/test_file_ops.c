/*
 * embedded-fs/tests/test_file_ops.c
 *
 * Unit Tests for File Operations
 * 文件操作单元测试
 *
 * Tests all file operations: open, close, read, write, seek, stat.
 * 测试所有文件操作：open、close、read、write、seek、stat。
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
extern EFS_Result efs_get_fs_info(EFS_SuperBlock *out_sb);

static int tests_run = 0;
static int tests_passed = 0;
static int tests_failed = 0;

#define TEST(name) printf("  TEST: %s ... ", name); tests_run++;
#define PASS()     printf("PASS\n"); tests_passed++
#define FAIL(msg)  printf("FAIL: %s\n", msg); tests_failed++
#define ASSERT(cond, msg) do { \
    if (!(cond)) { FAIL(msg); return; } \
} while(0)

/* Test file creation and writing */
static void test_file_create_and_write(void) {
    TEST("create and write file");

    efs_format();

    int fd = efs_open("/test1.txt", EFS_O_WRONLY | EFS_O_CREAT);
    ASSERT(fd >= 0, "open should succeed");

    const char *msg = "Hello World";
    int written = efs_write(fd, msg, strlen(msg));
    ASSERT(written == strlen(msg), "write should return correct bytes");

    efs_close(fd);
    PASS();
}

/* Test file reading */
static void test_file_read(void) {
    TEST("read file");

    efs_format();

    int fd = efs_open("/test2.txt", EFS_O_WRONLY | EFS_O_CREAT);
    ASSERT(fd >= 0, "open should succeed");

    const char *msg = "Read test data";
    efs_write(fd, msg, strlen(msg));
    efs_close(fd);

    /* Read back */
    fd = efs_open("/test2.txt", EFS_O_RDONLY);
    ASSERT(fd >= 0, "open for read should succeed");

    char buf[256];
    int read_bytes = efs_read(fd, buf, sizeof(buf));
    ASSERT(read_bytes == strlen(msg), "read should return correct bytes");

    buf[read_bytes] = '\0';
    ASSERT(strcmp(buf, msg) == 0, "content should match");

    efs_close(fd);
    PASS();
}

/* Test file seek */
static void test_file_seek(void) {
    TEST("seek in file");

    efs_format();

    int fd = efs_open("/test3.txt", EFS_O_WRONLY | EFS_O_CREAT);
    const char *msg = "0123456789ABCDEF";
    efs_write(fd, msg, strlen(msg));

    /* Seek to middle */
    int new_pos = efs_seek(fd, 5, 0);  /* SEEK_SET */
    ASSERT(new_pos == 5, "seek to offset 5");

    char buf[16];
    int n = efs_read(fd, buf, 6);
    ASSERT(n == 6, "read after seek");
    buf[n] = '\0';
    ASSERT(strcmp(buf, "56789A") == 0, "content after seek");

    /* Seek from current */
    new_pos = efs_seek(fd, 3, 1);  /* SEEK_CUR */
    ASSERT(new_pos == 14, "seek from current");

    efs_close(fd);
    PASS();
}

/* Test file truncation */
static void test_file_truncate(void) {
    TEST("truncate file");

    efs_format();

    int fd = efs_open("/test4.txt", EFS_O_WRONLY | EFS_O_CREAT);
    const char *msg = "This is a longer file";
    efs_write(fd, msg, strlen(msg));
    efs_close(fd);

    EFS_Result res = efs_truncate("/test4.txt", 8);
    ASSERT(res == EFS_OK, "truncate should succeed");

    fd = efs_open("/test4.txt", EFS_O_RDONLY);
    char buf[256];
    int n = efs_read(fd, buf, sizeof(buf));
    buf[n] = '\0';
    ASSERT(n == 8, "truncated size");
    ASSERT(strcmp(buf, "This is ") == 0, "truncated content");

    efs_close(fd);
    PASS();
}

/* Test overwrite with truncate flag */
static void test_overwrite(void) {
    TEST("overwrite with truncate");

    efs_format();

    int fd = efs_open("/test5.txt", EFS_O_WRONLY | EFS_O_CREAT);
    efs_write(fd, "Old content", 11);
    efs_close(fd);

    /* Overwrite with truncate */
    fd = efs_open("/test5.txt", EFS_O_WRONLY | EFS_O_TRUNC);
    efs_write(fd, "New", 3);
    efs_close(fd);

    fd = efs_open("/test5.txt", EFS_O_RDONLY);
    char buf[256];
    int n = efs_read(fd, buf, sizeof(buf));
    buf[n] = '\0';
    ASSERT(n == 3, "truncated on open");
    ASSERT(strcmp(buf, "New") == 0, "content should be new");

    efs_close(fd);
    PASS();
}

/* Test append mode */
static void test_append(void) {
    TEST("append mode");

    efs_format();

    int fd = efs_open("/test6.txt", EFS_O_WRONLY | EFS_O_CREAT);
    efs_write(fd, "Line 1\n", 7);
    efs_close(fd);

    fd = efs_open("/test6.txt", EFS_O_WRONLY | EFS_O_APPEND);
    efs_write(fd, "Line 2\n", 7);
    efs_close(fd);

    fd = efs_open("/test6.txt", EFS_O_RDONLY);
    char buf[256];
    int n = efs_read(fd, buf, sizeof(buf));
    buf[n] = '\0';
    ASSERT(strcmp(buf, "Line 1\nLine 2\n") == 0, "append should work");

    efs_close(fd);
    PASS();
}

/* Test file stat */
static void test_file_stat(void) {
    TEST("file stat");

    efs_format();

    int fd = efs_open("/test7.txt", EFS_O_WRONLY | EFS_O_CREAT);
    const char *msg = "Stat test data";
    efs_write(fd, msg, strlen(msg));

    EFS_Inode info;
    EFS_Result res = efs_fstat(fd, &info);
    ASSERT(res == EFS_OK, "fstat should succeed");
    ASSERT(info.size == strlen(msg), "size should match");
    ASSERT(info.type == EFS_FILE_REGULAR, "type should be regular");

    efs_close(fd);

    /* Also test stat by path */
    res = efs_stat("/test7.txt", &info);
    ASSERT(res == EFS_OK, "stat should succeed");
    ASSERT(info.size == strlen(msg), "stat size should match");

    PASS();
}

/* Test opening non-existent file without create */
static void test_open_nonexistent(void) {
    TEST("open nonexistent without create");

    efs_format();

    int fd = efs_open("/nonexistent.txt", EFS_O_RDONLY);
    ASSERT(fd < 0, "should fail for non-existent file");
    PASS();
}

/* Test multiple files */
static void test_multiple_files(void) {
    TEST("multiple files");

    efs_format();

    /* Create multiple files */
    int fd1 = efs_open("/file_a.txt", EFS_O_WRONLY | EFS_O_CREAT);
    efs_write(fd1, "File A", 6);
    efs_close(fd1);

    int fd2 = efs_open("/file_b.txt", EFS_O_WRONLY | EFS_O_CREAT);
    efs_write(fd2, "File B", 6);
    efs_close(fd2);

    int fd3 = efs_open("/file_c.txt", EFS_O_WRONLY | EFS_O_CREAT);
    efs_write(fd3, "File C", 6);
    efs_close(fd3);

    /* Read them back */
    fd1 = efs_open("/file_a.txt", EFS_O_RDONLY);
    char buf[64];
    int n = efs_read(fd1, buf, sizeof(buf));
    buf[n] = '\0';
    ASSERT(strcmp(buf, "File A") == 0, "file_a content");
    efs_close(fd1);

    fd2 = efs_open("/file_b.txt", EFS_O_RDONLY);
    n = efs_read(fd2, buf, sizeof(buf));
    buf[n] = '\0';
    ASSERT(strcmp(buf, "File B") == 0, "file_b content");
    efs_close(fd2);

    PASS();
}

/* Test binary data */
static void test_binary_data(void) {
    TEST("binary data");

    efs_format();

    uint8_t data[256];
    for (int i = 0; i < 256; i++) data[i] = (uint8_t)i;

    int fd = efs_open("/binary.bin", EFS_O_WRONLY | EFS_O_CREAT);
    int written = efs_write(fd, data, 256);
    ASSERT(written == 256, "write 256 bytes");
    efs_close(fd);

    fd = efs_open("/binary.bin", EFS_O_RDONLY);
    uint8_t read_buf[256];
    int n = efs_read(fd, read_buf, 256);
    ASSERT(n == 256, "read 256 bytes");

    for (int i = 0; i < 256; i++) {
        ASSERT(read_buf[i] == (uint8_t)i, "binary data match");
    }
    efs_close(fd);

    PASS();
}

/* Test large file */
static void test_large_file(void) {
    TEST("large file");

    efs_format();

    char data[1024];
    for (int i = 0; i < 1024; i++) data[i] = (char)(i % 256);

    int fd = efs_open("/large.bin", EFS_O_WRONLY | EFS_O_CREAT);
    int total = 0;
    for (int i = 0; i < 10; i++) {
        total += efs_write(fd, data, 1024);
    }
    ASSERT(total == 10240, "write 10KB");
    efs_close(fd);

    EFS_Inode info;
    efs_stat("/large.bin", &info);
    ASSERT(info.size == 10240, "size should be 10KB");

    PASS();
}

int main(void) {
    printf("=== Embedded File System - File Operations Tests ===\n");
    printf("====================================================\n\n");

    test_file_create_and_write();
    test_file_read();
    test_file_seek();
    test_file_truncate();
    test_overwrite();
    test_append();
    test_file_stat();
    test_open_nonexistent();
    test_multiple_files();
    test_binary_data();
    test_large_file();

    printf("\n====================================================\n");
    printf("Results: %d/%d passed, %d failed\n",
           tests_passed, tests_run, tests_failed);
    printf("====================================================\n");

    return tests_failed > 0 ? 1 : 0;
}
