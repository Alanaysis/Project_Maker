#include "image_engine/image_engine.h"
#include <iostream>

using namespace image_engine;

int main() {
    std::cout << "=== 图像变换示例 ===" << std::endl;

    Image img(32, 32, 3);
    for (int y = 0; y < 32; y++) {
        for (int x = 0; x < 32; x++) {
            uint8_t r = static_cast<uint8_t>((x / 32.0f) * 255);
            uint8_t g = static_cast<uint8_t>((y / 32.0f) * 255);
            img.set_pixel_rgb(x, y, r, g, 128);
        }
    }

    std::cout << "原始: " << img.name() << std::endl;

    Image rotated = rotate90(img, true);
    std::cout << "旋转90度: " << rotated.name() << std::endl;

    Image scaled = scale(img, 0.5f);
    std::cout << "缩放50%: " << scaled.name() << std::endl;

    Image flipped = flip_horizontal(img);
    std::cout << "水平翻转: " << flipped.name() << std::endl;

    Image cropped = crop(img, 8, 8, 16, 16);
    std::cout << "裁剪(8,8,16x16): " << cropped.name() << std::endl;

    Image thresh = threshold(img, 128);
    std::cout << "阈值分割: " << thresh.name() << std::endl;

    Image sharpened = sharpen(img);
    std::cout << "锐化: " << sharpened.name() << std::endl;

    std::cout << "\n所有变换完成!" << std::endl;
    return 0;
}
