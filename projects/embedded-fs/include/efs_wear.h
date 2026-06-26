#ifndef EFS_WEAR_H
#define EFS_WEAR_H

#include "efs_types.h"

/* ============================================================
 * Wear Leveling Module
 * 磨损均衡模块
 *
 * Flash memory has limited erase cycles (typically 10K-100K).
 * Wear leveling distributes erase cycles evenly across all blocks
 * to maximize flash lifetime.
 *
 * 闪存寿命有限（通常 10K-100K 次擦除）。
 * 磨损均衡将擦除周期均匀分布在所有块上，以最大化闪存寿命。
 *
 * Two algorithms are implemented:
 * 1. Simple count-based: Track wear, prefer least-worn blocks
 * 2. Advanced with garbage collection: Reclaim space from stale blocks
 *
 * 实现了两种算法：
 * 1. 简单计数法：跟踪磨损，优先选择磨损最小的块
 * 2. 带垃圾回收的高级法：从过期块回收空间
 * ============================================================ */

/*
 * Initialize wear leveling.
 * 初始化磨损均衡。
 */
EFS_Result efs_wear_init(void);

/*
 * Simple wear leveling: choose block with minimum wear.
 * 简单磨损均衡：选择磨损最小的块。
 */
uint32_t efs_wear_level_simple(void);

/*
 * Advanced wear leveling with garbage collection.
 * 带垃圾回收的高级磨损均衡。
 *
 * If free blocks are scarce, this triggers garbage collection
 * to reclaim space from blocks with stale data.
 *
 * 如果空闲块稀缺，此函数会触发垃圾回收，
 * 从包含过期数据的块回收空间。
 */
uint32_t efs_wear_level_advanced(void);

/*
 * Garbage collection: merge valid data and erase stale blocks.
 * 垃圾回收：合并有效数据并擦除过期块。
 */
EFS_Result efs_gc_collect(void);

/*
 * Update wear count after erase.
 * 擦除后更新磨损计数。
 */
EFS_Result efs_wear_update_after_erase(uint32_t block);

/*
 * Check if wear leveling is needed.
 * 检查是否需要磨损均衡。
 */
int efs_wear_needs_leveling(void);

/*
 * Perform wear leveling rebalance if needed.
 * 如果需要，执行磨损均衡重平衡。
 */
EFS_Result efs_wear_rebalance(void);

/*
 * Get wear leveling statistics.
 * 获取磨损均衡统计信息。
 */
EFS_Result efs_wear_get_stats(EFS_WearStats *stats);

/*
 * Print wear leveling statistics (for debugging).
 * 打印磨损均衡统计信息（用于调试）。
 */
void efs_wear_print_stats(void);

#endif /* EFS_WEAR_H */
