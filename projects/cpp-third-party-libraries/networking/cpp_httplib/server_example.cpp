/**
 * @file server_example.cpp
 * @brief cpp-httplib HTTP 服务器示例
 * @details 展示如何使用 cpp-httplib 创建 HTTP 服务器
 *          cpp-httplib 是一个简单易用的单头文件 HTTP 库
 *          支持 GET/POST/PUT/DELETE 等方法
 */

#include <iostream>
#include <string>
#include <map>
#include <httplib.h>

/**
 * @brief 基础服务器示例
 * @details 创建简单的 HTTP 服务器
 */
void basic_server() {
    std::cout << "=== 基础服务器 ===" << std::endl;

    httplib::Server svr;

    // GET 请求处理
    svr.Get("/", [](const httplib::Request& req, httplib::Response& res) {
        res.set_content("Hello, World!", "text/plain");
    });

    // 带参数的 GET 请求
    svr.Get("/hello/:name", [](const httplib::Request& req, httplib::Response& res) {
        std::string name = req.path_params.at("name");
        res.set_content("Hello, " + name + "!", "text/plain");
    });

    std::cout << "Server starting on port 8080..." << std::endl;
    std::cout << "Try: curl http://localhost:8080/" << std::endl;
    std::cout << "Try: curl http://localhost:8080/hello/World" << std::endl;

    // 启动服务器（阻塞）
    svr.listen("0.0.0.0", 8080);
}

/**
 * @brief JSON API 示例
 * @details 创建 RESTful JSON API
 */
void json_api_server() {
    std::cout << "=== JSON API 服务器 ===" << std::endl;

    httplib::Server svr;

    // 模拟数据存储
    std::map<int, std::string> users = {
        {1, "Alice"},
        {2, "Bob"},
        {3, "Charlie"}
    };

    // GET /api/users - 获取所有用户
    svr.Get("/api/users", [&users](const httplib::Request& req, httplib::Response& res) {
        std::string json = "[";
        bool first = true;
        for (const auto& [id, name] : users) {
            if (!first) json += ",";
            json += "{\"id\":" + std::to_string(id) + ",\"name\":\"" + name + "\"}";
            first = false;
        }
        json += "]";
        res.set_content(json, "application/json");
    });

    // GET /api/users/:id - 获取单个用户
    svr.Get("/api/users/:id", [&users](const httplib::Request& req, httplib::Response& res) {
        int id = std::stoi(req.path_params.at("id"));
        auto it = users.find(id);
        if (it != users.end()) {
            std::string json = "{\"id\":" + std::to_string(id) + ",\"name\":\"" + it->second + "\"}";
            res.set_content(json, "application/json");
        } else {
            res.status = 404;
            res.set_content("{\"error\":\"User not found\"}", "application/json");
        }
    });

    std::cout << "JSON API server starting on port 8081..." << std::endl;

    svr.listen("0.0.0.0", 8081);
}

int main() {
    std::cout << "=== cpp-httplib 服务器示例 ===" << std::endl;
    std::cout << std::endl;

    // 选择运行哪个示例
    std::cout << "选择示例:" << std::endl;
    std::cout << "1. 基础服务器" << std::endl;
    std::cout << "2. JSON API 服务器" << std::endl;

    int choice;
    std::cin >> choice;

    switch (choice) {
        case 1:
            basic_server();
            break;
        case 2:
            json_api_server();
            break;
        default:
            std::cout << "无效选择" << std::endl;
            return 1;
    }

    return 0;
}