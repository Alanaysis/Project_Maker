#pragma once
/**
 * @file serialization.hpp
 * @brief 编译期序列化框架
 *
 * 使用模板元编程实现类型安全的序列化框架。
 * 在编译期确定序列化/反序列化逻辑。
 *
 * 核心特性：
 *   - 自动字段检测
 *   - 编译期格式生成
 *   - 类型安全
 *   - 支持多种格式 (JSON, Binary)
 */

#include <string>
#include <sstream>
#include <type_traits>
#include <vector>
#include <map>
#include <optional>
#include <cstring>

namespace tmp {

// ============================================================================
// 1. 序列化器基类
// ============================================================================

/**
 * @brief 序列化格式标签
 */
struct JsonFormat {};
struct BinaryFormat {};
struct CsvFormat {};

/**
 * @brief 序列化器 - 将对象转换为字符串
 */
template <typename Format = JsonFormat>
class Serializer {
    std::ostringstream ss_;
    bool first_ = true;

public:
    void begin_object() {
        if constexpr (std::is_same_v<Format, JsonFormat>) {
            ss_ << "{";
            first_ = true;
        }
    }

    void end_object() {
        if constexpr (std::is_same_v<Format, JsonFormat>) {
            ss_ << "}";
        }
    }

    void begin_array() {
        if constexpr (std::is_same_v<Format, JsonFormat>) {
            ss_ << "[";
            first_ = true;
        }
    }

    void end_array() {
        if constexpr (std::is_same_v<Format, JsonFormat>) {
            ss_ << "]";
        }
    }

    template <typename T>
    void write_field(const std::string& name, const T& value) {
        if constexpr (std::is_same_v<Format, JsonFormat>) {
            if (!first_) ss_ << ",";
            first_ = false;
            ss_ << "\"" << name << "\":";
            write_value(value);
        }
    }

    template <typename T>
    void write_value(const T& value) {
        if constexpr (std::is_same_v<Format, JsonFormat>) {
            if constexpr (std::is_same_v<T, std::string>) {
                ss_ << "\"" << value << "\"";
            } else if constexpr (std::is_same_v<T, bool>) {
                ss_ << (value ? "true" : "false");
            } else if constexpr (std::is_arithmetic_v<T>) {
                ss_ << value;
            }
        }
    }

    std::string str() const { return ss_.str(); }
};

// ============================================================================
// 2. 反序列化器
// ============================================================================

/**
 * @brief 简单的 JSON 反序列化器
 */
class Deserializer {
    std::string data_;
    std::size_t pos_ = 0;

public:
    explicit Deserializer(const std::string& data) : data_(data) {}

    void skip_whitespace() {
        while (pos_ < data_.size() && std::isspace(data_[pos_])) ++pos_;
    }

    char peek() {
        skip_whitespace();
        return pos_ < data_.size() ? data_[pos_] : '\0';
    }

    char advance() {
        skip_whitespace();
        return pos_ < data_.size() ? data_[pos_++] : '\0';
    }

    bool expect(char c) {
        char got = advance();
        return got == c;
    }

    std::string read_string() {
        if (advance() != '"') return "";
        std::string result;
        while (pos_ < data_.size() && data_[pos_] != '"') {
            if (data_[pos_] == '\\') {
                ++pos_;
                if (pos_ < data_.size()) {
                    result += data_[pos_++];
                }
            } else {
                result += data_[pos_++];
            }
        }
        if (pos_ < data_.size()) ++pos_;  // skip closing quote
        return result;
    }

    double read_number() {
        std::string num;
        while (pos_ < data_.size() &&
               (std::isdigit(data_[pos_]) || data_[pos_] == '.' ||
                data_[pos_] == '-' || data_[pos_] == 'e' || data_[pos_] == 'E')) {
            num += data_[pos_++];
        }
        return std::stod(num);
    }

    bool read_bool() {
        if (data_.substr(pos_, 4) == "true") {
            pos_ += 4;
            return true;
        }
        if (data_.substr(pos_, 5) == "false") {
            pos_ += 5;
            return false;
        }
        return false;
    }
};

// ============================================================================
// 3. 字段描述元编程
// ============================================================================

/**
 * @brief 字段描述符
 * @tparam T 结构体类型
 * @tparam FieldType 字段类型
 */
template <typename T, typename FieldType>
struct FieldDescriptor {
    const char* name;
    FieldType T::*member_ptr;
};

/**
 * @brief 创建字段描述符
 */
template <typename T, typename FieldType>
constexpr auto make_field(const char* name, FieldType T::*ptr) {
    return FieldDescriptor<T, FieldType>{name, ptr};
}

// ============================================================================
// 4. 可序列化结构体宏
// ============================================================================

/**
 * @brief 定义可序列化结构体
 *
 * 用法：
 *   struct Person {
 *       std::string name;
 *       int age;
 *       double height;
 *   };
 *
 *   // 定义字段
 *   constexpr auto person_fields = std::make_tuple(
 *       make_field("name", &Person::name),
 *       make_field("age", &Person::age),
 *       make_field("height", &Person::height)
 *   );
 */

// ============================================================================
// 5. 自动序列化函数
// ============================================================================

/**
 * @brief 自动序列化 - 使用折叠表达式遍历字段
 */
template <typename T, typename... Fields>
std::string auto_serialize(const T& obj,
                            const std::tuple<Fields...>& fields) {
    Serializer<JsonFormat> serializer;
    serializer.begin_object();

    std::apply([&](const auto&... field) {
        bool first = true;
        (([&]() {
            if (!first) {
                // 添加逗号（在 serializer 内部处理）
            }
            serializer.write_field(field.name, obj.*(field.member_ptr));
            first = false;
        })(), ...);
    }, fields);

    serializer.end_object();
    return serializer.str();
}

// ============================================================================
// 6. 类型特征检测
// ============================================================================

/// @brief 检测类型是否有 serialize 方法
template <typename T, typename = void>
struct has_serialize_method : std::false_type {};

template <typename T>
struct has_serialize_method<T, std::void_t<decltype(std::declval<T>().serialize())>>
    : std::true_type {};

/// @brief 检测类型是否有 deserialize 方法
template <typename T, typename = void>
struct has_deserialize_method : std::false_type {};

template <typename T>
struct has_deserialize_method<T, std::void_t<decltype(
    std::declval<T>().deserialize(std::declval<std::string>()))>>
    : std::true_type {};

// ============================================================================
// 7. 基本类型的序列化
// ============================================================================

/// @brief 基本类型序列化
template <typename T>
std::string serialize_value(const T& value) {
    if constexpr (std::is_same_v<T, std::string>) {
        return "\"" + value + "\"";
    } else if constexpr (std::is_same_v<T, bool>) {
        return value ? "true" : "false";
    } else if constexpr (std::is_arithmetic_v<T>) {
        return std::to_string(value);
    } else {
        static_assert(std::is_arithmetic_v<T> || std::is_same_v<T, std::string>,
                      "Type must be arithmetic or string");
        return "";
    }
}

/// @brief 向量序列化
template <typename T>
std::string serialize_vector(const std::vector<T>& vec) {
    std::string result = "[";
    for (std::size_t i = 0; i < vec.size(); ++i) {
        if (i > 0) result += ",";
        result += serialize_value(vec[i]);
    }
    result += "]";
    return result;
}

// ============================================================================
// 8. 二进制序列化
// ============================================================================

/**
 * @brief 二进制序列化器
 */
class BinarySerializer {
    std::string buffer_;

public:
    template <typename T>
    void write(const T& value) {
        const char* bytes = reinterpret_cast<const char*>(&value);
        buffer_.append(bytes, sizeof(T));
    }

    void write_string(const std::string& s) {
        std::size_t len = s.size();
        write(len);
        buffer_.append(s);
    }

    const std::string& buffer() const { return buffer_; }
};

/**
 * @brief 二进制反序列化器
 */
class BinaryDeserializer {
    std::string buffer_;
    std::size_t pos_ = 0;

public:
    explicit BinaryDeserializer(const std::string& buffer)
        : buffer_(buffer) {}

    template <typename T>
    T read() {
        T value;
        std::memcpy(&value, buffer_.data() + pos_, sizeof(T));
        pos_ += sizeof(T);
        return value;
    }

    std::string read_string() {
        std::size_t len = read<std::size_t>();
        std::string s(buffer_.data() + pos_, len);
        pos_ += len;
        return s;
    }
};

}  // namespace tmp
