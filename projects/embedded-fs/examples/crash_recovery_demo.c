/*
 * embedded-fs/examples/crash_recovery_demo.c
 *
 * Crash Recovery Demo
 * 崩溃恢复演示
 *
 * Demonstrates crash recovery: simulate a crash, then recover.
 * Shows how the log-structured FS rebuilds state from the log.
 *
 * 演示崩溃恢复：模拟崩溃，然后恢复。
 * 展示日志式文件系统如何从日志重建状态。
 *
 * Simulated crash scenarios:
 * 1. Clean shutdown (no recovery needed)
 * 2. Unclean shutdown (recovery from log)
 * 3. Corrupted superblock (format required)
 *
 * 模拟的崩溃场景：
 * 1. 正常关机（无需恢复）
 * 2. 非正常关机（从日志恢复）
 * 3. 超级块损坏（需要格式化）
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
extern EFS_Result efs_init(void);
extern EFS_Result efs_get_fs_info(EFS_SuperBlock *out_sb);

/* Scenario 1: Clean shutdown */
static void scenario_clean_shutdown(void) {
    printf("\n=== Scenario 1: Clean Shutdown ===\n");

    /* Format */
    efs_format();

    /* Create some files */
    int fd = efs_open("/clean_test.txt", EFS_O_WRONLY | EFS_O_CREAT);
    if (fd >= 0) {
        const char *msg = "This file was created before clean shutdown.\n";
        efs_write(fd, msg, strlen(msg));
        efs_close(fd);
        printf("Created /clean_test.txt\n");
    }

    /* Mark as clean shutdown */
    efs_recovery_mark_clean();
    printf("Marked as clean shutdown.\n");

    /* Simulate restart */
    printf("\n--- Simulating restart ---\n");
    efs_init();

    int was_clean = 0;
    int needs_recovery = 0;
    efs_recovery_get_status(&was_clean, &needs_recovery);
    printf("Was clean: %s, Recovery needed: %s\n",
           was_clean ? "yes" : "no",
           needs_recovery ? "yes" : "no");

    /* Verify file still exists */
    uint32_t ino = 0;
    if (efs_path_exists("/clean_test.txt", &ino) == EFS_OK) {
        printf("File /clean_test.txt still exists (ino=%u) - CORRECT!\n", ino);
    } else {
        printf("File /clean_test.txt NOT FOUND - ERROR!\n");
    }
}

/* Scenario 2: Unclean shutdown */
static void scenario_unclean_shutdown(void) {
    printf("\n\n=== Scenario 2: Unclean Shutdown ===\n");

    /* Format */
    efs_format();

    /* Create files */
    int fd = efs_open("/unclean_test.txt", EFS_O_WRONLY | EFS_O_CREAT);
    if (fd >= 0) {
        const char *msg = "Data before crash!\n";
        efs_write(fd, msg, strlen(msg));
        /* Simulate crash: close without syncing */
        efs_close(fd);
        printf("Created /unclean_test.txt\n");
    }

    /* Mark as dirty (simulating crash) */
    efs_recovery_mark_dirty();
    printf("Simulating crash (unclean shutdown)...\n");

    /* Simulate restart with recovery */
    printf("\n--- Simulating restart with recovery ---\n");
    efs_init();

    int was_clean = 0;
    int needs_recovery = 0;
    efs_recovery_get_status(&was_clean, &needs_recovery);
    printf("Was clean: %s, Recovery needed: %s\n",
           was_clean ? "yes" : "no",
           needs_recovery ? "yes" : "no");

    /* Verify data survived */
    uint32_t ino = 0;
    if (efs_path_exists("/unclean_test.txt", &ino) == EFS_OK) {
        printf("File /unclean_test.txt exists (ino=%u)\n", ino);

        fd = efs_open("/unclean_test.txt", EFS_O_RDONLY);
        if (fd >= 0) {
            char buf[256];
            int n = efs_read(fd, buf, sizeof(buf));
            buf[n] = '\0';
            printf("Content: %s", buf);
            efs_close(fd);
        }
    } else {
        printf("File /unclean_test.txt NOT FOUND\n");
    }
}

/* Scenario 3: Corrupted superblock */
static void scenario_corrupted_sb(void) {
    printf("\n\n=== Scenario 3: Corrupted Superblock ===\n");

    /* Format first */
    efs_format();
    printf("File system formatted.\n");

    /* Corrupt the superblock */
    printf("Corrupting superblock...\n");
    EFS_SuperBlock corrupted_sb;
    memset(&corrupted_sb, 0, sizeof(corrupted_sb));
    corrupted_sb.magic = 0xDEADBEEF;  /* Wrong magic */
    corrupted_sb.checksum = 0;
    efs_flash_write(EFS_SUPERBLOCK_BLOCK, 0, &corrupted_sb, sizeof(corrupted_sb));
    printf("Superblock corrupted (magic = 0x%08X)\n", corrupted_sb.magic);

    /* Try to initialize */
    printf("\n--- Trying to initialize with corrupted superblock ---\n");
    EFS_Result res = efs_init();
    if (res == EFS_ERR_BADFS) {
        printf("Detected bad file system (as expected)\n");
        printf("Would need to run format again.\n");
    } else {
        printf("Unexpected result: %d\n", res);
    }
}

int main(void) {
    printf("=== Embedded File System - Crash Recovery Demo ===\n");
    printf("===================================================\n\n");

    printf("This demo shows how the file system handles:\n");
    printf("1. Clean shutdown (no data loss)\n");
    printf("2. Unclean shutdown (crash recovery)\n");
    printf("3. Corrupted superblock (error detection)\n");

    /* Run scenarios */
    scenario_clean_shutdown();
    scenario_unclean_shutdown();
    scenario_corrupted_sb();

    printf("\n\n=== Demo complete ===\n");
    printf("\nKey takeaways:\n");
    printf("1. Clean shutdown: immediate mount, no recovery needed\n");
    printf("2. Unclean shutdown: log replay restores consistent state\n");
    printf("3. Corrupted superblock: detected and reported\n");
    printf("4. Log-structured design enables fast recovery\n");
    return 0;
}
