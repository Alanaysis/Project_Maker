#include "../include/keyboard.h"
#include <stdio.h>
#include <string.h>

/* 矩阵扫描器配置 */
#define SCAN_DELAY_US   10      /* 扫描延迟（微秒） */

/* 行引脚定义（模拟） */
static const int row_pins[MATRIX_ROWS] = {0, 1, 2, 3, 4, 5};

/* 列引脚定义（模拟） */
static const int col_pins[MATRIX_COLS] = {6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19};

/* 初始化矩阵扫描器 */
int matrix_scanner_init(void)
{
    printf("[Matrix] Initializing matrix scanner\n");
    printf("[Matrix] Rows: %d, Columns: %d\n", MATRIX_ROWS, MATRIX_COLS);

    /* 在实际硬件中，这里会：
     * 1. 配置行引脚为输出模式
     * 2. 配置列引脚为输入模式（带上拉电阻）
     * 3. 设置初始电平
     */

    for (int i = 0; i < MATRIX_ROWS; i++) {
        printf("[Matrix] Row pin %d configured as output\n", row_pins[i]);
    }

    for (int i = 0; i < MATRIX_COLS; i++) {
        printf("[Matrix] Column pin %d configured as input (pull-up)\n", col_pins[i]);
    }

    return KB_OK;
}

/* 扫描单行 */
static int scan_row(int row, uint8_t *col_state)
{
    if (row < 0 || row >= MATRIX_ROWS || col_state == NULL) {
        return KB_ERR_SCAN;
    }

    /* 在实际硬件中，这里会：
     * 1. 将当前行拉低
     * 2. 等待一小段时间（让电平稳定）
     * 3. 读取所有列的状态
     * 4. 将当前行拉高
     */

    /* 模拟：假设第2行第3列有按键按下 */
    for (int col = 0; col < MATRIX_COLS; col++) {
        if (row == 2 && col == 3) {
            col_state[col] = 0;  /* 低电平表示按下 */
        } else {
            col_state[col] = 1;  /* 高电平表示未按下 */
        }
    }

    return KB_OK;
}

/* 完整矩阵扫描 */
int matrix_scan_full(matrix_t *matrix)
{
    if (matrix == NULL) {
        return KB_ERR_SCAN;
    }

    /* 保存上一次状态 */
    memcpy(matrix->prev_state, matrix->state, sizeof(matrix->state));

    /* 逐行扫描 */
    for (int row = 0; row < MATRIX_ROWS; row++) {
        uint8_t col_state[MATRIX_COLS];

        int ret = scan_row(row, col_state);
        if (ret != KB_OK) {
            return ret;
        }

        /* 更新矩阵状态 */
        for (int col = 0; col < MATRIX_COLS; col++) {
            /* 按键按下时为低电平，转换为1表示按下 */
            matrix->state[row][col] = (col_state[col] == 0) ? 1 : 0;
        }
    }

    return KB_OK;
}

/* 打印矩阵扫描结果 */
void matrix_dump(const matrix_t *matrix)
{
    if (matrix == NULL) {
        return;
    }

    printf("\n[Matrix] Scan Result:\n");
    printf("  ");
    for (int col = 0; col < MATRIX_COLS; col++) {
        printf("%2d ", col);
    }
    printf("\n");

    for (int row = 0; row < MATRIX_ROWS; row++) {
        printf("%2d ", row);
        for (int col = 0; col < MATRIX_COLS; col++) {
            printf(" %d ", matrix->state[row][col]);
        }
        printf("\n");
    }
    printf("\n");
}

/* 检测按键变化 */
int matrix_detect_changes(const matrix_t *matrix, key_event_t *events, int max_events)
{
    if (matrix == NULL || events == NULL || max_events <= 0) {
        return 0;
    }

    int event_count = 0;

    for (int row = 0; row < MATRIX_ROWS && event_count < max_events; row++) {
        for (int col = 0; col < MATRIX_COLS && event_count < max_events; col++) {
            bool current = matrix->state[row][col];
            bool previous = matrix->prev_state[row][col];

            if (current != previous) {
                events[event_count].row = row;
                events[event_count].col = col;
                events[event_count].state = current ? EV_KEY_PRESS : EV_KEY_RELEASE;
                event_count++;
            }
        }
    }

    return event_count;
}
