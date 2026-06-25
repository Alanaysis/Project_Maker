"""Pinball game example using the physics engine."""

import pygame
import sys
import math
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src import (
    Vector2D, RigidBody, CircleCollider, AABBCollider,
    PhysicsWorld, VerletIntegrator
)


# Initialize pygame
pygame.init()

# Screen settings
WIDTH, HEIGHT = 400, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Physics Pinball")

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 50, 50)
BLUE = (50, 50, 255)
GREEN = (50, 255, 50)
YELLOW = (255, 255, 50)
GRAY = (100, 100, 100)
DARK_GRAY = (50, 50, 50)


class PinballGame:
    """Simple pinball game."""

    def __init__(self):
        self.world = PhysicsWorld(integrator=VerletIntegrator())
        self.world.gravity = Vector2D(0, 500)  # Stronger gravity for pinball feel
        self.score = 0
        self.ball = None
        self.flipper_left = None
        self.flipper_right = None

        self._create_walls()
        self._create_bumpers()
        self._create_flippers()
        self._launch_ball()

    def _create_walls(self) -> None:
        """Create game boundaries."""
        wall_thickness = 20

        # Left wall
        left = RigidBody(Vector2D(wall_thickness / 2, HEIGHT / 2), is_static=True)
        self.world.add_body(left, AABBCollider(left, wall_thickness, HEIGHT))

        # Right wall
        right = RigidBody(Vector2D(WIDTH - wall_thickness / 2, HEIGHT / 2), is_static=True)
        self.world.add_body(right, AABBCollider(right, wall_thickness, HEIGHT))

        # Top wall
        top = RigidBody(Vector2D(WIDTH / 2, wall_thickness / 2), is_static=True)
        self.world.add_body(top, AABBCollider(top, WIDTH, wall_thickness))

        # Bottom (drain)
        bottom = RigidBody(Vector2D(WIDTH / 2, HEIGHT + 50), is_static=True)
        self.world.add_body(bottom, AABBCollider(bottom, WIDTH + 100, 20))

    def _create_bumpers(self) -> None:
        """Create bumpers that give points."""
        bumper_positions = [
            (100, 150, 25),
            (200, 120, 25),
            (300, 150, 25),
            (150, 250, 20),
            (250, 250, 20),
            (200, 320, 30),
        ]

        self.bumpers = []
        for x, y, radius in bumper_positions:
            bumper = RigidBody(Vector2D(x, y), is_static=True)
            bumper.restitution = 1.5  # Extra bouncy
            collider = CircleCollider(bumper, radius)
            self.world.add_body(bumper, collider)
            self.bumpers.append(bumper)

    def _create_flippers(self) -> None:
        """Create left and right flippers."""
        # Left flipper
        self.flipper_left = RigidBody(Vector2D(130, 520), is_static=True)
        flipper_collider = AABBCollider(self.flipper_left, 80, 15)
        self.world.add_body(self.flipper_left, flipper_collider)

        # Right flipper
        self.flipper_right = RigidBody(Vector2D(270, 520), is_static=True)
        flipper_collider = AABBCollider(self.flipper_right, 80, 15)
        self.world.add_body(self.flipper_right, flipper_collider)

    def _launch_ball(self) -> None:
        """Launch a new ball."""
        self.ball = RigidBody(Vector2D(370, 500), mass=1.0)
        self.ball.restitution = 0.6
        collider = CircleCollider(self.ball, 10)
        self.world.add_body(self.ball, collider)
        self.ball.apply_impulse(Vector2D(-300, -800))

    def handle_input(self) -> None:
        """Handle player input."""
        keys = pygame.key.get_pressed()

        # Flipper control
        if keys[K_LEFT]:
            self.flipper_left.rotation = math.radians(30)
        else:
            self.flipper_left.rotation = 0

        if keys[K_RIGHT]:
            self.flipper_right.rotation = math.radians(-30)
        else:
            self.flipper_right.rotation = 0

    def check_scoring(self) -> None:
        """Check if ball hit any bumpers."""
        for bumper in self.bumpers:
            distance = self.ball.position.distance_to(bumper.position)
            if distance < 40:  # Approximate collision distance
                self.score += 100
                break

    def check_drain(self) -> None:
        """Check if ball fell through drain."""
        if self.ball.position.y > HEIGHT + 30:
            self.world.remove_body(self.ball)
            self._launch_ball()

    def update(self, dt: float) -> None:
        """Update game state."""
        self.world.step(dt)
        self.check_scoring()

    def render(self) -> None:
        """Render the game."""
        screen.fill(BLACK)

        # Draw walls
        pygame.draw.rect(screen, GRAY, (0, 0, 20, HEIGHT))
        pygame.draw.rect(screen, GRAY, (WIDTH - 20, 0, 20, HEIGHT))
        pygame.draw.rect(screen, GRAY, (0, 0, WIDTH, 20))

        # Draw bumpers
        for bumper in self.bumpers:
            pos = (int(bumper.position.x), int(bumper.position.y))
            pygame.draw.circle(screen, YELLOW, pos, 25)
            pygame.draw.circle(screen, RED, pos, 20)

        # Draw flippers
        left_pos = (int(self.flipper_left.position.x), int(self.flipper_left.position.y))
        right_pos = (int(self.flipper_right.position.x), int(self.flipper_right.position.y))
        pygame.draw.rect(screen, BLUE, (left_pos[0] - 40, left_pos[1] - 7, 80, 15))
        pygame.draw.rect(screen, BLUE, (right_pos[0] - 40, right_pos[1] - 7, 80, 15))

        # Draw ball
        ball_pos = (int(self.ball.position.x), int(self.ball.position.y))
        pygame.draw.circle(screen, WHITE, ball_pos, 10)

        # Draw score
        font = pygame.font.Font(None, 36)
        score_text = font.render(f"Score: {self.score}", True, WHITE)
        screen.blit(score_text, (WIDTH - 150, 30))

        pygame.display.flip()

    def run(self) -> None:
        """Main game loop."""
        clock = pygame.time.Clock()
        running = True

        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                    elif event.key == pygame.K_SPACE:
                        self._launch_ball()

            self.handle_input()
            self.update(1 / 60)
            self.render()
            clock.tick(60)

        pygame.quit()


if __name__ == "__main__":
    from pygame.locals import K_LEFT, K_RIGHT, K_ESCAPE, K_SPACE
    game = PinballGame()
    game.run()
