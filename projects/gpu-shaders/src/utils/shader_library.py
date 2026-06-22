"""
Shader Library Manager

Provides a high-level API for managing a collection of shaders.
Handles loading, caching, validation, and shader program creation.
"""

import os
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional

from .shader_parser import (
    ShaderParser, ShaderInfo, ShaderType, ShaderVariable,
    parse_shader, load_and_parse
)


@dataclass
class ShaderPass:
    """Represents a single render pass with vertex and fragment shaders."""
    name: str
    vertex_source: str
    fragment_source: str
    vertex_info: Optional[ShaderInfo] = None
    fragment_info: Optional[ShaderInfo] = None
    uniforms: dict[str, ShaderVariable] = field(default_factory=dict)
    valid: bool = False
    errors: list[str] = field(default_factory=list)


@dataclass
class ShaderEffect:
    """Represents a complete rendering effect (one or more passes)."""
    name: str
    description: str
    passes: list[ShaderPass] = field(default_factory=list)
    category: str = ""


class ShaderLibrary:
    """
    Manages a collection of GPU shaders.

    Provides functionality to:
    - Load shaders from files or strings
    - Validate shader syntax
    - Extract uniform information
    - Organize shaders by category
    """

    def __init__(self, shader_dir: Optional[str] = None):
        self.shader_dir = shader_dir
        self.shaders: dict[str, ShaderInfo] = {}
        self.effects: dict[str, ShaderEffect] = {}
        self.parser = ShaderParser()

        if shader_dir:
            self.load_directory(shader_dir)

    def load_directory(self, directory: str):
        """Load all shader files from a directory tree."""
        directory = Path(directory)
        for shader_file in directory.rglob("*.vert"):
            self.load_shader(str(shader_file), ShaderType.VERTEX)
        for shader_file in directory.rglob("*.frag"):
            self.load_shader(str(shader_file), ShaderType.FRAGMENT)
        for shader_file in directory.rglob("*.glsl"):
            self.load_shader(str(shader_file))

    def load_shader(self, filepath: str,
                    shader_type: Optional[ShaderType] = None) -> ShaderInfo:
        """Load and parse a single shader file."""
        info = load_and_parse(filepath)

        if shader_type:
            info.shader_type = shader_type
        elif not info.shader_type:
            # Try to detect from extension
            ext = Path(filepath).suffix
            if ext == ".vert":
                info.shader_type = ShaderType.VERTEX
            elif ext == ".frag":
                info.shader_type = ShaderType.FRAGMENT

        name = Path(filepath).stem
        self.shaders[name] = info
        return info

    def load_from_string(self, name: str, source: str,
                         shader_type: Optional[ShaderType] = None) -> ShaderInfo:
        """Load and parse a shader from a source string."""
        info = parse_shader(source)
        if shader_type:
            info.shader_type = shader_type
        self.shaders[name] = info
        return info

    def validate_shader(self, name: str) -> tuple[bool, list[str]]:
        """Validate a loaded shader."""
        if name not in self.shaders:
            return False, [f"Shader '{name}' not found"]

        info = self.shaders[name]
        errors = list(info.errors)

        # Additional validation
        if info.shader_type == ShaderType.VERTEX:
            # Vertex shaders should output gl_Position
            if "gl_Position" not in '\n'.join(info.source_lines):
                errors.append("Vertex shader does not set gl_Position")

        if info.shader_type == ShaderType.FRAGMENT:
            # Fragment shaders should have color output
            has_output = any(v.type_name in ("vec4", "vec3")
                           for v in info.outputs)
            if not has_output and "gl_FragColor" not in '\n'.join(info.source_lines):
                errors.append("Fragment shader has no color output")

        return len(errors) == 0, errors

    def get_uniforms(self, name: str) -> list[ShaderVariable]:
        """Get uniform variables from a shader."""
        if name not in self.shaders:
            return []
        return self.shaders[name].uniforms

    def create_pass(self, name: str, vertex_name: str,
                    fragment_name: str) -> ShaderPass:
        """Create a shader pass from two loaded shaders."""
        if vertex_name not in self.shaders:
            raise ValueError(f"Vertex shader '{vertex_name}' not found")
        if fragment_name not in self.shaders:
            raise ValueError(f"Fragment shader '{fragment_name}' not found")

        vert_info = self.shaders[vertex_name]
        frag_info = self.shaders[fragment_name]

        pass_obj = ShaderPass(
            name=name,
            vertex_source='\n'.join(vert_info.source_lines),
            fragment_source='\n'.join(frag_info.source_lines),
            vertex_info=vert_info,
            fragment_info=frag_info
        )

        # Collect all uniforms
        for u in vert_info.uniforms:
            pass_obj.uniforms[u.name] = u
        for u in frag_info.uniforms:
            pass_obj.uniforms[u.name] = u

        # Validate
        vert_valid, vert_errors = self.validate_shader(vertex_name)
        frag_valid, frag_errors = self.validate_shader(fragment_name)
        pass_obj.valid = vert_valid and frag_valid
        pass_obj.errors = vert_errors + frag_errors

        return pass_obj

    def create_effect(self, name: str, description: str,
                      passes: list[tuple[str, str, str]],
                      category: str = "") -> ShaderEffect:
        """
        Create a shader effect with multiple passes.

        Args:
            name: Effect name
            description: Effect description
            passes: List of (pass_name, vertex_shader, fragment_shader) tuples
            category: Effect category
        """
        effect = ShaderEffect(
            name=name,
            description=description,
            category=category
        )

        for pass_name, vert_name, frag_name in passes:
            shader_pass = self.create_pass(pass_name, vert_name, frag_name)
            effect.passes.append(shader_pass)

        self.effects[name] = effect
        return effect

    def list_shaders(self) -> list[dict]:
        """List all loaded shaders with their metadata."""
        result = []
        for name, info in self.shaders.items():
            result.append({
                "name": name,
                "type": info.shader_type.name if info.shader_type else "UNKNOWN",
                "version": info.version,
                "uniforms": len(info.uniforms),
                "inputs": len(info.inputs),
                "outputs": len(info.outputs),
                "errors": len(info.errors),
                "warnings": len(info.warnings)
            })
        return result

    def get_shader_source(self, name: str) -> Optional[str]:
        """Get the source code of a loaded shader."""
        if name not in self.shaders:
            return None
        return '\n'.join(self.shaders[name].source_lines)

    def get_errors(self, name: str) -> list[str]:
        """Get all errors and warnings for a shader."""
        if name not in self.shaders:
            return [f"Shader '{name}' not found"]
        info = self.shaders[name]
        return [f"ERROR: {e}" for e in info.errors] + \
               [f"WARNING: {w}" for w in info.warnings]
