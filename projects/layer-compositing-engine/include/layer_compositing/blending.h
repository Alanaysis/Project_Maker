#pragma once

#include "layer_compositing/image.h"
#include <cstdlib>
#include <algorithm>

namespace layer_compositing {

inline uint8_t blend_multiply(uint8_t top, uint8_t bottom) {
    return static_cast<uint8_t>((top * bottom) / 255);
}

inline uint8_t blend_screen(uint8_t top, uint8_t bottom) {
    return static_cast<uint8_t>(255 - ((255 - top) * (255 - bottom)) / 255);
}

inline uint8_t blend_overlay(uint8_t top, uint8_t bottom) {
    return bottom < 128 ? blend_multiply(top, bottom * 2) : blend_screen(top, bottom * 2 + 1);
}

inline uint8_t blend_darken(uint8_t top, uint8_t bottom) {
    return std::min(top, bottom);
}

inline uint8_t blend_lighten(uint8_t top, uint8_t bottom) {
    return std::max(top, bottom);
}

inline uint8_t blend_difference(uint8_t top, uint8_t bottom) {
    return static_cast<uint8_t>(std::abs(static_cast<int>(top) - static_cast<int>(bottom)));
}

inline uint8_t blend_addition(uint8_t top, uint8_t bottom) {
    return static_cast<uint8_t>(std::min(static_cast<int>(top + bottom), 255));
}

inline uint8_t blend_subtract(uint8_t top, uint8_t bottom) {
    return static_cast<uint8_t>(std::max(static_cast<int>(top - bottom), 0));
}

inline uint8_t blend_normal(uint8_t top, uint8_t bottom, uint8_t top_alpha, uint8_t bottom_alpha) {
    if (top_alpha == 0) return bottom;
    if (top_alpha == 255) return top;
    float ta = top_alpha / 255.0f;
    return static_cast<uint8_t>(top * ta + bottom * (1.0f - ta));
}

inline Image blend_layers(const Image& top, const Image& bottom, int mode = 0) {
    int w = std::min(top.width_, bottom.width_);
    int h = std::min(top.height_, bottom.height_);
    Image dst(w, h, 4);

    auto apply = [&](int x, int y) {
        uint8_t tr, tg, tb, ta;
        uint8_t br, bg, bb, ba;
        top.get_pixel(x, y, tr, tg, tb, ta);
        bottom.get_pixel(x, y, br, bg, bb, ba);

        uint8_t dr, dg, db;
        switch (mode) {
            case 0: dr = blend_normal(tr, br, ta, ba); dg = blend_normal(tg, bg, ta, ba); db = blend_normal(tb, bb, ta, ba); break;
            case 1: dr = blend_multiply(tr, br); dg = blend_multiply(tg, bg); db = blend_multiply(tb, bb); break;
            case 2: dr = blend_screen(tr, br); dg = blend_screen(tg, bg); db = blend_screen(tb, bb); break;
            case 3: dr = blend_overlay(tr, br); dg = blend_overlay(tg, bg); db = blend_overlay(tb, bb); break;
            case 4: dr = blend_darken(tr, br); dg = blend_darken(tg, bg); db = blend_darken(tb, bb); break;
            case 5: dr = blend_lighten(tr, br); dg = blend_lighten(tg, bg); db = blend_lighten(tb, bb); break;
            case 6: dr = blend_difference(tr, br); dg = blend_difference(tg, bg); db = blend_difference(tb, bb); break;
            case 7: dr = blend_addition(tr, br); dg = blend_addition(tg, bg); db = blend_addition(tb, bb); break;
            case 8: dr = blend_subtract(tr, br); dg = blend_subtract(tg, bg); db = blend_subtract(tb, bb); break;
            default: dr = tr; dg = tg; db = tb; break;
        }
        dst.set_pixel(x, y, dr, dg, db, std::max(ta, ba));
    };

    for (int y = 0; y < h; y++) {
        for (int x = 0; x < w; x++) {
            apply(x, y);
        }
    }
    return dst;
}

} // namespace layer_compositing
