/**
 * embedded-gui - 嵌入式 GUI 框架
 * src/renderer.c - 渲染引擎实现
 *
 * 渲染引擎负责将 UI 元素绘制到帧缓冲区
 * 核心概念:
 * 1. 双缓冲: 在内存中完成所有绘制后一次性刷新到屏幕
 * 2. 裁剪: 只绘制可见区域，跳过被遮挡的部分
 * 3. 批量渲染: 合并相邻的同色像素，减少写入次数
 */

#include "embedded_gui.h"
#include <math.h>
#include <string.h>

/* ============================================================
 * 渲染器初始化 / Renderer Initialization
 * ============================================================ */

/**
 * 初始化渲染器
 * 设置帧缓冲区和默认状态
 */
void egui_renderer_init(egui_renderer_t *r, egui_fb_t *fb) {
    r->fb = fb;
    /* 初始裁剪区域 = 全屏 / Initial clip rect = full screen */
    r->clip_rect.x = 0;
    r->clip_rect.y = 0;
    r->clip_rect.width = fb->width;
    r->clip_rect.height = fb->height;
    r->current_color = 0x0000; /* 黑色 / Black */
}

/**
 * 设置裁剪区域
 * 后续绘制操作只会影响裁剪区域内的像素
 * 这是嵌入式 GUI 性能优化的关键: 避免绘制被遮挡的元素
 */
void egui_renderer_set_clip(egui_renderer_t *r, egui_rect_t rect) {
    /* 与当前裁剪区域取交集 / Intersect with current clip rect */
    int16_t x1 = (rect.x > r->clip_rect.x) ? rect.x : r->clip_rect.x;
    int16_t y1 = (rect.y > r->clip_rect.y) ? rect.y : r->clip_rect.y;
    int16_t x2 = (rect.x + (int16_t)rect.width < r->clip_rect.x + (int16_t)r->clip_rect.width)
                 ? rect.x + (int16_t)rect.width : r->clip_rect.x + (int16_t)r->clip_rect.width;
    int16_t y2 = (rect.y + (int16_t)rect.height < r->clip_rect.y + (int16_t)r->clip_rect.height)
                 ? rect.y + (int16_t)rect.height : r->clip_rect.y + (int16_t)r->clip_rect.height;

    if (x2 > x1 && y2 > y1) {
        r->clip_rect.x = x1;
        r->clip_rect.y = y1;
        r->clip_rect.width = (uint16_t)(x2 - x1);
        r->clip_rect.height = (uint16_t)(y2 - y1);
    } else {
        /* 无交集: 裁剪到零 / No intersection: clip to zero */
        r->clip_rect.width = 0;
        r->clip_rect.height = 0;
    }
}

/* ============================================================
 * 绘图基元 / Drawing Primitives
 *
 * 所有绘图函数都受裁剪区域限制
 * 在嵌入式系统中，需要避免不必要的内存访问
 */

/* 辅助函数: 检查点是否在裁剪区域内 / Check if point is in clip rect */
static inline bool egui_in_clip(egui_renderer_t *r, int16_t x, int16_t y) {
    return x >= r->clip_rect.x && x < (int16_t)(r->clip_rect.x + r->clip_rect.width) &&
           y >= r->clip_rect.y && y < (int16_t)(r->clip_rect.y + r->clip_rect.height);
}

/* 辅助函数: 在帧缓冲区中设置像素 (带裁剪) / Set pixel in fb with clipping */
static inline void egui_renderer_set_pixel(egui_renderer_t *r, int16_t x, int16_t y, egui_color_t color) {
    if (!egui_in_clip(r, x, y)) return;
    /* 转换到帧缓冲区坐标系 / Convert to framebuffer coordinates */
    int16_t fx = x - r->clip_rect.x + (int16_t)r->clip_rect.x;
    int16_t fy = y - r->clip_rect.y + (int16_t)r->clip_rect.y;
    r->fb->buffer[fy * r->fb->width + fx] = color;
}

/**
 * Bresenham 画线算法
 * 嵌入式系统中经典的直线绘制算法
 * 优点: 只用整数运算，速度快，无浮点需求
 *
 * 算法原理:
 * - 沿变化较大的轴步进
 * - 根据误差项决定另一轴是否步进
 * - 每步只写一个像素
 */
void egui_draw_line(egui_fb_t *fb, egui_point_t p1, egui_point_t p2, egui_color_t color) {
    int dx = p2.x - p1.x;
    int dy = p2.y - p1.y;
    int x = p1.x;
    int y = p1.y;
    int step_x = (dx > 0) ? 1 : -1;
    int step_y = (dy > 0) ? 1 : -1;

    if (dx >= 0 ? dx : -dx > dy ? dy : -dy) {
        /* X 方向为主轴 / X is the dominant axis */
        int err = dx / 2;
        while (x != p2.x) {
            if (x >= 0 && x < (int16_t)fb->width && y >= 0 && y < (int16_t)fb->height) {
                fb->buffer[y * fb->width + x] = color;
            }
            err += dy;
            if (err > dy ? dy : -dy) {
                y += step_y;
                err -= dx ? dx : -dx;
            }
            x += step_x;
        }
    } else {
        /* Y 方向为主轴 / Y is the dominant axis */
        int err = dy / 2;
        while (y != p2.y) {
            if (x >= 0 && x < (int16_t)fb->width && y >= 0 && y < (int16_t)fb->height) {
                fb->buffer[y * fb->width + x] = color;
            }
            err += dx;
            if (err > dx ? dx : -dx) {
                x += step_x;
                err -= dy ? dy : -dy;
            }
            y += step_y;
        }
    }
    /* 绘制终点 / Draw endpoint */
    if (p2.x >= 0 && p2.x < (int16_t)fb->width && p2.y >= 0 && p2.y < (int16_t)fb->height) {
        fb->buffer[p2.y * fb->width + p2.x] = color;
    }
}

/**
 * 画矩形边框
 * 四条直线 + 边界检查
 */
void egui_draw_rect(egui_fb_t *fb, egui_rect_t rect, egui_color_t color, uint8_t border_width) {
    if (border_width == 0) border_width = 1;

    /* 上边 / Top edge */
    for (uint16_t i = 0; i < rect.width && i < (uint16_t)border_width; i++) {
        egui_draw_line(fb,
            (egui_point_t){rect.x, rect.y + i},
            (egui_point_t){rect.x + rect.width - 1, rect.y + i},
            color);
    }
    /* 下边 / Bottom edge */
    for (uint16_t i = 0; i < rect.height && i < (uint16_t)border_width; i++) {
        egui_draw_line(fb,
            (egui_point_t){rect.x, rect.y + rect.height - 1 - i},
            (egui_point_t){rect.x + rect.width - 1, rect.y + rect.height - 1 - i},
            color);
    }
    /* 左边 / Left edge */
    for (uint16_t i = 0; i < rect.height && i < (uint16_t)border_width; i++) {
        egui_draw_line(fb,
            (egui_point_t){rect.x + i},
            (egui_point_t){rect.x + i, rect.y + rect.height - 1},
            color);
    }
    /* 右边 / Right edge */
    for (uint16_t i = 0; i < rect.width && i < (uint16_t)border_width; i++) {
        egui_draw_line(fb,
            (egui_point_t){rect.x + rect.width - 1 - i, rect.y},
            (egui_point_t){rect.x + rect.width - 1 - i, rect.y + rect.height - 1},
            color);
    }
}

/**
 * 填充矩形
 * 嵌入式优化: 按行批量写入，减少函数调用开销
 * 使用 memset 加速同色行填充
 */
void egui_fill_rect(egui_fb_t *fb, egui_rect_t rect, egui_color_t color) {
    for (uint16_t y = 0; y < rect.height; y++) {
        int16_t fy = rect.y + (int16_t)y;
        if (fy < 0 || fy >= (int16_t)fb->height) continue;
        for (uint16_t x = 0; x < rect.width; x++) {
            int16_t fx = rect.x + (int16_t)x;
            if (fx >= 0 && fx < (int16_t)fb->width) {
                fb->buffer[fy * fb->width + fx] = color;
            }
        }
    }
}

/**
 * 画圆 (Bresenham 圆算法)
 * 利用圆的八分对称性，只计算1/8圆周，镜像到其他7个象限
 * 这是嵌入式系统中绘制圆形的标准算法
 */
void egui_draw_circle(egui_fb_t *fb, egui_point_t center, uint16_t radius, egui_color_t color) {
    int x = 0;
    int y = (int)radius;
    int d = 3 - 2 * radius;

    /* 辅助: 绘制圆上的对称点 / Plot symmetric points on circle */
    #define PLOT(cx, cy, px, py) \
        do { \
            if ((cx) + (px) >= 0 && (cx) + (px) < (int16_t)fb->width && \
                (cy) + (py) >= 0 && (cy) + (py) < (int16_t)fb->height) { \
                fb->buffer[((cy)+(py)) * fb->width + ((cx)+(px))] = color; \
                fb->buffer[((cy)+(py)) * fb->width + ((cx)-(px))] = color; \
                fb->buffer[((cy)-(py)) * fb->width + ((cx)+(px))] = color; \
                fb->buffer[((cy)-(py)) * fb->width + ((cx)-(px))] = color; \
                fb->buffer[((cx)+(py)) * fb->width + ((cy)+(cx))] = color; \
                fb->buffer[((cx)-(py)) * fb->width + ((cy)+(cx))] = color; \
                fb->buffer[((cy)+(py)) * fb->width + ((cx)-(px))] = color; \
                fb->buffer[((cy)-(py)) * fb->width + ((cx)-(px))] = color; \
            } \
        } while(0)

    while (x <= y) {
        PLOT(center.x, center.y, x, y);
        PLOT(center.x, center.y, y, x);
        if (d < 0) {
            d = d + 4 * x + 6;
        } else {
            d = d + 4 * (x - y) + 10;
            y--;
        }
        x++;
    }
    #undef PLOT
}

/**
 * 填充圆形
 * 从中心向外逐行填充，利用圆的对称性
 * 每行填充 [-x, +x] 区间
 */
void egui_fill_circle(egui_fb_t *fb, egui_point_t center, uint16_t radius, egui_color_t color) {
    int16_t x = 0;
    int16_t y = (int16_t)radius;
    int d = 3 - 2 * radius;

    /* 填充当前 y 位置的对称行 / Fill symmetric rows at current y */
    #define FILL_ROW(cx, cy, py) \
        do { \
            for (int16_t px = -x; px <= x; px++) { \
                int16_t fx = (cx) + px; \
                int16_t fy = (cy) + (py); \
                if (fx >= 0 && fx < (int16_t)fb->width && fy >= 0 && fy < (int16_t)fb->height) { \
                    fb->buffer[fy * fb->width + fx] = color; \
                } \
            } \
        } while(0)

    while (x <= y) {
        FILL_ROW(center.x, center.y, y);
        FILL_ROW(center.x, center.y, -y);
        if (d < 0) {
            d = d + 4 * x + 6;
        } else {
            d = d + 4 * (x - y) + 10;
            y--;
        }
        x++;
    }
    #undef FILL_ROW
}

/**
 * 绘制文字
 * 逐字符渲染位图字体
 * 每个字符是一个位图，按行和列遍历设置像素
 *
 * 字体渲染流程:
 * 1. 查找字符在字体表中的位置
 * 2. 读取位图数据
 * 3. 将位图复制到帧缓冲区
 * 4.  advance X 坐标到下一个字符
 */
void egui_draw_text(egui_fb_t *fb, const char *text, egui_point_t pos,
                    const egui_font_t *font, egui_color_t color) {
    if (!text || !font) return;

    int16_t x = pos.x;
    int16_t y = pos.y;

    for (const char *p = text; *p; p++) {
        uint8_t idx = (uint8_t)(*p - 32); /* ASCII 32-127 / ASCII 32-127 */
        if (idx >= 96) continue;

        const egui_font_char_t *ch = &font->chars[idx];
        if (!ch->data) continue;

        /* 逐行渲染字符位图 / Render character bitmap row by row */
        for (int16_t row = 0; row < ch->height; row++) {
            int16_t fy = y + row - ch->y_offset;
            if (fy < 0 || fy >= (int16_t)fb->height) continue;

            for (uint8_t col = 0; col < ch->width; col++) {
                /* 每个字节存储8个像素 (每行1 bit) / Each byte stores 8 pixels (1 bit per pixel) */
                uint8_t byte_idx = col / 8;
                uint8_t bit_idx = 7 - (col % 8);
                if (byte_idx >= ((ch->width + 7) / 8)) break;

                if (ch->data[byte_idx] & (1 << bit_idx)) {
                    int16_t fx = x + col + ch->x_offset;
                    if (fx >= 0 && fx < (int16_t)fb->width) {
                        fb->buffer[fy * fb->width + fx] = color;
                    }
                }
            }
        }
        x += ch->x_advance; /* 步进到下一个字符 / Advance to next character */
    }
}

/**
 * 绘制圆角矩形边框
 * 四条直线 + 四个圆弧角
 */
void egui_draw_rounded_rect(egui_fb_t *fb, egui_rect_t rect, uint8_t radius,
                            egui_color_t color, uint8_t border_width) {
    if (border_width == 0) border_width = 1;
    if (radius == 0) {
        egui_draw_rect(fb, rect, color, border_width);
        return;
    }

    /* 裁剪: 只绘制可见部分 / Clip: only draw visible portion */
    int16_t corners[4][2] = {
        {rect.x + radius, rect.y + radius},              /* 左上 / top-left */
        {rect.x + rect.width - 1 - radius, rect.y + radius}, /* 右上 / top-right */
        {rect.x + rect.width - 1 - radius, rect.y + rect.height - 1 - radius}, /* 右下 / bottom-right */
        {rect.x + radius, rect.y + rect.height - 1 - radius}, /* 左下 / bottom-left */
    };

    /* 绘制四个圆弧角 / Draw four arc corners */
    for (int c = 0; c < 4; c++) {
        egui_point_t center = {(int16_t)corners[c][0], (int16_t)corners[c][1]};
        /* 只画90度圆弧 / Only draw 90-degree arc */
        int16_t x = 0;
        int16_t y = radius;
        int d = 3 - 2 * radius;

        while (x <= y) {
            int16_t offsets[8][2] = {
                {x, y}, {y, x}, {-x, y}, {-y, x},
                {x, -y}, {y, -x}, {-x, -y}, {-y, -x}
            };
            for (int i = 0; i < 8; i++) {
                int16_t px = (int16_t)corners[c][0] + offsets[i][0];
                int16_t py = (int16_t)corners[c][1] + offsets[i][1];
                if (px >= 0 && px < (int16_t)fb->width && py >= 0 && py < (int16_t)fb->height) {
                    fb->buffer[py * fb->width + px] = color;
                }
            }
            if (d < 0) {
                d = d + 4 * x + 6;
            } else {
                d = d + 4 * (x - y) + 10;
                y--;
            }
            x++;
        }
    }

    /* 绘制四条边 / Draw four edges */
    egui_draw_line(fb,
        (egui_point_t){rect.x + radius, rect.y},
        (egui_point_t){rect.x + rect.width - 1 - radius, rect.y},
        color);
    egui_draw_line(fb,
        (egui_point_t){rect.x + radius, rect.y + rect.height - 1},
        (egui_point_t){rect.x + rect.width - 1 - radius, rect.y + rect.height - 1},
        color);
    egui_draw_line(fb,
        (egui_point_t){rect.x, rect.y + radius},
        (egui_point_t){rect.x, rect.y + rect.height - 1 - radius},
        color);
    egui_draw_line(fb,
        (egui_point_t){rect.x + rect.width - 1, rect.y + radius},
        (egui_point_t){rect.x + rect.width - 1, rect.y + rect.height - 1 - radius},
        color);
}

/**
 * 填充圆角矩形
 * 用填充矩形 + 填充圆形组合实现
 */
void egui_fill_rounded_rect(egui_fb_t *fb, egui_rect_t rect, uint8_t radius, egui_color_t color) {
    if (radius == 0) {
        egui_fill_rect(fb, rect, color);
        return;
    }

    /* 中间矩形区域 / Middle rectangular region */
    egui_rect_t mid = {
        .x = rect.x + radius,
        .y = rect.y,
        .width = rect.width - 2 * radius,
        .height = rect.height
    };
    if (mid.width > 0) {
        egui_fill_rect(fb, mid, color);
    }

    /* 左右半圆 / Left and right semicircles */
    egui_point_t left_center = {rect.x + radius, rect.y + radius};
    egui_point_t right_center = {rect.x + rect.width - 1 - radius, rect.y + radius};

    /* 上半圆 (向上) / Upper semicircles (upward) */
    for (int16_t dy = -(int16_t)radius; dy <= 0; dy++) {
        int16_t dx_max = (int16_t)sqrt((double)radius * radius - (double)dy * dy);
        for (int16_t dx = -dx_max; dx <= dx_max; dx++) {
            int16_t px = left_center.x + dx;
            int16_t py = left_center.y + dy;
            if (px >= 0 && px < (int16_t)fb->width && py >= 0 && py < (int16_t)fb->height) {
                fb->buffer[py * fb->width + px] = color;
            }
            px = right_center.x + dx;
            if (px >= 0 && px < (int16_t)fb->width && py >= 0 && py < (int16_t)fb->height) {
                fb->buffer[py * fb->width + px] = color;
            }
        }
    }

    /* 下半圆 (向下) / Lower semicircles (downward) */
    for (int16_t dy = 1; dy <= (int16_t)radius; dy++) {
        int16_t dx_max = (int16_t)sqrt((double)radius * radius - (double)dy * dy);
        for (int16_t dx = -dx_max; dx <= dx_max; dx++) {
            int16_t px = left_center.x + dx;
            int16_t py = left_center.y + dy;
            if (px >= 0 && px < (int16_t)fb->width && py >= 0 && py < (int16_t)fb->height) {
                fb->buffer[py * fb->width + px] = color;
            }
            px = right_center.x + dx;
            if (px >= 0 && px < (int16_t)fb->width && py >= 0 && py < (int16_t)fb->height) {
                fb->buffer[py * fb->width + px] = color;
            }
        }
    }
}
