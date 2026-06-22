#ifndef DISASTER_RECOVERY_STORAGE_UTILS_CHECKSUM_H_
#define DISASTER_RECOVERY_STORAGE_UTILS_CHECKSUM_H_

#include <cstdint>
#include <cstddef>
#include <string>
#include <vector>

namespace disaster_recovery {
namespace utils {

/**
 * @brief 校验和工具类
 *
 * 提供多种校验和算法，用于数据完整性验证
 *
 * @note 数据完整性是容灾存储的关键
 */
class Checksum {
public:
    /**
     * @brief 计算CRC32校验和
     *
     * @param data 数据指针
     * @param size 数据大小
     * @return CRC32校验和
     */
    static uint32_t crc32(const uint8_t* data, size_t size);

    /**
     * @brief 计算CRC32校验和（字符串形式）
     *
     * @param data 数据指针
     * @param size 数据大小
     * @return CRC32校验和的十六进制字符串
     */
    static std::string crc32String(const uint8_t* data, size_t size);

    /**
     * @brief 计算CRC32校验和（向量形式）
     *
     * @param data 数据向量
     * @return CRC32校验和
     */
    static uint32_t crc32(const std::vector<uint8_t>& data);

    /**
     * @brief 计算Adler32校验和
     *
     * @param data 数据指针
     * @param size 数据大小
     * @return Adler32校验和
     */
    static uint32_t adler32(const uint8_t* data, size_t size);

    /**
     * @brief 计算FNV-1a哈希
     *
     * @param data 数据指针
     * @param size 数据大小
     * @return FNV-1a哈希值
     */
    static uint64_t fnv1a(const uint8_t* data, size_t size);

    /**
     * @brief 计算简单哈希
     *
     * @param data 数据指针
     * @param size 数据大小
     * @return 哈希值
     */
    static uint32_t simple(const uint8_t* data, size_t size);

    /**
     * @brief 验证CRC32校验和
     *
     * @param data 数据指针
     * @param size 数据大小
     * @param expected 期望的校验和
     * @return true 如果校验通过，false 否则
     */
    static bool verifyCrc32(const uint8_t* data, size_t size,
                            uint32_t expected);

    /**
     * @brief 验证CRC32校验和（字符串形式）
     *
     * @param data 数据指针
     * @param size 数据大小
     * @param expected 期望的校验和字符串
     * @return true 如果校验通过，false 否则
     */
    static bool verifyCrc32(const uint8_t* data, size_t size,
                            const std::string& expected);

    /**
     * @brief 计算分块校验和
     *
     * 将数据分成多个块，分别计算校验和
     *
     * @param data 数据指针
     * @param size 数据大小
     * @param block_size 块大小
     * @return 每个块的校验和列表
     */
    static std::vector<uint32_t> blockCrc32(const uint8_t* data, size_t size,
                                            size_t block_size);

private:
    // CRC32查找表
    static uint32_t crc32_table_[256];
    static bool crc32_table_initialized_;

    /**
     * @brief 初始化CRC32查找表
     */
    static void initCrc32Table();

    // Adler32常量
    static constexpr uint32_t ADLER32_BASE = 65521;
};

}  // namespace utils
}  // namespace disaster_recovery

#endif  // DISASTER_RECOVERY_STORAGE_UTILS_CHECKSUM_H_
