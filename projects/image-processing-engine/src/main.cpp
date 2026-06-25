#include "image_engine/image_engine.h"
#include <iostream>
#include <iomanip>

int main() {
    std::cout << "=== 图像处理引擎演示 ===" << std::endl;

    // Create a test image (64x64 gradient)
    int w = 64, h = 64;
    Image img(w, h, 3);
    for (int y = 0; y < h; y++) {
        for (int x = 0; x < w; x++) {
            uint8_t r = static_cast<uint8_t>((x / (float)w) * 255);
            uint8_t g = static_cast<uint8_t>((y / (float)h) * 255);
            uint8_t b = 128;
            img.set_pixel_rgb(x, y, r, g, b);
        }
    }

    std::cout << "原始图像: " << img.name() << std::endl;

    // Grayscale
    Image gray = grayscale(img);
    std::cout << "灰度图像: " << gray.name() << std::endl;

    // Gaussian blur
    Image blurred = gaussian_blur(img, 2);
    std::cout << "高斯模糊: " << blurred.name() << std::endl;

    // Sharpen
    Image sharp = sharpen(img);
    std::cout << "锐化: " << sharp.name() << std::endl;

    // Threshold
    Image thresh = threshold(img, 128);
    std::cout << "阈值分割: " << thresh.name() << std::endl;

    // Sepia
    Image sepia = sepia(img);
    std::cout << "复古色调: " << sepia.name() << std::endl;

    // Invert
    Image inv = invert(img);
    std::cout << "反转: " << inv.name() << std::endl;

    // Rotate
    Image rotated = rotate90(img, true);
    std::cout << "旋转90度: " << rotated.name() << std::endl;

    // Scale
    Image scaled = scale(img, 0.5f);
    std::cout << "缩放50%: " << scaled.name() << std::endl;

    // Flip
    Image flipped = flip_horizontal(img);
    std::cout << "水平翻转: " << flipped.name() << std::endl;

    // Brightness
    Image bright = brightness_contrast(img, 30.0f, 0.0f);
    std::cout << "亮度+30: " << bright.name() << std::endl;

    // Histogram equalize
    Image eq = histogram_equalize(img);
    std::cout << "直方图均衡化: " << eq.name() << std::endl;

    std::cout << "\n所有图像处理操作完成!" << std::endl;
    return 0;
}
