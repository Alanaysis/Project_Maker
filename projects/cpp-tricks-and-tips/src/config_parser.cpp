/**
 * config_parser.cpp - 配置文件解析器
 *
 * 本文件演示如何实现一个简单的配置文件解析器，包括：
 *   1. INI/TOML 风格的配置文件解析
 *   2. 类型安全的配置访问
 *   3. 默认值支持
 *   4. 配置分组（Section）支持
 *   5. 注释和空白行处理
 *
 * 支持的配置格式:
 *   ; 或 # 开头的注释行
 *   [section] 分组
 *   key = value 键值对
 *   支持的类型: 字符串、整数、浮点数、布尔值
 *
 * 编译命令:
 *   g++ -std=c++17 -o config_parser config_parser.cpp
 */

#include <iostream>
#include <string>
#include <string_view>
#include <sstream>
#include <fstream>
#include <map>
#include <optional>
#include <variant>
#include <algorithm>
#include <stdexcept>
#include <type_traits>
#include <vector>
#include <functional>

// ============================================================================
// 第一部分: 配置值类型
// ============================================================================
// 使用 std::variant 存储多种类型的配置值

// 配置值可以是这四种类型之一
using ConfigValue = std::variant<std::string, int, double, bool>;

// 配置值的类型枚举，用于类型检查
enum class ValueType {
    STRING,
    INT,
    DOUBLE,
    BOOL
};

// 获取配置值的类型名（用于错误消息）
inline const char* value_type_name(ValueType type) {
    switch (type) {
        case ValueType::STRING: return "字符串";
        case ValueType::INT:    return "整数";
        case ValueType::DOUBLE: return "浮点数";
        case ValueType::BOOL:   return "布尔值";
        default: return "未知";
    }
}

//// ============================================================================
// 第二部分: 配置值解析
// ============================================================================
// 将字符串解析为具体的类型

namespace config_detail {

    // 判断字符串是否为布尔值
    inline bool is_bool(std::string_view s) {
        std::string lower(s);
        std::transform(lower.begin(), lower.end(), lower.begin(), ::tolower);
        return lower == "true" || lower == "false"
            || lower == "yes" || lower == "no"
            || lower == "on" || lower == "off"
            || lower == "1" || lower == "0";
    }

    // 解析布尔值
    inline bool parse_bool(std::string_view s) {
        std::string lower(s);
        std::transform(lower.begin(), lower.end(), lower.begin(), ::tolower);
        return lower == "true" || lower == "yes"
            || lower == "on" || lower == "1";
    }

    // 判断字符串是否为整数
    inline bool is_integer(std::string_view s) {
        if (s.empty()) return false;
        size_t start = (s[0] == '-' || s[0] == '+') ? 1 : 0;
        if (start >= s.size()) return false;
        return std::all_of(s.begin() + start, s.end(), ::isdigit);
    }

    // 判断字符串是否为浮点数
    inline bool is_double(std::string_view s) {
        if (s.empty()) return false;
        try {
            size_t pos;
            std::stod(std::string(s), &pos);
            return pos == s.size();
        } catch (...) {
            return false;
        }
    }

    // 去除字符串首尾空白
    inline std::string trim(std::string_view s) {
        auto start = s.find_first_not_of(" \t\r\n");
        if (start == std::string_view::npos) return "";
        auto end = s.find_last_not_of(" \t\r\n");
        return std::string(s.substr(start, end - start + 1));
    }

    // 去除行内注释（处理引号内的分号/井号）
    inline std::string remove_inline_comment(std::string_view s) {
        bool in_quotes = false;
        for (size_t i = 0; i < s.size(); ++i) {
            if (s[i] == '"') in_quotes = !in_quotes;
            if (!in_quotes && (s[i] == ';' || s[i] == '#')) {
                return trim(s.substr(0, i));
            }
        }
        return trim(s);
    }

    // 去除字符串两端的引号
    inline std::string unquote(std::string_view s) {
        if (s.size() >= 2) {
            if ((s.front() == '"' && s.back() == '"') ||
                (s.front() == '\'' && s.back() == '\'')) {
                return std::string(s.substr(1, s.size() - 2));
            }
        }
        return std::string(s);
    }

    // 自动推断类型并解析值
    inline ConfigValue auto_parse(std::string_view raw) {
        std::string value = trim(raw);

        // 空值返回空字符串
        if (value.empty()) return std::string("");

        // 布尔值
        if (is_bool(value)) return parse_bool(value);

        // 整数（优先于浮点数判断）
        if (is_integer(value)) {
            try {
                return static_cast<int>(std::stoll(value));
            } catch (...) {}
        }

        // 浮点数
        if (is_double(value)) {
            try {
                return std::stod(value);
            } catch (...) {}
        }

        // 默认作为字符串（去除引号）
        return unquote(value);
    }

}  // namespace config_detail

// ============================================================================
// 第三部分: 配置节点
// ============================================================================
// 代表一个配置键值对，支持类型安全的访问

class ConfigNode {
public:
    ConfigNode() = default;
    explicit ConfigNode(ConfigValue value) : m_value(std::move(value)) {}

    // 检查是否有值
    bool has_value() const { return m_value.has_value(); }

    // 获取值的类型
    ValueType type() const {
        if (!m_value) throw std::runtime_error("配置节点无值");
        if (std::holds_alternative<std::string>(*m_value)) return ValueType::STRING;
        if (std::holds_alternative<int>(*m_value)) return ValueType::INT;
        if (std::holds_alternative<double>(*m_value)) return ValueType::DOUBLE;
        if (std::holds_alternative<bool>(*m_value)) return ValueType::BOOL;
        throw std::runtime_error("未知的配置值类型");
    }

    // 类型安全的值获取
    template <typename T>
    T as() const {
        if (!m_value) throw std::runtime_error("配置节点无值");

        // 直接类型匹配
        if constexpr (std::is_same_v<T, std::string>) {
            if (auto* p = std::get_if<std::string>(&*m_value)) return *p;
            // 其他类型转字符串
            if (auto* p = std::get_if<int>(&*m_value)) return std::to_string(*p);
            if (auto* p = std::get_if<double>(&*m_value)) return std::to_string(*p);
            if (auto* p = std::get_if<bool>(&*m_value)) return *p ? "true" : "false";
        }
        if constexpr (std::is_same_v<T, int>) {
            if (auto* p = std::get_if<int>(&*m_value)) return *p;
            if (auto* p = std::get_if<double>(&*m_value)) return static_cast<int>(*p);
            if (auto* p = std::get_if<std::string>(&*m_value)) return std::stoi(*p);
        }
        if constexpr (std::is_same_v<T, double>) {
            if (auto* p = std::get_if<double>(&*m_value)) return *p;
            if (auto* p = std::get_if<int>(&*m_value)) return static_cast<double>(*p);
            if (auto* p = std::get_if<std::string>(&*m_value)) return std::stod(*p);
        }
        if constexpr (std::is_same_v<T, bool>) {
            if (auto* p = std::get_if<bool>(&*m_value)) return *p;
            if (auto* p = std::get_if<int>(&*m_value)) return *p != 0;
        }

        throw std::runtime_error("类型转换失败");
    }

    // 值转字符串（用于显示）
    std::string to_string() const {
        if (!m_value) return "<empty>";
        return std::visit([](const auto& v) -> std::string {
            using T = std::decay_t<decltype(v)>;
            if constexpr (std::is_same_v<T, bool>) return v ? "true" : "false";
            else if constexpr (std::is_same_v<T, std::string>) return v;
            else return std::to_string(v);
        }, *m_value);
    }

private:
    std::optional<ConfigValue> m_value;
};

// ============================================================================
// 第四部分: 配置节 (Section)
// ============================================================================
// 代表配置文件中的一个 [section]

class ConfigSection {
public:
    // 设置键值对
    void set(const std::string& key, ConfigValue value) {
        m_data[key] = ConfigNode(std::move(value));
    }

    // 获取配置节点（不带默认值）
    std::optional<ConfigNode> get(const std::string& key) const {
        auto it = m_data.find(key);
        if (it != m_data.end()) return it->second;
        return std::nullopt;
    }

    // 获取配置值（带默认值）
    template <typename T>
    T get_or(const std::string& key, const T& default_value) const {
        auto node = get(key);
        if (node && node->has_value()) {
            try {
                return node->as<T>();
            } catch (...) {
                return default_value;
            }
        }
        return default_value;
    }

    // 检查键是否存在
    bool has(const std::string& key) const {
        return m_data.find(key) != m_data.end();
    }

    // 获取所有键
    std::vector<std::string> keys() const {
        std::vector<std::string> result;
        for (const auto& [k, v] : m_data) {
            result.push_back(k);
        }
        return result;
    }

    // 获取键值对数量
    size_t size() const { return m_data.size(); }

    // 用于调试：打印所有配置
    void dump(std::ostream& os, const std::string& section_name = "") const {
        if (!section_name.empty()) {
            os << "[" << section_name << "]" << std::endl;
        }
        for (const auto& [key, node] : m_data) {
            os << "  " << key << " = " << node.to_string()
               << " (" << value_type_name(node.type()) << ")" << std::endl;
        }
    }

private:
    std::map<std::string, ConfigNode> m_data;
};

// ============================================================================
// 第五部分: 配置解析器主类
// ============================================================================
// 解析 INI/TOML 风格的配置文件

class ConfigParser {
public:
    ConfigParser() = default;

    // 从文件加载配置
    bool load_file(const std::string& filename) {
        std::ifstream file(filename);
        if (!file.is_open()) {
            std::cerr << "无法打开配置文件: " << filename << std::endl;
            return false;
        }

        std::string content((std::istreambuf_iterator<char>(file)),
                             std::istreambuf_iterator<char>());
        return parse(content);
    }

    // 从字符串解析配置
    bool parse(std::string_view content) {
        std::string content_str(content);
        std::istringstream stream(content_str);
        std::string line;
        std::string current_section;  // 当前节名，空字符串表示全局节
        int line_number = 0;

        while (std::getline(stream, line)) {
            ++line_number;

            // 去除行首尾空白
            line = config_detail::trim(line);

            // 跳过空行和注释行
            if (line.empty() || line[0] == ';' || line[0] == '#') {
                continue;
            }

            // 解析节名 [section]
            if (line.front() == '[' && line.back() == ']') {
                current_section = config_detail::trim(
                    line.substr(1, line.size() - 2));
                continue;
            }

            // 解析键值对 key = value
            auto eq_pos = line.find('=');
            if (eq_pos == std::string::npos) {
                std::cerr << "警告: 第 " << line_number
                          << " 行格式错误，跳过: " << line << std::endl;
                continue;
            }

            std::string key = config_detail::trim(line.substr(0, eq_pos));
            std::string value_str = config_detail::trim(line.substr(eq_pos + 1));

            // 去除行内注释
            value_str = config_detail::remove_inline_comment(value_str);

            if (key.empty()) {
                std::cerr << "警告: 第 " << line_number
                          << " 行键名为空，跳过" << std::endl;
                continue;
            }

            // 自动推断类型并存储
            ConfigValue value = config_detail::auto_parse(value_str);
            m_sections[current_section].set(key, std::move(value));
        }

        return true;
    }

    // 获取指定节
    const ConfigSection& section(const std::string& name = "") const {
        static const ConfigSection empty_section;
        auto it = m_sections.find(name);
        if (it != m_sections.end()) return it->second;
        return empty_section;
    }

    // 便捷方法：直接获取全局节的值
    template <typename T>
    T get(const std::string& key, const T& default_value = T{}) const {
        return section("").get_or(key, default_value);
    }

    // 便捷方法：获取指定节的值
    template <typename T>
    T get(const std::string& section_name,
          const std::string& key,
          const T& default_value = T{}) const {
        return section(section_name).get_or(key, default_value);
    }

    // 检查节是否存在
    bool has_section(const std::string& name) const {
        return m_sections.find(name) != m_sections.end();
    }

    // 获取所有节名
    std::vector<std::string> sections() const {
        std::vector<std::string> result;
        for (const auto& [k, v] : m_sections) {
            result.push_back(k);
        }
        return result;
    }

    // 打印所有配置（用于调试）
    void dump(std::ostream& os = std::cout) const {
        for (const auto& [name, section] : m_sections) {
            section.dump(os, name);
            os << std::endl;
        }
    }

    // 设置配置值（运行时修改）
    void set(const std::string& section_name,
             const std::string& key,
             ConfigValue value) {
        m_sections[section_name].set(key, std::move(value));
    }

private:
    std::map<std::string, ConfigSection> m_sections;
};

// ============================================================================
// 第六部分: 配置构建器（Fluent API）
// ============================================================================
// 提供链式调用的配置构建方式

class ConfigBuilder {
public:
    ConfigBuilder& section(const std::string& name) {
        m_current_section = name;
        return *this;
    }

    ConfigBuilder& set(const std::string& key, ConfigValue value) {
        m_parser.set(m_current_section, key, std::move(value));
        return *this;
    }

    ConfigParser build() {
        return std::move(m_parser);
    }

private:
    ConfigParser m_parser;
    std::string m_current_section;
};

// ============================================================================
// 演示代码
// ============================================================================

void demo_config_parser() {
    std::cout << "========================================" << std::endl;
    std::cout << "1. 基本配置解析" << std::endl;
    std::cout << "========================================" << std::endl;

    // 模拟一个配置文件的内容
    std::string config_content = R"(
# 应用程序配置文件
; 这是另一种注释格式

[app]
name = MyApplication    # 应用名称
version = 2.1.0         # 版本号
debug = true            # 调试模式
max_connections = 100   # 最大连接数

[database]
host = localhost
port = 5432
name = mydb
user = admin
password = "secret;pass"  # 密码包含分号，使用引号
timeout = 30.5
pool_size = 10

[logging]
level = INFO
file = /var/log/app.log
console = true
max_size = 10485760
)";

    ConfigParser parser;
    if (!parser.parse(config_content)) {
        std::cerr << "配置解析失败!" << std::endl;
        return;
    }

    // 打印解析结果
    std::cout << "解析结果:" << std::endl;
    parser.dump();

    std::cout << "\n========================================" << std::endl;
    std::cout << "2. 类型安全的配置访问" << std::endl;
    std::cout << "========================================" << std::endl;

    // 访问 app 节的配置
    const auto& app = parser.section("app");
    std::cout << "应用名称: " << app.get_or<std::string>("name", "Unknown") << std::endl;
    std::cout << "版本号:   " << app.get_or<std::string>("version", "0.0.0") << std::endl;
    std::cout << "调试模式: " << (app.get_or<bool>("debug", false) ? "开启" : "关闭") << std::endl;
    std::cout << "最大连接: " << app.get_or<int>("max_connections", 10) << std::endl;

    // 访问 database 节的配置
    const auto& db = parser.section("database");
    std::cout << "\n数据库主机: " << db.get_or<std::string>("host", "127.0.0.1") << std::endl;
    std::cout << "数据库端口: " << db.get_or<int>("port", 3306) << std::endl;
    std::cout << "数据库名称: " << db.get_or<std::string>("name", "test") << std::endl;
    std::cout << "连接超时:   " << db.get_or<double>("timeout", 10.0) << " 秒" << std::endl;
    std::cout << "连接池大小: " << db.get_or<int>("pool_size", 5) << std::endl;

    std::cout << "\n========================================" << std::endl;
    std::cout << "3. 默认值支持" << std::endl;
    std::cout << "========================================" << std::endl;

    // 访问不存在的键，返回默认值
    std::cout << "不存在的键 (返回默认值):" << std::endl;
    std::cout << "  app.unknown_string = "
              << app.get_or<std::string>("unknown_string", "默认值") << std::endl;
    std::cout << "  app.unknown_int = "
              << app.get_or<int>("unknown_int", 42) << std::endl;
    std::cout << "  app.unknown_bool = "
              << (app.get_or<bool>("unknown_bool", true) ? "true" : "false") << std::endl;

    // 访问不存在的节
    const auto& missing = parser.section("nonexistent");
    std::cout << "  nonexistent.key = "
              << missing.get_or<std::string>("key", "节不存在") << std::endl;

    std::cout << "\n========================================" << std::endl;
    std::cout << "4. 便捷访问方法" << std::endl;
    std::cout << "========================================" << std::endl;

    // 使用两参数 get 直接访问
    std::cout << "直接访问:" << std::endl;
    std::cout << "  app.name = "
              << parser.get<std::string>("app", "name") << std::endl;
    std::cout << "  db.port = "
              << parser.get<int>("database", "port") << std::endl;
    std::cout << "  log.level = "
              << parser.get<std::string>("logging", "level") << std::endl;

    std::cout << "\n========================================" << std::endl;
    std::cout << "5. 配置构建器 (Fluent API)" << std::endl;
    std::cout << "========================================" << std::endl;

    // 使用构建器链式创建配置
    ConfigParser built = ConfigBuilder()
        .section("server")
            .set("host", std::string("0.0.0.0"))
            .set("port", 8080)
            .set("ssl", true)
        .section("cache")
            .set("enabled", true)
            .set("ttl", 3600)
            .set("max_entries", 10000)
        .build();

    std::cout << "构建的配置:" << std::endl;
    built.dump();

    std::cout << "\n========================================" << std::endl;
    std::cout << "6. 运行时修改配置" << std::endl;
    std::cout << "========================================" << std::endl;

    // 修改已解析的配置
    parser.set("app", "debug", false);
    parser.set("app", "version", std::string("3.0.0"));
    parser.set("app", "new_feature", true);

    std::cout << "修改后的 app 节:" << std::endl;
    parser.section("app").dump(std::cout, "app");

    std::cout << "\n========================================" << std::endl;
    std::cout << "7. 文件加载演示" << std::endl;
    std::cout << "========================================" << std::endl;

    // 创建临时配置文件
    std::string temp_file = "/tmp/test_config.ini";
    {
        std::ofstream ofs(temp_file);
        ofs << "# 临时配置文件\n";
        ofs << "[test]\n";
        ofs << "key1 = value1\n";
        ofs << "key2 = 42\n";
        ofs << "key3 = 3.14\n";
        ofs << "key4 = true\n";
    }

    ConfigParser file_parser;
    if (file_parser.load_file(temp_file)) {
        std::cout << "从文件加载的配置:" << std::endl;
        file_parser.dump();
    }

    // 清理临时文件
    std::remove(temp_file.c_str());

    std::cout << "\n========================================" << std::endl;
    std::cout << "8. 错误处理" << std::endl;
    std::cout << "========================================" << std::endl;

    // 类型转换错误处理
    const auto& test_section = file_parser.section("test");
    try {
        // 尝试将字符串值转换为整数
        int val = test_section.get_or<int>("key1", -1);
        std::cout << "key1 as int: " << val << " (转换成功)" << std::endl;
    } catch (const std::exception& e) {
        std::cout << "key1 转换为 int 失败: " << e.what() << std::endl;
    }

    // 安全的默认值方式
    int safe_val = test_section.get_or<int>("key1", -1);
    std::cout << "key1 as int (安全方式): " << safe_val << std::endl;
}

// ============================================================================
// 主函数
// ============================================================================
int main() {
    std::cout << "╔══════════════════════════════════════╗" << std::endl;
    std::cout << "║  C++ 配置文件解析器 (config_parser)  ║" << std::endl;
    std::cout << "╚══════════════════════════════════════╝" << std::endl;
    std::cout << std::endl;

    demo_config_parser();

    std::cout << "\n配置解析器演示完成。" << std::endl;
    return 0;
}
