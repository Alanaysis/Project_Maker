#ifndef EFS_RECOVERY_H
#define EFS_RECOVERY_H

#include "efs_types.h"

/* ============================================================
 * Crash Recovery Module
 * 崩溃恢复模块
 *
 * Embedded systems often crash unexpectedly (power loss, reset).
 * This module ensures the file system can recover to a consistent
 * state after a crash.
 *
 * 嵌入式系统经常意外崩溃（断电、复位）。
 * 此模块确保文件系统能在崩溃后恢复到一致状态。
 *
 * Recovery strategy:
 * 1. Read superblock and verify checksum
 * 2. Walk the log from tail to head
 * 3. Replay valid log records
 * 4. Restore file system to last checkpoint state
 *
 * 恢复策略：
 * 1. 读取超级块并校验和
 * 2. 从日志尾到日志头遍历
 * 3. 重放有效日志记录
 * 4. 将文件系统恢复到上次检查点状态
 * ============================================================ */

/*
 * Initialize crash recovery.
 * 初始化崩溃恢复。
 */
EFS_Result efs_recovery_init(void);

/*
 * Run crash recovery.
 * 执行崩溃恢复。
 *
 * Returns EFS_OK if recovery completed successfully.
 * 如果恢复成功完成，返回 EFS_OK。
 */
EFS_Result efs_recovery_run(void);

/*
 * Check if file system was cleanly unmounted.
 * 检查文件系统是否已干净卸载。
 */
int efs_recovery_is_clean(void);

/*
 * Mark file system as clean.
 * 标记文件系统为干净。
 */
EFS_Result efs_recovery_mark_clean(void);

/*
 * Mark file system as dirty (unclean shutdown detected).
 * 标记文件系统为脏（检测到非正常关机）。
 */
EFS_Result efs_recovery_mark_dirty(void);

/*
 * Get recovery status.
 * 获取恢复状态。
 */
EFS_Result efs_recovery_get_status(int *was_clean, int *recovery_needed);

/*
 * Walk the log and validate records.
 * 遍历日志并验证记录。
 */
EFS_Result efs_recovery_walk_log(void);

/*
 * Replay log records to restore state.
 * 重放日志记录以恢复状态。
 */
EFS_Result efs_recovery_replay(void);

/*
 * Validate superblock checksum and integrity.
 * 验证超级块校验和完整性。
 */
EFS_Result efs_recovery_validate_superblock(void);

#endif /* EFS_RECOVERY_H */
