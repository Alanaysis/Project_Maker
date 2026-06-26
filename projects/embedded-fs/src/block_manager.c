/*
 * embedded-fs/src/block_manager.c
 *
 * Block Allocation and Management
 * 块分配和管理
 *
 * Manages flash block allocation, tracking block states and wear counts.
 * Maintains a block descriptor table for efficient block management.
 *
 * 管理闪存块分配，跟踪块状态和磨损计数。
 * 维护块描述符表以高效管理块。
 * ============================================================ */

#include "efs_block.h"
#include "efs_flash.h"
#include <string.h>

/* Block descriptor table stored in memory */
static EFS_BlockDesc g_block_table[256];

/* Initialize block manager */
EFS_Result efs_block_init(void) {
    memset(g_block_table, 0, sizeof(g_block_table));
    return EFS_OK;
}

/* Allocate a free block, preferring low-wear blocks */
uint32_t efs_block_allocate(void) {
    uint32_t best_block = 0xFFFFFFFF;
    uint32_t min_wear = 0xFFFFFFFF;

    /* Find free block with minimum wear (simple wear leveling) */
    for (uint32_t i = 0; i < 256; i++) {
        if (g_block_table[i].state == EFS_BLOCK_FREE) {
            if (g_block_table[i].wear_count < min_wear) {
                min_wear = g_block_table[i].wear_count;
                best_block = i;
            }
        }
    }

    if (best_block == 0xFFFFFFFF) {
        return 0xFFFFFFFF;  /* No free blocks */
    }

    /* Mark block as dirty (prepared for writing) */
    g_block_table[best_block].state = EFS_BLOCK_DIRTY;
    g_block_table[best_block].block_id = best_block;
    g_block_table[best_block].next_block = 0xFFFFFFFF;
    g_block_table[best_block].prev_block = 0xFFFFFFFF;

    return best_block;
}

/* Free a block */
EFS_Result efs_block_free(uint32_t block) {
    if (block >= 256) return EFS_ERR_INVAL;

    g_block_table[block].state = EFS_BLOCK_FREE;
    g_block_table[block].next_block = 0xFFFFFFFF;
    g_block_table[block].prev_block = 0xFFFFFFFF;

    return EFS_OK;
}

/* Get block state */
EFS_BlockState efs_block_get_state(uint32_t block) {
    if (block >= 256) return EFS_BLOCK_BAD;
    return (EFS_BlockState)g_block_table[block].state;
}

/* Set block state */
EFS_Result efs_block_set_state(uint32_t block, EFS_BlockState state) {
    if (block >= 256) return EFS_ERR_INVAL;
    g_block_table[block].state = (uint8_t)state;
    return EFS_OK;
}

/* Get wear count */
uint32_t efs_block_get_wear(uint32_t block) {
    if (block >= 256) return 0;
    return g_block_table[block].wear_count;
}

/* Update wear count */
EFS_Result efs_block_update_wear(uint32_t block, uint32_t new_wear) {
    if (block >= 256) return EFS_ERR_INVAL;
    g_block_table[block].wear_count = new_wear;
    return EFS_OK;
}

/* Find block with minimum wear */
uint32_t efs_block_find_min_wear(void) {
    uint32_t best = 0xFFFFFFFF;
    uint32_t min_wear = 0xFFFFFFFF;

    for (uint32_t i = 0; i < 256; i++) {
        if (g_block_table[i].state == EFS_BLOCK_FREE ||
            g_block_table[i].state == EFS_BLOCK_USED) {
            if (g_block_table[i].wear_count < min_wear) {
                min_wear = g_block_table[i].wear_count;
                best = i;
            }
        }
    }
    return best;
}

/* Find block with maximum wear */
uint32_t efs_block_find_max_wear(void) {
    uint32_t best = 0xFFFFFFFF;
    uint32_t max_wear = 0;

    for (uint32_t i = 0; i < 256; i++) {
        if (g_block_table[i].state == EFS_BLOCK_USED) {
            if (g_block_table[i].wear_count > max_wear) {
                max_wear = g_block_table[i].wear_count;
                best = i;
            }
        }
    }
    return best;
}

/* Get free block count */
uint32_t efs_block_get_free_count(void) {
    uint32_t count = 0;
    for (uint32_t i = 0; i < 256; i++) {
        if (g_block_table[i].state == EFS_BLOCK_FREE) count++;
    }
    return count;
}

/* Scan flash and rebuild block table (for recovery) */
EFS_Result efs_block_scan_and_rebuild(void) {
    /* In a real system, scan all blocks and rebuild state */
    /* For simulation, block table is already in memory */
    (void)0;
    return EFS_OK;
}

/* Get block descriptor */
EFS_BlockDesc *efs_block_get_desc(uint32_t block) {
    if (block >= 256) return NULL;
    return &g_block_table[block];
}
