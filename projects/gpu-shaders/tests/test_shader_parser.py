"""
Tests for the GLSL Shader Parser

Validates that the parser correctly extracts shader information
including uniforms, inputs, outputs, functions, and performs
basic syntax validation.
"""

import unittest
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from utils.shader_parser import ShaderParser, ShaderType, parse_shader


class TestShaderParserVersion(unittest.TestCase):
    """Test version directive parsing."""

    def test_parse_version_330(self):
        source = "#version 330 core\nvoid main() {}"
        info = parse_shader(source)
        self.assertEqual(info.version, "330")

    def test_parse_version_300_es(self):
        source = "#version 300 es\nvoid main() {}"
        info = parse_shader(source)
        self.assertEqual(info.version, "300")

    def test_no_version_warning(self):
        source = "void main() {}"
        info = parse_shader(source)
        self.assertTrue(any("version" in w.lower() for w in info.warnings))

    def test_version_450(self):
        source = "#version 450\nvoid main() {}"
        info = parse_shader(source)
        self.assertEqual(info.version, "450")


class TestShaderParserUniforms(unittest.TestCase):
    """Test uniform variable extraction."""

    def test_single_uniform(self):
        source = "uniform float time;\nvoid main() {}"
        info = parse_shader(source)
        self.assertEqual(len(info.uniforms), 1)
        self.assertEqual(info.uniforms[0].name, "time")
        self.assertEqual(info.uniforms[0].type_name, "float")
        self.assertEqual(info.uniforms[0].qualifier, "uniform")

    def test_multiple_uniforms(self):
        source = """
        uniform vec3 lightPos;
        uniform vec3 viewPos;
        uniform mat4 model;
        uniform float intensity;
        void main() {}
        """
        info = parse_shader(source)
        self.assertEqual(len(info.uniforms), 4)
        names = {u.name for u in info.uniforms}
        self.assertEqual(names, {"lightPos", "viewPos", "model", "intensity"})

    def test_array_uniform(self):
        source = "uniform vec3 lights[4];\nvoid main() {}"
        info = parse_shader(source)
        self.assertEqual(len(info.uniforms), 1)
        self.assertEqual(info.uniforms[0].name, "lights")
        self.assertEqual(info.uniforms[0].array_size, 4)

    def test_sampler_uniform(self):
        source = "uniform sampler2D textureSampler;\nvoid main() {}"
        info = parse_shader(source)
        self.assertEqual(len(info.uniforms), 1)
        self.assertEqual(info.uniforms[0].type_name, "sampler2D")

    def test_mat4_uniform(self):
        source = """
        uniform mat4 model;
        uniform mat4 view;
        uniform mat4 projection;
        void main() {}
        """
        info = parse_shader(source)
        self.assertEqual(len(info.uniforms), 3)
        for u in info.uniforms:
            self.assertEqual(u.type_name, "mat4")


class TestShaderParserInputsOutputs(unittest.TestCase):
    """Test input/output variable extraction."""

    def test_input_with_location(self):
        source = "layout(location = 0) in vec3 aPos;\nvoid main() {}"
        info = parse_shader(source)
        self.assertEqual(len(info.inputs), 1)
        self.assertEqual(info.inputs[0].name, "aPos")
        self.assertEqual(info.inputs[0].location, 0)
        self.assertEqual(info.inputs[0].type_name, "vec3")

    def test_multiple_inputs(self):
        source = """
        layout(location = 0) in vec3 aPos;
        layout(location = 1) in vec3 aNormal;
        layout(location = 2) in vec2 aTexCoord;
        void main() {}
        """
        info = parse_shader(source)
        self.assertEqual(len(info.inputs), 3)
        names = {v.name for v in info.inputs}
        self.assertEqual(names, {"aPos", "aNormal", "aTexCoord"})

    def test_output_variable(self):
        source = "out vec4 FragColor;\nvoid main() { FragColor = vec4(1.0); }"
        info = parse_shader(source)
        self.assertEqual(len(info.outputs), 1)
        self.assertEqual(info.outputs[0].name, "FragColor")
        self.assertEqual(info.outputs[0].type_name, "vec4")


class TestShaderParserFunctions(unittest.TestCase):
    """Test function extraction."""

    def test_main_function(self):
        source = "void main() { gl_Position = vec4(0.0); }"
        info = parse_shader(source)
        self.assertEqual(len(info.functions), 1)
        self.assertEqual(info.functions[0].name, "main")
        self.assertEqual(info.functions[0].return_type, "void")

    def test_function_with_params(self):
        source = """
        vec3 calcLight(vec3 norm, vec3 lightDir) {
            return max(dot(norm, lightDir), 0.0) * vec3(1.0);
        }
        void main() {}
        """
        info = parse_shader(source)
        self.assertEqual(len(info.functions), 2)
        calc_func = next(f for f in info.functions if f.name == "calcLight")
        self.assertEqual(calc_func.return_type, "vec3")
        self.assertEqual(len(calc_func.parameters), 2)

    def test_function_with_return(self):
        source = """
        float luminance(vec3 color) {
            return dot(color, vec3(0.2126, 0.7152, 0.0722));
        }
        void main() {}
        """
        info = parse_shader(source)
        lum_func = next(f for f in info.functions if f.name == "luminance")
        self.assertEqual(lum_func.return_type, "float")


class TestShaderParserComments(unittest.TestCase):
    """Test comment handling."""

    def test_single_line_comment(self):
        source = """
        // This is a comment
        uniform float time;
        void main() {}
        """
        info = parse_shader(source)
        self.assertEqual(len(info.uniforms), 1)

    def test_multi_line_comment(self):
        source = """
        /* This is a
           multi-line comment */
        uniform float time;
        void main() {}
        """
        info = parse_shader(source)
        self.assertEqual(len(info.uniforms), 1)

    def test_inline_comment(self):
        source = """
        uniform float time; // Time uniform
        void main() {}
        """
        info = parse_shader(source)
        self.assertEqual(len(info.uniforms), 1)


class TestShaderParserValidation(unittest.TestCase):
    """Test syntax validation."""

    def test_missing_main(self):
        source = "uniform float time;"
        info = parse_shader(source)
        self.assertTrue(any("main" in e.lower() for e in info.errors))

    def test_unbalanced_braces(self):
        source = "void main() {"
        info = parse_shader(source)
        self.assertTrue(any("brace" in e.lower() for e in info.errors))

    def test_unbalanced_parentheses(self):
        source = "void main() { float x = (1.0 + 2.0; }"
        info = parse_shader(source)
        self.assertTrue(any("parenthes" in e.lower() for e in info.errors))

    def test_valid_shader(self):
        source = """
        #version 330 core
        out vec4 FragColor;
        void main() {
            FragColor = vec4(1.0, 0.0, 0.0, 1.0);
        }
        """
        info = parse_shader(source)
        self.assertEqual(len(info.errors), 0)

    def test_deprecated_keyword_warning(self):
        source = """
        varying vec3 color;
        void main() {}
        """
        info = parse_shader(source)
        self.assertTrue(any("deprecated" in w.lower() for w in info.warnings))


class TestShaderParserDefines(unittest.TestCase):
    """Test #define extraction."""

    def test_simple_define(self):
        source = """
        #define MAX_LIGHTS 4
        void main() {}
        """
        info = parse_shader(source)
        self.assertIn("MAX_LIGHTS", info.defines)
        self.assertEqual(info.defines["MAX_LIGHTS"], "4")

    def test_expression_define(self):
        source = """
        #define PI 3.14159265
        void main() {}
        """
        info = parse_shader(source)
        self.assertIn("PI", info.defines)
        self.assertEqual(info.defines["PI"], "3.14159265")


class TestShaderTypeDetection(unittest.TestCase):
    """Test shader type detection."""

    def test_detect_vertex_shader(self):
        parser = ShaderParser()
        source = """
        layout(location = 0) in vec3 aPos;
        void main() {
            gl_Position = vec4(aPos, 1.0);
        }
        """
        shader_type = parser.detect_shader_type(source)
        self.assertEqual(shader_type, ShaderType.VERTEX)

    def test_detect_fragment_shader(self):
        parser = ShaderParser()
        source = """
        out vec4 FragColor;
        void main() {
            FragColor = vec4(1.0);
        }
        """
        shader_type = parser.detect_shader_type(source)
        self.assertEqual(shader_type, ShaderType.FRAGMENT)


class TestRealShaderParsing(unittest.TestCase):
    """Test parsing actual shader files from the library."""

    def _load_shader(self, relative_path):
        base_dir = os.path.join(os.path.dirname(__file__), '..', 'src')
        filepath = os.path.join(base_dir, relative_path)
        with open(filepath, 'r') as f:
            return f.read()

    def test_parse_passthrough_vertex(self):
        source = self._load_shader('basic/passthrough.vert')
        info = parse_shader(source)
        self.assertEqual(info.version, "330")
        self.assertTrue(any(f.name == "main" for f in info.functions))
        self.assertTrue(any(u.name == "model" for u in info.uniforms))
        self.assertTrue(any(u.name == "view" for u in info.uniforms))
        self.assertTrue(any(u.name == "projection" for u in info.uniforms))

    def test_parse_solid_color_fragment(self):
        source = self._load_shader('basic/solid_color.frag')
        info = parse_shader(source)
        self.assertTrue(any(u.name == "color" for u in info.uniforms))
        self.assertTrue(any(v.name == "FragColor" for v in info.outputs))

    def test_parse_texture_fragment(self):
        source = self._load_shader('basic/texture.frag')
        info = parse_shader(source)
        uniform_names = {u.name for u in info.uniforms}
        self.assertIn("textureSampler", uniform_names)
        self.assertIn("tintColor", uniform_names)
        self.assertIn("tintStrength", uniform_names)

    def test_parse_phong_fragment(self):
        source = self._load_shader('lighting/phong.frag')
        info = parse_shader(source)
        uniform_names = {u.name for u in info.uniforms}
        self.assertIn("lightPos", uniform_names)
        self.assertIn("lightColor", uniform_names)
        self.assertIn("objectColor", uniform_names)
        self.assertIn("viewPos", uniform_names)
        self.assertIn("shininess", uniform_names)

    def test_parse_grayscale_fragment(self):
        source = self._load_shader('postprocessing/grayscale.frag')
        info = parse_shader(source)
        uniform_names = {u.name for u in info.uniforms}
        self.assertIn("screenTexture", uniform_names)
        self.assertIn("intensity", uniform_names)

    def test_parse_multi_light_fragment(self):
        source = self._load_shader('lighting/multi_light.frag')
        info = parse_shader(source)
        # Should have defines for MAX_POINT_LIGHTS and MAX_SPOT_LIGHTS
        self.assertIn("MAX_POINT_LIGHTS", info.defines)
        self.assertEqual(info.defines["MAX_POINT_LIGHTS"], "4")
        self.assertIn("MAX_SPOT_LIGHTS", info.defines)
        self.assertEqual(info.defines["MAX_SPOT_LIGHTS"], "2")

    def test_parse_bloom_fragment(self):
        source = self._load_shader('postprocessing/bloom.frag')
        info = parse_shader(source)
        uniform_names = {u.name for u in info.uniforms}
        self.assertIn("screenTexture", uniform_names)
        self.assertIn("bloomTexture", uniform_names)
        self.assertIn("bloomThreshold", uniform_names)
        self.assertIn("bloomIntensity", uniform_names)

    def test_parse_hdr_tonemapping_fragment(self):
        source = self._load_shader('postprocessing/hdr_tonemapping.frag')
        info = parse_shader(source)
        uniform_names = {u.name for u in info.uniforms}
        self.assertIn("exposure", uniform_names)
        self.assertIn("tonemapOperator", uniform_names)
        # Should have helper functions
        func_names = {f.name for f in info.functions}
        self.assertIn("reinhard", func_names)
        self.assertIn("aces", func_names)
        self.assertIn("uncharted2", func_names)

    def test_parse_edge_detection_fragment(self):
        source = self._load_shader('postprocessing/edge_detection.frag')
        info = parse_shader(source)
        uniform_names = {u.name for u in info.uniforms}
        self.assertIn("edgeStrength", uniform_names)
        self.assertIn("edgeColor", uniform_names)

    def test_parse_spotlight_fragment(self):
        source = self._load_shader('lighting/spotlight.frag')
        info = parse_shader(source)
        uniform_names = {u.name for u in info.uniforms}
        self.assertIn("innerCutoff", uniform_names)
        self.assertIn("outerCutoff", uniform_names)
        self.assertIn("constant", uniform_names)
        self.assertIn("linear", uniform_names)
        self.assertIn("quadratic", uniform_names)


class TestAllShadersParseWithoutErrors(unittest.TestCase):
    """Verify all shader files in the library parse without errors."""

    def _load_all_shaders(self):
        base_dir = os.path.join(os.path.dirname(__file__), '..', 'src')
        shaders = []
        for root, dirs, files in os.walk(base_dir):
            # Skip utils directory
            if 'utils' in root:
                continue
            for f in files:
                if f.endswith(('.vert', '.frag', '.glsl')):
                    filepath = os.path.join(root, f)
                    with open(filepath, 'r') as fh:
                        source = fh.read()
                    rel_path = os.path.relpath(filepath, base_dir)
                    shaders.append((rel_path, source))
        return shaders

    def test_all_shaders_have_main(self):
        shaders = self._load_all_shaders()
        self.assertGreater(len(shaders), 0, "No shaders found")
        for path, source in shaders:
            info = parse_shader(source)
            has_main = any(f.name == "main" for f in info.functions)
            self.assertTrue(has_main, f"Shader {path} missing main()")

    def test_all_shaders_balanced_braces(self):
        shaders = self._load_all_shaders()
        for path, source in shaders:
            info = parse_shader(source)
            brace_errors = [e for e in info.errors if "brace" in e.lower()]
            self.assertEqual(len(brace_errors), 0,
                           f"Shader {path} has brace errors: {brace_errors}")

    def test_all_shaders_balanced_parens(self):
        shaders = self._load_all_shaders()
        for path, source in shaders:
            info = parse_shader(source)
            paren_errors = [e for e in info.errors if "parenthes" in e.lower()]
            self.assertEqual(len(paren_errors), 0,
                           f"Shader {path} has parenthesis errors: {paren_errors}")


if __name__ == '__main__':
    unittest.main()
