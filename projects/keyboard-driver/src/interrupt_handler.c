#include "../include/keyboard.h"
#include <stdio.h>
#include <signal.h>
#include <time.h>

/* 中断配置 */
#define IRQ_NUMBER      1       /* 中断号 */
#define IRQ_PRIORITY    1       /* 中断优先级 */

/* 中断统计 */
static volatile int irq_count = 0;
static volatile int irq_errors = 0;

/* 中断处理函数 */
static void irq_handler(int signum)
{
    (void)signum;  /* 避免未使用参数警告 */
    irq_count++;
}

/* 初始化中断 */
int interrupt_init(void)
{
    printf("[IRQ] Initializing interrupt handler\n");
    printf("[IRQ] IRQ Number: %d\n", IRQ_NUMBER);
    printf("[IRQ] IRQ Priority: %d\n", IRQ_PRIORITY);

    /* 在实际硬件中，这里会：
     * 1. 配置GPIO中断
     * 2. 设置中断触发方式（上升沿/下降沿/双边沿）
     * 3. 注册中断处理函数
     * 4. 使能中断
     */

    /* 注册信号处理（用于模拟中断） */
    signal(SIGINT, irq_handler);

    printf("[IRQ] Interrupt handler registered\n");

    return KB_OK;
}

/* 中断服务程序 */
int interrupt_service_routine(keyboard_dev_t *dev)
{
    if (dev == NULL) {
        irq_errors++;
        return KB_ERR_IRQ;
    }

    /* 在中断上下文中，需要快速处理 */
    /* 1. 读取中断状态寄存器 */
    /* 2. 清除中断标志 */
    /* 3. 调用键盘扫描 */
    /* 4. 将事件放入队列 */

    int ret = keyboard_interrupt_handler(dev);
    if (ret != KB_OK) {
        irq_errors++;
        return ret;
    }

    return KB_OK;
}

/* 获取中断统计信息 */
void interrupt_get_stats(int *count, int *errors)
{
    if (count != NULL) {
        *count = irq_count;
    }
    if (errors != NULL) {
        *errors = irq_errors;
    }
}

/* 清除中断统计 */
void interrupt_clear_stats(void)
{
    irq_count = 0;
    irq_errors = 0;
}

/* 打印中断信息 */
void interrupt_dump_info(void)
{
    printf("\n[IRQ] Interrupt Statistics:\n");
    printf("  IRQ Count: %d\n", irq_count);
    printf("  IRQ Errors: %d\n", irq_errors);
    printf("\n");
}

/* 模拟中断触发 */
int interrupt_simulate_trigger(keyboard_dev_t *dev)
{
    if (dev == NULL) {
        return KB_ERR_IRQ;
    }

    printf("[IRQ] Simulating interrupt trigger\n");
    irq_count++;

    return interrupt_service_routine(dev);
}

/* 配置中断触发方式 */
int interrupt_configure_trigger(int trigger_type)
{
    /* 触发类型：
     * 0 - 上升沿触发
     * 1 - 下降沿触发
     * 2 - 双边沿触发
     * 3 - 高电平触发
     * 4 - 低电平触发
     */

    const char *trigger_names[] = {
        "Rising Edge",
        "Falling Edge",
        "Both Edges",
        "High Level",
        "Low Level"
    };

    if (trigger_type < 0 || trigger_type > 4) {
        printf("[IRQ] Invalid trigger type: %d\n", trigger_type);
        return KB_ERR_IRQ;
    }

    printf("[IRQ] Configured trigger: %s\n", trigger_names[trigger_type]);

    /* 在实际硬件中，这里会配置中断触发寄存器 */

    return KB_OK;
}

/* 使能/禁用中断 */
int interrupt_enable(bool enable)
{
    printf("[IRQ] Interrupt %s\n", enable ? "enabled" : "disabled");

    /* 在实际硬件中，这里会设置中断使能寄存器 */

    return KB_OK;
}
