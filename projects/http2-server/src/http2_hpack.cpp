/**
 * @file http2_hpack.cpp
 * @brief HPACK 头部压缩实现
 */

#include "http2_hpack.h"
#include <algorithm>
#include <stdexcept>

namespace http2 {

// 静态表定义
const std::vector<HeaderField> HPACKEncoder::static_table_ = {
    {"", ""},                                    // 0: 空
    {":authority", ""},                          // 1
    {":method", "GET"},                          // 2
    {":method", "POST"},                         // 3
    {":path", "/"},                              // 4
    {":path", "/index.html"},                    // 5
    {":scheme", "http"},                         // 6
    {":scheme", "https"},                        // 7
    {":status", "200"},                          // 8
    {":status", "204"},                          // 9
    {":status", "206"},                          // 10
    {":status", "304"},                          // 11
    {":status", "400"},                          // 12
    {":status", "404"},                          // 13
    {":status", "500"},                          // 14
    {"accept-charset", ""},                      // 15
    {"accept-encoding", "gzip, deflate"},        // 16
    {"accept-language", ""},                     // 17
    {"accept-ranges", ""},                       // 18
    {"accept", ""},                              // 19
    {"access-control-allow-origin", ""},         // 20
    {"age", ""},                                 // 21
    {"allow", ""},                               // 22
    {"authorization", ""},                       // 23
    {"cache-control", ""},                       // 24
    {"content-disposition", ""},                 // 25
    {"content-encoding", ""},                    // 26
    {"content-language", ""},                    // 27
    {"content-length", ""},                      // 28
    {"content-location", ""},                    // 29
    {"content-range", ""},                       // 30
    {"content-type", ""},                        // 31
    {"cookie", ""},                              // 32
    {"date", ""},                                // 33
    {"etag", ""},                                // 34
    {"expect", ""},                              // 35
    {"expires", ""},                             // 36
    {"from", ""},                                // 37
    {"host", ""},                                // 38
    {"if-match", ""},                            // 39
    {"if-modified-since", ""},                   // 40
    {"if-none-match", ""},                       // 41
    {"if-range", ""},                            // 42
    {"if-unmodified-since", ""},                 // 43
    {"last-modified", ""},                       // 44
    {"link", ""},                                // 45
    {"location", ""},                            // 46
    {"max-forwards", ""},                        // 47
    {"proxy-authenticate", ""},                  // 48
    {"proxy-authorization", ""},                 // 49
    {"range", ""},                               // 50
    {"referer", ""},                             // 51
    {"refresh", ""},                             // 52
    {"retry-after", ""},                         // 53
    {"server", ""},                              // 54
    {"set-cookie", ""},                          // 55
    {"strict-transport-security", ""},           // 56
    {"transfer-encoding", ""},                   // 57
    {"user-agent", ""},                          // 58
    {"vary", ""},                                // 59
    {"via", ""},                                 // 60
    {"www-authenticate", ""}                     // 61
};

HPACKEncoder::HPACKEncoder() {}

std::vector<uint8_t> HPACKEncoder::encode(const std::vector<HeaderField>& headers) {
    std::vector<uint8_t> result;

    for (const auto& header : headers) {
        int index = find_index(header);

        if (index > 0 && header.value == (index < static_cast<int>(static_table_.size()) ?
            static_table_[index].value : "")) {
            // 索引头部字段
            auto encoded = encode_integer(index, 7);
            encoded[0] |= 0x80;  // 设置最高位
            result.insert(result.end(), encoded.begin(), encoded.end());
        } else if (index > 0) {
            // 索引名称，字面量值
            auto encoded = encode_integer(index, 6);
            encoded[0] |= 0x40;  // 设置次高位
            result.insert(result.end(), encoded.begin(), encoded.end());

            auto encoded_value = encode_string(header.value);
            result.insert(result.end(), encoded_value.begin(), encoded_value.end());

            add_to_dynamic_table(header);
        } else {
            // 字面量名称和值
            result.push_back(0x40);  // 带索引的字面量
            auto encoded_name = encode_string(header.name);
            result.insert(result.end(), encoded_name.begin(), encoded_name.end());

            auto encoded_value = encode_string(header.value);
            result.insert(result.end(), encoded_value.begin(), encoded_value.end());

            add_to_dynamic_table(header);
        }
    }

    return result;
}

std::vector<HeaderField> HPACKEncoder::decode(const uint8_t* data, size_t length) {
    std::vector<HeaderField> headers;
    const uint8_t* pos = data;
    const uint8_t* end = data + length;

    while (pos < end) {
        uint8_t first = *pos;

        if (first & 0x80) {
            // 索引头部字段
            uint32_t index = decode_integer(pos, end, 7);
            if (index == 0 || index > static_table_.size() + dynamic_table_.size()) {
                throw std::runtime_error("Invalid HPACK index");
            }

            if (index <= static_table_.size()) {
                headers.push_back(static_table_[index]);
            } else {
                auto it = dynamic_table_.begin();
                std::advance(it, index - static_table_.size() - 1);
                headers.push_back(*it);
            }
        } else if (first & 0x40) {
            // 带索引的字面量
            uint32_t index = decode_integer(pos, end, 6);
            HeaderField field;

            if (index > 0) {
                if (index <= static_table_.size()) {
                    field.name = static_table_[index].name;
                } else {
                    auto it = dynamic_table_.begin();
                    std::advance(it, index - static_table_.size() - 1);
                    field.name = it->name;
                }
            } else {
                field.name = decode_string(pos, end);
            }

            field.value = decode_string(pos, end);
            headers.push_back(field);
            add_to_dynamic_table(field);
        } else if (first & 0x20) {
            // 动态表大小更新
            uint32_t new_size = decode_integer(pos, end, 5);
            if (new_size <= max_dynamic_table_size_) {
                while (dynamic_table_size_ > new_size && !dynamic_table_.empty()) {
                    dynamic_table_size_ -= dynamic_table_.back().name.size() + dynamic_table_.back().value.size() + 32;
                    dynamic_table_.pop_back();
                }
            }
        } else {
            // 不索引的字面量
            uint32_t index = 0;
            if (first & 0x10) {
                index = decode_integer(pos, end, 4);
            } else {
                index = decode_integer(pos, end, 4);
            }

            HeaderField field;
            if (index > 0) {
                if (index <= static_table_.size()) {
                    field.name = static_table_[index].name;
                } else {
                    auto it = dynamic_table_.begin();
                    std::advance(it, index - static_table_.size() - 1);
                    field.name = it->name;
                }
            } else {
                field.name = decode_string(pos, end);
            }

            field.value = decode_string(pos, end);
            headers.push_back(field);
        }
    }

    return headers;
}

void HPACKEncoder::set_max_dynamic_table_size(size_t max_size) {
    max_dynamic_table_size_ = max_size;
    while (dynamic_table_size_ > max_size && !dynamic_table_.empty()) {
        dynamic_table_size_ -= dynamic_table_.back().name.size() + dynamic_table_.back().value.size() + 32;
        dynamic_table_.pop_back();
    }
}

int HPACKEncoder::find_index(const HeaderField& field) const {
    // 先查静态表
    for (size_t i = 1; i < static_table_.size(); ++i) {
        if (static_table_[i].name == field.name) {
            if (static_table_[i].value == field.value || field.value.empty()) {
                return i;
            }
        }
    }

    // 再查动态表
    size_t index = static_table_.size();
    for (const auto& entry : dynamic_table_) {
        ++index;
        if (entry.name == field.name && entry.value == field.value) {
            return index;
        }
    }

    return 0;
}

void HPACKEncoder::add_to_dynamic_table(const HeaderField& field) {
    size_t entry_size = field.name.size() + field.value.size() + 32;

    while (dynamic_table_size_ + entry_size > max_dynamic_table_size_ && !dynamic_table_.empty()) {
        dynamic_table_size_ -= dynamic_table_.back().name.size() + dynamic_table_.back().value.size() + 32;
        dynamic_table_.pop_back();
    }

    if (entry_size <= max_dynamic_table_size_) {
        dynamic_table_.push_front(field);
        dynamic_table_size_ += entry_size;
    }
}

std::vector<uint8_t> HPACKEncoder::encode_integer(uint32_t value, uint8_t prefix) {
    std::vector<uint8_t> result;
    uint32_t max_value = (1 << prefix) - 1;

    if (value < max_value) {
        result.push_back(value & 0xFF);
    } else {
        result.push_back(max_value & 0xFF);
        value -= max_value;
        while (value >= 128) {
            result.push_back((value & 0x7F) | 0x80);
            value >>= 7;
        }
        result.push_back(value & 0xFF);
    }

    return result;
}

uint32_t HPACKEncoder::decode_integer(const uint8_t*& data, const uint8_t* end, uint8_t prefix) {
    uint32_t max_value = (1 << prefix) - 1;
    uint32_t value = (*data) & max_value;
    ++data;

    if (value == max_value) {
        uint32_t shift = 0;
        while (data < end) {
            uint8_t byte = *data;
            ++data;
            value += (byte & 0x7F) << shift;
            shift += 7;
            if (!(byte & 0x80)) {
                break;
            }
        }
    }

    return value;
}

std::vector<uint8_t> HPACKEncoder::encode_string(const std::string& str) {
    std::vector<uint8_t> result;

    // 尝试霍夫曼编码
    auto huffman_encoded = huffman_encode(str);
    if (huffman_encoded.size() < str.size()) {
        // 使用霍夫曼编码
        auto length = encode_integer(huffman_encoded.size(), 7);
        length[0] |= 0x80;  // 设置霍夫曼标志
        result.insert(result.end(), length.begin(), length.end());
        result.insert(result.end(), huffman_encoded.begin(), huffman_encoded.end());
    } else {
        // 使用原始字符串
        auto length = encode_integer(str.size(), 7);
        result.insert(result.end(), length.begin(), length.end());
        result.insert(result.end(), str.begin(), str.end());
    }

    return result;
}

std::string HPACKEncoder::decode_string(const uint8_t*& data, const uint8_t* end) {
    bool is_huffman = (*data & 0x80) != 0;
    uint32_t length = decode_integer(data, end, 7);

    if (data + length > end) {
        throw std::runtime_error("Invalid HPACK string length");
    }

    std::string result;
    if (is_huffman) {
        result = huffman_decode(data, length);
    } else {
        result = std::string(reinterpret_cast<const char*>(data), length);
    }

    data += length;
    return result;
}

std::vector<uint8_t> HPACKEncoder::huffman_encode(const std::string& str) const {
    std::vector<uint8_t> result;
    uint32_t current = 0;
    int bits = 0;

    for (char c : str) {
        uint8_t ch = static_cast<uint8_t>(c);
        if (ch < sizeof(huffman_codes) / sizeof(huffman_codes[0])) {
            current = (current << huffman_codes[ch].bits) | huffman_codes[ch].code;
            bits += huffman_codes[ch].bits;

            while (bits >= 8) {
                bits -= 8;
                result.push_back((current >> bits) & 0xFF);
            }
        }
    }

    // 填充剩余位
    if (bits > 0) {
        current = (current << (8 - bits)) | ((1 << (8 - bits)) - 1);
        result.push_back(current & 0xFF);
    }

    return result;
}

std::string HPACKEncoder::huffman_decode(const uint8_t* data, size_t length) const {
    std::string result;
    uint32_t current = 0;
    int bits = 0;

    for (size_t i = 0; i < length; ++i) {
        current = (current << 8) | data[i];
        bits += 8;

        while (bits > 0) {
            // 查找匹配的编码
            bool found = false;
            for (size_t j = 0; j < sizeof(huffman_codes) / sizeof(huffman_codes[0]); ++j) {
                if (huffman_codes[j].bits <= bits) {
                    uint32_t mask = (1 << huffman_codes[j].bits) - 1;
                    if ((current >> (bits - huffman_codes[j].bits)) == huffman_codes[j].code) {
                        result += static_cast<char>(j);
                        bits -= huffman_codes[j].bits;
                        found = true;
                        break;
                    }
                }
            }
            if (!found) break;
        }
    }

    return result;
}

} // namespace http2
