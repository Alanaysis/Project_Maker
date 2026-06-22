/**
 * 物理内存管理 (memory.c)
 * 功能: 管理物理内存的分配和释放
 */

#include "../include/memory.h"
#include "../include/screen.h"

// 内存位图
#define MAX_PAGES (1024 * 1024 / 4)  // 最大支持 4GB 内存
static uint8_t memory_bitmap[MAX_PAGES / 8];
static uint32_t total_pages = 0;
static uint32_t used_pages = 0;
static uint32_t memory_size = 0;

// 内核结束地址 (由链接器提供)
extern uint32_t _end;

// 内存管理初始化
void mm_init(uint32_t total_memory) {
    memory_size = total_memory;
    total_pages = total_memory / PAGE_SIZE;
    used_pages = 0;

    // 清空位图
    memset(memory_bitmap, 0, sizeof(memory_bitmap));

    // 标记内核使用的内存为已使用
    uint32_t kernel_end = (uint32_t)&_end;
    uint32_t kernel_pages = (kernel_end - KERNEL_BASE) / PAGE_SIZE + 1;

    for (uint32_t i = 0; i < kernel_pages; i++) {
        mm_mark_page_used(i);
    }

    // 标记前 1MB 内存为已使用 (BIOS, 显示内存等)
    for (uint32_t i = 0; i < 256; i++) {  // 1MB = 256 页
        mm_mark_page_used(i);
    }

    screen_puts("[MM] Memory manager initialized.\n");
    screen_puts("[MM] Total memory: ");
    screen_put_int(total_memory / 1024 / 1024);
    screen_puts(" MB\n");
    screen_puts("[MM] Total pages: ");
    screen_put_int(total_pages);
    screen_puts("\n");
    screen_puts("[MM] Used pages: ");
    screen_put_int(used_pages);
    screen_puts("\n");
}

// 标记页面为已使用
void mm_mark_page_used(uint32_t page) {
    uint32_t byte_idx = page / 8;
    uint32_t bit_idx = page % 8;

    if (!(memory_bitmap[byte_idx] & (1 << bit_idx))) {
        memory_bitmap[byte_idx] |= (1 << bit_idx);
        used_pages++;
    }
}

// 标记页面为空闲
void mm_mark_page_free(uint32_t page) {
    uint32_t byte_idx = page / 8;
    uint32_t bit_idx = page % 8;

    if (memory_bitmap[byte_idx] & (1 << bit_idx)) {
        memory_bitmap[byte_idx] &= ~(1 << bit_idx);
        used_pages--;
    }
}

// 检查页面是否已使用
uint8_t mm_is_page_used(uint32_t page) {
    uint32_t byte_idx = page / 8;
    uint32_t bit_idx = page % 8;

    return (memory_bitmap[byte_idx] >> bit_idx) & 1;
}

// 分配一个物理页
uint32_t mm_alloc_page() {
    for (uint32_t i = 0; i < total_pages; i++) {
        if (!mm_is_page_used(i)) {
            mm_mark_page_used(i);
            return i * PAGE_SIZE;
        }
    }

    // 内存不足
    screen_puts("[MM] ERROR: Out of memory!\n");
    return 0;
}

// 释放一个物理页
void mm_free_page(uint32_t page) {
    if (page == 0) return;

    uint32_t page_num = page / PAGE_SIZE;
    if (page_num < total_pages) {
        mm_mark_page_free(page_num);
    }
}

// 获取空闲页面数
uint32_t mm_get_free_pages() {
    return total_pages - used_pages;
}

// 获取总页面数
uint32_t mm_get_total_pages() {
    return total_pages;
}

// 内存工具函数: memset
void *memset(void *dest, int c, size_t n) {
    uint8_t *d = (uint8_t *)dest;
    for (size_t i = 0; i < n; i++) {
        d[i] = (uint8_t)c;
    }
    return dest;
}

// 内存工具函数: memcpy
void *memcpy(void *dest, const void *src, size_t n) {
    uint8_t *d = (uint8_t *)dest;
    const uint8_t *s = (const uint8_t *)src;
    for (size_t i = 0; i < n; i++) {
        d[i] = s[i];
    }
    return dest;
}

// 内存工具函数: memmove
void *memmove(void *dest, const void *src, size_t n) {
    uint8_t *d = (uint8_t *)dest;
    const uint8_t *s = (const uint8_t *)src;

    if (d < s) {
        for (size_t i = 0; i < n; i++) {
            d[i] = s[i];
        }
    } else if (d > s) {
        for (size_t i = n; i > 0; i--) {
            d[i-1] = s[i-1];
        }
    }
    return dest;
}

// 内存工具函数: memcmp
int memcmp(const void *s1, const void *s2, size_t n) {
    const uint8_t *p1 = (const uint8_t *)s1;
    const uint8_t *p2 = (const uint8_t *)s2;

    for (size_t i = 0; i < n; i++) {
        if (p1[i] != p2[i]) {
            return p1[i] - p2[i];
        }
    }
    return 0;
}
