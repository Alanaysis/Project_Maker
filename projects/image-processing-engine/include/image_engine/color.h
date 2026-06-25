#pragma once

#include "image_engine/image.h"
#include <algorithm>

namespace image_engine {

inline Image grayscale(const Image& src) {
    Image dst(src.width_, src.height_, 1);
    for (int y = 0; y < src.height_; y++) {
        for (int x = 0; x < src.width_; x++) {
            uint8_t r, g, b;
            src.get_pixel_rgb(x, y, r, g, b);
            float gray = 0.299f * r + 0.587f * g + 0.114f * b;
            dst.set_pixel(x, y, 0, static_cast<uint8_t>(gray));
        }
    }
    return dst;
}

inline Image invert(const Image& src) {
    Image dst = src.clone();
    for (auto& v : dst.data_) {
        v = 255 - v;
    }
    return dst;
}

inline Image sepia(const Image& src) {
    Image dst = src.clone();
    for (int y = 0; y < src.height_; y++) {
        for (int x = 0; x < src.width_; x++) {
            uint8_t r, g, b;
            src.get_pixel_rgb(x, y, r, g, b);
            float tr = 0.393f * r + 0.769f * g + 0.189f * b;
            float tg = 0.349f * r + 0.686f * g + 0.168f * b;
            float tb = 0.272f * r + 0.534f * g + 0.131f * b;
            dst.set_pixel_rgb(x, y,
                static_cast<uint8_t>(std::clamp(tr, 0.0f, 255.0f)),
                static_cast<uint8_t>(std::clamp(tg, 0.0f, 255.0f)),
                static_cast<uint8_t>(std::clamp(tb, 0.0f, 255.0f)));
        }
    }
    return dst;
}

inline Image brightness_contrast(const Image& src, float brightness, float contrast) {
    Image dst = src.clone();
    float factor = (259.0f * (contrast + 255.0f)) / (255.0f * (259.0f - contrast));
    for (auto& v : dst.data_) {
        float adjusted = factor * (v - 128.0f) + 128.0f + brightness;
        v = static_cast<uint8_t>(std::clamp(adjusted, 0.0f, 255.0f));
    }
    return dst;
}

inline Image histogram_equalize(const Image& src) {
    Image dst = src.clone();
    std::vector<int> hist(256, 0);
    for (auto v : src.data_) hist[v]++;
    int total = src.size();
    float cum = 0;
    std::vector<float> lut(256);
    for (int i = 0; i < 256; i++) {
        cum += hist[i];
        lut[i] = (cum / total) * 255.0f;
    }
    for (auto& v : dst.data_) {
        v = static_cast<uint8_t>(lut[v]);
    }
    return dst;
}

} // namespace image_engine
