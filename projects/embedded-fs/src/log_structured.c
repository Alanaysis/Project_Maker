/*
 * embedded-fs/src/log_structured.c
 *
 * Log-Structured File System Design
 * 日志式文件系统设计
 *
 * Key concepts of log-structured file systems:
 * 1. All writes are sequential (appended to log)
 * 2. No random writes to flash (which are slow and wear-intensive)
 * 3. Periodic compaction to reclaim space
 * 4. Checkpoint for fast recovery
 *
 * 日志式文件系统的核心概念：
 * 1. 所有写入都是顺序的（追加到日志）
 * 2. 无随机闪存写入（慢且增加磨损）
 * 3. 定期压缩回收空间
 * 4. 检查点用于快速恢复
 * ============================================================ */

#include "efs_log.h"
#include "efs_block.h"
#include "efs_flash.h"
#include "efs_wear.h"
#include <string.h>

/* Log state */
static uint32_t g_log_head = EFS_LOG_BLOCK_START;
static uint32_t g_log_tail = EFS_LOG_BLOCK_START;
static uint32_t g_log_sequence = 0;

/* Initialize log */
EFS_Result efs_log_init(void) {
    g_log_head = EFS_LOG_BLOCK_START;
    g_log_tail = EFS_LOG_BLOCK_START;
    g_log_sequence = 0;
    return EFS_OK;
}

/* Get next sequential write position */
EFS_Result efs_log_next_write_pos(uint32_t *block, uint32_t *offset) {
    *block = g_log_head;
    *offset = 0;  /* Start at block boundary for simplicity */

    /* In a real implementation, track byte offset within block */
    return EFS_OK;
}

/* Append a log record */
EFS_Result efs_log_append(EFS_LogRecordType type, const void *data, uint32_t size) {
    /* Get write position */
    uint32_t block, offset;
    EFS_Result res = efs_log_next_write_pos(&block, &offset);
    if (res != EFS_OK) return res;

    /* Build log record */
    EFS_LogRecord record;
    memset(&record, 0, sizeof(record));
    record.type = (uint32_t)type;
    record.size = size;
    record.sequence = g_log_sequence++;

    /* Calculate checksum */
    uint32_t cksum = 0;
    const uint8_t *p = (const uint8_t *)&record;
    for (uint32_t i = 0; i < sizeof(EFS_LogRecord); i++) {
        cksum ^= p[i];
    }
    if (data) {
        const uint8_t *d = (const uint8_t *)data;
        for (uint32_t i = 0; i < size; i++) {
            cksum ^= d[i];
        }
    }
    record.checksum = cksum;

    /* Write record header */
    efs_flash_write(block, offset, &record, sizeof(EFS_LogRecord));
    offset += sizeof(EFS_LogRecord);

    /* Write payload */
    if (data && size > 0) {
        efs_flash_write(block, offset, data, size);
    }

    /* Update log head */
    g_log_head = block;

    return EFS_OK;
}

/* Get log head */
uint32_t efs_log_get_head(void) {
    return g_log_head;
}

/* Get log tail */
uint32_t efs_log_get_tail(void) {
    return g_log_tail;
}

/* Set log head */
EFS_Result efs_log_set_head(uint32_t block) {
    g_log_head = block;
    return EFS_OK;
}

/* Set log tail */
EFS_Result efs_log_set_tail(uint32_t block) {
    g_log_tail = block;
    return EFS_OK;
}

/* Write checkpoint */
EFS_Result efs_log_write_checkpoint(void) {
    /* Write a checkpoint record with file system state */
    EFS_LogRecord checkpoint;
    memset(&checkpoint, 0, sizeof(checkpoint));
    checkpoint.type = (uint32_t)EFS_LOG_CHECKPOINT;
    checkpoint.size = 0;
    checkpoint.sequence = g_log_sequence++;

    efs_log_append(EFS_LOG_CHECKPOINT, &checkpoint, sizeof(checkpoint));

    return EFS_OK;
}

/* Check if log needs compaction */
int efs_log_needs_compaction(void) {
    /* Simple heuristic: if free blocks < 10%, compact */
    uint32_t free_count = efs_block_get_free_count();
    return free_count < 25;  /* Less than 10% of 256 blocks */
}

/* Compact the log */
EFS_Result efs_log_compact(void) {
    /* In a real implementation:
     * 1. Identify valid data in log blocks
     * 2. Allocate new blocks for valid data
     * 3. Copy valid data to new blocks
     * 4. Update log head/tail
     * 5. Erase old blocks
     *
     * For learning, we simulate compaction by GC
     */
    return efs_gc_collect();
}
