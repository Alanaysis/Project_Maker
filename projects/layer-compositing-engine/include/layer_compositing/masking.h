#pragma once

#include "layer_compositing/image.h"

namespace layer_compositing {

inline Image apply_mask(const Image& src, const Image& mask) {
    int w = src.width_;
    int h = src.height_;
    Image dst(w, h, 4);

    for (int y = 0; y < h; y++) {
        for (int x = 0; x < w; x++) {
            uint8_t r, g, b, a;
            src.get_pixel(x, y, r, g, b, a);
            uint8_t ma = (x < mask.width_ && y < mask.height_) ? mask.get(x, y, 0) : 255;
            a = static_cast<uint8_t>((a * ma) / 255);
            dst.set_pixel(x, y, r, g, b, a);
        }
    }
    return dst;
}

inline Image erode(const Image& src, int radius) {
    Image dst(src.width_, src.height_, 4);
    for (int y = 0; y < src.height_; y++) {
        for (int x = 0; x < src.width_; x++) {
            uint8_t min_a = 255;
            for (int dy = -radius; dy <= radius; dy++) {
                for (int dx = -radius; dx <= radius; dx++) {
                    int nx = x + dx, ny = y + dy;
                    if (nx < 0 || nx >= src.width_ || ny < 0 || ny >= src.height_) {
                        min_a = 0; break;
                    }
                    uint8_t r, g, b, a;
                    src.get_pixel(nx, ny, r, g, b, a);
                    min_a = std::min(min_a, a);
                }
                if (min_a == 0) break;
            }
            uint8_t r, g, b;
            src.get_pixel(x, y, r, g, b, min_a);
            dst.set_pixel(x, y, r, g, b, min_a);
        }
    }
    return dst;
}

inline Image dilate(const Image& src, int radius) {
    Image dst(src.width_, src.height_, 4);
    for (int y = 0; y < src.height_; y++) {
        for (int x = 0; x < src.width_; x++) {
            uint8_t max_a = 0;
            for (int dy = -radius; dy <= radius; dy++) {
                for (int dx = -radius; dx <= radius; dx++) {
                    int nx = x + dx, ny = y + dy;
                    if (nx < 0 || nx >= src.width_ || ny < 0 || ny >= src.height_) continue;
                    uint8_t r, g, b, a;
                    src.get_pixel(nx, ny, r, g, b, a);
                    max_a = std::max(max_a, a);
                }
            }
            uint8_t r = 0, g = 0, b = 0, a = 0;
            src.get_pixel(x, y, r, g, b, a);
            dst.set_pixel(x, y, r, g, b, max_a);
        }
    }
    return dst;
}

} // namespace layer_compositing
