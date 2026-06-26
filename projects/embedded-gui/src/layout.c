/**
 * embedded-gui - 嵌入式 GUI 框架
 * src/layout.c - 布局引擎实现
 *
 * 布局引擎负责计算每个 widget 的位置和大小
 * 嵌入式 GUI 的布局算法需要:
 * 1. 低内存占用: 不使用复杂的树结构
 * 2. 确定性: 同样的输入产生同样的输出
 * 3. 可预测的性能: 布局计算时间有限
 *
 * 布局模式:
 * - 绝对定位: 手动指定每个 widget 的 (x, y)
 * - 相对定位: 基于父组件或兄弟组件定位
 * - 流式布局: widget 按顺序排列，自动换行
 * - 重力对齐: widget 靠边对齐 (左/右/上/下/居中)
 */

#include "embedded_gui.h"
#include <string.h>

/* ============================================================
 * 绝对定位布局 / Absolute Positioning Layout
 *
 * 每个 widget 的 rect 直接指定其位置
 * 这是嵌入式系统中最常用的布局方式:
 * - 最简单，性能最高
 * - 无布局计算开销
 * - 适合固定界面 (如仪表盘、状态显示)
 *
 * 算法: O(n)，只需遍历子组件链表
 */
void egui_layout_absolute(egui_widget_t *w) {
    if (!w) return;

    /* 遍历所有子组件 / Traverse all children */
    egui_widget_t *child = w->child;
    while (child) {
        /* 子组件的 rect 已经在创建时设置 / Child rect already set at creation */
        /* 递归处理子组件的子组件 / Recurse into children's children */
        egui_layout_absolute(child);
        child = child->next;
    }
}

/* ============================================================
 * 相对定位布局 / Relative Positioning Layout
 *
 * widget 的位置基于容器边界和偏移量计算
 * 适合响应式界面: 当容器大小变化时，子组件自动调整
 *
 * 算法:
 * 1. 遍历子组件
 * 2. 根据 margin 和 align 计算位置
 * 3. 递归处理子组件
 */
void egui_layout_relative(egui_widget_t *w, const egui_rect_t *container) {
    if (!w || !container) return;

    egui_widget_t *child = w->child;
    while (child) {
        if (child->visible) {
            /* 计算子组件相对于容器的位置 / Calculate child position relative to container */
            int16_t x = container->x + child->margin_left;
            int16_t y = container->y + child->margin_top;

            /* 应用对齐 / Apply alignment */
            if (child->align & EGUI_ALIGN_CENTER) {
                x = container->x + (int16_t)(container->width - child->rect.width) / 2;
            }
            if (child->align & EGUI_ALIGN_RIGHT) {
                x = container->x + (int16_t)container->width - child->rect.width - child->margin_right;
            }
            if (child->align & EGUI_ALIGN_MIDDLE) {
                y = container->y + (int16_t)(container->height - child->rect.height) / 2;
            }
            if (child->align & EGUI_ALIGN_BOTTOM) {
                y = container->y + (int16_t)container->height - child->rect.height - child->margin_bottom;
            }

            /* 更新子组件位置 / Update child position */
            child->rect.x = x;
            child->rect.y = y;

            /* 递归处理子组件 / Recurse into children */
            egui_layout_relative(child, &child->rect);
        }
        child = child->next;
    }
}

/* ============================================================
 * 流式布局 / Flow Layout
 *
 * widget 按顺序排列，到达边界时自动换行
 * 类似 HTML 中的 flow layout
 *
 * 算法:
 * 1. 维护当前行位置和下一行位置
 * 2. 每个 widget 添加到当前行
 * 3. 如果超出边界，换行
 * 4. 递归处理子组件
 */
void egui_layout_flow(egui_widget_t *w, const egui_rect_t *container, egui_align_t direction) {
    if (!w || !container) return;

    int16_t x = container->x;
    int16_t y = container->y;
    int16_t row_height = 0;

    /* 判断方向: 水平 (默认) 或垂直 / Determine direction: horizontal (default) or vertical */
    bool horizontal = (direction & EGUI_ALIGN_LEFT) || (direction & EGUI_ALIGN_CENTER) || (direction & EGUI_ALIGN_RIGHT);

    egui_widget_t *child = w->child;
    while (child) {
        if (child->visible) {
            if (horizontal) {
                /* 水平流式布局 / Horizontal flow */
                if (x + (int16_t)child->rect.width > container->x + (int16_t)container->width) {
                    /* 换行 / Wrap to next line */
                    x = container->x;
                    y += row_height + 4; /* 行间距 / Line spacing */
                    row_height = 0;
                }

                child->rect.x = x + child->margin_left;
                child->rect.y = y + child->margin_top;

                if (child->rect.height > row_height) {
                    row_height = child->rect.height;
                }
                x += child->rect.width + child->margin_left + child->margin_right + 4;
            } else {
                /* 垂直流式布局 / Vertical flow */
                if (y + (int16_t)child->rect.height > container->y + (int16_t)container->height) {
                    /* 超出容器 / Exceeds container */
                    break;
                }

                child->rect.x = container->x + child->margin_left;
                child->rect.y = y + child->margin_top;
                y += child->rect.height + child->margin_top + child->margin_bottom + 4;
            }

            /* 递归处理子组件 / Recurse into children */
            egui_layout_flow(child, &child->rect, direction);
        }
        child = child->next;
    }
}

/* ============================================================
 * 重力对齐布局 / Gravity Layout
 *
 * widget 靠容器的某一边对齐
 * 常见用法:
 * - 导航栏: widget 靠左/右对齐
 * - 底部按钮: widget 靠下对齐
 * - 居中弹窗: widget 居中对齐
 *
 * 算法:
 * 1. 根据对齐标志计算偏移
 * 2. 应用到 widget rect
 */
void egui_layout_gravity(egui_widget_t *w, const egui_rect_t *container, egui_align_t align) {
    if (!w || !container) return;

    egui_widget_t *child = w->child;
    while (child) {
        if (child->visible) {
            int16_t x = child->rect.x;
            int16_t y = child->rect.y;

            /* 水平对齐 / Horizontal alignment */
            if (align & EGUI_ALIGN_LEFT) {
                x = container->x + child->margin_left;
            } else if (align & EGUI_ALIGN_CENTER) {
                x = container->x + (int16_t)(container->width - child->rect.width) / 2;
            } else if (align & EGUI_ALIGN_RIGHT) {
                x = container->x + (int16_t)container->width - child->rect.width - child->margin_right;
            }

            /* 垂直对齐 / Vertical alignment */
            if (align & EGUI_ALIGN_TOP) {
                y = container->y + child->margin_top;
            } else if (align & EGUI_ALIGN_MIDDLE) {
                y = container->y + (int16_t)(container->height - child->rect.height) / 2;
            } else if (align & EGUI_ALIGN_BOTTOM) {
                y = container->y + (int16_t)container->height - child->rect.height - child->margin_bottom;
            }

            child->rect.x = x;
            child->rect.y = y;

            /* 递归处理子组件 / Recurse into children */
            egui_layout_gravity(child, &child->rect, align);
        }
        child = child->next;
    }
}

/**
 * 创建布局结果
 */
egui_layout_result_t egui_layout_result_create(void) {
    egui_layout_result_t result;
    result.bounds.x = 0;
    result.bounds.y = 0;
    result.bounds.width = 0;
    result.bounds.height = 0;
    result.child_count = 0;
    return result;
}
