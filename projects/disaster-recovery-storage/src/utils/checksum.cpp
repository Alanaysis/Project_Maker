#include "utils/checksum.h"
#include <sstream>
#include <iomanip>

namespace disaster_recovery {
namespace utils {

// CRC32查找表
uint32_t Checksum::crc32_table_[256];
bool Checksum::crc32_table_initialized_ = false;

void Checksum::initCrc32Table() {
    if (crc32_table_initialized_) {
        return;
    }

    for (uint32_t i = 0; i < 256; i++) {
        uint32_t crc = i;
        for (int j = 0; j < 8; j++) {
            if (crc & 1) {
                crc = (crc >> 1) ^ 0xEDB88320;
            } else {
                crc >>= 1;
            }
        }
        crc32_table_[i] = crc;
    }

    crc32_table_initialized_ = true;
}

uint32_t Checksum::crc32(const uint8_t* data, size_t size) {
    initCrc32Table();

    uint32_t crc = 0xFFFFFFFF;

    for (size_t i = 0; i < size; i++) {
        crc = crc32_table_[(crc ^ data[i]) & 0xFF] ^ (crc >> 8);
    }

    return crc ^ 0xFFFFFFFF;
}

std::string Checksum::crc32String(const uint8_t* data, size_t size) {
    uint32_t crc = crc32(data, size);

    std::stringstream ss;
    ss << std::hex << std::setw(8) << std::setfill('0') << crc;
    return ss.str();
}

uint32_t Checksum::crc32(const std::vector<uint8_t>& data) {
    return crc32(data.data(), data.size());
}

uint32_t Checksum::adler32(const uint8_t* data, size_t size) {
    uint32_t a = 1;
    uint32_t b = 0;

    for (size_t i = 0; i < size; i++) {
        a = (a + data[i]) % ADLER32_BASE;
        b = (b + a) % ADLER32_BASE;
    }

    return (b << 16) | a;
}

uint64_t Checksum::fnv1a(const uint8_t* data, size_t size) {
    // FNV-1a哈希算法
    const uint64_t FNV_OFFSET_BASIS = 14695981039346656037ULL;
    const uint64_t FNV_PRIME = 1099511628211ULL;

    uint64_t hash = FNV_OFFSET_BASIS;

    for (size_t i = 0; i < size; i++) {
        hash ^= data[i];
        hash *= FNV_PRIME;
    }

    return hash;
}

uint32_t Checksum::simple(const uint8_t* data, size_t size) {
    // 简单的哈希算法
    uint32_t hash = 0;

    for (size_t i = 0; i < size; i++) {
        hash = (hash * 31) + data[i];
    }

    return hash;
}

bool Checksum::verifyCrc32(const uint8_t* data, size_t size,
                           uint32_t expected) {
    return crc32(data, size) == expected;
}

bool Checksum::verifyCrc32(const uint8_t* data, size_t size,
                           const std::string& expected) {
    std::string actual = crc32String(data, size);
    return actual == expected;
}

std::vector<uint32_t> Checksum::blockCrc32(const uint8_t* data, size_t size,
                                           size_t block_size) {
    std::vector<uint32_t> checksums;

    size_t offset = 0;
    while (offset < size) {
        size_t current_block_size = std::min(block_size, size - offset);
        uint32_t checksum = crc32(data + offset, current_block_size);
        checksums.push_back(checksum);
        offset += current_block_size;
    }

    return checksums;
}

}  // namespace utils
}  // namespace disaster_recovery
