/**
 * 17_std_stop_token.cpp - C++20 std::stop_token 和 std::stop_source
 *
 * stop_token 提供了协作式线程取消机制。
 *
 * 核心要点：
 * 1. std::stop_token - 检查停止请求
 * 2. std::stop_source - 发起停止请求
 * 3. std::stop_callback - 停止时回调
 * 4. 与 jthread 的集成
 * 5. 线程安全的停止机制
 */

#include <iostream>
#include <thread>
#include <stop_token>
#include <chrono>
#include <string>
#include <vector>
#include <atomic>

using namespace std::chrono_literals;

// ============================================================
// 1. 基本 stop_token 用法
// ============================================================

void basic_stop_token() {
    std::cout << "【1. 基本 stop_token】\n";

    std::stop_source source;
    std::stop_token token = source.get_token();

    std::jthread worker([token]() {
        int count = 0;
        while (!token.stop_requested()) {
            std::cout << "  工作中... " << ++count << "\n";
            std::this_thread::sleep_for(200ms);
        }
        std::cout << "  收到停止信号，退出\n";
    });

    std::this_thread::sleep_for(700ms);
    std::cout << "  主线程请求停止\n";
    source.request_stop();
    // jthread 析构时自动 join
}

// ============================================================
// 2. stop_source 深入使用
// ============================================================

void stop_source_details() {
    std::cout << "\n【2. stop_source 详解】\n";

    std::stop_source source;

    std::cout << "  stop_possible: " << std::boolalpha << source.stop_possible() << "\n";
    std::cout << "  stop_requested: " << source.stop_requested() << "\n";

    source.request_stop();

    std::cout << "  请求停止后:\n";
    std::cout << "  stop_requested: " << source.stop_requested() << "\n";

    // 再次请求 - 返回 false（已经请求过了）
    bool result = source.request_stop();
    std::cout << "  再次请求: " << result << " (false 表示之前已请求)\n";
}

// ============================================================
// 3. stop_callback - 停止回调
// ============================================================

void stop_callback_demo() {
    std::cout << "\n【3. stop_callback 停止回调】\n";

    std::stop_source source;
    std::stop_token token = source.get_token();

    // 注册多个回调
    std::stop_callback cb1(token, []() {
        std::cout << "  [回调1] 清理资源 A\n";
    });

    std::stop_callback cb2(token, []() {
        std::cout << "  [回调2] 清理资源 B\n";
    });

    std::stop_callback cb3(token, []() {
        std::cout << "  [回调3] 保存状态\n";
    });

    std::cout << "  触发停止...\n";
    source.request_stop();
    // 回调按注册的相反顺序执行（LIFO）
}

// ============================================================
// 4. 多线程协作取消
// ============================================================

void cooperative_cancel() {
    std::cout << "\n【4. 多线程协作取消】\n";

    std::stop_source source;
    std::vector<std::jthread> workers;
    std::atomic<int> completed{0};

    for (int i = 0; i < 3; ++i) {
        workers.emplace_back([i, token = source.get_token(), &completed]() {
            while (!token.stop_requested()) {
                // 模拟工作
                std::this_thread::sleep_for(100ms);
            }
            ++completed;
            std::cout << "  Worker-" << i << " 已停止\n";
        });
    }

    std::this_thread::sleep_for(500ms);
    std::cout << "  停止所有 worker (" << completed << " 已完成)\n";
    source.request_stop();

    std::this_thread::sleep_for(200ms);
    std::cout << "  全部完成: " << completed << "/3\n";
}

// ============================================================
// 5. 超时取消
// ============================================================

void timeout_cancel() {
    std::cout << "\n【5. 超时取消】\n";

    std::stop_source source;
    std::stop_token token = source.get_token();

    std::jthread worker([token]() {
        // 模拟长时间运行的任务
        for (int i = 0; i < 100; ++i) {
            if (token.stop_requested()) {
                std::cout << "  任务被取消 (进度: " << i << "%)\n";
                return;
            }
            std::this_thread::sleep_for(50ms);
        }
        std::cout << "  任务完成\n";
    });

    // 2 秒后超时取消
    std::this_thread::sleep_for(2s);
    std::cout << "  超时，取消任务\n";
    source.request_stop();
}

// ============================================================
// Main
// ============================================================

int main() {
    std::cout << "=== C++20 std::stop_token 示例 ===\n\n";

    basic_stop_token();
    stop_source_details();
    stop_callback_demo();
    cooperative_cancel();
    timeout_cancel();

    std::cout << "\n=== stop_token 示例完成 ===\n";
    return 0;
}
