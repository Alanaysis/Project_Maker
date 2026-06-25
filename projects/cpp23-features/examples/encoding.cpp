/**
 * @file encoding.cpp
 * @brief C++23 字符编码转换示例
 *
 * C++23 引入了新的字符编码转换工具，简化了不同编码之间的转换。
 *
 * 主要特点：
 * - 支持 UTF-8、UTF-16、UTF-32 编码
 * - 提供编码转换函数
 * - 支持宽字符
 * - 简化国际化处理
 *
 * 编译命令：
 * g++ -std=c++23 -o encoding encoding.cpp
 */

#include <iostream>
#include <string>
#include <string_view>
#include <locale>
#include <codecvt>
#include <iomanip>

// ========== 1. 基本编码类型 ==========

void basic_encoding_types() {
    std::cout << "=== 基本编码类型 ===" << std::endl;

    // UTF-8 字符串
    std::string utf8_str = u8"Hello, 世界!";
    std::cout << "UTF-8: " << utf8_str << std::endl;
    std::cout << "UTF-8 size: " << utf8_str.size() << " bytes" << std::endl;

    // UTF-16 字符串
    std::u16string utf16_str = u"Hello, 世界!";
    std::cout << "UTF-16 size: " << utf16_str.size() << " code units" << std::endl;

    // UTF-32 字符串
    std::u32string utf32_str = U"Hello, 世界!";
    std::cout << "UTF-32 size: " << utf32_str.size() << " code points" << std::endl;

    // 宽字符字符串
    std::wstring wide_str = L"Hello, 世界!";
    std::cout << "Wide string size: " << wide_str.size() << " wide chars" << std::endl;
}

// ========== 2. UTF-8 编码详解 ==========

void utf8_details() {
    std::cout << "\n=== UTF-8 编码详解 ===" << std::endl;

    // UTF-8 编码的字符
    std::string str = u8"A中𝄞";  // A (1 byte), 中 (3 bytes), 𝄞 (4 bytes)

    std::cout << "String: " << str << std::endl;
    std::cout << "Byte length: " << str.size() << std::endl;

    // 显示每个字节
    std::cout << "Bytes: ";
    for (unsigned char c : str) {
        std::cout << std::hex << std::setw(2) << std::setfill('0')
                  << static_cast<int>(c) << " ";
    }
    std::cout << std::dec << std::endl;
}

// ========== 3. 字符计数 ==========

// 计算 UTF-8 字符数
size_t count_utf8_chars(const std::string& str) {
    size_t count = 0;
    for (size_t i = 0; i < str.size(); ++i) {
        // 检查是否是 UTF-8 序列的开始字节
        if ((str[i] & 0xC0) != 0x80) {
            ++count;
        }
    }
    return count;
}

void character_counting() {
    std::cout << "\n=== 字符计数 ===" << std::endl;

    std::string str = u8"Hello, 世界!";
    std::cout << "String: " << str << std::endl;
    std::cout << "Byte size: " << str.size() << std::endl;
    std::cout << "Character count: " << count_utf8_chars(str) << std::endl;
}

// ========== 4. 编码验证 ==========

// 验证 UTF-8 编码
bool is_valid_utf8(const std::string& str) {
    size_t i = 0;
    while (i < str.size()) {
        unsigned char c = str[i];
        int bytes = 0;

        if (c <= 0x7F) {
            bytes = 1;
        } else if ((c & 0xE0) == 0xC0) {
            bytes = 2;
        } else if ((c & 0xF0) == 0xE0) {
            bytes = 3;
        } else if ((c & 0xF8) == 0xF0) {
            bytes = 4;
        } else {
            return false;
        }

        // 检查后续字节
        for (int j = 1; j < bytes; ++j) {
            if (i + j >= str.size() || (str[i + j] & 0xC0) != 0x80) {
                return false;
            }
        }

        i += bytes;
    }
    return true;
}

void encoding_validation() {
    std::cout << "\n=== 编码验证 ===" << std::endl;

    std::string valid_str = u8"Hello, 世界!";
    std::cout << "Valid UTF-8: " << (is_valid_utf8(valid_str) ? "yes" : "no") << std::endl;

    // 无效的 UTF-8 序列
    std::string invalid_str = "Hello\xFF\xFE";
    std::cout << "Invalid UTF-8: " << (is_valid_utf8(invalid_str) ? "yes" : "no") << std::endl;
}

// ========== 5. 实际应用：国际化文本 ==========

void internationalization() {
    std::cout << "\n=== 实际应用：国际化文本 ===" << std::endl;

    // 不同语言的文本
    std::string english = u8"Hello, World!";
    std::string chinese = u8"你好，世界！";
    std::string japanese = u8"こんにちは、世界！";
    std::string korean = u8"안녕하세요, 세계!";

    std::cout << "English: " << english << std::endl;
    std::cout << "Chinese: " << chinese << std::endl;
    std::cout << "Japanese: " << japanese << std::endl;
    std::cout << "Korean: " << korean << std::endl;

    // 字符数统计
    std::cout << "\nCharacter counts:" << std::endl;
    std::cout << "  English: " << count_utf8_chars(english) << std::endl;
    std::cout << "  Chinese: " << count_utf8_chars(chinese) << std::endl;
    std::cout << "  Japanese: " << count_utf8_chars(japanese) << std::endl;
    std::cout << "  Korean: " << count_utf8_chars(korean) << std::endl;
}

// ========== 6. 实际应用：URL 编码 ==========

// URL 编码
std::string url_encode(const std::string& str) {
    std::string result;
    for (unsigned char c : str) {
        if (std::isalnum(c) || c == '-' || c == '_' || c == '.' || c == '~') {
            result += c;
        } else {
            result += '%';
            result += "0123456789ABCDEF"[c >> 4];
            result += "0123456789ABCDEF"[c & 0xF];
        }
    }
    return result;
}

void url_encoding() {
    std::cout << "\n=== 实际应用：URL 编码 ===" << std::endl;

    std::string url = u8"https://example.com/搜索?q=你好";
    std::cout << "Original URL: " << url << std::endl;
    std::cout << "Encoded URL: " << url_encode(url) << std::endl;
}

// ========== 7. 实际应用：Base64 编码 ==========

// Base64 编码表
const std::string base64_chars =
    "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    "abcdefghijklmnopqrstuvwxyz"
    "0123456789+/";

// Base64 编码
std::string base64_encode(const std::string& str) {
    std::string result;
    int i = 0;
    int j = 0;
    unsigned char char_array_3[3];
    unsigned char char_array_4[4];

    for (unsigned char c : str) {
        char_array_3[i++] = c;
        if (i == 3) {
            char_array_4[0] = (char_array_3[0] & 0xfc) >> 2;
            char_array_4[1] = ((char_array_3[0] & 0x03) << 4) + ((char_array_3[1] & 0xf0) >> 4);
            char_array_4[2] = ((char_array_3[1] & 0x0f) << 2) + ((char_array_3[2] & 0xc0) >> 6);
            char_array_4[3] = char_array_3[2] & 0x3f;

            for (i = 0; i < 4; i++) {
                result += base64_chars[char_array_4[i]];
            }
            i = 0;
        }
    }

    if (i) {
        for (j = i; j < 3; j++) {
            char_array_3[j] = '\0';
        }

        char_array_4[0] = (char_array_3[0] & 0xfc) >> 2;
        char_array_4[1] = ((char_array_3[0] & 0x03) << 4) + ((char_array_3[1] & 0xf0) >> 4);
        char_array_4[2] = ((char_array_3[1] & 0x0f) << 2) + ((char_array_3[2] & 0xc0) >> 6);

        for (j = 0; j < i + 1; j++) {
            result += base64_chars[char_array_4[j]];
        }

        while (i++ < 3) {
            result += '=';
        }
    }

    return result;
}

void base64_encoding() {
    std::cout << "\n=== 实际应用：Base64 编码 ===" << std::endl;

    std::string text = "Hello, World!";
    std::cout << "Original: " << text << std::endl;
    std::cout << "Base64: " << base64_encode(text) << std::endl;

    // 中文 Base64
    std::string chinese = u8"你好";
    std::cout << "\nOriginal: " << chinese << std::endl;
    std::cout << "Base64: " << base64_encode(chinese) << std::endl;
}

// ========== 8. 实际应用：HTML 实体编码 ==========

// HTML 实体编码
std::string html_encode(const std::string& str) {
    std::string result;
    for (char c : str) {
        switch (c) {
            case '&':  result += "&amp;"; break;
            case '<':  result += "&lt;"; break;
            case '>':  result += "&gt;"; break;
            case '"':  result += "&quot;"; break;
            case '\'': result += "&#39;"; break;
            default:   result += c; break;
        }
    }
    return result;
}

void html_encoding() {
    std::cout << "\n=== 实际应用：HTML 实体编码 ===" << std::endl;

    std::string html = "<div class=\"test\">Hello & World</div>";
    std::cout << "Original: " << html << std::endl;
    std::cout << "Encoded: " << html_encode(html) << std::endl;
}

// ========== 9. 实际应用：JSON 编码 ==========

// JSON 字符串编码
std::string json_encode(const std::string& str) {
    std::string result = "\"";
    for (char c : str) {
        switch (c) {
            case '"':  result += "\\\""; break;
            case '\\': result += "\\\\"; break;
            case '\b': result += "\\b"; break;
            case '\f': result += "\\f"; break;
            case '\n': result += "\\n"; break;
            case '\r': result += "\\r"; break;
            case '\t': result += "\\t"; break;
            default:   result += c; break;
        }
    }
    result += "\"";
    return result;
}

void json_encoding() {
    std::cout << "\n=== 实际应用：JSON 编码 ===" << std::endl;

    std::string text = "Hello\nWorld\t\"Test\"";
    std::cout << "Original: " << text << std::endl;
    std::cout << "JSON: " << json_encode(text) << std::endl;
}

// ========== 10. 实际应用：文件编码检测 ==========

// 简单的编码检测
std::string detect_encoding(const std::string& data) {
    if (data.size() >= 3 &&
        static_cast<unsigned char>(data[0]) == 0xEF &&
        static_cast<unsigned char>(data[1]) == 0xBB &&
        static_cast<unsigned char>(data[2]) == 0xBF) {
        return "UTF-8 with BOM";
    }

    if (data.size() >= 2 &&
        static_cast<unsigned char>(data[0]) == 0xFF &&
        static_cast<unsigned char>(data[1]) == 0xFE) {
        return "UTF-16 LE";
    }

    if (data.size() >= 2 &&
        static_cast<unsigned char>(data[0]) == 0xFE &&
        static_cast<unsigned char>(data[1]) == 0xFF) {
        return "UTF-16 BE";
    }

    // 检查是否是有效的 UTF-8
    if (is_valid_utf8(data)) {
        return "UTF-8";
    }

    return "Unknown";
}

void encoding_detection() {
    std::cout << "\n=== 实际应用：文件编码检测 ===" << std::endl;

    std::string utf8 = u8"Hello, 世界!";
    std::cout << "UTF-8 string: " << detect_encoding(utf8) << std::endl;

    // UTF-8 with BOM
    std::string utf8_bom = "\xEF\xBB\xBF" + utf8;
    std::cout << "UTF-8 with BOM: " << detect_encoding(utf8_bom) << std::endl;
}

int main() {
    std::cout << "C++23 字符编码转换示例\n" << std::endl;

    basic_encoding_types();
    utf8_details();
    character_counting();
    encoding_validation();
    internationalization();
    url_encoding();
    base64_encoding();
    html_encoding();
    json_encoding();
    encoding_detection();

    return 0;
}
