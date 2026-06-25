#ifndef MEMORY_H
#define MEMORY_H

#include "riscv.h"

/* ============================================================
 * 内存模型
 *
 * RISC-V 采用统一的字节寻址内存模型
 * 支持小端序 (Little-Endian)
 * ============================================================ */

/* 内存默认大小 */
#define DEFAULT_MEM_SIZE  (1024 * 1024)  /* 1 MB */

/* 内存基地址 */
#define DEFAULT_MEM_BASE  0x80000000     /* 与 QEMU virt 机器一致 */

/* 内存对齐要求 */
#define ALIGN_BYTE  1
#define ALIGN_HALF  2
#define ALIGN_WORD  4

/* 内存结构 */
typedef struct {
    u8*  data;       /* 内存数据 */
    u32  size;       /* 内存大小 (字节) */
    u32  base_addr;  /* 基地址 */
} Memory;

/* ============================================================
 * 内存操作 API
 * ============================================================ */

/* 创建内存 */
Memory* memory_create(u32 size, u32 base_addr);

/* 销毁内存 */
void memory_destroy(Memory* mem);

/* 加载数据到内存 */
SimError memory_load(Memory* mem, u32 addr, const u8* data, u32 len);

/* 加载 ELF 二进制到内存 */
SimError memory_load_binary(Memory* mem, const char* filename, u32 load_addr);

/* 读取字节 */
SimError memory_read_byte(Memory* mem, u32 addr, u8* out);

/* 读取半字 (16 位) */
SimError memory_read_half(Memory* mem, u32 addr, u16* out);

/* 读取字 (32 位) */
SimError memory_read_word(Memory* mem, u32 addr, u32* out);

/* 写入字节 */
SimError memory_write_byte(Memory* mem, u32 addr, u8 val);

/* 写入半字 (16 位) */
SimError memory_write_half(Memory* mem, u32 addr, u16 val);

/* 写入字 (32 位) */
SimError memory_write_word(Memory* mem, u32 addr, u32 val);

/* 打印内存内容 (调试用) */
void memory_dump(Memory* mem, u32 addr, u32 len);

#endif /* MEMORY_H */
