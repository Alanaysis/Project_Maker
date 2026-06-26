#ifndef EFS_BLOCK_H
#define EFS_BLOCK_H

#include "efs_types.h"

/* ============================================================
 * Block Allocation and Management
 * 块分配和管理
 *
 * This module manages the allocation and deallocation of flash
 * blocks. It maintains a free list and tracks block states.
 *
 * 本模块管理闪存块的分配和释放。它维护空闲列表并跟踪块状态。
 * ============================================================ */

/*
 * Initialize the block manager.
 * 初始化块管理器。
 */
EFS_Result efs_block_init(void);

/*
 * Allocate a free block.
 * 分配一个空闲块。
 *
 * Returns the block ID, or EFS_ERR_NOSPACE if none available.
 * 返回块ID，如果没有可用块则返回 EFS_ERR_NOSPACE。
 */
uint32_t efs_block_allocate(void);

/*
 * Free a previously allocated block.
 * 释放之前分配的块。
 */
EFS_Result efs_block_free(uint32_t block);

/*
 * Get the state of a block.
 * 获取块的状态。
 */
EFS_BlockState efs_block_get_state(uint32_t block);

/*
 * Set the state of a block.
 * 设置块的状态。
 */
EFS_Result efs_block_set_state(uint32_t block, EFS_BlockState state);

/*
 * Get the wear count of a block.
 * 获取块的磨损计数。
 */
uint32_t efs_block_get_wear(uint32_t block);

/*
 * Update the wear count of a block.
 * 更新块的磨损计数。
 */
EFS_Result efs_block_update_wear(uint32_t block, uint32_t new_wear);

/*
 * Find the block with minimum wear (for wear leveling).
 * 查找磨损最小的块（用于磨损均衡）。
 */
uint32_t efs_block_find_min_wear(void);

/*
 * Find the block with maximum wear (for garbage collection).
 * 查找磨损最大的块（用于垃圾回收）。
 */
uint32_t efs_block_find_max_wear(void);

/*
 * Get the number of free blocks.
 * 获取空闲块数量。
 */
uint32_t efs_block_get_free_count(void);

/*
 * Scan and rebuild the block table from flash.
 * 扫描并从闪存重建块表。
 */
EFS_Result efs_block_scan_and_rebuild(void);

/*
 * Get block descriptor.
 * 获取块描述符。
 */
EFS_BlockDesc *efs_block_get_desc(uint32_t block);

#endif /* EFS_BLOCK_H */
