# Sprint 10 Testing Guide

## Quick Start

### Install Dependencies
```bash
pip install -r requirements.txt
```

### Run All Tests
```bash
pytest -v
```

### Run with Coverage
```bash
pytest --cov=app --cov=website --cov-report=html --cov-report=term-missing
```

## Test Categories

### 1. Unit Tests
```bash
pytest tests/unit -v
pytest -m unit
```

### 2. Integration Tests
```bash
pytest tests/integration -v
pytest -m integration
```

### 3. Performance Tests
```bash
# Benchmarks
pytest tests/performance/benchmark.py -v -s

# Load testing
locust -f tests/performance/locustfile.py --host=http://localhost:5000
```

### 4. Security Tests
```bash
pytest tests/security -v
pytest -m security
```

## Coverage Report

```bash
# Generate HTML coverage report
pytest --cov=app --cov=website --cov-report=html

# View report
open htmlcov/index.html  # macOS/Linux
start htmlcov/index.html  # Windows
```

## CI/CD

Tests run automatically on GitHub Actions for every push and pull request.

**Coverage Target**: 80%+

## Health Checks

```bash
# Full health check
curl http://localhost:5000/health

# Readiness check
curl http://localhost:5000/health/ready

# Liveness check
curl http://localhost:5000/health/live
```

## Common Issues

### Database Connection
```bash
# Ensure PostgreSQL is running
# Check DATABASE_URL environment variable
```

### Import Errors
```bash
# Run from project root
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

For detailed documentation, see `tests/README.md`
