#include "layer_compositing/blending.h"
#include <iostream>
#include <cassert>

using namespace layer_compositing;

int main() {
    int passed = 0;
    int total = 0;

    // Test 1: Multiply
    {
        Image top(1, 1, 4);
        top.set_pixel(0, 0, 200, 100, 50, 255);
        Image bottom(1, 1, 4);
        bottom.set_pixel(0, 0, 100, 200, 50, 255);
        Image result = blend_layers(top, bottom, 1);
        uint8_t r = result.get(0, 0, 0);
        assert(r == static_cast<uint8_t>((200 * 100) / 255));
        passed++;
    }
    total++;
    std::cout << "test_multiply: PASS" << std::endl;

    // Test 2: Screen
    {
        Image top(1, 1, 4);
        top.set_pixel(0, 0, 100, 100, 100, 255);
        Image bottom(1, 1, 4);
        bottom.set_pixel(0, 0, 155, 155, 155, 255);
        Image result = blend_layers(top, bottom, 2);
        uint8_t r = result.get(0, 0, 0);
        // screen(100, 155) = 255 - (155 * 100) / 255 = 255 - 60 = 195
        assert(r == 195);
        passed++;
    }
    total++;
    std::cout << "test_screen: PASS" << std::endl;

    // Test 3: Normal blend with alpha
    {
        Image top(1, 1, 4);
        top.set_pixel(0, 0, 255, 0, 0, 128);
        Image bottom(1, 1, 4);
        bottom.set_pixel(0, 0, 0, 255, 0, 255);
        Image result = blend_layers(top, bottom, 0);
        // result = 255 * 0.5 + 0 * 0.5 = 127 (or 128)
        assert(result.get(0, 0, 0) >= 125 && result.get(0, 0, 0) <= 130);
        passed++;
    }
    total++;
    std::cout << "test_normal_alpha: PASS" << std::endl;

    // Test 4: Darken
    {
        Image top(1, 1, 4);
        top.set_pixel(0, 0, 100, 200, 50, 255);
        Image bottom(1, 1, 4);
        bottom.set_pixel(0, 0, 150, 100, 150, 255);
        Image result = blend_layers(top, bottom, 4);
        assert(result.get(0, 0, 0) == 100);
        assert(result.get(0, 0, 1) == 100);
        assert(result.get(0, 0, 2) == 50);
        passed++;
    }
    total++;
    std::cout << "test_darken: PASS" << std::endl;

    // Test 5: Lighten
    {
        Image top(1, 1, 4);
        top.set_pixel(0, 0, 100, 200, 50, 255);
        Image bottom(1, 1, 4);
        bottom.set_pixel(0, 0, 150, 100, 150, 255);
        Image result = blend_layers(top, bottom, 5);
        assert(result.get(0, 0, 0) == 150);
        assert(result.get(0, 0, 1) == 200);
        assert(result.get(0, 0, 2) == 150);
        passed++;
    }
    total++;
    std::cout << "test_lighten: PASS" << std::endl;

    // Test 6: Difference
    {
        Image top(1, 1, 4);
        top.set_pixel(0, 0, 200, 100, 50, 255);
        Image bottom(1, 1, 4);
        bottom.set_pixel(0, 0, 100, 200, 50, 255);
        Image result = blend_layers(top, bottom, 6);
        assert(result.get(0, 0, 0) == 100);
        assert(result.get(0, 0, 1) == 100);
        assert(result.get(0, 0, 2) == 0);
        passed++;
    }
    total++;
    std::cout << "test_difference: PASS" << std::endl;

    // Test 7: Overlay
    {
        Image top(1, 1, 4);
        top.set_pixel(0, 0, 200, 200, 200, 255);
        Image bottom(1, 1, 4);
        bottom.set_pixel(0, 0, 100, 200, 50, 255);
        Image result = blend_layers(top, bottom, 3);
        // bottom=100 < 128, so multiply(200, 200) = (200*200)/255 = 157
        assert(result.get(0, 0, 0) == 156);
        passed++;
    }
    total++;
    std::cout << "test_overlay: PASS" << std::endl;

    // Test 8: Size preservation
    {
        Image top(10, 10, 4);
        Image bottom(10, 10, 4);
        Image result = blend_layers(top, bottom, 0);
        assert(result.width_ == 10);
        assert(result.height_ == 10);
        passed++;
    }
    total++;
    std::cout << "test_size_preserve: PASS" << std::endl;

    std::cout << "\n结果: " << passed << "/" << total << " 通过" << std::endl;
    return (passed == total) ? 0 : 1;
}
