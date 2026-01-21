# Contributing to MemGraph

Thank you for your interest in contributing to MemGraph! This document provides guidelines for contributing to the project.

## Development Setup

1. Fork and clone the repository:
   ```bash
   git clone https://github.com/your-username/memgraph.git
   cd memgraph
   ```

2. Install in development mode with all dependencies:
   ```bash
   pip install -e ".[dev]"
   ```

3. Verify installation:
   ```bash
   pytest
   mypy src/memgraph
   ```

## Making Changes

1. Create a new branch for your feature or fix:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. Make your changes

3. Ensure all tests pass:
   ```bash
   pytest
   ```

4. Run type checking:
   ```bash
   mypy src/memgraph
   ```

5. Check test coverage:
   ```bash
   pytest --cov=memgraph --cov-report=term-missing
   ```

6. Commit your changes with clear, descriptive commit messages

7. Push to your fork and submit a pull request

## Code Style

- Follow PEP 8 style guidelines
- Use type hints for all functions
- Write docstrings for public functions and classes
- Keep functions focused and modular

Example docstring format:
```python
def my_function(param1: int, param2: str) -> bool:
    """
    Brief description of what the function does.

    Args:
        param1: Description of param1
        param2: Description of param2

    Returns:
        Description of return value

    Raises:
        ValueError: When something goes wrong

    Example:
        >>> my_function(42, "hello")
        True
    """
    pass
```

## Adding New Patterns

To add a new reference pattern to the classifier:

1. Edit `src/memgraph/classifier/patterns.py`

2. Define the canonical graphlet signature:
   ```python
   ReferencePattern(
       name="MY_PATTERN",
       signature=GraphletSignature(...),
       characteristics=[
           "Description of pattern characteristics",
       ],
       recommendations=[
           "Optimization recommendations",
       ]
   )
   ```

3. Add tests in `tests/test_classifier.py`:
   ```python
   def test_my_pattern_classification():
       # Test that pattern is correctly classified
       pass
   ```

4. Add example C program in `examples/my_pattern.c`

5. Update documentation in `docs/patterns.md`

## Testing

- Write tests for all new features
- Ensure existing tests still pass
- Aim for >80% code coverage
- Test edge cases and error conditions

Run specific tests:
```bash
pytest tests/test_classifier.py::test_specific_function
```

## Documentation

- Update README.md if adding user-facing features
- Add docstrings to new functions
- Update relevant documentation in `docs/`
- Include examples in docstrings when helpful

## Pull Request Guidelines

- Keep PRs focused on a single feature or fix
- Include tests for new functionality
- Update documentation as needed
- Provide a clear description of changes
- Reference any related issues

### PR Description Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
Describe testing performed

## Checklist
- [ ] Tests pass locally
- [ ] Type checking passes
- [ ] Documentation updated
- [ ] Code follows project style
```

## Reporting Issues

When reporting bugs, please include:

1. MemGraph version: `python -c "import memgraph; print(memgraph.__version__)"`
2. Python version: `python --version`
3. Operating system
4. Steps to reproduce
5. Expected behavior
6. Actual behavior
7. Relevant trace files or code samples (if applicable)

## Feature Requests

Feature requests are welcome! Please:

1. Check existing issues first to avoid duplicates
2. Provide a clear use case
3. Describe the expected behavior
4. Consider potential implementation approaches

## Questions

For questions about using MemGraph:

1. Check the [documentation](docs/)
2. Search existing [issues](https://github.com/jimmybentley/memgraph/issues)
3. Open a new issue with the "question" label

## Code of Conduct

- Be respectful and professional
- Welcome newcomers and be patient with questions
- Focus on constructive feedback
- Assume good intentions

## License

By contributing to MemGraph, you agree that your contributions will be licensed under the MIT License.
