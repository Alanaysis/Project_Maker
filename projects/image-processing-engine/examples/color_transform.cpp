#include "image_engine/color.h"
#include <iostream>

using namespace image_engine;

int main() {
    std::cout << "=== 颜色变换示例 ===" << std::endl;

    Image img(32, 32, 3);
    for (int y = 0; y < 32; y++) {
        for (int x = 0; x < 32; x++) {
            img.set_pixel_rgb(x, y,
                static_cast<uint8_t>(x * 8),
                static_cast<uint8_t>(y * 8),
                static_cast<uint8_t>(128));
        }
    }

    std::cout << "原始: " << img.name() << std::endl;

    Image gray = grayscale(img);
    std::cout << "灰度: " << gray.name() << std::endl;

    Image sepia_img = sepia(img);
    std::cout << "复古: " << sepia_img.name() << std::endl;

    Image inv = invert(img);
    std::cout << "反转: " << inv.name() << std::endl;

    Image bright = brightness_contrast(img, 50.0f, 20.0f);
    std::cout << "亮度+50, 对比度+20: " << bright.name() << std::endl;

    Image eq = histogram_equalize(img);
    std::cout << "直方图均衡化: " << eq.name() << std::endl;

    std::cout << "\n所有颜色变换完成!" << std::endl;
    return 0;
}
