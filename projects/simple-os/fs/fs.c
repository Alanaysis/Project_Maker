/**
 * 简单文件系统 (fs.c)
 * 功能: 实现基本的文件操作
 */

#include "../include/fs.h"
#include "../include/memory.h"
#include "../include/screen.h"

// 文件描述符表
static file_descriptor_t fd_table[MAX_OPEN_FILES];

// 根目录
static file_node_t *root_directory = NULL;

// 辅助函数: 复制字符串（带边界检查）
static void strcpy(char *dest, const char *src, size_t max_len) {
    if (max_len == 0) return;
    size_t i;
    for (i = 0; i < max_len - 1 && src[i] != '\0'; i++) {
        dest[i] = src[i];
    }
    dest[i] = '\0';
}

// 辅助函数: 字符串比较
static int strcmp(const char *s1, const char *s2) {
    while (*s1 && *s2) {
        if (*s1 != *s2) return *s1 - *s2;
        s1++;
        s2++;
    }
    return *s1 - *s2;
}

// 辅助函数: 字符串长度
static int strlen(const char *s) {
    int len = 0;
    while (*s++) len++;
    return len;
}

// 辅助函数: 查找文件
static file_node_t *find_file(file_node_t *dir, const char *name) {
    if (!dir || dir->type != FILE_TYPE_DIRECTORY) return NULL;

    file_node_t *child = dir->children;
    while (child) {
        if (strcmp(child->name, name) == 0) {
            return child;
        }
        child = child->next;
    }
    return NULL;
}

// 辅助函数: 获取父目录路径
static void get_parent_path(const char *path, char *parent_path) {
    int len = strlen(path);
    int last_slash = -1;

    for (int i = len - 1; i >= 0; i--) {
        if (path[i] == '/') {
            last_slash = i;
            break;
        }
    }

    if (last_slash <= 0) {
        strcpy(parent_path, "/", MAX_FILENAME_LEN);
    } else {
        for (int i = 0; i < last_slash; i++) {
            parent_path[i] = path[i];
        }
        parent_path[last_slash] = '\0';
    }
}

// 辅助函数: 获取文件名
static const char *get_filename(const char *path) {
    int len = strlen(path);
    int last_slash = -1;

    for (int i = len - 1; i >= 0; i--) {
        if (path[i] == '/') {
            last_slash = i;
            break;
        }
    }

    return path + last_slash + 1;
}

// 辅助函数: 查找目录
static file_node_t *find_directory(const char *path) {
    if (!path || path[0] != '/') return NULL;

    // 简化实现: 只支持一级目录
    if (path[1] == '\0') {
        return root_directory;
    }

    // 跳过开头的 '/'
    const char *name = path + 1;

    // 查找目录
    file_node_t *dir = root_directory->children;
    while (dir) {
        if (strcmp(dir->name, name) == 0 && dir->type == FILE_TYPE_DIRECTORY) {
            return dir;
        }
        dir = dir->next;
    }

    return NULL;
}

// 初始化文件系统
void fs_init() {
    // 清空文件描述符表
    memset(fd_table, 0, sizeof(fd_table));

    // 创建根目录
    root_directory = (file_node_t *)kmalloc(sizeof(file_node_t));
    if (!root_directory) {
        screen_puts("[FS] ERROR: Failed to create root directory!\n");
        return;
    }
    memset(root_directory, 0, sizeof(file_node_t));

    strcpy(root_directory->name, "/", MAX_FILENAME_LEN);
    root_directory->type = FILE_TYPE_DIRECTORY;
    root_directory->size = 0;
    root_directory->permissions = 0755;
    root_directory->parent = NULL;
    root_directory->children = NULL;
    root_directory->next = NULL;

    // 创建一些示例文件
    fs_create("/hello.txt", 0644);
    int fd = fs_open("/hello.txt", 0);
    fs_write(fd, "Hello, Simple OS!\n", 18);
    fs_close(fd);

    fs_create("/readme.txt", 0644);
    fd = fs_open("/readme.txt", 0);
    fs_write(fd, "This is a simple file system.\n", 30);
    fs_close(fd);

    screen_puts("[FS] File system initialized.\n");
}

// 打开文件
int fs_open(const char *path, int flags) {
    if (!path) return -ERROR_INVAL;

    // 查找空闲的文件描述符
    int fd = -1;
    for (int i = 0; i < MAX_OPEN_FILES; i++) {
        if (!fd_table[i].in_use) {
            fd = i;
            break;
        }
    }

    if (fd == -1) return -ERROR_NOMEM;

    // 查找文件
    file_node_t *file = find_file(root_directory, get_filename(path));
    if (!file) {
        // 如果文件不存在且设置了创建标志，则创建文件
        if (flags & 0x01) {  // O_CREATE
            int ret = fs_create(path, 0644);
            if (ret != SUCCESS) return ret;
            file = find_file(root_directory, get_filename(path));
        } else {
            return -ERROR_NOENT;
        }
    }

    // 设置文件描述符
    fd_table[fd].file = file;
    fd_table[fd].position = 0;
    fd_table[fd].flags = flags;
    fd_table[fd].in_use = 1;

    return fd;
}

// 关闭文件
int fs_close(int fd) {
    if (fd < 0 || fd >= MAX_OPEN_FILES) return -ERROR_INVAL;
    if (!fd_table[fd].in_use) return -ERROR_INVAL;

    fd_table[fd].in_use = 0;
    fd_table[fd].file = NULL;

    return SUCCESS;
}

// 读取文件
int fs_read(int fd, void *buf, size_t count) {
    if (fd < 0 || fd >= MAX_OPEN_FILES) return -ERROR_INVAL;
    if (!fd_table[fd].in_use || !fd_table[fd].file) return -ERROR_INVAL;

    file_node_t *file = fd_table[fd].file;
    if (file->type != FILE_TYPE_REGULAR) return -ERROR_INVAL;

    // 计算实际读取大小
    size_t available = file->size - fd_table[fd].position;
    size_t to_read = (count < available) ? count : available;

    // 复制数据
    if (file->data && to_read > 0) {
        memcpy(buf, file->data + fd_table[fd].position, to_read);
        fd_table[fd].position += to_read;
    }

    return to_read;
}

// 写入文件
int fs_write(int fd, const void *buf, size_t count) {
    if (fd < 0 || fd >= MAX_OPEN_FILES) return -ERROR_INVAL;
    if (!fd_table[fd].in_use || !fd_table[fd].file) return -ERROR_INVAL;

    file_node_t *file = fd_table[fd].file;
    if (file->type != FILE_TYPE_REGULAR) return -ERROR_INVAL;

    // 扩展文件大小
    uint32_t new_size = fd_table[fd].position + count;
    if (new_size > file->size) {
        // 重新分配内存
        uint8_t *new_data = (uint8_t *)kmalloc(new_size);
        if (!new_data) return -ERROR_NOMEM;

        // 复制旧数据
        if (file->data) {
            memcpy(new_data, file->data, file->size);
            kfree(file->data);
        }

        file->data = new_data;
        file->size = new_size;
    }

    // 写入数据
    memcpy(file->data + fd_table[fd].position, buf, count);
    fd_table[fd].position += count;

    return count;
}

// 创建文件
int fs_create(const char *path, uint32_t permissions) {
    if (!path) return -ERROR_INVAL;

    const char *filename = get_filename(path);
    if (!filename || strlen(filename) == 0) return -ERROR_INVAL;

    // 检查文件是否已存在
    if (find_file(root_directory, filename)) {
        return -ERROR_EXIST;
    }

    // 创建新文件节点
    file_node_t *file = (file_node_t *)kmalloc(sizeof(file_node_t));
    if (!file) return -ERROR_NOMEM;
    memset(file, 0, sizeof(file_node_t));

    strcpy(file->name, filename, MAX_FILENAME_LEN);
    file->type = FILE_TYPE_REGULAR;
    file->size = 0;
    file->permissions = permissions;
    file->data = NULL;
    file->parent = root_directory;
    file->children = NULL;

    // 添加到根目录
    file->next = root_directory->children;
    root_directory->children = file;

    return SUCCESS;
}

// 删除文件
int fs_delete(const char *path) {
    if (!path) return -ERROR_INVAL;

    const char *filename = get_filename(path);

    // 查找文件
    file_node_t *prev = NULL;
    file_node_t *current = root_directory->children;

    while (current) {
        if (strcmp(current->name, filename) == 0) {
            // 找到文件，从链表中移除
            if (prev) {
                prev->next = current->next;
            } else {
                root_directory->children = current->next;
            }

            // 释放资源
            if (current->data) {
                kfree(current->data);
            }
            kfree(current);

            return SUCCESS;
        }
        prev = current;
        current = current->next;
    }

    return -ERROR_NOENT;
}

// 创建目录
int fs_mkdir(const char *path, uint32_t permissions) {
    if (!path) return -ERROR_INVAL;

    const char *dirname = get_filename(path);
    if (!dirname || strlen(dirname) == 0) return -ERROR_INVAL;

    // 检查目录是否已存在
    if (find_file(root_directory, dirname)) {
        return -ERROR_EXIST;
    }

    // 创建新目录节点
    file_node_t *dir = (file_node_t *)kmalloc(sizeof(file_node_t));
    if (!dir) return -ERROR_NOMEM;
    memset(dir, 0, sizeof(file_node_t));

    strcpy(dir->name, dirname, MAX_FILENAME_LEN);
    dir->type = FILE_TYPE_DIRECTORY;
    dir->size = 0;
    dir->permissions = permissions;
    dir->data = NULL;
    dir->parent = root_directory;
    dir->children = NULL;

    // 添加到根目录
    dir->next = root_directory->children;
    root_directory->children = dir;

    return SUCCESS;
}

// 删除目录
int fs_rmdir(const char *path) {
    // 简化实现: 与删除文件相同
    return fs_delete(path);
}

// 获取文件信息
file_node_t *fs_stat(const char *path) {
    if (!path) return NULL;

    const char *filename = get_filename(path);
    return find_file(root_directory, filename);
}

// 检查文件是否存在
int fs_exists(const char *path) {
    return fs_stat(path) != NULL;
}
