// ============================================================
// cad-kernel: Geometric Primitives
//
// Implements basic 3D geometric primitives used in CAD kernels:
// - Point3D: a position in 3D space
// - Line: parametric line through two points
// - Plane: point + normal representation
// - Cylinder: axis + radius
// - Sphere: center + radius
// - Torus: major radius, minor radius, center, axis
// ============================================================

#pragma once
#include "brep.h"
#include <cmath>
#include <iostream>

// ============================================================
// Line: defined by origin point and direction vector
// P(u) = origin + u * direction
// ============================================================
class Line {
public:
    Point3D origin;
    Vector3D direction;

    Line() : origin(0,0,0), direction(0,0,1) {}
    Line(Point3D o, Vector3D d) : origin(o), direction(d) {}
    Line(Point3D p1, Point3D p2)
        : origin(p1), direction(p2.x-p1.x, p2.y-p1.y, p2.z-p1.z) {}

    Point3D pointAt(double u) const {
        return {origin.x + u*direction.x, origin.y + u*direction.y, origin.z + u*direction.z};
    }

    bool contains(Point3D p) const {
        double dx = p.x - origin.x, dy = p.y - origin.y, dz = p.z - origin.z;
        double dir_len = direction.length();
        if (approx_zero(dir_len)) return false;
        double t = (dx*direction.x + dy*direction.y + dz*direction.z) / (dir_len*dir_len);
        Point3D hit = {origin.x + t*direction.x, origin.y + t*direction.y, origin.z + t*direction.z};
        double err = std::sqrt((p.x-hit.x)*(p.x-hit.x) + (p.y-hit.y)*(p.y-hit.y) + (p.z-hit.z)*(p.z-hit.z));
        return err < EPSILON * 10;
    }

    double distance(Point3D p) const {
        double dx = p.x - origin.x, dy = p.y - origin.y, dz = p.z - origin.z;
        double dir_len = direction.length();
        if (approx_zero(dir_len)) return std::sqrt(dx*dx+dy*dy+dz*dz);
        double t = (dx*direction.x + dy*direction.y + dz*direction.z) / (dir_len*dir_len);
        Point3D proj = {origin.x + t*direction.x, origin.y + t*direction.y, origin.z + t*direction.z};
        return std::sqrt((p.x-proj.x)*(p.x-proj.x) + (p.y-proj.y)*(p.y-proj.y) + (p.z-proj.z)*(p.z-proj.z));
    }

    double project(Point3D p) const {
        double dx = p.x - origin.x, dy = p.y - origin.y, dz = p.z - origin.z;
        double dir_len = direction.length();
        if (approx_zero(dir_len)) return 0.0;
        return (dx*direction.x + dy*direction.y + dz*direction.z) / (dir_len * dir_len);
    }

    void print() const {
        std::cout << "Line: origin=(" << origin.x << "," << origin.y << "," << origin.z
                  << ") dir=(" << direction.x << "," << direction.y << "," << direction.z << ")\n";
    }
};

// ============================================================
// Plane: defined by a point and a normal vector
// (P - point_on_plane) . normal = 0
// ============================================================
class Plane {
public:
    Point3D origin;
    Vector3D normal;

    Plane() : origin(0,0,0), normal(0,0,1) {}
    Plane(Point3D o, Vector3D n) : origin(o), normal(n) {}
    Plane(Point3D o, Point3D n) : origin(o), normal(n.x, n.y, n.z) {}

    Vector3D getNormal() const { return normal.normalized(); }

    double signedDistance(Point3D p) const {
        Vector3D n = getNormal();
        return (p.x-origin.x)*n.x + (p.y-origin.y)*n.y + (p.z-origin.z)*n.z;
    }

    Point3D project(Point3D p) const {
        double d = signedDistance(p);
        Vector3D n = getNormal();
        return {p.x - n.x*d, p.y - n.y*d, p.z - n.z*d};
    }

    bool contains(Point3D p) const { return approx_zero(signedDistance(p)); }

    void print() const {
        std::cout << "Plane: origin=(" << origin.x << "," << origin.y << "," << origin.z
                  << ") normal=(" << normal.x << "," << normal.y << "," << normal.z << ")\n";
    }
};

// ============================================================
// Cylinder: axis line + radius
// ============================================================
class Cylinder {
public:
    Point3D origin;
    Vector3D axis;
    double radius;

    Cylinder() : origin(0,0,0), axis(0,0,1), radius(1.0) {}
    Cylinder(Point3D o, Vector3D a, double r) : origin(o), axis(a), radius(r) {}

    bool onSurface(Point3D p) const {
        double dx = p.x-origin.x, dy = p.y-origin.y, dz = p.z-origin.z;
        Vector3D ax = axis.normalized();
        double cross_x = ax.y*dz - ax.z*dy;
        double cross_y = ax.z*dx - ax.x*dz;
        double cross_z = ax.x*dy - ax.y*dx;
        double dist = std::sqrt(cross_x*cross_x + cross_y*cross_y + cross_z*cross_z);
        return approx_equal(dist, radius);
    }

    double distance(Point3D p) const {
        double dx = p.x-origin.x, dy = p.y-origin.y, dz = p.z-origin.z;
        Vector3D ax = axis.normalized();
        double cross_x = ax.y*dz - ax.z*dy;
        double cross_y = ax.z*dx - ax.x*dz;
        double cross_z = ax.x*dy - ax.y*dx;
        double dist_to_axis = std::sqrt(cross_x*cross_x + cross_y*cross_y + cross_z*cross_z);
        return std::fabs(dist_to_axis - radius);
    }

    Point3D sample(double theta, double z) const {
        Vector3D ax = axis.normalized();
        Vector3D u, v;
        if (std::fabs(ax.x) < 0.9) u = {ax.y, -ax.x, 0}; else u = {0, ax.z, -ax.y};
        u = Vector3D(u.x, u.y, u.z).normalized();
        v = Vector3D(ax.y*u.z - ax.z*u.y, ax.z*u.x - ax.x*u.z, ax.x*u.y - ax.y*u.x);
        return {origin.x + radius*std::cos(theta)*u.x + z*ax.x,
                origin.y + radius*std::cos(theta)*u.y + z*ax.y,
                origin.z + radius*std::cos(theta)*u.z + z*ax.z};
    }

    void print() const {
        std::cout << "Cylinder: origin=(" << origin.x << "," << origin.y << "," << origin.z
                  << ") axis=(" << axis.x << "," << axis.y << "," << axis.z
                  << ") radius=" << radius << "\n";
    }
};

// ============================================================
// Sphere: center + radius
// ============================================================
class Sphere {
public:
    Point3D center;
    double radius;

    Sphere() : center(0,0,0), radius(1.0) {}
    Sphere(Point3D c, double r) : center(c), radius(r) {}

    bool onSurface(Point3D p) const {
        double dx = p.x-center.x, dy = p.y-center.y, dz = p.z-center.z;
        return approx_equal(std::sqrt(dx*dx+dy*dy+dz*dz), radius);
    }

    double distance(Point3D p) const {
        double dx = p.x-center.x, dy = p.y-center.y, dz = p.z-center.z;
        return std::fabs(std::sqrt(dx*dx+dy*dy+dz*dz) - radius);
    }

    Vector3D normalAt(double phi, double theta) const {
        return {std::sin(phi)*std::cos(theta), std::sin(phi)*std::sin(theta), std::cos(phi)};
    }

    Point3D sample(double phi, double theta) const {
        return {center.x + radius*std::sin(phi)*std::cos(theta),
                center.y + radius*std::sin(phi)*std::sin(theta),
                center.z + radius*std::cos(phi)};
    }

    double surfaceArea() const { return 4.0 * M_PI * radius * radius; }
    double volume() const { return (4.0/3.0) * M_PI * radius * radius * radius; }

    void print() const {
        std::cout << "Sphere: center=(" << center.x << "," << center.y << "," << center.z
                  << ") radius=" << radius << "\n";
    }
};

// ============================================================
// Torus: major radius (R), minor radius (r), center, axis
// ============================================================
class Torus {
public:
    Point3D center;
    Vector3D axis;
    double majorRadius, minorRadius;

    Torus() : center(0,0,0), axis(0,0,1), majorRadius(2.0), minorRadius(0.5) {}
    Torus(Point3D c, Vector3D a, double R, double r) : center(c), axis(a), majorRadius(R), minorRadius(r) {}

    bool onSurface(Point3D p) const {
        Vector3D ax = axis.normalized();
        double dx = p.x-center.x, dy = p.y-center.y, dz = p.z-center.z;
        double proj = dx*ax.x + dy*ax.y + dz*ax.z;
        double to_cx = dx - proj*ax.x, to_cy = dy - proj*ax.y, to_cz = dz - proj*ax.z;
        double d_circle = std::sqrt(to_cx*to_cx + to_cy*to_cy + to_cz*to_cz);
        return approx_equal(std::sqrt((d_circle-majorRadius)*(d_circle-majorRadius) + proj*proj), minorRadius);
    }

    Point3D sample(double theta, double phi) const {
        Vector3D ax = axis.normalized();
        Vector3D u, v;
        if (std::fabs(ax.x) < 0.9) u = {ax.y, -ax.x, 0}; else u = {0, ax.z, -ax.y};
        u = Vector3D(u.x, u.y, u.z).normalized();
        v = Vector3D(ax.y*u.z - ax.z*u.y, ax.z*u.x - ax.x*u.z, ax.x*u.y - ax.y*u.x);
        return {center.x + (majorRadius+minorRadius*std::cos(phi))*std::cos(theta)*u.x + minorRadius*std::sin(phi)*v.x,
                center.y + (majorRadius+minorRadius*std::cos(phi))*std::cos(theta)*u.y + minorRadius*std::sin(phi)*v.y,
                center.z + (majorRadius+minorRadius*std::cos(phi))*std::cos(theta)*u.z + minorRadius*std::sin(phi)*v.z};
    }

    double surfaceArea() const { return 4.0 * M_PI * M_PI * majorRadius * minorRadius; }
    double volume() const { return 2.0 * M_PI * M_PI * majorRadius * minorRadius * minorRadius; }

    void print() const {
        std::cout << "Torus: center=(" << center.x << "," << center.y << "," << center.z
                  << ") axis=(" << axis.x << "," << axis.y << "," << axis.z
                  << ") R=" << majorRadius << " r=" << minorRadius << "\n";
    }
};

// ============================================================
// Cone: apex + axis + angle
// ============================================================
class Cone {
public:
    Point3D apex;
    Vector3D axis;
    double halfAngle;

    Cone() : apex(0,0,0), axis(0,0,1), halfAngle(M_PI/4) {}
    Cone(Point3D a, Vector3D ax, double angle) : apex(a), axis(ax), halfAngle(angle) {}

    double distance(Point3D p) const {
        double dx = p.x-apex.x, dy = p.y-apex.y, dz = p.z-apex.z;
        Vector3D ax = axis.normalized();
        double proj = dx*ax.x + dy*ax.y + dz*ax.z;
        double perp_x = dx - proj*ax.x, perp_y = dy - proj*ax.y, perp_z = dz - proj*ax.z;
        double perp_len = std::sqrt(perp_x*perp_x + perp_y*perp_y + perp_z*perp_z);
        if (approx_zero(proj) || approx_zero(perp_len)) return perp_len;
        double actual_angle = std::atan2(perp_len, proj);
        double angle_diff = actual_angle - halfAngle;
        return perp_len * std::sin(angle_diff);
    }

    void print() const {
        std::cout << "Cone: apex=(" << apex.x << "," << apex.y << "," << apex.z
                  << ") axis=(" << axis.x << "," << axis.y << "," << axis.z
                  << ") angle=" << halfAngle << "\n";
    }
};
