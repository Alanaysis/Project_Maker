#ifndef MEMORY_H
#define MEMORY_H

#include "types.h"

// 内存大小定义
#define PAGE_SIZE        4096
#define PAGE_SHIFT       12
#define KERNEL_BASE      0x100000
#define KERNEL_STACK     0x90000
#define VIDEO_MEMORY     0xB8000

// 页目录/页表标志
#define PAGE_PRESENT     0x01
#define PAGE_WRITABLE    0x02
#define PAGE_USER        0x04
#define PAGE_ACCESSED    0x20
#define PAGE_DIRTY       0x40

// 页目录项
typedef struct {
    uint32_t present    : 1;
    uint32_t rw         : 1;
    uint32_t user       : 1;
    uint32_t pwt        : 1;
    uint32_t pcd        : 1;
    uint32_t accessed   : 1;
    uint32_t reserved   : 1;
    uint32_t page_size  : 1;
    uint32_t ignored    : 1;
    uint32_t available  : 3;
    uint32_t frame      : 20;
} __attribute__((packed)) page_directory_entry_t;

// 页表项
typedef struct {
    uint32_t present    : 1;
    uint32_t rw         : 1;
    uint32_t user       : 1;
    uint32_t pwt        : 1;
    uint32_t pcd        : 1;
    uint32_t accessed   : 1;
    uint32_t dirty      : 1;
    uint32_t pat        : 1;
    uint32_t global     : 1;
    uint32_t available  : 3;
    uint32_t frame      : 20;
} __attribute__((packed)) page_table_entry_t;

// 页目录
typedef struct {
    page_directory_entry_t entries[1024];
} __attribute__((aligned(PAGE_SIZE))) page_directory_t;

// 页表
typedef struct {
    page_table_entry_t entries[1024];
} __attribute__((aligned(PAGE_SIZE))) page_table_t;

// 内存块头部
typedef struct block_header {
    uint32_t size;
    uint8_t free;
    struct block_header *next;
    uint32_t magic;
} block_header_t;

// 内存管理函数
void mm_init(uint32_t total_memory);
uint32_t mm_alloc_page();
void mm_free_page(uint32_t page);
uint32_t mm_get_free_pages();
uint32_t mm_get_total_pages();

// 分页管理函数
void paging_init();
void page_map(uint32_t virtual, uint32_t physical, uint32_t flags);
void page_unmap(uint32_t virtual);
page_directory_t *paging_create_directory();
void paging_destroy_directory(page_directory_t *dir);
void paging_switch_directory(page_directory_t *dir);

// 内核堆函数
void heap_init();
void *kmalloc(uint32_t size);
void *kmalloc_aligned(uint32_t size);
void *kmalloc_physical(uint32_t size, uint32_t *physical);
void kfree(void *ptr);
void *krealloc(void *ptr, uint32_t size);

// 内存工具函数
void *memset(void *dest, int c, size_t n);
void *memcpy(void *dest, const void *src, size_t n);
void *memmove(void *dest, const void *src, size_t n);
int memcmp(const void *s1, const void *s2, size_t n);

#endif /* MEMORY_H */
