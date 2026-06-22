"""
GLSL Shader Parser and Validator

This module provides a pure-Python GLSL parser that can validate shader
syntax without requiring a GPU or OpenGL context. It performs lexical
analysis, basic syntax checking, and uniform/attribute extraction.
"""

import re
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Optional


class ShaderType(Enum):
    """Supported shader types."""
    VERTEX = auto()
    FRAGMENT = auto()
    GEOMETRY = auto()
    TESS_CONTROL = auto()
    TESS_EVALUATION = auto()
    COMPUTE = auto()


@dataclass
class ShaderVariable:
    """Represents a GLSL variable declaration."""
    type_name: str
    name: str
    qualifier: str = ""
    array_size: Optional[int] = None
    location: Optional[int] = None

    def __str__(self):
        parts = []
        if self.qualifier:
            parts.append(self.qualifier)
        if self.location is not None:
            parts.append(f"layout(location={self.location})")
        parts.append(self.type_name)
        parts.append(self.name)
        if self.array_size is not None:
            parts[-1] += f"[{self.array_size}]"
        return " ".join(parts)


@dataclass
class ShaderFunction:
    """Represents a GLSL function declaration."""
    return_type: str
    name: str
    parameters: list[str]
    body: str = ""
    line_number: int = 0


@dataclass
class ShaderInfo:
    """Contains parsed information about a shader."""
    shader_type: Optional[ShaderType] = None
    version: str = ""
    inputs: list[ShaderVariable] = field(default_factory=list)
    outputs: list[ShaderVariable] = field(default_factory=list)
    uniforms: list[ShaderVariable] = field(default_factory=list)
    functions: list[ShaderFunction] = field(default_factory=list)
    defines: dict[str, str] = field(default_factory=dict)
    extensions: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    source_lines: list[str] = field(default_factory=list)


# GLSL type definitions
GLSL_SCALAR_TYPES = {"float", "int", "uint", "bool", "double"}
GLSL_VEC_TYPES = {"vec2", "vec3", "vec4", "ivec2", "ivec3", "ivec4",
                  "uvec2", "uvec3", "uvec4", "bvec2", "bvec3", "bvec4",
                  "dvec2", "dvec3", "dvec4"}
GLSL_MAT_TYPES = {"mat2", "mat3", "mat4", "mat2x2", "mat2x3", "mat2x4",
                  "mat3x2", "mat3x3", "mat3x4", "mat4x2", "mat4x3", "mat4x4",
                  "dmat2", "dmat3", "dmat4"}
GLSL_SAMPLER_TYPES = {"sampler1D", "sampler2D", "sampler3D", "samplerCube",
                      "sampler2DShadow", "samplerCubeShadow",
                      "sampler1DArray", "sampler2DArray",
                      "isampler1D", "isampler2D", "isampler3D",
                      "usampler1D", "usampler2D", "usampler3D"}
GLSL_QUALIFIERS = {"in", "out", "inout", "uniform", "varying", "attribute",
                   "const", "flat", "smooth", "noperspective", "centroid"}
GLSL_BUILTIN_TYPES = GLSL_SCALAR_TYPES | GLSL_VEC_TYPES | GLSL_MAT_TYPES | GLSL_SAMPLER_TYPES


class ShaderParser:
    """
    Parses GLSL source code and extracts structural information.

    This parser performs:
    - Version directive detection
    - Input/output/uniform variable extraction
    - Function signature parsing
    - Basic syntax validation
    - Extension handling
    """

    def __init__(self):
        self.info = ShaderInfo()

    def parse(self, source: str) -> ShaderInfo:
        """
        Parse GLSL source code and return shader information.

        Args:
            source: GLSL shader source code

        Returns:
            ShaderInfo containing parsed shader data
        """
        self.info = ShaderInfo()
        self.info.source_lines = source.split('\n')

        # Remove comments
        source = self._remove_comments(source)

        # Extract version directive
        self._extract_version(source)

        # Extract extensions
        self._extract_extensions(source)

        # Extract defines
        self._extract_defines(source)

        # Extract uniform declarations
        self._extract_uniforms(source)

        # Extract input/output variables
        self._extract_varyings(source)

        # Extract functions
        self._extract_functions(source)

        # Validate
        self._validate(source)

        return self.info

    def _remove_comments(self, source: str) -> str:
        """Remove single-line and multi-line comments."""
        # Remove multi-line comments
        source = re.sub(r'/\*.*?\*/', '', source, flags=re.DOTALL)
        # Remove single-line comments
        source = re.sub(r'//[^\n]*', '', source)
        return source

    def _extract_version(self, source: str):
        """Extract GLSL version directive."""
        match = re.search(r'#version\s+(\d+)\s*(\w+)?', source)
        if match:
            self.info.version = match.group(1)
            profile = match.group(2) or ""

    def _extract_extensions(self, source: str):
        """Extract extension directives."""
        for match in re.finditer(r'#extension\s+(\w+)\s*:\s*(\w+)', source):
            self.info.extensions.append(match.group(1))

    def _extract_defines(self, source: str):
        """Extract #define macros."""
        for match in re.finditer(r'#define\s+(\w+)\s*(.*?)$', source, re.MULTILINE):
            self.info.defines[match.group(1)] = match.group(2).strip()

    def _extract_uniforms(self, source: str):
        """Extract uniform variable declarations."""
        # Match: uniform type name; or uniform type name[size];
        pattern = r'uniform\s+(\w+)\s+(\w+)(?:\[(\d+)\])?\s*;'
        for match in re.finditer(pattern, source):
            var = ShaderVariable(
                type_name=match.group(1),
                name=match.group(2),
                qualifier="uniform",
                array_size=int(match.group(3)) if match.group(3) else None
            )
            self.info.uniforms.append(var)

        # Match struct-based uniforms (simplified)
        struct_pattern = r'uniform\s+(\w+)\s*\{[^}]*\}\s*(\w+)(?:\[(\d+)\])?\s*;'
        for match in re.finditer(struct_pattern, source, re.DOTALL):
            var = ShaderVariable(
                type_name=match.group(1),
                name=match.group(2),
                qualifier="uniform",
                array_size=int(match.group(3)) if match.group(3) else None
            )
            self.info.uniforms.append(var)

    def _extract_varyings(self, source: str):
        """Extract input (in) and output (out) variable declarations."""
        # Match in/out declarations
        pattern = r'(?:layout\s*\(\s*location\s*=\s*(\d+)\s*\)\s*)?(in|out)\s+(\w+)\s+(\w+)\s*;'
        for match in re.finditer(pattern, source):
            var = ShaderVariable(
                type_name=match.group(3),
                name=match.group(4),
                qualifier=match.group(2),
                location=int(match.group(1)) if match.group(1) else None
            )
            if match.group(2) == "in":
                self.info.inputs.append(var)
            else:
                self.info.outputs.append(var)

    def _extract_functions(self, source: str):
        """Extract function definitions."""
        # Match function definitions: type name(params) { body }
        # Allow leading whitespace before return type
        pattern = r'^\s*(\w+)\s+(\w+)\s*\(([^)]*)\)\s*\{'
        for match in re.finditer(pattern, source, re.MULTILINE):
            func = ShaderFunction(
                return_type=match.group(1),
                name=match.group(2),
                parameters=[p.strip() for p in match.group(3).split(',') if p.strip()],
                line_number=source[:match.start()].count('\n') + 1
            )
            self.info.functions.append(func)

    def _validate(self, source: str):
        """Perform basic syntax validation."""
        # Check for version directive
        if not self.info.version:
            self.info.warnings.append("No #version directive found")

        # Check for main function in vertex/fragment shaders
        main_found = any(f.name == "main" for f in self.info.functions)
        if not main_found:
            self.info.errors.append("No main() function found")

        # Check balanced braces
        open_braces = source.count('{')
        close_braces = source.count('}')
        if open_braces != close_braces:
            self.info.errors.append(
                f"Unbalanced braces: {open_braces} opening vs {close_braces} closing"
            )

        # Check balanced parentheses
        open_parens = source.count('(')
        close_parens = source.count(')')
        if open_parens != close_parens:
            self.info.errors.append(
                f"Unbalanced parentheses: {open_parens} opening vs {close_parens} closing"
            )

        # Check for deprecated keywords
        deprecated = {"varying", "attribute", "gl_FragColor"}
        for keyword in deprecated:
            if keyword in source:
                self.info.warnings.append(
                    f"Deprecated keyword '{keyword}' found - consider using in/out instead"
                )

    def detect_shader_type(self, source: str) -> Optional[ShaderType]:
        """
        Detect shader type from source content.

        Uses heuristics like:
        - File extension hints in comments
        - Presence of gl_Position (vertex shader)
        - Presence of FragColor/gl_FragColor output (fragment shader)
        """
        if "gl_Position" in source and "gl_Position" in source:
            # Check if there's also a fragment output
            if re.search(r'out\s+vec4\s+\w+', source):
                return ShaderType.VERTEX

        if re.search(r'out\s+vec4\s+(FragColor|gl_FragColor)', source):
            return ShaderType.FRAGMENT

        if "gl_Position" in source:
            return ShaderType.VERTEX

        return None


def parse_shader(source: str) -> ShaderInfo:
    """Convenience function to parse a shader source string."""
    parser = ShaderParser()
    return parser.parse(source)


def load_and_parse(filepath: str) -> ShaderInfo:
    """Load a shader file and parse it."""
    with open(filepath, 'r') as f:
        source = f.read()
    return parse_shader(source)
