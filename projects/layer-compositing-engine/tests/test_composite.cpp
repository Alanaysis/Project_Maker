#include "layer_compositing/layer.h"
#include <iostream>
#include <cassert>

using namespace layer_compositing;

int main() {
    int passed = 0;
    int total = 0;

    // Test 1: Single layer
    {
        Image img(10, 10, 4);
        for (int y = 0; y < 10; y++)
            for (int x = 0; x < 10; x++)
                img.set_pixel(x, y, 100, 150, 200, 255);
        std::vector<layer_compositing::Layer> layers;
        layers.emplace_back(img, "bg", 1.0f);
        Image result = layer_compositing::composite_layers(layers, 10, 10);
        assert(result.get(5, 5, 0) == 100);
        assert(result.get(5, 5, 3) == 255);
        passed++;
    }
    total++;
    std::cout << "test_single_layer: PASS" << std::endl;

    // Test 2: Two layers normal blend
    {
        Image bg(10, 10, 4);
        for (auto& v : bg.data_) v = 50;
        bg.data_[0*10*4 + 3] = 255;

        Image fg(10, 10, 4);
        for (auto& v : fg.data_) v = 0;
        fg.data_[0*10*4 + 0] = 255;
        fg.data_[0*10*4 + 3] = 255;

        std::vector<layer_compositing::Layer> layers;
        layers.emplace_back(bg, "bg", 1.0f);
        layers.emplace_back(fg, "fg", 1.0f);
        layers.back().blend_mode = 0;

        Image result = layer_compositing::composite_layers(layers, 10, 10);
        // First pixel should be 255 (red from fg)
        assert(result.get(0, 0, 0) == 255);
        passed++;
    }
    total++;
    std::cout << "test_two_layers: PASS" << std::endl;

    // Test 3: Opacity
    {
        Image bg(10, 10, 4);
        for (auto& v : bg.data_) v = 0;
        bg.data_[0*10*4 + 1] = 255;
        bg.data_[0*10*4 + 3] = 255;

        Image fg(10, 10, 4);
        for (auto& v : fg.data_) v = 0;
        fg.data_[0*10*4 + 0] = 255;
        fg.data_[0*10*4 + 3] = 255;

        std::vector<layer_compositing::Layer> layers;
        layers.emplace_back(bg, "bg", 1.0f);
        layers.emplace_back(fg, "fg", 0.5f);
        layers.back().blend_mode = 0;

        Image result = layer_compositing::composite_layers(layers, 10, 10);
        // With 50% opacity, green channel should be non-zero
        assert(result.get(0, 0, 1) > 0);
        passed++;
    }
    total++;
    std::cout << "test_opacity: PASS" << std::endl;

    // Test 4: Zero opacity layer skipped
    {
        Image bg(10, 10, 4);
        for (auto& v : bg.data_) v = 100;
        bg.data_[0*10*4 + 3] = 255;

        Image fg(10, 10, 4);
        for (auto& v : fg.data_) v = 200;
        fg.data_[0*10*4 + 3] = 255;

        std::vector<layer_compositing::Layer> layers;
        layers.emplace_back(bg, "bg", 1.0f);
        layers.emplace_back(fg, "fg", 0.0f);
        Image result = layer_compositing::composite_layers(layers, 10, 10);
        assert(result.get(0, 0, 0) == 100);
        passed++;
    }
    total++;
    std::cout << "test_zero_opacity: PASS" << std::endl;

    // Test 5: Size mismatch
    {
        Image bg(10, 10, 4);
        for (auto& v : bg.data_) v = 100;
        bg.data_[0*10*4 + 3] = 255;

        Image fg(5, 5, 4);
        for (auto& v : fg.data_) v = 200;
        fg.data_[0*4 + 3] = 255;

        std::vector<layer_compositing::Layer> layers;
        layers.emplace_back(bg, "bg", 1.0f);
        layers.emplace_back(fg, "fg", 1.0f);
        Image result = layer_compositing::composite_layers(layers, 10, 10);
        assert(result.width_ == 10);
        assert(result.height_ == 10);
        passed++;
    }
    total++;
    std::cout << "test_size_mismatch: PASS" << std::endl;

    std::cout << "\n结果: " << passed << "/" << total << " 通过" << std::endl;
    return (passed == total) ? 0 : 1;
}
