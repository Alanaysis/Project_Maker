# Testing: GPU Shader Library

## 1. Testing Strategy

### Testing Layers
1. **Unit Tests**: Individual parser and library functions
2. **Integration Tests**: End-to-end shader loading and validation
3. **Shader Tests**: All shaders parse correctly and have valid structure

### Test Environment
- Pure Python tests (no GPU required)
- Uses unittest framework
- Tests run against actual shader files in `src/`

## 2. Test Categories

### Shader Parser Tests (test_shader_parser.py)

#### Version Parsing Tests
- `test_parse_version_330`: Standard GLSL 330 core
- `test_parse_version_300_es`: OpenGL ES 3.0
- `test_no_version_warning`: Missing version generates warning
- `test_version_450`: GLSL 4.50

#### Uniform Extraction Tests
- `test_single_uniform`: Basic float uniform
- `test_multiple_uniforms`: Various types (vec3, mat4, float)
- `test_array_uniform`: Array uniforms with size
- `test_sampler_uniform`: Texture sampler uniforms
- `test_mat4_uniform`: Matrix uniform types

#### Input/Output Tests
- `test_input_with_location`: Layout location qualifier
- `test_multiple_inputs`: Vertex attributes (position, normal, texcoord)
- `test_output_variable`: Fragment shader output

#### Function Tests
- `test_main_function`: Main entry point detection
- `test_function_with_params`: Functions with parameters
- `test_function_with_return`: Return type detection

#### Comment Handling Tests
- `test_single_line_comment`: `//` comments
- `test_multi_line_comment`: `/* */` comments
- `test_inline_comment`: Comments after code

#### Validation Tests
- `test_missing_main`: Error when no main()
- `test_unbalanced_braces`: Error on `{` without `}`
- `test_unbalanced_parentheses`: Error on `(` without `)`
- `test_valid_shader`: Valid shader passes validation
- `test_deprecated_keyword_warning`: Warning for old keywords

#### Define Tests
- `test_simple_define`: `#define MAX_LIGHTS 4`
- `test_expression_define`: `#define PI 3.14159`

#### Type Detection Tests
- `test_detect_vertex_shader`: Identifies vertex shaders
- `test_detect_fragment_shader`: Identifies fragment shaders

### Shader Library Tests (test_shader_library.py)

#### Loading Tests
- `test_load_basic_shaders`: Loads all basic shaders
- `test_load_lighting_shaders`: Loads all lighting shaders
- `test_load_postprocessing_shaders`: Loads all post-processing shaders
- `test_shader_count`: Expected number of shaders loaded

#### Validation Tests
- `test_all_shaders_valid`: All loaded shaders pass validation
- `test_validate_nonexistent_shader`: Error for missing shader
- `test_passthrough_has_required_uniforms`: MVP uniforms present

#### Pass Creation Tests
- `test_create_basic_pass`: Basic vertex + fragment pass
- `test_create_phong_pass`: Phong lighting pass with all uniforms
- `test_create_postprocess_pass`: Post-processing pass
- `test_create_pass_invalid_vert`: Error for missing vertex shader
- `test_create_pass_invalid_frag`: Error for missing fragment shader

#### Effect Creation Tests
- `test_create_single_pass_effect`: Single-pass effect
- `test_create_multi_pass_effect`: Multi-pass bloom effect
- `test_create_phong_lighting_effect`: Lighting effect
- `test_effects_stored_in_library`: Effects persist in library

#### Listing Tests
- `test_list_shaders`: Returns all shaders with metadata
- `test_list_includes_shader_types`: Includes VERTEX and FRAGMENT

#### String Loading Tests
- `test_load_from_string`: Load shader from source string
- `test_load_vertex_from_string`: Load with type hint

#### Source Retrieval Tests
- `test_get_existing_source`: Returns source for loaded shader
- `test_get_nonexistent_source`: Returns None for missing
- `test_get_errors`: Returns error list
- `test_get_errors_nonexistent`: Returns error for missing shader

### Integration Tests (test_shader_parser.py)

#### Real Shader Parsing Tests
- `test_parse_passthrough_vertex`: Actual passthrough shader
- `test_parse_solid_color_fragment`: Actual solid color shader
- `test_parse_texture_fragment`: Actual texture shader
- `test_parse_phong_fragment`: Actual Phong shader
- `test_parse_grayscale_fragment`: Actual grayscale shader
- `test_parse_multi_light_fragment`: Multi-light with defines
- `test_parse_bloom_fragment`: Bloom with multiple textures
- `test_parse_hdr_tonemapping_fragment`: HDR with helper functions
- `test_parse_edge_detection_fragment`: Edge detection with uniforms
- `test_parse_spotlight_fragment`: Spotlight with all parameters

#### All Shaders Validation Tests
- `test_all_shaders_have_main`: Every shader has main()
- `test_all_shaders_balanced_braces`: All braces balanced
- `test_all_shaders_balanced_parens`: All parentheses balanced

## 3. Running Tests

### Run All Tests
```bash
cd projects/gpu-shaders
python3 -m pytest tests/ -v
```

### Run Specific Test File
```bash
python3 -m pytest tests/test_shader_parser.py -v
python3 -m pytest tests/test_shader_library.py -v
```

### Run Specific Test Class
```bash
python3 -m pytest tests/test_shader_parser.py::TestShaderParserUniforms -v
```

### Run with Coverage
```bash
python3 -m pytest tests/ -v --cov=src/utils
```

## 4. Test Coverage Goals

| Component | Target Coverage |
|-----------|----------------|
| Shader Parser | 95%+ |
| Shader Library | 90%+ |
| All Shaders | 100% parse success |

## 5. Continuous Validation

### Pre-commit Checks
- All tests pass
- All shaders parse without errors
- No deprecated keywords in new shaders

### Regression Prevention
- Adding new shaders triggers validation of all existing shaders
- Parser changes trigger full test suite
- Library changes trigger integration tests
