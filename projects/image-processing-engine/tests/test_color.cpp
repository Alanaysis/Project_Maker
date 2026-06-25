#include "image_engine/color.h"
#include <iostream>
#include <cassert>

using namespace image_engine;

int main() {
    int passed = 0;
    int total = 0;

    // Test 1: Grayscale channel count
    {
        Image src(4, 4, 3);
        for (auto& v : src.data_) v = 128;
        Image dst = grayscale(src);
        assert(dst.channels_ == 1);
        assert(dst.width_ == 4);
        assert(dst.height_ == 4);
        passed++;
    }
    total++;
    std::cout << "test_grayscale_channels: PASS" << std::endl;

    // Test 2: Grayscale of gray pixel
    {
        Image src(1, 1, 3);
        src.set_pixel_rgb(0, 0, 100, 100, 100);
        Image dst = grayscale(src);
        assert(dst.get_pixel(0, 0, 0) == 100);
        passed++;
    }
    total++;
    std::cout << "test_grayscale_gray_pixel: PASS" << std::endl;

    // Test 3: Invert of black is white
    {
        Image src(1, 1, 3);
        src.set_pixel_rgb(0, 0, 0, 0, 0);
        Image dst = invert(src);
        assert(dst.get_pixel(0, 0, 0) == 255);
        assert(dst.get_pixel(0, 0, 1) == 255);
        assert(dst.get_pixel(0, 0, 2) == 255);
        passed++;
    }
    total++;
    std::cout << "test_invert_black: PASS" << std::endl;

    // Test 4: Invert of white is black
    {
        Image src(1, 1, 3);
        src.set_pixel_rgb(0, 0, 255, 255, 255);
        Image dst = invert(src);
        assert(dst.get_pixel(0, 0, 0) == 0);
        passed++;
    }
    total++;
    std::cout << "test_invert_white: PASS" << std::endl;

    // Test 5: Sepia preserves size
    {
        Image src(5, 5, 3);
        Image dst = sepia(src);
        assert(dst.width_ == 5);
        assert(dst.height_ == 5);
        passed++;
    }
    total++;
    std::cout << "test_sepia_size: PASS" << std::endl;

    // Test 6: Brightness increases values
    {
        Image src(2, 2, 3);
        for (auto& v : src.data_) v = 50;
        Image dst = brightness_contrast(src, 100.0f, 0.0f);
        assert(dst.get_pixel(0, 0, 0) > 50);
        passed++;
    }
    total++;
    std::cout << "test_brightness_increase: PASS" << std::endl;

    // Test 7: Histogram equalize preserves size
    {
        Image src(4, 4, 3);
        Image dst = histogram_equalize(src);
        assert(dst.size() == src.size());
        passed++;
    }
    total++;
    std::cout << "test_histogram_equalize_size: PASS" << std::endl;

    std::cout << "\n结果: " << passed << "/" << total << " 通过" << std::endl;
    return (passed == total) ? 0 : 1;
}
