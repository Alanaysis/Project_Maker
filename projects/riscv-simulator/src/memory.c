#include "memory.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

/* ============================================================
 * 内存模型实现
 * ============================================================ */

Memory* memory_create(u32 size, u32 base_addr) {
    Memory* mem = (Memory*)malloc(sizeof(Memory));
    if (!mem) return NULL;

    mem->data = (u8*)calloc(size, 1);
    if (!mem->data) {
        free(mem);
        return NULL;
    }

    mem->size = size;
    mem->base_addr = base_addr;
    return mem;
}

void memory_destroy(Memory* mem) {
    if (mem) {
        free(mem->data);
        free(mem);
    }
}

/* 检查地址是否在范围内 */
static bool memory_in_range(Memory* mem, u32 addr) {
    return addr >= mem->base_addr && addr < mem->base_addr + mem->size;
}

/* 将外部地址转换为内部偏移 */
static u32 memory_offset(Memory* mem, u32 addr) {
    return addr - mem->base_addr;
}

SimError memory_load(Memory* mem, u32 addr, const u8* data, u32 len) {
    if (!mem || !data) return ERR_MEMORY_FAULT;
    if (!memory_in_range(mem, addr)) return ERR_MEMORY_FAULT;
    if (!memory_in_range(mem, addr + len - 1)) return ERR_MEMORY_FAULT;

    u32 offset = memory_offset(mem, addr);
    memcpy(mem->data + offset, data, len);
    return ERR_OK;
}

SimError memory_load_binary(Memory* mem, const char* filename, u32 load_addr) {
    if (!mem || !filename) return ERR_MEMORY_FAULT;

    FILE* f = fopen(filename, "rb");
    if (!f) {
        fprintf(stderr, "Error: cannot open file '%s'\n", filename);
        return ERR_MEMORY_FAULT;
    }

    /* 获取文件大小 */
    fseek(f, 0, SEEK_END);
    long file_size = ftell(f);
    fseek(f, 0, SEEK_SET);

    if (file_size <= 0) {
        fclose(f);
        return ERR_MEMORY_FAULT;
    }

    /* 检查是否超出内存范围 */
    if (!memory_in_range(mem, load_addr) ||
        !memory_in_range(mem, load_addr + (u32)file_size - 1)) {
        fclose(f);
        fprintf(stderr, "Error: binary too large for memory\n");
        return ERR_MEMORY_FAULT;
    }

    u32 offset = memory_offset(mem, load_addr);
    size_t read = fread(mem->data + offset, 1, (size_t)file_size, f);
    fclose(f);

    if (read != (size_t)file_size) {
        fprintf(stderr, "Error: short read (%zu / %ld)\n", read, file_size);
        return ERR_MEMORY_FAULT;
    }

    printf("Loaded %ld bytes at 0x%08X\n", file_size, load_addr);
    return ERR_OK;
}

/* ============================================================
 * 内存读写操作 (小端序)
 * ============================================================ */

SimError memory_read_byte(Memory* mem, u32 addr, u8* out) {
    if (!mem || !out) return ERR_MEMORY_FAULT;
    if (!memory_in_range(mem, addr)) return ERR_MEMORY_FAULT;

    u32 offset = memory_offset(mem, addr);
    *out = mem->data[offset];
    return ERR_OK;
}

SimError memory_read_half(Memory* mem, u32 addr, u16* out) {
    if (!mem || !out) return ERR_MEMORY_FAULT;
    if (addr % ALIGN_HALF != 0) return ERR_UNALIGNED_ACCESS;
    if (!memory_in_range(mem, addr) || !memory_in_range(mem, addr + 1))
        return ERR_MEMORY_FAULT;

    u32 offset = memory_offset(mem, addr);
    /* 小端序: 低字节在前 */
    *out = (u16)mem->data[offset] | ((u16)mem->data[offset + 1] << 8);
    return ERR_OK;
}

SimError memory_read_word(Memory* mem, u32 addr, u32* out) {
    if (!mem || !out) return ERR_MEMORY_FAULT;
    if (addr % ALIGN_WORD != 0) return ERR_UNALIGNED_ACCESS;
    if (!memory_in_range(mem, addr) || !memory_in_range(mem, addr + 3))
        return ERR_MEMORY_FAULT;

    u32 offset = memory_offset(mem, addr);
    /* 小端序 */
    *out = (u32)mem->data[offset]
         | ((u32)mem->data[offset + 1] << 8)
         | ((u32)mem->data[offset + 2] << 16)
         | ((u32)mem->data[offset + 3] << 24);
    return ERR_OK;
}

SimError memory_write_byte(Memory* mem, u32 addr, u8 val) {
    if (!mem) return ERR_MEMORY_FAULT;
    if (!memory_in_range(mem, addr)) return ERR_MEMORY_FAULT;

    u32 offset = memory_offset(mem, addr);
    mem->data[offset] = val;
    return ERR_OK;
}

SimError memory_write_half(Memory* mem, u32 addr, u16 val) {
    if (!mem) return ERR_MEMORY_FAULT;
    if (addr % ALIGN_HALF != 0) return ERR_UNALIGNED_ACCESS;
    if (!memory_in_range(mem, addr) || !memory_in_range(mem, addr + 1))
        return ERR_MEMORY_FAULT;

    u32 offset = memory_offset(mem, addr);
    mem->data[offset]     = (u8)(val & 0xFF);
    mem->data[offset + 1] = (u8)((val >> 8) & 0xFF);
    return ERR_OK;
}

SimError memory_write_word(Memory* mem, u32 addr, u32 val) {
    if (!mem) return ERR_MEMORY_FAULT;
    if (addr % ALIGN_WORD != 0) return ERR_UNALIGNED_ACCESS;
    if (!memory_in_range(mem, addr) || !memory_in_range(mem, addr + 3))
        return ERR_MEMORY_FAULT;

    u32 offset = memory_offset(mem, addr);
    mem->data[offset]     = (u8)(val & 0xFF);
    mem->data[offset + 1] = (u8)((val >> 8) & 0xFF);
    mem->data[offset + 2] = (u8)((val >> 16) & 0xFF);
    mem->data[offset + 3] = (u8)((val >> 24) & 0xFF);
    return ERR_OK;
}

void memory_dump(Memory* mem, u32 addr, u32 len) {
    if (!mem) return;

    printf("Memory dump from 0x%08X (%u bytes):\n", addr, len);
    for (u32 i = 0; i < len; i += 16) {
        printf("  0x%08X: ", addr + i);
        /* 十六进制 */
        for (u32 j = 0; j < 16 && (i + j) < len; j++) {
            u32 a = addr + i + j;
            if (memory_in_range(mem, a)) {
                u8 val = mem->data[memory_offset(mem, a)];
                printf("%02X ", val);
            } else {
                printf("?? ");
            }
            if (j == 7) printf(" ");
        }
        printf("\n");
    }
}
