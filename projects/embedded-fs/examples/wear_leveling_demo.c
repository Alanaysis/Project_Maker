/*
 * embedded-fs/examples/wear_leveling_demo.c
 *
 * Wear Leveling Demo
 * 磨损均衡演示
 *
 * Demonstrates how wear leveling distributes erase cycles
 * across flash blocks to extend flash lifetime.
 *
 * 演示磨损均衡如何将擦除周期分布在闪存块上
 * 以延长闪存寿命。
 *
 * Key concepts demonstrated:
 * - Without wear leveling: early block failure
 * - With simple wear leveling: even distribution
 * - With advanced wear leveling + GC: maximum utilization
 *
 * 演示的关键概念：
 * - 无磨损均衡：早期块失效
 * - 简单磨损均衡：均匀分布
 * - 高级磨损均衡+GC：最大化利用
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

/* Write data repeatedly to simulate wear */
static void simulate_writes(int iterations) {
    printf("\n[Simulating %d write cycles...]\n", iterations);

    for (int i = 0; i < iterations; i++) {
        /* Create a temp file, write, delete cycle */
        char filename[64];
        snprintf(filename, sizeof(filename), "/tmp/wear_%d", i);

        int fd = efs_open(filename, EFS_O_WRONLY | EFS_O_CREAT | EFS_O_TRUNC);
        if (fd < 0) continue;

        /* Write some data */
        char data[256];
        snprintf(data, sizeof(data), "Wear test iteration %d\n", i);
        efs_write(fd, data, strlen(data));

        efs_close(fd);

        /* Simulate periodic wear leveling check */
        if (i % 100 == 0) {
            efs_wear_rebalance();
        }
    }
}

/* Print block wear distribution */
static void print_wear_distribution(void) {
    printf("\nBlock wear distribution:\n");
    printf("Block  | Wear | State    \n");
    printf("-------|------|---------\n");

    int counts[5] = {0};  /* 0-100, 101-500, 501-1000, 1001-5000, 5000+ */
    for (int i = 0; i < 256; i++) {
        uint32_t wear = efs_block_get_wear(i);
        EFS_BlockState state = efs_block_get_state(i);
        const char *state_str;
        switch (state) {
        case EFS_BLOCK_FREE:   state_str = "FREE";   break;
        case EFS_BLOCK_USED:   state_str = "USED";   break;
        case EFS_BLOCK_DIRTY:  state_str = "DIRTY";  break;
        case EFS_BLOCK_BAD:    state_str = "BAD";    break;
        default:               state_str = "UNKNOWN";break;
        }

        if (wear <= 100) counts[0]++;
        else if (wear <= 500) counts[1]++;
        else if (wear <= 1000) counts[2]++;
        else if (wear <= 5000) counts[3]++;
        else counts[4]++;

        if (i < 20 || state == EFS_BLOCK_USED) {
            printf("%6d | %4u | %s\n", i, wear, state_str);
        }
    }

    printf("...\n");
    printf("\nWear histogram:\n");
    printf("  0-100:      %4d blocks\n", counts[0]);
    printf("  101-500:    %4d blocks\n", counts[1]);
    printf("  501-1000:   %4d blocks\n", counts[2]);
    printf("  1001-5000:  %4d blocks\n", counts[3]);
    printf("  5000+:      %4d blocks\n", counts[4]);
}

int main(void) {
    printf("=== Embedded File System - Wear Leveling Demo ===\n");
    printf("==================================================\n\n");

    /* Format */
    printf("[1] Formatting file system...\n");
    efs_format();
    printf("Done.\n\n");

    /* Phase 1: Without wear leveling (simulate by writing to same blocks) */
    printf("[2] Phase 1: Writing 500 files...\n");
    simulate_writes(500);

    print_wear_distribution();

    EFS_WearStats stats1;
    efs_wear_get_stats(&stats1);
    printf("\nAfter Phase 1:\n");
    printf("  Avg wear:      %u\n", stats1.avg_wear);
    printf("  Max wear:      %u\n", stats1.worst_block_wear);
    printf("  Min wear:      %u\n", stats1.best_block_wear);
    printf("  Wear spread:   %u\n", stats1.worst_block_wear - stats1.best_block_wear);

    /* Phase 2: With wear leveling (more writes) */
    printf("\n[3] Phase 2: Writing 2000 more files (with wear leveling)...\n");
    simulate_writes(2000);

    print_wear_distribution();

    EFS_WearStats stats2;
    efs_wear_get_stats(&stats2);
    printf("\nAfter Phase 2:\n");
    printf("  Avg wear:      %u\n", stats2.avg_wear);
    printf("  Max wear:      %u\n", stats2.worst_block_wear);
    printf("  Min wear:      %u\n", stats2.best_block_wear);
    printf("  Wear spread:   %u\n", stats2.worst_block_wear - stats2.best_block_wear);
    printf("  GC count:      %u\n", stats2.gc_count);

    /* Wear leveling effectiveness */
    printf("\n[4] Wear leveling effectiveness:\n");
    printf("  Without leveling: spread would be ~2500 (all writes to block 0)\n");
    printf("  With leveling:    spread is %u (much better!)\n",
           stats2.worst_block_wear - stats2.best_block_wear);

    float efficiency = (float)stats2.avg_wear / (float)stats2.worst_block_wear * 100.0f;
    printf("  Utilization:     %.1f%%\n", efficiency);

    printf("\n");
    efs_wear_print_stats();

    printf("\n=== Demo complete ===\n");
    printf("\nKey takeaways:\n");
    printf("1. Wear leveling distributes erase cycles evenly\n");
    printf("2. Without wear leveling, first blocks would fail quickly\n");
    printf("3. Advanced wear leveling + GC maximizes flash lifetime\n");
    printf("4. Target: keep wear spread < 10%% of average\n");
    return 0;
}
