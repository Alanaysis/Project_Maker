/**
 * embedded-gui - 嵌入式 GUI 框架
 * src/widget.c - Widget 系统实现
 *
 * Widget 是 GUI 的基本构建块
 * 采用面向对象风格 (C 语言模拟 OOP):
 * - 所有 widget 共享一个基类结构 (egui_widget_t)
 * - 通过 type 字段区分具体类型
 * - 通过 data 字段存储类型特定的数据
 * - 通过 on_event/on_render 回调处理事件和渲染
 *
 * Widget 层次结构:
 * - 树形结构: 每个 widget 有父节点和子节点链表
 * - 事件冒泡: 事件从子节点向父节点传播
 * - 渲染顺序: 父节点先渲染，子节点后渲染 ( painter's algorithm )
 */

#include "embedded_gui.h"
#include <string.h>
#include <stdio.h>

/* ============================================================
 * 静态数据 (用于无外部内存分配) / Static data (no malloc)
 * ============================================================ */

/* 用于存储 widget 文本内容的缓冲区池 / Buffer pool for widget text */
#define TEXT_POOL_SIZE 4096
static char egui_text_pool[TEXT_POOL_SIZE];
static size_t egui_text_pool_used = 0;

/* 用于存储 widget 私有数据的缓冲区 / Buffer for widget private data */
#define DATA_POOL_SIZE 8192
static char egui_data_pool[DATA_POOL_SIZE];
static size_t egui_data_pool_used = 0;

/* ============================================================
 * Widget 创建 / Widget Creation
 * ============================================================ */

/**
 * 创建 widget 基类
 * 初始化所有公共字段
 */
static egui_widget_t *egui_widget_create(egui_widget_type_t type) {
    static uint16_t next_id = 1;
    static egui_widget_t widgets[64];
    static bool initialized = false;

    if (!initialized) {
        memset(widgets, 0, sizeof(widgets));
        initialized = true;
    }

    /* 查找空槽位 / Find empty slot */
    for (int i = 0; i < 64; i++) {
        if (widgets[i].type == EGUI_WIDGET_NONE) {
            widgets[i].type = type;
            widgets[i].id = next_id++;
            widgets[i].visible = 1;
            widgets[i].enabled = 1;
            widgets[i].layout_mode = EGUI_LAYOUT_ABSOLUTE;
            widgets[i].align = EGUI_ALIGN_LEFT | EGUI_ALIGN_TOP;
            widgets[i].state = EGUI_STATE_NORMAL;
            widgets[i].style.border_width = 1;
            widgets[i].style.corner_radius = 2;
            widgets[i].style.padding = 4;
            return &widgets[i];
        }
    }
    return NULL; /* 池已满 / Pool full */
}

/**
 * 创建按钮
 * data 指向一个自定义结构，存储按钮文本
 */
typedef struct {
    char text[64];
    bool pressed;
} egui_button_data_t;

egui_widget_t *egui_button_create(egui_widget_t *parent, const char *text, egui_rect_t rect) {
    egui_widget_t *w = egui_widget_create(EGUI_WIDGET_BUTTON);
    if (!w) return NULL;

    w->rect = rect;

    /* 复制文本到池 / Copy text to pool */
    egui_button_data_t *data = (egui_button_data_t *)egui_data_pool;
    strncpy(data->text, text, sizeof(data->text) - 1);
    data->text[sizeof(data->text) - 1] = '\0';
    data->pressed = false;
    w->data = data;

    /* 设置默认样式 / Set default style */
    w->style.bg_color = egui_rgb888_to_rgb565(0x4A, 0x90, 0xD9); /* 蓝色 / Blue */
    w->style.fg_color = egui_rgb888_to_rgb565(0xFF, 0xFF, 0xFF); /* 白色 / White */
    w->style.border_color = egui_rgb888_to_rgb565(0x35, 0x6E, 0xA8);
    w->style.border_width = 2;
    w->style.corner_radius = 4;
    w->style.padding = 8;

    /* 设置渲染回调 / Set render callback */
    w->on_render = NULL; /* 由应用层设置 / Set by app layer */

    /* 添加到父组件 / Add to parent */
    if (parent) {
        egui_widget_add_child(parent, w);
    }

    return w;
}

/**
 * 创建标签
 * data 存储文本指针
 */
typedef struct {
    char text[256];
} egui_label_data_t;

egui_widget_t *egui_label_create(egui_widget_t *parent, const char *text, egui_rect_t rect) {
    egui_widget_t *w = egui_widget_create(EGUI_WIDGET_LABEL);
    if (!w) return NULL;

    w->rect = rect;

    egui_label_data_t *data = (egui_label_data_t *)((char *)egui_data_pool + sizeof(egui_button_data_t));
    strncpy(data->text, text, sizeof(data->text) - 1);
    data->text[sizeof(data->text) - 1] = '\0';
    w->data = data;

    w->style.fg_color = egui_rgb888_to_rgb565(0x00, 0x00, 0x00); /* 黑色 / Black */
    w->style.padding = 2;

    if (parent) {
        egui_widget_add_child(parent, w);
    }

    return w;
}

/**
 * 创建文本框
 * data 存储缓冲区信息和光标位置
 */
typedef struct {
    char *buffer;
    size_t buf_size;
    size_t text_len;
    int16_t cursor_pos;
    int16_t scroll_offset;
} egui_textbox_data_t;

egui_widget_t *egui_textbox_create(egui_widget_t *parent, char *buffer, size_t buf_size, egui_rect_t rect) {
    egui_widget_t *w = egui_widget_create(EGUI_WIDGET_TEXTBOX);
    if (!w) return NULL;

    w->rect = rect;

    egui_textbox_data_t *data = (egui_textbox_data_t *)((char *)egui_data_pool + sizeof(egui_button_data_t) + sizeof(egui_label_data_t));
    data->buffer = buffer;
    data->buf_size = buf_size;
    data->text_len = strlen(buffer);
    data->cursor_pos = (int16_t)data->text_len;
    data->scroll_offset = 0;
    w->data = data;

    w->style.bg_color = egui_rgb888_to_rgb565(0xFF, 0xFF, 0xFF); /* 白色背景 / White background */
    w->style.fg_color = egui_rgb888_to_rgb565(0x00, 0x00, 0x00); /* 黑色文字 / Black text */
    w->style.border_color = egui_rgb888_to_rgb565(0x88, 0x88, 0x88);
    w->style.border_width = 1;
    w->style.padding = 4;

    if (parent) {
        egui_widget_add_child(parent, w);
    }

    return w;
}

/**
 * 创建滑块
 * data 存储范围、值和方向
 */
typedef struct {
    int16_t min;
    int16_t max;
    int16_t value;
    int16_t prev_value;
    bool vertical;
    bool dragging;
} egui_slider_data_t;

egui_widget_t *egui_slider_create(egui_widget_t *parent, int16_t min, int16_t max, int16_t value, egui_rect_t rect) {
    egui_widget_t *w = egui_widget_create(EGUI_WIDGET_SLIDER);
    if (!w) return NULL;

    w->rect = rect;

    /* 找下一个数据槽位 / Find next data slot */
    size_t offset = sizeof(egui_button_data_t) + sizeof(egui_label_data_t) +
                    (sizeof(egui_textbox_data_t) > sizeof(egui_slider_data_t) ?
                     sizeof(egui_textbox_data_t) : sizeof(egui_slider_data_t));
    egui_slider_data_t *data = (egui_slider_data_t *)((char *)egui_data_pool + offset);
    data->min = min;
    data->max = max;
    data->value = value;
    data->prev_value = value;
    data->vertical = (rect.height > rect.width);
    data->dragging = false;
    w->data = data;

    w->style.fg_color = egui_rgb888_to_rgb565(0x4A, 0x90, 0xD9); /* 蓝色 / Blue */
    w->style.border_color = egui_rgb888_to_rgb565(0x88, 0x88, 0x88);
    w->style.border_width = 1;

    if (parent) {
        egui_widget_add_child(parent, w);
    }

    return w;
}

/**
 * 创建复选框
 * data 存储选中状态和标签文本
 */
typedef struct {
    bool checked;
    char label[64];
} egui_checkbox_data_t;

egui_widget_t *egui_checkbox_create(egui_widget_t *parent, const char *text, bool checked, egui_rect_t rect) {
    egui_widget_t *w = egui_widget_create(EGUI_WIDGET_CHECKBOX);
    if (!w) return NULL;

    w->rect = rect;

    size_t offset = sizeof(egui_button_data_t) + sizeof(egui_label_data_t) +
                    (sizeof(egui_textbox_data_t) > sizeof(egui_slider_data_t) ?
                     sizeof(egui_textbox_data_t) : sizeof(egui_slider_data_t)) +
                    sizeof(egui_checkbox_data_t);
    egui_checkbox_data_t *data = (egui_checkbox_data_t *)((char *)egui_data_pool + offset);
    data->checked = checked;
    strncpy(data->label, text, sizeof(data->label) - 1);
    data->label[sizeof(data->label) - 1] = '\0';
    w->data = data;

    w->style.fg_color = egui_rgb888_to_rgb565(0x00, 0x00, 0x00);
    w->style.border_color = egui_rgb888_to_rgb565(0x88, 0x88, 0x88);
    w->style.border_width = 1;

    if (parent) {
        egui_widget_add_child(parent, w);
    }

    return w;
}

/**
 * 创建容器
 * 容器是特殊的 widget，用于组织子组件
 */
egui_widget_t *egui_container_create(egui_widget_t *parent, egui_rect_t rect) {
    egui_widget_t *w = egui_widget_create(EGUI_WIDGET_CONTAINER);
    if (!w) return NULL;

    w->rect = rect;
    w->style.bg_color = egui_rgb888_to_rgb565(0xF0, 0xF0, 0xF0); /* 浅灰背景 / Light gray bg */
    w->style.border_color = egui_rgb888_to_rgb565(0xCC, 0xCC, 0xCC);
    w->style.border_width = 1;
    w->style.corner_radius = 4;

    if (parent) {
        egui_widget_add_child(parent, w);
    }

    return w;
}

/* ============================================================
 * Widget 操作 / Widget Operations
 * ============================================================ */

/**
 * 销毁 widget
 * 仅标记为无效，不释放内存 (静态池管理)
 */
void egui_widget_destroy(egui_widget_t *w) {
    if (!w) return;
    w->type = EGUI_WIDGET_NONE;
    w->visible = 0;
    w->enabled = 0;
}

/**
 * 设置 widget 矩形区域
 */
void egui_widget_set_rect(egui_widget_t *w, egui_rect_t rect) {
    if (!w) return;
    w->rect = rect;
}

/**
 * 设置 widget 可见性
 */
void egui_widget_set_visible(egui_widget_t *w, bool visible) {
    if (!w) return;
    w->visible = visible ? 1 : 0;
}

/**
 * 设置 widget 启用状态
 */
void egui_widget_set_enabled(egui_widget_t *w, bool enabled) {
    if (!w) return;
    w->enabled = enabled ? 1 : 0;
    if (!enabled) {
        w->state &= ~(EGUI_STATE_PRESSED | EGUI_STATE_FOCUSED | EGUI_STATE_HOVER);
    }
}

/**
 * 设置 widget 文本
 * 更新 data 中的文本字段
 */
void egui_widget_set_text(egui_widget_t *w, const char *text) {
    if (!w || !text) return;

    switch (w->type) {
    case EGUI_WIDGET_BUTTON: {
        egui_button_data_t *data = (egui_button_data_t *)w->data;
        strncpy(data->text, text, sizeof(data->text) - 1);
        data->text[sizeof(data->text) - 1] = '\0';
        break;
    }
    case EGUI_WIDGET_LABEL: {
        egui_label_data_t *data = (egui_label_data_t *)w->data;
        strncpy(data->text, text, sizeof(data->text) - 1);
        data->text[sizeof(data->text) - 1] = '\0';
        break;
    }
    default:
        break;
    }
}

/**
 * 设置 widget 样式
 */
void egui_widget_set_style(egui_widget_t *w, const egui_style_t *style) {
    if (!w || !style) return;
    w->style = *style;
}

/**
 * 设置 widget 事件回调
 */
void egui_widget_set_on_event(egui_widget_t *w, egui_event_fn callback) {
    if (!w) return;
    w->on_event = callback;
}

/**
 * 设置 widget 渲染回调
 */
void egui_widget_set_on_render(egui_widget_t *w, egui_render_fn callback) {
    if (!w) return;
    w->on_render = callback;
}

/**
 * 添加子组件到父组件
 * 维护双向链表: parent -> child -> next/prev
 */
void egui_widget_add_child(egui_widget_t *parent, egui_widget_t *child) {
    if (!parent || !child) return;

    child->parent = parent;
    child->next = NULL;
    child->prev = NULL;

    if (!parent->child) {
        parent->child = child;
    } else {
        /* 添加到链表末尾 / Add to end of list */
        egui_widget_t *last = parent->child;
        while (last->next) {
            last = last->next;
        }
        last->next = child;
        child->prev = last;
    }
}

/**
 * 从父组件移除子组件
 */
void egui_widget_remove_child(egui_widget_t *parent, egui_widget_t *child) {
    if (!parent || !child) return;

    if (child->prev) {
        child->prev->next = child->next;
    } else {
        parent->child = child->next;
    }
    if (child->next) {
        child->next->prev = child->prev;
    }
    child->parent = NULL;
    child->next = NULL;
    child->prev = NULL;
}

/* ============================================================
 * Widget 渲染回调 / Widget Render Callbacks
 *
 * 每个 widget 类型有自己的渲染逻辑
 * 渲染器使用裁剪区域优化: 被遮挡的 widget 不渲染
 */

/**
 * 按钮渲染
 * 绘制圆角矩形 + 居中文本
 */
static void egui_button_render(egui_widget_t *w, egui_fb_t *fb) {
    if (!w || !w->visible) return;

    egui_rect_t rect = w->rect;
    egui_style_t *style = &w->style;

    /* 根据状态调整颜色 / Adjust color based on state */
    egui_color_t bg = style->bg_color;
    egui_color_t fg = style->fg_color;

    if (w->state & EGUI_STATE_PRESSED) {
        /* 按下时变暗 / Darken when pressed */
        uint8_t r, g, b;
        egui_rgb565_to_rgb888(bg, &r, &g, &b);
        r = (uint8_t)(r * 0.8);
        g = (uint8_t)(g * 0.8);
        b = (uint8_t)(b * 0.8);
        bg = egui_rgb888_to_rgb565(r, g, b);
    }

    if (w->state & EGUI_STATE_DISABLED) {
        /* 禁用时变灰 / Gray out when disabled */
        uint8_t r, g, b;
        egui_rgb565_to_rgb888(bg, &r, &g, &b);
        uint8_t gray = (uint8_t)((r + g + b) / 3);
        bg = egui_rgb888_to_rgb565(gray, gray, gray);
        fg = egui_rgb888_to_rgb565(gray + 40, gray + 40, gray + 40);
    }

    /* 绘制背景 / Draw background */
    egui_fill_rounded_rect(fb, rect, style->corner_radius, bg);

    /* 绘制边框 / Draw border */
    if (style->border_width > 0) {
        egui_draw_rounded_rect(fb, rect, style->corner_radius, style->border_color, style->border_width);
    }

    /* 绘制文本 / Draw text */
    if (w->data) {
        egui_button_data_t *data = (egui_button_data_t *)w->data;
        if (data->text[0]) {
            /* 计算文本居中位置 / Calculate centered text position */
            /* 简化: 使用固定宽度估算 / Simplified: use fixed width estimation */
            int16_t text_width = (int16_t)strlen(data->text) * 6; /* 6px per char / 每字符6像素 */
            int16_t text_x = rect.x + (rect.width > (uint16_t)text_width ?
                        (rect.width - text_width) / 2 : 4);
            int16_t text_y = rect.y + (rect.height > 16 ?
                        (rect.height - 16) / 2 + 4 : 4);

            egui_draw_text(fb, data->text,
                (egui_point_t){text_x, text_y},
                NULL, fg); /* font will be set from theme */
        }
    }
}

/**
 * 标签渲染
 * 直接绘制文本
 */
static void egui_label_render(egui_widget_t *w, egui_fb_t *fb) {
    if (!w || !w->visible) return;

    if (w->data) {
        egui_label_data_t *data = (egui_label_data_t *)w->data;
        if (data->text[0]) {
            egui_draw_text(fb, data->text,
                (egui_point_t){w->rect.x, w->rect.y},
                NULL, w->style.fg_color);
        }
    }
}

/**
 * 文本框渲染
 * 绘制边框 + 文本 + 光标
 */
static void egui_textbox_render(egui_widget_t *w, egui_fb_t *fb) {
    if (!w || !w->visible) return;

    egui_style_t *style = &w->style;

    /* 绘制背景 / Draw background */
    egui_fill_rect(fb, w->rect, style->bg_color);

    /* 绘制边框 / Draw border */
    egui_draw_rect(fb, w->rect, style->border_color, style->border_width);

    /* 绘制文本 / Draw text */
    if (w->data) {
        egui_textbox_data_t *data = (egui_textbox_data_t *)w->data;
        if (data->text_len > 0) {
            egui_draw_text(fb, data->buffer,
                (egui_point_t){w->rect.x + style->padding,
                               w->rect.y + style->padding},
                NULL, style->fg_color);
        }
    }

    /* 绘制光标 (如果聚焦) / Draw cursor if focused */
    if (w->state & EGUI_STATE_FOCUSED) {
        uint16_t cursor_x = w->rect.x + w->style.padding + 6; /* 简化估算 / Simplified estimate */
        uint16_t cursor_y = w->rect.y + w->rect.height / 2 - 8;
        egui_draw_line(fb,
            (egui_point_t){(int16_t)cursor_x, (int16_t)cursor_y},
            (egui_point_t){(int16_t)cursor_x, (int16_t)(cursor_y + 8)},
            style->fg_color);
    }
}

/**
 * 滑块渲染
 * 绘制轨道 + 指示器
 */
static void egui_slider_render(egui_widget_t *w, egui_fb_t *fb) {
    if (!w || !w->visible) return;

    egui_style_t *style = &w->style;

    if (w->data) {
        egui_slider_data_t *data = (egui_slider_data_t *)w->data;

        if (data->vertical) {
            /* 垂直滑块 / Vertical slider */
            float ratio = (data->max != data->min) ?
                (float)(data->value - data->min) / (data->max - data->min) : 0.5f;
            uint16_t track_height = w->rect.height - 4;
            uint16_t thumb_y = w->rect.y + 2 + (uint16_t)((1.0f - ratio) * track_height);

            /* 绘制轨道 / Draw track */
            egui_fill_rect(fb, (egui_rect_t){w->rect.x + 2, w->rect.y + 2, 4, track_height},
                           egui_rgb888_to_rgb565(0xCC, 0xCC, 0xCC));

            /* 绘制指示器 / Draw indicator */
            egui_fill_rect(fb, (egui_rect_t){w->rect.x, thumb_y, 8, 8}, style->fg_color);
            egui_draw_circle(fb, (egui_point_t){w->rect.x + 4, (int16_t)(thumb_y + 4)}, 4, style->fg_color);
        } else {
            /* 水平滑块 / Horizontal slider */
            float ratio = (data->max != data->min) ?
                (float)(data->value - data->min) / (data->max - data->min) : 0.5f;
            uint16_t track_width = w->rect.width - 4;
            uint16_t thumb_x = w->rect.x + 2 + (uint16_t)(ratio * track_width);

            /* 绘制轨道 / Draw track */
            egui_fill_rect(fb, (egui_rect_t){w->rect.x + 2, w->rect.y + w->rect.height / 2 - 2,
                                           track_width, 4},
                           egui_rgb888_to_rgb565(0xCC, 0xCC, 0xCC));

            /* 绘制指示器 / Draw indicator */
            egui_fill_circle(fb, (egui_point_t){(int16_t)(thumb_x + 4), w->rect.y + w->rect.height / 2}, 4, style->fg_color);
        }
    }
}

/**
 * 复选框渲染
 * 绘制方框 + 选中标记
 */
static void egui_checkbox_render(egui_widget_t *w, egui_fb_t *fb) {
    if (!w || !w->visible) return;

    egui_style_t *style = &w->style;

    /* 绘制方框 / Draw box */
    egui_fill_rect(fb, w->rect, style->bg_color);
    egui_draw_rect(fb, w->rect, style->border_color, style->border_width);

    /* 如果选中，绘制标记 / Draw checkmark if checked */
    if (w->data) {
        egui_checkbox_data_t *data = (egui_checkbox_data_t *)w->data;
        if (data->checked) {
            /* 绘制 "X" 标记 / Draw "X" mark */
            int16_t cx = w->rect.x + w->rect.width / 2;
            int16_t cy = w->rect.y + w->rect.height / 2;
            int16_t s = w->rect.width / 4;
            egui_draw_line(fb,
                (egui_point_t){cx - s, cy - s},
                (egui_point_t){cx + s, cy + s},
                style->fg_color);
            egui_draw_line(fb,
                (egui_point_t){cx + s, cy - s},
                (egui_point_t){cx - s, cy + s},
                style->fg_color);
        }
    }

    /* 绘制标签文本 (如果有) / Draw label text if available */
    if (w->data) {
        egui_checkbox_data_t *data = (egui_checkbox_data_t *)w->data;
        if (data->label[0]) {
            egui_draw_text(fb, data->label,
                (egui_point_t){w->rect.x + w->rect.width + 4, w->rect.y},
                NULL, style->fg_color);
        }
    }
}

/**
 * 容器渲染
 * 绘制背景 + 边框
 */
static void egui_container_render(egui_widget_t *w, egui_fb_t *fb) {
    if (!w || !w->visible) return;

    egui_style_t *style = &w->style;
    egui_fill_rect(fb, w->rect, style->bg_color);
    if (style->border_width > 0) {
        egui_draw_rounded_rect(fb, w->rect, style->corner_radius, style->border_color, style->border_width);
    }
}

/* ============================================================
 * Widget 渲染分发 / Widget Render Dispatch
 *
 * 根据 widget 类型调用对应的渲染函数
 * 这是嵌入式 GUI 的核心调度机制
 */
void egui_widget_render(egui_widget_t *w, egui_fb_t *fb) {
    if (!w || !w->visible || !w->enabled) return;

    /* 先渲染父组件 / Render parent first */
    if (w->parent && w->parent->on_render) {
        /* 父组件的渲染由父组件的 on_render 处理，这里跳过 */
    }

    /* 应用裁剪 / Apply clipping */
    egui_rect_t clip = w->rect;
    /* 与父组件裁剪区域取交集 / Intersect with parent clip rect */

    /* 根据类型调用对应的渲染函数 / Call render function based on type */
    if (w->on_render) {
        w->on_render(w, fb);
    } else {
        /* 默认渲染 / Default render */
        switch (w->type) {
        case EGUI_WIDGET_BUTTON:    egui_button_render(w, fb); break;
        case EGUI_WIDGET_LABEL:     egui_label_render(w, fb); break;
        case EGUI_WIDGET_TEXTBOX:   egui_textbox_render(w, fb); break;
        case EGUI_WIDGET_SLIDER:    egui_slider_render(w, fb); break;
        case EGUI_WIDGET_CHECKBOX:  egui_checkbox_render(w, fb); break;
        case EGUI_WIDGET_CONTAINER: egui_container_render(w, fb); break;
        default:
            /* 未知类型: 绘制矩形框 / Unknown type: draw rectangle */
            egui_draw_rect(fb, w->rect, egui_rgb888_to_rgb565(0xFF, 0x00, 0x00), 1);
            break;
        }
    }

    /* 递归渲染子组件 / Recursively render children */
    egui_widget_t *child = w->child;
    while (child) {
        egui_widget_render(child, fb);
        child = child->next;
    }
}
