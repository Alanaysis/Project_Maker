#pragma once

#include "image_engine/image.h"
#include <algorithm>
#include <cmath>

namespace image_engine {

inline Image gaussian_blur(const Image& src, int radius) {
    Image dst(src.width_, src.height_, src.channels_);
    int k_size = 2 * radius + 1;
    std::vector<float> kernel(k_size);
    float sigma = radius / 2.0f + 0.1f;
    float sum = 0.0f;

    for (int i = 0; i < k_size; i++) {
        int x = i - radius;
        kernel[i] = expf(-(x * x) / (2.0f * sigma * sigma));
        sum += kernel[i];
    }
    for (int i = 0; i < k_size; i++) kernel[i] /= sum;

    for (int y = 0; y < src.height_; y++) {
        for (int x = 0; x < src.width_; x++) {
            float r_sum = 0, g_sum = 0, b_sum = 0;
            float w_sum = 0;

            for (int ky = -radius; ky <= radius; ky++) {
                for (int kx = -radius; kx <= radius; kx++) {
                    int px = x + kx;
                    int py = y + ky;
                    if (px < 0 || px >= src.width_ || py < 0 || py >= src.height_) continue;
                    float w = kernel[kx + radius] * kernel[ky + radius];
                    uint8_t r, g, b;
                    src.get_pixel_rgb(px, py, r, g, b);
                    r_sum += r * w;
                    g_sum += g * w;
                    b_sum += b * w;
                    w_sum += w;
                }
            }

            if (w_sum > 0) {
                r_sum /= w_sum; g_sum /= w_sum; b_sum /= w_sum;
            }
            dst.set_pixel_rgb(x, y,
                static_cast<uint8_t>(r_sum),
                static_cast<uint8_t>(g_sum),
                static_cast<uint8_t>(b_sum));
        }
    }
    return dst;
}

inline Image box_blur(const Image& src, int radius) {
    Image dst(src.width_, src.height_, src.channels_);

    for (int y = 0; y < src.height_; y++) {
        for (int x = 0; x < src.width_; x++) {
            int r_sum = 0, g_sum = 0, b_sum = 0, count = 0;
            for (int ky = -radius; ky <= radius; ky++) {
                for (int kx = -radius; kx <= radius; kx++) {
                    int px = x + kx;
                    int py = y + ky;
                    if (px < 0 || px >= src.width_ || py < 0 || py >= src.height_) continue;
                    uint8_t r, g, b;
                    src.get_pixel_rgb(px, py, r, g, b);
                    r_sum += r; g_sum += g; b_sum += b;
                    count++;
                }
            }
            if (count > 0) {
                dst.set_pixel_rgb(x, y,
                    static_cast<uint8_t>(r_sum / count),
                    static_cast<uint8_t>(g_sum / count),
                    static_cast<uint8_t>(b_sum / count));
            }
        }
    }
    return dst;
}

inline Image sharpen(const Image& src) {
    Image dst(src.width_, src.height_, src.channels_);
    for (int y = 0; y < src.height_; y++) {
        for (int x = 0; x < src.width_; x++) {
            for (int c = 0; c < src.channels_; c++) {
                int center = static_cast<int>(src.get_pixel(x, y, c));
                int sum = center * 5;
                if (x > 0) sum -= static_cast<int>(src.get_pixel(x - 1, y, c));
                if (x < src.width_ - 1) sum -= static_cast<int>(src.get_pixel(x + 1, y, c));
                if (y > 0) sum -= static_cast<int>(src.get_pixel(x, y - 1, c));
                if (y < src.height_ - 1) sum -= static_cast<int>(src.get_pixel(x, y + 1, c));
                dst.set_pixel(x, y, c, static_cast<uint8_t>(std::clamp(sum, 0, 255)));
            }
        }
    }
    return dst;
}

inline Image threshold(const Image& src, uint8_t thresh) {
    Image dst(src.width_, src.height_, src.channels_);
    for (int i = 0; i < src.size(); i++) {
        dst.data_[i] = src.data_[i] > thresh ? 255 : 0;
    }
    return dst;
}

} // namespace image_engine
