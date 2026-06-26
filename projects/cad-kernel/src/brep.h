// ============================================================
// cad-kernel: CAD Kernel Basics Learning Project
// B-rep (Boundary Representation) Data Structure
//
// B-rep is the standard way to represent 3D solids in CAD.
// It defines a solid by its bounding surfaces (faces), which
// are bounded by edges, which are bounded by vertices.
//
// Hierarchy: Vertex -> Edge -> Face -> Shell -> Solid
// ============================================================

#pragma once
#include <vector>
#include <memory>
#include <string>
#include <unordered_map>
#include <unordered_set>
#include <functional>
#include <cmath>
#include <iostream>
#include <algorithm>
#include <cassert>
#include <limits>
#include <sstream>

// ============================================================
// Tolerance for geometric comparisons
// ============================================================
constexpr double EPSILON = 1e-9;

// ============================================================
// Utility: comparison with tolerance
// ============================================================
inline bool approx_equal(double a, double b) {
    return std::fabs(a - b) < EPSILON;
}

inline bool approx_zero(double x) {
    return std::fabs(x) < EPSILON;
}

inline double clamp(double v, double lo, double hi) {
    return v < lo ? lo : (v > hi ? hi : v);
}

// ============================================================
// Unique ID generator for topological entities
// ============================================================
class IdGenerator {
public:
    static IdGenerator& instance() {
        static IdGenerator gen;
        return gen;
    }
    unsigned int next() { return ++counter_; }
private:
    IdGenerator() : counter_(0) {}
    unsigned int counter_ = 0;
};

// ============================================================
// Forward declarations
// ============================================================
class Vertex;
class Edge;
class Face;
class Shell;
class Solid;
class HalfEdge;

// ============================================================
// Geometric primitives
// ============================================================
struct Point3D {
    double x = 0.0, y = 0.0, z = 0.0;

    Point3D() = default;
    Point3D(double x, double y, double z) : x(x), y(y), z(z) {}

    Point3D operator+(const Point3D& o) const { return {x+o.x, y+o.y, z+o.z}; }
    Point3D operator-(const Point3D& o) const { return {x-o.x, y-o.y, z-o.z}; }
    Point3D operator*(double s) const { return {x*s, y*s, z*s}; }

    double length() const { return std::sqrt(x*x + y*y + z*z); }
    Point3D normalized() const {
        double l = length();
        if (approx_zero(l)) return {0, 0, 0};
        return {x/l, y/l, z/l};
    }

    bool operator==(const Point3D& o) const {
        return approx_equal(x,o.x) && approx_equal(y,o.y) && approx_equal(z,o.z);
    }
};

inline double dot(Point3D a, Point3D b) {
    return a.x*b.x + a.y*b.y + a.z*b.z;
}

inline Point3D cross(Point3D a, Point3D b) {
    return {a.y*b.z - a.z*b.y, a.z*b.x - a.x*b.z, a.x*b.y - a.y*b.x};
}

inline Point3D lerp(Point3D a, Point3D b, double t) {
    return {a.x + (b.x-a.x)*t, a.y + (b.y-a.y)*t, a.z + (b.z-a.z)*t};
}

// ============================================================
// Vector3D (direction)
// ============================================================
struct Vector3D {
    double x = 0.0, y = 0.0, z = 0.0;
    Vector3D() = default;
    Vector3D(double x, double y, double z) : x(x), y(y), z(z) {}
    double length() const { return std::sqrt(x*x + y*y + z*z); }
    Vector3D normalized() const {
        double l = length();
        return approx_zero(l) ? Vector3D(0,0,0) : Vector3D(x/l, y/l, z/l);
    }
};

// ============================================================
// BRep Entity Types
// ============================================================
enum class EntityType {
    VERTEX,
    EDGE,
    FACE,
    SHELL,
    SOLID,
    HALFEDGE
};

// ============================================================
// Geometric types for edges and faces
// ============================================================
enum class CurveType {
    LINE,
    CIRCLE,
    ELLIPSE,
    SPLINE,
    NURBS
};

enum class SurfaceType {
    PLANE,
    CYLINDER,
    SPHERE,
    TORUS,
    CONE,
    NURBS_SURFACE
};

// ============================================================
// Topological validity status
// ============================================================
enum class TopoStatus {
    VALID,
    INVALID,
    INCOMPLETE
};

// ============================================================
// HalfEdge: connects vertices and edges in a face loop
// ============================================================
class HalfEdge {
public:
    unsigned int id = 0;
    Vertex* vertex = nullptr;       // origin vertex
    HalfEdge* twin = nullptr;       // opposite half-edge on adjacent face
    HalfEdge* next = nullptr;       // next half-edge in loop
    HalfEdge* prev = nullptr;       // previous half-edge in loop
    Edge* edge = nullptr;           // owning edge
    Face* face = nullptr;           // owning face

    // Parameter position on the edge (u)
    double u_start = 0.0;
    double u_end = 1.0;

    HalfEdge() { id = IdGenerator::instance().next(); }

    // Get the point at parameter u on this half-edge's curve
    Point3D pointAt(double u) const;
    double length() const;
};

// ============================================================
// Vertex: a point in 3D space
// ============================================================
class Vertex {
public:
    unsigned int id = 0;
    Point3D point;
    EntityType type = EntityType::VERTEX;

    Vertex() { id = IdGenerator::instance().next(); }
    Vertex(double x, double y, double z) : id(IdGenerator::instance().next()), point(x, y, z) {}
    Vertex(const Point3D& p) : id(IdGenerator::instance().next()), point(p) {}

    std::string toString() const {
        return "Vertex(" + std::to_string(point.x) + "," +
               std::to_string(point.y) + "," +
               std::to_string(point.z) + ")";
    }
};

// ============================================================
// Edge: a curve connecting two vertices
// ============================================================
class Edge {
public:
    unsigned int id = 0;
    EntityType type = EntityType::EDGE;
    Point3D start, end;
    CurveType curve_type = CurveType::LINE;

    // Geometric data for the curve
    double radius = 0.0;      // for circles
    Point3D center;             // for circles/spheres
    Vector3D direction;         // for lines/cylinders
    double startParam = 0.0;
    double endParam = 1.0;

    // Topological connectivity
    std::vector<HalfEdge*> half_edges;
    std::vector<Face*> adjacent_faces;

    Edge() { id = IdGenerator::instance().next(); }
    Edge(Point3D s, Point3D e) : id(IdGenerator::instance().next()), start(s), end(e) {}

    double length() const {
        double dx = end.x - start.x;
        double dy = end.y - start.y;
        double dz = end.z - start.z;
        return std::sqrt(dx*dx + dy*dy + dz*dz);
    }

    std::string toString() const {
        return "Edge(" + std::to_string(start.x) + "," +
               std::to_string(start.y) + "," + std::to_string(start.z) +
               " -> " + std::to_string(end.x) + "," +
               std::to_string(end.y) + "," + std::to_string(end.z) + ")";
    }
};

// ============================================================
// Face: a bounded surface patch
// ============================================================
class Face {
public:
    unsigned int id = 0;
    EntityType type = EntityType::FACE;
    SurfaceType surface_type = SurfaceType::PLANE;

    // Geometric data for the surface
    Point3D origin;       // surface origin point
    Vector3D normal;      // surface normal
    double radius1 = 0.0; // primary radius (sphere, cylinder)
    double radius2 = 0.0; // secondary radius (torus)
    Vector3D axis;         // axis direction for revolution surfaces
    Point3D center;       // center point for sphere/cylinder

    // Topological boundary: loop of half-edges
    std::vector<HalfEdge*> outer_loop;
    std::vector<std::vector<HalfEdge*>> inner_loops; // holes

    // Connected topological entities
    std::vector<std::unique_ptr<Vertex>> vertices;
    std::vector<std::unique_ptr<Edge>> edges;
    std::vector<std::unique_ptr<Face>> sub_faces;

    // Surface parameter bounds
    double u_min = 0.0, u_max = 1.0;
    double v_min = 0.0, v_max = 1.0;
    double height = 0.0;
    double area = 0.0;

    Solid* solid = nullptr; // owning solid (for orientation)
    Shell* shell = nullptr; // owning shell

    Face() { id = IdGenerator::instance().next(); }

    // Compute surface normal
    Vector3D getNormal() const {
        if (approx_zero(normal.x) && approx_zero(normal.y) && approx_zero(normal.z)) {
            return Vector3D(0, 0, 1); // default Z-up
        }
        return normal.normalized();
    }

    // Check if face is oriented correctly (normal points outward)
    bool isOriented() const { return solid != nullptr; }

    // Compute approximate area of this face
    double computeArea() const;

    std::string toString() const {
        return "Face(type=" + std::to_string(static_cast<int>(surface_type)) + ")";
    }
};

// ============================================================
// Shell: a closed set of connected faces
// ============================================================
class Shell {
public:
    unsigned int id = 0;
    EntityType type = EntityType::SHELL;
    std::vector<Face*> faces;

    Shell() { id = IdGenerator::instance().next(); }

    // Check if shell is watertight (no boundary edges)
    bool isWatertight() const;

    // Compute surface area
    double computeArea() const;

    std::string toString() const {
        return "Shell(faces=" + std::to_string(faces.size()) + ")";
    }
};

// ============================================================
// Solid: a 3D volume bounded by shells
// ============================================================
class Solid {
public:
    unsigned int id = 0;
    EntityType type = EntityType::SOLID;
    std::string name;

    // Outer boundary shell
    std::unique_ptr<Shell> outer_shell;

    // Inner shells (holes, cavities)
    std::vector<std::unique_ptr<Shell>> inner_shells;

    // All vertices, edges, faces in this solid (for iteration)
    std::vector<std::unique_ptr<Vertex>> vertices;
    std::vector<std::unique_ptr<Edge>> edges;
    std::vector<std::unique_ptr<Face>> faces;
    std::vector<std::unique_ptr<Shell>> shells;

    Solid() { id = IdGenerator::instance().next(); }

    // Compute volume using divergence theorem (sum over faces)
    double computeVolume() const {
        double vol = 0.0;
        for (auto& face : faces) {
            if (!face || face->vertices.empty()) continue;
            // Simple volume estimation: sum of tetrahedra from origin
            for (size_t i = 1; i + 1 < face->vertices.size(); ++i) {
                Point3D a = face->vertices[i]->point;
                Point3D b = face->vertices[i+1]->point;
                Vector3D na(face->normal.x, face->normal.y, face->normal.z);
                na = na.normalized();
                double h = (a.x+a.y+a.z) / 3.0 * na.x; // simplified height
                // Simplified: use centroid distance
                Point3D centroid;
                centroid.x = (a.x + b.x + face->vertices[i]->point.x) / 3.0;
                centroid.y = (a.y + b.y + face->vertices[i]->point.y) / 3.0;
                centroid.z = (a.z + b.z + face->vertices[i]->point.z) / 3.0;
                double dist = centroid.x*na.x + centroid.y*na.y + centroid.z*na.z;
                // Triangle area
                Vector3D e1(b.x-a.x, b.y-a.y, b.z-a.z);
                Vector3D e2(face->vertices[i]->point.x-a.x, face->vertices[i]->point.y-a.y, face->vertices[i]->point.z-a.z);
                Vector3D cross_prod = Vector3D(e1.y*e2.z-e1.z*e2.y, e1.z*e2.x-e1.x*e2.z, e1.x*e2.y-e1.y*e2.x);
                double area = 0.5 * std::sqrt(cross_prod.x*cross_prod.x + cross_prod.y*cross_prod.y + cross_prod.z*cross_prod.z);
                vol += area * dist / 3.0;
            }
        }
        return std::fabs(vol);
    }

    // Compute surface area
    double computeSurfaceArea() const {
        double area = 0.0;
        for (auto& face : faces) {
            if (!face || face->vertices.empty()) continue;
            for (size_t i = 1; i + 1 < face->vertices.size(); ++i) {
                Point3D a = face->vertices[i]->point;
                Point3D b = face->vertices[i+1]->point;
                Vector3D e1(b.x-a.x, b.y-a.y, b.z-a.z);
                Vector3D e2(face->vertices[i]->point.x-a.x, face->vertices[i]->point.y-a.y, face->vertices[i]->point.z-a.z);
                Vector3D cross_prod = Vector3D(e1.y*e2.z-e1.z*e2.y, e1.z*e2.x-e1.x*e2.z, e1.x*e2.y-e1.y*e2.x);
                area += 0.5 * std::sqrt(cross_prod.x*cross_prod.x + cross_prod.y*cross_prod.y + cross_prod.z*cross_prod.z);
            }
        }
        return area;
    }

    // Count topological entities
    int vertexCount() const { return static_cast<int>(vertices.size()); }
    int edgeCount() const { return static_cast<int>(edges.size()); }
    int faceCount() const { return static_cast<int>(faces.size()); }
    int shellCount() const { return static_cast<int>(shells.size()); }

    // Euler characteristic check: V - E + F = 2 for solid
    bool checkEuler() const;

    // Validate topological consistency
    TopoStatus validate() const {
        if (!outer_shell) return TopoStatus::INVALID;
        if (outer_shell->faces.empty()) return TopoStatus::INCOMPLETE;
        return TopoStatus::VALID;
    }

    std::string toString() const {
        return "Solid(name=" + name + ", V=" + std::to_string(vertexCount()) +
               ", E=" + std::to_string(edgeCount()) +
               ", F=" + std::to_string(faceCount()) + ")";
    }
};

// ============================================================
// BRep: the top-level container for a boundary representation
// ============================================================
class BRep {
public:
    std::string name;
    std::vector<std::unique_ptr<Solid>> solids;

    BRep() = default;
    explicit BRep(const std::string& n) : name(n) {}

    // Add a solid to this B-rep
    void addSolid(std::unique_ptr<Solid> solid) {
        solids.push_back(std::move(solid));
    }

    // Get all vertices across all solids
    std::vector<Vertex*> allVertices() const {
        std::vector<Vertex*> result;
        for (auto& s : solids)
            for (auto& v : s->vertices) result.push_back(v.get());
        return result;
    }

    // Get all edges across all solids
    std::vector<Edge*> allEdges() const {
        std::vector<Edge*> result;
        for (auto& s : solids)
            for (auto& e : s->edges) result.push_back(e.get());
        return result;
    }

    // Get all faces across all solids
    std::vector<Face*> allFaces() const {
        std::vector<Face*> result;
        for (auto& s : solids)
            for (auto& f : s->faces) result.push_back(f.get());
        return result;
    }

    std::string toString() const {
        return "BRep(name=" + name + ", solids=" + std::to_string(solids.size()) + ")";
    }
};

// ============================================================
// Implementation of HalfEdge methods
// ============================================================
inline Point3D HalfEdge::pointAt(double u) const {
    if (!edge) return {0, 0, 0};
    // Linear interpolation along the edge curve
    return lerp(edge->start, edge->end, (u - edge->startParam) /
        (edge->endParam - edge->startParam + EPSILON));
}

inline double HalfEdge::length() const {
    if (!edge) return 0.0;
    return edge->length();
}
