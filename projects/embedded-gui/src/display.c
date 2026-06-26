/**
 * embedded-gui - 嵌入式 GUI 框架
 * src/display.c - 帧缓冲区和显示驱动实现
 *
 * 帧缓冲区 (Framebuffer) 是嵌入式 GUI 的核心
 * 它是一块内存区域，存储屏幕每个像素的颜色值
 * 渲染引擎将 UI 绘制到帧缓冲区，再由显示驱动刷新到屏幕
 */

#include "embedded_gui.h"
#include <string.h>

/* ============================================================
 * 帧缓冲区操作 / Framebuffer Operations
 * ============================================================ */

/**
 * 初始化帧缓冲区
 * 分配并清零像素缓冲区
 */
void egui_fb_init(egui_fb_t *fb, egui_color_t *mem, uint16_t width, uint16_t height) {
    fb->buffer = mem;
    fb->width = width;
    fb->height = height;
    /* stride = 每行的字节数 (RGB565 每像素2字节) */
    fb->stride = width * 2;
    /* 初始化为黑色 */
    memset(fb->buffer, 0, (size_t)width * height * 2);
}

/**
 * 设置帧缓冲区中单个像素的颜色
 * 边界检查: 防止越界写入
 */
static void egui_fb_set_pixel(egui_fb_t *fb, int16_t x, int16_t y, egui_color_t color) {
    if (x < 0 || x >= (int16_t)fb->width || y < 0 || y >= (int16_t)fb->height) {
        return; /* 越界: 直接丢弃 / Out of bounds: discard */
    }
    fb->buffer[y * fb->width + x] = color;
}

/**
 * 获取帧缓冲区中单个像素的颜色
 */
static egui_color_t egui_fb_get_pixel(egui_fb_t *fb, int16_t x, int16_t y) {
    if (x < 0 || x >= (int16_t)fb->width || y < 0 || y >= (int16_t)fb->height) {
        return 0; /* 黑色 / Black */
    }
    return fb->buffer[y * fb->width + x];
}

/* ============================================================
 * 显示驱动 (模拟实现) / Display Driver (Mock Implementation)
 *
 * 在实际嵌入式系统中，这里会对接具体的硬件驱动:
 * - SPI LCD 控制器
 * - RGB LCD 接口
 * - E-Ink 控制器
 * - 等等
 */

static void display_init(void) {
    /* 模拟: 初始化显示硬件 / Mock: init display hardware */
}

static void display_flush(egui_fb_t *fb, const egui_rect_t *rect) {
    /* 模拟: 将帧缓冲区数据发送到显示器
     * 实际实现会:
     * 1. 计算需要更新的区域 (dirty rect)
     * 2. 通过 SPI/I2C/RGB 接口发送数据
     * 3. 更新显示控制器的 RAM
     */
    (void)fb;
    (void)rect;
}

static void display_set_orientation(uint8_t orientation) {
    (void)orientation;
}

static void display_set_backlight(uint8_t level) {
    (void)level;
}

/* 创建默认显示驱动 / Create default display driver */
egui_display_driver_t egui_display_driver_default(void) {
    egui_display_driver_t driver;
    driver.init = display_init;
    driver.flush = display_flush;
    driver.set_orientation = display_set_orientation;
    driver.set_backlight = display_set_backlight;
    return driver;
}

/* ============================================================
 * 输入驱动 (模拟实现) / Input Driver (Mock Implementation)
 *
 * 在实际嵌入式系统中，这里会对接:
 * - 电容式触摸屏 (I2C/SPI)
 * - 电阻式触摸屏 (ADC)
 * - 物理按键 (GPIO)
 */

static bool input_init(void) {
    /* 模拟: 初始化输入硬件 / Mock: init input hardware */
    return true;
}

static bool input_poll_event(egui_event_t *event) {
    /* 模拟: 轮询输入事件
     * 实际实现会:
     * 1. 读取触摸屏 ADC/SPI 数据
     * 2. 去抖动处理
     * 3. 坐标变换 (ADC -> 屏幕坐标)
     * 4. 生成事件
     */
    (void)event;
    return false; /* 无事件 / No event */
}

static bool input_has_event(void) {
    /* 模拟: 检查是否有待处理的事件 / Mock: check for pending events */
    return false;
}

/* 创建默认输入驱动 / Create default input driver */
egui_input_driver_t egui_input_driver_default(void) {
    egui_input_driver_t driver;
    driver.init = input_init;
    driver.poll_event = input_poll_event;
    driver.has_event = input_has_event;
    return driver;
}
