/**
 * 原子浮点 (C++20)
 *
 * C++20 的原子浮点操作：
 * 1. std::atomic<float>
 * 2. std::atomic<double>
 * 3. 支持 fetch_add, fetch_sub
 * 4. 使用浮点硬件指令
 *
 * 编译：g++ -std=c++20 -pthread atomic_float.cpp -o atomic_float
 */

#include <iostream>
#include <atomic>
#include <thread>
#include <vector>
#include <cmath>
#include <iomanip>

// 示例1：基本原子浮点操作
void basic_atomic_float() {
    std::cout << "=== 基本原子浮点操作 ===" << std::endl;

    std::atomic<double> value{0.0};

    // load 和 store
    std::cout << "初始值: " << value.load() << std::endl;
    value.store(3.14);
    std::cout << "存储后: " << value.load() << std::endl;

    // exchange
    double old = value.exchange(2.71);
    std::cout << "exchange: 旧值=" << old << ", 新值=" << value.load() << std::endl;

    // fetch_add
    double prev = value.fetch_add(1.0);
    std::cout << "fetch_add(1.0): 旧值=" << prev << ", 新值=" << value.load() << std::endl;

    // fetch_sub
    prev = value.fetch_sub(0.5);
    std::cout << "fetch_sub(0.5): 旧值=" << prev << ", 新值=" << value.load() << std::endl;

    // 运算符重载
    value += 1.5;
    std::cout << "operator+= 1.5: " << value.load() << std::endl;

    value -= 0.5;
    std::cout << "operator-= 0.5: " << value.load() << std::endl;
}

// 示例2：CAS 操作
void cas_atomic_float() {
    std::cout << "\n=== CAS 操作 ===" << std::endl;

    std::atomic<double> value{1.0};

    // compare_exchange_weak
    double expected = 1.0;
    bool success = value.compare_exchange_weak(expected, 2.0);
    std::cout << "weak CAS: 成功=" << success << ", 值=" << value.load() << std::endl;

    // compare_exchange_strong
    expected = value.load();
    success = value.compare_exchange_strong(expected, 3.0);
    std::cout << "strong CAS: 成功=" << success << ", 值=" << value.load() << std::endl;
}

// 示例3：并发累加
void concurrent_accumulation() {
    std::cout << "\n=== 并发累加 ===" << std::endl;

    std::atomic<double> sum{0.0};
    const int iterations = 100000;

    auto adder = [&](int id) {
        for (int i = 0; i < iterations; ++i) {
            sum.fetch_add(1.0, std::memory_order_relaxed);
        }
    };

    std::vector<std::thread> threads;
    for (int i = 0; i < 4; ++i) {
        threads.emplace_back(adder, i);
    }

    for (auto& t : threads) {
        t.join();
    }

    std::cout << std::fixed << std::setprecision(0);
    std::cout << "最终值: " << sum.load() << std::endl;
    std::cout << "期望值: " << 4.0 * iterations << std::endl;
    std::cout << "误差: " << std::abs(sum.load() - 4.0 * iterations) << std::endl;
}

// 示例4：统计计算
class AtomicStatistics {
public:
    void add(double value) {
        sum_.fetch_add(value, std::memory_order_relaxed);
        sum_sq_.fetch_add(value * value, std::memory_order_relaxed);
        count_.fetch_add(1, std::memory_order_relaxed);
    }

    double mean() const {
        int n = count_.load(std::memory_order_relaxed);
        if (n == 0) return 0.0;
        return sum_.load(std::memory_order_relaxed) / n;
    }

    double variance() const {
        int n = count_.load(std::memory_order_relaxed);
        if (n < 2) return 0.0;
        double m = mean();
        return (sum_sq_.load(std::memory_order_relaxed) / n) - (m * m);
    }

    int count() const {
        return count_.load(std::memory_order_relaxed);
    }

private:
    std::atomic<double> sum_{0.0};
    std::atomic<double> sum_sq_{0.0};
    std::atomic<int> count_{0};
};

void statistics_demo() {
    std::cout << "\n=== 统计计算 ===" << std::endl;

    AtomicStatistics stats;

    auto adder = [&](int id) {
        for (int i = 0; i < 10000; ++i) {
            double value = static_cast<double>(id * 10000 + i) / 1000.0;
            stats.add(value);
        }
    };

    std::vector<std::thread> threads;
    for (int i = 0; i < 4; ++i) {
        threads.emplace_back(adder, i);
    }

    for (auto& t : threads) {
        t.join();
    }

    std::cout << std::fixed << std::setprecision(2);
    std::cout << "样本数: " << stats.count() << std::endl;
    std::cout << "均值: " << stats.mean() << std::endl;
    std::cout << "方差: " << stats.variance() << std::endl;
}

// 示例5：原子浮点的精度问题
void precision_issues() {
    std::cout << "\n=== 精度问题 ===" << std::endl;

    // 浮点累加的顺序依赖
    std::atomic<double> atomic_sum{0.0};
    double sequential_sum = 0.0;

    const int n = 1000000;

    // 顺序累加
    for (int i = 0; i < n; ++i) {
        sequential_sum += 1.0 / (i + 1);
    }

    // 原子累加（并发）
    auto adder = [&](int start, int end) {
        for (int i = start; i < end; ++i) {
            atomic_sum.fetch_add(1.0 / (i + 1), std::memory_order_relaxed);
        }
    };

    std::vector<std::thread> threads;
    int chunk = n / 4;
    for (int i = 0; i < 4; ++i) {
        threads.emplace_back(adder, i * chunk, (i + 1) * chunk);
    }

    for (auto& t : threads) {
        t.join();
    }

    std::cout << std::fixed << std::setprecision(10);
    std::cout << "顺序累加: " << sequential_sum << std::endl;
    std::cout << "原子累加: " << atomic_sum.load() << std::endl;
    std::cout << "差异: " << std::abs(sequential_sum - atomic_sum.load()) << std::endl;
}

int main() {
    std::cout << "C++ 原子操作：原子浮点 (C++20)" << std::endl;
    std::cout << "================================\n" << std::endl;

    basic_atomic_float();
    cas_atomic_float();
    concurrent_accumulation();
    statistics_demo();
    precision_issues();

    return 0;
}
