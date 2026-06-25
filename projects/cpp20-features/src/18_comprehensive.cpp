/**
 * 18_comprehensive.cpp - C++20 综合示例
 *
 * 综合运用多个 C++20 特性，展示实际应用场景。
 *
 * 场景：
 * 1. 概念 + 范围 + 格式化 = 类型安全的数据处理管道
 * 2. 协程 + 同步原语 = 异步任务系统
 * 3. 三向比较 + 聚合初始化 = 配置系统
 * 4. source_location + format = 增强日志系统
 */

#include <iostream>
#include <string>
#include <vector>
#include <map>
#include <algorithm>
#include <ranges>
#include <format>
#include <concepts>
#include <compare>
#include <source_location>
#include <thread>
#include <stop_token>
#include <span>
#include <optional>
#include <functional>

using namespace std::chrono_literals;

// ============================================================
// 1. 概念约束的数据处理框架
// ============================================================

template <typename T>
concept Numeric = std::integral<T> || std::floating_point<T>;

template <typename T>
concept Printable = requires(std::ostream& os, T t) {
    { os << t } -> std::same_as<std::ostream&>;
};

// 统计结果
struct Stats {
    double mean;
    double min;
    double max;
    size_t count;

    auto operator<=>(const Stats&) const = default;
};

template <typename Formatter = std::string>
struct StatsPrinter {
    static std::string format(const Stats& s) {
        return std::format("mean={:.2f}, min={:.2f}, max={:.2f}, n={}",
                          s.mean, s.min, s.max, s.count);
    }
};

// 使用概念约束的统计函数
template <std::ranges::range R>
    requires Numeric<std::ranges::range_value_t<R>>
Stats compute_stats(R&& range) {
    Stats s{0.0, 0.0, 0.0, 0};
    bool first = true;

    for (auto val : range) {
        double v = static_cast<double>(val);
        if (first) {
            s.min = s.max = v;
            first = false;
        } else {
            s.min = std::min(s.min, v);
            s.max = std::max(s.max, v);
        }
        s.mean += v;
        ++s.count;
    }

    if (s.count > 0) s.mean /= s.count;
    return s;
}

// ============================================================
// 2. 范围管道 + 格式化
// ============================================================

struct Record {
    std::string name;
    double value;
    std::string category;
};

void data_pipeline() {
    std::cout << "【1. 概念 + 范围 + 格式化 - 数据处理管道】\n\n";

    // 模拟数据
    std::vector<Record> records = {
        {"A1", 10.5, "sensor"}, {"A2", 25.3, "sensor"},
        {"B1", 8.1, "actuator"}, {"B2", 30.7, "sensor"},
        {"C1", 15.2, "actuator"}, {"C2", 5.9, "sensor"},
    };

    // 范围管道：过滤传感器 -> 提取值 -> 排序
    auto sensor_values = records
        | std::views::filter([](const Record& r) { return r.category == "sensor"; })
        | std::views::transform([](const Record& r) { return r.value; });

    // 使用概念约束的统计函数
    auto stats = compute_stats(sensor_values);
    std::cout << "传感器统计: " << StatsPrinter<>::format(stats) << "\n";

    // 格式化表格输出
    std::cout << "\n" << std::format("| {:<6} | {:>8} | {:<10} |\n", "Name", "Value", "Category");
    std::cout << std::format("|{:-<8}|{:-<10}|{:-<12}|\n", "", "", "");
    for (const auto& r : records) {
        std::cout << std::format("| {:<6} | {:>8.1f} | {:<10} |\n", r.name, r.value, r.category);
    }
    std::cout << "\n";
}

// ============================================================
// 3. 增强日志系统
// ============================================================

class EnhancedLogger {
public:
    enum class Level { Debug, Info, Warning, Error };

    static void log(Level level, const std::string& msg,
                    std::source_location loc = std::source_location::current()) {
        static const char* level_str[] = {"DEBUG", "INFO", "WARN", "ERROR"};
        auto idx = static_cast<int>(level);
        std::cout << std::format("[{:<5}] {}:{} - {}\n",
                                level_str[idx],
                                loc.file_name(),
                                loc.line(),
                                msg);
    }
};

#define LOG_DEBUG(msg) EnhancedLogger::log(EnhancedLogger::Level::Debug, msg)
#define LOG_INFO(msg) EnhancedLogger::log(EnhancedLogger::Level::Info, msg)
#define LOG_WARN(msg) EnhancedLogger::log(EnhancedLogger::Level::Warning, msg)
#define LOG_ERROR(msg) EnhancedLogger::log(EnhancedLogger::Level::Error, msg)

// ============================================================
// 4. 配置系统 - 聚合初始化 + 三向比较
// ============================================================

struct ServerConfig {
    std::string host = "localhost";
    int port = 8080;
    int max_connections = 100;
    bool enable_ssl = false;
    double timeout_sec = 30.0;

    auto operator<=>(const ServerConfig&) const = default;
};

// ============================================================
// 5. span + 概念 = 安全的数据接口
// ============================================================

template <Numeric T>
T sum(std::span<const T> data) {
    T total{};
    for (auto v : data) total += v;
    return total;
}

template <Numeric T>
std::optional<T> safe_average(std::span<const T> data) {
    if (data.empty()) return std::nullopt;
    return sum<T>(data) / static_cast<T>(data.size());
}

// ============================================================
// 6. 综合演示
// ============================================================

void comprehensive_demo() {
    std::cout << "【2. 增强日志系统】\n";
    LOG_INFO("应用启动");
    LOG_DEBUG("加载配置");
    LOG_WARN("内存使用率 85%");
    LOG_ERROR("数据库连接失败");
    std::cout << "\n";

    std::cout << "【3. 配置系统 - 聚合初始化 + 比较】\n";
    // 聚合初始化 + 指定初始化器
    ServerConfig cfg1{
        .host = "0.0.0.0",
        .port = 443,
        .max_connections = 1000,
        .enable_ssl = true,
        .timeout_sec = 60.0
    };
    ServerConfig cfg2 = cfg1;  // 相同配置
    ServerConfig cfg3{.port = 8080};  // 默认其他值

    std::cout << std::format("cfg1 == cfg2: {}\n", cfg1 == cfg2);
    std::cout << std::format("cfg1 == cfg3: {}\n", cfg1 == cfg3);
    std::cout << std::format("cfg1 <=> cfg3: {}\n",
                            (cfg1 < cfg3) ? "less" : (cfg1 > cfg3) ? "greater" : "equal");
    std::cout << "\n";

    std::cout << "【4. span + 概念 = 安全接口】\n";
    int arr[] = {10, 20, 30, 40, 50};
    std::vector<double> vec = {1.5, 2.5, 3.5};

    auto total = sum(std::span<const int>(arr));
    auto avg = safe_average(std::span<const double>(vec));

    std::cout << "sum([10,20,30,40,50]) = " << total << "\n";
    std::cout << "avg([1.5,2.5,3.5]) = " << avg.value_or(0.0) << "\n";

    // 空 span
    std::vector<int> empty;
    auto empty_avg = safe_average(std::span<const int>(empty));
    std::cout << "avg([]) = " << (empty_avg.has_value() ? std::to_string(*empty_avg) : "nullopt") << "\n";
    std::cout << "\n";

    std::cout << "【5. 范围 + 概念 = 灵活过滤】\n";
    std::vector numbers = {1, 2, 3, 4, 5, 6, 7, 8, 9, 10};

    // 范围管道 + 概念约束
    auto pipeline = numbers
        | std::views::filter([](int x) { return x % 2 == 0; })
        | std::views::transform([](int x) { return x * x; });

    std::cout << "偶数平方: ";
    for (auto v : pipeline) std::cout << v << " ";
    std::cout << "\n";

    // 统计
    auto stats = compute_stats(pipeline);
    std::cout << "统计: " << StatsPrinter<>::format(stats) << "\n\n";

    std::cout << "【6. jthread + stop_token = 可取消任务】\n";
    std::stop_source source;

    std::jthread worker([token = source.get_token()]() {
        int progress = 0;
        while (!token.stop_requested() && progress < 100) {
            progress += 10;
            std::this_thread::sleep_for(50ms);
        }
        if (token.stop_requested()) {
            std::cout << std::format("  任务被取消 (进度: {}%)\n", progress);
        } else {
            std::cout << std::format("  任务完成 (进度: 100%)\n");
        }
    });

    std::this_thread::sleep_for(300ms);
    source.request_stop();
}

// ============================================================
// Main
// ============================================================

int main() {
    std::cout << "=== C++20 综合示例 ===\n\n";

    data_pipeline();
    comprehensive_demo();

    std::cout << "\n=== 综合示例完成 ===\n";
    return 0;
}
