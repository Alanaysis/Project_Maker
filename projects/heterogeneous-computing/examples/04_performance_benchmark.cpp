/**
 * @file 04_performance_benchmark.cpp
 * @brief 性能基准测试
 *
 * 本示例展示如何进行性能基准测试，并分析 CPU/GPU 性能差异。
 *
 * 学习目标:
 * - 理解性能测量方法
 * - 掌握基准测试技巧
 * - 了解性能优化方向
 */

#include <heterogeneous/task.h>
#include <heterogeneous/device.h>
#include <heterogeneous/executor.h>
#include <utils/timer.h>
#include <iostream>
#include <vector>
#include <random>
#include <cmath>
#include <iomanip>
#include <map>

using namespace heterogeneous;
using namespace heterogeneous::utils;

// 测试配置
struct BenchmarkConfig {
    std::string name;
    size_t data_size;
    size_t iterations;
};

// 测试结果
struct BenchmarkResult {
    std::string name;
    double avg_time_ms;
    double min_time_ms;
    double max_time_ms;
    double throughput;  // 操作/秒
};

// 向量加法基准测试
BenchmarkResult benchmark_vector_add(std::shared_ptr<Device> device, size_t N, size_t iterations) {
    auto executor = ExecutorFactory::create(device);
    auto& task_manager = TaskManager::instance();

    std::vector<float> a(N), b(N), c(N, 0.0f);
    std::random_device rd;
    std::mt19937 gen(rd());
    std::uniform_real_distribution<float> dist(-100.0f, 100.0f);

    for (size_t i = 0; i < N; i++) {
        a[i] = dist(gen);
        b[i] = dist(gen);
    }

    std::vector<double> times;
    times.reserve(iterations);

    for (size_t iter = 0; iter < iterations; iter++) {
        auto task = task_manager.create_task("bench_add_" + std::to_string(iter),
            [&a, &b, &c, N](const void*, void*, size_t, const DeviceInfo*) {
                for (size_t i = 0; i < N; i++) {
                    c[i] = a[i] + b[i];
                }
            });

        task->set_input(a.data(), N * sizeof(float))
             .set_output(c.data(), N * sizeof(float));

        Timer timer("", true);
        executor->execute(task);
        timer.stop();

        times.push_back(timer.elapsed_ms());
    }

    // 计算统计
    double avg = 0.0, min_val = times[0], max_val = times[0];
    for (double t : times) {
        avg += t;
        if (t < min_val) min_val = t;
        if (t > max_val) max_val = t;
    }
    avg /= iterations;

    BenchmarkResult result;
    result.name = "Vector Add";
    result.avg_time_ms = avg;
    result.min_time_ms = min_val;
    result.max_time_ms = max_val;
    result.throughput = N / (avg * 1000.0);  // 操作/秒

    return result;
}

// 矩阵乘法基准测试
BenchmarkResult benchmark_matrix_multiply(std::shared_ptr<Device> device, size_t N, size_t iterations) {
    auto executor = ExecutorFactory::create(device);
    auto& task_manager = TaskManager::instance();

    std::vector<float> A(N * N), B(N * N), C(N * N, 0.0f);
    std::random_device rd;
    std::mt19937 gen(rd());
    std::uniform_real_distribution<float> dist(-1.0f, 1.0f);

    for (size_t i = 0; i < N * N; i++) {
        A[i] = dist(gen);
        B[i] = dist(gen);
    }

    std::vector<double> times;
    times.reserve(iterations);

    for (size_t iter = 0; iter < iterations; iter++) {
        auto task = task_manager.create_task("bench_mul_" + std::to_string(iter),
            [&A, &B, &C, N](const void*, void*, size_t, const DeviceInfo*) {
                for (size_t i = 0; i < N; i++) {
                    for (size_t j = 0; j < N; j++) {
                        float sum = 0.0f;
                        for (size_t k = 0; k < N; k++) {
                            sum += A[i * N + k] * B[k * N + j];
                        }
                        C[i * N + j] = sum;
                    }
                }
            });

        task->set_input(A.data(), N * N * sizeof(float))
             .set_output(C.data(), N * N * sizeof(float));

        Timer timer("", true);
        executor->execute(task);
        timer.stop();

        times.push_back(timer.elapsed_ms());
    }

    // 计算统计
    double avg = 0.0, min_val = times[0], max_val = times[0];
    for (double t : times) {
        avg += t;
        if (t < min_val) min_val = t;
        if (t > max_val) max_val = t;
    }
    avg /= iterations;

    BenchmarkResult result;
    result.name = "Matrix Multiply";
    result.avg_time_ms = avg;
    result.min_time_ms = min_val;
    result.max_time_ms = max_val;
    result.throughput = (2.0 * N * N * N) / (avg * 1e9);  // GFLOPS

    return result;
}

// 内存带宽基准测试
BenchmarkResult benchmark_memory_bandwidth(std::shared_ptr<Device> device, size_t N, size_t iterations) {
    auto executor = ExecutorFactory::create(device);
    auto& task_manager = TaskManager::instance();

    std::vector<float> src(N), dst(N, 0.0f);
    std::random_device rd;
    std::mt19937 gen(rd());
    std::uniform_real_distribution<float> dist(-100.0f, 100.0f);

    for (size_t i = 0; i < N; i++) {
        src[i] = dist(gen);
    }

    std::vector<double> times;
    times.reserve(iterations);

    for (size_t iter = 0; iter < iterations; iter++) {
        auto task = task_manager.create_task("bench_memcpy_" + std::to_string(iter),
            [&src, &dst, N](const void*, void*, size_t, const DeviceInfo*) {
                std::memcpy(dst.data(), src.data(), N * sizeof(float));
            });

        task->set_input(src.data(), N * sizeof(float))
             .set_output(dst.data(), N * sizeof(float));

        Timer timer("", true);
        executor->execute(task);
        timer.stop();

        times.push_back(timer.elapsed_ms());
    }

    // 计算统计
    double avg = 0.0, min_val = times[0], max_val = times[0];
    for (double t : times) {
        avg += t;
        if (t < min_val) min_val = t;
        if (t > max_val) max_val = t;
    }
    avg /= iterations;

    BenchmarkResult result;
    result.name = "Memory Bandwidth";
    result.avg_time_ms = avg;
    result.min_time_ms = min_val;
    result.max_time_ms = max_val;
    result.throughput = (N * sizeof(float) * 2) / (avg * 1e9);  // GB/s

    return result;
}

// 打印结果表
void print_results(const std::vector<BenchmarkResult>& results) {
    std::cout << std::setw(20) << "测试名称"
              << std::setw(15) << "平均时间(ms)"
              << std::setw(15) << "最小时间(ms)"
              << std::setw(15) << "最大时间(ms)"
              << std::setw(15) << "吞吐量"
              << std::endl;

    std::cout << std::string(80, '-') << std::endl;

    for (const auto& result : results) {
        std::cout << std::setw(20) << result.name
                  << std::setw(15) << std::fixed << std::setprecision(3) << result.avg_time_ms
                  << std::setw(15) << std::fixed << std::setprecision(3) << result.min_time_ms
                  << std::setw(15) << std::fixed << std::setprecision(3) << result.max_time_ms
                  << std::setw(15) << std::fixed << std::setprecision(2) << result.throughput;

        if (result.name == "Memory Bandwidth") {
            std::cout << " GB/s";
        } else if (result.name == "Matrix Multiply") {
            std::cout << " GFLOPS";
        } else {
            std::cout << " MOp/s";
        }

        std::cout << std::endl;
    }
}

int main() {
    std::cout << "=== 性能基准测试 ===" << std::endl;
    std::cout << std::endl;

    // 1. 初始化
    std::cout << "1. 初始化..." << std::endl;
    auto& device_manager = DeviceManager::instance();
    if (!device_manager.initialize()) {
        std::cerr << "错误: 无法初始化设备管理器" << std::endl;
        return 1;
    }

    // 显示设备信息
    auto devices = device_manager.detect_devices();
    for (const auto& info : devices) {
        std::cout << "   设备: " << info.name
                  << " (" << device_type_name(info.type) << ")"
                  << ", 计算单元: " << info.compute_units
                  << std::endl;
    }
    std::cout << std::endl;

    // 2. 测试配置
    std::cout << "2. 测试配置:" << std::endl;

    std::vector<BenchmarkConfig> configs = {
        {"Small", 10000, 100},
        {"Medium", 100000, 50},
        {"Large", 1000000, 10}
    };

    for (const auto& config : configs) {
        std::cout << "   " << config.name << ": "
                  << config.data_size << " 元素, "
                  << config.iterations << " 次迭代" << std::endl;
    }
    std::cout << std::endl;

    // 3. 运行基准测试
    std::cout << "3. 运行基准测试..." << std::endl;

    auto cpu_device = device_manager.get_default_device(DeviceType::CPU);
    if (!cpu_device) {
        std::cerr << "错误: 未找到 CPU 设备" << std::endl;
        return 1;
    }

    for (const auto& config : configs) {
        std::cout << "\n--- " << config.name << " ---" << std::endl;

        std::vector<BenchmarkResult> results;

        // 向量加法
        std::cout << "   测试向量加法..." << std::flush;
        results.push_back(benchmark_vector_add(cpu_device, config.data_size, config.iterations));
        std::cout << " 完成" << std::endl;

        // 内存带宽
        std::cout << "   测试内存带宽..." << std::flush;
        results.push_back(benchmark_memory_bandwidth(cpu_device, config.data_size, config.iterations));
        std::cout << " 完成" << std::endl;

        // 矩阵乘法 (仅小规模)
        if (config.data_size <= 10000) {
            size_t matrix_size = static_cast<size_t>(std::sqrt(config.data_size));
            std::cout << "   测试矩阵乘法 (" << matrix_size << "x" << matrix_size << ")..." << std::flush;
            results.push_back(benchmark_matrix_multiply(cpu_device, matrix_size, config.iterations));
            std::cout << " 完成" << std::endl;
        }

        // 打印结果
        std::cout << std::endl;
        print_results(results);
    }

    // 4. 性能分析
    std::cout << "\n4. 性能分析:" << std::endl;
    std::cout << "   - CPU 适合复杂控制逻辑和串行任务" << std::endl;
    std::cout << "   - GPU 适合大规模并行计算" << std::endl;
    std::cout << "   - 内存带宽是性能瓶颈之一" << std::endl;
    std::cout << "   - 数据传输开销会影响整体性能" << std::endl;
    std::cout << std::endl;

    // 5. 优化建议
    std::cout << "5. 优化建议:" << std::endl;
    std::cout << "   - 使用 SIMD 指令优化 CPU 计算" << std::endl;
    std::cout << "   - 减少 CPU/GPU 之间的数据传输" << std::endl;
    std::cout << "   - 使用异步执行重叠计算和传输" << std::endl;
    std::cout << "   - 选择合适的任务粒度" << std::endl;
    std::cout << std::endl;

    // 6. 清理
    std::cout << "6. 清理资源..." << std::endl;
    device_manager.shutdown();
    std::cout << "   完成!" << std::endl;

    return 0;
}
