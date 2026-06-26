/**
 * embedded-gui - 嵌入式 GUI 框架
 *
 * 嵌入式的 8x12 位图字体
 * 每个字符 96 个 (ASCII 32-127)
 * 字体数据以 1-bit per pixel 存储
 *
 * 字体在嵌入式系统中的存储:
 * - 编译时嵌入到二进制文件 (flash)
 * - 不使用外部字体文件
 * - 每个字符独立存储，按需访问
 */

#include "embedded_gui.h"
#include <string.h>

/* ============================================================
 * 位图字体数据 / Bitmap Font Data
 *
 * 字体设计原则 (嵌入式):
 * 1. 小尺寸: 8x12 或 8x8 适合小屏幕
 * 2. 清晰可读: 笔画粗细适中
 * 3. 紧凑存储: 1-bit per pixel
 * 4. 固定宽度: 简化布局计算
 *
 * 每个字符的位图数据:
 * - 每行 1 byte (8 pixels)
 * - 高位在前 (MSB first)
 * - 黑色 = 0, 白色 = 1 (反色)
 */

/* 字符 'A' (ASCII 65) - 三角形 */
static const uint8_t font_char_A[] = {
    0x00, 0x18, 0x3C, 0x66, 0x66, 0x7E, 0x66, 0x66, 0x66, 0x00,
};

/* 字符 'B' - 两个圆圈 */
static const uint8_t font_char_B[] = {
    0x00, 0x7C, 0x66, 0x66, 0x7C, 0x66, 0x66, 0x7C, 0x00, 0x00,
};

/* 字符 'C' - 开口向右的 C */
static const uint8_t font_char_C[] = {
    0x00, 0x3C, 0x66, 0x60, 0x60, 0x60, 0x60, 0x66, 0x3C, 0x00,
};

/* 字符 'D' - 半圆 */
static const uint8_t font_char_D[] = {
    0x00, 0x7C, 0x66, 0x66, 0x66, 0x66, 0x66, 0x7C, 0x00, 0x00,
};

/* 字符 'E' - 左侧竖线 + 三横 */
static const uint8_t font_char_E[] = {
    0x00, 0x7E, 0x60, 0x60, 0x7E, 0x60, 0x60, 0x7E, 0x00, 0x00,
};

/* 字符 'F' - 左侧竖线 + 两横 */
static const uint8_t font_char_F[] = {
    0x00, 0x7E, 0x60, 0x60, 0x7E, 0x60, 0x60, 0x60, 0x00, 0x00,
};

/* 字符 'G' - C + 中间横 */
static const uint8_t font_char_G[] = {
    0x00, 0x3C, 0x66, 0x60, 0x6E, 0x66, 0x66, 0x3E, 0x00, 0x00,
};

/* 字符 'H' - 两竖 + 中间横 */
static const uint8_t font_char_H[] = {
    0x00, 0x66, 0x66, 0x66, 0x7E, 0x66, 0x66, 0x66, 0x00, 0x00,
};

/* 字符 'I' - 竖线 */
static const uint8_t font_char_I[] = {
    0x00, 0x3C, 0x18, 0x18, 0x18, 0x18, 0x18, 0x3C, 0x00, 0x00,
};

/* 字符 'L' - 左侧竖线 + 底部横 */
static const uint8_t font_char_L[] = {
    0x00, 0x60, 0x60, 0x60, 0x60, 0x60, 0x60, 0x7E, 0x00, 0x00,
};

/* 字符 'M' - 两竖 + 两个斜线 */
static const uint8_t font_char_M[] = {
    0x00, 0x66, 0x6E, 0x7E, 0x7E, 0x66, 0x66, 0x66, 0x00, 0x00,
};

/* 字符 'N' - 两竖 + 对角线 */
static const uint8_t font_char_N[] = {
    0x00, 0x66, 0x66, 0x6C, 0x76, 0x76, 0x6E, 0x66, 0x00, 0x00,
};

/* 字符 'O' - 椭圆 */
static const uint8_t font_char_O[] = {
    0x00, 0x3C, 0x66, 0x66, 0x66, 0x66, 0x66, 0x3C, 0x00, 0x00,
};

/* 字符 'P' - 左侧竖线 + 上半圆 */
static const uint8_t font_char_P[] = {
    0x00, 0x7C, 0x66, 0x66, 0x7C, 0x60, 0x60, 0x60, 0x00, 0x00,
};

/* 字符 'R' - P + 右下斜线 */
static const uint8_t font_char_R[] = {
    0x00, 0x7C, 0x66, 0x66, 0x7C, 0x6C, 0x66, 0x66, 0x00, 0x00,
};

/* 字符 'S' - S 形 */
static const uint8_t font_char_S[] = {
    0x00, 0x3C, 0x66, 0x60, 0x3C, 0x06, 0x66, 0x3C, 0x00, 0x00,
};

/* 字符 'T' - 顶部横 + 中间竖 */
static const uint8_t font_char_T[] = {
    0x00, 0x7E, 0x18, 0x18, 0x18, 0x18, 0x18, 0x18, 0x00, 0x00,
};

/* 字符 'U' - U 形 */
static const uint8_t font_char_U[] = {
    0x00, 0x66, 0x66, 0x66, 0x66, 0x66, 0x66, 0x3C, 0x00, 0x00,
};

/* 字符 'X' - 交叉 */
static const uint8_t font_char_X[] = {
    0x00, 0x66, 0x66, 0x3C, 0x18, 0x3C, 0x66, 0x66, 0x00, 0x00,
};

/* 字符 'Y' - Y 形 */
static const uint8_t font_char_Y[] = {
    0x00, 0x66, 0x66, 0x3C, 0x18, 0x18, 0x18, 0x18, 0x00, 0x00,
};

/* 字符 'Z' - Z 形 */
static const uint8_t font_char_Z[] = {
    0x00, 0x7E, 0x06, 0x0C, 0x18, 0x30, 0x66, 0x7E, 0x00, 0x00,
};

/* 字符 '0' - 椭圆 + 中间斜线 */
static const uint8_t font_char_0[] = {
    0x00, 0x3C, 0x66, 0x6E, 0x76, 0x6E, 0x66, 0x3C, 0x00, 0x00,
};

/* 字符 '1' - 竖线 */
static const uint8_t font_char_1[] = {
    0x00, 0x18, 0x38, 0x18, 0x18, 0x18, 0x18, 0x3C, 0x00, 0x00,
};

/* 字符 '2' - 2 形 */
static const uint8_t font_char_2[] = {
    0x00, 0x3C, 0x66, 0x0C, 0x18, 0x30, 0x60, 0x7E, 0x00, 0x00,
};

/* 字符 '3' - 3 形 */
static const uint8_t font_char_3[] = {
    0x00, 0x3C, 0x66, 0x0C, 0x3C, 0x0C, 0x66, 0x3C, 0x00, 0x00,
};

/* 字符 '4' - 4 形 */
static const uint8_t font_char_4[] = {
    0x00, 0x06, 0x06, 0x06, 0x66, 0x7E, 0x06, 0x06, 0x00, 0x00,
};

/* 字符 '5' - 5 形 */
static const uint8_t font_char_5[] = {
    0x00, 0x7E, 0x60, 0x7C, 0x06, 0x66, 0x66, 0x3C, 0x00, 0x00,
};

/* 字符 '6' - 6 形 */
static const uint8_t font_char_6[] = {
    0x00, 0x3C, 0x60, 0x60, 0x7C, 0x66, 0x66, 0x3C, 0x00, 0x00,
};

/* 字符 '7' - 7 形 */
static const uint8_t font_char_7[] = {
    0x00, 0x7E, 0x06, 0x0C, 0x18, 0x18, 0x18, 0x18, 0x00, 0x00,
};

/* 字符 '8' - 8 形 */
static const uint8_t font_char_8[] = {
    0x00, 0x3C, 0x66, 0x66, 0x3C, 0x66, 0x66, 0x3C, 0x00, 0x00,
};

/* 字符 '9' - 9 形 */
static const uint8_t font_char_9[] = {
    0x00, 0x3C, 0x66, 0x66, 0x3E, 0x06, 0x0C, 0x38, 0x00, 0x00,
};

/* 空格 */
static const uint8_t font_char_space[] = { 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00 };

/* 标点符号 */
static const uint8_t font_char_dot[] = { 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x18 };
static const uint8_t font_char_comma[] = { 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x18 };
static const uint8_t font_char_exclaim[] = { 0x00, 0x18, 0x18, 0x18, 0x18, 0x00, 0x00, 0x18 };
static const uint8_t font_char_colon[] = { 0x00, 0x00, 0x18, 0x00, 0x00, 0x00, 0x18, 0x00 };
static const uint8_t font_char_semicolon[] = { 0x00, 0x00, 0x18, 0x00, 0x00, 0x00, 0x18, 0x18 };
static const uint8_t font_char_dash[] = { 0x00, 0x00, 0x00, 0x3C, 0x00, 0x00, 0x00, 0x00 };
static const uint8_t font_char_underscore[] = { 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x7E };
static const uint8_t font_char_question[] = { 0x00, 0x3C, 0x66, 0x0C, 0x18, 0x00, 0x00, 0x18 };

/* 括号 */
static const uint8_t font_char_lparen[] = { 0x00, 0x06, 0x0C, 0x18, 0x18, 0x30, 0x60, 0x60 };
static const uint8_t font_char_rparen[] = { 0x00, 0x60, 0x60, 0x30, 0x18, 0x18, 0x0C, 0x06 };

/* 加号 */
static const uint8_t font_char_plus[] = { 0x00, 0x00, 0x18, 0x18, 0x7E, 0x18, 0x18, 0x00 };
/* 等号 */
static const uint8_t font_char_equal[] = { 0x00, 0x00, 0x00, 0x3C, 0x00, 0x00, 0x3C, 0x00 };
/* 小于号 */
static const uint8_t font_char_lt[] = { 0x00, 0x06, 0x0C, 0x18, 0x30, 0x18, 0x0C, 0x06 };
/* 大于号 */
static const uint8_t font_char_gt[] = { 0x00, 0x30, 0x18, 0x0C, 0x06, 0x0C, 0x18, 0x30 };
/* 斜杠 */
static const uint8_t font_char_slash[] = { 0x00, 0x60, 0x30, 0x18, 0x0C, 0x06, 0x03, 0x00 };
/* 反斜杠 */
static const uint8_t font_char_backslash[] = { 0x00, 0x00, 0x03, 0x06, 0x0C, 0x18, 0x30, 0x60 };

/* 构建字体字符表 */
static egui_font_char_t font_chars[96];

/**
 * 初始化字体字符表
 * 将上述位图数据映射到字符
 */
static void font_init_chars(void) {
    /* 空格 */
    font_chars[0].width = 5;
    font_chars[0].height = 8;
    font_chars[0].x_offset = 0;
    font_chars[0].y_offset = 0;
    font_chars[0].x_advance = 5;
    font_chars[0].data = font_char_space;

    /* 数字 0-9 */
    font_chars[48].width = 6; font_chars[48].height = 8;
    font_chars[48].x_offset = 0; font_chars[48].y_offset = 0;
    font_chars[48].x_advance = 6; font_chars[48].data = font_char_0;

    font_chars[49].width = 4; font_chars[49].height = 8;
    font_chars[49].x_offset = 1; font_chars[49].y_offset = 0;
    font_chars[49].x_advance = 4; font_chars[49].data = font_char_1;

    font_chars[50].width = 6; font_chars[50].height = 8;
    font_chars[50].x_offset = 0; font_chars[50].y_offset = 0;
    font_chars[50].x_advance = 6; font_chars[50].data = font_char_2;

    font_chars[51].width = 6; font_chars[51].height = 8;
    font_chars[51].x_offset = 0; font_chars[51].y_offset = 0;
    font_chars[51].x_advance = 6; font_chars[51].data = font_char_3;

    font_chars[52].width = 6; font_chars[52].height = 8;
    font_chars[52].x_offset = 0; font_chars[52].y_offset = 0;
    font_chars[52].x_advance = 6; font_chars[52].data = font_char_4;

    font_chars[53].width = 6; font_chars[53].height = 8;
    font_chars[53].x_offset = 0; font_chars[53].y_offset = 0;
    font_chars[53].x_advance = 6; font_chars[53].data = font_char_5;

    font_chars[54].width = 6; font_chars[54].height = 8;
    font_chars[54].x_offset = 0; font_chars[54].y_offset = 0;
    font_chars[54].x_advance = 6; font_chars[54].data = font_char_6;

    font_chars[55].width = 6; font_chars[55].height = 8;
    font_chars[55].x_offset = 0; font_chars[55].y_offset = 0;
    font_chars[55].x_advance = 6; font_chars[55].data = font_char_7;

    font_chars[56].width = 6; font_chars[56].height = 8;
    font_chars[56].x_offset = 0; font_chars[56].y_offset = 0;
    font_chars[56].x_advance = 6; font_chars[56].data = font_char_8;

    font_chars[57].width = 6; font_chars[57].height = 8;
    font_chars[57].x_offset = 0; font_chars[57].y_offset = 0;
    font_chars[57].x_advance = 6; font_chars[57].data = font_char_9;

    /* 字母 A-Z */
    font_chars[65].width = 6; font_chars[65].height = 8;
    font_chars[65].x_offset = 0; font_chars[65].y_offset = 0;
    font_chars[65].x_advance = 6; font_chars[65].data = font_char_A;

    font_chars[66].width = 6; font_chars[66].height = 8;
    font_chars[66].x_offset = 0; font_chars[66].y_offset = 0;
    font_chars[66].x_advance = 6; font_chars[66].data = font_char_B;

    font_chars[67].width = 6; font_chars[67].height = 8;
    font_chars[67].x_offset = 0; font_chars[67].y_offset = 0;
    font_chars[67].x_advance = 6; font_chars[67].data = font_char_C;

    font_chars[68].width = 6; font_chars[68].height = 8;
    font_chars[68].x_offset = 0; font_chars[68].y_offset = 0;
    font_chars[68].x_advance = 6; font_chars[68].data = font_char_D;

    font_chars[69].width = 6; font_chars[69].height = 8;
    font_chars[69].x_offset = 0; font_chars[69].y_offset = 0;
    font_chars[69].x_advance = 6; font_chars[69].data = font_char_E;

    font_chars[70].width = 6; font_chars[70].height = 8;
    font_chars[70].x_offset = 0; font_chars[70].y_offset = 0;
    font_chars[70].x_advance = 6; font_chars[70].data = font_char_F;

    font_chars[71].width = 6; font_chars[71].height = 8;
    font_chars[71].x_offset = 0; font_chars[71].y_offset = 0;
    font_chars[71].x_advance = 6; font_chars[71].data = font_char_G;

    font_chars[72].width = 6; font_chars[72].height = 8;
    font_chars[72].x_offset = 0; font_chars[72].y_offset = 0;
    font_chars[72].x_advance = 6; font_chars[72].data = font_char_H;

    font_chars[73].width = 4; font_chars[73].height = 8;
    font_chars[73].x_offset = 1; font_chars[73].y_offset = 0;
    font_chars[73].x_advance = 4; font_chars[73].data = font_char_I;

    font_chars[74].width = 6; font_chars[74].height = 8;
    font_chars[74].x_offset = 0; font_chars[74].y_offset = 0;
    font_chars[74].x_advance = 6; font_chars[74].data = font_char_L;

    font_chars[75].width = 6; font_chars[75].height = 8;
    font_chars[75].x_offset = 0; font_chars[75].y_offset = 0;
    font_chars[75].x_advance = 6; font_chars[75].data = font_char_M;

    font_chars[76].width = 6; font_chars[76].height = 8;
    font_chars[76].x_offset = 0; font_chars[76].y_offset = 0;
    font_chars[76].x_advance = 6; font_chars[76].data = font_char_N;

    font_chars[77].width = 6; font_chars[77].height = 8;
    font_chars[77].x_offset = 0; font_chars[77].y_offset = 0;
    font_chars[77].x_advance = 6; font_chars[77].data = font_char_O;

    font_chars[78].width = 6; font_chars[78].height = 8;
    font_chars[78].x_offset = 0; font_chars[78].y_offset = 0;
    font_chars[78].x_advance = 6; font_chars[78].data = font_char_P;

    font_chars[79].width = 6; font_chars[79].height = 8;
    font_chars[79].x_offset = 0; font_chars[79].y_offset = 0;
    font_chars[79].x_advance = 6; font_chars[79].data = font_char_O; /* 复用 O */
    font_chars[79].data = font_char_O;

    font_chars[80].width = 6; font_chars[80].height = 8;
    font_chars[80].x_offset = 0; font_chars[80].y_offset = 0;
    font_chars[80].x_advance = 6; font_chars[80].data = font_char_R;

    font_chars[81].width = 6; font_chars[81].height = 8;
    font_chars[81].x_offset = 0; font_chars[81].y_offset = 0;
    font_chars[81].x_advance = 6; font_chars[81].data = font_char_S;

    font_chars[82].width = 6; font_chars[82].height = 8;
    font_chars[82].x_offset = 0; font_chars[82].y_offset = 0;
    font_chars[82].x_advance = 6; font_chars[82].data = font_char_T;

    font_chars[83].width = 6; font_chars[83].height = 8;
    font_chars[83].x_offset = 0; font_chars[83].y_offset = 0;
    font_chars[83].x_advance = 6; font_chars[83].data = font_char_U;

    font_chars[84].width = 6; font_chars[84].height = 8;
    font_chars[84].x_offset = 0; font_chars[84].y_offset = 0;
    font_chars[84].x_advance = 6; font_chars[84].data = font_char_X; /* 复用 X */
    font_chars[84].data = font_char_X;

    font_chars[85].width = 6; font_chars[85].height = 8;
    font_chars[85].x_offset = 0; font_chars[85].y_offset = 0;
    font_chars[85].x_advance = 6; font_chars[85].data = font_char_Y;

    font_chars[86].width = 6; font_chars[86].height = 8;
    font_chars[86].x_offset = 0; font_chars[86].y_offset = 0;
    font_chars[86].x_advance = 6; font_chars[86].data = font_char_Z;

    /* 标点符号 */
    font_chars[46].width = 2; font_chars[46].height = 4;
    font_chars[46].x_offset = 1; font_chars[46].y_offset = 4;
    font_chars[46].x_advance = 3; font_chars[46].data = font_char_dot;

    font_chars[33].width = 4; font_chars[33].height = 8;
    font_chars[33].x_offset = 1; font_chars[33].y_offset = 0;
    font_chars[33].x_advance = 4; font_chars[33].data = font_char_exclaim;

    font_chars[58].width = 4; font_chars[58].height = 8;
    font_chars[58].x_offset = 1; font_chars[58].y_offset = 0;
    font_chars[58].x_advance = 4; font_chars[58].data = font_char_colon;

    font_chars[59].width = 4; font_chars[59].height = 8;
    font_chars[59].x_offset = 1; font_chars[59].y_offset = 0;
    font_chars[59].x_advance = 4; font_chars[59].data = font_char_semicolon;

    font_chars[45].width = 6; font_chars[45].height = 2;
    font_chars[45].x_offset = 0; font_chars[45].y_offset = 3;
    font_chars[45].x_advance = 6; font_chars[45].data = font_char_dash;

    font_chars[43].width = 6; font_chars[43].height = 4;
    font_chars[43].x_offset = 0; font_chars[43].y_offset = 2;
    font_chars[43].x_advance = 6; font_chars[43].data = font_char_plus;

    font_chars[61].width = 6; font_chars[61].height = 2;
    font_chars[61].x_offset = 0; font_chars[61].y_offset = 3;
    font_chars[61].x_advance = 6; font_chars[61].data = font_char_equal;

    font_chars[40].width = 4; font_chars[40].height = 8;
    font_chars[40].x_offset = 3; font_chars[40].y_offset = 0;
    font_chars[40].x_advance = 4; font_chars[40].data = font_char_lparen;

    font_chars[41].width = 4; font_chars[41].height = 8;
    font_chars[41].x_offset = 0; font_chars[41].y_offset = 0;
    font_chars[41].x_advance = 4; font_chars[41].data = font_char_rparen;

    font_chars[60].width = 6; font_chars[60].height = 8;
    font_chars[60].x_offset = 0; font_chars[60].y_offset = 0;
    font_chars[60].x_advance = 6; font_chars[60].data = font_char_lt;

    font_chars[62].width = 6; font_chars[62].height = 8;
    font_chars[62].x_offset = 0; font_chars[62].y_offset = 0;
    font_chars[62].x_advance = 6; font_chars[62].data = font_char_gt;

    font_chars[47].width = 6; font_chars[47].height = 8;
    font_chars[47].x_offset = 0; font_chars[47].y_offset = 0;
    font_chars[47].x_advance = 6; font_chars[47].data = font_char_slash;
}

/* 单例字体实例 / Singleton font instance */
static egui_font_t builtin_font;
static bool font_initialized = false;

/**
 * 获取内置字体
 * 首次调用时初始化字体字符表
 */
const egui_font_t *egui_font_get_builtin(void) {
    if (!font_initialized) {
        font_init_chars();
        builtin_font.char_height = 8;
        builtin_font.baseline = 6;
        builtin_font.max_width = 6;
        memcpy(builtin_font.chars, font_chars, sizeof(font_chars));
        font_initialized = true;
    }
    return &builtin_font;
}
