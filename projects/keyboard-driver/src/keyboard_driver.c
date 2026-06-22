#include "../include/keyboard.h"
#include <stdio.h>
#include <string.h>
#include <time.h>

/* 获取当前时间戳（毫秒） */
static int32_t get_timestamp_ms(void)
{
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return (int32_t)(ts.tv_sec * 1000 + ts.tv_nsec / 1000000);
}

/* 初始化键盘设备 */
int keyboard_init(keyboard_dev_t *dev)
{
    if (dev == NULL) {
        return KB_ERR_INIT;
    }

    /* 清零矩阵状态 */
    memset(&dev->matrix, 0, sizeof(matrix_t));

    /* 清零事件队列 */
    memset(dev->event_queue, 0, sizeof(dev->event_queue));
    dev->queue_head = 0;
    dev->queue_tail = 0;

    /* 设置初始化标志 */
    dev->initialized = true;

    printf("[Keyboard] Device initialized successfully\n");
    printf("[Keyboard] Matrix size: %d x %d\n", MATRIX_ROWS, MATRIX_COLS);
    printf("[Keyboard] Debounce time: %d ms\n", DEBOUNCE_MS);

    return KB_OK;
}

/* 扫描键盘矩阵 */
int keyboard_scan(keyboard_dev_t *dev)
{
    if (dev == NULL || !dev->initialized) {
        return KB_ERR_SCAN;
    }

    /* 保存上一次状态 */
    memcpy(dev->matrix.prev_state, dev->matrix.state, sizeof(dev->matrix.state));

    /* 模拟矩阵扫描 */
    /* 在实际硬件中，这里会：
     * 1. 逐行输出低电平
     * 2. 读取列线状态
     * 3. 组合成完整的矩阵状态
     */

    /* 这里模拟一个按键按下事件 */
    /* 假设第2行第3列的按键被按下 */
    static int scan_count = 0;
    scan_count++;

    if (scan_count % 10 == 0) {
        /* 模拟按键按下 */
        dev->matrix.state[2][3] = 1;
    } else if (scan_count % 10 == 5) {
        /* 模拟按键释放 */
        dev->matrix.state[2][3] = 0;
    }

    return KB_OK;
}

/* 处理中断 */
int keyboard_interrupt_handler(keyboard_dev_t *dev)
{
    if (dev == NULL || !dev->initialized) {
        return KB_ERR_IRQ;
    }

    /* 扫描键盘矩阵 */
    int ret = keyboard_scan(dev);
    if (ret != KB_OK) {
        return ret;
    }

    /* 检测按键变化 */
    for (int row = 0; row < MATRIX_ROWS; row++) {
        for (int col = 0; col < MATRIX_COLS; col++) {
            bool current = dev->matrix.state[row][col];
            bool previous = dev->matrix.prev_state[row][col];

            /* 检测状态变化 */
            if (current != previous) {
                /* 进行去抖处理 */
                if (keyboard_debounce(dev, row, col)) {
                    /* 创建按键事件 */
                    key_event_t event;
                    event.row = row;
                    event.col = col;
                    event.keycode = keyboard_map_key(row, col);
                    event.state = current ? EV_KEY_PRESS : EV_KEY_RELEASE;
                    event.timestamp = get_timestamp_ms();

                    /* 报告事件 */
                    keyboard_report_event(dev, &event);
                }
            }
        }
    }

    return KB_OK;
}

/* 映射按键 */
uint8_t keyboard_map_key(uint8_t row, uint8_t col)
{
    /* 默认按键映射表 */
    /* 简化版本：根据行列计算键值 */
    static const uint8_t keymap[MATRIX_ROWS][MATRIX_COLS] = {
        /* 行0: ESC, F1-F12, DEL */
        {KEY_ESC, KEY_NONE, KEY_NONE, KEY_NONE, KEY_NONE, KEY_NONE, KEY_NONE, KEY_NONE, KEY_NONE, KEY_NONE, KEY_NONE, KEY_NONE, KEY_NONE, KEY_NONE},
        /* 行1: `, 1-9, 0, -, =, BACKSPACE */
        {KEY_NONE, KEY_1, KEY_2, KEY_3, KEY_4, KEY_5, KEY_6, KEY_7, KEY_8, KEY_9, KEY_0, KEY_NONE, KEY_NONE, KEY_BACKSPACE},
        /* 行2: TAB, Q-P, [, ], \ */
        {KEY_TAB, KEY_Q, KEY_W, KEY_E, KEY_R, KEY_T, KEY_Y, KEY_U, KEY_I, KEY_O, KEY_P, KEY_NONE, KEY_NONE, KEY_NONE},
        /* 行3: CAPS, A-L, ;, ', ENTER */
        {KEY_NONE, KEY_A, KEY_S, KEY_D, KEY_F, KEY_G, KEY_H, KEY_J, KEY_K, KEY_L, KEY_NONE, KEY_NONE, KEY_ENTER, KEY_NONE},
        /* 行4: SHIFT, Z-M, ,, ., /, SHIFT */
        {KEY_NONE, KEY_Z, KEY_X, KEY_C, KEY_V, KEY_B, KEY_N, KEY_M, KEY_NONE, KEY_NONE, KEY_NONE, KEY_NONE, KEY_NONE, KEY_NONE},
        /* 行5: CTRL, WIN, ALT, SPACE, ALT, FN, CTRL */
        {KEY_NONE, KEY_NONE, KEY_NONE, KEY_SPACE, KEY_NONE, KEY_NONE, KEY_NONE, KEY_NONE, KEY_NONE, KEY_NONE, KEY_NONE, KEY_NONE, KEY_NONE, KEY_NONE}
    };

    if (row >= MATRIX_ROWS || col >= MATRIX_COLS) {
        return KEY_NONE;
    }

    return keymap[row][col];
}

/* 去抖处理 */
bool keyboard_debounce(keyboard_dev_t *dev, uint8_t row, uint8_t col)
{
    if (dev == NULL || row >= MATRIX_ROWS || col >= MATRIX_COLS) {
        return false;
    }

    int32_t current_time = get_timestamp_ms();
    int32_t last_time = dev->matrix.debounce_time[row][col];

    /* 检查去抖时间（使用有符号整数避免回绕问题） */
    if ((current_time - last_time) < DEBOUNCE_MS) {
        /* 在去抖时间内，忽略变化 */
        return false;
    }

    /* 更新去抖时间 */
    dev->matrix.debounce_time[row][col] = current_time;

    return true;
}

/* 生成输入事件 */
int keyboard_report_event(keyboard_dev_t *dev, key_event_t *event)
{
    if (dev == NULL || event == NULL) {
        return KB_ERR_MAP;
    }

    /* 检查队列是否已满 */
    int next_tail = (dev->queue_tail + 1) % 64;
    if (next_tail == dev->queue_head) {
        printf("[Keyboard] Event queue full!\n");
        return KB_ERR_MAP;
    }

    /* 将事件加入队列 */
    dev->event_queue[dev->queue_tail] = *event;
    dev->queue_tail = next_tail;

    /* 打印事件信息 */
    const char *state_str = (event->state == EV_KEY_PRESS) ? "PRESS" : "RELEASE";
    printf("[Keyboard] Key %s: row=%d, col=%d, keycode=0x%02X\n",
           state_str, event->row, event->col, event->keycode);

    return KB_OK;
}

/* 获取按键事件 */
int keyboard_get_event(keyboard_dev_t *dev, key_event_t *event)
{
    if (dev == NULL || event == NULL) {
        return KB_ERR_INIT;
    }

    /* 检查队列是否为空 */
    if (dev->queue_head == dev->queue_tail) {
        return -1;  /* 队列为空 */
    }

    /* 从队列中取出事件 */
    *event = dev->event_queue[dev->queue_head];
    dev->queue_head = (dev->queue_head + 1) % 64;

    return KB_OK;
}

/* 清除事件队列 */
void keyboard_clear_events(keyboard_dev_t *dev)
{
    if (dev == NULL) {
        return;
    }

    dev->queue_head = 0;
    dev->queue_tail = 0;
}

/* 打印键盘状态 */
void keyboard_dump_state(const keyboard_dev_t *dev)
{
    if (dev == NULL) {
        return;
    }

    printf("\n[Keyboard] Current Matrix State:\n");
    printf("  ");
    for (int col = 0; col < MATRIX_COLS; col++) {
        printf("%2d ", col);
    }
    printf("\n");

    for (int row = 0; row < MATRIX_ROWS; row++) {
        printf("%2d ", row);
        for (int col = 0; col < MATRIX_COLS; col++) {
            printf(" %d ", dev->matrix.state[row][col]);
        }
        printf("\n");
    }
    printf("\n");
}
