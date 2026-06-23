#include "../include/ray.h"
#include <iostream>
#include <cassert>
#include <cmath>

using namespace rt;

void test_constructor() {
    Vec3 origin(1.0, 2.0, 3.0);
    Vec3 direction(0.0, 0.0, -1.0);
    Ray ray(origin, direction);

    assert(std::abs(ray.origin.x - 1.0) < 1e-10);
    assert(std::abs(ray.origin.y - 2.0) < 1e-10);
    assert(std::abs(ray.origin.z - 3.0) < 1e-10);

    // 方向应该被单位化
    assert(std::abs(ray.direction.x - 0.0) < 1e-10);
    assert(std::abs(ray.direction.y - 0.0) < 1e-10);
    assert(std::abs(ray.direction.z - (-1.0)) < 1e-10);

    std::cout << "  [PASS] Constructor" << std::endl;
}

void test_at() {
    Vec3 origin(0.0, 0.0, 0.0);
    Vec3 direction(1.0, 0.0, 0.0);
    Ray ray(origin, direction);

    Vec3 p1 = ray.at(0.0);
    assert(std::abs(p1.x - 0.0) < 1e-10);
    assert(std::abs(p1.y - 0.0) < 1e-10);
    assert(std::abs(p1.z - 0.0) < 1e-10);

    Vec3 p2 = ray.at(5.0);
    assert(std::abs(p2.x - 5.0) < 1e-10);
    assert(std::abs(p2.y - 0.0) < 1e-10);
    assert(std::abs(p2.z - 0.0) < 1e-10);

    Vec3 p3 = ray.at(-3.0);
    assert(std::abs(p3.x - (-3.0)) < 1e-10);

    std::cout << "  [PASS] At" << std::endl;
}

void test_diagonal_direction() {
    Vec3 origin(0.0, 0.0, 0.0);
    Vec3 direction(1.0, 1.0, 0.0);
    Ray ray(origin, direction);

    // 方向应该被单位化
    double len = ray.direction.length();
    assert(std::abs(len - 1.0) < 1e-10);

    Vec3 p = ray.at(std::sqrt(2.0));
    assert(std::abs(p.x - 1.0) < 1e-10);
    assert(std::abs(p.y - 1.0) < 1e-10);

    std::cout << "  [PASS] Diagonal Direction" << std::endl;
}

int main() {
    std::cout << "Running Ray tests..." << std::endl;

    test_constructor();
    test_at();
    test_diagonal_direction();

    std::cout << "All Ray tests passed!" << std::endl;
    return 0;
}
