/*
 * embedded-fs/examples/dir_management.c
 *
 * Directory Management Demo
 * 目录管理演示
 *
 * Demonstrates directory operations: create, list, lookup, remove.
 * Shows the hierarchical directory structure.
 *
 * 演示目录操作：创建、列出、查找、删除。
 * 展示分层目录结构。
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

int main(void) {
    printf("=== Embedded File System - Directory Management ===\n");
    printf("===================================================\n\n");

    /* Format */
    printf("[1] Formatting...\n");
    efs_format();
    printf("Done.\n\n");

    /* Create directory structure */
    printf("[2] Creating directory structure...\n");
    efs_mkdir("/docs");
    printf("  Created /docs\n");
    efs_mkdir("/docs/guide");
    printf("  Created /docs/guide\n");
    efs_mkdir("/data");
    printf("  Created /data\n");
    efs_mkdir("/data/logs");
    printf("  Created /data/logs\n");
    printf("Done.\n\n");

    /* Create files in directories */
    printf("[3] Creating files in directories...\n");
    int fd = efs_open("/docs/readme.txt", EFS_O_WRONLY | EFS_O_CREAT);
    if (fd >= 0) {
        const char *content = "Welcome to the embedded file system!\n";
        efs_write(fd, content, strlen(content));
        efs_close(fd);
        printf("  Created /docs/readme.txt\n");
    }

    fd = efs_open("/docs/guide/user.txt", EFS_O_WRONLY | EFS_O_CREAT);
    if (fd >= 0) {
        const char *content = "User guide content here.\n";
        efs_write(fd, content, strlen(content));
        efs_close(fd);
        printf("  Created /docs/guide/user.txt\n");
    }

    fd = efs_open("/data/config.ini", EFS_O_WRONLY | EFS_O_CREAT);
    if (fd >= 0) {
        const char *content = "[settings]\nmode=production\n";
        efs_write(fd, content, strlen(content));
        efs_close(fd);
        printf("  Created /data/config.ini\n");
    }
    printf("Done.\n\n");

    /* Lookup files */
    printf("[4] Looking up files...\n");
    uint32_t ino;
    EFS_Result res;

    res = efs_path_exists("/docs/readme.txt", &ino);
    printf("  /docs/readme.txt: %s (ino=%u)\n",
           res == EFS_OK ? "exists" : "not found", ino);

    res = efs_path_exists("/nonexistent", &ino);
    printf("  /nonexistent: %s\n",
           res == EFS_OK ? "exists" : "not found");

    res = efs_path_exists("/data/config.ini", &ino);
    printf("  /data/config.ini: %s (ino=%u)\n",
           res == EFS_OK ? "exists" : "not found", ino);
    printf("Done.\n\n");

    /* Read files back */
    printf("[5] Reading files back...\n");
    fd = efs_open("/docs/readme.txt", EFS_O_RDONLY);
    if (fd >= 0) {
        char buf[256];
        int n = efs_read(fd, buf, sizeof(buf));
        buf[n] = '\0';
        printf("  /docs/readme.txt: %s", buf);
        efs_close(fd);
    }

    fd = efs_open("/data/config.ini", EFS_O_RDONLY);
    if (fd >= 0) {
        char buf[256];
        int n = efs_read(fd, buf, sizeof(buf));
        buf[n] = '\0';
        printf("  /data/config.ini: %s", buf);
        efs_close(fd);
    }
    printf("Done.\n\n");

    /* Create and read nested file */
    printf("[6] Testing nested paths...\n");
    fd = efs_open("/data/logs/app.log", EFS_O_WRONLY | EFS_O_CREAT);
    if (fd >= 0) {
        const char *log = "2024-01-01 App started\n2024-01-02 App running\n";
        efs_write(fd, log, strlen(log));
        efs_close(fd);
        printf("  Created /data/logs/app.log\n");
    }

    fd = efs_open("/data/logs/app.log", EFS_O_RDONLY);
    if (fd >= 0) {
        char buf[256];
        int n = efs_read(fd, buf, sizeof(buf));
        buf[n] = '\0';
        printf("  Content: %s", buf);
        efs_close(fd);
    }
    printf("Done.\n\n");

    /* Directory statistics */
    printf("[7] Directory statistics:\n");
    EFS_WearStats wear;
    efs_wear_get_stats(&wear);
    printf("  Total writes:  %u\n", wear.total_writes);
    printf("  Total erases:  %u\n", wear.total_erases);
    printf("  Wear leveling: %u\n", wear.wear_leveling_count);
    printf("\n");

    printf("=== Demo complete ===\n");
    return 0;
}
