#include "image_engine/transform.h"
#include <iostream>
#include <cassert>

using namespace image_engine;

int main() {
    int passed = 0;
    int total = 0;

    // Test 1: Rotate 90 swaps dimensions
    {
        Image src(4, 6, 3);
        Image dst = rotate90(src, true);
        assert(dst.width_ == 6);
        assert(dst.height_ == 4);
        passed++;
    }
    total++;
    std::cout << "test_rotate90_swap: PASS" << std::endl;

    // Test 2: Rotate 90 clockwise preserves pixel count
    {
        Image src(3, 3, 3);
        for (int i = 0; i < 27; i++) src.data_[i] = static_cast<uint8_t>(i);
        Image dst = rotate90(src, true);
        assert(dst.size() == src.size());
        passed++;
    }
    total++;
    std::cout << "test_rotate90_preserve: PASS" << std::endl;

    // Test 3: Scale by 1.0 preserves image
    {
        Image src(5, 5, 3);
        for (auto& v : src.data_) v = 42;
        Image dst = scale(src, 1.0f);
        assert(dst.size() == src.size());
        passed++;
    }
    total++;
    std::cout << "test_scale_1: PASS" << std::endl;

    // Test 4: Scale by 0.5 halves dimensions
    {
        Image src(10, 10, 3);
        Image dst = scale(src, 0.5f);
        assert(dst.width_ == 5);
        assert(dst.height_ == 5);
        passed++;
    }
    total++;
    std::cout << "test_scale_half: PASS" << std::endl;

    // Test 5: Crop reduces size
    {
        Image src(10, 10, 3);
        Image dst = crop(src, 2, 2, 4, 4);
        assert(dst.width_ == 4);
        assert(dst.height_ == 4);
        passed++;
    }
    total++;
    std::cout << "test_crop: PASS" << std::endl;

    // Test 6: Flip horizontal preserves size
    {
        Image src(5, 5, 3);
        for (auto& v : src.data_) v = 100;
        Image dst = flip_horizontal(src);
        assert(dst.size() == src.size());
        passed++;
    }
    total++;
    std::cout << "test_flip_size: PASS" << std::endl;

    // Test 7: Flip horizontal swaps pixels
    {
        Image src(4, 1, 1);
        src.data_ = {1, 2, 3, 4};
        Image dst = flip_horizontal(src);
        assert(dst.get_pixel(0, 0, 0) == 4);
        assert(dst.get_pixel(3, 0, 0) == 1);
        passed++;
    }
    total++;
    std::cout << "test_flip_content: PASS" << std::endl;

    std::cout << "\n结果: " << passed << "/" << total << " 通过" << std::endl;
    return (passed == total) ? 0 : 1;
}
