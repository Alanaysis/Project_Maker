"""
Main Animation Engine.

Orchestrates all animation subsystems: keyframe animations, tweens,
skeletal animations, particle systems, and animation queues.
"""

from __future__ import annotations

import time
from typing import Any, Callable, Dict, List, Optional

from .keyframe import KeyframeAnimation
from .particle import ParticleSystem
from .queue import AnimationQueue
from .skeleton import SkeletalAnimation, Skeleton, SkinnedMesh
from .tween import Tween
from .types import AnimationConfig, TweenConfig
from .utils import FrameRateCounter, Timer


class AnimationEngine:
    """Central animation engine that manages all animation types.

    Provides a unified API for creating and managing animations.

    Example::

        engine = AnimationEngine()

        # Create animations
        fade_in = engine.create_animation(AnimationConfig(
            keyframes=[
                Keyframe(time=0.0, values={"opacity": 0}),
                Keyframe(time=1.0, values={"opacity": 1}),
            ],
            duration=1.0,
        ))

        tween = engine.create_tween(TweenConfig(
            from_values={"x": 0},
            to_values={"x": 200},
            duration=0.5,
            easing="ease_out_cubic",
        ))

        # Game loop
        while running:
            dt = get_delta_time()
            engine.update(dt)
            fps = engine.fps
    """

    def __init__(self):
        self._animations: Dict[str, KeyframeAnimation] = {}
        self._tweens: Dict[str, Tween] = {}
        self._queues: Dict[str, AnimationQueue] = {}
        self._skeletons: Dict[str, Skeleton] = {}
        self._skeletal_anims: Dict[str, SkeletalAnimation] = {}
        self._particle_systems: Dict[str, ParticleSystem] = {}
        self._meshes: Dict[str, SkinnedMesh] = {}

        self._fps_counter = FrameRateCounter()
        self._timer = Timer()
        self._running: bool = False
        self._paused: bool = False
        self._time_scale: float = 1.0
        self._total_time: float = 0.0

        # Global callbacks
        self._on_update: Optional[Callable[[float], None]] = None

    # -----------------------------------------------------------------------
    # Properties
    # -----------------------------------------------------------------------

    @property
    def fps(self) -> float:
        """Current frames per second."""
        return self._fps_counter.fps

    @property
    def frame_time(self) -> float:
        """Average frame time in seconds."""
        return self._fps_counter.frame_time

    @property
    def frame_time_ms(self) -> float:
        """Average frame time in milliseconds."""
        return self._fps_counter.frame_time_ms

    @property
    def time_scale(self) -> float:
        """Global time scale factor."""
        return self._time_scale

    @time_scale.setter
    def time_scale(self, value: float) -> None:
        self._time_scale = max(0, value)

    @property
    def total_time(self) -> float:
        """Total elapsed time since engine started."""
        return self._total_time

    @property
    def is_paused(self) -> bool:
        return self._paused

    # -----------------------------------------------------------------------
    # Lifecycle
    # -----------------------------------------------------------------------

    def start(self) -> None:
        """Start the engine."""
        self._timer.start()
        self._running = True
        self._paused = False

    def pause(self) -> None:
        """Pause all animations."""
        self._paused = True
        for anim in self._animations.values():
            anim.pause()
        for tw in self._tweens.values():
            tw.pause()
        for queue in self._queues.values():
            queue.pause()

    def resume(self) -> None:
        """Resume all animations."""
        self._paused = False
        for anim in self._animations.values():
            anim.resume()
        for tw in self._tweens.values():
            tw.resume()
        for queue in self._queues.values():
            queue.resume()

    def stop(self) -> None:
        """Stop all animations."""
        self._running = False
        for anim in self._animations.values():
            anim.stop()
        for tw in self._tweens.values():
            tw.stop()
        for queue in self._queues.values():
            queue.stop()

    def update(self, dt: float) -> None:
        """Advance all animations by dt seconds.

        This is the main update function that should be called
        once per frame in your application loop.

        Args:
            dt: Delta time in seconds.
        """
        self._fps_counter.frame()

        if self._paused:
            return

        scaled_dt = dt * self._time_scale
        self._total_time += scaled_dt

        # Update keyframe animations
        finished_anims = []
        for name, anim in self._animations.items():
            anim.update(scaled_dt)
            if anim.is_finished:
                finished_anims.append(name)

        # Update tweens
        finished_tweens = []
        for name, tw in self._tweens.items():
            tw.update(scaled_dt)
            if tw.is_finished:
                finished_tweens.append(name)

        # Update queues
        for queue in self._queues.values():
            queue.update(scaled_dt)

        # Update skeletal animations
        for skel_anim in self._skeletal_anims.values():
            for skeleton in self._skeletons.values():
                skel_anim.apply(skeleton, self._total_time)

        # Update particle systems
        for ps in self._particle_systems.values():
            ps.update(scaled_dt)

        # Update meshes
        for name, mesh in self._meshes.items():
            for skeleton in self._skeletons.values():
                mesh.deform(skeleton)

        # Cleanup finished
        for name in finished_anims:
            del self._animations[name]
        for name in finished_tweens:
            del self._tweens[name]

        if self._on_update:
            self._on_update(scaled_dt)

    # -----------------------------------------------------------------------
    # Keyframe Animations
    # -----------------------------------------------------------------------

    def create_animation(
        self, config: AnimationConfig, name: Optional[str] = None
    ) -> KeyframeAnimation:
        """Create and register a keyframe animation.

        Args:
            config: Animation configuration.
            name: Optional name for the animation.

        Returns:
            The created KeyframeAnimation.
        """
        anim = KeyframeAnimation(config)
        if name is None:
            name = f"anim_{len(self._animations)}"
        self._animations[name] = anim
        return anim

    def play_animation(self, name: str) -> Optional[KeyframeAnimation]:
        """Start playing a named animation."""
        anim = self._animations.get(name)
        if anim:
            anim.start()
        return anim

    def get_animation(self, name: str) -> Optional[KeyframeAnimation]:
        """Get a named animation."""
        return self._animations.get(name)

    def remove_animation(self, name: str) -> None:
        """Remove a named animation."""
        self._animations.pop(name, None)

    # -----------------------------------------------------------------------
    # Tweens
    # -----------------------------------------------------------------------

    def create_tween(
        self, config: TweenConfig, name: Optional[str] = None
    ) -> Tween:
        """Create and register a tween.

        Args:
            config: Tween configuration.
            name: Optional name.

        Returns:
            The created Tween.
        """
        tw = Tween(config)
        if name is None:
            name = f"tween_{len(self._tweens)}"
        self._tweens[name] = tw
        return tw

    def play_tween(self, name: str) -> Optional[Tween]:
        """Start playing a named tween."""
        tw = self._tweens.get(name)
        if tw:
            tw.start()
        return tw

    def get_tween(self, name: str) -> Optional[Tween]:
        return self._tweens.get(name)

    def remove_tween(self, name: str) -> None:
        self._tweens.pop(name, None)

    # -----------------------------------------------------------------------
    # Animation Queues
    # -----------------------------------------------------------------------

    def create_queue(self, name: str) -> AnimationQueue:
        """Create and register an animation queue."""
        queue = AnimationQueue()
        self._queues[name] = queue
        return queue

    def get_queue(self, name: str) -> Optional[AnimationQueue]:
        return self._queues.get(name)

    def remove_queue(self, name: str) -> None:
        self._queues.pop(name, None)

    # -----------------------------------------------------------------------
    # Skeletal Animation
    # -----------------------------------------------------------------------

    def add_skeleton(self, name: str, skeleton: Skeleton) -> None:
        """Register a skeleton."""
        self._skeletons[name] = skeleton

    def get_skeleton(self, name: str) -> Optional[Skeleton]:
        return self._skeletons.get(name)

    def add_skeletal_animation(self, name: str, anim: SkeletalAnimation) -> None:
        """Register a skeletal animation."""
        self._skeletal_anims[name] = anim

    def get_skeletal_animation(self, name: str) -> Optional[SkeletalAnimation]:
        return self._skeletal_anims.get(name)

    def add_mesh(self, name: str, mesh: SkinnedMesh) -> None:
        """Register a skinned mesh."""
        self._meshes[name] = mesh

    # -----------------------------------------------------------------------
    # Particle Systems
    # -----------------------------------------------------------------------

    def add_particle_system(self, name: str, system: ParticleSystem) -> None:
        """Register a particle system."""
        self._particle_systems[name] = system

    def get_particle_system(self, name: str) -> Optional[ParticleSystem]:
        return self._particle_systems.get(name)

    def remove_particle_system(self, name: str) -> None:
        self._particle_systems.pop(name, None)

    # -----------------------------------------------------------------------
    # Callbacks
    # -----------------------------------------------------------------------

    def on_update(self, callback: Callable[[float], None]) -> None:
        """Set a global update callback."""
        self._on_update = callback

    # -----------------------------------------------------------------------
    # Stats
    # -----------------------------------------------------------------------

    def get_stats(self) -> Dict[str, Any]:
        """Get engine statistics."""
        return {
            "fps": round(self.fps, 1),
            "frame_time_ms": round(self.frame_time_ms, 2),
            "total_time": round(self._total_time, 3),
            "time_scale": self._time_scale,
            "paused": self._paused,
            "animations": len(self._animations),
            "tweens": len(self._tweens),
            "queues": len(self._queues),
            "skeletons": len(self._skeletons),
            "particle_systems": len(self._particle_systems),
            "total_particles": sum(
                ps.total_particles for ps in self._particle_systems.values()
            ),
        }

    def __repr__(self) -> str:
        return (
            f"AnimationEngine(animations={len(self._animations)}, "
            f"tweens={len(self._tweens)}, queues={len(self._queues)})"
        )
