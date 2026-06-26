#ifndef EFS_DIR_H
#define EFS_DIR_H

#include "efs_types.h"

/* ============================================================
 * Directory Management
 * 目录管理
 *
 * Implements directory structure and operations.
 * Directories are special files containing EFS_DirEntry records.
 *
 * 实现目录结构和操作。
 * 目录是包含 EFS_DirEntry 记录的特殊文件。
 * ============================================================ */

/*
 * Create a directory.
 * 创建目录。
 */
EFS_Result efs_mkdir(const char *path);

/*
 * Remove a directory (must be empty).
 * 删除目录（必须为空）。
 */
EFS_Result efs_rmdir(const char *path);

/*
 * Open a directory for reading entries.
 * 打开目录以读取条目。
 */
int efs_opendir(const char *path);

/*
 * Read next directory entry.
 * 读取下一个目录条目。
 */
EFS_Result efs_readdir(int dir_fd, EFS_DirEntry *entry);

/*
 * Close a directory.
 * 关闭目录。
 */
EFS_Result efs_closedir(int dir_fd);

/*
 * List directory contents.
 * 列出目录内容。
 */
EFS_Result efs_readdir_list(const char *path, EFS_DirEntry *entries, int max_entries);

/*
 * Find a directory entry by name.
 * 按名称查找目录条目。
 */
EFS_Result efs_dir_lookup(const char *path, uint32_t *found_ino);

/*
 * Get parent directory inode.
 * 获取父目录索引节点。
 */
EFS_Result efs_get_parent(const char *path, uint32_t *parent_ino, char *name, int name_size);

/*
 * Add entry to directory.
 * 向目录添加条目。
 */
EFS_Result efs_dir_add_entry(uint32_t dir_ino, const char *name, uint32_t ino, uint8_t type);

/*
 * Remove entry from directory.
 * 从目录删除条目。
 */
EFS_Result efs_dir_remove_entry(uint32_t dir_ino, const char *name);

/*
 * Check if path exists.
 * 检查路径是否存在。
 */
EFS_Result efs_path_exists(const char *path, uint32_t *ino);

/*
 * Resolve path to inode (with parent info).
 * 解析路径到索引节点（含父信息）。
 */
EFS_Result efs_resolve_path(const char *path, uint32_t *final_ino, uint32_t *parent_ino,
                              char *last_name, int name_size);

#endif /* EFS_DIR_H */
