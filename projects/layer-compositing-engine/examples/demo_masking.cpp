#include "layer_compositing/layer_compositing.h"
#include <iostream>
#include <cmath>

using namespace layer_compositing;

int main() {
    std::cout << "=== 蒙版操作演示 ===" << std::endl;

    int W = 30, H = 15;

    // Source image (colorful gradient)
    Image src(W, H, 4);
    for (int y = 0; y < H; y++) {
        for (int x = 0; x < W; x++) {
            uint8_t r = static_cast<uint8_t>((x / (float)W) * 255);
            uint8_t g = static_cast<uint8_t>((y / (float)H) * 255);
            src.set_pixel(x, y, r, g, 100, 255);
        }
    }

    // Mask (circle mask)
    Image mask(W, H, 4);
    for (int y = 0; y < H; y++) {
        for (int x = 0; x < W; x++) {
            float dx = x - W/2.0f;
            float dy = y - H/2.0f;
            float d = sqrtf(dx*dx + dy*dy);
            uint8_t v = (d < 6.0f) ? 255 : 0;
            mask.set_pixel(x, y, v, v, v, 255);
        }
    }

    // Apply mask
    Image masked = layer_compositing::apply_mask(src, mask);

    // Erode mask
    Image eroded = layer_compositing::erode(mask, 2);

    // Dilate mask
    Image dilated = layer_compositing::dilate(mask, 2);

    auto print_image = [](const Image& img, const std::string& title) {
        std::cout << "\n" << title << ":\n";
        for (int y = 0; y < img.height_; y++) {
            std::string line = " ";
            for (int x = 0; x < img.width_; x++) {
                uint8_t a = img.get(x, y, 3);
                if (a < 64) line += ' ';
                else if (a < 128) line += '#';
                else if (a < 200) line += '*';
                else line += '.';
            }
            std::cout << line << std::endl;
        }
    };

    print_image(src, "原始图像");
    print_image(mask, "圆形蒙版");
    print_image(masked, "应用蒙版后");
    print_image(eroded, "腐蚀蒙版");
    print_image(dilated, "膨胀蒙版");

    std::cout << "\n蒙版操作完成!" << std::endl;
    return 0;
}
