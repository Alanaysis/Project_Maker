/**
 * @file string_contains_example.cpp
 * @brief C++23 std::string::contains 示例
 *
 * C++23 为 std::string 添加了 contains 方法，简化字符串查找。
 *
 * 主要特点：
 * - 简化字符串查找
 * - 支持字符和字符串
 * - 返回 bool 值
 * - 更简洁的语法
 *
 * 编译命令：
 * g++ -std=c++23 -o string_contains_example string_contains_example.cpp
 */

#include <iostream>
#include <string>
#include <string_view>
#include <vector>
#include <algorithm>

// ========== 1. 基本用法 ==========

void basic_usage() {
    std::cout << "=== 基本用法 ===" << std::endl;

    std::string text = "Hello, World!";

    // 检查是否包含字符
    std::cout << "Contains 'W': " << (text.contains('W') ? "yes" : "no") << std::endl;
    std::cout << "Contains 'X': " << (text.contains('X') ? "yes" : "no") << std::endl;

    // 检查是否包含子串
    std::cout << "Contains 'World': " << (text.contains("World") ? "yes" : "no") << std::endl;
    std::cout << "Contains 'xyz': " << (text.contains("xyz") ? "yes" : "no") << std::endl;
}

// ========== 2. 实际应用：输入验证 ==========

void input_validation() {
    std::cout << "\n=== 实际应用：输入验证 ===" << std::endl;

    std::string email = "user@example.com";

    // 验证邮箱格式
    bool has_at = email.contains('@');
    bool has_dot = email.contains('.');

    std::cout << "Email: " << email << std::endl;
    std::cout << "Has @: " << (has_at ? "yes" : "no") << std::endl;
    std::cout << "Has .: " << (has_dot ? "yes" : "no") << std::endl;
    std::cout << "Valid format: " << (has_at && has_dot ? "yes" : "no") << std::endl;
}

// ========== 3. 实际应用：日志过滤 ==========

void log_filtering() {
    std::cout << "\n=== 实际应用：日志过滤 ===" << std::endl;

    std::vector<std::string> logs = {
        "[INFO] Application started",
        "[ERROR] Connection failed",
        "[DEBUG] Loading config",
        "[ERROR] Timeout occurred",
        "[INFO] Ready to serve"
    };

    // 过滤错误日志
    std::cout << "Error logs:" << std::endl;
    for (const auto& log : logs) {
        if (log.contains("[ERROR]")) {
            std::cout << "  " << log << std::endl;
        }
    }
}

// ========== 4. 实际应用：文件类型检查 ==========

void file_type_check() {
    std::cout << "\n=== 实际应用：文件类型检查 ===" << std::endl;

    std::vector<std::string> files = {
        "document.pdf",
        "image.png",
        "script.py",
        "data.csv",
        "backup.tar.gz"
    };

    // 检查文件类型
    for (const auto& file : files) {
        std::cout << file << ": ";
        if (file.contains(".pdf")) {
            std::cout << "PDF document";
        } else if (file.contains(".png") || file.contains(".jpg")) {
            std::cout << "Image file";
        } else if (file.contains(".py")) {
            std::cout << "Python script";
        } else if (file.contains(".csv")) {
            std::cout << "CSV data";
        } else if (file.contains(".gz")) {
            std::cout << "Compressed file";
        } else {
            std::cout << "Unknown type";
        }
        std::cout << std::endl;
    }
}

// ========== 5. 实际应用：URL 解析 ==========

void url_parsing() {
    std::cout << "\n=== 实际应用：URL 解析 ===" << std::endl;

    std::vector<std::string> urls = {
        "https://example.com/path",
        "http://localhost:8080",
        "ftp://files.example.com",
        "https://api.example.com/v1/users"
    };

    // 解析 URL
    for (const auto& url : urls) {
        std::cout << "URL: " << url << std::endl;
        std::cout << "  HTTPS: " << (url.contains("https") ? "yes" : "no") << std::endl;
        std::cout << "  HTTP: " << (url.contains("http://") ? "yes" : "no") << std::endl;
        std::cout << "  FTP: " << (url.contains("ftp") ? "yes" : "no") << std::endl;
        std::cout << "  Has port: " << (url.contains(":") ? "yes" : "no") << std::endl;
    }
}

// ========== 6. 实际应用：敏感词过滤 ==========

void sensitive_word_filter() {
    std::cout << "\n=== 实际应用：敏感词过滤 ===" << std::endl;

    std::vector<std::string> sensitive_words = {"spam", "hack", "cheat"};
    std::vector<std::string> messages = {
        "Hello, how are you?",
        "This is spam content",
        "Let's hack the system",
        "Normal message",
        "Don't cheat in the game"
    };

    // 过滤敏感词
    std::cout << "Filtered messages:" << std::endl;
    for (const auto& msg : messages) {
        bool contains_sensitive = false;
        for (const auto& word : sensitive_words) {
            if (msg.contains(word)) {
                contains_sensitive = true;
                break;
            }
        }

        if (contains_sensitive) {
            std::cout << "  [BLOCKED] " << msg << std::endl;
        } else {
            std::cout << "  [ALLOWED] " << msg << std::endl;
        }
    }
}

// ========== 7. 实际应用：配置解析 ==========

void config_parsing() {
    std::cout << "\n=== 实际应用：配置解析 ===" << std::endl;

    std::vector<std::string> config_lines = {
        "host=localhost",
        "port=8080",
        "# This is a comment",
        "debug=true",
        "  ",
        "database=postgres"
    };

    // 解析配置
    std::cout << "Parsed configuration:" << std::endl;
    for (const auto& line : config_lines) {
        // 跳过注释和空行
        if (line.contains('#') || line.empty() || line.find_first_not_of(' ') == std::string::npos) {
            continue;
        }

        if (line.contains('=')) {
            std::cout << "  " << line << std::endl;
        }
    }
}

// ========== 8. 实际应用：数据验证 ==========

void data_validation() {
    std::cout << "\n=== 实际应用：数据验证 ===" << std::endl;

    std::vector<std::string> passwords = {
        "password123",
        "P@ssw0rd!",
        "abc",
        "StrongP@ss1",
        "12345678"
    };

    // 验证密码强度
    std::cout << "Password validation:" << std::endl;
    for (const auto& pwd : passwords) {
        bool has_upper = false;
        bool has_lower = false;
        bool has_digit = false;
        bool has_special = false;

        for (char c : pwd) {
            if (std::isupper(c)) has_upper = true;
            if (std::islower(c)) has_lower = true;
            if (std::isdigit(c)) has_digit = true;
            if (!std::isalnum(c)) has_special = true;
        }

        bool is_strong = pwd.length() >= 8 && has_upper && has_lower && has_digit && has_special;

        std::cout << "  " << pwd << ": " << (is_strong ? "STRONG" : "WEAK") << std::endl;
    }
}

// ========== 9. 实际应用：搜索功能 ==========

void search_functionality() {
    std::cout << "\n=== 实际应用：搜索功能 ===" << std::endl;

    std::vector<std::string> documents = {
        "The quick brown fox jumps over the lazy dog",
        "C++23 introduces many new features",
        "The fox is a clever animal",
        "Programming in C++ is fun",
        "The dog is man's best friend"
    };

    std::string search_term = "fox";

    // 搜索包含关键词的文档
    std::cout << "Search results for '" << search_term << "':" << std::endl;
    for (size_t i = 0; i < documents.size(); ++i) {
        if (documents[i].contains(search_term)) {
            std::cout << "  Document " << i << ": " << documents[i] << std::endl;
        }
    }
}

// ========== 10. 实际应用：命令解析 ==========

void command_parsing() {
    std::cout << "\n=== 实际应用：命令解析 ===" << std::endl;

    std::vector<std::string> commands = {
        "GET /api/users",
        "POST /api/users",
        "DELETE /api/users/1",
        "PUT /api/users/1",
        "GET /api/products"
    };

    // 解析 HTTP 方法
    std::cout << "Command parsing:" << std::endl;
    for (const auto& cmd : commands) {
        std::cout << "  " << cmd << " -> ";
        if (cmd.contains("GET")) {
            std::cout << "Read operation";
        } else if (cmd.contains("POST")) {
            std::cout << "Create operation";
        } else if (cmd.contains("PUT")) {
            std::cout << "Update operation";
        } else if (cmd.contains("DELETE")) {
            std::cout << "Delete operation";
        }
        std::cout << std::endl;
    }
}

int main() {
    std::cout << "C++23 std::string::contains 示例\n" << std::endl;

    basic_usage();
    input_validation();
    log_filtering();
    file_type_check();
    url_parsing();
    sensitive_word_filter();
    config_parsing();
    data_validation();
    search_functionality();
    command_parsing();

    return 0;
}
