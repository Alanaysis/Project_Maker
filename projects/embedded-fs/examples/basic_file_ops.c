/*
 * embedded-fs/examples/basic_file_ops.c
 *
 * Basic File Operations Demo
 * 基本文件操作演示
 *
 * Demonstrates the core file operations: open, write, read, seek, close.
 * Shows how the log-structured FS handles sequential writes.
 *
 * 演示核心文件操作：open、write、read、seek、close。
 * 展示日志式文件系统如何处理顺序写入。
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

/* Forward declaration for format/init */
extern EFS_Result efs_format(void);
extern EFS_Result efs_init(void);
extern EFS_Result efs_get_fs_info(EFS_SuperBlock *out_sb);

int main(void) {
    printf("=== Embedded File System - Basic File Operations ===\n");
    printf("====================================================\n\n");

    /* Format the file system */
    printf("[1] Formatting file system...\n");
    EFS_Result res = efs_format();
    if (res != EFS_OK) {
        printf("Format failed: %d\n", res);
        return 1;
    }
    printf("File system formatted.\n\n");

    /* Get file system info */
    EFS_SuperBlock sb;
    efs_get_fs_info(&sb);
    printf("File system info:\n");
    printf("  Magic:      0x%08X\n", sb.magic);
    printf("  Version:    %u\n", sb.version);
    printf("  Block size: %u bytes\n", sb.block_size);
    printf("  Total:      %u blocks\n", sb.total_blocks);
    printf("  Free:       %u blocks\n\n", sb.free_blocks);

    /* Open a file for writing */
    printf("[2] Creating file 'hello.txt'...\n");
    int fd = efs_open("/hello.txt", EFS_O_WRONLY | EFS_O_CREAT | EFS_O_TRUNC);
    if (fd < 0) {
        printf("Open failed: %d\n", fd);
        return 1;
    }
    printf("File opened with fd=%d\n\n", fd);

    /* Write data */
    const char *message = "Hello from Embedded File System!\n";
    int written = efs_write(fd, message, strlen(message));
    printf("Wrote %d bytes: \"%s\"\n", written, message);

    /* Write more data */
    const char *more = "Log-structured FS stores data sequentially.\n";
    written = efs_write(fd, more, strlen(more));
    printf("Wrote %d more bytes\n\n", written);

    /* Seek back and read */
    printf("[3] Reading file...\n");
    efs_seek(fd, 0, 0);  /* Seek to start */

    char buffer[256];
    int read_bytes = efs_read(fd, buffer, sizeof(buffer));
    buffer[read_bytes] = '\0';
    printf("Read %d bytes: \"%s\"\n\n", read_bytes, buffer);

    /* Get file status */
    EFS_Inode info;
    efs_fstat(fd, &info);
    printf("[4] File info:\n");
    printf("  Size:     %u bytes\n", info.size);
    printf("  Type:     %u\n", info.type);
    printf("  Blocks:   %u\n", info.block_count);
    printf("  Modified: %u\n\n", info.mtime);

    /* Append more data */
    printf("[5] Appending data...\n");
    const char *append = "Appended line.\n";
    int fd2 = efs_open("/hello.txt", EFS_O_WRONLY | EFS_O_APPEND);
    if (fd2 >= 0) {
        written = efs_write(fd2, append, strlen(append));
        printf("Appended %d bytes\n", written);
        efs_close(fd2);
    }

    /* Read again to verify */
    int fd3 = efs_open("/hello.txt", EFS_O_RDONLY);
    if (fd3 >= 0) {
        efs_seek(fd3, 0, 0);
        read_bytes = efs_read(fd3, buffer, sizeof(buffer));
        buffer[read_bytes] = '\0';
        printf("Full content:\n%s", buffer);
        efs_close(fd3);
    }
    printf("\n");

    /* Create another file */
    printf("[6] Creating 'data.bin'...\n");
    int fd4 = efs_open("/data.bin", EFS_O_WRONLY | EFS_O_CREAT);
    if (fd4 >= 0) {
        uint8_t test_data[1024];
        for (int i = 0; i < 1024; i++) test_data[i] = (uint8_t)(i & 0xFF);
        written = efs_write(fd4, test_data, 1024);
        printf("Wrote %d bytes to binary file\n", written);

        /* Read back */
        efs_seek(fd4, 0, 0);
        read_bytes = efs_read(fd4, buffer, 16);
        buffer[read_bytes] = '\0';
        printf("Read back (hex): ");
        efs_seek(fd4, 0, 0);
        read_bytes = efs_read(fd4, buffer, 16);
        for (int i = 0; i < read_bytes; i++) {
            printf("%02X ", ((uint8_t *)buffer)[i]);
        }
        printf("\n");
        efs_close(fd4);
    }
    printf("\n");

    /* List files (simple listing) */
    printf("[7] File system state:\n");
    EFS_WearStats wear;
    efs_wear_get_stats(&wear);
    printf("  Total writes:  %u\n", wear.total_writes);
    printf("  Total erases:  %u\n", wear.total_erases);
    printf("  Avg wear:      %u\n", wear.avg_wear);
    printf("\n");

    printf("=== Demo complete ===\n");
    return 0;
}
