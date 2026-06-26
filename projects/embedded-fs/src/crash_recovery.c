/*
 * embedded-fs/src/crash_recovery.c
 *
 * Crash Recovery Module
 * 崩溃恢复模块
 *
 * Embedded systems crash frequently (power loss, watchdog reset, etc.).
 * This module ensures the file system can recover to a consistent state.
 *
 * 嵌入式系统经常崩溃（断电、看门狗复位等）。
 * 此模块确保文件系统能恢复到一致状态。
 *
 * Recovery process:
 * 1. Validate superblock checksum
 * 2. Walk log from tail to head
 * 3. Replay valid records
 * 4. Restore to last consistent checkpoint
 *
 * 恢复流程：
 * 1. 验证超级块校验和
 * 2. 从尾到头遍历日志
 * 3. 重放有效记录
 * 4. 恢复到最后一个一致检查点
 * ============================================================ */

#include "efs_recovery.h"
#include "efs_log.h"
#include "efs_block.h"
#include "efs_flash.h"
#include <string.h>
#include <stdio.h>

/* Recovery state */
static int g_clean_shutdown = 1;
static int g_recovery_needed = 0;
static int g_recovery_completed = 0;

/* Initialize recovery */
EFS_Result efs_recovery_init(void) {
    g_clean_shutdown = 1;
    g_recovery_needed = 0;
    g_recovery_completed = 0;
    return EFS_OK;
}

/* Validate superblock */
EFS_Result efs_recovery_validate_superblock(void) {
    /* Read superblock from block 0 */
    EFS_SuperBlock sb;
    memset(&sb, 0, sizeof(sb));

    EFS_Result res = efs_flash_read(EFS_SUPERBLOCK_BLOCK, 0, &sb, sizeof(sb));
    if (res != EFS_OK) return res;

    /* Check magic number */
    if (sb.magic != EFS_MAGIC) {
        return EFS_ERR_BADFS;  /* Not a valid file system */
    }

    /* Verify checksum */
    uint32_t cksum = 0;
    const uint8_t *p = (const uint8_t *)&sb;
    for (uint32_t i = 0; i < sizeof(EFS_SuperBlock); i++) {
        if (i != offsetof(EFS_SuperBlock, checksum)) {
            cksum ^= p[i];
        }
    }

    if (cksum != sb.checksum) {
        return EFS_ERR_CORRUPT;  /* Checksum mismatch */
    }

    return EFS_OK;
}

/* Walk the log and validate records */
EFS_Result efs_recovery_walk_log(void) {
    uint32_t block = efs_log_get_tail();
    uint32_t end = efs_log_get_head();

    printf("[Recovery] Walking log from block %u to %u\n", block, end);

    /* In a real system, read and validate each log record */
    /* For learning, we just walk through */
    (void)block;
    (void)end;

    return EFS_OK;
}

/* Replay log records */
EFS_Result efs_recovery_replay(void) {
    /* In a real system:
     * 1. Read log records from tail
     * 2. For each record, apply the operation
     * 3. Stop at last checkpoint
     * 4. Replay records after checkpoint
     *
     * For learning, we simulate the process
     */
    printf("[Recovery] Replay phase\n");
    return EFS_OK;
}

/* Run crash recovery */
EFS_Result efs_recovery_run(void) {
    printf("[Recovery] Starting crash recovery...\n");

    /* Step 1: Validate superblock */
    EFS_Result res = efs_recovery_validate_superblock();
    if (res != EFS_OK) {
        printf("[Recovery] Superblock invalid (code=%d)\n", res);
        if (res == EFS_ERR_BADFS) {
            printf("[Recovery] File system not formatted. Run format first.\n");
        }
        return res;
    }

    /* Step 2: Check if clean shutdown */
    if (g_clean_shutdown) {
        printf("[Recovery] Clean shutdown detected. No recovery needed.\n");
        g_recovery_completed = 1;
        return EFS_OK;
    }

    /* Step 3: Walk the log */
    res = efs_recovery_walk_log();
    if (res != EFS_OK) {
        printf("[Recovery] Log walk failed: %d\n", res);
        return res;
    }

    /* Step 4: Replay log records */
    res = efs_recovery_replay();
    if (res != EFS_OK) {
        printf("[Recovery] Replay failed: %d\n", res);
        return res;
    }

    /* Step 5: Mark as recovered */
    g_recovery_completed = 1;
    printf("[Recovery] Recovery completed successfully.\n");

    return EFS_OK;
}

/* Check if clean shutdown */
int efs_recovery_is_clean(void) {
    return g_clean_shutdown;
}

/* Mark clean shutdown */
EFS_Result efs_recovery_mark_clean(void) {
    g_clean_shutdown = 1;
    g_recovery_needed = 0;
    return EFS_OK;
}

/* Mark dirty shutdown */
EFS_Result efs_recovery_mark_dirty(void) {
    g_clean_shutdown = 0;
    g_recovery_needed = 1;
    return EFS_OK;
}

/* Get recovery status */
EFS_Result efs_recovery_get_status(int *was_clean, int *recovery_needed) {
    if (was_clean) *was_clean = g_clean_shutdown;
    if (recovery_needed) *recovery_needed = g_recovery_needed;
    return EFS_OK;
}
