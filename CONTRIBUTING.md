# Contributing to Agent Foundry

Thank you for your interest in contributing to Agent Foundry! This document provides guidelines and steps for contributing.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Making Contributions](#making-contributions)
- [Pull Request Process](#pull-request-process)
- [Coding Standards](#coding-standards)
- [Testing Guidelines](#testing-guidelines)
- [Documentation](#documentation)

## Code of Conduct

By participating in this project, you agree to abide by our [Code of Conduct](CODE_OF_CONDUCT.md). Please read it before contributing.

## Getting Started

1. Fork the repository on GitHub
2. Clone your fork locally:
   ```bash
   git clone https://github.com/YOUR_USERNAME/Agent-Foundry.git
   cd Agent-Foundry
   ```
3. Add the upstream repository:
   ```bash
   git remote add upstream https://github.com/wildhash/Agent-Foundry.git
   ```

## Development Setup

### Prerequisites

- Python 3.9+
- Node.js 18+
- Docker and Docker Compose (optional, for containerized development)
- Poetry (recommended for Python dependency management)

### Backend Setup

```bash
cd backend

# Using Poetry (recommended)
poetry install

# Or using pip
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Install development dependencies
pip install flake8 black pytest pytest-cov
```

### Frontend Setup

```bash
cd frontend
npm install
```

### Pre-commit Hooks

Install pre-commit hooks to ensure code quality:

```bash
pip install pre-commit
pre-commit install
```

## Making Contributions

### Branching Strategy

- Create a new branch for each feature or bug fix
- Use descriptive branch names:
  - `feature/add-new-agent-type`
  - `fix/resolve-memory-leak`
  - `docs/update-api-reference`

```bash
git checkout -b feature/your-feature-name
```

### Commit Messages

Follow these conventions for commit messages:

- Use the present tense ("Add feature" not "Added feature")
- Use the imperative mood ("Move cursor to..." not "Moves cursor to...")
- Limit the first line to 72 characters
- Reference issues and pull requests when relevant

Example:
```
Add reflexion loop optimization for coder agent

- Implement caching for repeated code patterns
- Reduce memory usage by 30%
- Add unit tests for new functionality

Fixes #123
```

## Pull Request Process

1. **Update your branch** with the latest changes from upstream:
   ```bash
   git fetch upstream
   git rebase upstream/main
   ```

2. **Run tests** to ensure your changes don't break existing functionality:
   ```bash
   cd backend
   pytest --cov=. tests/
   ```

3. **Run linters** to ensure code quality:
   ```bash
   flake8 .
   black --check .
   ```

4. **Push your changes** to your fork:
   ```bash
   git push origin feature/your-feature-name
   ```

5. **Create a Pull Request** on GitHub:
   - Fill out the PR template completely
   - Link any related issues
   - Request reviews from maintainers

6. **Address review feedback** and update your PR as needed

## Coding Standards

### Python

- Follow [PEP 8](https://pep8.org/) style guidelines
- Use [Black](https://black.readthedocs.io/) for code formatting
- Use [flake8](https://flake8.pycqa.org/) for linting
- Use type hints for function signatures
- Write docstrings for all public functions and classes

Example:
```python
def process_agent_output(
    output: str,
    max_length: int = 1000,
    sanitize: bool = True
) -> dict[str, Any]:
    """
    Process and validate agent output.

    Args:
        output: Raw output string from agent
        max_length: Maximum allowed output length
        sanitize: Whether to sanitize the output

    Returns:
        Processed output dictionary with status and data

    Raises:
        ValueError: If output exceeds max_length
    """
    ...
```

### TypeScript/JavaScript

- Follow ESLint configuration in the project
- Use TypeScript for type safety
- Use meaningful variable and function names

## Testing Guidelines

### Writing Tests

- Write tests for all new features and bug fixes
- Place tests in the appropriate `tests/` directory
- Use descriptive test names that explain what is being tested

Example:
```python
def test_architect_agent_generates_valid_architecture():
    """Test that architect agent produces valid system architecture."""
    agent = ArchitectAgent()
    result = agent.design("Build a REST API")
    
    assert result.status == "success"
    assert "components" in result.architecture
    assert len(result.architecture["components"]) > 0
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=. --cov-report=html

# Run specific test file
pytest tests/test_agents.py

# Run tests matching a pattern
pytest -k "test_architect"
```

## Documentation

- Update documentation for any user-facing changes
- Add docstrings to new functions and classes
- Update README.md if adding new features
- Add API documentation for new endpoints

## Questions?

If you have questions about contributing, please:

1. Check existing issues and discussions
2. Open a new issue with your question
3. Join our community discussions

Thank you for contributing to Agent Foundry! 🚀
