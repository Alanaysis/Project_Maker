#include "../include/keyboard.h"
#include <stdio.h>
#include <string.h>

/* 去抖状态 */
typedef struct {
    key_state_t state;          /* 当前状态 */
    int32_t last_time;          /* 上次变化时间 */
    int counter;                /* 计数器 */
    bool stable;                /* 是否稳定 */
} debounce_state_t;

/* 去抖器 */
typedef struct {
    debounce_type_t type;       /* 去抖类型 */
    debounce_state_t keys[MATRIX_ROWS][MATRIX_COLS]; /* 按键状态 */
    int32_t debounce_time;      /* 去抖时间 */
    int threshold;              /* 阈值 */
} debouncer_t;

/* 全局去抖器实例 */
static debouncer_t g_debouncer;

/* 初始化去抖器 */
int debounce_init(debounce_type_t type, int32_t debounce_time)
{
    printf("[Debounce] Initializing debouncer\n");
    printf("[Debounce] Type: %s\n",
           type == DEBOUNCE_TYPE_TIMER ? "Timer" :
           type == DEBOUNCE_TYPE_COUNTER ? "Counter" : "State Machine");
    printf("[Debounce] Debounce time: %d ms\n", debounce_time);

    memset(&g_debouncer, 0, sizeof(debouncer_t));
    g_debouncer.type = type;
    g_debouncer.debounce_time = debounce_time;
    g_debouncer.threshold = DEBOUNCE_CYCLES;

    /* 初始化所有按键状态为空闲 */
    for (int row = 0; row < MATRIX_ROWS; row++) {
        for (int col = 0; col < MATRIX_COLS; col++) {
            g_debouncer.keys[row][col].state = KEY_STATE_IDLE;
            g_debouncer.keys[row][col].stable = true;
        }
    }

    return KB_OK;
}

/* 定时器去抖算法 */
static bool debounce_timer(uint8_t row, uint8_t col, bool pressed, int32_t current_time)
{
    debounce_state_t *key = &g_debouncer.keys[row][col];

    /* 检查时间间隔 */
    if ((current_time - key->last_time) < g_debouncer.debounce_time) {
        /* 在去抖时间内，忽略变化 */
        return false;
    }

    /* 更新时间 */
    key->last_time = current_time;

    /* 状态变化 */
    if (pressed && key->state != KEY_STATE_PRESSED) {
        key->state = KEY_STATE_PRESSED;
        return true;
    } else if (!pressed && key->state != KEY_STATE_RELEASED) {
        key->state = KEY_STATE_RELEASED;
        return true;
    }

    return false;
}

/* 计数器去抖算法 */
static bool debounce_counter(uint8_t row, uint8_t col, bool pressed)
{
    debounce_state_t *key = &g_debouncer.keys[row][col];

    if (pressed) {
        key->counter++;
        if (key->counter >= g_debouncer.threshold) {
            if (key->state != KEY_STATE_PRESSED) {
                key->state = KEY_STATE_PRESSED;
                key->counter = 0;
                return true;
            }
        }
    } else {
        key->counter--;
        if (key->counter <= -g_debouncer.threshold) {
            if (key->state != KEY_STATE_RELEASED) {
                key->state = KEY_STATE_RELEASED;
                key->counter = 0;
                return true;
            }
        }
    }

    return false;
}

/* 状态机去抖算法 */
static bool debounce_state_machine(uint8_t row, uint8_t col, bool pressed, int32_t current_time)
{
    debounce_state_t *key = &g_debouncer.keys[row][col];

    switch (key->state) {
    case KEY_STATE_IDLE:
        if (pressed) {
            key->state = KEY_STATE_DEBOUNCING;
            key->last_time = current_time;
        }
        break;

    case KEY_STATE_DEBOUNCING:
        if ((current_time - key->last_time) >= g_debouncer.debounce_time) {
            if (pressed) {
                key->state = KEY_STATE_PRESSED;
                return true;
            } else {
                key->state = KEY_STATE_IDLE;
            }
        }
        break;

    case KEY_STATE_PRESSED:
        if (!pressed) {
            key->state = KEY_STATE_RELEASED;
            key->last_time = current_time;
        }
        break;

    case KEY_STATE_RELEASED:
        if ((current_time - key->last_time) >= g_debouncer.debounce_time) {
            if (!pressed) {
                key->state = KEY_STATE_IDLE;
                return true;
            } else {
                key->state = KEY_STATE_PRESSED;
            }
        }
        break;
    }

    return false;
}

/* 去抖处理主函数 */
bool debounce_process(uint8_t row, uint8_t col, bool pressed, int32_t current_time)
{
    if (row >= MATRIX_ROWS || col >= MATRIX_COLS) {
        return false;
    }

    switch (g_debouncer.type) {
    case DEBOUNCE_TYPE_TIMER:
        return debounce_timer(row, col, pressed, current_time);

    case DEBOUNCE_TYPE_COUNTER:
        return debounce_counter(row, col, pressed);

    case DEBOUNCE_TYPE_STATE_MACHINE:
        return debounce_state_machine(row, col, pressed, current_time);

    default:
        return false;
    }
}

/* 获取按键状态 */
key_state_t debounce_get_state(uint8_t row, uint8_t col)
{
    if (row >= MATRIX_ROWS || col >= MATRIX_COLS) {
        return KEY_STATE_IDLE;
    }

    return g_debouncer.keys[row][col].state;
}

/* 打印去抖状态 */
void debounce_dump_state(void)
{
    printf("\n[Debounce] Current State:\n");
    printf("  Type: %s\n",
           g_debouncer.type == DEBOUNCE_TYPE_TIMER ? "Timer" :
           g_debouncer.type == DEBOUNCE_TYPE_COUNTER ? "Counter" : "State Machine");
    printf("  Debounce Time: %d ms\n", g_debouncer.debounce_time);
    printf("  Threshold: %d\n", g_debouncer.threshold);

    printf("\n  Key States:\n");
    printf("  ");
    for (int col = 0; col < MATRIX_COLS; col++) {
        printf("%2d ", col);
    }
    printf("\n");

    for (int row = 0; row < MATRIX_ROWS; row++) {
        printf("%2d ", row);
        for (int col = 0; col < MATRIX_COLS; col++) {
            const char *state_str;
            switch (g_debouncer.keys[row][col].state) {
            case KEY_STATE_IDLE:       state_str = "I"; break;
            case KEY_STATE_PRESSED:    state_str = "P"; break;
            case KEY_STATE_DEBOUNCING: state_str = "D"; break;
            case KEY_STATE_RELEASED:   state_str = "R"; break;
            default:                   state_str = "?"; break;
            }
            printf(" %s ", state_str);
        }
        printf("\n");
    }
    printf("\n");
}
