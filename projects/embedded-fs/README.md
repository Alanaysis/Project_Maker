# Embedded File System / 嵌入式文件系统

A learning project implementing a log-structured embedded file system in C.

从零实现的日志式嵌入式文件系统学习项目。

---

## Overview / 项目概述

This project implements a minimal log-structured file system designed for embedded
systems with flash memory. It demonstrates key embedded file system concepts including:

本项目实现了一个最小化的日志式嵌入式文件系统，专为带闪存的嵌入式系统设计。
演示了关键嵌入式文件系统概念：

- **Log-structured design**: All writes go to the end of a sequential log
  - 日志式设计：所有写入都到顺序日志末尾
- **Wear leveling**: Distributes erase cycles to extend flash lifetime
  - 磨损均衡：均匀分布擦除周期以延长闪存寿命
- **Crash recovery**: Restores consistency after power loss
  - 崩溃恢复：断电后恢复一致性
- **Block management**: Allocates and tracks flash blocks
  - 块管理：分配和跟踪闪存块
- **Directory hierarchy**: Supports nested directories
  - 目录层次：支持嵌套目录

## Learning Objectives / 学习目标

### 1. Understand File System Principles / 理解文件系统原理
- Inode-based file metadata storage
- Block allocation strategies
- Directory entry encoding
- File system on-disk layout

### 2. Master Flash Memory Management / 掌握闪存管理
- Flash erase-before-write requirement
- Page-sized writes and reads
- Bad block handling
- Flash geometry and addressing

### 3. Learn Wear Leveling / 学会磨损均衡
- Simple count-based wear leveling
- Advanced wear leveling with garbage collection
- Wear distribution analysis
- Flash lifetime estimation

## Architecture / 架构

```
┌─────────────────────────────────────────────────────┐
│                 Application Layer                     │
│  open() close() read() write() seek() stat()         │
├─────────────────────────────────────────────────────┤
│                 File Operations Layer                 │
│  File table, inode management, path resolution       │
├─────────────────────────────────────────────────────┤
│              Directory Management Layer               │
│  mkdir() rmdir() opendir() readdir() lookup()       │
├─────────────────────────────────────────────────────┤
│              Block Allocation Layer                   │
│  Free list, wear tracking, block descriptors         │
├─────────────────────────────────────────────────────┤
│             Wear Leveling Layer                       │
│  Simple leveling, advanced leveling + GC            │
├─────────────────────────────────────────────────────┤
│             Log-Structured Writer                     │
│  Sequential log, checkpoints, compaction             │
├─────────────────────────────────────────────────────┤
│             Crash Recovery Layer                      │
│  Log replay, superblock validation, state restore   │
├─────────────────────────────────────────────────────┤
│             Flash Abstraction Layer                   │
│  Read/erase/erase, bad block detection               │
├─────────────────────────────────────────────────────┤
│               Physical Flash Memory                   │
│  256 blocks × 512 bytes (simulated)                 │
└─────────────────────────────────────────────────────┘
```

## Core Loop / 核心循环

```
File Operation → Block Management → Flash Write → Wear Leveling
     │                │                    │               │
     ▼                ▼                    ▼               ▼
  open/read     Allocate block     Sequential      Track wear
  write/seek    Update table       Log append      Trigger GC
  close/stat    Free blocks        Checkpoint      Rebalance
```

## Building / 构建

```bash
# Build everything
make all

# Build examples only
make examples

# Build tests only
make tests

# Run all tests
make test

# Clean
make clean
```

## Running Examples / 运行示例

### 1. Basic File Operations / 基本文件操作

```bash
make examples
./examples/basic_file_ops
```

Demonstrates:
- Creating and opening files
- Writing and reading data
- Seeking within files
- File truncation
- Binary data handling

### 2. Directory Management / 目录管理

```bash
./examples/dir_management
```

Demonstrates:
- Creating directories
- Nested directory paths
- File lookup in directories
- Reading directory contents

### 3. Wear Leveling Demo / 磨损均衡演示

```bash
./examples/wear_leveling_demo
```

Demonstrates:
- Wear distribution across blocks
- Simple wear leveling algorithm
- Advanced wear leveling with GC
- Flash lifetime impact

### 4. Crash Recovery Demo / 崩溃恢复演示

```bash
./examples/crash_recovery_demo
```

Demonstrates:
- Clean shutdown handling
- Unclean shutdown recovery
- Corrupted superblock detection
- Log replay for consistency

## File System Layout / 文件系统布局

```
Block 0:  SuperBlock (filesystem metadata)
Block 1:  Log start / Root directory
Block 2-255: Data blocks / Log area
```

### SuperBlock / 超级块
| Field | Offset | Description |
|-------|--------|-------------|
| magic | 0 | File system magic number (0x45465331) |
| version | 4 | File system version |
| block_size | 8 | Block size in bytes |
| total_blocks | 12 | Total flash blocks |
| log_head | 16 | Current log head block |
| log_tail | 20 | Current log tail block |
| free_blocks | 24 | Number of free blocks |
| root_dir_block | 28 | Root directory block |
| checksum | 32 | Superblock checksum |

### Inode / 索引节点
| Field | Offset | Description |
|-------|--------|-------------|
| magic | 0 | Inode magic (0x494E4F44) |
| ino | 4 | Inode number |
| type | 8 | File type (regular/directory) |
| size | 12 | File size in bytes |
| blocks[16] | 16 | Direct block pointers |
| parent_ino | 80 | Parent directory inode |
| atime | 84 | Access time |
| mtime | 88 | Modification time |
| checksum | 92 | Inode checksum |

## Key Concepts / 关键概念

### Log-Structured File System / 日志式文件系统

Instead of updating data in place (like traditional FS), all writes are
appended to a log. This ensures sequential writes to flash, which is
much faster and causes less wear than random writes.

传统文件系统原地更新数据，而日志式文件系统将所有写入追加到日志。
这确保了对闪存的顺序写入，比随机写入更快且磨损更小。

### Wear Leveling / 磨损均衡

Flash memory has limited erase cycles. Wear leveling distributes writes
evenly across all blocks:

闪存寿命有限。磨损均衡将写入均匀分布到所有块：

1. **Simple**: Track wear count, prefer least-worn blocks
   - 简单法：跟踪磨损计数，优先选择磨损最小的块
2. **Advanced**: Combine with garbage collection to reclaim space
   - 高级法：结合垃圾回收回收空间

### Crash Recovery / 崩溃恢复

Embedded systems crash frequently. Recovery ensures consistency:

嵌入式系统经常崩溃。恢复确保一致性：

1. Validate superblock checksum
2. Walk log from tail to head
3. Replay valid records
4. Restore to last checkpoint

## Directory Structure / 目录结构

```
embedded-fs/
├── Makefile              # Build system
├── README.md             # This file
├── include/              # Header files
│   ├── efs_types.h       # Core types and structures
│   ├── efs_flash.h       # Flash abstraction
│   ├── efs_block.h       # Block management
│   ├── efs_file.h        # File operations
│   ├── efs_dir.h         # Directory management
│   ├── efs_wear.h        # Wear leveling
│   ├── efs_log.h         # Log-structured design
│   └── efs_recovery.h    # Crash recovery
├── src/                  # Implementation
│   ├── flash_sim.c       # Simulated flash
│   ├── block_manager.c   # Block allocation
│   ├── file_ops.c        # File operations
│   ├── dir_ops.c         # Directory operations
│   ├── wear_leveling.c   # Wear leveling algorithms
│   ├── log_structured.c  # Log-structured writer
│   ├── crash_recovery.c  # Crash recovery
│   └── format.c          # Format and init
├── examples/             # Demo programs
│   ├── basic_file_ops.c  # Basic file operations
│   ├── dir_management.c  # Directory management
│   ├── wear_leveling_demo.c  # Wear leveling demo
│   └── crash_recovery_demo.c # Crash recovery demo
└── tests/                # Unit tests
    ├── test_file_ops.c   # File operation tests
    ├── test_dir_ops.c    # Directory tests
    ├── test_wear_leveling.c  # Wear leveling tests
    └── test_crash_recovery.c   # Recovery tests
```

## Technical Details / 技术细节

### Flash Abstraction / 闪存抽象

```c
typedef struct {
    EFS_Result (*init)(void);
    EFS_Result (*read)(uint32_t block, uint32_t offset, void *buf, uint32_t len);
    EFS_Result (*write)(uint32_t block, uint32_t offset, const void *buf, uint32_t len);
    EFS_Result (*erase)(uint32_t block);
    EFS_Result (*get_geometry)(EFS_FlashGeometry *geo);
    int        (*is_bad_block)(uint32_t block);
    EFS_Result (*mark_bad)(uint32_t block);
} EFS_FlashOps;
```

### File Operations API / 文件操作 API

```c
int      efs_open(const char *path, uint32_t flags);
EFS_Result efs_close(int fd);
int      efs_read(int fd, void *buf, uint32_t len);
int      efs_write(int fd, const void *buf, uint32_t len);
int      efs_seek(int fd, int32_t offset, int whence);
EFS_Result efs_stat(const char *path, EFS_Inode *info);
```

### Supported Open Flags / 支持的打开标志

| Flag | Value | Description |
|------|-------|-------------|
| EFS_O_RDONLY | 0x01 | Read-only |
| EFS_O_WRONLY | 0x02 | Write-only |
| EFS_O_RDWR | 0x04 | Read/write |
| EFS_O_CREAT | 0x08 | Create if not exists |
| EFS_O_TRUNC | 0x10 | Truncate existing |
| EFS_O_APPEND | 0x20 | Append mode |
| EFS_O_SYNC | 0x40 | Synchronous write |

## Real-World Comparisons / 现实对比

| Feature | This Project | LittleFS | FatFS | SPIFFS |
|---------|-------------|----------|-------|--------|
| Design | Log-structured | Log-structured | Cluster-based | Log-structured |
| Wear leveling | Simple + GC | Yes | No | No |
| Crash recovery | Yes | Yes | Limited | Limited |
| Compression | No | No | No | No |
| Symlinks | No | Yes | No | No |
| Target | Learning | Production | Production | Production |
| Dependencies | None | Minimal | Minimal | Minimal |

## Contributing / 参与贡献

This is a learning project. Feel free to:
- Add new features
- Improve wear leveling algorithms
- Add more test cases
- Port to real hardware

## License / 许可证

MIT License

## References / 参考

- "Log-Structured File Systems" - Dr. Ousterhout
- "Embedded File Systems" - Thomas F. Naughton
- LittleFS source code
- SPIFFS source code
- NAND flash datasheets
