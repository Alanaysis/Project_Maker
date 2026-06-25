#pragma once

#include "layer_compositing/image.h"
#include <string>
#include "layer_compositing/blending.h"
#include "layer_compositing/masking.h"

namespace layer_compositing {

struct Layer {
    Image image;
    std::string name;
    float opacity = 1.0f;
    int blend_mode = 0; // 0=normal, 1=multiply, 2=screen, 3=overlay

    Layer() = default;
    Layer(const Image& img, const std::string& n, float op = 1.0f)
        : image(img), name(n), opacity(op) {}
};

inline Image composite_layers(const std::vector<Layer>& layers, int width, int height) {
    Image result(width, height, 4);
    result.data_.assign(width * height * 4, 0);

    for (const auto& layer : layers) {
        if (layer.opacity <= 0.0f) continue;
        int w = std::min(static_cast<int>(layer.image.width_), width);
        int h = std::min(static_cast<int>(layer.image.height_), height);
        for (int y = 0; y < h; y++) {
            for (int x = 0; x < w; x++) {
                uint8_t lr, lg, lb, la;
                layer.image.get_pixel(x, y, lr, lg, lb, la);
                uint8_t rr, rg, rb, ra;
                result.get_pixel(x, y, rr, rg, rb, ra);

                float op = layer.opacity * (la / 255.0f);
                float sr = lr * op;
                float sg = lg * op;
                float sb = lb * op;
                float sa = op;

                float dr, dg, db, da;
                switch (layer.blend_mode) {
                    case 1: // multiply
                        dr = sr * (rr / 255.0f); dg = sg * (rg / 255.0f); db = sb * (rb / 255.0f); break;
                    case 2: // screen
                        dr = 255.0f - (255.0f - sr) * (255.0f - rr) / 255.0f;
                        dg = 255.0f - (255.0f - sg) * (255.0f - rg) / 255.0f;
                        db = 255.0f - (255.0f - sb) * (255.0f - rb) / 255.0f; break;
                    default: // normal
                        dr = sr + rr * (1.0f - sa);
                        dg = sg + rg * (1.0f - sa);
                        db = sb + rb * (1.0f - sa); break;
                }
                da = sa + ra * (1.0f - sa);
                da = std::min(da, 1.0f);

                result.set_pixel(x, y, static_cast<uint8_t>(dr), static_cast<uint8_t>(dg), static_cast<uint8_t>(db), static_cast<uint8_t>(da * 255.0f));
            }
        }
    }
    return result;
}

} // namespace layer_compositing
