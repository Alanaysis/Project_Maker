"""
Tests for the Shader Library Manager

Validates loading, organization, and management of shader collections.
"""

import unittest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from utils.shader_library import ShaderLibrary, ShaderPass, ShaderEffect


class TestShaderLibraryLoading(unittest.TestCase):
    """Test shader loading functionality."""

    def setUp(self):
        self.shader_dir = os.path.join(os.path.dirname(__file__), '..', 'src')
        self.library = ShaderLibrary(self.shader_dir)

    def test_load_basic_shaders(self):
        """Should load all basic shaders."""
        self.assertIn("passthrough", self.library.shaders)
        self.assertIn("solid_color", self.library.shaders)
        self.assertIn("texture", self.library.shaders)
        self.assertIn("gradient", self.library.shaders)

    def test_load_lighting_shaders(self):
        """Should load all lighting shaders."""
        expected = ["ambient", "diffuse", "phong", "blinn_phong",
                    "directional", "point_light", "spotlight", "multi_light"]
        for name in expected:
            self.assertIn(name, self.library.shaders,
                         f"Lighting shader '{name}' not loaded")

    def test_load_postprocessing_shaders(self):
        """Should load all post-processing shaders."""
        expected = ["screen_quad", "grayscale", "sepia", "blur",
                    "edge_detection", "vignette", "chromatic_aberration",
                    "bloom", "hdr_tonemapping"]
        for name in expected:
            self.assertIn(name, self.library.shaders,
                         f"Post-processing shader '{name}' not loaded")

    def test_shader_count(self):
        """Should load expected number of shaders."""
        # 4 basic + 8 lighting + 9 postprocessing = 21
        self.assertGreaterEqual(len(self.library.shaders), 20)


class TestShaderLibraryValidation(unittest.TestCase):
    """Test shader validation through the library."""

    def setUp(self):
        self.shader_dir = os.path.join(os.path.dirname(__file__), '..', 'src')
        self.library = ShaderLibrary(self.shader_dir)

    def test_all_shaders_valid(self):
        """All shaders in the library should pass validation."""
        for name in self.library.shaders:
            valid, errors = self.library.validate_shader(name)
            self.assertTrue(valid,
                          f"Shader '{name}' failed validation: {errors}")

    def test_validate_nonexistent_shader(self):
        """Validating a non-existent shader should return error."""
        valid, errors = self.library.validate_shader("nonexistent")
        self.assertFalse(valid)
        self.assertTrue(any("not found" in e.lower() for e in errors))

    def test_passthrough_has_required_uniforms(self):
        """Passthrough vertex shader should have MVP uniforms."""
        uniforms = self.library.get_uniforms("passthrough")
        uniform_names = {u.name for u in uniforms}
        self.assertIn("model", uniform_names)
        self.assertIn("view", uniform_names)
        self.assertIn("projection", uniform_names)


class TestShaderLibraryPasses(unittest.TestCase):
    """Test shader pass creation."""

    def setUp(self):
        self.shader_dir = os.path.join(os.path.dirname(__file__), '..', 'src')
        self.library = ShaderLibrary(self.shader_dir)

    def test_create_basic_pass(self):
        """Should create a basic rendering pass."""
        pass_obj = self.library.create_pass(
            "basic_pass", "passthrough", "solid_color"
        )
        self.assertEqual(pass_obj.name, "basic_pass")
        self.assertTrue(pass_obj.valid)
        self.assertEqual(len(pass_obj.errors), 0)

    def test_create_phong_pass(self):
        """Should create a Phong lighting pass."""
        pass_obj = self.library.create_pass(
            "phong_pass", "passthrough", "phong"
        )
        self.assertTrue(pass_obj.valid)
        uniform_names = {u.name for u in pass_obj.uniforms.values()}
        self.assertIn("model", uniform_names)
        self.assertIn("lightPos", uniform_names)
        self.assertIn("shininess", uniform_names)

    def test_create_postprocess_pass(self):
        """Should create a post-processing pass."""
        pass_obj = self.library.create_pass(
            "grayscale_pass", "screen_quad", "grayscale"
        )
        self.assertTrue(pass_obj.valid)
        uniform_names = {u.name for u in pass_obj.uniforms.values()}
        self.assertIn("screenTexture", uniform_names)
        self.assertIn("intensity", uniform_names)

    def test_create_pass_invalid_vert(self):
        """Should fail when vertex shader doesn't exist."""
        with self.assertRaises(ValueError):
            self.library.create_pass("test", "nonexistent", "solid_color")

    def test_create_pass_invalid_frag(self):
        """Should fail when fragment shader doesn't exist."""
        with self.assertRaises(ValueError):
            self.library.create_pass("test", "passthrough", "nonexistent")


class TestShaderLibraryEffects(unittest.TestCase):
    """Test shader effect creation."""

    def setUp(self):
        self.shader_dir = os.path.join(os.path.dirname(__file__), '..', 'src')
        self.library = ShaderLibrary(self.shader_dir)

    def test_create_single_pass_effect(self):
        """Should create a single-pass effect."""
        effect = self.library.create_effect(
            name="solid_render",
            description="Solid color rendering",
            passes=[("main", "passthrough", "solid_color")],
            category="basic"
        )
        self.assertEqual(effect.name, "solid_render")
        self.assertEqual(len(effect.passes), 1)
        self.assertEqual(effect.category, "basic")

    def test_create_multi_pass_effect(self):
        """Should create a multi-pass effect."""
        effect = self.library.create_effect(
            name="bloom_effect",
            description="Bloom post-processing",
            passes=[
                ("bright_pass", "screen_quad", "bloom"),
                ("blur_pass", "screen_quad", "blur"),
                ("combine_pass", "screen_quad", "bloom"),
            ],
            category="postprocessing"
        )
        self.assertEqual(len(effect.passes), 3)

    def test_create_phong_lighting_effect(self):
        """Should create a Phong lighting effect."""
        effect = self.library.create_effect(
            name="phong_lighting",
            description="Phong lighting model",
            passes=[("main", "passthrough", "phong")],
            category="lighting"
        )
        self.assertTrue(effect.passes[0].valid)

    def test_effects_stored_in_library(self):
        """Created effects should be stored in the library."""
        self.library.create_effect(
            name="test_effect",
            description="Test",
            passes=[("main", "passthrough", "solid_color")]
        )
        self.assertIn("test_effect", self.library.effects)


class TestShaderLibraryList(unittest.TestCase):
    """Test shader listing functionality."""

    def setUp(self):
        self.shader_dir = os.path.join(os.path.dirname(__file__), '..', 'src')
        self.library = ShaderLibrary(self.shader_dir)

    def test_list_shaders(self):
        """Should list all loaded shaders with metadata."""
        shader_list = self.library.list_shaders()
        self.assertGreater(len(shader_list), 0)

        # Check structure of list items
        for item in shader_list:
            self.assertIn("name", item)
            self.assertIn("type", item)
            self.assertIn("version", item)
            self.assertIn("uniforms", item)
            self.assertIn("errors", item)

    def test_list_includes_shader_types(self):
        """List should include both vertex and fragment shaders."""
        shader_list = self.library.list_shaders()
        types = {s["type"] for s in shader_list}
        self.assertIn("VERTEX", types)
        self.assertIn("FRAGMENT", types)


class TestShaderLibraryStringLoading(unittest.TestCase):
    """Test loading shaders from strings."""

    def setUp(self):
        self.library = ShaderLibrary()

    def test_load_from_string(self):
        """Should load a shader from a source string."""
        source = """
        #version 330 core
        uniform float time;
        out vec4 FragColor;
        void main() {
            FragColor = vec4(sin(time), 0.0, 0.0, 1.0);
        }
        """
        info = self.library.load_from_string("test_shader", source,
                                              shader_type=None)
        self.assertIn("test_shader", self.library.shaders)
        self.assertEqual(len(info.uniforms), 1)
        self.assertEqual(info.uniforms[0].name, "time")

    def test_load_vertex_from_string(self):
        """Should load a vertex shader from string with type hint."""
        source = """
        #version 330 core
        layout(location = 0) in vec3 aPos;
        void main() {
            gl_Position = vec4(aPos, 1.0);
        }
        """
        from utils.shader_parser import ShaderType
        info = self.library.load_from_string("test_vert", source,
                                              ShaderType.VERTEX)
        self.assertEqual(info.shader_type, ShaderType.VERTEX)


class TestShaderLibraryGetSource(unittest.TestCase):
    """Test source code retrieval."""

    def setUp(self):
        self.shader_dir = os.path.join(os.path.dirname(__file__), '..', 'src')
        self.library = ShaderLibrary(self.shader_dir)

    def test_get_existing_source(self):
        """Should return source for loaded shader."""
        source = self.library.get_shader_source("passthrough")
        self.assertIsNotNone(source)
        self.assertIn("gl_Position", source)

    def test_get_nonexistent_source(self):
        """Should return None for non-existent shader."""
        source = self.library.get_shader_source("nonexistent")
        self.assertIsNone(source)

    def test_get_errors(self):
        """Should return errors list for shader."""
        errors = self.library.get_errors("passthrough")
        self.assertIsInstance(errors, list)

    def test_get_errors_nonexistent(self):
        """Should return error message for non-existent shader."""
        errors = self.library.get_errors("nonexistent")
        self.assertTrue(any("not found" in e.lower() for e in errors))


if __name__ == '__main__':
    unittest.main()
