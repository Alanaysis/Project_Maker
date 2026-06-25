#pragma once

#include "vec3.h"
#include <memory>
#include <vector>

namespace rt {

// 光源基类
class Light {
public:
    Vec3 color;                         // 光源颜色
    double intensity;                   // 光源强度

    Light(const Vec3& color, double intensity)
        : color(color), intensity(intensity) {}

    virtual ~Light() = default;

    // 计算光源到某点的方向和距离
    virtual Vec3 direction_to(const Vec3& point) const = 0;

    // 计算某点接收到的光照强度
    virtual double intensity_at(const Vec3& point) const = 0;

    // 获取光源到某点的距离（用于阴影计算）
    virtual double distance_to(const Vec3& point) const = 0;
};

// 点光源
class PointLight : public Light {
public:
    Vec3 position;

    PointLight(const Vec3& position, const Vec3& color, double intensity)
        : Light(color, intensity), position(position) {}

    Vec3 direction_to(const Vec3& point) const override {
        return (position - point).normalize();
    }

    double intensity_at(const Vec3& point) const override {
        double dist_sq = (position - point).length_squared();
        return intensity / (4.0 * M_PI * dist_sq);
    }

    double distance_to(const Vec3& point) const override {
        return (position - point).length();
    }
};

// 方向光源（平行光，如太阳光）
class DirectionalLight : public Light {
public:
    Vec3 direction;                     // 光照方向（指向光源）

    DirectionalLight(const Vec3& direction, const Vec3& color, double intensity)
        : Light(color, intensity), direction(direction.normalize()) {}

    Vec3 direction_to(const Vec3& point) const override {
        return -direction;  // 从点指向光源的方向
    }

    double intensity_at(const Vec3& point) const override {
        return intensity;   // 方向光强度不变
    }

    double distance_to(const Vec3& point) const override {
        return std::numeric_limits<double>::infinity();  // 无限远
    }
};

// 面光源
class AreaLight : public Light {
public:
    Vec3 position;                      // 光源中心位置
    Vec3 u, v;                          // 光源平面的两个方向
    double width, height;               // 光源尺寸

    AreaLight(const Vec3& position, const Vec3& u, const Vec3& v,
              double width, double height, const Vec3& color, double intensity)
        : Light(color, intensity), position(position),
          u(u.normalize()), v(v.normalize()), width(width), height(height) {}

    Vec3 direction_to(const Vec3& point) const override {
        // 返回到光源中心的方向
        return (position - point).normalize();
    }

    double intensity_at(const Vec3& point) const override {
        double dist = distance_to(point);
        return intensity / (4.0 * M_PI * dist * dist);
    }

    double distance_to(const Vec3& point) const override {
        return (position - point).length();
    }

    // 获取光源上的随机采样点
    Vec3 random_point(double u_rand, double v_rand) const {
        return position + u * (width * (u_rand - 0.5)) + v * (height * (v_rand - 0.5));
    }
};

// 环境光遮蔽计算
class AmbientOcclusion {
public:
    int samples;                        // 采样数
    double max_distance;                // 最大遮蔽距离

    AmbientOcclusion(int samples = 16, double max_distance = 1.0)
        : samples(samples), max_distance(max_distance) {}

    // 计算某点的环境遮蔽因子
    double compute(const Vec3& point, const Vec3& normal,
                   const class Hitable* world) const;
};

// 光照计算
class Lighting {
public:
    // Phong 光照模型
    static Vec3 phong(const Vec3& point, const Vec3& normal, const Vec3& view_dir,
                      const Vec3& light_dir, const Vec3& light_color,
                      const Vec3& ambient, const Vec3& diffuse, const Vec3& specular,
                      double shininess) {
        // 环境光分量
        Vec3 result = ambient * diffuse;

        // 漫反射分量
        double diff = std::fmax(normal.dot(light_dir), 0.0);
        result += diffuse * light_color * diff;

        // 镜面反射分量
        Vec3 reflect_dir = (-light_dir).reflect(normal);
        double spec = std::pow(std::fmax(view_dir.dot(reflect_dir), 0.0), shininess);
        result += specular * light_color * spec;

        return result;
    }

    // 简化的环境遮蔽
    static double simple_ao(const Vec3& point, const Vec3& normal,
                            const class Hitable* world, int samples = 16);
};

} // namespace rt
