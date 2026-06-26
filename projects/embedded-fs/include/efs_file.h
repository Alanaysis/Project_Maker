#ifndef EFS_FILE_H
#define EFS_FILE_H

#include "efs_types.h"

/* ============================================================
 * File Operations Layer
 * 文件操作层
 *
 * Implements the POSIX-like file API for the embedded file system.
 * Supports open, close, read, write, seek, and stat operations.
 *
 * 为嵌入式文件系统实现类 POSIX 文件 API。
 * 支持 open、close、read、write、seek 和 stat 操作。
 * ============================================================ */

/*
 * Open a file.
 * 打开文件。
 *
 * Args:
 *   path: File path / 文件路径
 *   flags: Open flags (EFS_O_RDONLY, EFS_O_WRONLY, etc.) / 打开标志
 * Returns: File descriptor (>= 0) or negative error code / 文件描述符或负错误码
 */
int efs_open(const char *path, uint32_t flags);

/*
 * Close a file.
 * 关闭文件。
 */
EFS_Result efs_close(int fd);

/*
 * Read data from a file.
 * 从文件读取数据。
 *
 * Returns bytes read, or negative error code.
 * 返回读取字节数或负错误码。
 */
int efs_read(int fd, void *buf, uint32_t len);

/*
 * Write data to a file.
 * 向文件写入数据。
 *
 * Returns bytes written, or negative error code.
 * 返回写入字节数或负错误码。
 */
int efs_write(int fd, const void *buf, uint32_t len);

/*
 * Seek to a position in the file.
 * 在文件中定位。
 *
 * Args:
 *   fd: File descriptor / 文件描述符
 *   offset: Byte offset / 字节偏移
 *   whence: SEEK_SET, SEEK_CUR, SEEK_END / 基准位置
 * Returns: New position or negative error code / 新位置或负错误码
 */
int efs_seek(int fd, int32_t offset, int whence);

/*
 * Get file status (like stat()).
 * 获取文件状态。
 */
EFS_Result efs_stat(const char *path, EFS_Inode *info);

/*
 * Get file info from file descriptor (like fstat()).
 * 从文件描述符获取文件信息。
 */
EFS_Result efs_fstat(int fd, EFS_Inode *info);

/*
 * Truncate a file to a given size.
 * 将文件截断到指定大小。
 */
EFS_Result efs_truncate(const char *path, uint32_t new_size);

/*
 * Sync file data to flash.
 * 将文件数据同步到闪存。
 */
EFS_Result efs_sync(int fd);

/*
 * Find an empty slot in the file table.
 * 在文件表中查找空槽位。
 */
int efs_file_table_find_free(void);

/*
 * Get file descriptor by index.
 * 通过索引获取文件描述符。
 */
EFS_FileDesc *efs_file_table_get(int fd);

/*
 * Allocate a new inode.
 * 分配新的索引节点。
 */
uint32_t efs_inode_alloc(void);

/*
 * Get inode by number.
 * 通过编号获取索引节点。
 */
EFS_Inode *efs_inode_get(uint32_t ino);

/*
 * Write an inode to disk.
 * 将索引节点写入磁盘。
 */
EFS_Result efs_inode_write(EFS_Inode *inode);

/*
 * Read an inode from disk.
 * 从磁盘读取索引节点。
 */
EFS_Result efs_inode_read(uint32_t ino, EFS_Inode *inode);

#endif /* EFS_FILE_H */
