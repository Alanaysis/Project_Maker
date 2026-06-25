/**
 * @file compact_structures.cpp
 * @brief 紧凑数据结构示例
 */

#include <iostream>
#include <vector>
#include <chrono>
#include <iomanip>
#include <bitset>

void demonstrateBitFields()
{
    std::cout << "=== 示例1: 位字段 ===\n\n";

    struct NormalFlags {
        bool flag1; bool flag2; bool flag3; bool flag4;
        int value;
    };

    struct BitFlags {
        unsigned flag1 : 1; unsigned flag2 : 1;
        unsigned flag3 : 1; unsigned flag4 : 1;
        unsigned value : 28;
    };

    std::cout << "NormalFlags 大小: " << sizeof(NormalFlags) << " bytes\n";
    std::cout << "BitFlags 大小:    " << sizeof(BitFlags) << " bytes\n";
}

void demonstrateCompactStorage()
{
    std::cout << "\n=== 示例2: 紧凑存储 ===\n\n";

    struct CompactRGB { uint8_t r, g, b; };
    struct WastefulRGB { int r, g, b; };

    std::cout << "CompactRGB:  " << sizeof(CompactRGB) << " bytes\n";
    std::cout << "WastefulRGB: " << sizeof(WastefulRGB) << " bytes\n";

    const size_t N = 1000000;
    std::cout << N << " 个像素: Compact=" << N * sizeof(CompactRGB) / 1024.0 / 1024.0
              << " MB, Wasteful=" << N * sizeof(WastefulRGB) / 1024.0 / 1024.0 << " MB\n";
}

int main()
{
    std::cout << "========================================\n";
    std::cout << "  紧凑数据结构\n";
    std::cout << "========================================\n\n";
    demonstrateBitFields();
    demonstrateCompactStorage();
    std::cout << "\n总结: 选择合适的类型和位字段可以显著减少内存使用。\n";
    return 0;
}
