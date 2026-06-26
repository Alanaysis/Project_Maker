// ============================================================
// cad-kernel: Topology Management
//
// Implements topological entity construction and relationships:
// - Wiring: ordered loop of edges connected by vertices
// - Shell: collection of faces forming a closed boundary
// - Solid: volume bounded by shells
//
// These functions manage the connectivity between topological
// entities, which is the core of B-rep data structure.
// ============================================================

#include "brep.h"
#include "geometry.h"
#include <cmath>
#include <iostream>
#include <algorithm>

// ============================================================
// Wiring: an ordered loop of edges
// ============================================================
class Wiring {
public:
    std::vector<std::unique_ptr<Edge>> edges;
    std::vector<std::unique_ptr<Vertex>> vertices;

    Wiring() = default;

    // Create a wiring from a list of 3D points (closed loop)
    static Wiring createFromPoints(const std::vector<Point3D>& points) {
        Wiring w;
        if (points.size() < 3) return w;

        // Create vertices
        for (const auto& p : points) {
            w.vertices.push_back(std::make_unique<Vertex>(p));
        }

        // Create edges connecting consecutive vertices
        for (size_t i = 0; i < points.size(); ++i) {
            size_t next = (i + 1) % points.size();
            auto edge = std::make_unique<Edge>(points[i], points[next]);
            edge->curve_type = CurveType::LINE;
            w.edges.push_back(std::move(edge));
        }

        return w;
    }

    // Get number of vertices/edges
    int size() const { return static_cast<int>(edges.size()); }

    // Check if wiring is closed (first and last vertex coincide)
    bool isClosed() const {
        if (edges.empty()) return false;
        return edges.front()->start == edges.back()->end;
    }

    // Compute perimeter
    double perimeter() const {
        double total = 0.0;
        for (const auto& e : edges) {
            total += e->length();
        }
        return total;
    }

    // Compute bounding box
    struct BoundingBox {
        Point3D min, max;
    };

    BoundingBox boundingBox() const {
        BoundingBox bb;
        if (vertices.empty()) {
            bb.min = bb.max = {0,0,0};
            return bb;
        }
        bb.min = bb.max = vertices.front()->point;
        for (const auto& v : vertices) {
            bb.min.x = std::min(bb.min.x, v->point.x);
            bb.min.y = std::min(bb.min.y, v->point.y);
            bb.min.z = std::min(bb.min.z, v->point.z);
            bb.max.x = std::max(bb.max.x, v->point.x);
            bb.max.y = std::max(bb.max.y, v->point.y);
            bb.max.z = std::max(bb.max.z, v->point.z);
        }
        return bb;
    }
};

// ============================================================
// FaceBuilder: constructs a Face from a wiring
// ============================================================
class FaceBuilder {
public:
    // Create a planar face from a wiring (list of vertices)
    static std::unique_ptr<Face> createPlanarFace(const std::vector<Point3D>& points) {
        auto face = std::make_unique<Face>();
        face->surface_type = SurfaceType::PLANE;

        if (points.size() < 3) return face;

        // Compute face normal using cross product of first two edges
        Vector3D e1(points[1].x - points[0].x, points[1].y - points[0].y, points[1].z - points[0].z);
        Vector3D e2(points[2].x - points[0].x, points[2].y - points[0].y, points[2].z - points[0].z);
        face->normal = Vector3D(
            e1.y * e2.z - e1.z * e2.y,
            e1.z * e2.x - e1.x * e2.z,
            e1.x * e2.y - e1.y * e2.x
        );

        // Set origin to first point
        face->origin = points[0];

        // Create half-edges and edges
        for (size_t i = 0; i < points.size(); ++i) {
            size_t next = (i + 1) % points.size();

            auto edge = std::make_unique<Edge>(points[i], points[next]);
            edge->curve_type = CurveType::LINE;
            face->edges.push_back(std::move(edge));

            auto vertex = std::make_unique<Vertex>(points[i]);
            face->vertices.push_back(std::move(vertex));
        }

        // Compute area of planar face
        face->area = computePlanarArea(points);

        return face;
    }

    // Create a cylindrical face
    static std::unique_ptr<Face> createCylindricalFace(
        Point3D origin, Vector3D axis, double radius,
        double startAngle, double endAngle, double height)
    {
        auto face = std::make_unique<Face>();
        face->surface_type = SurfaceType::CYLINDER;
        face->origin = origin;
        face->axis = Vector3D(axis.x, axis.y, axis.z);
        face->radius1 = radius;
        face->height = height;
        face->u_min = startAngle;
        face->u_max = endAngle;
        face->v_min = 0.0;
        face->v_max = height;

        // Approximate with straight edges
        const int segments = 32;
        for (int i = 0; i < segments; ++i) {
            double a1 = startAngle + (endAngle - startAngle) * i / segments;
            double a2 = startAngle + (endAngle - startAngle) * (i + 1) / segments;

            Point3D p1 = sampleCylinderPoint(origin, axis, radius, a1, 0);
            Point3D p2 = sampleCylinderPoint(origin, axis, radius, a2, 0);
            Point3D p3 = sampleCylinderPoint(origin, axis, radius, a2, height);
            Point3D p4 = sampleCylinderPoint(origin, axis, radius, a1, height);

            auto edge = std::make_unique<Edge>(p1, p2);
            edge->curve_type = CurveType::LINE;
            face->edges.push_back(std::move(edge));
        }

        // Compute approximate area
        face->area = radius * (endAngle - startAngle) * height;

        return face;
    }

    // Create a spherical face
    static std::unique_ptr<Face> createSphericalFace(
        Point3D center, double radius,
        double phi_min, double phi_max,
        double theta_min, double theta_max)
    {
        auto face = std::make_unique<Face>();
        face->surface_type = SurfaceType::SPHERE;
        face->origin = center;
        face->radius1 = radius;
        face->u_min = phi_min;
        face->u_max = phi_max;
        face->v_min = theta_min;
        face->v_max = theta_max;

        // Approximate with planar patches
        const int phi_seg = 16;
        const int theta_seg = 16;
        for (int i = 0; i < phi_seg; ++i) {
            for (int j = 0; j < theta_seg; ++j) {
                double phi1 = phi_min + (phi_max - phi_min) * i / phi_seg;
                double phi2 = phi_min + (phi_max - phi_min) * (i + 1) / phi_seg;
                double theta1 = theta_min + (theta_max - theta_min) * j / theta_seg;
                double theta2 = theta_min + (theta_max - theta_min) * (j + 1) / theta_seg;

                Point3D corners[4] = {
                    sampleSpherePoint(center, radius, phi1, theta1),
                    sampleSpherePoint(center, radius, phi2, theta1),
                    sampleSpherePoint(center, radius, phi2, theta2),
                    sampleSpherePoint(center, radius, phi1, theta2)
                };

                auto patch = createPlanarFace({corners[0], corners[1], corners[2], corners[3]});
                face->sub_faces.push_back(std::move(patch));
            }
        }

        // Compute approximate area
        face->area = (phi_max - phi_min) * (theta_max - theta_min) * radius * radius;

        return face;
    }

    // Create a toroidal face
    static std::unique_ptr<Face> createTorusFace(
        Point3D center, Vector3D axis,
        double majorR, double minorR,
        double theta_min, double theta_max,
        double phi_min, double phi_max)
    {
        auto face = std::make_unique<Face>();
        face->surface_type = SurfaceType::TORUS;
        face->origin = center;
        face->axis = Vector3D(axis.x, axis.y, axis.z);
        face->radius1 = majorR;
        face->radius2 = minorR;
        face->u_min = theta_min;
        face->u_max = theta_max;
        face->v_min = phi_min;
        face->v_max = phi_max;

        // Approximate with planar patches
        const int theta_seg = 16;
        const int phi_seg = 16;
        for (int i = 0; i < theta_seg; ++i) {
            for (int j = 0; j < phi_seg; ++j) {
                double t1 = theta_min + (theta_max - theta_min) * i / theta_seg;
                double t2 = theta_min + (theta_max - theta_min) * (i + 1) / theta_seg;
                double p1 = phi_min + (phi_max - phi_min) * j / phi_seg;
                double p2 = phi_min + (phi_max - phi_min) * (j + 1) / phi_seg;

                Point3D corners[4] = {
                    sampleTorusPoint(center, axis, majorR, minorR, t1, p1),
                    sampleTorusPoint(center, axis, majorR, minorR, t2, p1),
                    sampleTorusPoint(center, axis, majorR, minorR, t2, p2),
                    sampleTorusPoint(center, axis, majorR, minorR, t1, p2)
                };

                auto patch = createPlanarFace({corners[0], corners[1], corners[2], corners[3]});
                face->sub_faces.push_back(std::move(patch));
            }
        }

        // Area: (2*pi*R) * (2*pi*r) for full torus, scaled by angle fractions
        face->area = (2.0 * M_PI * majorR) * (2.0 * M_PI * minorR) *
                     ((theta_max - theta_min) / (2.0 * M_PI)) *
                     ((phi_max - phi_min) / (2.0 * M_PI));

        return face;
    }

private:
    static double computePlanarArea(const std::vector<Point3D>& points) {
        if (points.size() < 3) return 0.0;

        // Compute normal
        Vector3D e1(points[1].x - points[0].x, points[1].y - points[0].y, points[1].z - points[0].z);
        Vector3D e2(points[2].x - points[0].x, points[2].y - points[0].y, points[2].z - points[0].z);
        Vector3D n = Vector3D(
            e1.y * e2.z - e1.z * e2.y,
            e1.z * e2.x - e1.x * e2.z,
            e1.x * e2.y - e1.y * e2.x
        );
        double area = 0.0;

        // Triangle fan method
        for (size_t i = 1; i + 1 < points.size(); ++i) {
            Vector3D a(points[i].x - points[0].x, points[i].y - points[0].y, points[i].z - points[0].z);
            Vector3D b(points[i+1].x - points[0].x, points[i+1].y - points[0].y, points[i+1].z - points[0].z);
            Vector3D cross_prod = Vector3D(
                a.y * b.z - a.z * b.y,
                a.z * b.x - a.x * b.z,
                a.x * b.y - a.y * b.x
            );
            area += 0.5 * std::sqrt(cross_prod.x*cross_prod.x + cross_prod.y*cross_prod.y + cross_prod.z*cross_prod.z);
        }

        return area;
    }

    static Point3D sampleCylinderPoint(Point3D origin, Vector3D axis, double radius,
                                        double angle, double height) {
        Vector3D ax = Vector3D(axis.x, axis.y, axis.z).normalized();
        // Find perpendicular basis
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
            origin.x + radius * std::cos(angle) * u.x + height * ax.x,
            origin.y + radius * std::cos(angle) * u.y + height * ax.y,
            origin.z + radius * std::cos(angle) * u.z + height * ax.z
        };
    }

    static Point3D sampleSpherePoint(Point3D center, double radius,
                                      double phi, double theta) {
        return {
            center.x + radius * std::sin(phi) * std::cos(theta),
            center.y + radius * std::sin(phi) * std::sin(theta),
            center.z + radius * std::cos(phi)
        };
    }

    static Point3D sampleTorusPoint(Point3D center, Vector3D axis,
                                     double R, double r,
                                     double theta, double phi) {
        Vector3D ax = Vector3D(axis.x, axis.y, axis.z).normalized();
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
            center.x + (R + r * std::cos(phi)) * std::cos(theta) * u.x
                      + r * std::sin(phi) * v.x,
            center.y + (R + r * std::cos(phi)) * std::cos(theta) * u.y
                      + r * std::sin(phi) * v.y,
            center.z + (R + r * std::cos(phi)) * std::cos(theta) * u.z
                      + r * std::sin(phi) * v.z
        };
    }
};

// ============================================================
// ShellBuilder: constructs a Shell from faces
// ============================================================
class ShellBuilder {
public:
    // Create a watertight shell from a list of faces
    static std::unique_ptr<Shell> createWatertightShell(std::vector<std::unique_ptr<Face>> face_list) {
        auto shell = std::make_unique<Shell>();

        for (auto& f : face_list) {
            shell->faces.push_back(f.release());
        }

        // Set solid ownership for orientation
        for (auto& f : shell->faces) {
            f->shell = shell.get();
        }

        return shell;
    }

    // Check if shell is watertight
    static bool isWatertight(const std::vector<Face*>& faces) {
        // A shell is watertight if every edge is shared by exactly 2 faces
        std::unordered_map<std::string, int> edge_count;

        for (auto* face : faces) {
            for (auto* he : face->outer_loop) {
                if (he && he->edge) {
                    std::string key = std::to_string(he->edge->id);
                    edge_count[key]++;
                }
            }
        }

        for (const auto& pair : edge_count) {
            if (pair.second != 2) return false;
        }

        return true;
    }
};

// ============================================================
// SolidBuilder: constructs a Solid from shells
// ============================================================
class SolidBuilder {
public:
    // Create a solid from an outer shell (and optional inner shells)
    static std::unique_ptr<Solid> createBox(
        Point3D corner, double width, double height, double depth)
    {
        auto solid = std::make_unique<Solid>();
        solid->name = "Box";

        // Six faces of the box
        std::vector<Point3D> front = {
            {corner.x, corner.y, corner.z},
            {corner.x + width, corner.y, corner.z},
            {corner.x + width, corner.y + height, corner.z},
            {corner.x, corner.y + height, corner.z}
        };
        std::vector<Point3D> back = {
            {corner.x, corner.y + depth, corner.z},
            {corner.x + width, corner.y + depth, corner.z},
            {corner.x + width, corner.y + depth, corner.z + height},
            {corner.x, corner.y + depth, corner.z + height}
        };
        std::vector<Point3D> bottom = {
            {corner.x, corner.y, corner.z},
            {corner.x + width, corner.y, corner.z},
            {corner.x + width, corner.y, corner.z + depth},
            {corner.x, corner.y, corner.z + depth}
        };
        std::vector<Point3D> top = {
            {corner.x, corner.y + height, corner.z},
            {corner.x + width, corner.y + height, corner.z},
            {corner.x + width, corner.y + height, corner.z + depth},
            {corner.x, corner.y + height, corner.z + depth}
        };
        std::vector<Point3D> left = {
            {corner.x, corner.y, corner.z},
            {corner.x, corner.y + height, corner.z},
            {corner.x, corner.y + height, corner.z + depth},
            {corner.x, corner.y, corner.z + depth}
        };
        std::vector<Point3D> right = {
            {corner.x + width, corner.y, corner.z},
            {corner.x + width, corner.y + height, corner.z},
            {corner.x + width, corner.y + height, corner.z + depth},
            {corner.x + width, corner.y, corner.z + depth}
        };

        std::vector<std::unique_ptr<Face>> faces;
        faces.push_back(FaceBuilder::createPlanarFace(front));
        faces.push_back(FaceBuilder::createPlanarFace(back));
        faces.push_back(FaceBuilder::createPlanarFace(bottom));
        faces.push_back(FaceBuilder::createPlanarFace(top));
        faces.push_back(FaceBuilder::createPlanarFace(left));
        faces.push_back(FaceBuilder::createPlanarFace(right));

        // Flip normals for back face to ensure outward orientation
        if (!faces[1]->normal.x == 0 || !faces[1]->normal.y == 0 || !faces[1]->normal.z == 0) {
            // Reverse the order to flip normal
            std::reverse(faces[1]->vertices.begin(), faces[1]->vertices.end());
        }

        solid->outer_shell = ShellBuilder::createWatertightShell(std::move(faces));
        solid->shells.push_back(std::move(solid->outer_shell));

        return solid;
    }

    // Create a cylinder solid
    static std::unique_ptr<Solid> createCylinder(
        Point3D center, Vector3D axis, double radius, double height, int segments = 32)
    {
        auto solid = std::make_unique<Solid>();
        solid->name = "Cylinder";

        std::vector<std::unique_ptr<Face>> faces;

        // Side surface
        faces.push_back(FaceBuilder::createCylindricalFace(center, axis, radius, 0, 2*M_PI, height));

        // Top cap
        Vector3D ax = Vector3D(axis.x, axis.y, axis.z).normalized();
        Point3D topCenter = {
            center.x + height * ax.x,
            center.y + height * ax.y,
            center.z + height * ax.z
        };
        // Approximate circular cap with triangular fan
        std::vector<Point3D> cap_points;
        cap_points.push_back(topCenter);
        for (int i = 0; i <= segments; ++i) {
            double angle = 2.0 * M_PI * i / segments;
            cap_points.push_back(sampleCirclePoint(topCenter, ax, radius, angle));
        }
        faces.push_back(FaceBuilder::createPlanarFace(cap_points));

        // Bottom cap
        Point3D botCenter = center;
        std::vector<Point3D> bot_points;
        bot_points.push_back(botCenter);
        for (int i = 0; i <= segments; ++i) {
            double angle = 2.0 * M_PI * i / segments;
            bot_points.push_back(sampleCirclePoint(botCenter, ax, radius, angle));
        }
        faces.push_back(FaceBuilder::createPlanarFace(bot_points));

        solid->outer_shell = ShellBuilder::createWatertightShell(std::move(faces));
        solid->shells.push_back(std::move(solid->outer_shell));

        return solid;
    }

    // Create a sphere solid
    static std::unique_ptr<Solid> createSphere(Point3D center, double radius,
                                                int phi_seg = 16, int theta_seg = 16)
    {
        auto solid = std::make_unique<Solid>();
        solid->name = "Sphere";

        std::vector<std::unique_ptr<Face>> faces;

        // Approximate sphere with planar triangular patches
        for (int i = 0; i < phi_seg; ++i) {
            double phi1 = M_PI * i / phi_seg;
            double phi2 = M_PI * (i + 1) / phi_seg;

            for (int j = 0; j < theta_seg; ++j) {
                double theta1 = 2.0 * M_PI * j / theta_seg;
                double theta2 = 2.0 * M_PI * (j + 1) / theta_seg;

                Point3D corners[4] = {
                    sampleSpherePoint(center, radius, phi1, theta1),
                    sampleSpherePoint(center, radius, phi2, theta1),
                    sampleSpherePoint(center, radius, phi2, theta2),
                    sampleSpherePoint(center, radius, phi1, theta2)
                };

                // Two triangles per quad
                faces.push_back(FaceBuilder::createPlanarFace({corners[0], corners[1], corners[2]}));
                faces.push_back(FaceBuilder::createPlanarFace({corners[0], corners[2], corners[3]}));
            }
        }

        solid->outer_shell = ShellBuilder::createWatertightShell(std::move(faces));
        solid->shells.push_back(std::move(solid->outer_shell));

        return solid;
    }

    // Create a torus solid
    static std::unique_ptr<Solid> createTorus(
        Point3D center, Vector3D axis, double majorR, double minorR,
        int theta_seg = 24, int phi_seg = 16)
    {
        auto solid = std::make_unique<Solid>();
        solid->name = "Torus";

        std::vector<std::unique_ptr<Face>> faces;

        for (int i = 0; i < theta_seg; ++i) {
            double t1 = 2.0 * M_PI * i / theta_seg;
            double t2 = 2.0 * M_PI * (i + 1) / theta_seg;

            for (int j = 0; j < phi_seg; ++j) {
                double p1 = 2.0 * M_PI * j / phi_seg;
                double p2 = 2.0 * M_PI * (j + 1) / phi_seg;

                Point3D corners[4] = {
                    sampleTorusPoint(center, axis, majorR, minorR, t1, p1),
                    sampleTorusPoint(center, axis, majorR, minorR, t2, p1),
                    sampleTorusPoint(center, axis, majorR, minorR, t2, p2),
                    sampleTorusPoint(center, axis, majorR, minorR, t1, p2)
                };

                faces.push_back(FaceBuilder::createPlanarFace({corners[0], corners[1], corners[2]}));
                faces.push_back(FaceBuilder::createPlanarFace({corners[0], corners[2], corners[3]}));
            }
        }

        solid->outer_shell = ShellBuilder::createWatertightShell(std::move(faces));
        solid->shells.push_back(std::move(solid->outer_shell));

        return solid;
    }

    // Create a prism solid from a polygon base
    static std::unique_ptr<Solid> createPrism(
        const std::vector<Point3D>& base, double height, Vector3D extrusionDir = {0,0,1})
    {
        auto solid = std::make_unique<Solid>();
        solid->name = "Prism";

        std::vector<std::unique_ptr<Face>> faces;

        // Side faces
        for (size_t i = 0; i < base.size(); ++i) {
            size_t next = (i + 1) % base.size();
            std::vector<Point3D> side = {
                base[i],
                base[next],
                {base[next].x + height*extrusionDir.x,
                 base[next].y + height*extrusionDir.y,
                 base[next].z + height*extrusionDir.z},
                {base[i].x + height*extrusionDir.x,
                 base[i].y + height*extrusionDir.y,
                 base[i].z + height*extrusionDir.z}
            };
            faces.push_back(FaceBuilder::createPlanarFace(side));
        }

        // Bottom face
        faces.push_back(FaceBuilder::createPlanarFace(base));

        // Top face
        std::vector<Point3D> top;
        for (const auto& p : base) {
            top.push_back({
                p.x + height*extrusionDir.x,
                p.y + height*extrusionDir.y,
                p.z + height*extrusionDir.z
            });
        }
        faces.push_back(FaceBuilder::createPlanarFace(top));

        solid->outer_shell = ShellBuilder::createWatertightShell(std::move(faces));
        solid->shells.push_back(std::move(solid->outer_shell));

        return solid;
    }

private:
    static Point3D sampleCirclePoint(Point3D center, Vector3D axis, double radius, double angle) {
        Vector3D ax = Vector3D(axis.x, axis.y, axis.z).normalized();
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
            center.x + radius * std::cos(angle) * u.x + radius * std::sin(angle) * v.x,
            center.y + radius * std::cos(angle) * u.y + radius * std::sin(angle) * v.y,
            center.z + radius * std::cos(angle) * u.z + radius * std::sin(angle) * v.z
        };
    }

    static Point3D sampleSpherePoint(Point3D center, double radius,
                                      double phi, double theta) {
        return {
            center.x + radius * std::sin(phi) * std::cos(theta),
            center.y + radius * std::sin(phi) * std::sin(theta),
            center.z + radius * std::cos(phi)
        };
    }

    static Point3D sampleTorusPoint(Point3D center, Vector3D axis,
                                     double R, double r,
                                     double theta, double phi) {
        Vector3D ax = Vector3D(axis.x, axis.y, axis.z).normalized();
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
            center.x + (R + r * std::cos(phi)) * std::cos(theta) * u.x
                      + r * std::sin(phi) * v.x,
            center.y + (R + r * std::cos(phi)) * std::cos(theta) * u.y
                      + r * std::sin(phi) * v.y,
            center.z + (R + r * std::cos(phi)) * std::cos(theta) * u.z
                      + r * std::sin(phi) * v.z
        };
    }
};
