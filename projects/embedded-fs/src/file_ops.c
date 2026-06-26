/*
 * embedded-fs/src/file_ops.c
 *
 * File Operations Layer
 * 文件操作层
 *
 * Implements POSIX-like file operations for the embedded file system.
 * Supports open, close, read, write, seek, and stat.
 *
 * 为嵌入式文件系统实现类 POSIX 文件操作。
 * 支持 open、close、read、write、seek 和 stat。
 * ============================================================ */

#include "efs_file.h"
#include "efs_block.h"
#include "efs_dir.h"
#include "efs_log.h"
#include "efs_wear.h"
#include <string.h>
#include <stdio.h>

/* Global file system context */
static EFS_Context g_efs_ctx = {0};

/* Initialize file system context */
static void efs_init_context(void) {
    memset(&g_efs_ctx, 0, sizeof(g_efs_ctx));
    g_efs_ctx.initialized = 0;
    g_efs_ctx.next_ino = 1;
    g_efs_ctx.time_counter = 0;
}

/* Get global context */
EFS_Context *efs_get_context(void) {
    return &g_efs_ctx;
}

/* Find free slot in file table */
int efs_file_table_find_free(void) {
    for (int i = 0; i < EFS_MAX_FILES; i++) {
        if (g_efs_ctx.file_table[i].fd == -1 || g_efs_ctx.file_table[i].ino == 0) {
            return i;
        }
    }
    return -1;
}

/* Get file descriptor */
EFS_FileDesc *efs_file_table_get(int fd) {
    if (fd < 0 || fd >= EFS_MAX_FILES) return NULL;
    if (g_efs_ctx.file_table[fd].ino == 0) return NULL;
    return &g_efs_ctx.file_table[fd];
}

/* Allocate new inode */
uint32_t efs_inode_alloc(void) {
    uint32_t ino = g_efs_ctx.next_ino++;
    if (ino >= EFS_MAX_FILES) return 0;

    /* Clear inode */
    memset(&g_efs_ctx.inodes[ino], 0, sizeof(EFS_Inode));
    g_efs_ctx.inodes[ino].magic = EFS_INODE_MAGIC;
    g_efs_ctx.inodes[ino].ino = ino;

    return ino;
}

/* Get inode by number */
EFS_Inode *efs_inode_get(uint32_t ino) {
    if (ino >= EFS_MAX_FILES) return NULL;
    if (g_efs_ctx.inodes[ino].magic != EFS_INODE_MAGIC) return NULL;
    return &g_efs_ctx.inodes[ino];
}

/* Write inode to "disk" (simulated) */
EFS_Result efs_inode_write(EFS_Inode *inode) {
    if (!inode || inode->magic != EFS_INODE_MAGIC) return EFS_ERR_INVAL;

    /* Calculate checksum */
    uint32_t cksum = 0;
    const uint8_t *p = (const uint8_t *)inode;
    for (uint32_t i = 0; i < sizeof(EFS_Inode); i++) {
        if (i != sizeof(uint32_t) * 4) {  /* Skip checksum fields */
            cksum ^= p[i];
        }
    }
    inode->checksum = cksum;

    /* In real system, write to flash block here */
    /* For simulation, data is in memory */
    return EFS_OK;
}

/* Read inode from "disk" */
EFS_Result efs_inode_read(uint32_t ino, EFS_Inode *out) {
    if (ino >= EFS_MAX_FILES) return EFS_ERR_INVAL;

    /* Copy from memory (simulated disk) */
    memcpy(out, &g_efs_ctx.inodes[ino], sizeof(EFS_Inode));

    /* Verify checksum */
    uint32_t cksum = 0;
    const uint8_t *p = (const uint8_t *)out;
    for (uint32_t i = 0; i < sizeof(EFS_Inode); i++) {
        if (i != sizeof(uint32_t) * 4) {
            cksum ^= p[i];
        }
    }
    if (cksum != out->checksum) return EFS_ERR_CORRUPT;

    return EFS_OK;
}

/* Open a file */
int efs_open(const char *path, uint32_t flags) {
    uint32_t ino = 0;
    EFS_Result res;

    /* Check if file exists */
    res = efs_path_exists(path, &ino);

    if (res != EFS_OK) {
        /* File doesn't exist */
        if (!(flags & EFS_O_CREAT)) {
            return -EFS_ERR_NOTFOUND;
        }

        /* Create new file */
        uint32_t parent_ino = 0;
        char name[EFS_MAX_FILENAME];
        res = efs_get_parent(path, &parent_ino, name, sizeof(name));
        if (res != EFS_OK) return -EFS_ERR_INVAL;

        ino = efs_inode_alloc();
        if (ino == 0) return -EFS_ERR_NOMEM;

        /* Initialize inode */
        memset(&g_efs_ctx.inodes[ino], 0, sizeof(EFS_Inode));
        g_efs_ctx.inodes[ino].magic = EFS_INODE_MAGIC;
        g_efs_ctx.inodes[ino].ino = ino;
        g_efs_ctx.inodes[ino].type = EFS_FILE_REGULAR;
        g_efs_ctx.inodes[ino].size = 0;
        g_efs_ctx.inodes[ino].block_count = 0;
        g_efs_ctx.inodes[ino].parent_ino = parent_ino;
        g_efs_ctx.inodes[ino].atime = g_efs_ctx.time_counter;
        g_efs_ctx.inodes[ino].mtime = g_efs_ctx.time_counter;

        /* Add to parent directory */
        char basename[EFS_MAX_FILENAME];
        const char *last_slash = strrchr(path, '/');
        if (last_slash) {
            strncpy(basename, last_slash + 1, EFS_MAX_FILENAME - 1);
            basename[EFS_MAX_FILENAME - 1] = '\0';
        } else {
            strncpy(basename, path, EFS_MAX_FILENAME - 1);
            basename[EFS_MAX_FILENAME - 1] = '\0';
        }
        efs_dir_add_entry(parent_ino, basename, ino, EFS_FILE_REGULAR);

        efs_inode_write(&g_efs_ctx.inodes[ino]);
    } else {
        /* File exists - handle truncate flag */
        if (flags & EFS_O_TRUNC) {
            g_efs_ctx.inodes[ino].size = 0;
            g_efs_ctx.inodes[ino].block_count = 0;
            memset(g_efs_ctx.inodes[ino].blocks, 0, sizeof(g_efs_ctx.inodes[ino].blocks));
            g_efs_ctx.inodes[ino].mtime = g_efs_ctx.time_counter;
            efs_inode_write(&g_efs_ctx.inodes[ino]);
        }
    }

    /* Allocate file descriptor */
    int fd = efs_file_table_find_free();
    if (fd < 0) return -EFS_ERR_NOSPACE;

    EFS_FileDesc *fdesc = &g_efs_ctx.file_table[fd];
    fdesc->fd = fd;
    fdesc->ino = ino;
    fdesc->flags = flags;
    fdesc->offset = 0;

    /* Handle append mode */
    if (flags & EFS_O_APPEND) {
        fdesc->offset = g_efs_ctx.inodes[ino].size;
    }

    fdesc->size = g_efs_ctx.inodes[ino].size;
    fdesc->type = g_efs_ctx.inodes[ino].type;
    fdesc->block_count = g_efs_ctx.inodes[ino].block_count;
    fdesc->blocks = g_efs_ctx.inodes[ino].blocks;
    fdesc->atime = g_efs_ctx.time_counter;
    fdesc->mtime = g_efs_ctx.time_counter;

    return fd;
}

/* Close a file */
EFS_Result efs_close(int fd) {
    if (fd < 0 || fd >= EFS_MAX_FILES) return EFS_ERR_INVAL;

    EFS_FileDesc *fdesc = &g_efs_ctx.file_table[fd];
    if (fdesc->ino == 0) return EFS_ERR_INVAL;

    /* Update inode */
    g_efs_ctx.inodes[fdesc->ino].size = fdesc->size;
    g_efs_ctx.inodes[fdesc->ino].mtime = g_efs_ctx.time_counter;
    efs_inode_write(&g_efs_ctx.inodes[fdesc->ino]);

    /* Release file descriptor */
    fdesc->fd = -1;
    fdesc->ino = 0;

    return EFS_OK;
}

/* Read from file */
int efs_read(int fd, void *buf, uint32_t len) {
    EFS_FileDesc *fdesc = efs_file_table_get(fd);
    if (!fdesc) return -EFS_ERR_INVAL;
    if (fdesc->flags & EFS_O_WRONLY) return -EFS_ERR_INVAL;

    EFS_Inode *inode = &g_efs_ctx.inodes[fdesc->ino];

    /* Calculate bytes remaining */
    uint32_t remaining = inode->size - fdesc->offset;
    if (len > remaining) len = remaining;
    if (len == 0) return 0;

    /* Read from block chain */
    uint32_t blocks_needed = (len + fdesc->offset + EFS_BLOCK_SIZE - 1) / EFS_BLOCK_SIZE;
    uint32_t read = 0;
    uint8_t *out = (uint8_t *)buf;

    for (uint32_t i = 0; i < blocks_needed && read < len; i++) {
        uint32_t block = fdesc->blocks[i];
        if (block == 0 || block >= 256) break;

        /* Calculate offset within block */
        uint32_t block_offset = fdesc->offset - read;
        uint32_t off_in_block = block_offset % EFS_BLOCK_SIZE;
        uint32_t bytes_in_block = EFS_BLOCK_SIZE - off_in_block;
        uint32_t to_read = (len - read > bytes_in_block) ? bytes_in_block : (len - read);

        /* Read from simulated flash */
        efs_flash_read(block, off_in_block, out + read, to_read);
        read += to_read;
    }

    fdesc->offset += read;
    fdesc->atime = g_efs_ctx.time_counter;

    return (int)read;
}

/* Write to file */
int efs_write(int fd, const void *buf, uint32_t len) {
    EFS_FileDesc *fdesc = efs_file_table_get(fd);
    if (!fdesc) return -EFS_ERR_INVAL;
    if (fdesc->flags & EFS_O_RDONLY) return -EFS_ERR_INVAL;

    EFS_Inode *inode = &g_efs_ctx.inodes[fdesc->ino];
    const uint8_t *data = (const uint8_t *)buf;
    uint32_t written = 0;

    while (written < len) {
        /* Check if we need a new block */
        uint32_t current_pos = fdesc->offset;
        uint32_t block_idx = current_pos / EFS_BLOCK_SIZE;
        uint32_t off_in_block = current_pos % EFS_BLOCK_SIZE;

        /* Need more blocks? */
        if (block_idx >= inode->block_count) {
            /* Allocate new block with wear leveling */
            uint32_t new_block = efs_wear_level_advanced();
            if (new_block == 0xFFFFFFFF) return -EFS_ERR_NOSPACE;

            /* Erase the block first (flash requirement) */
            efs_flash_erase(new_block);
            efs_block_set_state(new_block, EFS_BLOCK_USED);
            efs_block_update_wear(new_block, efs_block_get_wear(new_block) + 1);

            /* Add to inode block chain */
            if (inode->block_count < 16) {
                inode->blocks[inode->block_count] = new_block;
                inode->block_count++;
                fdesc->block_count = inode->block_count;
                fdesc->blocks = inode->blocks;
            } else {
                return -EFS_ERR_NOSPACE;  /* Max blocks per file reached */
            }
        }

        /* Calculate bytes to write in this block */
        uint32_t off_in_blk = current_pos % EFS_BLOCK_SIZE;
        uint32_t space_in_blk = EFS_BLOCK_SIZE - off_in_blk;
        uint32_t to_write = (len - written > space_in_blk) ? space_in_blk : (len - written);

        /* Write to simulated flash */
        efs_flash_write(block_idx >= 0 ? fdesc->blocks[block_idx] : 0,
                       off_in_blk, data + written, to_write);

        fdesc->offset += to_write;
        written += to_write;
    }

    /* Update inode */
    if (fdesc->offset > inode->size) {
        inode->size = fdesc->offset;
    }
    inode->mtime = g_efs_ctx.time_counter;
    efs_inode_write(inode);

    g_efs_ctx.time_counter++;

    return (int)written;
}

/* Seek in file */
int efs_seek(int fd, int32_t offset, int whence) {
    EFS_FileDesc *fdesc = efs_file_table_get(fd);
    if (!fdesc) return -EFS_ERR_INVAL;

    EFS_Inode *inode = &g_efs_ctx.inodes[fdesc->ino];
    uint32_t new_offset;

    switch (whence) {
    case 0:  /* SEEK_SET */
        new_offset = (uint32_t)offset;
        break;
    case 1:  /* SEEK_CUR */
        new_offset = fdesc->offset + (uint32_t)offset;
        break;
    case 2:  /* SEEK_END */
        new_offset = inode->size + (uint32_t)offset;
        break;
    default:
        return -EFS_ERR_INVAL;
    }

    /* Clamp to valid range */
    if (new_offset > inode->size) new_offset = inode->size;

    fdesc->offset = new_offset;
    return (int)new_offset;
}

/* Get file status */
EFS_Result efs_stat(const char *path, EFS_Inode *info) {
    uint32_t ino;
    EFS_Result res = efs_path_exists(path, &ino);
    if (res != EFS_OK) return res;

    return efs_inode_read(ino, info);
}

/* Get file status from fd */
EFS_Result efs_fstat(int fd, EFS_Inode *info) {
    EFS_FileDesc *fdesc = efs_file_table_get(fd);
    if (!fdesc) return EFS_ERR_INVAL;

    return efs_inode_read(fdesc->ino, info);
}

/* Truncate file */
EFS_Result efs_truncate(const char *path, uint32_t new_size) {
    uint32_t ino;
    EFS_Result res = efs_path_exists(path, &ino);
    if (res != EFS_OK) return res;

    EFS_Inode *inode = &g_efs_ctx.inodes[ino];
    uint32_t old_blocks = inode->block_count;

    /* Calculate new block count */
    uint32_t new_blocks = (new_size + EFS_BLOCK_SIZE - 1) / EFS_BLOCK_SIZE;
    if (new_size == 0) new_blocks = 0;

    /* Free extra blocks */
    for (uint32_t i = new_blocks; i < old_blocks; i++) {
        uint32_t block = inode->blocks[i];
        if (block < 256) {
            efs_block_free(block);
        }
    }

    inode->size = new_size;
    inode->block_count = new_blocks;
    inode->mtime = g_efs_ctx.time_counter;

    /* Zero out freed block pointers */
    for (uint32_t i = new_blocks; i < old_blocks; i++) {
        inode->blocks[i] = 0;
    }

    efs_inode_write(inode);
    return EFS_OK;
}

/* Sync file to flash */
EFS_Result efs_sync(int fd) {
    EFS_FileDesc *fdesc = efs_file_table_get(fd);
    if (!fdesc) return EFS_ERR_INVAL;

    /* In a real system, flush buffers to flash */
    /* For simulation, data is already in memory */
    return EFS_OK;
}

/* Global context accessor */
EFS_Context *efs_get_context(void);  /* Forward declaration */
