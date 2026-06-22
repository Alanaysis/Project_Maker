/**
 * 分页管理 (paging.c)
 * 功能: 管理虚拟内存的分页机制
 */

#include "../include/memory.h"
#include "../include/screen.h"

// 页目录
static page_directory_t *kernel_page_directory = NULL;

// 当前页目录
static page_directory_t *current_page_directory = NULL;

// 初始化分页
void paging_init() {
    // 分配内核页目录
    kernel_page_directory = (page_directory_t *)mm_alloc_page();
    if (!kernel_page_directory) {
        screen_puts("[PAGING] ERROR: Failed to allocate page directory!\n");
        return;
    }
    memset(kernel_page_directory, 0, PAGE_SIZE);

    // 映射内核空间 (前 4MB)
    // 使用一个页表映射前 1024 页
    page_table_t *kernel_table = (page_table_t *)mm_alloc_page();
    if (!kernel_table) {
        screen_puts("[PAGING] ERROR: Failed to allocate kernel page table!\n");
        return;
    }
    memset(kernel_table, 0, PAGE_SIZE);

    // 映射前 4MB 内存 (内核空间)
    for (uint32_t i = 0; i < 1024; i++) {
        kernel_table->entries[i].frame = i;
        kernel_table->entries[i].present = 1;
        kernel_table->entries[i].rw = 1;  // 可读写
        kernel_table->entries[i].user = 0; // 内核空间
    }

    // 设置页目录的第一个条目
    kernel_page_directory->entries[0].frame = (uint32_t)kernel_table >> 12;
    kernel_page_directory->entries[0].present = 1;
    kernel_page_directory->entries[0].rw = 1;
    kernel_page_directory->entries[0].user = 0;

    // 启用分页
    paging_switch_directory(kernel_page_directory);

    screen_puts("[PAGING] Paging initialized.\n");
}

// 切换页目录
void paging_switch_directory(page_directory_t *dir) {
    current_page_directory = dir;
    asm volatile("mov %0, %%cr3" : : "r"(dir));

    // 启用分页 (设置 CR0 的 PG 位)
    uint32_t cr0;
    asm volatile("mov %%cr0, %0" : "=r"(cr0));
    cr0 |= 0x80000000;  // 设置 PG 位
    asm volatile("mov %0, %%cr0" : : "r"(cr0));
}

// 映射虚拟地址到物理地址
void page_map(uint32_t virtual, uint32_t physical, uint32_t flags) {
    uint32_t page_dir_idx = virtual >> 22;         // 高 10 位
    uint32_t page_table_idx = (virtual >> 12) & 0x3FF;  // 中间 10 位

    // 获取或创建页表
    page_table_t *table = NULL;
    if (!current_page_directory->entries[page_dir_idx].present) {
        // 分配新页表
        table = (page_table_t *)mm_alloc_page();
        if (!table) {
            screen_puts("[PAGING] ERROR: Failed to allocate page table!\n");
            return;
        }
        memset(table, 0, PAGE_SIZE);

        // 设置页目录项
        current_page_directory->entries[page_dir_idx].frame = (uint32_t)table >> 12;
        current_page_directory->entries[page_dir_idx].present = 1;
        current_page_directory->entries[page_dir_idx].rw = 1;
        current_page_directory->entries[page_dir_idx].user = (flags & PAGE_USER) ? 1 : 0;
    } else {
        table = (page_table_t *)(current_page_directory->entries[page_dir_idx].frame << 12);
    }

    // 设置页表项
    table->entries[page_table_idx].frame = physical >> 12;
    table->entries[page_table_idx].present = 1;
    table->entries[page_table_idx].rw = (flags & PAGE_WRITABLE) ? 1 : 0;
    table->entries[page_table_idx].user = (flags & PAGE_USER) ? 1 : 0;

    // 刷新 TLB
    asm volatile("invlpg (%0)" : : "r"(virtual) : "memory");
}

// 取消虚拟地址映射
void page_unmap(uint32_t virtual) {
    uint32_t page_dir_idx = virtual >> 22;
    uint32_t page_table_idx = (virtual >> 12) & 0x3FF;

    if (!current_page_directory->entries[page_dir_idx].present) {
        return;  // 页目录项不存在
    }

    page_table_t *table = (page_table_t *)(current_page_directory->entries[page_dir_idx].frame << 12);
    table->entries[page_table_idx].present = 0;

    // 刷新 TLB
    asm volatile("invlpg (%0)" : : "r"(virtual) : "memory");
}

// 创建新的页目录
page_directory_t *paging_create_directory() {
    page_directory_t *dir = (page_directory_t *)mm_alloc_page();
    if (!dir) {
        return NULL;
    }
    memset(dir, 0, PAGE_SIZE);

    // 复制内核页表映射
    if (kernel_page_directory) {
        // 只复制第一个条目 (内核空间)
        dir->entries[0] = kernel_page_directory->entries[0];
    }

    return dir;
}

// 销毁页目录
void paging_destroy_directory(page_directory_t *dir) {
    if (!dir || dir == kernel_page_directory) {
        return;
    }

    // 释放用户空间页表
    for (int i = 1; i < 1024; i++) {
        if (dir->entries[i].present) {
            page_table_t *table = (page_table_t *)(dir->entries[i].frame << 12);
            mm_free_page((uint32_t)table);
        }
    }

    // 释放页目录本身
    mm_free_page((uint32_t)dir);
}

// 获取虚拟地址对应的物理地址
uint32_t paging_get_physical(uint32_t virtual) {
    uint32_t page_dir_idx = virtual >> 22;
    uint32_t page_table_idx = (virtual >> 12) & 0x3FF;
    uint32_t offset = virtual & 0xFFF;

    if (!current_page_directory->entries[page_dir_idx].present) {
        return 0;
    }

    page_table_t *table = (page_table_t *)(current_page_directory->entries[page_dir_idx].frame << 12);
    if (!table->entries[page_table_idx].present) {
        return 0;
    }

    return (table->entries[page_table_idx].frame << 12) + offset;
}

// 页面错误处理函数
void page_fault_handler(uint32_t error_code, uint32_t faulting_address) {
    screen_set_color(COLOR_LIGHT_RED, COLOR_BLACK);
    screen_puts("[PAGE FAULT] Error code: ");
    screen_put_hex(error_code);
    screen_puts("\n");
    screen_puts("[PAGE FAULT] Faulting address: ");
    screen_put_hex(faulting_address);
    screen_puts("\n");

    // 分析错误原因
    if (!(error_code & 0x01)) {
        screen_puts("[PAGE FAULT] Page not present.\n");
    }
    if (error_code & 0x02) {
        screen_puts("[PAGE FAULT] Write access.\n");
    } else {
        screen_puts("[PAGE FAULT] Read access.\n");
    }
    if (error_code & 0x04) {
        screen_puts("[PAGE FAULT] User mode.\n");
    } else {
        screen_puts("[PAGE FAULT] Kernel mode.\n");
    }

    screen_puts("[PAGE FAULT] System halted.\n");
    while (1) {
        asm volatile("hlt");
    }
}
