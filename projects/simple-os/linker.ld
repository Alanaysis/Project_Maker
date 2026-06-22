/* Simple OS 链接脚本 */
/* 功能: 定义内核的内存布局 */

ENTRY(_start)

SECTIONS
{
    /* 内核加载地址: 1MB */
    . = 0x100000;

    /* 代码段 */
    .text : {
        *(.text)
        *(.text.*)
    }

    /* 只读数据段 */
    .rodata : {
        *(.rodata)
        *(.rodata.*)
    }

    /* 数据段 */
    .data : {
        *(.data)
        *(.data.*)
    }

    /* BSS 段 */
    .bss : {
        *(.bss)
        *(.bss.*)
        *(COMMON)
    }

    /* 内核结束地址 */
    _end = .;
}
