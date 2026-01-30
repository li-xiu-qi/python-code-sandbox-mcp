# Troubleshooting & Dev Notes

A summary of common issues encountered during development and CI/CD, and their solutions.

## 1. Linting & Formatting

### Issue: Ruff Check Failure
**Symptom**: CI `Lint and Format` step fails with `exit code 1`.
**Reason**:
- Unused imports (F401) or variables (F841).
- Bare `except:` blocks (E722).
- Code style inconsistencies.

**Solution**:
- Run `uv run ruff check . --fix` to fix logical issues.
- Run `uv run ruff format .` to format the code.

## 2. Docker Build

### Issue: Invalid `uv sync` Flag
**Symptom**: Error `unexpected argument '--system' found`.
**Reason**: `uv sync` does not support the `--system` flag directly.
**Solution**: Set `ENV UV_SYSTEM_PYTHON=1` in the Dockerfile instead.

### Issue: Missing README.md
**Symptom**: `hatchling` error `OSError: Readme file does not exist`.
**Reason**: The build backend requires the readme defined in `pyproject.toml`, but it wasn't copied yet.
**Solution**: Ensure `COPY README.md .` is executed before `uv sync`.

### Issue: Source Path Mapping (src layout)
**Symptom**: Error `ValueError: Unable to determine which files to ship`.
**Reason**: `hatchling` couldn't find the package in the `src/` directory automatically.
**Solution**: Add the following to `pyproject.toml`:
```toml
[tool.hatch.build.targets.wheel]
packages = ["src/python_code_sandbox_mcp"]
```

## 3. CI/CD (GitHub Actions)

### Issue: Missing `uv` Virtual Environment
**Symptom**: Error `No virtual environment found`.
**Reason**: Running `uv pip install` directly in CI without proper context.
**Solution**: Use `uv run <cmd>` to auto-manage a temporary environment.

### Issue: GitHub Actions Syntax Error (Unrecognized named-value: 'id')
**Symptom**: Error `Unrecognized named-value: 'id'` in `publish.yml`.
**Reason**: Using `${{ id.step_id.outputs }}` instead of the correct `steps` context.
**Solution**: Correct the expression to `${{ steps.step_id.outputs }}`.

### Issue: Docker Login Failure (Username and password required)
**Symptom**: `Login failed` error in the `publish.yml` step.
**Reason**: Missing `DOCKER_USERNAME` and `DOCKER_PASSWORD` in repository secrets.
**Solution**: Migrate to **GHCR** (GitHub Container Registry). It uses built-in `${{ github.actor }}` and `${{ secrets.GITHUB_TOKEN }}` for automatic authentication.

### Issue: GitHub Packages Permission Denied
**Symptom**: Error when pushing to `ghcr.io`.
**Reason**: Default `GITHUB_TOKEN` permissions are read-only.
**Solution**: Explicitly grant write access in the workflow job:
```yaml
permissions:
  packages: write
```

### Issue: Metadata Action Tag Error (Unknown tag type attribute: latest)
**Symptom**: Error `Unknown tag type attribute: latest`.
**Reason**: YAML parsing issues with multiline blocks or `type=latest` interpretation.
**Solution**: Use the more robust `type=raw,value=latest` definition.
