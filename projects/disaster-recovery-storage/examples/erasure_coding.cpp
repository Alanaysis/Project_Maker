/**
 * @file erasure_coding.cpp
 * @brief 纠删码详细示例
 *
 * 深入演示纠删码的原理和使用
 */

#include <iostream>
#include <vector>
#include <random>
#include <cassert>
#include <iomanip>

#include "ec/galois_field.h"
#include "ec/reed_solomon.h"

using namespace disaster_recovery;

// 生成随机数据
std::vector<uint8_t> generateRandomData(size_t size) {
    std::vector<uint8_t> data(size);
    std::mt19937 rng(42);
    std::uniform_int_distribution<int> dist(0, 255);
    for (auto& byte : data) {
        byte = static_cast<uint8_t>(dist(rng));
    }
    return data;
}

// 打印十六进制数据
void printHex(const std::string& label, const uint8_t* data, size_t size) {
    std::cout << label << ": ";
    for (size_t i = 0; i < std::min(size, (size_t)16); i++) {
        std::cout << std::hex << std::setw(2) << std::setfill('0')
                  << (int)data[i] << " ";
    }
    if (size > 16) {
        std::cout << "...";
    }
    std::cout << std::dec << std::endl;
}

// 演示有限域运算细节
void demoGaloisFieldDetails() {
    std::cout << "=== 有限域 GF(2^8) 详细演示 ===" << std::endl;
    std::cout << std::endl;

    ec::GaloisField gf;
    gf.init();

    // 展示加法表（部分）
    std::cout << "加法表 (XOR):" << std::endl;
    std::cout << "  +  | 0x0 0x1 0x2 0x3" << std::endl;
    std::cout << "-----+----------------" << std::endl;
    for (int i = 0; i < 4; i++) {
        std::cout << "0x" << std::hex << i << "  | ";
        for (int j = 0; j < 4; j++) {
            std::cout << "0x" << std::hex << (int)gf.add(i, j) << " ";
        }
        std::cout << std::endl;
    }
    std::cout << std::endl;

    // 展示乘法表（部分）
    std::cout << "乘法表:" << std::endl;
    std::cout << "  *  | 0x0 0x1 0x2 0x3" << std::endl;
    std::cout << "-----+----------------" << std::endl;
    for (int i = 0; i < 4; i++) {
        std::cout << "0x" << std::hex << i << "  | ";
        for (int j = 0; j < 4; j++) {
            std::cout << "0x" << std::hex << (int)gf.multiply(i, j) << " ";
        }
        std::cout << std::endl;
    }
    std::cout << std::endl;

    // 展示逆元
    std::cout << "逆元表 (部分):" << std::endl;
    for (int i = 1; i < 8; i++) {
        uint8_t a = static_cast<uint8_t>(i);
        uint8_t a_inv = gf.inverse(a);
        uint8_t product = gf.multiply(a, a_inv);
        std::cout << "  0x" << std::hex << (int)a << " * 0x" << (int)a_inv
                  << " = 0x" << (int)product << std::endl;
    }
    std::cout << std::endl;
}

// 演示Reed-Solomon编码原理
void demoReedSolomonPrinciple() {
    std::cout << "=== Reed-Solomon 编码原理演示 ===" << std::endl;
    std::cout << std::endl;

    ec::GaloisField gf;
    gf.init();

    // 简化示例: 使用GF(2^4)演示
    std::cout << "假设使用 GF(2^4)，数据分片 k=2，校验分片 m=2" << std::endl;
    std::cout << std::endl;

    // 原始数据: [d0, d1] = [5, 3]
    uint8_t d0 = 5;
    uint8_t d1 = 3;
    std::cout << "原始数据: [" << (int)d0 << ", " << (int)d1 << "]" << std::endl;

    // 编码矩阵 (简化版):
    // G = [1 0]
    //     [0 1]
    //     [1 1]
    //     [1 2]
    std::cout << "编码矩阵 G:" << std::endl;
    std::cout << "  [1 0]" << std::endl;
    std::cout << "  [0 1]" << std::endl;
    std::cout << "  [1 1]" << std::endl;
    std::cout << "  [1 2]" << std::endl;
    std::cout << std::endl;

    // 计算校验分片
    uint8_t p0 = gf.add(d0, d1);           // p0 = d0 + d1
    uint8_t p1 = gf.add(d0, gf.multiply(2, d1));  // p1 = d0 + 2*d1

    std::cout << "计算校验分片:" << std::endl;
    std::cout << "  p0 = d0 + d1 = " << (int)d0 << " + " << (int)d1
              << " = " << (int)p0 << std::endl;
    std::cout << "  p1 = d0 + 2*d1 = " << (int)d0 << " + 2*" << (int)d1
              << " = " << (int)p1 << std::endl;
    std::cout << std::endl;

    // 编码结果
    std::cout << "编码结果: [" << (int)d0 << ", " << (int)d1 << ", "
              << (int)p0 << ", " << (int)p1 << "]" << std::endl;
    std::cout << std::endl;

    // 演示恢复
    std::cout << "假设丢失分片 d0 和 p1，使用 d1 和 p0 恢复:" << std::endl;
    std::cout << "  已知: d1=" << (int)d1 << ", p0=" << (int)p0 << std::endl;
    std::cout << "  p0 = d0 + d1" << std::endl;
    std::cout << "  d0 = p0 - d1 = " << (int)p0 << " - " << (int)d1
              << " = " << (int)gf.subtract(p0, d1) << std::endl;
    std::cout << std::endl;
}

// 演示不同配置的纠删码
void demoDifferentConfigs() {
    std::cout << "=== 不同配置的纠删码演示 ===" << std::endl;
    std::cout << std::endl;

    // 测试不同配置
    std::vector<std::pair<int, int>> configs = {
        {2, 1},  // 2+1, 容忍1个故障
        {4, 2},  // 4+2, 容忍2个故障
        {6, 3},  // 6+3, 容忍3个故障
        {8, 4},  // 8+4, 容忍4个故障
    };

    size_t data_size = 512;
    auto original_data = generateRandomData(data_size);

    for (const auto& config : configs) {
        int k = config.first;
        int m = config.second;

        ec::ReedSolomon rs(k, m);

        // 计算存储开销
        double overhead = (double)(k + m) / k;
        double storage_efficiency = (double)k / (k + m) * 100;

        std::cout << "配置: k=" << k << ", m=" << m << std::endl;
        std::cout << "  总分片数: " << rs.getTotalShards() << std::endl;
        std::cout << "  容忍故障数: " << m << std::endl;
        std::cout << "  存储开销: " << std::fixed << std::setprecision(2)
                  << overhead << "x" << std::endl;
        std::cout << "  存储效率: " << storage_efficiency << "%" << std::endl;

        // 编码
        std::vector<std::vector<uint8_t>> shards;
        int result = rs.encode(original_data.data(), data_size, shards);
        assert(result == 0);

        // 测试恢复能力
        for (int lost = 1; lost <= m; lost++) {
            std::vector<bool> available(k + m, true);
            for (int i = 0; i < lost; i++) {
                available[i] = false;  // 丢失前lost个分片
            }

            std::vector<uint8_t> decoded_data;
            result = rs.decode(shards, available, decoded_data);
            bool success = (result == 0 && decoded_data.size() == data_size);

            std::cout << "  丢失 " << lost << " 个分片: "
                      << (success ? "可恢复" : "不可恢复") << std::endl;
        }

        std::cout << std::endl;
    }
}

// 演示性能测试
void demoPerformance() {
    std::cout << "=== 性能测试演示 ===" << std::endl;
    std::cout << std::endl;

    ec::ReedSolomon rs(4, 2);

    // 测试不同数据大小
    std::vector<size_t> sizes = {1024, 10240, 102400, 1048576};  // 1KB, 10KB, 100KB, 1MB

    for (size_t size : sizes) {
        auto data = generateRandomData(size);

        // 编码测试
        auto start = std::chrono::high_resolution_clock::now();
        std::vector<std::vector<uint8_t>> shards;
        rs.encode(data.data(), size, shards);
        auto end = std::chrono::high_resolution_clock::now();

        auto encode_time = std::chrono::duration_cast<std::chrono::microseconds>(
            end - start).count();

        // 解码测试
        std::vector<bool> available(6, true);
        available[0] = false;  // 丢失一个分片
        std::vector<uint8_t> decoded;

        start = std::chrono::high_resolution_clock::now();
        rs.decode(shards, available, decoded);
        end = std::chrono::high_resolution_clock::now();

        auto decode_time = std::chrono::duration_cast<std::chrono::microseconds>(
            end - start).count();

        std::cout << "数据大小: " << size / 1024 << " KB" << std::endl;
        std::cout << "  编码时间: " << encode_time << " μs" << std::endl;
        std::cout << "  解码时间: " << decode_time << " μs" << std::endl;
        std::cout << "  编码速度: " << std::fixed << std::setprecision(2)
                  << (double)size / encode_time << " MB/s" << std::endl;
        std::cout << std::endl;
    }
}

int main() {
    std::cout << "========================================" << std::endl;
    std::cout << "  纠删码详细示例" << std::endl;
    std::cout << "========================================" << std::endl;
    std::cout << std::endl;

    // 运行各个演示
    demoGaloisFieldDetails();
    demoReedSolomonPrinciple();
    demoDifferentConfigs();
    demoPerformance();

    std::cout << "========================================" << std::endl;
    std::cout << "  所有演示完成！" << std::endl;
    std::cout << "========================================" << std::endl;

    return 0;
}
