#include "image_engine/filters.h"
#include <iostream>
#include <cassert>

using namespace image_engine;

int main() {
    int passed = 0;
    int total = 0;

    // Test 1: Box blur preserves size
    {
        Image src(10, 10, 3);
        for (int y = 0; y < 10; y++)
            for (int x = 0; x < 10; x++)
                src.set_pixel_rgb(x, y, 100, 150, 200);
        Image dst = box_blur(src, 1);
        assert(dst.width_ == 10);
        assert(dst.height_ == 10);
        passed++;
    }
    total++;
    std::cout << "test_box_blur_size: PASS" << std::endl;

    // Test 2: Gaussian blur preserves size
    {
        Image src(10, 10, 3);
        Image dst = gaussian_blur(src, 1);
        assert(dst.width_ == 10);
        assert(dst.height_ == 10);
        passed++;
    }
    total++;
    std::cout << "test_gaussian_blur_size: PASS" << std::endl;

    // Test 3: Threshold creates binary image
    {
        Image src(5, 5, 3);
        for (int i = 0; i < 25; i++) {
            src.data_[i] = (i % 2 == 0) ? 200 : 50;
        }
        Image dst = threshold(src, 128);
        for (int i = 0; i < 25; i++) {
            assert(dst.data_[i] == 0 || dst.data_[i] == 255);
        }
        passed++;
    }
    total++;
    std::cout << "test_threshold_values: PASS" << std::endl;

    // Test 4: Sharpen preserves size
    {
        Image src(8, 8, 3);
        Image dst = sharpen(src);
        assert(dst.width_ == 8);
        assert(dst.height_ == 8);
        passed++;
    }
    total++;
    std::cout << "test_sharpen_size: PASS" << std::endl;

    // Test 5: Box blur on uniform image
    {
        Image src(10, 10, 3);
        for (auto& v : src.data_) v = 100;
        Image dst = box_blur(src, 2);
        for (auto& v : dst.data_) {
            assert(v >= 95 && v <= 105);
        }
        passed++;
    }
    total++;
    std::cout << "test_box_blur_uniform: PASS" << std::endl;

    std::cout << "\n结果: " << passed << "/" << total << " 通过" << std::endl;
    return (passed == total) ? 0 : 1;
}
