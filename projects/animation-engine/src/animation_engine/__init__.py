"""
Animation Engine - A comprehensive Python animation framework.

Supports keyframe animations, tween animations with easing functions,
skeletal animation, and particle systems.
"""

__version__ = "1.0.0"

from .easing import (
    linear,
    ease_in_quad, ease_out_quad, ease_in_out_quad,
    ease_in_cubic, ease_out_cubic, ease_in_out_cubic,
    ease_in_sine, ease_out_sine, ease_in_out_sine,
    ease_in_expo, ease_out_expo, ease_in_out_expo,
    ease_in_circ, ease_out_circ, ease_in_out_circ,
    ease_in_elastic, ease_out_elastic, ease_in_out_elastic,
    ease_in_back, ease_out_back, ease_in_out_back,
    ease_in_bounce, ease_out_bounce, ease_in_out_bounce,
    get_easing_function,
)
from .types import Keyframe, AnimationConfig, TweenConfig, Vector3, Color
from .keyframe import KeyframeAnimation
from .tween import Tween
from .skeleton import Bone, Skeleton, SkinWeight, SkinnedMesh
from .particle import Particle, ParticleEmitter, ParticleSystem
from .queue import AnimationQueue
from .engine import AnimationEngine

__all__ = [
    "AnimationEngine",
    "KeyframeAnimation",
    "Tween",
    "AnimationQueue",
    "Bone",
    "Skeleton",
    "SkinWeight",
    "SkinnedMesh",
    "Particle",
    "ParticleEmitter",
    "ParticleSystem",
    "Keyframe",
    "AnimationConfig",
    "TweenConfig",
    "Vector3",
    "Color",
    "linear",
    "ease_in_quad",
    "ease_out_quad",
    "ease_in_out_quad",
    "ease_in_cubic",
    "ease_out_cubic",
    "ease_in_out_cubic",
    "ease_in_sine",
    "ease_out_sine",
    "ease_in_out_sine",
    "ease_in_expo",
    "ease_out_expo",
    "ease_in_out_expo",
    "ease_in_circ",
    "ease_out_circ",
    "ease_in_out_circ",
    "ease_in_elastic",
    "ease_out_elastic",
    "ease_in_out_elastic",
    "ease_in_back",
    "ease_out_back",
    "ease_in_out_back",
    "ease_in_bounce",
    "ease_out_bounce",
    "ease_in_out_bounce",
    "get_easing_function",
]
