#pragma once

#include <cmath>
#include <vector>
#include <string>
#include <sstream>
#include <iomanip>

namespace cadsolver {

// Forward declarations
class Point2D;
class Line2D;
class Circle2D;

/**
 * @brief 2D Point - fundamental geometric entity
 *
 * Points are the primary unknowns in the constraint system.
 * Each point has x, y coordinates that the solver will adjust
 * to satisfy constraints.
 */
struct Point2D {
    double x;
    double y;
    int id;  // Unique identifier for constraint reference

    Point2D() : x(0.0), y(0.0), id(-1) {}
    Point2D(double x, double y, int id = -1) : x(x), y(y), id(id) {}

    // Distance to another point
    double distanceTo(const Point2D& other) const {
        double dx = x - other.x;
        double dy = y - other.y;
        return std::sqrt(dx * dx + dy * dy);
    }

    // Squared distance (avoids sqrt for performance)
    double distanceSquaredTo(const Point2D& other) const {
        double dx = x - other.x;
        double dy = y - other.y;
        return dx * dx + dy * dy;
    }

    // Vector operations
    Point2D operator+(const Point2D& other) const { return {x + other.x, y + other.y}; }
    Point2D operator-(const Point2D& other) const { return {x - other.x, y - other.y}; }
    Point2D operator*(double scalar) const { return {x * scalar, y * scalar}; }

    double dot(const Point2D& other) const { return x * other.x + y * other.y; }
    double cross(const Point2D& other) const { return x * other.y - y * other.x; }
    double length() const { return std::sqrt(x * x + y * y); }

    Point2D normalized() const {
        double len = length();
        if (len < 1e-12) return {0.0, 0.0};
        return {x / len, y / len};
    }

    std::string toString() const {
        std::ostringstream oss;
        oss << std::fixed << std::setprecision(4) << "(" << x << ", " << y << ")";
        return oss.str();
    }
};

/**
 * @brief 2D Line segment defined by two endpoints
 */
struct Line2D {
    Point2D start;
    Point2D end;
    int id;

    Line2D() : id(-1) {}
    Line2D(const Point2D& s, const Point2D& e, int id = -1) : start(s), end(e), id(id) {}

    // Direction vector (not normalized)
    Point2D direction() const { return end - start; }

    // Normal vector (perpendicular to direction)
    Point2D normal() const {
        Point2D dir = direction();
        return {-dir.y, dir.x};
    }

    double length() const { return start.distanceTo(end); }

    // Angle with another line (in radians)
    double angleWith(const Line2D& other) const {
        Point2D d1 = direction().normalized();
        Point2D d2 = other.direction().normalized();
        double cos_angle = d1.dot(d2);
        // Clamp for numerical stability
        cos_angle = std::max(-1.0, std::min(1.0, cos_angle));
        return std::acos(cos_angle);
    }

    // Closest point on line to given point
    Point2D closestPointTo(const Point2D& p) const {
        Point2D d = direction();
        double len2 = d.dot(d);
        if (len2 < 1e-12) return start;

        double t = (p - start).dot(d) / len2;
        t = std::max(0.0, std::min(1.0, t));
        return start + d * t;
    }

    // Distance from point to line segment
    double distanceToPoint(const Point2D& p) const {
        return p.distanceTo(closestPointTo(p));
    }

    std::string toString() const {
        return "Line[" + start.toString() + " -> " + end.toString() + "]";
    }
};

/**
 * @brief 2D Circle defined by center and radius
 */
struct Circle2D {
    Point2D center;
    double radius;
    int id;

    Circle2D() : radius(0.0), id(-1) {}
    Circle2D(const Point2D& c, double r, int id = -1) : center(c), radius(r), id(id) {}

    double area() const { return M_PI * radius * radius; }
    double circumference() const { return 2.0 * M_PI * radius; }

    // Distance from circle boundary to a point
    double distanceToPoint(const Point2D& p) const {
        return std::abs(center.distanceTo(p) - radius);
    }

    // Check if point is inside circle
    bool containsPoint(const Point2D& p) const {
        return center.distanceSquaredTo(p) <= radius * radius;
    }

    std::string toString() const {
        std::ostringstream oss;
        oss << std::fixed << std::setprecision(4)
            << "Circle[" << center.toString() << ", r=" << radius << "]";
        return oss.str();
    }
};

} // namespace cadsolver
