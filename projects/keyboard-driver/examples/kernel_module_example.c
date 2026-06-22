/*
 * 键盘驱动内核模块示例
 *
 * 这是一个简化的Linux内核模块示例，展示键盘驱动的基本结构。
 * 注意：这是一个教学示例，不能直接编译运行，需要内核开发环境。
 *
 * 编译内核模块需要：
 * 1. Linux内核头文件
 * 2. 内核模块构建系统
 *
 * 编译命令：
 * make -C /lib/modules/$(uname -r)/build M=$(PWD) modules
 *
 * 加载模块：
 * sudo insmod keyboard_module.ko
 *
 * 卸载模块：
 * sudo rmmod keyboard_module
 */

#include <linux/module.h>
#include <linux/kernel.h>
#include <linux/init.h>
#include <linux/interrupt.h>
#include <linux/input.h>
#include <linux/gpio.h>
#include <linux/timer.h>

/* 模块信息 */
MODULE_LICENSE("GPL");
MODULE_AUTHOR("Keyboard Driver Tutorial");
MODULE_DESCRIPTION("Simple keyboard driver example");
MODULE_VERSION("1.0");

/* 硬件配置 */
#define MATRIX_ROWS     6
#define MATRIX_COLS     14
#define DEBOUNCE_MS     5

/* GPIO引脚定义（示例） */
static int row_pins[MATRIX_ROWS] = {0, 1, 2, 3, 4, 5};
static int col_pins[MATRIX_COLS] = {6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19};

/* 输入设备结构 */
static struct input_dev *keyboard_input;

/* 中断号 */
static int irq_number;

/* 去抖定时器 */
static struct timer_list debounce_timer;

/* 键盘矩阵状态 */
static uint8_t matrix_state[MATRIX_ROWS][MATRIX_COLS];
static uint8_t prev_state[MATRIX_ROWS][MATRIX_COLS];

/* 按键映射表 */
static const unsigned int keymap[MATRIX_ROWS][MATRIX_COLS] = {
    /* 行0: ESC, F1-F12, DEL */
    {KEY_ESC, KEY_F1, KEY_F2, KEY_F3, KEY_F4, KEY_F5, KEY_F6, KEY_F7, KEY_F8, KEY_F9, KEY_F10, KEY_F11, KEY_F12, KEY_DELETE},
    /* 行1: `, 1-9, 0, -, =, BACKSPACE */
    {KEY_GRAVE, KEY_1, KEY_2, KEY_3, KEY_4, KEY_5, KEY_6, KEY_7, KEY_8, KEY_9, KEY_0, KEY_MINUS, KEY_EQUAL, KEY_BACKSPACE},
    /* 行2: TAB, Q-P, [, ], \ */
    {KEY_TAB, KEY_Q, KEY_W, KEY_E, KEY_R, KEY_T, KEY_Y, KEY_U, KEY_I, KEY_O, KEY_P, KEY_LEFTBRACE, KEY_RIGHTBRACE, KEY_BACKSLASH},
    /* 行3: CAPS, A-L, ;, ', ENTER */
    {KEY_CAPSLOCK, KEY_A, KEY_S, KEY_D, KEY_F, KEY_G, KEY_H, KEY_J, KEY_K, KEY_L, KEY_SEMICOLON, KEY_APOSTROPHE, KEY_ENTER, KEY_UNKNOWN},
    /* 行4: SHIFT, Z-M, ,, ., /, SHIFT */
    {KEY_LEFTSHIFT, KEY_Z, KEY_X, KEY_C, KEY_V, KEY_B, KEY_N, KEY_M, KEY_COMMA, KEY_DOT, KEY_SLASH, KEY_RIGHTSHIFT, KEY_UNKNOWN, KEY_UNKNOWN},
    /* 行5: CTRL, WIN, ALT, SPACE, ALT, FN, CTRL */
    {KEY_LEFTCTRL, KEY_LEFTMETA, KEY_LEFTALT, KEY_SPACE, KEY_RIGHTALT, KEY_UNKNOWN, KEY_RIGHTCTRL, KEY_UNKNOWN, KEY_UNKNOWN, KEY_UNKNOWN, KEY_UNKNOWN, KEY_UNKNOWN, KEY_UNKNOWN, KEY_UNKNOWN}
};

/* 扫描键盘矩阵 */
static void scan_matrix(void)
{
    int row, col;

    /* 保存上一次状态 */
    memcpy(prev_state, matrix_state, sizeof(matrix_state));

    /* 逐行扫描 */
    for (row = 0; row < MATRIX_ROWS; row++) {
        /* 将当前行拉低 */
        gpio_set_value(row_pins[row], 0);

        /* 等待电平稳定 */
        udelay(10);

        /* 读取列状态 */
        for (col = 0; col < MATRIX_COLS; col++) {
            matrix_state[row][col] = !gpio_get_value(col_pins[col]);
        }

        /* 将当前行拉高 */
        gpio_set_value(row_pins[row], 1);
    }
}

/* 报告按键事件 */
static void report_key_event(unsigned int keycode, int pressed)
{
    input_report_key(keyboard_input, keycode, pressed);
    input_sync(keyboard_input);

    printk(KERN_DEBUG "Keyboard: key %s (code=%d)\n",
           pressed ? "pressed" : "released", keycode);
}

/* 去抖定时器回调 */
static void debounce_timer_callback(struct timer_list *t)
{
    int row, col;
    bool current, previous;

    /* 扫描矩阵 */
    scan_matrix();

    /* 检测按键变化 */
    for (row = 0; row < MATRIX_ROWS; row++) {
        for (col = 0; col < MATRIX_COLS; col++) {
            current = matrix_state[row][col];
            previous = prev_state[row][col];

            /* 检测状态变化 */
            if (current != previous) {
                /* 报告按键事件 */
                report_key_event(keymap[row][col], current);
            }
        }
    }
}

/* 中断处理函数 */
static irqreturn_t keyboard_irq_handler(int irq, void *dev_id)
{
    /* 启动去抖定时器 */
    mod_timer(&debounce_timer, jiffies + msecs_to_jiffies(DEBOUNCE_MS));

    return IRQ_HANDLED;
}

/* 初始化GPIO */
static int init_gpio(void)
{
    int i, ret;

    /* 初始化行引脚（输出） */
    for (i = 0; i < MATRIX_ROWS; i++) {
        ret = gpio_request(row_pins[i], "keyboard_row");
        if (ret) {
            printk(KERN_ERR "Keyboard: failed to request row pin %d\n", row_pins[i]);
            goto err_row;
        }
        gpio_direction_output(row_pins[i], 1);
    }

    /* 初始化列引脚（输入） */
    for (i = 0; i < MATRIX_COLS; i++) {
        ret = gpio_request(col_pins[i], "keyboard_col");
        if (ret) {
            printk(KERN_ERR "Keyboard: failed to request col pin %d\n", col_pins[i]);
            goto err_col;
        }
        gpio_direction_input(col_pins[i]);
    }

    return 0;

err_col:
    for (i--; i >= 0; i--) {
        gpio_free(col_pins[i]);
    }
    i = MATRIX_ROWS;
err_row:
    for (i--; i >= 0; i--) {
        gpio_free(row_pins[i]);
    }
    return ret;
}

/* 初始化输入设备 */
static int init_input_device(void)
{
    int i, j, ret;

    /* 分配输入设备 */
    keyboard_input = input_allocate_device();
    if (!keyboard_input) {
        printk(KERN_ERR "Keyboard: failed to allocate input device\n");
        return -ENOMEM;
    }

    /* 设置设备属性 */
    keyboard_input->name = "Keyboard Driver Example";
    keyboard_input->phys = "keyboard/input0";
    keyboard_input->id.bustype = BUS_VIRTUAL;
    keyboard_input->id.vendor = 0x0001;
    keyboard_input->id.product = 0x0001;
    keyboard_input->id.version = 0x0100;

    /* 设置事件类型 */
    set_bit(EV_KEY, keyboard_input->evbit);

    /* 设置支持的按键 */
    for (i = 0; i < MATRIX_ROWS; i++) {
        for (j = 0; j < MATRIX_COLS; j++) {
            if (keymap[i][j] != KEY_UNKNOWN) {
                set_bit(keymap[i][j], keyboard_input->keybit);
            }
        }
    }

    /* 注册输入设备 */
    ret = input_register_device(keyboard_input);
    if (ret) {
        printk(KERN_ERR "Keyboard: failed to register input device\n");
        input_free_device(keyboard_input);
        return ret;
    }

    return 0;
}

/* 初始化中断 */
static int init_interrupt(void)
{
    int ret;

    /* 请求中断 */
    /* 注意：实际硬件需要根据具体GPIO配置中断 */
    irq_number = gpio_to_irq(row_pins[0]);
    if (irq_number < 0) {
        printk(KERN_ERR "Keyboard: failed to get IRQ number\n");
        return irq_number;
    }

    ret = request_irq(irq_number, keyboard_irq_handler,
                      IRQF_TRIGGER_FALLING, "keyboard", NULL);
    if (ret) {
        printk(KERN_ERR "Keyboard: failed to request IRQ %d\n", irq_number);
        return ret;
    }

    printk(KERN_INFO "Keyboard: IRQ %d registered\n", irq_number);

    return 0;
}

/* 模块初始化函数 */
static int __init keyboard_init(void)
{
    int ret;

    printk(KERN_INFO "Keyboard: initializing module\n");

    /* 初始化GPIO */
    ret = init_gpio();
    if (ret) {
        goto err_gpio;
    }

    /* 初始化输入设备 */
    ret = init_input_device();
    if (ret) {
        goto err_input;
    }

    /* 初始化中断 */
    ret = init_interrupt();
    if (ret) {
        goto err_irq;
    }

    /* 初始化去抖定时器 */
    timer_setup(&debounce_timer, debounce_timer_callback, 0);

    printk(KERN_INFO "Keyboard: module initialized successfully\n");

    return 0;

err_irq:
    input_unregister_device(keyboard_input);
err_input:
    /* 释放GPIO */
err_gpio:
    return ret;
}

/* 模块退出函数 */
static void __exit keyboard_exit(void)
{
    int i;

    printk(KERN_INFO "Keyboard: exiting module\n");

    /* 删除定时器 */
    del_timer_sync(&debounce_timer);

    /* 释放中断 */
    free_irq(irq_number, NULL);

    /* 注销输入设备 */
    input_unregister_device(keyboard_input);

    /* 释放GPIO */
    for (i = 0; i < MATRIX_ROWS; i++) {
        gpio_free(row_pins[i]);
    }
    for (i = 0; i < MATRIX_COLS; i++) {
        gpio_free(col_pins[i]);
    }

    printk(KERN_INFO "Keyboard: module exited\n");
}

/* 注册模块初始化和退出函数 */
module_init(keyboard_init);
module_exit(keyboard_exit);
