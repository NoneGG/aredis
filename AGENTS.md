# AGENTS.md

This file provides context and guidelines for AI agents working on the `aredis` repository.

## Project Overview

`aredis` is an efficient and user-friendly async Redis client for Python, ported from `redis-py`. It allows interaction with Redis using Python's `asyncio` framework.

## Development Guidelines

### Language and Style
- **Language**: Python (supports Python 3.8+).
- **Style**: Follow PEP 8 coding standards.
- **Asyncio**: This is an asynchronous library. Ensure all I/O operations are non-blocking and use `async`/`await` syntax where appropriate.

### Code Structure
- **Source Code**: Located in the `aredis/` directory.
- **Tests**: Located in the `tests/` directory.
- **Benchmarks**: Located in the `benchmarks/` directory.
- **Documentation**: Located in the `docs/` directory (Sphinx-based).
- **Examples**: Usage examples are in the `examples/` directory.

## Testing

- The project uses `pytest` for testing.
- Run tests using `pytest` or `python setup.py test`.
- Ensure new features or bug fixes include appropriate test coverage in the `tests/` directory.
- For performance-critical changes, consider running scripts in `benchmarks/` to ensure no regression.

## Documentation

- Documentation is written in reStructuredText (`.rst`) and built with Sphinx.
- Update documentation in `docs/source/` when adding new features or changing public APIs.

## Dependencies

- Core dependencies are listed in `setup.py`.
- Development dependencies are in `dev_requirements.txt`.
- Test dependencies are in `test_requirements.txt`.

## Contribution

- When creating Pull Requests, ensure the code is clean, tested, and documented.
- Check `dev_requirements.txt` and `test_requirements.txt` for necessary tools.
