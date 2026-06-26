# API Reference: Physics Simulation Engine

## Vec2

### Constructor
```cpp
Vec2();
Vec2(double x, double y);
```

### Static Methods
```cpp
static Vec2 zero();
static Vec2 unit_x();
static Vec2 unit_y();
```

### Operators
```cpp
Vec2 operator+(const Vec2& other) const;
Vec2 operator-(const Vec2& other) const;
Vec2 operator*(double scalar) const;
Vec2 operator/(double scalar) const;
Vec2 operator-() const;
```

### Methods
```cpp
double dot(const Vec2& other) const;
double cross(const Vec2& other) const;
double length() const;
double length_squared() const;
Vec2 normalized() const;
```

## AABB

### Constructor
```cpp
AABB();
AABB(const Vec2& min, const Vec2& max);
AABB(double min_x, double_min_y, double max_x, double max_y);
```

### Methods
```cpp
Vec2 center() const;
Vec2 size() const;
Vec2 half_size() const;
double area() const;
bool contains(const Vec2& point) const;
bool intersects(const AABB& other) const;
AABB merge(const AABB& other) const;
AABB expanded(double amount) const;
bool is_valid() const;
```

## RigidBody

### Body Types
```cpp
enum class BodyType {
    Static,     // Immovable, no physics
    Dynamic,    // Full physics simulation
    Kinematic   // Movable by velocity, no forces
};
```

### RigidBodyDef
```cpp
struct RigidBodyDef {
    BodyType type = BodyType::Dynamic;
    Vec2 position = {0.0, 0.0};
    double rotation = 0.0;
    Vec2 velocity = {0.0, 0.0};
    double angular_velocity = 0.0;
    double mass = 1.0;
    double radius = 0.5;
    double restitution = 0.5;
    double friction = 0.3;
    double linear_damping = 0.01;
    double angular_damping = 0.01;
    bool is_sensor = false;
    void* user_data = nullptr;
    std::string name = "";
};
```

### Methods
```cpp
uint32_t id() const;
const std::string& name() const;
void set_name(const std::string& name);
BodyType type() const;
const Vec2& position() const;
double rotation() const;
const Vec2& velocity() const;
double angular_velocity() const;
double mass() const;
double inv_mass() const;
double inertia() const;
double inv_inertia() const;
double radius() const;
double restitution() const;
double friction() const;
bool is_sensor() const;
bool is_static() const;
bool is_dynamic() const;
bool is_kinematic() const;
void* user_data() const;
void set_user_data(void* data);

void set_position(const Vec2& pos);
void set_rotation(double rot);
void set_velocity(const Vec2& vel);
void set_angular_velocity(double ang_vel);
void set_mass(double mass);
void set_restitution(double r);
void set_friction(double f);
void set_radius(double r);

void apply_force(const Vec2& force);
void apply_force_at_point(const Vec2& force, const Vec2& point);
void apply_impulse(const Vec2& impulse);
void apply_impulse_at_point(const Vec2& impulse, const Vec2& point);
void apply_torque(double torque);
void clear_forces();
void integrate(double dt);
AABB compute_aabb() const;
Vec2 velocity_at_point(const Vec2& point) const;
```

## Collision Functions

```cpp
CollisionResult aabb_vs_aabb(const AABB& a, const AABB& b);
CollisionResult circle_vs_circle(const Vec2& center_a, double radius_a,
                                  const Vec2& center_b, double radius_b);
CollisionResult aabb_vs_circle(const AABB& aabb, const Vec2& circle_center,
                                double circle_radius);
CollisionResult detect_collision(const RigidBody& a, const RigidBody& b);
```

## World

### WorldConfig
```cpp
struct WorldConfig {
    Vec2 gravity = {0.0, -9.81};
    int velocity_iterations = 8;
    int position_iterations = 3;
    double time_step = 1.0 / 60.0;
    bool allow_sleep = true;
    double sleep_linear_threshold = 0.01;
    double sleep_angular_threshold = 0.01;
};
```

### Methods
```cpp
World(const WorldConfig& config = WorldConfig{});
std::shared_ptr<RigidBody> create_body(const RigidBodyDef& def);
void destroy_body(std::shared_ptr<RigidBody> body);
std::shared_ptr<DistanceConstraint> create_distance_constraint(...);
std::shared_ptr<PinConstraint> create_pin_constraint(...);
std::shared_ptr<HingeConstraint> create_hinge_constraint(...);
std::shared_ptr<WeldConstraint> create_weld_constraint(...);
void destroy_constraint(std::shared_ptr<Constraint> constraint);
void set_collision_callback(CollisionCallback callback);
void step(double dt = -1.0);
const std::vector<std::shared_ptr<RigidBody>>& bodies() const;
size_t body_count() const;
const WorldConfig& config() const;
void set_config(const WorldConfig& config);
void clear();
ConstraintSolver& solver();
```

## Constraints

### DistanceConstraint
```cpp
DistanceConstraint(std::shared_ptr<RigidBody> a,
                   std::shared_ptr<RigidBody> b,
                   const Vec2& anchor_a = {0.0, 0.0},
                   const Vec2& anchor_b = {0.0, 0.0},
                   double distance = -1.0);
```

### PinConstraint
```cpp
PinConstraint(std::shared_ptr<RigidBody> body,
              const Vec2& world_point,
              const Vec2& local_anchor = {0.0, 0.0});
```

### HingeConstraint
```cpp
HingeConstraint(std::shared_ptr<RigidBody> a,
                std::shared_ptr<RigidBody> b,
                const Vec2& anchor_a = {0.0, 0.0},
                const Vec2& anchor_b = {0.0, 0.0});
```

### WeldConstraint
```cpp
WeldConstraint(std::shared_ptr<RigidBody> a,
               std::shared_ptr<RigidBody> b,
               const Vec2& anchor_a = {0.0, 0.0},
               const Vec2& anchor_b = {0.0, 0.0});
```
