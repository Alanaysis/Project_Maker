/*
 * embedded-fs/src/wear_leveling.c
 *
 * Wear Leveling Algorithm
 * 磨损均衡算法
 *
 * Flash memory has limited erase cycles (typically 10K-100K for
 * NAND flash, 100K+ for NOR flash). Wear leveling distributes
 * erase cycles evenly across all blocks to maximize flash lifetime.
 *
 * 闪存寿命有限（NAND 闪存通常为 10K-100K 次，NOR 闪存为 100K+ 次）。
 * 磨损均衡将擦除周期均匀分布到所有块上，以最大化闪存寿命。
 *
 * Two algorithms:
 * 1. Simple count-based wear leveling
 * 2. Advanced with garbage collection
 *
 * 两种算法：
 * 1. 基于计数的简单磨损均衡
 * 2. 带垃圾回收的高级算法
 * ============================================================ */

#include "efs_wear.h"
#include "efs_block.h"
#include "efs_flash.h"
#include "efs_log.h"
#include <string.h>

/* Global wear statistics */
static EFS_WearStats g_wear_stats = {0};

/* Initialize wear leveling */
EFS_Result efs_wear_init(void) {
    memset(&g_wear_stats, 0, sizeof(g_wear_stats));
    return EFS_OK;
}

/* Simple wear leveling: choose block with minimum wear */
uint32_t efs_wear_level_simple(void) {
    uint32_t min_block = 0xFFFFFFFF;
    uint32_t min_wear = 0xFFFFFFFF;

    for (uint32_t i = 0; i < 256; i++) {
        EFS_BlockState state = efs_block_get_state(i);
        if (state == EFS_BLOCK_FREE) {
            uint32_t wear = efs_block_get_wear(i);
            if (wear < min_wear) {
                min_wear = wear;
                min_block = i;
            }
        }
    }

    if (min_block == 0xFFFFFFFF) {
        /* No free blocks, try to find one anyway */
        for (uint32_t i = 0; i < 256; i++) {
            if (efs_block_get_state(i) == EFS_BLOCK_FREE) {
                return i;
            }
        }
    }

    return min_block;
}

/* Advanced wear leveling with garbage collection */
uint32_t efs_wear_level_advanced(void) {
    /* First try simple wear leveling */
    uint32_t block = efs_wear_level_simple();

    if (block != 0xFFFFFFFF) {
        g_wear_stats.wear_leveling_count++;
        return block;
    }

    /* No free blocks, trigger garbage collection */
    efs_gc_collect();

    /* Try again after GC */
    block = efs_wear_level_simple();
    if (block != 0xFFFFFFFF) {
        g_wear_stats.gc_count++;
        return block;
    }

    return 0xFFFFFFFF;  /* Still no blocks */
}

/* Garbage collection: merge valid data and erase stale blocks */
EFS_Result efs_gc_collect(void) {
    uint32_t max_wear_block = efs_block_find_max_wear();
    if (max_wear_block == 0xFFFFFFFF) return EFS_ERR_INVAL;

    /* In a real log-structured FS, we would:
     * 1. Find stale blocks (blocks with no valid references)
     * 2. Copy valid data to new blocks
     * 3. Erase the stale block
     * 4. Update block table
     *
     * For this learning implementation, we simulate GC by:
     * 1. Finding the most worn block
     * 2. Marking it as needing cleanup
     * 3. In production, a background thread would handle this
     */

    /* Simulate: erase the most worn block to free it */
    EFS_Result res = efs_flash_erase(max_wear_block);
    if (res != EFS_OK) return res;

    efs_block_set_state(max_wear_block, EFS_BLOCK_FREE);
    efs_block_update_wear(max_wear_block, efs_block_get_wear(max_wear_block) + 1);

    g_wear_stats.total_erases++;
    g_wear_stats.blocks_erased++;

    return EFS_OK;
}

/* Update wear count after erase */
EFS_Result efs_wear_update_after_erase(uint32_t block) {
    uint32_t current = efs_block_get_wear(block);
    return efs_block_update_wear(block, current + 1);
}

/* Check if wear leveling is needed */
int efs_wear_needs_leveling(void) {
    uint32_t min_wear = 0xFFFFFFFF;
    uint32_t max_wear = 0;

    for (uint32_t i = 0; i < 256; i++) {
        if (efs_block_get_state(i) == EFS_BLOCK_USED ||
            efs_block_get_state(i) == EFS_BLOCK_FREE) {
            uint32_t wear = efs_block_get_wear(i);
            if (wear < min_wear) min_wear = wear;
            if (wear > max_wear) max_wear = wear;
        }
    }

    return (max_wear - min_wear) > EFS_MAX_WEAR_ERR;
}

/* Perform wear leveling rebalance */
EFS_Result efs_wear_rebalance(void) {
    if (!efs_wear_needs_leveling()) return EFS_OK;

    /* Find most and least worn blocks */
    uint32_t worst = efs_block_find_max_wear();
    uint32_t best = efs_block_find_min_wear();

    if (worst == 0xFFFFFFFF || best == 0xFFFFFFFF) return EFS_ERR_INVAL;

    uint32_t worst_wear = efs_block_get_wear(worst);
    uint32_t best_wear = efs_block_get_wear(best);

    if ((worst_wear - best_wear) <= EFS_MAX_WEAR_ERR) return EFS_OK;

    /* In a real system, migrate data from worst to best block */
    /* For learning, we just update wear stats */
    g_wear_stats.wear_leveling_count++;

    return EFS_OK;
}

/* Get wear leveling statistics */
EFS_Result efs_wear_get_stats(EFS_WearStats *stats) {
    if (!stats) return EFS_ERR_INVAL;
    memcpy(stats, &g_wear_stats, sizeof(EFS_WearStats));

    /* Calculate avg wear */
    uint32_t total_wear = 0;
    uint32_t count = 0;
    for (uint32_t i = 0; i < 256; i++) {
        if (efs_block_get_state(i) != EFS_BLOCK_BAD) {
            total_wear += efs_block_get_wear(i);
            count++;
        }
    }
    stats->avg_wear = count > 0 ? total_wear / count : 0;

    /* Find min/max wear */
    stats->best_block_wear = 0xFFFFFFFF;
    stats->worst_block_wear = 0;
    for (uint32_t i = 0; i < 256; i++) {
        if (efs_block_get_state(i) != EFS_BLOCK_BAD) {
            uint32_t w = efs_block_get_wear(i);
            if (w < stats->best_block_wear) stats->best_block_wear = w;
            if (w > stats->worst_block_wear) stats->worst_block_wear = w;
        }
    }

    return EFS_OK;
}

/* Print wear leveling statistics */
void efs_wear_print_stats(void) {
    EFS_WearStats stats;
    efs_wear_get_stats(&stats);

    printf("=== Wear Leveling Statistics ===\n");
    printf("Total writes:     %u\n", stats.total_writes);
    printf("Total erases:     %u\n", stats.total_erases);
    printf("Blocks erased:    %u\n", stats.blocks_erased);
    printf("Wear leveling:    %u\n", stats.wear_leveling_count);
    printf("GC count:         %u\n", stats.gc_count);
    printf("Avg wear:         %u\n", stats.avg_wear);
    printf("Best block wear:  %u\n", stats.best_block_wear);
    printf("Worst block wear: %u\n", stats.worst_block_wear);
    printf("================================\n");
}
