"""Physics simulation demo with various objects."""

import pygame
import sys
import math
import random
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src import (
    Vector2D, RigidBody, CircleCollider, AABBCollider, PolygonCollider,
    PhysicsWorld, VerletIntegrator, SpringConstraint, DistanceConstraint
)


# Initialize pygame
pygame.init()

# Screen settings
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Physics Engine Demo")

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 50, 50)
BLUE = (50, 50, 255)
GREEN = (50, 255, 50)
YELLOW = (255, 255, 50)
PURPLE = (150, 50, 255)
ORANGE = (255, 150, 50)
GRAY = (100, 100, 100)


class PhysicsDemo:
    """Physics simulation demo."""

    def __init__(self):
        self.world = PhysicsWorld(integrator=VerletIntegrator())
        self.world.gravity = Vector2D(0, 300)
        self.objects = []  # List of (body, collider, color)
        self.springs = []  # Spring visualization

        self._create_boundaries()
        self._create_demo_objects()

    def _create_boundaries(self) -> None:
        """Create world boundaries."""
        wall_thickness = 30

        # Floor
        floor = RigidBody(Vector2D(WIDTH / 2, HEIGHT - wall_thickness / 2), is_static=True)
        self.world.add_body(floor, AABBCollider(floor, WIDTH, wall_thickness))
        self.objects.append((floor, None, GRAY))

        # Left wall
        left = RigidBody(Vector2D(wall_thickness / 2, HEIGHT / 2), is_static=True)
        self.world.add_body(left, AABBCollider(left, wall_thickness, HEIGHT))
        self.objects.append((left, None, GRAY))

        # Right wall
        right = RigidBody(Vector2D(WIDTH - wall_thickness / 2, HEIGHT / 2), is_static=True)
        self.world.add_body(right, AABBCollider(right, wall_thickness, HEIGHT))
        self.objects.append((right, None, GRAY))

        # Ceiling
        ceiling = RigidBody(Vector2D(WIDTH / 2, wall_thickness / 2), is_static=True)
        self.world.add_body(ceiling, AABBCollider(ceiling, WIDTH, wall_thickness))
        self.objects.append((ceiling, None, GRAY))

    def _create_demo_objects(self) -> None:
        """Create various physics objects for demonstration."""
        # 1. Bouncing balls with different masses
        balls = [
            (100, 100, 20, 1.0, RED),
            (200, 80, 30, 2.0, BLUE),
            (300, 60, 15, 0.5, GREEN),
        ]

        for x, y, radius, mass, color in balls:
            body = RigidBody(Vector2D(x, y), mass=mass)
            body.restitution = 0.8
            collider = CircleCollider(body, radius)
            self.world.add_body(body, collider)
            self.objects.append((body, collider, color))

        # 2. Stacked boxes
        box_size = 40
        for i in range(4):
            x = 500 + i * 10
            y = HEIGHT - 60 - i * (box_size + 2)
            body = RigidBody(Vector2D(x, y), mass=1.0)
            body.friction = 0.5
            collider = AABBCollider(body, box_size, box_size)
            self.world.add_body(body, collider)
            self.objects.append((body, collider, ORANGE))

        # 3. Spring-connected balls
        spring_ball1 = RigidBody(Vector2D(650, 200), mass=1.0)
        spring_ball2 = RigidBody(Vector2D(700, 250), mass=1.0)

        collider1 = CircleCollider(spring_ball1, 15)
        collider2 = CircleCollider(spring_ball2, 15)

        self.world.add_body(spring_ball1, collider1)
        self.world.add_body(spring_ball2, collider2)

        self.objects.append((spring_ball1, collider1, PURPLE))
        self.objects.append((spring_ball2, collider2, PURPLE))

        # Create spring constraint
        spring = SpringConstraint(spring_ball1, spring_ball2, stiffness=30.0, damping=2.0)
        self.world.add_constraint(spring)
        self.springs.append((spring_ball1, spring_ball2, spring))

        # 4. Chain of connected balls
        chain_balls = []
        prev_ball = None
        for i in range(5):
            x = 150 + i * 30
            y = 300
            ball = RigidBody(Vector2D(x, y), mass=0.5)
            collider = CircleCollider(ball, 10)
            self.world.add_body(ball, collider)
            self.objects.append((ball, collider, YELLOW))
            chain_balls.append(ball)

            if prev_ball:
                constraint = DistanceConstraint(prev_ball, ball, stiffness=0.8)
                self.world.add_constraint(constraint)

            prev_ball = ball

        # Pin first ball of chain
        chain_balls[0].is_static = True

        # 5. Polygon (triangle)
        triangle_body = RigidBody(Vector2D(400, 150), mass=2.0)
        triangle_collider = PolygonCollider(
            triangle_body,
            [Vector2D(0, -30), Vector2D(25, 20), Vector2D(-25, 20)]
        )
        self.world.add_body(triangle_body, triangle_collider)
        self.objects.append((triangle_body, triangle_collider, GREEN))

    def add_random_object(self, pos: Vector2D) -> None:
        """Add a random physics object at given position."""
        choice = random.choice(['circle', 'box', 'triangle'])

        if choice == 'circle':
            radius = random.randint(10, 30)
            mass = radius / 10
            body = RigidBody(pos, mass=mass)
            body.restitution = 0.7
            collider = CircleCollider(body, radius)
            color = (random.randint(100, 255), random.randint(100, 255), random.randint(100, 255))
        elif choice == 'box':
            size = random.randint(20, 50)
            mass = size / 20
            body = RigidBody(pos, mass=mass)
            body.friction = 0.4
            collider = AABBCollider(body, size, size)
            color = (random.randint(100, 255), random.randint(100, 255), random.randint(100, 255))
        else:
            size = random.randint(15, 35)
            mass = 1.0
            body = RigidBody(pos, mass=mass)
            collider = PolygonCollider(
                body,
                [Vector2D(0, -size), Vector2D(size * 0.866, size * 0.5),
                 Vector2D(-size * 0.866, size * 0.5)]
            )
            color = (random.randint(100, 255), random.randint(100, 255), random.randint(100, 255))

        self.world.add_body(body, collider)
        self.objects.append((body, collider, color))

    def update(self, dt: float) -> None:
        """Update simulation."""
        self.world.step(dt)

        # Remove objects that fall off screen
        to_remove = []
        for body, collider, color in self.objects:
            if not body.is_static and body.position.y > HEIGHT + 100:
                to_remove.append((body, collider, color))

        for item in to_remove:
            self.objects.remove(item)
            self.world.remove_body(item[0])

    def render(self) -> None:
        """Render the simulation."""
        screen.fill(BLACK)

        # Draw all objects
        for body, collider, color in self.objects:
            if isinstance(collider, CircleCollider):
                pos = (int(body.position.x), int(body.position.y))
                radius = int(collider.radius)
                pygame.draw.circle(screen, color, pos, radius)
                # Draw velocity indicator
                end_pos = (
                    int(body.position.x + body.velocity.x * 0.05),
                    int(body.position.y + body.velocity.y * 0.05)
                )
                pygame.draw.line(screen, WHITE, pos, end_pos, 2)

            elif isinstance(collider, AABBCollider):
                x = int(body.position.x - collider.half_width)
                y = int(body.position.y - collider.half_height)
                w = int(collider.width)
                h = int(collider.height)
                pygame.draw.rect(screen, color, (x, y, w, h))

            elif isinstance(collider, PolygonCollider):
                vertices = collider.get_world_vertices()
                points = [(int(v.x), int(v.y)) for v in vertices]
                if len(points) >= 3:
                    pygame.draw.polygon(screen, color, points)

        # Draw springs
        for body_a, body_b, spring in self.springs:
            start = (int(body_a.position.x), int(body_a.position.y))
            end = (int(body_b.position.x), int(body_b.position.y))
            pygame.draw.line(screen, PURPLE, start, end, 2)

        # Draw UI
        font = pygame.font.Font(None, 24)
        fps_text = font.render(f"FPS: {int(pygame.time.get_ticks())}", True, WHITE)
        obj_text = font.render(f"Objects: {len(self.objects)}", True, WHITE)
        help_text = font.render("Click to add objects | R to reset | ESC to quit", True, WHITE)

        screen.blit(fps_text, (10, 10))
        screen.blit(obj_text, (10, 35))
        screen.blit(help_text, (10, HEIGHT - 30))

        pygame.display.flip()

    def reset(self) -> None:
        """Reset the simulation."""
        self.world.clear()
        self.objects.clear()
        self.springs.clear()
        self._create_boundaries()
        self._create_demo_objects()

    def run(self) -> None:
        """Main simulation loop."""
        clock = pygame.time.Clock()
        running = True

        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                    elif event.key == pygame.K_r:
                        self.reset()
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    mouse_pos = Vector2D(*event.pos)
                    self.add_random_object(mouse_pos)

            self.update(1 / 60)
            self.render()
            clock.tick(60)

        pygame.quit()


if __name__ == "__main__":
    demo = PhysicsDemo()
    demo.run()
