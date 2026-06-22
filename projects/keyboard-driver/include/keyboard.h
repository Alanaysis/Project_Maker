#ifndef KEYBOARD_H
#define KEYBOARD_H

#include <stdint.h>
#include <stdbool.h>

/* 键盘矩阵配置 */
#define MATRIX_ROWS     6       /* 矩阵行数 */
#define MATRIX_COLS     14      /* 矩阵列数 */
#define MAX_KEYS        (MATRIX_ROWS * MATRIX_COLS)

/* 去抖配置 */
#define DEBOUNCE_MS     5       /* 去抖时间（毫秒） */
#define DEBOUNCE_CYCLES 3       /* 去抖周期数 */

/* 键值定义 */
#define KEY_NONE        0x00
#define KEY_A           0x04
#define KEY_B           0x05
#define KEY_C           0x06
#define KEY_D           0x07
#define KEY_E           0x08
#define KEY_F           0x09
#define KEY_G           0x0A
#define KEY_H           0x0B
#define KEY_I           0x0C
#define KEY_J           0x0D
#define KEY_K           0x0E
#define KEY_L           0x0F
#define KEY_M           0x10
#define KEY_N           0x11
#define KEY_O           0x12
#define KEY_P           0x13
#define KEY_Q           0x14
#define KEY_R           0x15
#define KEY_S           0x16
#define KEY_T           0x17
#define KEY_U           0x18
#define KEY_V           0x19
#define KEY_W           0x1A
#define KEY_X           0x1B
#define KEY_Y           0x1C
#define KEY_Z           0x1D
#define KEY_1           0x1E
#define KEY_2           0x1F
#define KEY_3           0x20
#define KEY_4           0x21
#define KEY_5           0x22
#define KEY_6           0x23
#define KEY_7           0x24
#define KEY_8           0x25
#define KEY_9           0x26
#define KEY_0           0x27
#define KEY_ENTER       0x28
#define KEY_ESC         0x29
#define KEY_BACKSPACE   0x2A
#define KEY_TAB         0x2B
#define KEY_SPACE       0x2C

/* 输入事件类型 */
#define EV_KEY_PRESS    0x01
#define EV_KEY_RELEASE  0x00

/* 错误码 */
#define KB_OK           0
#define KB_ERR_INIT     -1
#define KB_ERR_SCAN     -2
#define KB_ERR_IRQ      -3
#define KB_ERR_MAP      -4

/* 按键状态 */
typedef enum {
    KEY_STATE_IDLE,         /* 空闲状态 */
    KEY_STATE_PRESSED,      /* 按下状态 */
    KEY_STATE_DEBOUNCING,   /* 去抖状态 */
    KEY_STATE_RELEASED      /* 释放状态 */
} key_state_t;

/* 按键事件 */
typedef struct {
    uint8_t row;            /* 行号 */
    uint8_t col;            /* 列号 */
    uint8_t keycode;        /* 键值 */
    uint8_t state;          /* 状态 */
    int32_t timestamp;      /* 时间戳 */
} key_event_t;

/* 键盘矩阵 */
typedef struct {
    uint8_t state[MATRIX_ROWS][MATRIX_COLS];    /* 当前状态 */
    uint8_t prev_state[MATRIX_ROWS][MATRIX_COLS]; /* 上一次状态 */
    int32_t debounce_time[MATRIX_ROWS][MATRIX_COLS]; /* 去抖时间 */
} matrix_t;

/* 键盘设备 */
typedef struct {
    matrix_t matrix;                /* 键盘矩阵 */
    key_event_t event_queue[64];    /* 事件队列 */
    int queue_head;                 /* 队列头 */
    int queue_tail;                 /* 队队尾 */
    bool initialized;               /* 初始化标志 */
} keyboard_dev_t;

/* 函数声明 */

/* 初始化键盘设备 */
int keyboard_init(keyboard_dev_t *dev);

/* 扫描键盘矩阵 */
int keyboard_scan(keyboard_dev_t *dev);

/* 处理中断 */
int keyboard_interrupt_handler(keyboard_dev_t *dev);

/* 映射按键 */
uint8_t keyboard_map_key(uint8_t row, uint8_t col);

/* 去抖处理 */
bool keyboard_debounce(keyboard_dev_t *dev, uint8_t row, uint8_t col);

/* 生成输入事件 */
int keyboard_report_event(keyboard_dev_t *dev, key_event_t *event);

/* 获取按键事件 */
int keyboard_get_event(keyboard_dev_t *dev, key_event_t *event);

/* 清除事件队列 */
void keyboard_clear_events(keyboard_dev_t *dev);

/* 打印键盘状态 */
void keyboard_dump_state(const keyboard_dev_t *dev);

/* 矩阵扫描相关函数 */
int matrix_scan_full(matrix_t *matrix);
void matrix_dump(const matrix_t *matrix);
int matrix_detect_changes(const matrix_t *matrix, key_event_t *events, int max_events);

/* 去抖算法类型 */
typedef enum {
    DEBOUNCE_TYPE_TIMER,        /* 定时器去抖 */
    DEBOUNCE_TYPE_COUNTER,      /* 计数器去抖 */
    DEBOUNCE_TYPE_STATE_MACHINE /* 状态机去抖 */
} debounce_type_t;

/* 去抖相关函数 */
int debounce_init(debounce_type_t type, int32_t debounce_time);
bool debounce_process(uint8_t row, uint8_t col, bool pressed, int32_t current_time);
key_state_t debounce_get_state(uint8_t row, uint8_t col);
void debounce_dump_state(void);

/* 中断相关函数 */
int interrupt_init(void);
int interrupt_simulate_trigger(keyboard_dev_t *dev);
void interrupt_dump_info(void);
void interrupt_get_stats(int *count, int *errors);
int interrupt_configure_trigger(int trigger_type);
int interrupt_enable(bool enable);

/* 输入事件系统函数 */
typedef void (*event_handler_t)(const key_event_t *event);
int input_event_init(void);
int input_event_register_handler(event_handler_t handler);
int input_event_report(const key_event_t *event);
int input_event_get(key_event_t *event);
void input_event_clear(void);
int input_event_count(void);
void input_event_dump(const key_event_t *event);
void input_event_dump_status(void);

#endif /* KEYBOARD_H */
