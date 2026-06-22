#!/usr/bin/env python3
"""
GPU Shader Library - Demo of All Effects

This example demonstrates how to use the shader library to:
1. Load and validate all shaders
2. Create shader passes and effects
3. Display uniform information for each shader
4. Show the complete rendering pipeline

This is a headless demo that works without a GPU by using
the pure-Python shader parser for validation and analysis.
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from utils.shader_library import ShaderLibrary
from utils.shader_parser import ShaderType


def print_separator(title: str):
    """Print a formatted section separator."""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")


def print_shader_info(name: str, library: ShaderLibrary):
    """Print detailed information about a shader."""
    info = library.shaders.get(name)
    if not info:
        print(f"  Shader '{name}' not found")
        return

    shader_type = info.shader_type.name if info.shader_type else "UNKNOWN"
    print(f"\n  [{shader_type}] {name} (GLSL {info.version or 'unknown'})")

    if info.uniforms:
        print(f"    Uniforms ({len(info.uniforms)}):")
        for u in info.uniforms:
            array_str = f"[{u.array_size}]" if u.array_size else ""
            print(f"      - {u.type_name} {u.name}{array_str}")

    if info.inputs:
        print(f"    Inputs ({len(info.inputs)}):")
        for v in info.inputs:
            loc_str = f" (loc={v.location})" if v.location is not None else ""
            print(f"      - {v.type_name} {v.name}{loc_str}")

    if info.outputs:
        print(f"    Outputs ({len(info.outputs)}):")
        for v in info.outputs:
            print(f"      - {v.type_name} {v.name}")

    if info.functions:
        print(f"    Functions ({len(info.functions)}):")
        for f in info.functions:
            print(f"      - {f.return_type} {f.name}({', '.join(f.parameters)})")

    if info.defines:
        print(f"    Defines ({len(info.defines)}):")
        for k, v in info.defines.items():
            print(f"      - #define {k} {v}")

    valid, errors = library.validate_shader(name)
    status = "PASS" if valid else "FAIL"
    print(f"    Validation: {status}")
    if errors:
        for e in errors:
            print(f"      ERROR: {e}")
    if info.warnings:
        for w in info.warnings:
            print(f"      WARNING: {w}")


def demo_basic_shaders(library: ShaderLibrary):
    """Demonstrate basic shaders."""
    print_separator("Basic Shaders")

    basic_shaders = ["passthrough", "solid_color", "texture", "gradient"]
    for name in basic_shaders:
        print_shader_info(name, library)

    # Create a basic rendering pass
    print("\n  Creating 'basic_color' pass (passthrough + solid_color)...")
    pass_obj = library.create_pass("basic_color", "passthrough", "solid_color")
    print(f"    Valid: {pass_obj.valid}")
    print(f"    Total uniforms: {len(pass_obj.uniforms)}")


def demo_lighting_shaders(library: ShaderLibrary):
    """Demonstrate lighting shaders."""
    print_separator("Lighting Shaders")

    lighting_shaders = [
        "ambient", "diffuse", "phong", "blinn_phong",
        "directional", "point_light", "spotlight", "multi_light"
    ]

    for name in lighting_shaders:
        print_shader_info(name, library)

    # Create lighting effects
    effects = [
        ("ambient_lighting", "Ambient lighting model",
         [("main", "passthrough", "ambient")]),
        ("diffuse_lighting", "Lambertian diffuse lighting",
         [("main", "passthrough", "diffuse")]),
        ("phong_lighting", "Phong reflection model",
         [("main", "passthrough", "phong")]),
        ("blinn_phong_lighting", "Blinn-Phong reflection model",
         [("main", "passthrough", "blinn_phong")]),
        ("directional_lighting", "Directional light (sunlight)",
         [("main", "passthrough", "directional")]),
        ("point_lighting", "Point light with attenuation",
         [("main", "passthrough", "point_light")]),
        ("spotlight_lighting", "Spotlight with cone",
         [("main", "passthrough", "spotlight")]),
        ("multi_lighting", "Multiple light sources",
         [("main", "passthrough", "multi_light")]),
    ]

    print("\n  Creating lighting effects...")
    for name, desc, passes in effects:
        effect = library.create_effect(name, desc, passes, "lighting")
        all_valid = all(p.valid for p in effect.passes)
        print(f"    {name}: {'VALID' if all_valid else 'INVALID'}")


def demo_postprocessing_shaders(library: ShaderLibrary):
    """Demonstrate post-processing shaders."""
    print_separator("Post-Processing Shaders")

    pp_shaders = [
        "screen_quad", "grayscale", "sepia", "blur",
        "edge_detection", "vignette", "chromatic_aberration",
        "bloom", "hdr_tonemapping"
    ]

    for name in pp_shaders:
        print_shader_info(name, library)

    # Create post-processing effects
    effects = [
        ("grayscale_effect", "Convert to grayscale",
         [("main", "screen_quad", "grayscale")]),
        ("sepia_effect", "Sepia tone filter",
         [("main", "screen_quad", "sepia")]),
        ("blur_effect", "Gaussian blur",
         [("main", "screen_quad", "blur")]),
        ("edge_detect_effect", "Sobel edge detection",
         [("main", "screen_quad", "edge_detection")]),
        ("vignette_effect", "Vignette darkening",
         [("main", "screen_quad", "vignette")]),
        ("chromatic_aberration_effect", "Lens chromatic aberration",
         [("main", "screen_quad", "chromatic_aberration")]),
        ("bloom_effect", "HDR bloom (multi-pass)",
         [("bright_pass", "screen_quad", "bloom"),
          ("blur_h", "screen_quad", "blur"),
          ("blur_v", "screen_quad", "blur"),
          ("combine", "screen_quad", "bloom")]),
        ("hdr_effect", "HDR tone mapping",
         [("main", "screen_quad", "hdr_tonemapping")]),
    ]

    print("\n  Creating post-processing effects...")
    for name, desc, passes in effects:
        effect = library.create_effect(name, desc, passes, "postprocessing")
        all_valid = all(p.valid for p in effect.passes)
        print(f"    {name}: {'VALID' if all_valid else 'INVALID'} "
              f"({len(effect.passes)} pass(es))")


def demo_rendering_pipeline(library: ShaderLibrary):
    """Demonstrate a complete rendering pipeline."""
    print_separator("Complete Rendering Pipeline")

    # A typical forward rendering pipeline
    pipeline_stages = [
        ("Geometry Pass", "passthrough", "blinn_phong",
         "Render scene with Blinn-Phong lighting"),
        ("Bright Extract", "screen_quad", "bloom",
         "Extract bright pixels for bloom"),
        ("Bloom Blur H", "screen_quad", "blur",
         "Horizontal Gaussian blur"),
        ("Bloom Blur V", "screen_quad", "blur",
         "Vertical Gaussian blur"),
        ("Bloom Combine", "screen_quad", "bloom",
         "Combine bloom with scene"),
        ("HDR Tone Map", "screen_quad", "hdr_tonemapping",
         "Convert HDR to LDR"),
        ("Vignette", "screen_quad", "vignette",
         "Add vignette effect"),
    ]

    print("\n  Rendering Pipeline Stages:")
    for i, (stage_name, vert, frag, desc) in enumerate(pipeline_stages, 1):
        pass_obj = library.create_pass(stage_name, vert, frag)
        status = "OK" if pass_obj.valid else "FAIL"
        print(f"    {i}. [{status}] {stage_name}: {desc}")
        print(f"       Shader: {vert}.vert + {frag}.frag")
        print(f"       Uniforms: {len(pass_obj.uniforms)}")

    # Show uniform summary
    print("\n  Uniform Summary for Pipeline:")
    all_uniforms = set()
    for stage_name, vert, frag, _ in pipeline_stages:
        pass_obj = library.create_pass(stage_name, vert, frag)
        for name in pass_obj.uniforms:
            all_uniforms.add(name)
    for u in sorted(all_uniforms):
        print(f"    - {u}")


def main():
    print("GPU Shader Library - Demo of All Effects")
    print("=" * 60)

    # Load all shaders
    shader_dir = os.path.join(os.path.dirname(__file__), '..', 'src')
    library = ShaderLibrary(shader_dir)

    print(f"\nLoaded {len(library.shaders)} shaders")

    # Show all shaders
    shader_list = library.list_shaders()
    print("\nShader Inventory:")
    for s in shader_list:
        print(f"  {s['name']:25s} [{s['type']:8s}] v{s['version']:4s} "
              f"U:{s['uniforms']:2d} I:{s['inputs']:2d} O:{s['outputs']:2d}")

    # Demo each category
    demo_basic_shaders(library)
    demo_lighting_shaders(library)
    demo_postprocessing_shaders(library)
    demo_rendering_pipeline(library)

    # Summary
    print_separator("Summary")
    print(f"  Total shaders loaded: {len(library.shaders)}")
    print(f"  Total effects created: {len(library.effects)}")

    all_valid = all(
        library.validate_shader(name)[0]
        for name in library.shaders
    )
    print(f"  All shaders valid: {all_valid}")

    print("\n  Categories:")
    categories = {}
    for effect in library.effects.values():
        cat = effect.category or "uncategorized"
        categories.setdefault(cat, []).append(effect.name)
    for cat, effects in sorted(categories.items()):
        print(f"    {cat}: {len(effects)} effects")

    print("\nDemo complete!")


if __name__ == "__main__":
    main()
