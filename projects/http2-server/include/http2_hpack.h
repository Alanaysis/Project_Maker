#pragma once
/**
 * @file http2_hpack.h
 * @brief HPACK 头部压缩实现
 *
 * HPACK 是 HTTP/2 专用的头部压缩算法，主要特性：
 * - 静态表：预定义的常用头部字段
 * - 动态表：连接期间动态添加的头部字段
 * - 霍夫曼编码：高效的字符串编码
 *
 * 压缩原理：
 * 1. 索引表示：使用索引引用已存在的头部字段
 * 2. 字面量表示：直接传输头部字段
 * 3. 霍夫曼编码：使用变长编码压缩字符串
 */

#include <cstdint>
#include <string>
#include <vector>
#include <map>
#include <list>
#include <utility>

namespace http2 {

// 头部字段结构
struct HeaderField {
    std::string name;
    std::string value;

    bool operator==(const HeaderField& other) const {
        return name == other.name && value == other.value;
    }
};

// HPACK 编码器
class HPACKEncoder {
public:
    HPACKEncoder();

    // 编码头部列表
    std::vector<uint8_t> encode(const std::vector<HeaderField>& headers);

    // 解码头部列表
    std::vector<HeaderField> decode(const uint8_t* data, size_t length);

    // 设置最大动态表大小
    void set_max_dynamic_table_size(size_t max_size);

private:
    // 静态表
    static const std::vector<HeaderField> static_table_;

    // 动态表
    std::list<HeaderField> dynamic_table_;
    size_t dynamic_table_size_ = 0;
    size_t max_dynamic_table_size_ = 4096;

    // 查找头部字段在表中的索引
    int find_index(const HeaderField& field) const;

    // 更新动态表
    void add_to_dynamic_table(const HeaderField& field);

    // 编码整数
    std::vector<uint8_t> encode_integer(uint32_t value, uint8_t prefix);

    // 解码整数
    uint32_t decode_integer(const uint8_t*& data, const uint8_t* end, uint8_t prefix);

    // 编码字符串（带霍夫曼编码）
    std::vector<uint8_t> encode_string(const std::string& str);

    // 解码字符串
    std::string decode_string(const uint8_t*& data, const uint8_t* end);

    // 霍夫曼编码
    std::vector<uint8_t> huffman_encode(const std::string& str) const;

    // 霍夫曼解码
    std::string huffman_decode(const uint8_t* data, size_t length) const;
};

// 霍夫曼编码表
struct HuffmanCode {
    uint32_t code;
    uint8_t bits;
};

// 静态霍夫曼编码表（部分示例，完整表更长）
static const HuffmanCode huffman_codes[] = {
    {0x1ff8, 13},    // 0
    {0x7fffd8, 23},  // 1
    {0xfffffe2, 28}, // 2
    {0xfffffe3, 28}, // 3
    {0xfffffe4, 28}, // 4
    {0xfffffe5, 28}, // 5
    {0xfffffe6, 28}, // 6
    {0xfffffe7, 28}, // 7
    {0xfffffe8, 28}, // 8
    {0xffffea, 24},  // 9
    {0x3ffffffc, 30}, // 10
    {0xfffffe9, 28}, // 11
    {0xfffffea, 28}, // 12
    {0x3ffffffd, 30}, // 13
    {0xfffffeb, 28}, // 14
    {0xfffffec, 28}, // 15
    {0xfffffed, 28}, // 16
    {0xfffffee, 28}, // 17
    {0xfffffef, 28}, // 18
    {0xffffff0, 28}, // 19
    {0xffffff1, 28}, // 20
    {0xffffff2, 28}, // 21
    {0x3ffffffe, 30}, // 22
    {0xffffff3, 28}, // 23
    {0xffffff4, 28}, // 24
    {0xffffff5, 28}, // 25
    {0xffffff6, 28}, // 26
    {0xffffff7, 28}, // 27
    {0xffffff8, 28}, // 28
    {0xffffff9, 28}, // 29
    {0xffffffa, 28}, // 30
    {0xffffffb, 28}, // 31
    {0x14, 6},       // ' ' (32)
    {0x3f8, 10},     // '!' (33)
    {0x3f9, 10},     // '"' (34)
    {0xffa, 12},     // '#' (35)
    {0x1ff9, 13},    // '$' (36)
    {0x15, 6},       // '%' (37)
    {0xf8, 8},       // '&' (38)
    {0x7fa, 11},     // ''' (39)
    {0x3fa, 10},     // '(' (40)
    {0x3fb, 10},     // ')' (41)
    {0xf9, 8},       // '*' (42)
    {0x7fb, 11},     // '+' (43)
    {0xfa, 8},       // ',' (44)
    {0x16, 6},       // '-' (45)
    {0x17, 6},       // '.' (46)
    {0x18, 6},       // '/' (47)
    {0x0, 5},        // '0' (48)
    {0x1, 5},        // '1' (49)
    {0x2, 5},        // '2' (50)
    {0x3, 5},        // '3' (51)
    {0x4, 5},        // '4' (52)
    {0x5, 5},        // '5' (53)
    {0x6, 5},        // '6' (54)
    {0x7, 5},        // '7' (55)
    {0x8, 5},        // '8' (56)
    {0x9, 5},        // '9' (57)
    {0x7fc, 11},     // ':' (58)
    {0xfb, 8},       // ';' (59)
    {0x7ffc, 15},    // '<' (60)
    {0x1ffc, 13},    // '=' (61)
    {0x3ffc, 14},    // '>' (62)
    {0x1ffa, 13},    // '?' (63)
};

} // namespace http2
