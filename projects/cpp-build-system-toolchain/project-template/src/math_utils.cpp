#include "mylib/core.h"
#include <cmath>
#include <stdexcept>

namespace mylib {

int MathUtils::add(int a, int b) { return a + b; }
int MathUtils::subtract(int a, int b) { return a - b; }
int MathUtils::multiply(int a, int b) { return a * b; }

double MathUtils::divide(double a, double b) {
    if (b == 0.0) throw std::invalid_argument("Division by zero");
    return a / b;
}

double MathUtils::power(double base, int exponent) {
    return std::pow(base, exponent);
}

bool MathUtils::is_prime(int n) {
    if (n <= 1) return false;
    if (n <= 3) return true;
    if (n % 2 == 0 || n % 3 == 0) return false;
    for (int i = 5; i * i <= n; i += 6) {
        if (n % i == 0 || n % (i + 2) == 0) return false;
    }
    return true;
}

}  // namespace mylib
