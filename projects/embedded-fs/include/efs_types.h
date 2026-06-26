#ifndef EFS_TYPES_H
#define EFS_TYPES_H

#include <stdint.h>
#include <stddef.h>

/* ============================================================
 * Embedded File System (嵌入式文件系统)
 * Log-structured FS with wear leveling and crash recovery
 * ============================================================
 *
 * Architecture Overview / 架构概览:
 *
 *   File Operations (文件操作)
 *       |
 *       v
 *   [File Table] --> [Directory Tree]
 *       |
 *       v
 *   [Block Allocator] --> [Wear Leveling Layer]
 *       |
 *       v
 *   [Log-Structured Write] --> [Flash Abstraction]
 *       |
 *       v
 *   [Physical Flash Memory]
 *
 * Key Design Decisions / 关键设计决策:
 * 1. Log-structured: All writes go to end of log (sequential writes)
 * 2. Wear leveling: Simple count-based + advanced garbage collection
 * 3. Crash recovery: Write-ahead log + checksums
 * 4. No external dependencies: Pure C, works on bare metal
 */

/* ---- Constants / 常量定义 ---- */

#define EFS_MAGIC           0x45465331  /* "EFS1" */
#define EFS_VERSION         1
#define EFS_MAX_FILES       64
#define EFS_MAX_DIR_DEPTH   8
#define EFS_MAX_FILENAME    32
#define EFS_MAX_PATH        128
#define EFS_BLOCK_SIZE      512        /* Typical flash page size */
#define EFS_SUPERBLOCK_BLOCK 0
#define EFS_LOG_BLOCK_START 1
#define EFS_MAX_WEAR_ERR    16         /* Max wear level difference before rebalancing */

/* ---- Flash memory geometry / 闪存几何参数 ---- */

typedef struct {
    uint32_t total_blocks;      /* Total flash blocks / 总闪存块数 */
    uint32_t block_size;        /* Bytes per block / 每块字节数 */
    uint32_t erase_count;       /* Erase cycles per block / 每块擦除次数 */
    uint32_t bad_block_count;   /* Number of bad blocks / 坏块数量 */
} EFS_FlashGeometry;

/* ---- Block states / 块状态 ---- */

typedef enum {
    EFS_BLOCK_FREE = 0,         /* Block is free / 块空闲 */
    EFS_BLOCK_USED,             /* Block contains valid data / 块包含有效数据 */
    EFS_BLOCK_DIRTY,            /* Block has pending writes / 块有待写入数据 */
    EFS_BLOCK_BAD,              /* Block is bad / 块损坏 */
    EFS_BLOCK_LOG_HEAD,         /* Block is log head / 块是日志头 */
    EFS_BLOCK_LOG_TAIL          /* Block is log tail / 块是日志尾 */
} EFS_BlockState;

/* ---- File types / 文件类型 ---- */

typedef enum {
    EFS_FILE_REGULAR = 0,       /* Regular file / 普通文件 */
    EFS_FILE_DIRECTORY,         /* Directory / 目录 */
    EFS_FILE_SYMLINK            /* Symbolic link / 符号链接 */
} EFS_FileType;

/* ---- File flags / 文件标志 ---- */

typedef enum {
    EFS_O_RDONLY  = (1 << 0),   /* Open read-only / 只读打开 */
    EFS_O_WRONLY  = (1 << 1),   /* Open write-only / 只写打开 */
    EFS_O_RDWR    = (1 << 2),   /* Open read/write / 读写打开 */
    EFS_O_CREAT   = (1 << 3),   /* Create if not exists / 不存在则创建 */
    EFS_O_TRUNC   = (1 << 4),   /* Truncate existing / 截断已有文件 */
    EFS_O_APPEND  = (1 << 5),   /* Append mode / 追加模式 */
    EFS_O_SYNC    = (1 << 6)    /* Synchronous write / 同步写入 */
} EFS_OpenFlags;

/* ---- Return codes / 返回码 ---- */

typedef enum {
    EFS_OK          = 0,
    EFS_ERR_NOMEM   = -1,
    EFS_ERR_INVAL   = -2,
    EFS_ERR_IO      = -3,
    EFS_ERR_EXIST   = -4,
    EFS_ERR_NOTFOUND = -5,
    EFS_ERR_NOSPACE = -6,
    EFS_ERR_CORRUPT = -7,
    EFS_ERR_BADFS   = -8,
    EFS_ERR_BUSY    = -9
} EFS_Result;

/* ---- Checksum / 校验和 ---- */

#define EFS_CHECKSUM_SIZE 4

/* ---- Superblock / 超级块 ---- */

typedef struct {
    uint32_t magic;             /* EFS_MAGIC */
    uint32_t version;
    uint32_t block_size;
    uint32_t total_blocks;
    uint32_t log_head;          /* Current log head block / 当前日志头块 */
    uint32_t log_tail;          /* Current log tail block / 当前日志尾块 */
    uint32_t free_blocks;       /* Number of free blocks / 空闲块数 */
    uint32_t total_writes;      /* Total write operations / 总写入次数 */
    uint32_t total_erases;      /* Total erase operations / 总擦除次数 */
    uint32_t root_dir_block;    /* Root directory block / 根目录块 */
    uint32_t checksum;          /* Superblock checksum / 超级块校验和 */
    uint8_t  reserved[196];     /* Padding to fill block / 填充 */
} EFS_SuperBlock;

/* ---- Block descriptor / 块描述符 ---- */

typedef struct {
    uint32_t block_id;          /* Physical block ID / 物理块ID */
    uint32_t next_block;        /* Next block in chain / 链中下一个块 */
    uint32_t prev_block;        /* Previous block in chain / 链中上一个块 */
    uint32_t wear_count;        /* Erase count for wear leveling / 磨损计数 */
    uint8_t  state;             /* EFS_BlockState / 块状态 */
    uint8_t  reserved[3];
    uint32_t checksum;          /* Block header checksum / 块头校验和 */
} EFS_BlockDesc;

/* ---- File descriptor / 文件描述符 ---- */

typedef struct {
    int      fd;                /* File descriptor index / 文件描述符索引 */
    uint32_t ino;              /* Inode number / 索引节点号 */
    uint32_t flags;            /* EFS_OpenFlags / 打开标志 */
    uint32_t offset;           /* Current file offset / 当前文件偏移 */
    uint32_t size;             /* File size in bytes / 文件大小 */
    uint32_t block_count;      /* Number of data blocks / 数据块数 */
    uint32_t *blocks;          /* Block chain / 块链 */
    uint8_t  type;             /* EFS_FileType / 文件类型 */
    uint8_t  reserved[3];
    uint32_t atime;            /* Last access time / 最后访问时间 */
    uint32_t mtime;            /* Last modification time / 最后修改时间 */
} EFS_FileDesc;

/* ---- File metadata (on-disk) / 文件元数据（磁盘上） ---- */

typedef struct {
    uint32_t magic;             /* EFS_INODE_MAGIC */
    uint32_t ino;              /* Inode number / 索引节点号 */
    uint32_t type;             /* EFS_FileType / 文件类型 */
    uint32_t size;             /* File size / 文件大小 */
    uint32_t block_count;      /* Number of blocks / 块数 */
    uint32_t blocks[16];       /* Direct block pointers / 直接块指针 */
    uint32_t parent_ino;       /* Parent directory inode / 父目录索引节点 */
    uint32_t atime;            /* Access time / 访问时间 */
    uint32_t mtime;            /* Modification time / 修改时间 */
    uint32_t checksum;         /* Inode checksum / 索引节点校验和 */
    uint8_t  reserved[188];
} EFS_Inode;

#define EFS_INODE_MAGIC 0x494E4F44  /* "INOD" */

/* ---- Directory entry / 目录项 ---- */

typedef struct {
    uint32_t ino;              /* Inode number / 索引节点号 */
    uint8_t  type;             /* File type / 文件类型 */
    uint8_t  name_len;         /* Name length / 名称长度 */
    uint8_t  reserved[2];
    char     name[EFS_MAX_FILENAME];  /* Entry name / 条目名称 */
} EFS_DirEntry;

/* ---- Wear leveling stats / 磨损均衡统计 ---- */

typedef struct {
    uint32_t total_writes;
    uint32_t total_erases;
    uint32_t blocks_erased;
    uint32_t worst_block_wear;
    uint32_t best_block_wear;
    uint32_t avg_wear;
    uint32_t wear_leveling_count;
    uint32_t gc_count;
} EFS_WearStats;

/* ---- Flash operations interface / 闪存操作接口 ---- */

/*
 * These functions are platform-specific.
 * Implement them for your target hardware.
 * 这些函数是平台特定的，需要为目标硬件实现。
 */

typedef struct {
    EFS_Result (*init)(void);
    EFS_Result (*read)(uint32_t block, uint32_t offset, void *buf, uint32_t len);
    EFS_Result (*write)(uint32_t block, uint32_t offset, const void *buf, uint32_t len);
    EFS_Result (*erase)(uint32_t block);
    EFS_Result (*get_geometry)(EFS_FlashGeometry *geo);
    int        (*is_bad_block)(uint32_t block);
    EFS_Result (*mark_bad)(uint32_t block);
} EFS_FlashOps;

/* ---- File system context / 文件系统上下文 ---- */

typedef struct {
    EFS_SuperBlock superblock;
    EFS_BlockDesc  block_table[256];  /* Block descriptor table / 块描述符表 */
    EFS_Inode      inodes[EFS_MAX_FILES];
    EFS_FileDesc   file_table[EFS_MAX_FILES];
    EFS_FlashOps  *flash_ops;
    int            initialized;
    uint32_t       next_ino;
    uint32_t       time_counter;      /* Simple time counter / 简单时间计数器 */
    EFS_WearStats  wear_stats;
    uint32_t       log_head;          /* Current log head block / 当前日志头块 */
    uint32_t       log_tail;          /* Current log tail block / 当前日志尾块 */
} EFS_Context;

#endif /* EFS_TYPES_H */
