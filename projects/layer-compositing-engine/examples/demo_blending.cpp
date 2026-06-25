#include "layer_compositing/layer_compositing.h"
#include <iostream>
#include <cmath>

using namespace layer_compositing;

int main() {
    std::cout << "=== 图层合成引擎演示 ===" << std::endl;

    int W = 40, H = 20;

    // Create background layer (gradient)
    Image bg(W, H, 4);
    for (int y = 0; y < H; y++) {
        for (int x = 0; x < W; x++) {
            uint8_t r = static_cast<uint8_t>((x / (float)W) * 255);
            uint8_t g = static_cast<uint8_t>((y / (float)H) * 255);
            bg.set_pixel(x, y, r, g, 128, 255);
        }
    }

    // Create overlay circle
    Image circ(W, H, 4);
    for (int y = 0; y < H; y++) {
        for (int x = 0; x < W; x++) {
            float dx = x - W/2.0f;
            float dy = y - H/2.0f;
            float d = sqrtf(dx*dx + dy*dy);
            if (d < 8.0f) {
                circ.set_pixel(x, y, 255, 0, 0, 200);
            }
        }
    }

    // Composite with multiply blend
    std::vector<layer_compositing::Layer> layers;
    layers.emplace_back(bg, "background", 1.0f);
    layers.emplace_back(circ, "circle", 0.8f);
    layers.back().blend_mode = 1; // multiply

    Image result = layer_compositing::composite_layers(layers, W, H);

    std::cout << "\n图层合成结果 (ASCII):\n";
    for (int y = 0; y < H; y++) {
        std::string line = " ";
        for (int x = 0; x < W; x++) {
            uint8_t r = result.get(x, y, 0);
            uint8_t g = result.get(x, y, 1);
            uint8_t b = result.get(x, y, 2);
            uint8_t a = result.get(x, y, 3);
            uint8_t brightness = (r + g + b) / 3;
            if (a < 64) line += ' ';
            else if (brightness < 85) line += '#';
            else if (brightness < 170) line += '*';
            else line += '.';
        }
        std::cout << line << std::endl;
    }

    std::cout << "\n合成完成!" << std::endl;
    return 0;
}
