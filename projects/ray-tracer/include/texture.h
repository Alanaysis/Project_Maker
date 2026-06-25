#pragma once

#include "vec3.h"
#include <memory>
#include <cmath>
#include <vector>
#include <fstream>
#include <string>
#include <algorithm>

namespace rt {

// 纹理基类
class Texture {
public:
    virtual ~Texture() = default;
    virtual Vec3 value(double u, double v, const Vec3& p) const = 0;
};

// 纯色纹理
class SolidColor : public Texture {
public:
    Vec3 color;

    SolidColor(const Vec3& color) : color(color) {}
    SolidColor(double r, double g, double b) : color(r, g, b) {}

    Vec3 value(double u, double v, const Vec3& p) const override {
        return color;
    }
};

// 棋盘格纹理
class CheckerTexture : public Texture {
public:
    std::shared_ptr<Texture> odd;
    std::shared_ptr<Texture> even;
    double scale;

    CheckerTexture(double scale, const Vec3& c1, const Vec3& c2)
        : scale(scale),
          odd(std::make_shared<SolidColor>(c1)),
          even(std::make_shared<SolidColor>(c2)) {}

    CheckerTexture(double scale, std::shared_ptr<Texture> odd, std::shared_ptr<Texture> even)
        : scale(scale), odd(odd), even(even) {}

    Vec3 value(double u, double v, const Vec3& p) const override {
        double sines = std::sin(scale * p.x) * std::sin(scale * p.y) * std::sin(scale * p.z);
        return sines < 0 ? odd->value(u, v, p) : even->value(u, v, p);
    }
};

// 噪声纹理
class NoiseTexture : public Texture {
public:
    double scale;
    Vec3 color;

    NoiseTexture(double scale, const Vec3& color = Vec3(1, 1, 1))
        : scale(scale), color(color) {}

    Vec3 value(double u, double v, const Vec3& p) const override {
        // 简化的 Perlin 噪声
        double noise = perlin_noise(p * scale);
        return color * (0.5 * (1.0 + std::sin(scale * p.z + 10.0 * noise)));
    }

private:
    // 简化的 Perlin 噪声
    static double perlin_noise(const Vec3& p) {
        int xi = static_cast<int>(std::floor(p.x)) & 255;
        int yi = static_cast<int>(std::floor(p.y)) & 255;
        int zi = static_cast<int>(std::floor(p.z)) & 255;

        double xf = p.x - std::floor(p.x);
        double yf = p.y - std::floor(p.y);
        double zf = p.z - std::floor(p.z);

        // 使用简单插值
        double u = fade(xf);
        double v = fade(yf);
        double w = fade(zf);

        // 简化的哈希
        auto hash = [](int x, int y, int z) -> double {
            int h = (x * 73856093) ^ (y * 19349663) ^ (z * 83492791);
            h = ((h >> 16) ^ h) * 0x45d9f3b;
            h = ((h >> 16) ^ h) * 0x45d9f3b;
            h = (h >> 16) ^ h;
            return (h & 0xffff) / 65535.0;
        };

        // 三线性插值
        double c000 = hash(xi, yi, zi);
        double c100 = hash(xi + 1, yi, zi);
        double c010 = hash(xi, yi + 1, zi);
        double c110 = hash(xi + 1, yi + 1, zi);
        double c001 = hash(xi, yi, zi + 1);
        double c101 = hash(xi + 1, yi, zi + 1);
        double c011 = hash(xi, yi + 1, zi + 1);
        double c111 = hash(xi + 1, yi + 1, zi + 1);

        double c00 = c000 * (1 - u) + c100 * u;
        double c01 = c001 * (1 - u) + c101 * u;
        double c10 = c010 * (1 - u) + c110 * u;
        double c11 = c011 * (1 - u) + c111 * u;

        double c0 = c00 * (1 - v) + c10 * v;
        double c1 = c01 * (1 - v) + c11 * v;

        return c0 * (1 - w) + c1 * w;
    }

    static double fade(double t) {
        return t * t * t * (t * (t * 6 - 15) + 10);
    }
};

// 图像纹理（支持 PPM 格式）
class ImageTexture : public Texture {
public:
    std::vector<Vec3> pixels;
    int width, height;

    ImageTexture() : width(0), height(0) {}

    ImageTexture(const std::string& filename) {
        load_ppm(filename);
    }

    bool load_ppm(const std::string& filename) {
        std::ifstream file(filename);
        if (!file.is_open()) return false;

        std::string format;
        file >> format;
        if (format != "P3") return false;

        file >> width >> height;
        int max_val;
        file >> max_val;

        pixels.resize(width * height);
        for (int i = 0; i < width * height; i++) {
            int r, g, b;
            file >> r >> g >> b;
            pixels[i] = Vec3(r / 255.0, g / 255.0, b / 255.0);
        }

        return true;
    }

    Vec3 value(double u, double v, const Vec3& p) const override {
        if (pixels.empty()) return Vec3(0, 1, 1);  // 默认青色

        // 将纹理坐标限制在 [0, 1]
        u = std::fmod(u, 1.0);
        v = std::fmod(v, 1.0);
        if (u < 0) u += 1.0;
        if (v < 0) v += 1.0;

        int i = static_cast<int>(u * width);
        int j = static_cast<int>((1 - v) * height - 0.001);

        i = std::clamp(i, 0, width - 1);
        j = std::clamp(j, 0, height - 1);

        return pixels[j * width + i];
    }
};

// 渐变纹理
class GradientTexture : public Texture {
public:
    Vec3 color1, color2;
    bool vertical;

    GradientTexture(const Vec3& color1, const Vec3& color2, bool vertical = true)
        : color1(color1), color2(color2), vertical(vertical) {}

    Vec3 value(double u, double v, const Vec3& p) const override {
        double t = vertical ? v : u;
        return color1 * (1 - t) + color2 * t;
    }
};

// 条纹纹理
class StripeTexture : public Texture {
public:
    Vec3 color1, color2;
    double width;

    StripeTexture(const Vec3& color1, const Vec3& color2, double width = 0.1)
        : color1(color1), color2(color2), width(width) {}

    Vec3 value(double u, double v, const Vec3& p) const override {
        double stripe = std::fmod(p.x / width, 2.0);
        if (stripe < 0) stripe += 2.0;
        return stripe < 1.0 ? color1 : color2;
    }
};

} // namespace rt
