/*
 * embedded-fs/src/format.c
 *
 * File System Format and Initialization
 * 文件系统格式化和初始化
 *
 * Handles file system creation (formatting) and initialization.
 * Sets up the superblock, block table, and root directory.
 *
 * 处理文件系统创建（格式化）和初始化。
 * 设置超级块、块表和根目录。
 * ============================================================ */

#include "efs_types.h"
#include "efs_flash.h"
#include "efs_block.h"
#include "efs_dir.h"
#include "efs_file.h"
#include "efs_log.h"
#include "efs_wear.h"
#include "efs_recovery.h"
#include <string.h>
#include <stdio.h>

/* Global context */
static EFS_Context g_efs_ctx = {0};

/* Calculate checksum for a block of data */
static uint32_t efs_calculate_checksum(const void *data, uint32_t len) {
    const uint8_t *p = (const uint8_t *)data;
    uint32_t cksum = 0;
    for (uint32_t i = 0; i < len; i++) {
        cksum ^= p[i];
        cksum = (cksum << 1) | (cksum >> 31);  /* Rotate */
    }
    return cksum;
}

/* Format the file system */
EFS_Result efs_format(void) {
    printf("[Format] Starting file system format...\n");

    /* Step 1: Initialize flash */
    EFS_Result res = efs_flash_init();
    if (res != EFS_OK) return res;

    /* Step 2: Initialize block manager */
    res = efs_block_init();
    if (res != EFS_OK) return res;

    /* Step 3: Initialize wear leveling */
    res = efs_wear_init();
    if (res != EFS_OK) return res;

    /* Step 4: Initialize log */
    res = efs_log_init();
    if (res != EFS_OK) return res;

    /* Step 5: Initialize recovery */
    res = efs_recovery_init();
    if (res != EFS_OK) return res;

    /* Step 6: Erase all blocks */
    printf("[Format] Erasing all blocks...\n");
    for (uint32_t i = 0; i < 256; i++) {
        res = efs_flash_erase(i);
        if (res != EFS_OK) {
            printf("[Format] Block %u is bad, marking as bad\n", i);
            efs_flash_mark_bad(i);
            efs_block_set_state(i, EFS_BLOCK_BAD);
        } else {
            efs_block_set_state(i, EFS_BLOCK_FREE);
            efs_block_update_wear(i, 0);
        }
    }

    /* Step 7: Initialize block table */
    memset(g_efs_ctx.block_table, 0, sizeof(g_efs_ctx.block_table));

    /* Step 8: Create superblock */
    EFS_SuperBlock *sb = &g_efs_ctx.superblock;
    memset(sb, 0, sizeof(EFS_SuperBlock));
    sb->magic = EFS_MAGIC;
    sb->version = EFS_VERSION;
    sb->block_size = EFS_BLOCK_SIZE;
    sb->total_blocks = 256;
    sb->log_head = EFS_LOG_BLOCK_START;
    sb->log_tail = EFS_LOG_BLOCK_START;
    sb->free_blocks = 254;  /* Minus superblock and reserved */
    sb->root_dir_block = EFS_LOG_BLOCK_START;
    sb->checksum = efs_calculate_checksum(sb, sizeof(EFS_SuperBlock) - EFS_CHECKSUM_SIZE);

    /* Write superblock to block 0 */
    res = efs_flash_erase(EFS_SUPERBLOCK_BLOCK);
    if (res != EFS_OK) return res;
    res = efs_flash_write(EFS_SUPERBLOCK_BLOCK, 0, sb, sizeof(EFS_SuperBlock));
    if (res != EFS_OK) return res;

    /* Step 9: Create root directory */
    printf("[Format] Creating root directory...\n");

    /* Allocate a block for root directory */
    uint32_t root_block = efs_block_allocate();
    if (root_block == 0xFFFFFFFF) return EFS_ERR_NOSPACE;
    efs_flash_erase(root_block);
    efs_block_set_state(root_block, EFS_BLOCK_USED);

    /* Initialize root directory with . and .. */
    EFS_DirEntry dot, dotdot;
    memset(&dot, 0, sizeof(dot));
    dot.ino = 0;  /* Root inode */
    dot.type = EFS_FILE_DIRECTORY;
    dot.name_len = 1;
    strcpy(dot.name, ".");

    memset(&dotdot, 0, sizeof(dotdot));
    dotdot.ino = 0;  /* Root points to itself */
    dotdot.type = EFS_FILE_DIRECTORY;
    dotdot.name_len = 2;
    strcpy(dotdot.name, "..");

    efs_flash_write(root_block, 0, &dot, sizeof(dot));
    efs_flash_write(root_block, sizeof(dot), &dotdot, sizeof(dotdot));

    /* Step 10: Initialize file system context */
    memset(&g_efs_ctx, 0, sizeof(g_efs_ctx));
    g_efs_ctx.initialized = 1;
    g_efs_ctx.superblock = *sb;
    g_efs_ctx.next_ino = 1;
    g_efs_ctx.time_counter = 0;
    g_efs_ctx.log_head = EFS_LOG_BLOCK_START;
    g_efs_ctx.log_tail = EFS_LOG_BLOCK_START;

    /* Step 11: Mark as clean */
    efs_recovery_mark_clean();

    printf("[Format] File system formatted successfully.\n");
    printf("[Format] Total blocks: %u, Block size: %u bytes\n",
           sb->total_blocks, sb->block_size);
    printf("[Format] Free blocks: %u\n", sb->free_blocks);

    return EFS_OK;
}

/* Initialize file system (format if needed, or mount existing) */
EFS_Result efs_init(void) {
    printf("[Init] Initializing file system...\n");

    /* Try to read superblock */
    EFS_SuperBlock sb;
    memset(&sb, 0, sizeof(sb));
    EFS_Result res = efs_flash_read(EFS_SUPERBLOCK_BLOCK, 0, &sb, sizeof(sb));

    if (res != EFS_OK || sb.magic != EFS_MAGIC) {
        printf("[Init] No valid file system found. Formatting...\n");
        return efs_format();
    }

    /* Superblock is valid, mount existing file system */
    printf("[Init] Mounting existing file system...\n");

    /* Initialize all subsystems */
    efs_block_init();
    efs_wear_init();
    efs_log_init();
    efs_recovery_init();

    /* Copy superblock */
    g_efs_ctx.superblock = sb;
    g_efs_ctx.initialized = 1;

    /* Run recovery */
    res = efs_recovery_run();
    if (res != EFS_OK) {
        printf("[Init] Recovery failed: %d\n", res);
        return res;
    }

    /* Scan and rebuild block table */
    efs_block_scan_and_rebuild();

    printf("[Init] File system mounted successfully.\n");
    return EFS_OK;
}

/* Get file system context */
EFS_Context *efs_get_context(void) {
    return &g_efs_ctx;
}

/* Get file system info */
EFS_Result efs_get_fs_info(EFS_SuperBlock *out_sb) {
    if (!out_sb) return EFS_ERR_INVAL;
    if (!g_efs_ctx.initialized) return EFS_ERR_BADFS;
    *out_sb = g_efs_ctx.superblock;
    return EFS_OK;
}
