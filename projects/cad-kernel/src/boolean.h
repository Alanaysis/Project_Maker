// ============================================================
// cad-kernel: Boolean Operations on B-rep Solids
//
// Implements the core boolean operations:
// - Union (A | B): combined volume
// - Intersection (A & B): common volume
// - Difference (A - B): A minus B
//
// Simplified implementation for educational purposes.
// ============================================================

#pragma once
#include "brep.h"
#include "geometry.h"
#include <cmath>
#include <iostream>
#include <algorithm>
#include <queue>
#include <set>

// ============================================================
// Point classification: is a point inside a solid?
// Uses ray casting algorithm
// ============================================================
class PointClassifier {
public:
    static bool isInside(Solid* solid, Point3D p) {
        int intersections = 0;
        Point3D ray_dir = {1, 0, 0};

        for (auto& face : solid->faces) {
            if (rayIntersectsFace(p, ray_dir, face.get())) {
                intersections++;
            }
        }
        return (intersections % 2) == 1;
    }

    static bool isInsideShell(Shell* shell, Point3D p) {
        int intersections = 0;
        Point3D ray_dir = {1, 0, 0};
        for (auto* face : shell->faces) {
            if (rayIntersectsFace(p, ray_dir, face)) {
                intersections++;
            }
        }
        return (intersections % 2) == 1;
    }

private:
    static bool rayIntersectsFace(Point3D p, Point3D d, Face* face) {
        if (!face) return false;
        if (face->surface_type == SurfaceType::PLANE) {
            Vector3D n(face->normal.x, face->normal.y, face->normal.z);
            Vector3D n_norm = n.normalized();
            double denom = d.x*n_norm.x + d.y*n_norm.y + d.z*n_norm.z;
            if (approx_zero(denom)) return false;

            double diff_x = face->origin.x - p.x;
            double diff_y = face->origin.y - p.y;
            double diff_z = face->origin.z - p.z;
            double t = (diff_x*n_norm.x + diff_y*n_norm.y + diff_z*n_norm.z) / denom;
            if (t < 0) return false;

            Point3D hit = {p.x + t*d.x, p.y + t*d.y, p.z + t*d.z};
            return pointInFace(hit, face);
        }
        return false;
    }

    static bool pointInFace(Point3D p, Face* face) {
        if (!face || face->vertices.empty()) return false;
        for (size_t i = 0; i < face->vertices.size(); ++i) {
            size_t next = (i + 1) % face->vertices.size();
            if (pointNearLineSegment(p, face->vertices[i]->point, face->vertices[next]->point)) {
                return true;
            }
        }
        return pointInPolygon(p, face);
    }

    static bool pointNearLineSegment(Point3D p, Point3D a, Point3D b) {
        double ab_x = b.x-a.x, ab_y = b.y-a.y, ab_z = b.z-a.z;
        double ap_x = p.x-a.x, ap_y = p.y-a.y, ap_z = p.z-a.z;
        double len2 = ab_x*ab_x + ab_y*ab_y + ab_z*ab_z;
        if (approx_zero(len2)) return approx_zero(std::sqrt(ap_x*ap_x+ap_y*ap_y+ap_z*ap_z));
        double t = (ap_x*ab_x + ap_y*ab_y + ap_z*ab_z) / len2;
        t = clamp(t, 0.0, 1.0);
        Point3D proj = {a.x + t*ab_x, a.y + t*ab_y, a.z + t*ab_z};
        double dist = std::sqrt((p.x-proj.x)*(p.x-proj.x) + (p.y-proj.y)*(p.y-proj.y) + (p.z-proj.z)*(p.z-proj.z));
        return dist < EPSILON * 10;
    }

    static bool pointInPolygon(Point3D p, Face* face) {
        if (face->vertices.size() < 3) return false;
        Vector3D n(face->normal.x, face->normal.y, face->normal.z);
        int axis = 0;
        double max_comp = std::fabs(n.x);
        if (std::fabs(n.y) > max_comp) { axis = 1; max_comp = std::fabs(n.y); }
        if (std::fabs(n.z) > max_comp) { axis = 2; max_comp = std::fabs(n.z); }

        std::vector<std::pair<double,double> > poly2d;
        for (const auto& vp : face->vertices) {
            if (axis == 0) poly2d.push_back(std::make_pair(vp->point.y, vp->point.z));
            else if (axis == 1) poly2d.push_back(std::make_pair(vp->point.x, vp->point.z));
            else poly2d.push_back(std::make_pair(vp->point.x, vp->point.y));
        }

        double p2_x, p2_y;
        if (axis == 0) { p2_x = p.y; p2_y = p.z; }
        else if (axis == 1) { p2_x = p.x; p2_y = p.z; }
        else { p2_x = p.x; p2_y = p.y; }

        int wn = 0;
        for (size_t i = 0, j = poly2d.size()-1; i < poly2d.size(); j = i++) {
            if (poly2d[i].second <= p2_y) {
                if (poly2d[j].second > p2_y) {
                    double val = poly2d[i].first + (p2_y - poly2d[i].second) /
                        (poly2d[j].second - poly2d[i].second) * (poly2d[j].first - poly2d[i].first);
                    if (val < p2_x) wn++;
                }
            } else {
                if (poly2d[j].second <= p2_y) {
                    double val = poly2d[i].first + (p2_y - poly2d[i].second) /
                        (poly2d[j].second - poly2d[i].second) * (poly2d[j].first - poly2d[i].first);
                    if (val > p2_x) wn--;
                }
            }
        }
        return wn != 0;
    }
};

// ============================================================
// Boolean operations on two solids
// ============================================================
class BooleanOps {
public:
    static std::unique_ptr<Solid> unionSolids(Solid* a, Solid* b) {
        std::cout << "  Boolean Union (A | B):\n";
        std::cout << "    Solid A: " << a->toString() << "\n";
        std::cout << "    Solid B: " << b->toString() << "\n";

        auto result = std::make_unique<Solid>();
        result->name = "Union(A,B)";
        std::vector<std::unique_ptr<Face> > all_faces;

        for (auto& f : a->faces) {
            Point3D centroid = computeFaceCentroid(f.get());
            if (!PointClassifier::isInside(b, centroid)) {
                all_faces.push_back(std::move(f));
            }
        }
        for (auto& f : b->faces) {
            Point3D centroid = computeFaceCentroid(f.get());
            if (!PointClassifier::isInside(a, centroid)) {
                all_faces.push_back(std::move(f));
            }
        }

        result->outer_shell = ShellBuilder::createWatertightShell(std::move(all_faces));
        result->shells.push_back(std::move(result->outer_shell));
        std::cout << "    Result: " << result->toString() << "\n";
        return result;
    }

    static std::unique_ptr<Solid> intersectSolids(Solid* a, Solid* b) {
        std::cout << "  Boolean Intersection (A & B):\n";
        std::cout << "    Solid A: " << a->toString() << "\n";
        std::cout << "    Solid B: " << b->toString() << "\n";

        auto result = std::make_unique<Solid>();
        result->name = "Intersect(A,B)";
        std::vector<std::unique_ptr<Face> > all_faces;

        for (auto& f : a->faces) {
            Point3D centroid = computeFaceCentroid(f.get());
            if (PointClassifier::isInside(b, centroid)) {
                all_faces.push_back(std::move(f));
            }
        }
        for (auto& f : b->faces) {
            Point3D centroid = computeFaceCentroid(f.get());
            if (PointClassifier::isInside(a, centroid)) {
                all_faces.push_back(std::move(f));
            }
        }

        result->outer_shell = ShellBuilder::createWatertightShell(std::move(all_faces));
        result->shells.push_back(std::move(result->outer_shell));
        std::cout << "    Result: " << result->toString() << "\n";
        return result;
    }

    static std::unique_ptr<Solid> differenceSolids(Solid* a, Solid* b) {
        std::cout << "  Boolean Difference (A - B):\n";
        std::cout << "    Solid A: " << a->toString() << "\n";
        std::cout << "    Solid B: " << b->toString() << "\n";

        auto result = std::make_unique<Solid>();
        result->name = "Diff(A,B)";
        std::vector<std::unique_ptr<Face> > all_faces;

        for (auto& f : a->faces) {
            Point3D centroid = computeFaceCentroid(f.get());
            if (!PointClassifier::isInside(b, centroid)) {
                all_faces.push_back(std::move(f));
            }
        }
        for (auto& f : b->faces) {
            Point3D centroid = computeFaceCentroid(f.get());
            if (PointClassifier::isInside(a, centroid)) {
                std::unique_ptr<Face> flipped = flipFace(std::move(f));
                all_faces.push_back(std::move(flipped));
            }
        }

        result->outer_shell = ShellBuilder::createWatertightShell(std::move(all_faces));
        result->shells.push_back(std::move(result->outer_shell));
        std::cout << "    Result: " << result->toString() << "\n";
        return result;
    }

    static std::unique_ptr<Solid> symmetricDifference(Solid* a, Solid* b) {
        std::cout << "  Boolean Symmetric Difference:\n";
        auto result = std::make_unique<Solid>();
        result->name = "SymDiff(A,B)";
        std::vector<std::unique_ptr<Face> > all_faces;

        for (auto& f : a->faces) {
            Point3D centroid = computeFaceCentroid(f.get());
            if (!PointClassifier::isInside(b, centroid)) {
                all_faces.push_back(std::move(f));
            }
        }
        for (auto& f : b->faces) {
            Point3D centroid = computeFaceCentroid(f.get());
            if (!PointClassifier::isInside(a, centroid)) {
                std::unique_ptr<Face> flipped = flipFace(std::move(f));
                all_faces.push_back(std::move(flipped));
            }
        }

        result->outer_shell = ShellBuilder::createWatertightShell(std::move(all_faces));
        result->shells.push_back(std::move(result->outer_shell));
        return result;
    }

private:
    static Point3D computeFaceCentroid(Face* face) {
        Point3D centroid(0, 0, 0);
        int count = 0;
        for (const auto& vp : face->vertices) {
            centroid.x += vp->point.x;
            centroid.y += vp->point.y;
            centroid.z += vp->point.z;
            count++;
        }
        if (count > 0) {
            centroid.x /= count; centroid.y /= count; centroid.z /= count;
        }
        return centroid;
    }

    static std::unique_ptr<Face> flipFace(std::unique_ptr<Face> face) {
        auto vertices = std::move(face->vertices);
        std::reverse(vertices.begin(), vertices.end());
        auto flipped = std::make_unique<Face>();
        flipped->surface_type = face->surface_type;
        flipped->origin = face->origin;
        flipped->normal = Vector3D(-face->normal.x, -face->normal.y, -face->normal.z);
        flipped->radius1 = face->radius1;
        flipped->radius2 = face->radius2;
        flipped->axis = face->axis;
        flipped->center = face->center;
        flipped->vertices = std::move(vertices);
        flipped->edges = std::move(face->edges);
        return flipped;
    }
};
