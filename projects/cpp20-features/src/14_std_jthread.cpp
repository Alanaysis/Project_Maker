/**
 * 14_std_jthread.cpp - C++20 std::jthread 和 std::stop_token
 *
 * std::jthread 是 C++20 引入的自动合并线程。
 *
 * 核心要点：
 * 1. 自动 join - 析构时自动 join
 * 2. 内置停止机制 - std::stop_token
 * 3. 协作式取消 - 请求停止 + 检查停止
 * 4. std::stop_source - 发起停止请求
 * 5. std::stop_callback - 停止时回调
 */

#include <iostream>
#include <thread>
#include <chrono>
#include <vector>
#include <string>
#include <atomic>
#include <functional>

using namespace std::chrono_literals;

// ============================================================
// 1. 基本 jthread 用法
// ============================================================

void basic_jthread() {
    std::cout << "【1. 基本 jthread】\n";

    // jthread 自动管理生命周期
    std::jthread t([]() {
        std::cout << "  jthread 运行中 (线程 ID: " << std::this_thread::get_id() << ")\n";
        std::this_thread::sleep_for(100ms);
        std::cout << "  jthread 完成\n";
    });

    // 不需要手动 join - 析构时自动 join
    std::cout << "  主线程等待...\n";
    // t 离开作用域时自动 join
}

// ============================================================
// 2. stop_token - 协作式取消
// ============================================================

void worker_with_stop_token(std::stop_token token, const std::string& name) {
    int count = 0;
    while (!token.stop_requested()) {
        std::cout << "  " << name << " 工作中... (" << ++count << ")\n";
        std::this_thread::sleep_for(200ms);

        // 模拟工作完成
        if (count >= 5) break;
    }

    if (token.stop_requested()) {
        std::cout << "  " << name << " 收到停止请求，优雅退出\n";
    } else {
        std::cout << "  " << name << " 工作完成\n";
    }
}

void stop_token_demo() {
    std::cout << "\n【2. stop_token 协作式取消】\n";

    std::jthread worker(worker_with_stop_token, "Worker-1");

    // 主线程等待一段时间后请求停止
    std::this_thread::sleep_for(600ms);
    std::cout << "  主线程请求停止...\n";
    worker.request_stop();

    // worker 析构时会自动 join
}

// ============================================================
// 3. stop_source - 主动控制
// ============================================================

void stop_source_demo() {
    std::cout << "\n【3. stop_source 主动控制】\n";

    std::stop_source source;

    std::jthread t([&source]() {
        auto token = source.get_token();
        int i = 0;
        while (!token.stop_requested() && i < 10) {
            std::cout << "  计数: " << ++i << "\n";
            std::this_thread::sleep_for(150ms);
        }
        std::cout << "  线程退出\n";
    });

    std::this_thread::sleep_for(500ms);
    std::cout << "  发起停止请求\n";
    source.request_stop();
}

// ============================================================
// 4. stop_callback - 停止回调
// ============================================================

void stop_callback_demo() {
    std::cout << "\n【4. stop_callback 停止回调】\n";

    std::jthread t([](std::stop_token token) {
        // 注册停止回调
        std::stop_callback callback(token, []() {
            std::cout << "  [回调] 收到停止信号！执行清理...\n";
        });

        while (!token.stop_requested()) {
            std::this_thread::sleep_for(100ms);
        }
        std::cout << "  线程正常退出\n";
    });

    std::this_thread::sleep_for(400ms);
    std::cout << "  请求停止\n";
    t.request_stop();
    std::this_thread::sleep_for(100ms);
}

// ============================================================
// 5. 多线程协作取消
// ============================================================

void multi_thread_cancel() {
    std::cout << "\n【5. 多线程协作取消】\n";

    std::stop_source source;
    std::vector<std::jthread> workers;

    for (int i = 0; i < 3; ++i) {
        workers.emplace_back([i, token = source.get_token()]() {
            while (!token.stop_requested()) {
                std::cout << "  Worker-" << i << " 运行中\n";
                std::this_thread::sleep_for(300ms);
            }
            std::cout << "  Worker-" << i << " 已停止\n";
        });
    }

    std::this_thread::sleep_for(800ms);
    std::cout << "  停止所有 worker...\n";
    source.request_stop();
    // 所有 jthread 析构时自动 join
}

// ============================================================
// 6. jthread vs thread 对比
// ============================================================

void comparison() {
    std::cout << "\n【6. jthread vs thread 对比】\n";
    std::cout << "  std::thread:\n";
    std::cout << "    - 需要手动 join() 或 detach()\n";
    std::cout << "    - 忘记 join 会崩溃\n";
    std::cout << "    - 没有内置取消机制\n\n";
    std::cout << "  std::jthread:\n";
    std::cout << "    - 析构时自动 join\n";
    std::cout << "    - 内置 stop_token 支持\n";
    std::cout << "    - 更安全、更易用\n";
}

// ============================================================
// Main
// ============================================================

int main() {
    std::cout << "=== C++20 std::jthread 示例 ===\n\n";

    basic_jthread();
    stop_token_demo();
    stop_source_demo();
    stop_callback_demo();
    multi_thread_cancel();
    comparison();

    std::cout << "\n=== jthread 示例完成 ===\n";
    return 0;
}
