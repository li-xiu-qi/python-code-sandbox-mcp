# Changelog

## [0.1.0] - 2026-01-29

### Added
- **Production-ready Core**: Secure Python execution sandbox using Docker isolation.
- **One-Shot Mode**: `run_python_ephemeral` tool for instant script execution and file retrieval.
- **Session Support**: `sandbox_initialize` and `run_python` for persistent stateful environments.
- **Dependency Management**: Automated pip package installation with persistence via `PIP_CACHE_PATH`.
- **Security Features**: Base64 code injection, resource limits (CPU/Memory), and non-root execution.
- **Multi-Arch Docker**: Full support for `amd64` and `arm64` via Dockerfile and CI/CD.
- **Documentation**: Comprehensive bilingual (EN/ZH) documentation including USAGE, ARCHITECTURE, SECURITY, and TROUBLESHOOTING.
- **CI/CD**: Automated linting, unit testing, and Docker image publishing workflows.
