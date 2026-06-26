/*
 * embedded-fs/src/dir_ops.c
 *
 * Directory Management
 * 目录管理
 *
 * Implements directory structure and operations.
 * Directories are special files containing EFS_DirEntry records.
 *
 * 实现目录结构和操作。
 * 目录是包含 EFS_DirEntry 记录的特殊文件。
 * ============================================================ */

#include "efs_dir.h"
#include "efs_file.h"
#include "efs_block.h"
#include "efs_flash.h"
#include <string.h>
#include <stdio.h>

/* Global context */
extern EFS_Context *efs_get_context(void);

/* Create directory */
EFS_Result efs_mkdir(const char *path) {
    EFS_Context *ctx = efs_get_context();
    uint32_t parent_ino = 0;
    char name[EFS_MAX_FILENAME];

    /* Find parent directory */
    EFS_Result res = efs_get_parent(path, &parent_ino, name, sizeof(name));
    if (res != EFS_OK) return res;

    /* Check if already exists */
    uint32_t existing_ino = 0;
    if (efs_path_exists(path, &existing_ino) == EFS_OK) {
        return EFS_ERR_EXIST;
    }

    /* Allocate new inode for directory */
    uint32_t dir_ino = ctx->next_ino++;
    memset(&ctx->inodes[dir_ino], 0, sizeof(EFS_Inode));
    ctx->inodes[dir_ino].magic = EFS_INODE_MAGIC;
    ctx->inodes[dir_ino].ino = dir_ino;
    ctx->inodes[dir_ino].type = EFS_FILE_DIRECTORY;
    ctx->inodes[dir_ino].size = sizeof(EFS_DirEntry);  /* At least one entry */
    ctx->inodes[dir_ino].block_count = 0;
    ctx->inodes[dir_ino].parent_ino = parent_ino;
    ctx->inodes[dir_ino].atime = ctx->time_counter;
    ctx->inodes[dir_ino].mtime = ctx->time_counter;

    /* Add "." entry pointing to self */
    EFS_DirEntry dot;
    memset(&dot, 0, sizeof(dot));
    dot.ino = dir_ino;
    dot.type = EFS_FILE_DIRECTORY;
    dot.name_len = 1;
    strcpy(dot.name, ".");

    /* Add ".." entry pointing to parent */
    EFS_DirEntry dotdot;
    memset(&dotdot, 0, sizeof(dotdot));
    dotdot.ino = parent_ino;
    dotdot.type = EFS_FILE_DIRECTORY;
    dotdot.name_len = 2;
    strcpy(dotdot.name, "..");

    efs_inode_write(&ctx->inodes[dir_ino]);

    /* Add entry to parent directory */
    return efs_dir_add_entry(parent_ino, name, dir_ino, EFS_FILE_DIRECTORY);
}

/* Remove directory (must be empty) */
EFS_Result efs_rmdir(const char *path) {
    uint32_t dir_ino;
    EFS_Result res = efs_path_exists(path, &dir_ino);
    if (res != EFS_OK) return res;

    /* Check if directory is empty (only . and ..) */
    EFS_Inode dir_inode;
    res = efs_inode_read(dir_ino, &dir_inode);
    if (res != EFS_OK) return res;

    if (dir_inode.block_count > 0) {
        return EFS_ERR_INVAL;  /* Not empty */
    }

    /* Remove entry from parent */
    uint32_t parent_ino = 0;
    char name[EFS_MAX_FILENAME];
    res = efs_get_parent(path, &parent_ino, name, sizeof(name));
    if (res != EFS_OK) return res;

    efs_dir_remove_entry(parent_ino, name);

    /* Mark inode as free */
    ctx->inodes[dir_ino].magic = 0;

    return EFS_OK;
}

/* Open directory */
int efs_opendir(const char *path) {
    uint32_t ino;
    EFS_Result res = efs_path_exists(path, &ino);
    if (res != EFS_OK) return -1;

    /* Check it's a directory */
    EFS_Inode info;
    res = efs_inode_read(ino, &info);
    if (res != EFS_OK || info.type != EFS_FILE_DIRECTORY) {
        return -1;
    }

    /* Allocate directory file descriptor */
    int fd = efs_file_table_find_free();
    if (fd < 0) return -1;

    EFS_FileDesc *fdesc = &ctx->file_table[fd];
    fdesc->fd = fd;
    fdesc->ino = ino;
    fdesc->flags = EFS_O_RDONLY;
    fdesc->offset = 0;  /* Current directory entry position */
    fdesc->size = info.size;
    fdesc->type = EFS_FILE_DIRECTORY;

    return fd;
}

/* Read directory entry */
EFS_Result efs_readdir(int dir_fd, EFS_DirEntry *entry) {
    EFS_FileDesc *fdesc = efs_file_table_get(dir_fd);
    if (!fdesc) return EFS_ERR_INVAL;

    EFS_Inode *dir_inode = &ctx->inodes[fdesc->ino];

    /* Read directory entries from block */
    if (dir_inode->block_count == 0) {
        return EFS_ERR_NOTFOUND;
    }

    /* Simple: read from first block */
    uint32_t block = dir_inode->blocks[0];
    if (block >= 256) return EFS_ERR_INVAL;

    EFS_DirEntry de;
    efs_flash_read(block, fdesc->offset, &de, sizeof(EFS_DirEntry));

    /* Check if entry is valid (non-zero inode) */
    if (de.ino == 0) return EFS_ERR_NOTFOUND;

    *entry = de;
    fdesc->offset += sizeof(EFS_DirEntry);

    return EFS_OK;
}

/* Close directory */
EFS_Result efs_closedir(int dir_fd) {
    return efs_close(dir_fd);
}

/* List directory contents */
EFS_Result efs_readdir_list(const char *path, EFS_DirEntry *entries, int max_entries) {
    int dir_fd = efs_opendir(path);
    if (dir_fd < 0) return EFS_ERR_INVAL;

    int count = 0;
    EFS_DirEntry entry;
    while (count < max_entries) {
        EFS_Result res = efs_readdir(dir_fd, &entry);
        if (res != EFS_OK) break;
        entries[count++] = entry;
    }

    efs_closedir(dir_fd);
    return count > 0 ? EFS_OK : EFS_ERR_NOTFOUND;
}

/* Find directory entry by name */
EFS_Result efs_dir_lookup(const char *path, uint32_t *found_ino) {
    /* Parse path components */
    char path_copy[256];
    strncpy(path_copy, path, sizeof(path_copy) - 1);
    path_copy[sizeof(path_copy) - 1] = '\0';

    /* Start from root */
    uint32_t current_ino = 0;  /* Root inode */

    /* Skip leading slashes */
    char *tok = path_copy;
    while (*tok == '/') tok++;

    /* Walk each component */
    char *saveptr;
    char *component = strtok_r(tok, "/", &saveptr);
    while (component) {
        /* Find component in current directory */
        EFS_Inode dir_inode;
        if (efs_inode_read(current_ino, &dir_inode) != EFS_OK) {
            return EFS_ERR_NOTFOUND;
        }

        if (dir_inode.type != EFS_FILE_DIRECTORY) {
            return EFS_ERR_INVAL;
        }

        /* Search entries */
        uint32_t found = 0;
        if (dir_inode.block_count > 0) {
            uint32_t block = dir_inode.blocks[0];
            EFS_DirEntry de;
            for (int i = 0; i < EFS_BLOCK_SIZE / sizeof(EFS_DirEntry); i++) {
                efs_flash_read(block, i * sizeof(EFS_DirEntry), &de, sizeof(EFS_DirEntry));
                if (de.ino == 0) break;
                if (strcmp(de.name, component) == 0) {
                    found = de.ino;
                    break;
                }
            }
        }

        if (found == 0) return EFS_ERR_NOTFOUND;
        current_ino = found;
        component = strtok_r(NULL, "/", &saveptr);
    }

    *found_ino = current_ino;
    return EFS_OK;
}

/* Get parent directory */
EFS_Result efs_get_parent(const char *path, uint32_t *parent_ino, char *name, int name_size) {
    char path_copy[256];
    strncpy(path_copy, path, sizeof(path_copy) - 1);
    path_copy[sizeof(path_copy) - 1] = '\0';

    /* Find last component */
    char *last_slash = strrchr(path_copy, '/');
    if (!last_slash || last_slash == path_copy) {
        /* No parent (root) */
        *parent_ino = 0;
        if (name && name_size > 0) {
            strncpy(name, path_copy, name_size - 1);
            name[name_size - 1] = '\0';
        }
        return EFS_OK;
    }

    *last_slash = '\0';
    if (name && name_size > 0) {
        strncpy(name, last_slash + 1, name_size - 1);
        name[name_size - 1] = '\0';
    }

    /* Resolve parent path */
    return efs_dir_lookup(path_copy, parent_ino);
}

/* Add entry to directory */
EFS_Result efs_dir_add_entry(uint32_t dir_ino, const char *name, uint32_t ino, uint8_t type) {
    EFS_Inode dir_inode;
    EFS_Result res = efs_inode_read(dir_ino, &dir_inode);
    if (res != EFS_OK) return res;

    /* Find free slot in directory */
    EFS_DirEntry entry;
    memset(&entry, 0, sizeof(entry));
    entry.ino = ino;
    entry.type = type;
    entry.name_len = strlen(name);
    strncpy(entry.name, name, EFS_MAX_FILENAME - 1);

    /* Write to directory block */
    if (dir_inode.block_count == 0) {
        /* Need to allocate a block for directory */
        uint32_t block = efs_block_allocate();
        if (block == 0xFFFFFFFF) return EFS_ERR_NOSPACE;
        efs_flash_erase(block);
        efs_block_set_state(block, EFS_BLOCK_USED);
        dir_inode.blocks[0] = block;
        dir_inode.block_count = 1;
        dir_inode.size = sizeof(EFS_DirEntry);
    }

    /* Find empty slot */
    for (int i = 0; i < EFS_BLOCK_SIZE / sizeof(EFS_DirEntry); i++) {
        EFS_DirEntry check;
        uint32_t block = dir_inode.blocks[0];
        efs_flash_read(block, i * sizeof(EFS_DirEntry), &check, sizeof(EFS_DirEntry));
        if (check.ino == 0) {
            /* Write entry */
            efs_flash_write(block, i * sizeof(EFS_DirEntry), &entry, sizeof(entry));
            dir_inode.size += sizeof(EFS_DirEntry);
            dir_inode.mtime = efs_get_context()->time_counter;
            efs_inode_write(&dir_inode);
            return EFS_OK;
        }
    }

    return EFS_ERR_NOSPACE;
}

/* Remove entry from directory */
EFS_Result efs_dir_remove_entry(uint32_t dir_ino, const char *name) {
    EFS_Inode dir_inode;
    EFS_Result res = efs_inode_read(dir_ino, &dir_inode);
    if (res != EFS_OK) return res;

    if (dir_inode.block_count == 0) return EFS_ERR_NOTFOUND;

    uint32_t block = dir_inode.blocks[0];
    for (int i = 0; i < EFS_BLOCK_SIZE / sizeof(EFS_DirEntry); i++) {
        EFS_DirEntry entry;
        efs_flash_read(block, i * sizeof(EFS_DirEntry), &entry, sizeof(EFS_DirEntry));
        if (entry.ino == 0) break;
        if (strcmp(entry.name, name) == 0) {
            /* Clear entry */
            memset(&entry, 0, sizeof(entry));
            efs_flash_write(block, i * sizeof(EFS_DirEntry), &entry, sizeof(entry));
            dir_inode.size -= sizeof(EFS_DirEntry);
            dir_inode.mtime = efs_get_context()->time_counter;
            efs_inode_write(&dir_inode);
            return EFS_OK;
        }
    }

    return EFS_ERR_NOTFOUND;
}

/* Check if path exists */
EFS_Result efs_path_exists(const char *path, uint32_t *ino) {
    return efs_dir_lookup(path, ino);
}

/* Resolve path to inode */
EFS_Result efs_resolve_path(const char *path, uint32_t *final_ino, uint32_t *parent_ino,
                              char *last_name, int name_size) {
    /* Get parent and last component */
    EFS_Result res = efs_get_parent(path, parent_ino, last_name, name_size);
    if (res != EFS_OK) return res;

    /* Look up in parent */
    return efs_dir_lookup(path, final_ino);
}
