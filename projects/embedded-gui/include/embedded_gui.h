/**
 * embedded-gui - 嵌入式 GUI 框架 / Embedded GUI Framework
 *
 * 一个用于嵌入式系统的轻量级 GUI 框架
 * A lightweight GUI framework for embedded systems
 *
 * 架构: UI定义 -> 布局计算 -> 渲染 -> 事件处理
 * Architecture: UI Definition -> Layout -> Rendering -> Event Handling
 */

#ifndef EMBEDDED_GUI_H
#define EMBEDDED_GUI_H

#include <stdint.h>
#include <stdbool.h>
#include <stddef.h>

/* ============================================================
 * 基础类型定义 / Basic Type Definitions
 * ============================================================ */

/** 像素颜色格式: RGB565 (16-bit) - 嵌入式系统常用 */
typedef uint16_t egui_color_t;

/** 坐标和尺寸 */
typedef struct {
    int16_t x;
    int16_t y;
} egui_point_t;

typedef struct {
    int16_t x;
    int16_t y;
    uint16_t width;
    uint16_t height;
} egui_rect_t;

/** 帧缓冲区 / Framebuffer */
typedef struct {
    egui_color_t *buffer;     /* 像素缓冲区 / Pixel buffer */
    uint16_t width;           /* 屏幕宽度 / Screen width */
    uint16_t height;          /* 屏幕高度 / Screen height */
    uint16_t stride;          /* 每行字节数 / Bytes per row */
} egui_fb_t;

/* ============================================================
 * 事件系统 / Event System
 * ============================================================ */

/** 事件类型 / Event types */
typedef enum {
    EGUI_EVENT_NONE = 0,
    EGUI_EVENT_TOUCH_PRESS,       /* 触摸按下 / Touch press */
    EGUI_EVENT_TOUCH_RELEASE,     /* 触摸释放 / Touch release */
    EGUI_EVENT_TOUCH_MOVE,        /* 触摸移动 / Touch move */
    EGUI_EVENT_KEY_PRESS,         /* 按键按下 / Key press */
    EGUI_EVENT_KEY_RELEASE,       /* 按键释放 / Key release */
    EGUI_EVENT_TIMER,             /* 定时器 / Timer */
    EGUI_EVENT_FOCUS,             /* 焦点变化 / Focus change */
    EGUI_EVENT_SCROLL,            /* 滚动 / Scroll */
    EGUI_EVENT_CUSTOM,            /* 自定义事件 / Custom event */
} egui_event_type_t;

/** 按键码 / Key codes */
typedef enum {
    EGUI_KEY_NONE = 0,
    EGUI_KEY_UP,
    EGUI_KEY_DOWN,
    EGUI_KEY_LEFT,
    EGUI_KEY_RIGHT,
    EGUI_KEY_ENTER,
    EGUI_KEY_BACK,
    EGUI_KEY_TAB,
    EGUI_KEY_SPACE,
    EGUI_KEY_0 = 48,
    EGUI_KEY_9 = 57,
    EGUI_KEY_A = 65,
    EGUI_KEY_Z = 90,
} egui_key_code_t;

/** 事件结构 / Event structure */
typedef struct {
    egui_event_type_t type;       /* 事件类型 / Event type */
    egui_point_t pos;             /* 事件位置 (x, y) / Event position */
    int16_t key_code;             /* 按键码 (仅 KEY 事件) / Key code (key events only) */
    uint32_t timestamp;           /* 事件时间戳 / Event timestamp */
    void *user_data;              /* 用户数据 / User data */
} egui_event_t;

/* ============================================================
 * 字体系统 / Font System
 * ============================================================ */

/** 位图字体字符 / Bitmap font character */
typedef struct {
    uint8_t width;                /* 字符宽度 / Character width */
    uint8_t height;               /* 字符高度 / Character height */
    int8_t  x_offset;             /* X 偏移 / X offset */
    int8_t  y_offset;             /* Y 偏移 / Y offset */
    uint8_t x_advance;            /* X 步进 / X advance */
    const uint8_t *data;          /* 位图数据 / Bitmap data (每行1 bit) */
} egui_font_char_t;

/** 位图字体 / Bitmap font */
typedef struct {
    uint8_t  char_height;         /* 字符高度 / Character height */
    uint8_t  baseline;            /* 基线位置 / Baseline position */
    egui_font_char_t chars[96];   /* ASCII 32-127 / ASCII 32-127 */
    uint8_t  max_width;           /* 最大字符宽度 / Max character width */
} egui_font_t;

/* ============================================================
 * 主题/样式系统 / Theme/Style System
 * ============================================================ */

/** 组件样式 / Widget style */
typedef struct {
    egui_color_t bg_color;        /* 背景色 / Background color */
    egui_color_t fg_color;        /* 前景色 (文字/边框) / Foreground color (text/border) */
    egui_color_t border_color;    /* 边框色 / Border color */
    uint8_t  border_width;        /* 边框宽度 / Border width */
    uint8_t  corner_radius;       /* 圆角半径 / Corner radius */
    uint8_t  padding;             /* 内边距 / Padding */
    uint8_t  opacity;             /* 透明度 0-255 / Opacity 0-255 */
} egui_style_t;

/** 主题 / Theme - 定义全局外观 / Defines global appearance */
typedef struct {
    egui_style_t button;          /* 按钮样式 / Button style */
    egui_style_t label;           /* 标签样式 / Label style */
    egui_style_t textbox;         /* 文本框样式 / Textbox style */
    egui_style_t slider;          /* 滑块样式 / Slider style */
    egui_style_t checkbox;        /* 复选框样式 / Checkbox style */
    egui_color_t window_bg;       /* 窗口背景色 / Window background */
    egui_color_t window_title_fg; /* 窗口标题色 / Window title color */
    egui_color_t highlight;       /* 高亮色 / Highlight color */
    const egui_font_t *font;      /* 默认字体 / Default font */
} egui_theme_t;

/* ============================================================
 * Widget 系统 / Widget System
 * ============================================================ */

/** Widget 类型 / Widget types */
typedef enum {
    EGUI_WIDGET_NONE = 0,
    EGUI_WIDGET_BUTTON,           /* 按钮 / Button */
    EGUI_WIDGET_LABEL,            /* 标签 / Label */
    EGUI_WIDGET_TEXTBOX,          /* 文本框 / Textbox */
    EGUI_WIDGET_SLIDER,           /* 滑块 / Slider */
    EGUI_WIDGET_CHECKBOX,         /* 复选框 / Checkbox */
    EGUI_WIDGET_WINDOW,           /* 窗口 / Window */
    EGUI_WIDGET_CONTAINER,        /* 容器 / Container */
    EGUI_WIDGET_IMAGE,            /* 图像 / Image */
    EGUI_WIDGET_PROGRESS,         /* 进度条 / Progress bar */
    EGUI_WIDGET_SCROLLVIEW,       /* 滚动视图 / Scroll view */
} egui_widget_type_t;

/** 布局模式 / Layout modes */
typedef enum {
    EGUI_LAYOUT_ABSOLUTE,         /* 绝对定位 / Absolute positioning */
    EGUI_LAYOUT_RELATIVE,         /* 相对定位 / Relative positioning */
    EGUI_LAYOUT_FLOW,             /* 流式布局 / Flow layout */
    EGUI_LAYOUT_GRID,             /* 网格布局 / Grid layout */
} egui_layout_mode_t;

/** 对齐方式 / Alignment */
typedef enum {
    EGUI_ALIGN_LEFT   = (1 << 0),
    EGUI_ALIGN_CENTER = (1 << 1),
    EGUI_ALIGN_RIGHT  = (1 << 2),
    EGUI_ALIGN_TOP    = (1 << 3),
    EGUI_ALIGN_MIDDLE = (1 << 4),
    EGUI_ALIGN_BOTTOM = (1 << 5),
} egui_align_t;

/** 组件状态 / Widget states */
typedef enum {
    EGUI_STATE_NORMAL   = 0,
    EGUI_STATE_PRESSED  = (1 << 0),
    EGUI_STATE_FOCUSED  = (1 << 1),
    EGUI_STATE_DISABLED = (1 << 2),
    EGUI_STATE_HOVER    = (1 << 3),
} egui_state_t;

/** 渲染回调函数 / Render callback */
typedef void (*egui_render_fn)(void *widget, egui_fb_t *fb);

/** 事件回调函数 / Event callback */
typedef void (*egui_event_fn)(void *widget, const egui_event_t *event);

/* 前向声明 / Forward declarations */
typedef struct egui_widget egui_widget_t;
typedef struct egui_window egui_window_t;

/** 通用 Widget 基类 / Generic widget base class */
struct egui_widget {
    struct egui_widget *parent;   /* 父组件 / Parent widget */
    struct egui_widget *child;    /* 子组件链表头 / First child */
    struct egui_widget *next;     /* 兄弟组件 / Next sibling */
    struct egui_widget *prev;     /* 上一个兄弟 / Previous sibling */

    egui_rect_t rect;             /* 组件矩形区域 / Widget rectangle */
    egui_rect_t clip_rect;        /* 裁剪区域 / Clip rectangle */
    egui_widget_type_t type;      /* 组件类型 / Widget type */
    uint16_t id;                  /* 组件ID / Widget ID */
    uint8_t  state;               /* 当前状态 / Current state */
    uint8_t  visible;             /* 可见性 / Visibility */
    uint8_t  enabled;             /* 启用状态 / Enabled state */

    egui_layout_mode_t layout_mode; /* 布局模式 / Layout mode */
    egui_align_t align;           /* 对齐方式 / Alignment */
    int16_t  margin_left;         /* 左边距 / Left margin */
    int16_t  margin_top;          /* 上边距 / Top margin */
    int16_t  margin_right;        /* 右边距 / Right margin */
    int16_t  margin_bottom;       /* 下边距 / Bottom margin */

    egui_style_t style;           /* 组件样式 / Widget style */
    egui_event_fn on_event;       /* 事件回调 / Event callback */
    egui_render_fn on_render;     /* 渲染回调 / Render callback */

    void *data;                   /* 组件私有数据 / Widget private data */
};

/** 窗口 / Window */
struct egui_window {
    egui_widget_t root;           /* 窗口根组件 / Root widget */
    char title[64];               /* 窗口标题 / Window title */
    egui_rect_t frame;            /* 窗口帧 / Window frame */
    egui_window_t *next;          /* 下一个窗口 / Next window */
    uint8_t  z_order;             /* Z 轴层级 / Z-order */
    uint8_t  focused;             /* 是否聚焦 / Is focused */
};

/* ============================================================
 * 布局引擎 / Layout Engine
 * ============================================================ */

/** 布局结果 / Layout result */
typedef struct {
    egui_rect_t bounds;           /* 布局边界 / Layout bounds */
    uint16_t child_count;         /* 子组件数 / Child count */
} egui_layout_result_t;

/* ============================================================
 * 渲染引擎 / Rendering Engine
 * ============================================================ */

/** 渲染器 / Renderer */
typedef struct {
    egui_fb_t *fb;                /* 帧缓冲区 / Framebuffer */
    egui_rect_t clip_rect;        /* 当前裁剪区域 / Current clip rect */
    egui_color_t current_color;   /* 当前绘制颜色 / Current drawing color */
} egui_renderer_t;

/* ============================================================
 * 显示驱动 / Display Driver
 * ============================================================ */

/** 显示驱动接口 / Display driver interface */
typedef struct {
    void (*init)(void);           /* 初始化显示 / Initialize display */
    void (*flush)(egui_fb_t *fb, const egui_rect_t *rect); /* 刷新显示 / Flush to display */
    void (*set_orientation)(uint8_t orientation); /* 设置方向 / Set orientation */
    void (*set_backlight)(uint8_t level); /* 设置背光 / Set backlight */
} egui_display_driver_t;

/* ============================================================
 * 输入驱动 / Input Driver
 * ============================================================ */

/** 输入驱动接口 / Input driver interface */
typedef struct {
    bool (*init)(void);           /* 初始化输入 / Initialize input */
    bool (*poll_event)(egui_event_t *event); /* 轮询事件 / Poll event */
    bool (*has_event)(void);      /* 是否有事件 / Has event */
} egui_input_driver_t;

/* ============================================================
 * GUI 核心 / GUI Core
 * ============================================================ */

/** GUI 实例 / GUI instance */
typedef struct {
    egui_fb_t fb;                 /* 帧缓冲区 / Framebuffer */
    egui_window_t *windows;       /* 窗口链表 / Window list */
    egui_window_t *focused_window; /* 聚焦窗口 / Focused window */
    egui_event_t pending_event;   /* 待处理事件 / Pending event */
    egui_theme_t theme;           /* 当前主题 / Current theme */
    egui_display_driver_t *display_driver; /* 显示驱动 / Display driver */
    egui_input_driver_t *input_driver;     /* 输入驱动 / Input driver */
    uint32_t tick_count;          /* 系统滴答计数 / System tick count */
    bool running;                 /* 是否运行 / Is running */
} egui_t;

/* ============================================================
 * 公共 API / Public API
 * ============================================================ */

/* --- 帧缓冲区 / Framebuffer --- */
void egui_fb_init(egui_fb_t *fb, egui_color_t *mem, uint16_t width, uint16_t height);

/* --- 初始化 / Initialization --- */
void egui_init(egui_t *gui, egui_color_t *fb_mem, uint16_t width, uint16_t height);
void egui_deinit(egui_t *gui);
int  egui_run(egui_t *gui);
void egui_stop(egui_t *gui);

/* --- 窗口管理 / Window Management --- */
egui_window_t *egui_window_create(const char *title, egui_rect_t frame);
void egui_window_destroy(egui_window_t *win);
void egui_window_focus(egui_window_t *win);
void egui_window_raise(egui_window_t *win);
void egui_window_lower(egui_window_t *win);
void egui_gui_add_window(egui_t *gui, egui_window_t *win);
void egui_gui_remove_window(egui_t *gui, egui_window_t *win);

/* --- Widget 创建 / Widget Creation --- */
egui_widget_t *egui_button_create(egui_widget_t *parent, const char *text, egui_rect_t rect);
egui_widget_t *egui_label_create(egui_widget_t *parent, const char *text, egui_rect_t rect);
egui_widget_t *egui_textbox_create(egui_widget_t *parent, char *buffer, size_t buf_size, egui_rect_t rect);
egui_widget_t *egui_slider_create(egui_widget_t *parent, int16_t min, int16_t max, int16_t value, egui_rect_t rect);
egui_widget_t *egui_checkbox_create(egui_widget_t *parent, const char *text, bool checked, egui_rect_t rect);
egui_widget_t *egui_container_create(egui_widget_t *parent, egui_rect_t rect);

/* --- Widget 操作 / Widget Operations --- */
void egui_widget_destroy(egui_widget_t *w);
void egui_widget_set_rect(egui_widget_t *w, egui_rect_t rect);
void egui_widget_set_visible(egui_widget_t *w, bool visible);
void egui_widget_set_enabled(egui_widget_t *w, bool enabled);
void egui_widget_set_text(egui_widget_t *w, const char *text);
void egui_widget_set_style(egui_widget_t *w, const egui_style_t *style);
void egui_widget_set_on_event(egui_widget_t *w, egui_event_fn callback);
void egui_widget_set_on_render(egui_widget_t *w, egui_render_fn callback);
void egui_widget_add_child(egui_widget_t *parent, egui_widget_t *child);
void egui_widget_remove_child(egui_widget_t *parent, egui_widget_t *child);
void egui_widget_render(egui_widget_t *w, egui_fb_t *fb);

/* --- 布局引擎 / Layout Engine --- */
void egui_layout_absolute(egui_widget_t *w);
void egui_layout_relative(egui_widget_t *w, const egui_rect_t *container);
void egui_layout_flow(egui_widget_t *w, const egui_rect_t *container, egui_align_t direction);
void egui_layout_gravity(egui_widget_t *w, const egui_rect_t *container, egui_align_t align);
egui_layout_result_t egui_layout_result_create(void);

/* --- 渲染引擎 / Rendering Engine --- */
void egui_renderer_init(egui_renderer_t *r, egui_fb_t *fb);
void egui_renderer_set_clip(egui_renderer_t *r, egui_rect_t rect);

/* 绘图基元 / Drawing primitives */
void egui_draw_line(egui_fb_t *fb, egui_point_t p1, egui_point_t p2, egui_color_t color);
void egui_draw_rect(egui_fb_t *fb, egui_rect_t rect, egui_color_t color, uint8_t border_width);
void egui_fill_rect(egui_fb_t *fb, egui_rect_t rect, egui_color_t color);
void egui_draw_circle(egui_fb_t *fb, egui_point_t center, uint16_t radius, egui_color_t color);
void egui_fill_circle(egui_fb_t *fb, egui_point_t center, uint16_t radius, egui_color_t color);
void egui_draw_text(egui_fb_t *fb, const char *text, egui_point_t pos, const egui_font_t *font, egui_color_t color);
void egui_draw_rounded_rect(egui_fb_t *fb, egui_rect_t rect, uint8_t radius, egui_color_t color, uint8_t border_width);
void egui_fill_rounded_rect(egui_fb_t *fb, egui_rect_t rect, uint8_t radius, egui_color_t color);

/* --- 事件处理 / Event Handling --- */
void egui_event_dispatch(egui_t *gui, const egui_event_t *event);
egui_widget_t *egui_hit_test(egui_widget_t *w, egui_point_t pos);
void egui_event_queue_push(egui_event_t *event);

/* --- 主题 / Theme --- */
void egui_theme_default(egui_theme_t *theme, const egui_font_t *font);
void egui_theme_dark(egui_theme_t *theme, const egui_font_t *font);
void egui_theme_light(egui_theme_t *theme, const egui_font_t *font);

/* --- 颜色工具 / Color Utilities --- */
egui_color_t egui_rgb888_to_rgb565(uint8_t r, uint8_t g, uint8_t b);
void egui_rgb565_to_rgb888(egui_color_t color, uint8_t *r, uint8_t *g, uint8_t *b);

/* --- 字体 / Font --- */
const egui_font_t *egui_font_get_builtin(void);

#endif /* EMBEDDED_GUI_H */
