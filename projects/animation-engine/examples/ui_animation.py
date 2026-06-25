"""
UI Animation Example

Demonstrates common UI animation patterns: fade, slide, scale, and sequenced animations.
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from animation_engine import (
    AnimationEngine, Keyframe, AnimationConfig, TweenConfig,
    Vector3, Color,
)


class UIElement:
    """Simulated UI element with animatable properties."""

    def __init__(self, name, x=0, y=0, opacity=1.0, scale=1.0):
        self.name = name
        self.x = x
        self.y = y
        self.opacity = opacity
        self.scale = scale
        self.visible = True

    def __repr__(self):
        return (
            f"UIElement({self.name}: x={self.x:.1f}, y={self.y:.1f}, "
            f"opacity={self.opacity:.2f}, scale={self.scale:.2f})"
        )


def simulate_frame(engine, dt, frame_num):
    """Simulate one frame of the animation loop."""
    engine.update(dt)
    return engine.get_stats()


def main():
    print("=" * 60)
    print("  UI Animation Example")
    print("=" * 60)
    print()

    engine = AnimationEngine()

    # 1. Fade In Animation
    print("1. Fade In Animation")
    print("-" * 40)

    fade_element = UIElement("fade_panel", opacity=0)
    fade_anim = engine.create_animation(AnimationConfig(
        keyframes=[
            Keyframe(time=0.0, values={"opacity": 0.0}),
            Keyframe(time=1.0, values={"opacity": 1.0}),
        ],
        duration=0.5,
        easing="ease_out_cubic",
        on_update=lambda v: setattr(fade_element, "opacity", v["opacity"]),
        on_complete=lambda: print("  [Fade complete]"),
    ), name="fade_in")
    fade_anim.start()

    for i in range(30):
        simulate_frame(engine, 1 / 60, i)
    print(f"  Final: {fade_element}")
    print()

    # 2. Slide In Animation
    print("2. Slide In Animation")
    print("-" * 40)

    slide_element = UIElement("slide_panel", x=-200)
    slide_anim = engine.create_animation(AnimationConfig(
        keyframes=[
            Keyframe(time=0.0, values={"x": -200.0, "opacity": 0.0}),
            Keyframe(time=0.7, values={"x": 10.0, "opacity": 1.0}),
            Keyframe(time=1.0, values={"x": 0.0, "opacity": 1.0}),
        ],
        duration=0.8,
        easing="ease_out_back",
        on_update=lambda v: (
            setattr(slide_element, "x", v["x"]),
            setattr(slide_element, "opacity", v["opacity"]),
        ),
    ), name="slide_in")
    slide_anim.start()

    for i in range(50):
        simulate_frame(engine, 1 / 60, i)
    print(f"  Final: {slide_element}")
    print()

    # 3. Scale / Pop Animation
    print("3. Scale Pop Animation")
    print("-" * 40)

    pop_element = UIElement("button", scale=0)
    pop_anim = engine.create_animation(AnimationConfig(
        keyframes=[
            Keyframe(time=0.0, values={"scale": 0.0}),
            Keyframe(time=0.6, values={"scale": 1.1}),
            Keyframe(time=0.8, values={"scale": 0.95}),
            Keyframe(time=1.0, values={"scale": 1.0}),
        ],
        duration=0.5,
        on_update=lambda v: setattr(pop_element, "scale", v["scale"]),
    ), name="pop")
    pop_anim.start()

    for i in range(35):
        simulate_frame(engine, 1 / 60, i)
    print(f"  Final: {pop_element}")
    print()

    # 4. Tween-based animation
    print("4. Tween Animation (Numeric)")
    print("-" * 40)

    progress_bar = {"value": 0}
    tween = engine.create_tween(TweenConfig(
        from_values={"value": 0.0},
        to_values={"value": 100.0},
        duration=2.0,
        easing="ease_in_out_cubic",
        on_update=lambda v: progress_bar.update(v),
    ), name="progress")
    tween.start()

    for i in range(120):
        simulate_frame(engine, 1 / 60, i)
        if i % 20 == 0:
            bar = "#" * int(progress_bar["value"] / 2)
            print(f"  Progress: [{bar:50s}] {progress_bar['value']:.1f}%")
    print()

    # 5. Animation Queue
    print("5. Sequenced Animation")
    print("-" * 40)

    seq_element = UIElement("modal")
    queue = engine.create_queue("modal_sequence")
    queue.animate(AnimationConfig(
        keyframes=[
            Keyframe(time=0.0, values={"opacity": 0, "scale": 0.8}),
            Keyframe(time=1.0, values={"opacity": 1, "scale": 1.0}),
        ],
        duration=0.3,
        easing="ease_out_cubic",
        on_update=lambda v: (
            setattr(seq_element, "opacity", v["opacity"]),
            setattr(seq_element, "scale", v["scale"]),
        ),
    ))
    queue.wait(1.0)
    queue.animate(AnimationConfig(
        keyframes=[
            Keyframe(time=0.0, values={"opacity": 1, "scale": 1.0}),
            Keyframe(time=1.0, values={"opacity": 0, "scale": 0.9}),
        ],
        duration=0.2,
        easing="ease_in_cubic",
        on_update=lambda v: (
            setattr(seq_element, "opacity", v["opacity"]),
            setattr(seq_element, "scale", v["scale"]),
        ),
    ))
    queue.call(lambda: print("  [Modal closed]"))
    queue.start()

    for i in range(120):
        simulate_frame(engine, 1 / 60, i)
    print(f"  Final: {seq_element}")
    print()

    # 6. Multi-property animation
    print("6. Multi-Property Animation")
    print("-" * 40)

    card = UIElement("card", x=-100, y=50, opacity=0, scale=0.5)
    card_anim = engine.create_animation(AnimationConfig(
        keyframes=[
            Keyframe(time=0.0, values={
                "x": -100.0, "y": 50.0, "opacity": 0.0, "scale": 0.5,
            }),
            Keyframe(time=0.5, values={
                "x": 10.0, "y": 0.0, "opacity": 1.0, "scale": 1.05,
            }),
            Keyframe(time=1.0, values={
                "x": 0.0, "y": 0.0, "opacity": 1.0, "scale": 1.0,
            }),
        ],
        duration=0.6,
        easing="ease_out_cubic",
        on_update=lambda v: (
            setattr(card, "x", v["x"]),
            setattr(card, "y", v["y"]),
            setattr(card, "opacity", v["opacity"]),
            setattr(card, "scale", v["scale"]),
        ),
    ), name="card_entrance")
    card_anim.start()

    for i in range(40):
        simulate_frame(engine, 1 / 60, i)
    print(f"  Final: {card}")
    print()

    print("=" * 60)
    print("  All UI animations complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
