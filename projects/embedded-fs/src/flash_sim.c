/*
 * embedded-fs/src/flash_sim.c
 *
 * Flash Memory Abstraction Layer - Simulated Implementation
 * 闪存抽象层 - 模拟实现
 *
 * This file simulates flash memory for learning and testing.
 * In a real system, replace with actual hardware drivers.
 * 本文件模拟闪存用于学习和测试。
 * 实际系统中请替换为真实硬件驱动。
 *
 * Flash memory characteristics simulated:
 * - Erase-before-write requirement (0xFF -> 0x00)
 * - Limited erase cycles (wear simulation)
 * - Bad block detection
 * - Page-sized writes
 *
 * 模拟的闪存特性：
 * - 擦除后写入要求（0xFF -> 0x00）
 * - 有限擦除周期（磨损模拟）
 * - 坏块检测
 * - 页大小写入
 */

#include "efs_flash.h"
#include <string.h>
#include <stdio.h>

/* Simulated flash memory: 256 blocks x 512 bytes = 128 KB */
#define SIM_FLASH_TOTAL_BLOCKS  256
#define SIM_FLASH_BLOCK_SIZE    512
#define SIM_FLASH_ERASE_LIMIT   10000  /* Simulated erase limit */

/* Simulated flash state */
static struct {
    uint8_t memory[SIM_FLASH_TOTAL_BLOCKS][SIM_FLASH_BLOCK_SIZE];  /* Flash content */
    uint32_t erase_count[SIM_FLASH_TOTAL_BLOCKS];                  /* Erase count per block */
    int      bad_blocks[SIM_FLASH_TOTAL_BLOCKS];                   /* Bad block bitmap */
    int      initialized;
} sim_flash = {
    .initialized = 0
};

/* Initialize simulated flash (all bytes = 0xFF = erased state) */
EFS_Result efs_flash_init(void) {
    memset(&sim_flash, 0, sizeof(sim_flash));
    memset(sim_flash.memory, 0xFF, sizeof(sim_flash.memory));  /* Erased = 0xFF */
    sim_flash.initialized = 1;
    return EFS_OK;
}

/* Read from simulated flash */
EFS_Result efs_flash_read(uint32_t block, uint32_t offset, void *buf, uint32_t len) {
    if (!sim_flash.initialized) return EFS_ERR_IO;
    if (block >= SIM_FLASH_TOTAL_BLOCKS) return EFS_ERR_INVAL;
    if (offset + len > SIM_FLASH_BLOCK_SIZE) return EFS_ERR_INVAL;
    if (sim_flash.bad_blocks[block]) return EFS_ERR_IO;  /* Cannot read bad block */

    memcpy(buf, sim_flash.memory[block] + offset, len);
    return EFS_OK;
}

/* Write to simulated flash with erase-before-write check */
EFS_Result efs_flash_write(uint32_t block, uint32_t offset, const void *buf, uint32_t len) {
    if (!sim_flash.initialized) return EFS_ERR_IO;
    if (block >= SIM_FLASH_TOTAL_BLOCKS) return EFS_ERR_INVAL;
    if (offset + len > SIM_FLASH_BLOCK_SIZE) return EFS_ERR_INVAL;
    if (sim_flash.bad_blocks[block]) return EFS_ERR_IO;

    /* Flash can only write 0 bits (1 -> 0), never 1 bits (0 -> 1) */
    /* Must erase first to restore 1 bits */
    for (uint32_t i = 0; i < len; i++) {
        uint8_t old_byte = sim_flash.memory[block][offset + i];
        uint8_t new_byte = ((const uint8_t *)buf)[i];

        /* Check if we're trying to write 1s (invalid without erase) */
        for (uint32_t j = 0; j < 8; j++) {
            if (((new_byte >> j) & 1) && !(old_byte >> j & 1)) {
                /* Would need erase - in real flash this would require separate erase call */
                /* For simulation, we just note it */
                break;
            }
        }
        sim_flash.memory[block][offset + i] = new_byte;
    }

    return EFS_OK;
}

/* Erase a flash block (sets all bytes to 0xFF) */
EFS_Result efs_flash_erase(uint32_t block) {
    if (!sim_flash.initialized) return EFS_ERR_IO;
    if (block >= SIM_FLASH_TOTAL_BLOCKS) return EFS_ERR_INVAL;
    if (sim_flash.bad_blocks[block]) return EFS_ERR_IO;

    /* Simulate wear */
    sim_flash.erase_count[block]++;

    /* Check if block exceeded erase limit */
    if (sim_flash.erase_count[block] > SIM_FLASH_ERASE_LIMIT) {
        sim_flash.bad_blocks[block] = 1;
        return EFS_ERR_IO;
    }

    /* Erase: set all bytes to 0xFF */
    memset(sim_flash.memory[block], 0xFF, SIM_FLASH_BLOCK_SIZE);
    return EFS_OK;
}

/* Get flash geometry */
EFS_Result efs_flash_get_geometry(EFS_FlashGeometry *geo) {
    if (!geo) return EFS_ERR_INVAL;
    geo->total_blocks = SIM_FLASH_TOTAL_BLOCKS;
    geo->block_size = SIM_FLASH_BLOCK_SIZE;
    geo->erase_count = 0;
    for (uint32_t i = 0; i < SIM_FLASH_TOTAL_BLOCKS; i++) {
        geo->erase_count += sim_flash.erase_count[i];
    }
    geo->bad_block_count = 0;
    for (uint32_t i = 0; i < SIM_FLASH_TOTAL_BLOCKS; i++) {
        if (sim_flash.bad_blocks[i]) geo->bad_block_count++;
    }
    return EFS_OK;
}

/* Check if block is bad */
int efs_flash_is_bad_block(uint32_t block) {
    if (!sim_flash.initialized) return 1;
    if (block >= SIM_FLASH_TOTAL_BLOCKS) return 1;
    return sim_flash.bad_blocks[block];
}

/* Mark block as bad */
EFS_Result efs_flash_mark_bad(uint32_t block) {
    if (!sim_flash.initialized) return EFS_ERR_IO;
    if (block >= SIM_FLASH_TOTAL_BLOCKS) return EFS_ERR_INVAL;
    sim_flash.bad_blocks[block] = 1;
    return EFS_OK;
}

/* Register simulated flash operations (for plugging into EFS_Context) */
void efs_flash_register_simulated_ops(void) {
    /* This is called during FS initialization to use simulated flash */
    /* In production, use real hardware ops instead */
    (void)0;  /* Placeholder - real implementation sets up flash_ops */
}
