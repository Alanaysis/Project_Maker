#include "image_engine/image_engine.h"
#include <iostream>

using namespace image_engine;

int main() {
    std::cout << "=== 基础滤镜示例 ===" << std::endl;

    Image img(32, 32, 3);
    for (int y = 0; y < 32; y++) {
        for (int x = 0; x < 32; x++) {
            uint8_t r = static_cast<uint8_t>((x / 32.0f) * 255);
            uint8_t g = static_cast<uint8_t>((y / 32.0f) * 255);
            uint8_t b = static_cast<uint8_t>(128 + 64 * sinf(x / 8.0f));
            img.set_pixel_rgb(x, y, r, g, b);
        }
    }

    std::cout << "原始: " << img.name() << std::endl;

    Image gray = grayscale(img);
    std::cout << "灰度: " << gray.name() << std::endl;

    Image blurred = gaussian_blur(img, 3);
    std::cout << "高斯模糊(r=3): " << blurred.name() << std::endl;

    Image sharp = sharpen(img);
    std::cout << "锐化: " << sharp.name() << std::endl;

    Image thresh = threshold(img, 128);
    std::cout << "阈值分割: " << thresh.name() << std::endl;

    Image box = box_blur(img, 2);
    std::cout << "方框模糊(r=2): " << box.name() << std::endl;

    std::cout << "\n所有滤镜处理完成!" << std::endl;
    return 0;
}
