#ifndef EFS_FLASH_H
#define EFS_FLASH_H

#include "efs_types.h"

/* ============================================================
 * Flash Memory Abstraction Layer
 * 闪存抽象层
 *
 * This module provides a hardware abstraction for flash memory.
 * In a real embedded system, these functions would interface
 * with the actual flash controller (SPI flash, internal Flash,
 * NAND flash, etc.).
 *
 * 本模块提供闪存的硬件抽象层。
 * 在实际嵌入式系统中，这些函数会与实际的闪存控制器交互。
 * ============================================================ */

/*
 * Initialize the flash memory abstraction.
 * 初始化闪存抽象层。
 */
EFS_Result efs_flash_init(void);

/*
 * Read data from flash block.
 * 从闪存块读取数据。
 *
 * Args:
 *   block: Physical block number / 物理块号
 *   offset: Byte offset within block / 块内字节偏移
 *   buf: Output buffer / 输出缓冲区
 *   len: Number of bytes to read / 读取字节数
 */
EFS_Result efs_flash_read(uint32_t block, uint32_t offset, void *buf, uint32_t len);

/*
 * Write data to flash block.
 *
 * IMPORTANT: Flash must be erased before writing (erase=0xFF, write=0x00).
 * This function handles the erase-before-write requirement.
 *
 * 重要：写入前必须擦除闪存（擦除=0xFF，写入=0x00）。
 * 此函数处理擦除后写入的要求。
 */
EFS_Result efs_flash_write(uint32_t block, uint32_t offset, const void *buf, uint32_t len);

/*
 * Erase a flash block.
 * 擦除闪存块。
 */
EFS_Result efs_flash_erase(uint32_t block);

/*
 * Get flash geometry information.
 * 获取闪存几何信息。
 */
EFS_Result efs_flash_get_geometry(EFS_FlashGeometry *geo);

/*
 * Check if a block is bad.
 * 检查块是否损坏。
 */
int efs_flash_is_bad_block(uint32_t block);

/*
 * Mark a block as bad.
 * 标记块为损坏。
 */
EFS_Result efs_flash_mark_bad(uint32_t block);

/*
 * Simulated flash operations for learning/testing.
 * 用于学习和测试的模拟闪存操作。
 *
 * In production, replace with real hardware drivers.
 * 生产中请替换为真实硬件驱动。
 */
void efs_flash_register_simulated_ops(void);

#endif /* EFS_FLASH_H */
