#pragma once

#include "image_engine/image.h"

namespace image_engine {

inline Image rotate90(const Image& src, bool clockwise = true) {
    Image dst(src.height_, src.width_, src.channels_);
    for (int y = 0; y < src.height_; y++) {
        for (int x = 0; x < src.width_; x++) {
            for (int c = 0; c < src.channels_; c++) {
                uint8_t v = src.get_pixel(x, y, c);
                if (clockwise) {
                    dst.set_pixel(y, src.width_ - 1 - x, c, v);
                } else {
                    dst.set_pixel(src.height_ - 1 - y, x, c, v);
                }
            }
        }
    }
    return dst;
}

inline Image scale(const Image& src, float factor) {
    int new_w = static_cast<int>(src.width_ * factor);
    int new_h = static_cast<int>(src.height_ * factor);
    Image dst(new_w, new_h, src.channels_);
    for (int y = 0; y < new_h; y++) {
        for (int x = 0; x < new_w; x++) {
            int sx = static_cast<int>(x / factor);
            int sy = static_cast<int>(y / factor);
            sx = std::min(sx, src.width_ - 1);
            sy = std::min(sy, src.height_ - 1);
            for (int c = 0; c < src.channels_; c++) {
                dst.set_pixel(x, y, c, src.get_pixel(sx, sy, c));
            }
        }
    }
    return dst;
}

inline Image crop(const Image& src, int x, int y, int w, int h) {
    h = std::min(h, src.height_ - y);
    w = std::min(w, src.width_ - x);
    Image dst(w, h, src.channels_);
    for (int cy = 0; cy < h; cy++) {
        for (int cx = 0; cx < w; cx++) {
            for (int c = 0; c < src.channels_; c++) {
                dst.set_pixel(cx, cy, c, src.get_pixel(x + cx, y + cy, c));
            }
        }
    }
    return dst;
}

inline Image flip_horizontal(const Image& src) {
    Image dst = src.clone();
    for (int y = 0; y < src.height_; y++) {
        for (int x = 0; x < src.width_ / 2; x++) {
            for (int c = 0; c < src.channels_; c++) {
                uint8_t v1 = src.get_pixel(x, y, c);
                uint8_t v2 = src.get_pixel(src.width_ - 1 - x, y, c);
                dst.set_pixel(x, y, c, v2);
                dst.set_pixel(src.width_ - 1 - x, y, c, v1);
            }
        }
    }
    return dst;
}

} // namespace image_engine
