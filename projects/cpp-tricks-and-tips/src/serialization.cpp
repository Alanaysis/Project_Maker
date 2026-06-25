/**
 * serialization.cpp - 序列化与反序列化
 *
 * 本文件演示 C++ 中常见的序列化技术，包括：
 *   1. 二进制序列化（直接内存拷贝）
 *   2. 类型安全的二进制序列化框架
 *   3. JSON 风格的文本序列化
 *   4. 序列化/反序列化模式
 *
 * 编译命令:
 *   g++ -std=c++17 -o serialization serialization.cpp
 */

#include <iostream>
#include <sstream>
#include <fstream>
#include <string>
#include <vector>
#include <map>
#include <variant>
#include <optional>
#include <cstring>
#include <type_traits>
#include <algorithm>
#include <iomanip>
#include <memory>
#include <functional>

// ============================================================================
// 第一部分: 基础二进制序列化
// ============================================================================
// 最简单的序列化方式：直接将 POD 类型写入字节流
// 注意：这种方式不处理字节序，不适合跨平台传输

namespace binary {

    // 二进制写入器 - 将数据写入字节缓冲区
    class Writer {
    public:
        // 写入任意 POD（Plain Old Data）类型
        // 使用 SFINAE 确保只对 POD 类型生效
        template <typename T>
        std::enable_if_t<std::is_pod_v<T>> write(const T& value) {
            const char* bytes = reinterpret_cast<const char*>(&value);
            m_buffer.insert(m_buffer.end(), bytes, bytes + sizeof(T));
        }

        // 写入字符串（带长度前缀）
        // 格式: [4字节长度][字符串内容]
        void write_string(const std::string& str) {
            uint32_t length = static_cast<uint32_t>(str.size());
            write(length);
            m_buffer.insert(m_buffer.end(), str.begin(), str.end());
        }

        // 写入 vector（带长度前缀）
        template <typename T>
        void write_vector(const std::vector<T>& vec) {
            uint32_t size = static_cast<uint32_t>(vec.size());
            write(size);
            for (const auto& item : vec) {
                write(item);
            }
        }

        // 获取结果缓冲区
        const std::vector<char>& buffer() const { return m_buffer; }

        // 写入文件
        bool save_to_file(const std::string& filename) const {
            std::ofstream file(filename, std::ios::binary);
            if (!file) return false;
            file.write(m_buffer.data(), m_buffer.size());
            return true;
        }

        // 重置缓冲区
        void clear() { m_buffer.clear(); }

    private:
        std::vector<char> m_buffer;
    };

    // 二进制读取器 - 从字节缓冲区读取数据
    class Reader {
    public:
        explicit Reader(const std::vector<char>& data)
            : m_data(data), m_pos(0) {}

        // 从文件加载
        static std::optional<Reader> from_file(const std::string& filename) {
            std::ifstream file(filename, std::ios::binary);
            if (!file) return std::nullopt;

            file.seekg(0, std::ios::end);
            auto size = file.tellg();
            file.seekg(0, std::ios::beg);

            std::vector<char> data(size);
            file.read(data.data(), size);

            return Reader(data);
        }

        // 读取任意 POD 类型
        template <typename T>
        std::enable_if_t<std::is_pod_v<T>, std::optional<T>> read() {
            if (m_pos + sizeof(T) > m_data.size()) {
                return std::nullopt;  // 数据不足
            }
            T value;
            std::memcpy(&value, m_data.data() + m_pos, sizeof(T));
            m_pos += sizeof(T);
            return value;
        }

        // 读取字符串
        std::optional<std::string> read_string() {
            auto length = read<uint32_t>();
            if (!length) return std::nullopt;
            if (m_pos + *length > m_data.size()) return std::nullopt;

            std::string result(m_data.data() + m_pos, *length);
            m_pos += *length;
            return result;
        }

        // 读取 vector
        template <typename T>
        std::optional<std::vector<T>> read_vector() {
            auto size = read<uint32_t>();
            if (!size) return std::nullopt;

            std::vector<T> result;
            result.reserve(*size);
            for (uint32_t i = 0; i < *size; ++i) {
                auto item = read<T>();
                if (!item) return std::nullopt;
                result.push_back(*item);
            }
            return result;
        }

        // 检查是否还有数据
        bool has_more() const { return m_pos < m_data.size(); }

        // 剩余字节数
        size_t remaining() const { return m_data.size() - m_pos; }

    private:
        std::vector<char> m_data;
        size_t m_pos;
    };

}  // namespace binary

//// ============================================================================
// 第二部分: 类型安全的二进制序列化框架
// ============================================================================
// 通过特化 serialize/deserialize 函数实现自定义类型的序列化

namespace ser {

    // 序列化结果类型
    using ByteBuffer = std::vector<uint8_t>;

    // 基础类型的序列化
    template <typename T>
    std::enable_if_t<std::is_arithmetic_v<T>>
    serialize(ByteBuffer& buf, const T& value) {
        const auto* bytes = reinterpret_cast<const uint8_t*>(&value);
        buf.insert(buf.end(), bytes, bytes + sizeof(T));
    }

    // 基础类型的反序列化
    template <typename T>
    std::enable_if_t<std::is_arithmetic_v<T>, bool>
    deserialize(const uint8_t*& data, size_t& remaining, T& value) {
        if (remaining < sizeof(T)) return false;
        std::memcpy(&value, data, sizeof(T));
        data += sizeof(T);
        remaining -= sizeof(T);
        return true;
    }

    // 字符串序列化（带长度前缀）
    inline void serialize(ByteBuffer& buf, const std::string& str) {
        uint32_t len = static_cast<uint32_t>(str.size());
        serialize(buf, len);
        buf.insert(buf.end(), str.begin(), str.end());
    }

    // 字符串反序列化
    inline bool deserialize(const uint8_t*& data, size_t& remaining,
                            std::string& str) {
        uint32_t len;
        if (!deserialize(data, remaining, len)) return false;
        if (remaining < len) return false;
        str.assign(reinterpret_cast<const char*>(data), len);
        data += len;
        remaining -= len;
        return true;
    }

    // vector 序列化
    template <typename T>
    void serialize(ByteBuffer& buf, const std::vector<T>& vec) {
        uint32_t size = static_cast<uint32_t>(vec.size());
        serialize(buf, size);
        for (const auto& item : vec) {
            serialize(buf, item);
        }
    }

    // vector 反序列化
    template <typename T>
    bool deserialize(const uint8_t*& data, size_t& remaining,
                     std::vector<T>& vec) {
        uint32_t size;
        if (!deserialize(data, remaining, size)) return false;
        vec.resize(size);
        for (auto& item : vec) {
            if (!deserialize(data, remaining, item)) return false;
        }
        return true;
    }

}  // namespace ser

// ============================================================================
// 第三部分: 自定义类型的序列化示例
// ============================================================================
// 为自定义结构体实现序列化和反序列化

// 示例数据结构：游戏存档
struct GameSave {
    std::string player_name;     // 玩家名称
    int32_t level;               // 等级
    double experience;           // 经验值
    int32_t gold;                // 金币
    std::vector<int32_t> inventory;  // 物品栏
    bool is_cheat_mode;          // 是否作弊模式

    // 序列化到字节缓冲区
    void serialize(ser::ByteBuffer& buf) const {
        ser::serialize(buf, player_name);
        ser::serialize(buf, level);
        ser::serialize(buf, experience);
        ser::serialize(buf, gold);
        ser::serialize(buf, inventory);
        // bool 作为 uint8_t 序列化
        uint8_t cheat = is_cheat_mode ? 1 : 0;
        ser::serialize(buf, cheat);
    }

    // 从字节缓冲区反序列化
    bool deserialize(const uint8_t*& data, size_t& remaining) {
        if (!ser::deserialize(data, remaining, player_name)) return false;
        if (!ser::deserialize(data, remaining, level)) return false;
        if (!ser::deserialize(data, remaining, experience)) return false;
        if (!ser::deserialize(data, remaining, gold)) return false;
        if (!ser::deserialize(data, remaining, inventory)) return false;
        uint8_t cheat;
        if (!ser::deserialize(data, remaining, cheat)) return false;
        is_cheat_mode = (cheat != 0);
        return true;
    }

    void print() const {
        std::cout << "  玩家: " << player_name << std::endl;
        std::cout << "  等级: " << level << std::endl;
        std::cout << "  经验: " << experience << std::endl;
        std::cout << "  金币: " << gold << std::endl;
        std::cout << "  物品栏: [";
        for (size_t i = 0; i < inventory.size(); ++i) {
            if (i > 0) std::cout << ", ";
            std::cout << inventory[i];
        }
        std::cout << "]" << std::endl;
        std::cout << "  作弊模式: " << (is_cheat_mode ? "是" : "否") << std::endl;
    }
};

// ============================================================================
// 第四部分: JSON 风格的文本序列化
// ============================================================================
// 实现一个简化版的 JSON 序列化器，展示文本序列化技术

namespace json {

    // JSON 值类型
    class Value;
    using Object = std::map<std::string, Value>;
    using Array = std::vector<Value>;

    class Value {
    public:
        enum Type { NUL, BOOL, INT, DOUBLE, STRING, ARRAY, OBJECT };

        Value() : m_type(NUL) {}
        Value(bool v) : m_type(BOOL), m_bool(v) {}
        Value(int v) : m_type(INT), m_int(v) {}
        Value(double v) : m_type(DOUBLE), m_double(v) {}
        Value(const std::string& v) : m_type(STRING), m_string(new std::string(v)) {}
        Value(const char* v) : m_type(STRING), m_string(new std::string(v)) {}
        Value(const Array& v) : m_type(ARRAY), m_array(new Array(v)) {}
        Value(const Object& v) : m_type(OBJECT), m_object(new Object(v)) {}

        // 拷贝构造
        Value(const Value& other) : m_type(other.m_type) {
            copy_from(other);
        }

        // 移动构造
        Value(Value&& other) noexcept : m_type(other.m_type) {
            m_data = other.m_data;
            other.m_type = NUL;
            other.m_data = {};
        }

        ~Value() { cleanup(); }

        Value& operator=(const Value& other) {
            if (this != &other) {
                cleanup();
                m_type = other.m_type;
                copy_from(other);
            }
            return *this;
        }

        Type type() const { return m_type; }

        bool is_null() const { return m_type == NUL; }
        bool is_bool() const { return m_type == BOOL; }
        bool is_number() const { return m_type == INT || m_type == DOUBLE; }
        bool is_string() const { return m_type == STRING; }
        bool is_array() const { return m_type == ARRAY; }
        bool is_object() const { return m_type == OBJECT; }

        bool as_bool() const { return m_bool; }
        int as_int() const { return m_type == DOUBLE ? static_cast<int>(m_double) : m_int; }
        double as_double() const { return m_type == INT ? static_cast<double>(m_int) : m_double; }
        const std::string& as_string() const { return *m_string; }
        const Array& as_array() const { return *m_array; }
        const Object& as_object() const { return *m_object; }

        // 数组操作
        void push(const Value& v) {
            if (m_type != ARRAY) {
                cleanup();
                m_type = ARRAY;
                m_array = new Array();
            }
            m_array->push_back(v);
        }

        // 对象操作
        Value& operator[](const std::string& key) {
            if (m_type != OBJECT) {
                cleanup();
                m_type = OBJECT;
                m_object = new Object();
            }
            return (*m_object)[key];
        }

        // 序列化为 JSON 字符串
        std::string dump(int indent = 0, int current_indent = 0) const {
            std::string pad(current_indent, ' ');
            std::string inner_pad(current_indent + indent, ' ');

            switch (m_type) {
                case NUL:    return "null";
                case BOOL:   return m_bool ? "true" : "false";
                case INT:    return std::to_string(m_int);
                case DOUBLE: {
                    std::ostringstream oss;
                    oss << std::fixed << std::setprecision(2) << m_double;
                    return oss.str();
                }
                case STRING: return "\"" + escape_string(*m_string) + "\"";
                case ARRAY: {
                    if (m_array->empty()) return "[]";
                    std::string result = "[\n";
                    for (size_t i = 0; i < m_array->size(); ++i) {
                        result += inner_pad
                                + (*m_array)[i].dump(indent, current_indent + indent);
                        if (i + 1 < m_array->size()) result += ",";
                        result += "\n";
                    }
                    result += pad + "]";
                    return result;
                }
                case OBJECT: {
                    if (m_object->empty()) return "{}";
                    std::string result = "{\n";
                    size_t i = 0;
                    for (const auto& [key, val] : *m_object) {
                        result += inner_pad + "\"" + key + "\": "
                                + val.dump(indent, current_indent + indent);
                        if (i + 1 < m_object->size()) result += ",";
                        result += "\n";
                        ++i;
                    }
                    result += pad + "}";
                    return result;
                }
            }
            return "";
        }

    private:
        void cleanup() {
            switch (m_type) {
                case STRING: delete m_string; break;
                case ARRAY:  delete m_array; break;
                case OBJECT: delete m_object; break;
                default: break;
            }
            m_type = NUL;
        }

        void copy_from(const Value& other) {
            switch (m_type) {
                case BOOL:   m_bool = other.m_bool; break;
                case INT:    m_int = other.m_int; break;
                case DOUBLE: m_double = other.m_double; break;
                case STRING: m_string = new std::string(*other.m_string); break;
                case ARRAY:  m_array = new Array(*other.m_array); break;
                case OBJECT: m_object = new Object(*other.m_object); break;
                default: break;
            }
        }

        static std::string escape_string(const std::string& s) {
            std::string result;
            for (char c : s) {
                switch (c) {
                    case '"':  result += "\\\""; break;
                    case '\\': result += "\\\\"; break;
                    case '\n': result += "\\n"; break;
                    case '\t': result += "\\t"; break;
                    default:   result += c;
                }
            }
            return result;
        }

        Type m_type;
        union {
            bool m_bool;
            int m_int;
            double m_double;
            std::string* m_string;
            Array* m_array;
            Object* m_object;
        } m_data;

        // 为了简化，这里用独立成员代替 union 访问
        // 实际项目中应使用 union 或 variant
        bool m_bool = false;
        int m_int = 0;
        double m_double = 0.0;
        std::string* m_string = nullptr;
        Array* m_array = nullptr;
        Object* m_object = nullptr;
    };

}  // namespace json

// ============================================================================
// 演示代码
// ============================================================================

void demo_binary_serialization() {
    std::cout << "========================================" << std::endl;
    std::cout << "1. 基础二进制序列化" << std::endl;
    std::cout << "========================================" << std::endl;

    // 序列化
    binary::Writer writer;
    writer.write<int32_t>(42);
    writer.write<double>(3.14159);
    writer.write<bool>(true);
    writer.write_string("Hello, 序列化!");
    writer.write_vector<int32_t>({1, 2, 3, 4, 5});

    std::cout << "序列化完成，缓冲区大小: " << writer.buffer().size() << " 字节" << std::endl;

    // 保存到文件
    writer.save_to_file("/tmp/save.bin");
    std::cout << "已保存到 /tmp/save.bin" << std::endl;

    // 反序列化
    binary::Reader reader(writer.buffer());
    auto int_val = reader.read<int32_t>();
    auto double_val = reader.read<double>();
    auto bool_val = reader.read<bool>();
    auto str_val = reader.read_string();
    auto vec_val = reader.read_vector<int32_t>();

    std::cout << "\n反序列化结果:" << std::endl;
    std::cout << "  int32: " << int_val.value_or(0) << std::endl;
    std::cout << "  double: " << double_val.value_or(0.0) << std::endl;
    std::cout << "  bool: " << (bool_val.value_or(false) ? "true" : "false") << std::endl;
    std::cout << "  string: " << str_val.value_or("") << std::endl;
    std::cout << "  vector: [";
    if (vec_val) {
        for (size_t i = 0; i < vec_val->size(); ++i) {
            if (i > 0) std::cout << ", ";
            std::cout << (*vec_val)[i];
        }
    }
    std::cout << "]" << std::endl;

    // 从文件反序列化
    auto file_reader = binary::Reader::from_file("/tmp/save.bin");
    if (file_reader) {
        auto file_int = file_reader->read<int32_t>();
        std::cout << "\n从文件读取的 int32: " << file_int.value_or(0) << std::endl;
    }

    std::remove("/tmp/save.bin");
}

void demo_game_save() {
    std::cout << "\n========================================" << std::endl;
    std::cout << "2. 游戏存档序列化" << std::endl;
    std::cout << "========================================" << std::endl;

    // 创建游戏存档
    GameSave save;
    save.player_name = "勇者小明";
    save.level = 25;
    save.experience = 15680.5;
    save.gold = 9999;
    save.inventory = {101, 202, 303, 404, 505};
    save.is_cheat_mode = false;

    std::cout << "原始存档:" << std::endl;
    save.print();

    // 序列化
    ser::ByteBuffer buffer;
    save.serialize(buffer);
    std::cout << "\n序列化大小: " << buffer.size() << " 字节" << std::endl;

    // 反序列化
    GameSave loaded;
    const uint8_t* data = buffer.data();
    size_t remaining = buffer.size();
    if (loaded.deserialize(data, remaining)) {
        std::cout << "\n反序列化后的存档:" << std::endl;
        loaded.print();

        // 验证数据一致性
        bool match = (save.player_name == loaded.player_name)
                  && (save.level == loaded.level)
                  && (save.gold == loaded.gold)
                  && (save.inventory == loaded.inventory)
                  && (save.is_cheat_mode == loaded.is_cheat_mode);
        std::cout << "\n数据一致性验证: " << (match ? "通过" : "失败") << std::endl;
    } else {
        std::cerr << "反序列化失败!" << std::endl;
    }
}

void demo_json_serialization() {
    std::cout << "\n========================================" << std::endl;
    std::cout << "3. JSON 风格序列化" << std::endl;
    std::cout << "========================================" << std::endl;

    // 构建 JSON 对象
    json::Value player(json::Object{});
    player["name"] = "勇者小明";
    player["level"] = 25;
    player["hp"] = 100.0;
    player["alive"] = true;

    // 添加数组
    json::Value skills(json::Array{});
    skills.push("火球术");
    skills.push("冰冻术");
    skills.push("治愈术");
    player["skills"] = skills;

    // 嵌套对象
    json::Value position(json::Object{});
    position["x"] = 100;
    position["y"] = 200;
    position["z"] = 50;
    player["position"] = position;

    // 输出 JSON
    std::cout << "JSON 输出:" << std::endl;
    std::cout << player.dump(2) << std::endl;

    // 构建更复杂的 JSON
    json::Value config(json::Object{});
    config["app_name"] = "MyApp";
    config["version"] = 2;
    config["debug"] = false;

    json::Value servers(json::Array{});
    servers.push("server1.example.com");
    servers.push("server2.example.com");
    servers.push("server3.example.com");
    config["servers"] = servers;

    std::cout << "\n配置 JSON:" << std::endl;
    std::cout << config.dump(4) << std::endl;

    // 类型检查
    std::cout << "\n类型检查:" << std::endl;
    std::cout << "  app_name 是字符串: " << (config["app_name"].is_string() ? "是" : "否") << std::endl;
    std::cout << "  version 是数字: " << (config["version"].is_number() ? "是" : "否") << std::endl;
    std::cout << "  servers 是数组: " << (config["servers"].is_array() ? "是" : "否") << std::endl;
}

// ============================================================================
// 主函数
// ============================================================================
int main() {
    std::cout << "╔══════════════════════════════════════╗" << std::endl;
    std::cout << "║  C++ 序列化技术 (serialization)      ║" << std::endl;
    std::cout << "╚══════════════════════════════════════╝" << std::endl;
    std::cout << std::endl;

    demo_binary_serialization();
    demo_game_save();
    demo_json_serialization();

    std::cout << "\n序列化演示完成。" << std::endl;
    return 0;
}
