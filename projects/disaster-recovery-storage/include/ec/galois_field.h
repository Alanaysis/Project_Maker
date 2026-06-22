#ifndef DISASTER_RECOVERY_STORAGE_EC_GALOIS_FIELD_H_
#define DISASTER_RECOVERY_STORAGE_EC_GALOIS_FIELD_H_

#include <cstdint>
#include <array>

namespace disaster_recovery {
namespace ec {

/**
 * @brief GF(2^8) 有限域实现
 *
 * 实现Galois Field GF(2^8)的算术运算
 * 使用不可约多项式 x^8 + x^4 + x^3 + x^2 + 1 (0x11d)
 *
 * @note 这是纠删码的数学基础
 * @see https://www.samiam.org/galois.html
 */
class GaloisField {
public:
    /**
     * @brief 构造函数
     *
     * 初始化有限域，生成对数表和反对数表
     */
    GaloisField();

    /**
     * @brief 初始化有限域
     *
     * 生成查找表，必须在使用其他函数前调用
     */
    void init();

    /**
     * @brief 加法运算
     *
     * 在GF(2^8)中，加法就是XOR运算
     *
     * @param a 第一个操作数
     * @param b 第二个操作数
     * @return a + b 的结果
     */
    uint8_t add(uint8_t a, uint8_t b) const;

    /**
     * @brief 减法运算
     *
     * 在GF(2^8)中，减法和加法相同（XOR）
     *
     * @param a 第一个操作数
     * @param b 第二个操作数
     * @return a - b 的结果
     */
    uint8_t subtract(uint8_t a, uint8_t b) const;

    /**
     * @brief 乘法运算
     *
     * 使用对数表实现高效乘法
     *
     * @param a 第一个操作数
     * @param b 第二个操作数
     * @return a * b 的结果
     */
    uint8_t multiply(uint8_t a, uint8_t b) const;

    /**
     * @brief 除法运算
     *
     * 使用对数表实现高效除法
     *
     * @param a 被除数
     * @param b 除数（不能为0）
     * @return a / b 的结果
     * @throws 如果b为0，返回0
     */
    uint8_t divide(uint8_t a, uint8_t b) const;

    /**
     * @brief 求逆运算
     *
     * 计算a在GF(2^8)中的乘法逆元
     *
     * @param a 输入值（不能为0）
     * @return a的乘法逆元
     * @throws 如果a为0，返回0
     */
    uint8_t inverse(uint8_t a) const;

    /**
     * @brief 幂运算
     *
     * 计算a的n次幂
     *
     * @param a 底数
     * @param n 指数
     * @return a^n 的结果
     */
    uint8_t power(uint8_t a, int n) const;

    /**
     * @brief 获取对数值
     *
     * @param a 输入值（不能为0）
     * @return a的对数值
     */
    uint8_t log(uint8_t a) const;

    /**
     * @brief 获取反对数值
     *
     * @param a 输入值
     * @return 2^a 的值
     */
    uint8_t exp(uint8_t a) const;

    /**
     * @brief 检查是否已初始化
     *
     * @return true 如果已初始化，false 否则
     */
    bool isInitialized() const { return initialized_; }

private:
    // 不可约多项式: x^8 + x^4 + x^3 + x^2 + 1
    static constexpr uint16_t PRIMITIVE_POLYNOMIAL = 0x11d;

    // 本原元（生成元）
    static constexpr uint8_t GENERATOR = 2;

    // 对数表: log_table_[x] = log(x)
    std::array<uint8_t, 256> log_table_;

    // 反对数表: exp_table_[x] = 2^x
    std::array<uint8_t, 256> exp_table_;

    // 是否已初始化
    bool initialized_ = false;

    /**
     * @brief 生成查找表
     */
    void buildTables();

    /**
     * @brief 在GF(2^8)中进行多项式乘法
     *
     * @param a 第一个操作数
     * @param b 第二个操作数
     * @return 乘法结果
     */
    uint16_t multiplyNoLUT(uint16_t a, uint16_t b) const;
};

}  // namespace ec
}  // namespace disaster_recovery

#endif  // DISASTER_RECOVERY_STORAGE_EC_GALOIS_FIELD_H_
