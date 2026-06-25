/**
 * @file good_formatting.cpp
 * @brief 良好代码格式示例
 *
 * 本文件展示符合 C++ 代码格式规范的良好代码示例。
 * 遵循以下格式规则：
 * - 2 空格缩进
 * - K&R 大括号风格
 * - 80 列限制
 * - 正确的空格使用
 * - 合理的空行使用
 */

#include <iostream>
#include <string>
#include <vector>
#include <memory>
#include <algorithm>

// ============================================================================
// 缩进风格示例 - 使用 2 空格缩进
// ============================================================================

/**
 * @brief 用户管理器类
 *
 * 展示正确的缩进风格
 */
class UserManager {
public:
    /**
     * @brief 构造函数
     * @param max_users 最大用户数量
     */
    explicit UserManager(size_t max_users)
        : max_users_(max_users)
        , user_count_(0) {}

    /**
     * @brief 添加用户
     * @param name 用户名
     * @param email 邮箱
     * @return 是否成功
     */
    bool addUser(const std::string& name, const std::string& email) {
        if (user_count_ >= max_users_) {
            return false;
        }

        if (name.empty() || email.empty()) {
            return false;
        }

        users_.push_back({name, email});
        ++user_count_;

        return true;
    }

    /**
     * @brief 查找用户
     * @param name 用户名
     * @return 用户索引，-1 表示未找到
     */
    int findUser(const std::string& name) const {
        for (size_t i = 0; i < users_.size(); ++i) {
            if (users_[i].name == name) {
                return static_cast<int>(i);
            }
        }

        return -1;
    }

    /**
     * @brief 获取用户数量
     * @return 用户数量
     */
    size_t getUserCount() const {
        return user_count_;
    }

private:
    /// 用户信息结构体
    struct UserInfo {
        std::string name;    ///< 用户名
        std::string email;   ///< 邮箱
    };

    size_t max_users_;              ///< 最大用户数量
    size_t user_count_;             ///< 当前用户数量
    std::vector<UserInfo> users_;   ///< 用户列表
};

// ============================================================================
// 大括号风格示例 - 使用 K&R 风格
// ============================================================================

/**
 * @brief 日志记录器类
 *
 * 展示正确的 K&R 大括号风格
 */
class Logger {
public:
    /**
     * @brief 构造函数
     * @param log_file 日志文件路径
     */
    explicit Logger(const std::string& log_file)
        : log_file_(log_file)
        , is_open_(false) {
        // 初始化日志文件
        if (!log_file_.empty()) {
            is_open_ = true;
        }
    }

    /**
     * @brief 析构函数
     */
    ~Logger() {
        if (is_open_) {
            // 关闭日志文件
            is_open_ = false;
        }
    }

    /**
     * @brief 记录日志
     * @param level 日志级别
     * @param message 日志消息
     */
    void log(const std::string& level, const std::string& message) {
        if (!is_open_) {
            return;
        }

        // 格式化日志消息
        std::string formatted = "[" + level + "] " + message;

        // 输出日志
        std::cout << formatted << std::endl;
    }

private:
    std::string log_file_;  ///< 日志文件路径
    bool is_open_;          ///< 是否已打开
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
     * @param input 输入数据
     * @param output 输出数据
     * @param mode 处理模式
     * @return 是否成功
     */
    bool processData(
        const std::vector<int>& input,
        std::vector<int>& output,
        int mode
    ) {
        if (input.empty()) {
            return false;
        }

        output.clear();
        output.reserve(input.size());

        for (const auto& item : input) {
            int processed = processItem(item, mode);
            output.push_back(processed);
        }

        return true;
    }

private:
    /**
     * @brief 处理单个数据项
     * @param item 数据项
     * @param mode 处理模式
     * @return 处理后的数据
     */
    int processItem(int item, int mode) {
        switch (mode) {
            case 0:
                return item * 2;
            case 1:
                return item + 10;
            case 2:
                return item * item;
            default:
                return item;
        }
    }
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
    int add(int a, int b) const {
        return a + b;
    }

    /**
     * @brief 计算两个数的积
     * @param a 第一个数
     * @param b 第二个数
     * @return 积
     */
    int multiply(int a, int b) const {
        return a * b;
    }

    /**
     * @brief 计算幂
     * @param base 底数
     * @param exponent 指数
     * @return 幂
     */
    int power(int base, int exponent) const {
        if (exponent == 0) {
            return 1;
        }

        int result = 1;
        for (int i = 0; i < exponent; ++i) {
            result *= base;
        }

        return result;
    }

    /**
     * @brief 计算阶乘
     * @param n 输入数
     * @return 阶乘
     */
    int factorial(int n) const {
        if (n <= 1) {
            return 1;
        }

        return n * factorial(n - 1);
    }
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
    static std::string trim(const std::string& str) {
        size_t start = str.find_first_not_of(" \t\n\r");
        size_t end = str.find_last_not_of(" \t\n\r");

        if (start == std::string::npos) {
            return "";
        }

        return str.substr(start, end - start + 1);
    }

    /**
     * @brief 转换为大写
     * @param str 输入字符串
     * @return 转换后的字符串
     */
    static std::string toUpperCase(const std::string& str) {
        std::string result = str;
        std::transform(
            result.begin(),
            result.end(),
            result.begin(),
            [](unsigned char c) { return std::toupper(c); }
        );
        return result;
    }

    /**
     * @brief 转换为小写
     * @param str 输入字符串
     * @return 转换后的字符串
     */
    static std::string toLowerCase(const std::string& str) {
        std::string result = str;
        std::transform(
            result.begin(),
            result.end(),
            result.begin(),
            [](unsigned char c) { return std::tolower(c); }
        );
        return result;
    }

    /**
     * @brief 分割字符串
     * @param str 输入字符串
     * @param delimiter 分隔符
     * @return 分割后的字符串列表
     */
    static std::vector<std::string> split(
        const std::string& str,
        char delimiter
    ) {
        std::vector<std::string> result;
        std::string current;

        for (char c : str) {
            if (c == delimiter) {
                if (!current.empty()) {
                    result.push_back(current);
                    current.clear();
                }
            } else {
                current += c;
            }
        }

        if (!current.empty()) {
            result.push_back(current);
        }

        return result;
    }
};

// ============================================================================
// 演示函数
// ============================================================================

/**
 * @brief 演示良好代码格式
 */
void demonstrateGoodFormatting() {
    std::cout << "=== 良好代码格式示例 ===" << std::endl;

    // 缩进风格
    std::cout << "\n1. 缩进风格 (2 空格):" << std::endl;
    UserManager manager(10);
    manager.addUser("Alice", "alice@example.com");
    manager.addUser("Bob", "bob@example.com");
    std::cout << "   用户数量: " << manager.getUserCount() << std::endl;

    // 大括号风格
    std::cout << "\n2. 大括号风格 (K&R):" << std::endl;
    Logger logger("app.log");
    logger.log("INFO", "应用程序启动");
    logger.log("DEBUG", "调试信息");

    // 行长度限制
    std::cout << "\n3. 行长度限制 (80 列):" << std::endl;
    DataProcessor processor;
    std::vector<int> input = {1, 2, 3, 4, 5};
    std::vector<int> output;
    processor.processData(input, output, 0);
    std::cout << "   处理结果: ";
    for (const auto& item : output) {
        std::cout << item << " ";
    }
    std::cout << std::endl;

    // 空格使用
    std::cout << "\n4. 空格使用:" << std::endl;
    MathCalculator calc;
    std::cout << "   2 + 3 = " << calc.add(2, 3) << std::endl;
    std::cout << "   2 * 3 = " << calc.multiply(2, 3) << std::endl;
    std::cout << "   2^10 = " << calc.power(2, 10) << std::endl;
    std::cout << "   5! = " << calc.factorial(5) << std::endl;

    // 空行使用
    std::cout << "\n5. 空行使用:" << std::endl;
    std::string str = "  Hello, World!  ";
    std::cout << "   trim('" << str << "') = '"
              << StringUtils::trim(str) << "'" << std::endl;
    std::cout << "   toUpperCase('hello') = '"
              << StringUtils::toUpperCase("hello") << "'" << std::endl;
}
