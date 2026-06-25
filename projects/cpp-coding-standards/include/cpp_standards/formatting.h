#ifndef CPP_STANDARDS_FORMATTING_H
#define CPP_STANDARDS_FORMATTING_H

/**
 * @file formatting.h
 * @brief 代码格式规范示例头文件
 *
 * 本文件展示 C++ 代码格式规范的最佳实践，包括：
 * - 缩进风格
 * - 大括号风格
 * - 行长度限制
 * - 空格使用
 * - 空行使用
 * - 注释格式
 */

#include <string>
#include <vector>
#include <memory>

namespace cpp_standards {

// ============================================================================
// 缩进风格示例 - 使用 2 空格缩进
// ============================================================================

/**
 * @brief 配置管理器类
 *
 * 展示正确的缩进风格
 */
class ConfigManager {
public:
    /**
     * @brief 构造函数
     * @param config_path 配置文件路径
     */
    explicit ConfigManager(const std::string& config_path);

    /**
     * @brief 析构函数
     */
    ~ConfigManager() = default;

    /**
     * @brief 获取配置值
     * @param key 配置键
     * @return 配置值
     */
    std::string getValue(const std::string& key) const;

    /**
     * @brief 设置配置值
     * @param key 配置键
     * @param value 配置值
     */
    void setValue(const std::string& key, const std::string& value);

    /**
     * @brief 检查配置是否存在
     * @param key 配置键
     * @return 是否存在
     */
    bool hasKey(const std::string& key) const;

    /**
     * @brief 保存配置到文件
     * @return 是否成功
     */
    bool save();

private:
    /// 配置项结构体
    struct ConfigItem {
        std::string key;      ///< 配置键
        std::string value;    ///< 配置值
        std::string comment;  ///< 注释
    };

    std::string config_path_;              ///< 配置文件路径
    std::vector<ConfigItem> items_;        ///< 配置项列表
    bool is_modified_;                     ///< 是否已修改

    /**
     * @brief 解析配置文件
     * @return 是否成功
     */
    bool parseFile();

    /**
     * @brief 格式化配置项
     * @param item 配置项
     * @return 格式化后的字符串
     */
    std::string formatItem(const ConfigItem& item) const;
};

// ============================================================================
// 大括号风格示例 - 使用 K&R 风格
// ============================================================================

/**
 * @brief 日志记录器类
 *
 * 展示正确的大括号风格
 */
class Logger {
public:
    /**
     * @brief 构造函数
     * @param log_file 日志文件路径
     */
    explicit Logger(const std::string& log_file);

    /**
     * @brief 析构函数
     */
    ~Logger();

    /**
     * @brief 记录调试日志
     * @param message 日志消息
     */
    void debug(const std::string& message);

    /**
     * @brief 记录信息日志
     * @param message 日志消息
     */
    void info(const std::string& message);

    /**
     * @brief 记录警告日志
     * @param message 日志消息
     */
    void warning(const std::string& message);

    /**
     * @brief 记录错误日志
     * @param message 日志消息
     */
    void error(const std::string& message);

private:
    std::string log_file_;    ///< 日志文件路径
    FILE* file_handle_;       ///< 文件句柄
    bool is_open_;            ///< 是否已打开

    /**
     * @brief 写入日志
     * @param level 日志级别
     * @param message 日志消息
     */
    void writeLog(const std::string& level, const std::string& message);
};

// ============================================================================
// 行长度限制示例 - 限制 80 列
// ============================================================================

/**
 * @brief 数据处理器类
 *
 * 展示正确的行长度限制
 */
class DataProcessor {
public:
    /**
     * @brief 处理数据
     * @param input_data 输入数据
     * @param output_data 输出数据
     * @param processing_mode 处理模式
     * @return 是否成功
     */
    bool processData(
        const std::vector<uint8_t>& input_data,
        std::vector<uint8_t>& output_data,
        int processing_mode
    );

    /**
     * @brief 验证数据格式
     * @param data 数据
     * @param expected_format 期望格式
     * @return 是否有效
     */
    bool validateDataFormat(
        const std::vector<uint8_t>& data,
        const std::string& expected_format
    );

private:
    /**
     * @brief 转换数据格式
     * @param input 输入数据
     * @param output 输出数据
     * @param format 目标格式
     * @return 是否成功
     */
    bool convertFormat(
        const std::vector<uint8_t>& input,
        std::vector<uint8_t>& output,
        const std::string& format
    );
};

// ============================================================================
// 空格使用示例
// ============================================================================

/**
 * @brief 数学计算类
 *
 * 展示正确的空格使用
 */
class MathCalculator {
public:
    /**
     * @brief 计算两个数的和
     * @param a 第一个数
     * @param b 第二个数
     * @return 和
     */
    int add(int a, int b) const;

    /**
     * @brief 计算两个数的积
     * @param a 第一个数
     * @param b 第二个数
     * @return 积
     */
    int multiply(int a, int b) const;

    /**
     * @brief 计算幂
     * @param base 底数
     * @param exponent 指数
     * @return 幂
     */
    int power(int base, int exponent) const;

    /**
     * @brief 计算阶乘
     * @param n 输入数
     * @return 阶乘
     */
    int factorial(int n) const;
};

// ============================================================================
// 空行使用示例
// ============================================================================

/**
 * @brief 字符串工具类
 *
 * 展示正确的空行使用
 */
class StringUtils {
public:
    /**
     * @brief 去除首尾空格
     * @param str 输入字符串
     * @return 处理后的字符串
     */
    static std::string trim(const std::string& str);

    /**
     * @brief 转换为大写
     * @param str 输入字符串
     * @return 转换后的字符串
     */
    static std::string toUpperCase(const std::string& str);

    /**
     * @brief 转换为小写
     * @param str 输入字符串
     * @return 转换后的字符串
     */
    static std::string toLowerCase(const std::string& str);

    /**
     * @brief 分割字符串
     * @param str 输入字符串
     * @param delimiter 分隔符
     * @return 分割后的字符串列表
     */
    static std::vector<std::string> split(
        const std::string& str,
        char delimiter
    );

    /**
     * @brief 连接字符串
     * @param strings 字符串列表
     * @param separator 分隔符
     * @return 连接后的字符串
     */
    static std::string join(
        const std::vector<std::string>& strings,
        const std::string& separator
    );
};

}  // namespace cpp_standards

#endif  // CPP_STANDARDS_FORMATTING_H
