# Test Documentation for Kisan Smart

## Overview

This document describes the testing strategy, test execution procedures, and guidelines for the Kisan Smart fertilizer recommendation system.

## Test Coverage Goals

- **Overall Coverage**: ≥80%
- **Critical Modules** (auth, prediction): ≥90%
- **Models**: ≥85%
- **API Routes**: ≥85%

## Test Categories

### 1. Unit Tests (`tests/unit/`)

**Purpose**: Test individual components in isolation

**Files**:
- `test_models.py`: User model, Recommendation model
- `test_validators.py`: Input validation functions
- `test_ml_models.py`: ML prediction logic

**Run**:
```bash
pytest tests/unit -v
```

### 2. Integration Tests (`tests/integration/`)

**Purpose**: Test component interactions and workflows

**Files**:
- `test_auth_flow.py`: Registration, login, password reset
- `test_prediction_flow.py`: End-to-end prediction workflow
- `test_history_flow.py`: History management and filtering

**Run**:
```bash
pytest tests/integration -v
```

### 3. Performance Tests (`tests/performance/`)

**Purpose**: Validate performance under load

**Files**:
- `locustfile.py`: Load testing with 100+ concurrent users
- `benchmark.py`: Performance benchmarks for key operations

**Run**:
```bash
# Locust load test
locust -f tests/performance/locustfile.py --host=http://localhost:5000

# Benchmarks
pytest tests/performance/benchmark.py -v -s
```

**Performance Targets**:
- Prediction API: <3s response time (p95)
- History retrieval: <1s
- Dashboard stats: <0.5s
- Database queries: <100ms

### 4. Security Tests (`tests/security/`)

**Purpose**: Validate security measures

**Files**:
- `test_auth_security.py`: Authentication, authorization, injection prevention

**Run**:
```bash
pytest tests/security -v
```

## Running Tests

### All Tests
```bash
pytest -v
```

### With Coverage
```bash
pytest --cov=app --cov=website --cov-report=html --cov-report=term-missing
```

### Specific Test Categories
```bash
# Unit tests only
pytest -m unit

# Integration tests only
pytest -m integration

# Performance tests
pytest -m performance

# Security tests
pytest -m security
```

### Exclude Slow Tests
```bash
pytest -m "not slow"
```

## Test Data

Test data is managed through fixtures in `conftest.py`:
- `test_user`: Sample user for authentication tests
- `test_predictions`: Preloaded prediction data
- `sample_prediction_data`: Valid prediction input

## CI/CD Pipeline

Tests run automatically on:
- Every push to `main` or `develop`
- Every pull request

**Pipeline Steps**:
1. Lint with flake8
2. Security scan with bandit
3. Run unit tests
4. Run integration tests
5. Run security tests
6. Upload coverage to Codecov
7. Check coverage threshold (80%)

**GitHub Actions**: `.github/workflows/test.yml`

## Test Best Practices

1. **Independent Tests**: Each test should be independent
2. **Clear Names**: Use descriptive test names
3. **Arrange-Act-Assert**: Follow AAA pattern
4. **One Assertion**: Test one thing per test (generally)
5. **Mock External Services**: Use mocks for email, external APIs
6. **Clean Up**: Use fixtures for setup and teardown
7. **Fast Tests**: Keep unit tests fast (<1s each)

## Troubleshooting

### Database Connection Errors
- Ensure PostgreSQL is running
- Check `DATABASE_URL` environment variable
- Verify test database exists

### Import Errors
- Run from project root directory
- Check `PYTHONPATH` includes project root
- Install all dependencies: `pip install -r requirements.txt`

### Fixture Errors
- Check `conftest.py` is in tests directory
- Verify fixture scope (function, session)
- Ensure database is initialized in fixture

## Coverage Reports

### Viewing HTML Report
```bash
pytest --cov=app --cov-report=html
open htmlcov/index.html  # macOS/Linux
start htmlcov/index.html  # Windows
```

### Coverage Requirements
- All new code should have ≥80% coverage
- Critical paths (auth, prediction) should have ≥90%
- Pull requests with <80% coverage will be flagged

## Health Checks

**Endpoints**:
- `/health`: Full health check
- `/health/ready`: Readiness check for K8s
- `/health/live`: Liveness check for K8s

**Usage**:
```bash
curl http://localhost:5000/health
```

**Response**:
```json
{
  "status": "healthy",
  "timestamp": "2024-02-08T15:30:00Z",
  "checks": {
    "database": true,
    "ml_models": true,
    "disk_space": true
  }
}
```
