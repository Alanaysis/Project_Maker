#include "layer_compositing/masking.h"
#include <iostream>
#include <cassert>
#include <cmath>

using namespace layer_compositing;

int main() {
    int passed = 0;
    int total = 0;

    // Test 1: Apply mask - circle mask
    {
        Image src(10, 10, 4);
        for (int y = 0; y < 10; y++)
            for (int x = 0; x < 10; x++)
                src.set_pixel(x, y, 100, 100, 100, 255);

        Image mask(10, 10, 4);
        for (int y = 0; y < 10; y++) {
            for (int x = 0; x < 10; x++) {
                float dx = x - 4.5f;
                float dy = y - 4.5f;
                float d = sqrtf(dx*dx + dy*dy);
                uint8_t v = (d < 3.0f) ? 255 : 0;
                mask.set_pixel(x, y, v, v, v, 255);
            }
        }

        Image result = apply_mask(src, mask);
        // Center should have alpha 255
        assert(result.get(5, 5, 3) == 255);
        // Corner should have alpha 0
        assert(result.get(0, 0, 3) == 0);
        passed++;
    }
    total++;
    std::cout << "test_apply_mask: PASS" << std::endl;

    // Test 2: Erode reduces alpha
    {
        Image src(10, 10, 4);
        for (int y = 0; y < 10; y++) {
            for (int x = 0; x < 10; x++) {
                uint8_t a = ((x >= 2 && x <= 7) && (y >= 2 && y <= 7)) ? 255 : 0;
                src.set_pixel(x, y, 100, 100, 100, a);
            }
        }
        Image eroded = erode(src, 1);
        // Only the inner 6x6 should have alpha 255 after erode with radius 1
        assert(eroded.get(3, 3, 3) == 255);
        // Erode should reduce alpha at the boundary
        assert(eroded.get(2, 2, 3) <= eroded.get(3, 3, 3));
        passed++;
    }
    total++;
    std::cout << "test_erode: PASS" << std::endl;

    // Test 3: Dilate expands alpha
    {
        Image src(10, 10, 4);
        for (int y = 0; y < 10; y++) {
            for (int x = 0; x < 10; x++) {
                uint8_t a = ((x == 5 && y == 5)) ? 255 : 0;
                src.set_pixel(x, y, 100, 100, 100, a);
            }
        }
        Image dilated = dilate(src, 1);
        // Points around center should have alpha 255
        assert(dilated.get(5, 5, 3) == 255);
        assert(dilated.get(4, 5, 3) == 255);
        assert(dilated.get(6, 5, 3) == 255);
        passed++;
    }
    total++;
    std::cout << "test_dilate: PASS" << std::endl;

    // Test 4: Mask preserves size
    {
        Image src(20, 20, 4);
        Image mask(10, 10, 4);
        for (int y = 0; y < 10; y++)
            for (int x = 0; x < 10; x++)
                mask.set_pixel(x, y, 255, 255, 255, 255);
        Image result = apply_mask(src, mask);
        assert(result.width_ == 20);
        assert(result.height_ == 20);
        passed++;
    }
    total++;
    std::cout << "test_mask_size: PASS" << std::endl;

    std::cout << "\n结果: " << passed << "/" << total << " 通过" << std::endl;
    return (passed == total) ? 0 : 1;
}
