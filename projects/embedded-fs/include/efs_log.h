#ifndef EFS_LOG_H
#define EFS_LOG_H

#include "efs_types.h"

/* ============================================================
 * Log-Structured File System Design
 * 日志式文件系统设计
 *
 * In a log-structured FS, all writes are appended to the end
 * of a log (like a write-ahead log). This ensures sequential
 * writes to flash, which is much faster than random writes.
 *
 * 在日志式文件系统中，所有写入都追加到日志末尾
 * （类似于预写日志）。这确保了对闪存的顺序写入，
 * 比随机写入快得多。
 *
 * Key concepts:
 * - Log head: Current write position / 日志头：当前写入位置
 * - Log tail: Oldest valid block / 日志尾：最老的有效块
 * - Checkpoint: Periodic snapshot of file system state / 检查点：文件系统状态的定期快照
 * - Compaction: Merging valid data to reclaim space / 压缩：合并有效数据以回收空间
 *
 * 关键概念：
 * - 日志头：当前写入位置
 * - 日志尾：最老的有效块
 * - 检查点：文件系统状态的定期快照
 * - 压缩：合并有效数据以回收空间
 * ============================================================ */

/* ---- Log record types / 日志记录类型 ---- */

typedef enum {
    EFS_LOG_NONE = 0,
    EFS_LOG_INODE_ALLOC,      /* Inode allocation / 索引节点分配 */
    EFS_LOG_INODE_UPDATE,     /* Inode update / 索引节点更新 */
    EFS_LOG_BLOCK_ALLOC,      /* Block allocation / 块分配 */
    EFS_LOG_DATA_WRITE,       /* Data write / 数据写入 */
    EFS_LOG_DATA_DELETE,      /* Data delete / 数据删除 */
    EFS_LOG_DIR_UPDATE,       /* Directory update / 目录更新 */
    EFS_LOG_CHECKPOINT,       /* File system checkpoint / 文件系统检查点 */
    EFS_LOG_FORMAT            /* File system format / 文件系统格式化 */
} EFS_LogRecordType;

/* ---- Log record header / 日志记录头 ---- */

typedef struct {
    uint32_t type;            /* Log record type / 日志记录类型 */
    uint32_t size;            /* Payload size / 载荷大小 */
    uint32_t checksum;        /* Record checksum / 记录校验和 */
    uint32_t sequence;        /* Monotonic sequence number / 单调序列号 */
} EFS_LogRecord;

/*
 * Initialize the log-structured writer.
 * 初始化日志式写入器。
 */
EFS_Result efs_log_init(void);

/*
 * Append a log record.
 * 追加日志记录。
 */
EFS_Result efs_log_append(EFS_LogRecordType type, const void *data, uint32_t size);

/*
 * Get current log head position.
 * 获取当前日志头位置。
 */
uint32_t efs_log_get_head(void);

/*
 * Get current log tail position.
 * 获取当前日志尾位置。
 */
uint32_t efs_log_get_tail(void);

/*
 * Set log head position (after recovery).
 * 设置日志头位置（恢复后）。
 */
EFS_Result efs_log_set_head(uint32_t block);

/*
 * Set log tail position (after recovery).
 * 设置日志尾位置（恢复后）。
 */
EFS_Result efs_log_set_tail(uint32_t block);

/*
 * Write a checkpoint (full file system state snapshot).
 * 写入检查点（完整文件系统状态快照）。
 */
EFS_Result efs_log_write_checkpoint(void);

/*
 * Check if log is full and compaction is needed.
 * 检查日志是否已满且需要压缩。
 */
int efs_log_needs_compaction(void);

/*
 * Compact the log: move valid data to new blocks.
 * 压缩日志：将有效数据移动到新块。
 */
EFS_Result efs_log_compact(void);

/*
 * Get the next sequential write position.
 * 获取下一个顺序写入位置。
 */
EFS_Result efs_log_next_write_pos(uint32_t *block, uint32_t *offset);

#endif /* EFS_LOG_H */
