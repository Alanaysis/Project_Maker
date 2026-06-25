/**
 * @file api_server.cpp
 * @brief API 服务器示例
 *
 * 本示例展示如何创建一个 RESTful API 服务器，包括：
 * - RESTful 路由
 * - JSON 处理
 * - 请求验证
 * - 错误处理
 */

#include "http2_server.h"
#include <iostream>
#include <signal.h>
#include <map>
#include <mutex>
#include <sstream>

using namespace http2;

static Http2Server* g_server = nullptr;

void signal_handler(int sig) {
    if (sig == SIGINT || sig == SIGTERM) {
        std::cout << "\nShutting down server..." << std::endl;
        if (g_server) {
            g_server->stop();
        }
    }
}

// 简单的内存数据库
class Database {
public:
    struct User {
        int id;
        std::string name;
        std::string email;
    };

    struct Post {
        int id;
        int user_id;
        std::string title;
        std::string content;
    };

    // 用户操作
    std::vector<User> get_users() {
        std::lock_guard<std::mutex> lock(mutex_);
        std::vector<User> result;
        for (const auto& pair : users_) {
            result.push_back(pair.second);
        }
        return result;
    }

    User* get_user(int id) {
        std::lock_guard<std::mutex> lock(mutex_);
        auto it = users_.find(id);
        if (it != users_.end()) {
            return &it->second;
        }
        return nullptr;
    }

    User create_user(const std::string& name, const std::string& email) {
        std::lock_guard<std::mutex> lock(mutex_);
        int id = next_user_id_++;
        users_[id] = {id, name, email};
        return users_[id];
    }

    bool update_user(int id, const std::string& name, const std::string& email) {
        std::lock_guard<std::mutex> lock(mutex_);
        auto it = users_.find(id);
        if (it != users_.end()) {
            it->second.name = name;
            it->second.email = email;
            return true;
        }
        return false;
    }

    bool delete_user(int id) {
        std::lock_guard<std::mutex> lock(mutex_);
        return users_.erase(id) > 0;
    }

    // 文章操作
    std::vector<Post> get_posts(int user_id = 0) {
        std::lock_guard<std::mutex> lock(mutex_);
        std::vector<Post> result;
        for (const auto& pair : posts_) {
            if (user_id == 0 || pair.second.user_id == user_id) {
                result.push_back(pair.second);
            }
        }
        return result;
    }

    Post* get_post(int id) {
        std::lock_guard<std::mutex> lock(mutex_);
        auto it = posts_.find(id);
        if (it != posts_.end()) {
            return &it->second;
        }
        return nullptr;
    }

    Post create_post(int user_id, const std::string& title, const std::string& content) {
        std::lock_guard<std::mutex> lock(mutex_);
        int id = next_post_id_++;
        posts_[id] = {id, user_id, title, content};
        return posts_[id];
    }

private:
    std::mutex mutex_;
    std::map<int, User> users_;
    std::map<int, Post> posts_;
    int next_user_id_ = 1;
    int next_post_id_ = 1;
};

// JSON 工具函数
namespace json_util {

std::string escape(const std::string& str) {
    std::string result;
    for (char c : str) {
        switch (c) {
            case '"': result += "\\\""; break;
            case '\\': result += "\\\\"; break;
            case '\n': result += "\\n"; break;
            case '\r': result += "\\r"; break;
            case '\t': result += "\\t"; break;
            default: result += c;
        }
    }
    return result;
}

std::string user_to_json(const Database::User& user) {
    std::ostringstream json;
    json << "{\"id\":" << user.id
         << ",\"name\":\"" << escape(user.name) << "\""
         << ",\"email\":\"" << escape(user.email) << "\"}";
    return json.str();
}

std::string post_to_json(const Database::Post& post) {
    std::ostringstream json;
    json << "{\"id\":" << post.id
         << ",\"user_id\":" << post.user_id
         << ",\"title\":\"" << escape(post.title) << "\""
         << ",\"content\":\"" << escape(post.content) << "\"}";
    return json.str();
}

std::string array_to_json(const std::vector<std::string>& items) {
    std::ostringstream json;
    json << "[";
    for (size_t i = 0; i < items.size(); ++i) {
        if (i > 0) json << ",";
        json << items[i];
    }
    json << "]";
    return json.str();
}

// 简单的 JSON 解析（仅用于示例）
std::map<std::string, std::string> parse_json(const std::string& str) {
    std::map<std::string, std::string> result;
    // 简化实现，实际应该使用 JSON 库
    return result;
}

} // namespace json_util

int main() {
    signal(SIGINT, signal_handler);
    signal(SIGTERM, signal_handler);

    ServerConfig config;
    config.host = "0.0.0.0";
    config.port = 8080;
    config.num_threads = 4;

    Http2Server server(config);
    g_server = &server;

    Database db;

    // 添加示例数据
    db.create_user("Alice", "alice@example.com");
    db.create_user("Bob", "bob@example.com");
    db.create_post(1, "First Post", "Hello World!");
    db.create_post(2, "Second Post", "HTTP/2 is great!");

    auto& router = server.get_router();

    // CORS 中间件
    router.use([](std::shared_ptr<HttpRequest> request,
                  std::shared_ptr<HttpResponse> response,
                  std::function<void()> next) {
        response->set_cors_headers();
        if (request->get_method() == HttpMethod::OPTIONS) {
            response->set_status(HttpStatusCode::NO_CONTENT);
            return false;
        }
        next();
        return true;
    });

    // 日志中间件
    router.use([](std::shared_ptr<HttpRequest> request,
                  std::shared_ptr<HttpResponse> response,
                  std::function<void()> next) {
        std::cout << request->get_method_string() << " " << request->get_path() << std::endl;
        next();
        return true;
    });

    // API 路由

    // 获取所有用户
    router.get("/api/users", [&db](std::shared_ptr<HttpRequest> request,
                                   std::shared_ptr<HttpResponse> response) {
        auto users = db.get_users();
        std::vector<std::string> json_users;
        for (const auto& user : users) {
            json_users.push_back(json_util::user_to_json(user));
        }

        response->set_status(HttpStatusCode::OK);
        response->set_content_type("application/json");
        response->set_body(json_util::array_to_json(json_users));
    });

    // 获取单个用户
    router.get("/api/users/:id", [&db](std::shared_ptr<HttpRequest> request,
                                       std::shared_ptr<HttpResponse> response) {
        // 简化处理，实际应该解析路径参数
        response->set_status(HttpStatusCode::OK);
        response->set_content_type("application/json");

        auto users = db.get_users();
        if (!users.empty()) {
            response->set_body(json_util::user_to_json(users[0]));
        } else {
            response->set_status(HttpStatusCode::NOT_FOUND);
            response->set_body("{\"error\": \"User not found\"}");
        }
    });

    // 创建用户
    router.post("/api/users", [&db](std::shared_ptr<HttpRequest> request,
                                    std::shared_ptr<HttpResponse> response) {
        // 简化处理，实际应该解析 JSON 请求体
        auto user = db.create_user("New User", "new@example.com");

        response->set_status(HttpStatusCode::CREATED);
        response->set_content_type("application/json");
        response->set_body(json_util::user_to_json(user));
    });

    // 获取所有文章
    router.get("/api/posts", [&db](std::shared_ptr<HttpRequest> request,
                                   std::shared_ptr<HttpResponse> response) {
        auto posts = db.get_posts();
        std::vector<std::string> json_posts;
        for (const auto& post : posts) {
            json_posts.push_back(json_util::post_to_json(post));
        }

        response->set_status(HttpStatusCode::OK);
        response->set_content_type("application/json");
        response->set_body(json_util::array_to_json(json_posts));
    });

    // 创建文章
    router.post("/api/posts", [&db](std::shared_ptr<HttpRequest> request,
                                    std::shared_ptr<HttpResponse> response) {
        // 简化处理，实际应该解析 JSON 请求体
        auto post = db.create_post(1, "New Post", "Post content");

        response->set_status(HttpStatusCode::CREATED);
        response->set_content_type("application/json");
        response->set_body(json_util::post_to_json(post));
    });

    // 用户的文章
    router.get("/api/users/:id/posts", [&db](std::shared_ptr<HttpRequest> request,
                                             std::shared_ptr<HttpResponse> response) {
        // 简化处理
        auto posts = db.get_posts(1);
        std::vector<std::string> json_posts;
        for (const auto& post : posts) {
            json_posts.push_back(json_util::post_to_json(post));
        }

        response->set_status(HttpStatusCode::OK);
        response->set_content_type("application/json");
        response->set_body(json_util::array_to_json(json_posts));
    });

    // 健康检查
    router.get("/health", [](std::shared_ptr<HttpRequest> request,
                             std::shared_ptr<HttpResponse> response) {
        response->set_status(HttpStatusCode::OK);
        response->set_content_type("application/json");
        response->set_body("{\"status\": \"healthy\", \"version\": \"1.0.0\"}");
    });

    // API 文档
    router.get("/", [](std::shared_ptr<HttpRequest> request,
                       std::shared_ptr<HttpResponse> response) {
        response->set_status(HttpStatusCode::OK);
        response->set_content_type("text/html");
        response->set_body(R"(
<!DOCTYPE html>
<html>
<head>
    <title>API Server</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; }
        h1 { color: #333; }
        .endpoint { background: #f5f5f5; padding: 10px; margin: 10px 0; border-radius: 5px; }
        .method { font-weight: bold; color: #007bff; }
    </style>
</head>
<body>
    <h1>RESTful API Server</h1>
    <h2>Users API</h2>
    <div class="endpoint"><span class="method">GET</span> /api/users - List all users</div>
    <div class="endpoint"><span class="method">GET</span> /api/users/:id - Get user by ID</div>
    <div class="endpoint"><span class="method">POST</span> /api/users - Create new user</div>
    <h2>Posts API</h2>
    <div class="endpoint"><span class="method">GET</span> /api/posts - List all posts</div>
    <div class="endpoint"><span class="method">POST</span> /api/posts - Create new post</div>
    <div class="endpoint"><span class="method">GET</span> /api/users/:id/posts - Get user's posts</div>
</body>
</html>
        )");
    });

    // 启动服务器
    std::cout << "Starting API server..." << std::endl;

    if (!server.start()) {
        std::cerr << "Failed to start server" << std::endl;
        return 1;
    }

    std::cout << "Server started on http://localhost:8080" << std::endl;
    std::cout << "Press Ctrl+C to stop." << std::endl;

    while (server.is_running()) {
        std::this_thread::sleep_for(std::chrono::seconds(1));
    }

    return 0;
}
