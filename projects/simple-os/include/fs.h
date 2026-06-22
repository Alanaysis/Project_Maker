#ifndef FS_H
#define FS_H

#include "types.h"

// 文件类型
typedef enum {
    FILE_TYPE_REGULAR,
    FILE_TYPE_DIRECTORY
} file_type_t;

// 文件权限
#define FILE_PERM_READ    0x04
#define FILE_PERM_WRITE   0x02
#define FILE_PERM_EXEC    0x01

// 最大文件名长度
#define MAX_FILENAME_LEN 64
#define MAX_OPEN_FILES   16

// 文件节点
typedef struct file_node {
    char name[MAX_FILENAME_LEN];
    file_type_t type;
    uint32_t size;
    uint32_t permissions;
    uint32_t created;
    uint32_t modified;
    uint8_t *data;
    struct file_node *parent;
    struct file_node *children;
    struct file_node *next;
} file_node_t;

// 文件描述符
typedef struct {
    file_node_t *file;
    uint32_t position;
    uint32_t flags;
    uint8_t in_use;
} file_descriptor_t;

// 文件系统函数
void fs_init();
int fs_open(const char *path, int flags);
int fs_close(int fd);
int fs_read(int fd, void *buf, size_t count);
int fs_write(int fd, const void *buf, size_t count);
int fs_create(const char *path, uint32_t permissions);
int fs_delete(const char *path);
int fs_mkdir(const char *path, uint32_t permissions);
int fs_rmdir(const char *path);

// 目录操作
file_node_t *fs_opendir(const char *path);
file_node_t *fs_readdir(file_node_t *dir);
void fs_closedir(file_node_t *dir);

// 文件信息
file_node_t *fs_stat(const char *path);
int fs_exists(const char *path);

#endif /* FS_H */
