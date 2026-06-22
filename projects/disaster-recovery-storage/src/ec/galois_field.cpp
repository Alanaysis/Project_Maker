#include "ec/galois_field.h"
#include <stdexcept>

namespace disaster_recovery {
namespace ec {

GaloisField::GaloisField() : initialized_(false) {
    // 初始化表为0
    log_table_.fill(0);
    exp_table_.fill(0);
}

void GaloisField::init() {
    buildTables();
    initialized_ = true;
}

void GaloisField::buildTables() {
    // 生成反对数表 (exp表)
    // exp_table_[i] = GENERATOR^i in GF(2^8)
    uint16_t x = 1;
    for (int i = 0; i < 255; i++) {
        exp_table_[i] = static_cast<uint8_t>(x);
        x <<= 1;  // 乘以2 (在GF(2^8)中)
        if (x >= 256) {
            x ^= PRIMITIVE_POLYNOMIAL;  // 模不可约多项式
        }
    }
    // 处理溢出部分: g^255 = g^0 = 1 (乘法群阶为255)
    // 数组仅有256个元素(索引0-255)，仅需设置索引255的环绕值
    // 调用方已对索引做模255归约，无需扩展存储
    exp_table_[255] = exp_table_[0];

    // 生成对数表 (log表)
    // log_table_[x] = i 使得 GENERATOR^i = x
    log_table_[0] = 0;  // log(0)未定义，设为0
    for (int i = 0; i < 255; i++) {
        log_table_[exp_table_[i]] = static_cast<uint8_t>(i);
    }
}

uint8_t GaloisField::add(uint8_t a, uint8_t b) const {
    // 在GF(2^n)中，加法就是XOR
    return a ^ b;
}

uint8_t GaloisField::subtract(uint8_t a, uint8_t b) const {
    // 在GF(2^n)中，减法和加法相同
    return a ^ b;
}

uint8_t GaloisField::multiply(uint8_t a, uint8_t b) const {
    // 使用对数表加速乘法
    // a * b = exp(log(a) + log(b))
    if (a == 0 || b == 0) {
        return 0;
    }

    int log_sum = static_cast<int>(log_table_[a]) + static_cast<int>(log_table_[b]);
    if (log_sum >= 255) {
        log_sum -= 255;
    }
    return exp_table_[log_sum];
}

uint8_t GaloisField::divide(uint8_t a, uint8_t b) const {
    // 使用对数表加速除法
    // a / b = exp(log(a) - log(b))
    if (b == 0) {
        // 除以0未定义，返回0
        return 0;
    }
    if (a == 0) {
        return 0;
    }

    int log_diff = static_cast<int>(log_table_[a]) - static_cast<int>(log_table_[b]);
    if (log_diff < 0) {
        log_diff += 255;
    }
    return exp_table_[log_diff];
}

uint8_t GaloisField::inverse(uint8_t a) const {
    // a的逆元 = exp(255 - log(a))
    if (a == 0) {
        // 0没有逆元
        return 0;
    }
    return exp_table_[255 - log_table_[a]];
}

uint8_t GaloisField::power(uint8_t a, int n) const {
    if (n == 0) {
        return 1;
    }
    if (a == 0) {
        return 0;
    }

    // 使用对数表
    int log_result = (static_cast<int>(log_table_[a]) * n) % 255;
    if (log_result < 0) {
        log_result += 255;
    }
    return exp_table_[log_result];
}

uint8_t GaloisField::log(uint8_t a) const {
    if (a == 0) {
        // log(0)未定义
        return 0;
    }
    return log_table_[a];
}

uint8_t GaloisField::exp(uint8_t a) const {
    return exp_table_[a];
}

uint16_t GaloisField::multiplyNoLUT(uint16_t a, uint16_t b) const {
    // 不使用查找表的乘法（用于验证）
    uint16_t result = 0;
    uint16_t temp = a;

    for (int i = 0; i < 8; i++) {
        if (b & 1) {
            result ^= temp;
        }
        temp <<= 1;
        if (temp & 0x100) {
            temp ^= PRIMITIVE_POLYNOMIAL;
        }
        b >>= 1;
    }

    return result;
}

}  // namespace ec
}  // namespace disaster_recovery
