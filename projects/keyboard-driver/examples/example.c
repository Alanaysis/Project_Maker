#include "../include/keyboard.h"
#include <stdio.h>
#include <unistd.h>

/* 事件处理器示例 */
void my_event_handler(const key_event_t *event)
{
    if (event == NULL) {
        return;
    }

    const char *state_str = (event->state == EV_KEY_PRESS) ? "Pressed" : "Released";
    printf("[Handler] Key %s: 0x%02X (row=%d, col=%d)\n",
           state_str, event->keycode, event->row, event->col);
}

/* 基本使用示例 */
void example_basic_usage(void)
{
    printf("\n=== Basic Usage Example ===\n\n");

    /* 1. 初始化键盘设备 */
    keyboard_dev_t kb_dev;
    keyboard_init(&kb_dev);

    /* 2. 初始化输入事件系统 */
    input_event_init();

    /* 3. 注册事件处理器 */
    input_event_register_handler(my_event_handler);

    /* 4. 模拟中断处理 */
    printf("\nSimulating keyboard interrupts...\n");
    for (int i = 0; i < 5; i++) {
        keyboard_interrupt_handler(&kb_dev);
        usleep(100000);  /* 100ms */
    }

    /* 5. 打印键盘状态 */
    keyboard_dump_state(&kb_dev);

    /* 6. 获取事件 */
    key_event_t event;
    while (keyboard_get_event(&kb_dev, &event) == KB_OK) {
        printf("Event: keycode=0x%02X, state=%d\n", event.keycode, event.state);
    }
}

/* 去抖算法示例 */
void example_debounce(void)
{
    printf("\n=== Debounce Algorithm Example ===\n\n");

    /* 初始化去抖器 */
    debounce_init(DEBOUNCE_TYPE_STATE_MACHINE, 5);

    /* 模拟按键抖动 */
    printf("Simulating key bounce...\n");

    uint32_t time = 0;
    bool pressed = false;

    /* 模拟抖动序列 */
    for (int i = 0; i < 20; i++) {
        /* 模拟抖动：快速切换状态 */
        pressed = (i % 3 != 0);  /* 每3次有一次释放 */

        bool changed = debounce_process(2, 3, pressed, time);
        if (changed) {
            printf("Time %3u: Key state changed to %s\n",
                   time, pressed ? "PRESSED" : "RELEASED");
        }

        time += 2;  /* 每2ms一次扫描 */
    }

    /* 打印去抖状态 */
    debounce_dump_state();
}

/* 矩阵扫描示例 */
void example_matrix_scan(void)
{
    printf("\n=== Matrix Scan Example ===\n\n");

    matrix_t matrix;
    memset(&matrix, 0, sizeof(matrix_t));

    /* 执行完整扫描 */
    printf("Performing full matrix scan...\n");
    matrix_scan_full(&matrix);

    /* 打印扫描结果 */
    matrix_dump(&matrix);

    /* 检测变化 */
    key_event_t events[10];
    int count = matrix_detect_changes(&matrix, events, 10);

    printf("Detected %d key changes:\n", count);
    for (int i = 0; i < count; i++) {
        printf("  [%d] row=%d, col=%d, state=%s\n",
               i, events[i].row, events[i].col,
               events[i].state == EV_KEY_PRESS ? "PRESS" : "RELEASE");
    }
}

/* 中断处理示例 */
void example_interrupt(void)
{
    printf("\n=== Interrupt Handling Example ===\n\n");

    /* 初始化中断 */
    interrupt_init();

    /* 配置中断触发方式 */
    interrupt_configure_trigger(2);  /* 双边沿触发 */

    /* 使能中断 */
    interrupt_enable(true);

    /* 初始化键盘设备 */
    keyboard_dev_t kb_dev;
    keyboard_init(&kb_dev);

    /* 模拟多次中断 */
    printf("\nSimulating multiple interrupts...\n");
    for (int i = 0; i < 10; i++) {
        interrupt_simulate_trigger(&kb_dev);
        usleep(50000);  /* 50ms */
    }

    /* 打印中断统计 */
    interrupt_dump_info();
}

/* 完整工作流程示例 */
void example_full_workflow(void)
{
    printf("\n=== Full Workflow Example ===\n\n");
    printf("Keyboard Driver Complete Workflow:\n");
    printf("  1. Initialize hardware\n");
    printf("  2. Configure interrupts\n");
    printf("  3. Scan keyboard matrix\n");
    printf("  4. Handle debouncing\n");
    printf("  5. Map keys\n");
    printf("  6. Generate input events\n");
    printf("  7. Report to application\n\n");

    /* 初始化所有组件 */
    keyboard_dev_t kb_dev;
    keyboard_init(&kb_dev);

    input_event_init();
    input_event_register_handler(my_event_handler);

    debounce_init(DEBOUNCE_TYPE_STATE_MACHINE, 5);

    /* 模拟完整工作流程 */
    printf("Running complete workflow...\n\n");

    for (int cycle = 0; cycle < 3; cycle++) {
        printf("--- Cycle %d ---\n", cycle + 1);

        /* 1. 中断触发 */
        keyboard_interrupt_handler(&kb_dev);

        /* 2. 扫描矩阵 */
        matrix_t matrix;
        matrix_scan_full(&matrix);

        /* 3. 检测变化 */
        key_event_t events[5];
        int count = matrix_detect_changes(&matrix, events, 5);

        /* 4. 处理每个事件 */
        for (int i = 0; i < count; i++) {
            /* 5. 去抖处理 */
            bool stable = debounce_process(events[i].row, events[i].col,
                                          events[i].state == EV_KEY_PRESS, cycle * 100);

            if (stable) {
                /* 6. 映射按键 */
                events[i].keycode = keyboard_map_key(events[i].row, events[i].col);

                /* 7. 报告事件 */
                keyboard_report_event(&kb_dev, &events[i]);
                input_event_report(&events[i]);
            }
        }

        usleep(100000);  /* 100ms */
    }

    /* 打印最终状态 */
    printf("\nFinal Status:\n");
    keyboard_dump_state(&kb_dev);
    input_event_dump_status();
}

/* 主函数 */
int main(void)
{
    printf("========================================\n");
    printf("Keyboard Driver Examples\n");
    printf("========================================\n");

    /* 运行各个示例 */
    example_basic_usage();
    example_debounce();
    example_matrix_scan();
    example_interrupt();
    example_full_workflow();

    printf("\n========================================\n");
    printf("All examples completed!\n");
    printf("========================================\n\n");

    return 0;
}
