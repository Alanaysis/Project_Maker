#pragma once

#include <cstdint>
#include <vector>
#include <string>

namespace image_engine {

class Image {
public:
    int width_ = 0;
    int height_ = 0;
    int channels_ = 3;
    std::vector<uint8_t> data_;

    Image() = default;

    Image(int width, int height, int channels = 3)
        : width_(width), height_(height), channels_(channels) {
        data_.resize(width * height * channels, 0);
    }

    uint8_t get_pixel(int x, int y, int channel) const {
        if (x < 0 || x >= width_ || y < 0 || y >= height_) return 0;
        return data_[(y * width_ + x) * channels_ + channel];
    }

    void set_pixel(int x, int y, int channel, uint8_t value) {
        if (x < 0 || x >= width_ || y < 0 || y >= height_) return;
        data_[(y * width_ + x) * channels_ + channel] = value;
    }

    void set_pixel_rgb(int x, int y, uint8_t r, uint8_t g, uint8_t b) {
        if (channels_ < 3) return;
        set_pixel(x, y, 0, r);
        set_pixel(x, y, 1, g);
        set_pixel(x, y, 2, b);
    }

    void get_pixel_rgb(int x, int y, uint8_t& r, uint8_t& g, uint8_t& b) const {
        if (channels_ < 3) {
            r = g = b = get_pixel(x, y, 0);
            return;
        }
        r = get_pixel(x, y, 0);
        g = get_pixel(x, y, 1);
        b = get_pixel(x, y, 2);
    }

    int size() const { return static_cast<int>(data_.size()); }
    int pixel_count() const { return width_ * height_; }

    void clear(uint8_t val = 0) {
        std::fill(data_.begin(), data_.end(), val);
    }

    Image clone() const {
        Image img(width_, height_, channels_);
        img.data_ = data_;
        return img;
    }

    std::string name() const {
        return "Image(" + std::to_string(width_) + "x" + std::to_string(height_) + "x" + std::to_string(channels_) + ")";
    }
};

} // namespace image_engine
