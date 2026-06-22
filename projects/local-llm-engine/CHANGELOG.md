# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-06-18

### Added

#### Core Features
- GGUF model loader with full format support
- BPE and SentencePiece tokenizer implementations
- Transformer inference engine with RoPE position encoding
- KV Cache with multiple strategies (standard, sliding window, paged)
- Multiple sampling strategies (greedy, temperature, top-k, top-p, min-p)
- Beam search sampler
- Speculative decoding sampler

#### Engine
- Main LLMEngine class for single inference
- BatchLLMEngine for batch processing
- ContinuousBatchServer for production use
- Streaming output support
- Performance statistics

#### CLI Tools
- `llm_engine_cli` - Command line inference tool
- `chat` - Interactive chat interface
- `benchmark` - Performance benchmark tool

#### Testing
- Unit tests for tokenizer
- Unit tests for KV cache
- Unit tests for sampler
- Integration test support

#### Documentation
- README.md with project overview
- Market research document (01-RESEARCH.md)
- Requirements analysis (02-REQUIREMENTS.md)
- Technical design document (03-DESIGN.md)
- Product thinking document (04-PRODUCT.md)
- Development manual (05-DEVELOPMENT.md)
- Learning notes template
- Quick start guide
- Model download guide

#### Build System
- CMake build configuration
- Makefile for easy building
- Build script (build.sh)
- .gitignore file

### Known Limitations

- No GPU acceleration (planned for future)
- Limited model architecture support (LLaMA-style only)
- No distributed inference
- Performance not optimized for production use

## [Unreleased]

### Planned

- GPU acceleration (CUDA, Metal)
- More model architectures (GPT-2, BERT, etc.)
- Quantization improvements
- Memory optimization
- Documentation improvements
- More examples and tutorials

---

## Version History

- **1.0.0** (2026-06-18): Initial release with core functionality
- **0.1.0** (Development): Internal development version

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on how to contribute.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
