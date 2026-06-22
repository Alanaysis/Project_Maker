/**
 * @file 02_matrix_multiply.cpp
 * @brief 矩阵乘法示例
 *
 * 本示例展示如何实现矩阵乘法，并比较 CPU 和 GPU 的性能。
 *
 * 学习目标:
 * - 理解矩阵乘法的并行化
 * - 掌握数据传输和同步
 * - 了解性能优化技巧
 */

#include <heterogeneous/task.h>
#include <heterogeneous/device.h>
#include <heterogeneous/executor.h>
#include <utils/timer.h>
#include <iostream>
#include <vector>
#include <random>
#include <cmath>

using namespace heterogeneous;
using namespace heterogeneous::utils;

// 矩阵乘法内核
void matrix_multiply_cpu(const float* A, const float* B, float* C,
                         size_t M, size_t N, size_t K) {
    for (size_t i = 0; i < M; i++) {
        for (size_t j = 0; j < N; j++) {
            float sum = 0.0f;
            for (size_t k = 0; k < K; k++) {
                sum += A[i * K + k] * B[k * N + j];
            }
            C[i * N + j] = sum;
        }
    }
}

// 初始化随机矩阵
void init_random_matrix(std::vector<float>& matrix, size_t rows, size_t cols) {
    std::random_device rd;
    std::mt19937 gen(rd());
    std::uniform_real_distribution<float> dist(-1.0f, 1.0f);

    matrix.resize(rows * cols);
    for (size_t i = 0; i < rows * cols; i++) {
        matrix[i] = dist(gen);
    }
}

// 验证矩阵乘法结果
bool verify_result(const std::vector<float>& A, const std::vector<float>& B,
                   const std::vector<float>& C, size_t M, size_t N, size_t K) {
    for (size_t i = 0; i < M; i++) {
        for (size_t j = 0; j < N; j++) {
            float expected = 0.0f;
            for (size_t k = 0; k < K; k++) {
                expected += A[i * K + k] * B[k * N + j];
            }
            if (std::abs(C[i * N + j] - expected) > 1e-3f) {
                std::cerr << "验证失败: C[" << i << "][" << j << "] = "
                          << C[i * N + j] << ", 期望: " << expected << std::endl;
                return false;
            }
        }
    }
    return true;
}

int main() {
    std::cout << "=== 矩阵乘法示例 ===" << std::endl;
    std::cout << std::endl;

    // 1. 初始化设备
    std::cout << "1. 初始化设备..." << std::endl;
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

    // 2. 准备数据
    std::cout << "2. 准备矩阵数据..." << std::endl;

    const size_t M = 256;  // 行数
    const size_t N = 256;  // 列数
    const size_t K = 256;  // 内维

    std::vector<float> A, B, C(M * N, 0.0f);
    init_random_matrix(A, M, K);
    init_random_matrix(B, K, N);

    std::cout << "   矩阵 A: " << M << " x " << K << std::endl;
    std::cout << "   矩阵 B: " << K << " x " << N << std::endl;
    std::cout << "   矩阵 C: " << M << " x " << N << std::endl;
    std::cout << std::endl;

    // 3. CPU 执行
    std::cout << "3. CPU 执行矩阵乘法..." << std::endl;

    auto cpu_device = device_manager.get_default_device(DeviceType::CPU);
    if (!cpu_device) {
        std::cerr << "错误: 未找到 CPU 设备" << std::endl;
        return 1;
    }

    auto cpu_executor = ExecutorFactory::create(cpu_device);
    auto& task_manager = TaskManager::instance();

    // 创建 CPU 任务
    auto cpu_task = task_manager.create_task("matrix_mul_cpu",
        [&A, &B, &C, M, N, K](const void*, void*, size_t, const DeviceInfo*) {
            matrix_multiply_cpu(A.data(), B.data(), C.data(), M, N, K);
        });

    cpu_task->set_input(A.data(), A.size() * sizeof(float))
             .set_output(C.data(), C.size() * sizeof(float));

    // 执行并计时
    Timer cpu_timer("CPU", true);
    auto cpu_result = cpu_executor->execute(cpu_task);
    cpu_timer.stop();

    std::cout << "   CPU 执行时间: " << cpu_timer.elapsed_ms() << " ms" << std::endl;
    std::cout << "   CPU 状态: " << (cpu_result.success ? "成功" : "失败") << std::endl;
    std::cout << std::endl;

    // 4. 验证结果
    std::cout << "4. 验证结果..." << std::endl;
    if (verify_result(A, B, C, M, N, K)) {
        std::cout << "   结果正确!" << std::endl;
    } else {
        std::cerr << "   结果错误!" << std::endl;
    }
    std::cout << std::endl;

    // 5. 性能分析
    std::cout << "5. 性能分析:" << std::endl;

    // 计算浮点操作数
    double flops = 2.0 * M * N * K;  // 乘法和加法
    double cpu_gflops = flops / (cpu_timer.elapsed_sec() * 1e9);

    std::cout << "   浮点操作数: " << flops << std::endl;
    std::cout << "   CPU 性能: " << cpu_gflops << " GFLOPS" << std::endl;
    std::cout << std::endl;

    // 6. 批量执行示例
    std::cout << "6. 批量执行示例..." << std::endl;

    const int batch_size = 4;
    std::vector<std::shared_ptr<Task>> batch_tasks;
    std::vector<std::vector<float>> batch_results(batch_size, std::vector<float>(M * N, 0.0f));

    for (int b = 0; b < batch_size; b++) {
        auto task = task_manager.create_task("batch_task_" + std::to_string(b),
            [&A, &B, &batch_results, b, M, N, K](const void*, void*, size_t, const DeviceInfo*) {
                matrix_multiply_cpu(A.data(), B.data(), batch_results[b].data(), M, N, K);
            });
        batch_tasks.push_back(task);
    }

    Timer batch_timer("Batch", true);
    auto batch_exec_results = cpu_executor->execute_batch(batch_tasks);
    batch_timer.stop();

    std::cout << "   批量执行 " << batch_size << " 个任务" << std::endl;
    std::cout << "   总时间: " << batch_timer.elapsed_ms() << " ms" << std::endl;
    std::cout << "   平均时间: " << batch_timer.elapsed_ms() / batch_size << " ms" << std::endl;
    std::cout << std::endl;

    // 7. 清理
    std::cout << "7. 清理资源..." << std::endl;
    device_manager.shutdown();
    std::cout << "   完成!" << std::endl;

    return 0;
}
