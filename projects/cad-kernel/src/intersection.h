// ============================================================
// cad-kernel: Surface-Surface Intersection
//
// Computes the intersection curve between two surfaces.
// This is a fundamental operation in CAD kernels used for:
// - Boolean operations (finding where faces meet)
// - Filleting and blending
// - Mesh generation
//
// For simplicity, we focus on planar intersections and
// basic curve-surface intersections.
// ============================================================

#include "brep.h"
#include "geometry.h"
#include <cmath>
#include <iostream>
#include <vector>

// ============================================================
// Intersection result: a curve (represented as a set of points)
// ============================================================
struct IntersectionCurve {
    std::vector<Point3D> points;
    bool valid = false;

    void addPoint(Point3D p) { points.push_back(p); }

    size_t size() const { return points.size(); }

    bool isEmpty() const { return points.empty(); }

    void print() const {
        if (!valid) {
            std::cout << "  No intersection found.\n";
            return;
        }
        std::cout << "  Intersection curve: " << points.size() << " points\n";
        for (size_t i = 0; i < std::min(size_t(10), points.size()); ++i) {
            std::cout << "    (" << points[i].x << ", " << points[i].y << ", " << points[i].z << ")\n";
        }
        if (points.size() > 10) {
            std::cout << "    ... (" << (points.size() - 10) << " more points)\n";
        }
    }
};

// ============================================================
// Surface-Surface Intersection Algorithms
// ============================================================
class SurfaceIntersection {
public:
    // ============================================================
    // Plane-Plane intersection: returns a line
    // Two non-parallel planes intersect in a line
    // ============================================================
    static IntersectionCurve planePlane(const Plane& p1, const Plane& p2) {
        IntersectionCurve curve;

        Vector3D n1 = p1.getNormal();
        Vector3D n2 = p2.getNormal();

        // Check if planes are parallel
        double dot_n = dot(n1, n2);
        if (std::fabs(std::fabs(dot_n) - 1.0) < EPSILON) {
            curve.valid = false;
            return curve;
        }

        // Direction of intersection line = cross product of normals
        Vector3D dir = Vector3D(
            n1.y * n2.z - n1.z * n2.y,
            n1.z * n2.x - n1.x * n2.z,
            n1.x * n2.y - n1.y * n2.x
        );

        if (approx_zero(dir.length())) {
            curve.valid = false;
            return curve;
        }

        // Find a point on the intersection line
        Point3D origin = findLineOrigin(p1, p2);
        curve.valid = true;

        // Sample points along the line
        double dir_len = dir.length();
        dir = Vector3D(dir.x/dir_len, dir.y/dir_len, dir.z/dir_len);

        for (int i = -50; i <= 50; ++i) {
            double t = i * 0.1;
            curve.addPoint({origin.x + t*dir.x, origin.y + t*dir.y, origin.z + t*dir.z});
        }

        return curve;
    }

    // ============================================================
    // Plane-Cylinder intersection: returns ellipse or circle
    // ============================================================
    static IntersectionCurve planeCylinder(const Plane& plane, const Cylinder& cyl) {
        IntersectionCurve curve;

        Vector3D ax = Vector3D(cyl.axis.x, cyl.axis.y, cyl.axis.z).normalized();
        Vector3D n = plane.getNormal();

        // If plane is parallel to cylinder axis, intersection is two parallel lines
        double sin_theta = std::fabs(dot(ax, n));

        if (sin_theta < EPSILON) {
            // Parallel: two lines
            curve.valid = false;
            return curve;
        }

        // Find intersection point
        Vector3D diff(plane.origin.x - cyl.origin.x,
                      plane.origin.y - cyl.origin.y,
                      plane.origin.z - cyl.origin.z);

        // Project center to plane
        double d = dot(diff, n);
        Point3D center_on_plane = {
            cyl.origin.x - n.x * d,
            cyl.origin.y - n.y * d,
            cyl.origin.z - n.z * d
        };

        // The intersection is an ellipse (or circle if plane is perpendicular to axis)
        // Sample the intersection curve
        curve.valid = true;

        // Find orthonormal basis for the intersection plane
        Vector3D u = Vector3D(n.y * ax.z - n.z * ax.y,
                               n.z * ax.x - n.x * ax.z,
                               n.x * ax.y - n.y * ax.x);
        u = Vector3D(u.x, u.y, u.z).normalized();

        Vector3D v = Vector3D(n.y * u.z - n.z * u.y,
                               n.z * u.x - n.x * u.z,
                               n.x * u.y - n.y * u.x);

        // Semi-axes of the ellipse
        double cos_theta = std::fabs(dot(ax, n));
        double a = cyl.radius;
        double b = cyl.radius / cos_theta;

        for (int i = 0; i <= 100; ++i) {
            double theta = 2.0 * M_PI * i / 100;
            Point3D p = {
                center_on_plane.x + a * std::cos(theta) * u.x + b * std::sin(theta) * v.x,
                center_on_plane.y + a * std::cos(theta) * u.y + b * std::sin(theta) * v.y,
                center_on_plane.z + a * std::cos(theta) * u.z + b * std::sin(theta) * v.z
            };
            curve.addPoint(p);
        }

        return curve;
    }

    // ============================================================
    // Plane-Sphere intersection: returns circle
    // ============================================================
    static IntersectionCurve planeSphere(const Plane& plane, const Sphere& sphere) {
        IntersectionCurve curve;

        double dist = plane.signedDistance(sphere.center);

        if (std::fabs(std::fabs(dist) - sphere.radius) < EPSILON) {
            // Plane tangent to sphere: single point
            curve.addPoint(plane.project(sphere.center));
            curve.valid = true;
            return curve;
        }

        if (std::fabs(std::fabs(dist)) > sphere.radius + EPSILON) {
            // Plane doesn't intersect sphere
            curve.valid = false;
            return curve;
        }

        // Intersection is a circle
        double r = std::sqrt(sphere.radius * sphere.radius - dist * dist);
        Point3D center = plane.project(sphere.center);

        curve.valid = true;

        // Find orthonormal basis for the circle plane
        Vector3D n = plane.getNormal();
        Vector3D u, v;

        if (std::fabs(n.x) < 0.9) {
            u = Vector3D(n.y, -n.x, 0).normalized();
        } else {
            u = Vector3D(0, n.z, -n.y).normalized();
        }
        v = Vector3D(n.y * u.z - n.z * u.y,
                      n.z * u.x - n.x * u.z,
                      n.x * u.y - n.y * u.x);

        for (int i = 0; i <= 100; ++i) {
            double theta = 2.0 * M_PI * i / 100;
            curve.addPoint({
                center.x + r * std::cos(theta) * u.x + r * std::sin(theta) * v.x,
                center.y + r * std::cos(theta) * u.y + r * std::sin(theta) * v.y,
                center.z + r * std::cos(theta) * u.z + r * std::sin(theta) * v.z
            });
        }

        return curve;
    }

    // ============================================================
    // Plane-Torus intersection: returns complex curve
    // ============================================================
    static IntersectionCurve planeTorus(const Plane& plane, const Torus& torus) {
        IntersectionCurve curve;

        // Sample points on torus and check which lie on the plane
        curve.valid = true;

        Vector3D ax = Vector3D(torus.axis.x, torus.axis.y, torus.axis.z).normalized();

        for (int i = 0; i <= 200; ++i) {
            double theta = 2.0 * M_PI * i / 200;

            // For each theta, find phi values where torus intersects plane
            // This requires solving a quartic equation - simplified here
            for (int j = 0; j <= 50; ++j) {
                double phi = 2.0 * M_PI * j / 50;
                Point3D p = sampleTorus(torus, theta, phi);
                double dist = plane.signedDistance(p);

                if (std::fabs(dist) < 0.1) { // Within tolerance
                    // Project to plane
                    curve.addPoint(plane.project(p));
                }
            }
        }

        return curve;
    }

    // ============================================================
    // Sphere-Sphere intersection: returns circle
    // ============================================================
    static IntersectionCurve sphereSphere(const Sphere& s1, const Sphere& s2) {
        IntersectionCurve curve;

        double dx = s2.center.x - s1.center.x;
        double dy = s2.center.y - s1.center.y;
        double dz = s2.center.z - s1.center.z;
        double d = std::sqrt(dx*dx + dy*dy + dz*dz);

        // Check if spheres intersect
        if (d > s1.radius + s2.radius + EPSILON) {
            curve.valid = false; // Too far apart
            return curve;
        }
        if (d < std::fabs(s1.radius - s2.radius) - EPSILON) {
            curve.valid = false; // One inside other
            return curve;
        }
        if (approx_zero(d)) {
            curve.valid = false; // Concentric
            return curve;
        }

        // Intersection is a circle in a plane perpendicular to line of centers
        double a = (s1.radius * s1.radius - s2.radius * s2.radius + d*d) / (2*d);
        Point3D circleCenter = {
            s1.center.x + a * dx / d,
            s1.center.y + a * dy / d,
            s1.center.z + a * dz / d
        };
        double r = std::sqrt(s1.radius * s1.radius - a * a);

        curve.valid = true;

        // Find orthonormal basis
        Vector3D dir = Vector3D(dx, dy, dz).normalized();
        Vector3D u, v;

        if (std::fabs(dir.x) < 0.9) {
            u = Vector3D(dir.y, -dir.x, 0).normalized();
        } else {
            u = Vector3D(0, dir.z, -dir.y).normalized();
        }
        v = Vector3D(dir.y * u.z - dir.z * u.y,
                      dir.z * u.x - dir.x * u.z,
                      dir.x * u.y - dir.y * u.x);

        for (int i = 0; i <= 100; ++i) {
            double theta = 2.0 * M_PI * i / 100;
            curve.addPoint({
                circleCenter.x + r * std::cos(theta) * u.x + r * std::sin(theta) * v.x,
                circleCenter.y + r * std::cos(theta) * u.y + r * std::sin(theta) * v.y,
                circleCenter.z + r * std::cos(theta) * u.z + r * std::sin(theta) * v.z
            });
        }

        return curve;
    }

    // ============================================================
    // Cylinder-Cylinder intersection: complex curve
    // ============================================================
    static IntersectionCurve cylinderCylinder(const Cylinder& c1, const Cylinder& c2) {
        IntersectionCurve curve;

        // Simplified: sample points along first cylinder and check against second
        curve.valid = true;

        Vector3D ax1 = Vector3D(c1.axis.x, c1.axis.y, c1.axis.z).normalized();
        Vector3D ax2 = Vector3D(c2.axis.x, c2.axis.y, c2.axis.z).normalized();

        // Find a perpendicular basis for cylinder 1
        Vector3D u1, v1;
        if (std::fabs(ax1.x) < 0.9) {
            u1 = Vector3D(ax1.y, -ax1.x, 0);
        } else {
            u1 = Vector3D(0, ax1.z, -ax1.y);
        }
        u1 = Vector3D(u1.x, u1.y, u1.z).normalized();
        v1 = Vector3D(ax1.y*u1.z - ax1.z*u1.y,
                       ax1.z*u1.x - ax1.x*u1.z,
                       ax1.x*u1.y - ax1.y*u1.x);

        for (int i = 0; i <= 200; ++i) {
            double theta = 2.0 * M_PI * i / 200;

            // For each theta, sweep along the axis
            for (int j = -50; j <= 50; ++j) {
                double z = j * 0.1;
                Point3D p = {
                    c1.origin.x + c1.radius * std::cos(theta) * u1.x + z * ax1.x,
                    c1.origin.y + c1.radius * std::cos(theta) * u1.y + z * ax1.y,
                    c1.origin.z + c1.radius * std::cos(theta) * u1.z + z * ax1.z
                };

                double dist_to_c2 = distanceToCylinder(p, c2);
                if (std::fabs(dist_to_c2) < 0.05) {
                    curve.addPoint(p);
                }
            }
        }

        return curve;
    }

private:
    static Point3D findLineOrigin(const Plane& p1, const Plane& p2) {
        // Simplified: return midpoint of origins
        return {(p1.origin.x + p2.origin.x) * 0.5,
                (p1.origin.y + p2.origin.y) * 0.5,
                (p1.origin.z + p2.origin.z) * 0.5};
    }

    static Point3D sampleTorus(const Torus& torus, double theta, double phi) {
        Vector3D ax = Vector3D(torus.axis.x, torus.axis.y, torus.axis.z).normalized();
        Vector3D u, v;
        if (std::fabs(ax.x) < 0.9) {
            u = {ax.y, -ax.x, 0};
        } else {
            u = {0, ax.z, -ax.y};
        }
        u = Vector3D(u.x, u.y, u.z).normalized();
        v = Vector3D(
            ax.y * u.z - ax.z * u.y,
            ax.z * u.x - ax.x * u.z,
            ax.x * u.y - ax.y * u.x
        );

        return {
            torus.center.x + (torus.majorRadius + torus.minorRadius * std::cos(phi)) * std::cos(theta) * u.x
                            + torus.minorRadius * std::sin(phi) * v.x,
            torus.center.y + (torus.majorRadius + torus.minorRadius * std::cos(phi)) * std::cos(theta) * u.y
                            + torus.minorRadius * std::sin(phi) * v.y,
            torus.center.z + (torus.majorRadius + torus.minorRadius * std::cos(phi)) * std::cos(theta) * u.z
                            + torus.minorRadius * std::sin(phi) * v.z
        };
    }

    static double distanceToCylinder(Point3D p, const Cylinder& cyl) {
        Vector3D diff(p.x - cyl.origin.x, p.y - cyl.origin.y, p.z - cyl.origin.z);
        Vector3D ax = Vector3D(cyl.axis.x, cyl.axis.y, cyl.axis.z).normalized();
        Point3D cp = cross({ax.x, ax.y, ax.z}, {diff.x, diff.y, diff.z});
        double dist_to_axis = std::sqrt(cp.x*cp.x + cp.y*cp.y + cp.z*cp.z);
        return std::fabs(dist_to_axis - cyl.radius);
    }
};
