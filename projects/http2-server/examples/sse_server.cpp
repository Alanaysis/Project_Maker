/**
 * @file sse_server.cpp
 * @brief Server-Sent Events 服务器示例
 *
 * 本示例展示如何创建一个 SSE 服务器，包括：
 * - Server-Sent Events 支持
 * - 流式响应
 * - 实时数据推送
 */

#include "http2_server.h"
#include <iostream>
#include <sstream>
#include <iomanip>
#include <signal.h>
#include <thread>
#include <atomic>
#include <random>

using namespace http2;

static Http2Server* g_server = nullptr;
static std::atomic<bool> g_running{true};

void signal_handler(int sig) {
    if (sig == SIGINT || sig == SIGTERM) {
        std::cout << "\nShutting down server..." << std::endl;
        g_running = false;
        if (g_server) {
            g_server->stop();
        }
    }
}

// 模拟数据生成器
class DataGenerator {
public:
    struct SensorData {
        double temperature;
        double humidity;
        double pressure;
        std::string timestamp;
    };

    SensorData generate() {
        std::lock_guard<std::mutex> lock(mutex_);

        SensorData data;
        data.temperature = 20.0 + distribution_(generator_) * 10.0;
        data.humidity = 50.0 + distribution_(generator_) * 30.0;
        data.pressure = 1000.0 + distribution_(generator_) * 50.0;

        auto now = std::time(nullptr);
        char buf[64];
        std::strftime(buf, sizeof(buf), "%Y-%m-%d %H:%M:%S", std::localtime(&now));
        data.timestamp = buf;

        return data;
    }

private:
    std::mutex mutex_;
    std::random_device rd_;
    std::mt19937 generator_{rd_()};
    std::uniform_real_distribution<double> distribution_{-1.0, 1.0};
};

// JSON 工具
std::string sensor_to_json(const DataGenerator::SensorData& data) {
    std::ostringstream json;
    json << "{";
    json << "\"temperature\":" << std::fixed << std::setprecision(1) << data.temperature << ",";
    json << "\"humidity\":" << std::fixed << std::setprecision(1) << data.humidity << ",";
    json << "\"pressure\":" << std::fixed << std::setprecision(1) << data.pressure << ",";
    json << "\"timestamp\":\"" << data.timestamp << "\"";
    json << "}";
    return json.str();
}

int main() {
    signal(SIGINT, signal_handler);
    signal(SIGTERM, signal_handler);

    ServerConfig config;
    config.host = "0.0.0.0";
    config.port = 8080;
    config.num_threads = 4;

    Http2Server server(config);
    g_server = &server;

    DataGenerator data_gen;

    auto& router = server.get_router();

    // 首页
    router.get("/", [](std::shared_ptr<HttpRequest> request,
                       std::shared_ptr<HttpResponse> response) {
        response->set_status(HttpStatusCode::OK);
        response->set_content_type("text/html");
        response->set_body(R"(
<!DOCTYPE html>
<html>
<head>
    <title>SSE Server</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; }
        h1 { color: #333; }
        #events { background: #f5f5f5; padding: 20px; border-radius: 5px; min-height: 300px; }
        .event { margin: 10px 0; padding: 10px; background: white; border-radius: 3px; }
        .timestamp { color: #666; font-size: 0.9em; }
    </style>
</head>
<body>
    <h1>Server-Sent Events Example</h1>
    <p>Real-time sensor data updates:</p>
    <div id="events"></div>

    <script>
        const eventsDiv = document.getElementById('events');
        const eventSource = new EventSource('/api/sse/sensors');

        eventSource.onmessage = function(event) {
            const data = JSON.parse(event.data);
            const div = document.createElement('div');
            div.className = 'event';
            div.innerHTML = `
                <div class="timestamp">${data.timestamp}</div>
                <div>Temperature: ${data.temperature.toFixed(1)}°C</div>
                <div>Humidity: ${data.humidity.toFixed(1)}%</div>
                <div>Pressure: ${data.pressure.toFixed(1)} hPa</div>
            `;
            eventsDiv.insertBefore(div, eventsDiv.firstChild);

            // 限制显示数量
            while (eventsDiv.children.length > 10) {
                eventsDiv.removeChild(eventsDiv.lastChild);
            }
        };

        eventSource.onerror = function() {
            console.error('SSE connection error');
        };
    </script>
</body>
</html>
        )");
    });

    // SSE 端点
    router.get("/api/sse/sensors", [&data_gen](std::shared_ptr<HttpRequest> request,
                                               std::shared_ptr<HttpResponse> response) {
        response->set_status(HttpStatusCode::OK);
        response->set_content_type("text/event-stream");
        response->set_header("cache-control", "no-cache");
        response->set_header("connection", "keep-alive");
        response->set_header("access-control-allow-origin", "*");

        // 发送初始事件
        response->send_sse_event("message", sensor_to_json(data_gen.generate()));
    });

    // 数据生成线程
    std::thread data_thread([&data_gen, &server]() {
        while (g_running) {
            std::this_thread::sleep_for(std::chrono::seconds(1));

            // 广播新数据到所有 SSE 连接
            // 实际实现中需要维护连接列表
            auto data = data_gen.generate();
            std::cout << "Generated: " << sensor_to_json(data) << std::endl;
        }
    });

    // 启动服务器
    std::cout << "Starting SSE server..." << std::endl;

    if (!server.start()) {
        std::cerr << "Failed to start server" << std::endl;
        return 1;
    }

    std::cout << "Server started on http://localhost:8080" << std::endl;
    std::cout << "Press Ctrl+C to stop." << std::endl;

    while (server.is_running()) {
        std::this_thread::sleep_for(std::chrono::seconds(1));
    }

    if (data_thread.joinable()) {
        data_thread.join();
    }

    return 0;
}
