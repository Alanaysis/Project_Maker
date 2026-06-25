#pragma once

#include <cstdint>
#include <vector>

namespace layer_compositing {

class Image {
public:
    int width_ = 0;
    int height_ = 0;
    int channels_ = 4;
    std::vector<uint8_t> data_;

    Image() = default;

    Image(int width, int height, int channels = 4)
        : width_(width), height_(height), channels_(channels) {
        data_.resize(width * height * channels, 0);
    }

    uint8_t get(int x, int y, int ch) const {
        if (x < 0 || x >= width_ || y < 0 || y >= height_) return 0;
        return data_[(y * width_ + x) * channels_ + ch];
    }

    void set(int x, int y, int ch, uint8_t v) {
        if (x < 0 || x >= width_ || y < 0 || y >= height_) return;
        data_[(y * width_ + x) * channels_ + ch] = v;
    }

    void set_pixel(int x, int y, uint8_t r, uint8_t g, uint8_t b, uint8_t a = 255) {
        if (channels_ >= 4) {
            set(x, y, 0, r); set(x, y, 1, g); set(x, y, 2, b); set(x, y, 3, a);
        } else if (channels_ == 3) {
            set(x, y, 0, r); set(x, y, 1, g); set(x, y, 2, b);
        } else {
            set(x, y, 0, (r + g + b) / 3);
        }
    }

    void get_pixel(int x, int y, uint8_t& r, uint8_t& g, uint8_t& b, uint8_t& a) const {
        r = get(x, y, 0); g = get(x, y, 1); b = get(x, y, 2);
        a = channels_ >= 4 ? get(x, y, 3) : 255;
    }

    int size() const { return static_cast<int>(data_.size()); }

    Image clone() const {
        Image img(width_, height_, channels_);
        img.data_ = data_;
        return img;
    }
};

} // namespace layer_compositing
