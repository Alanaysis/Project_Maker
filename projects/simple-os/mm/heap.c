/**
 * 内核堆管理 (heap.c)
 * 功能: 实现内核堆内存分配
 */

#include "../include/memory.h"
#include "../include/screen.h"

// 堆起始地址和大小
#define HEAP_START 0x200000   // 2MB
#define HEAP_SIZE  0x100000   // 1MB

// 内存块魔数
#define BLOCK_MAGIC 0x12345678

// 堆管理结构
static block_header_t *heap_start = NULL;
static uint32_t heap_end = 0;

// 初始化堆
void heap_init() {
    // 映射堆内存
    for (uint32_t i = 0; i < HEAP_SIZE / PAGE_SIZE; i++) {
        uint32_t phys = mm_alloc_page();
        if (phys == 0) {
            screen_puts("[HEAP] ERROR: Failed to allocate heap pages!\n");
            return;
        }
        page_map(HEAP_START + i * PAGE_SIZE, phys, PAGE_WRITABLE);
    }

    // 初始化第一个块
    heap_start = (block_header_t *)HEAP_START;
    heap_start->size = HEAP_SIZE - sizeof(block_header_t);
    heap_start->free = 1;
    heap_start->next = NULL;
    heap_start->magic = BLOCK_MAGIC;

    heap_end = HEAP_START + HEAP_SIZE;

    screen_puts("[HEAP] Heap initialized at ");
    screen_put_hex(HEAP_START);
    screen_puts("\n");
}

// 分配内存
void *kmalloc(uint32_t size) {
    if (size == 0) return NULL;

    // 对齐大小到 8 字节
    size = (size + 7) & ~7;

    block_header_t *current = heap_start;

    // 首次适配算法
    while (current != NULL) {
        if (current->magic != BLOCK_MAGIC) {
            screen_puts("[HEAP] ERROR: Heap corruption detected!\n");
            return NULL;
        }

        if (current->free && current->size >= size) {
            // 如果块太大，分割它
            if (current->size > size + sizeof(block_header_t) + 8) {
                block_header_t *new_block = (block_header_t *)((uint32_t)current + sizeof(block_header_t) + size);
                new_block->size = current->size - size - sizeof(block_header_t);
                new_block->free = 1;
                new_block->next = current->next;
                new_block->magic = BLOCK_MAGIC;

                current->size = size;
                current->next = new_block;
            }

            current->free = 0;
            return (void *)((uint32_t)current + sizeof(block_header_t));
        }

        current = current->next;
    }

    // 没有足够空间
    screen_puts("[HEAP] ERROR: Out of heap memory!\n");
    return NULL;
}

// 分配对齐的内存
void *kmalloc_aligned(uint32_t size) {
    // 分配额外空间用于对齐
    void *ptr = kmalloc(size + PAGE_SIZE + sizeof(block_header_t));
    if (!ptr) return NULL;

    // 计算对齐后的地址
    uint32_t addr = (uint32_t)ptr;
    uint32_t aligned = (addr + PAGE_SIZE - 1) & ~(PAGE_SIZE - 1);

    // 如果需要调整，记录原始地址
    if (aligned != addr) {
        // 在对齐地址前存储原始地址
        *((uint32_t *)aligned - 1) = addr;
    }

    return (void *)aligned;
}

// 分配物理内存
void *kmalloc_physical(uint32_t size, uint32_t *physical) {
    void *ptr = kmalloc(size);
    if (!ptr) return NULL;

    *physical = paging_get_physical((uint32_t)ptr);
    return ptr;
}

// 释放内存
void kfree(void *ptr) {
    if (!ptr) return;

    block_header_t *header = (block_header_t *)((uint32_t)ptr - sizeof(block_header_t));

    if (header->magic != BLOCK_MAGIC) {
        screen_puts("[HEAP] ERROR: Invalid free!\n");
        return;
    }

    header->free = 1;

    // 合并相邻的空闲块
    block_header_t *current = heap_start;
    while (current != NULL && current->next != NULL) {
        if (current->free && current->next->free) {
            current->size += sizeof(block_header_t) + current->next->size;
            current->next = current->next->next;
        } else {
            current = current->next;
        }
    }
}

// 重新分配内存
void *krealloc(void *ptr, uint32_t size) {
    if (!ptr) return kmalloc(size);
    if (size == 0) {
        kfree(ptr);
        return NULL;
    }

    block_header_t *header = (block_header_t *)((uint32_t)ptr - sizeof(block_header_t));

    if (header->magic != BLOCK_MAGIC) {
        screen_puts("[HEAP] ERROR: Invalid realloc!\n");
        return NULL;
    }

    // 如果当前块足够大，直接返回
    if (header->size >= size) {
        return ptr;
    }

    // 分配新内存
    void *new_ptr = kmalloc(size);
    if (!new_ptr) return NULL;

    // 复制旧数据
    memcpy(new_ptr, ptr, header->size);

    // 释放旧内存
    kfree(ptr);

    return new_ptr;
}
