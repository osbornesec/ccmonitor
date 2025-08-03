# PRP Validation Guide: 4-Level Quality Assurance

This guide provides comprehensive validation strategies for PRPs (Product Requirement Prompts) using a 4-level validation approach that ensures production-ready code quality.

## Validation Philosophy

The 4-level validation approach provides progressive quality assurance:

1. **Level 0**: Test Creation (TDD Red Phase) - Ensure tests exist and fail appropriately
2. **Level 1**: Syntax & Style - Code formatting, linting, and type checking
3. **Level 2**: Unit Tests (TDD Green Phase) - Individual component testing
4. **Level 3**: Integration Testing - System-level validation
5. **Level 4**: Creative & Domain-Specific - Advanced validation tailored to the domain

## Level 0: Test Creation (TDD Red Phase)

### Purpose
Ensure comprehensive test coverage exists before any implementation begins. All tests must fail initially to prove they're testing the right behavior.

### Validation Commands by Technology

#### Python Projects
```bash
# Create tests that should fail initially
pytest tests/ -v --tb=short
# Expected: Tests fail because implementation doesn't exist yet

# Check test coverage requirements
pytest --cov=[module] --cov-report=term-missing --cov-fail-under=90
# Expected: Coverage requirement establishes quality baseline

# Validate test structure and naming
pytest --collect-only tests/
# Expected: Tests follow naming conventions and are discoverable
```

#### JavaScript/Node.js Projects
```bash
# Run tests that should fail initially
npm test -- --watchAll=false --verbose
# Expected: Tests fail due to missing implementation

# Check test coverage
npm test -- --coverage --coverageThreshold='{"global":{"lines":90}}'
# Expected: Coverage thresholds established

# Validate test structure
npm test -- --listTests
# Expected: All test files discovered and properly structured
```

#### React Projects
```bash
# Component tests that should fail initially
npm test -- --watchAll=false --verbose
# Expected: Component tests fail due to missing components

# Validate React Testing Library setup
npm test -- --testNamePattern="should render"
# Expected: Basic rendering tests exist and fail appropriately

# Check test environment setup
npm test -- --env=jsdom --verbose
# Expected: Test environment properly configured for React
```

### Best Practices for Level 0

1. **Write Comprehensive Test Suites**: Cover happy path, edge cases, and error conditions
2. **Validate Test Failures**: Ensure tests fail for the right reasons
3. **Establish Coverage Requirements**: Set minimum coverage thresholds
4. **Document Test Intent**: Each test should clearly describe expected behavior

### Common Level 0 Validation Patterns

```python
# Python: Comprehensive test creation
def test_user_registration_with_valid_data():
    """Test that user registration succeeds with valid data"""
    # This test should fail initially - no implementation exists
    user_data = {"email": "test@example.com", "name": "Test User"}
    result = register_user(user_data)
    assert result.success is True
    assert result.user.email == "test@example.com"

def test_user_registration_with_invalid_email():
    """Test that user registration fails with invalid email"""
    # This test should also fail initially
    user_data = {"email": "invalid-email", "name": "Test User"}
    result = register_user(user_data)
    assert result.success is False
    assert "Invalid email" in result.errors
```

```javascript
// JavaScript: Comprehensive test creation
describe('UserRegistration', () => {
  test('should register user with valid data', () => {
    // This test should fail initially - no implementation exists
    const userData = { email: 'test@example.com', name: 'Test User' };
    const result = registerUser(userData);
    expect(result.success).toBe(true);
    expect(result.user.email).toBe('test@example.com');
  });

  test('should reject registration with invalid email', () => {
    // This test should also fail initially
    const userData = { email: 'invalid-email', name: 'Test User' };
    const result = registerUser(userData);
    expect(result.success).toBe(false);
    expect(result.errors).toContain('Invalid email');
  });
});
```

## Level 1: Syntax & Style (Code Quality)

### Purpose
Ensure code follows consistent formatting, style guidelines, and passes static analysis before functional testing.

### Technology-Specific Validation

#### Python Projects
```bash
# Code formatting with Black
black --check [files/directories]
black --diff [files/directories]  # Show what would change
black [files/directories]         # Apply formatting

# Linting with Ruff (modern, fast linter)
ruff check [files/directories] --fix
ruff format [files/directories]

# Type checking with MyPy
mypy [files/directories] --strict
mypy [files/directories] --ignore-missing-imports

# Import sorting with isort
isort --check-only [files/directories]
isort --diff [files/directories]

# Security scanning with Bandit
bandit -r [directories] -f json
bandit -r [directories] -ll  # Low severity and above

# Complexity checking
radon cc [files/directories] --min B  # Cyclomatic complexity
radon mi [files/directories] --min B  # Maintainability index
```

#### JavaScript/TypeScript Projects
```bash
# ESLint for code quality
eslint [files/directories] --ext .js,.ts,.jsx,.tsx
eslint [files/directories] --fix  # Auto-fix issues

# Prettier for formatting
prettier --check [files/directories]
prettier --write [files/directories]

# TypeScript type checking
tsc --noEmit  # Type check without compilation
tsc --noEmit --strict  # Strict type checking

# JSHint for additional validation
jshint [files/directories]

# Dependency security audit
npm audit
npm audit fix  # Auto-fix vulnerabilities
```

#### React Projects
```bash
# React-specific linting
eslint --ext .jsx,.tsx [directories] --rule "react-hooks/exhaustive-deps: error"

# Accessibility linting
eslint [files] --rule "jsx-a11y/no-onchange: error"

# React Testing Library linting
eslint [test-files] --rule "testing-library/await-async-query: error"

# Bundle analysis
npm run build
npx webpack-bundle-analyzer build/static/js/*.js
```

### Best Practices for Level 1

1. **Automate Formatting**: Use automated tools to maintain consistency
2. **Strict Type Checking**: Enable strict mode for type checkers
3. **Security Scanning**: Include security analysis in the pipeline
4. **Performance Linting**: Check for performance anti-patterns

### Configuration Examples

#### Python: pyproject.toml
```toml
[tool.black]
line-length = 88
target-version = ['py311']

[tool.ruff]
select = ["E", "W", "F", "B", "I", "N", "UP", "ANN", "S", "BLE", "COM", "DTZ"]
ignore = ["E501", "ANN101", "ANN102"]
line-length = 88

[tool.mypy]
python_version = "3.11"
strict = true
warn_return_any = true
warn_unused_configs = true

[tool.coverage.run]
branch = true
source = ["src"]

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "def __repr__",
    "raise AssertionError",
    "raise NotImplementedError"
]
```

#### JavaScript: .eslintrc.js
```javascript
module.exports = {
  extends: [
    'eslint:recommended',
    '@typescript-eslint/recommended',
    'plugin:react/recommended',
    'plugin:react-hooks/recommended',
    'plugin:jsx-a11y/recommended',
    'plugin:testing-library/react'
  ],
  rules: {
    '@typescript-eslint/no-unused-vars': 'error',
    'react-hooks/exhaustive-deps': 'error',
    'jsx-a11y/no-onchange': 'error',
    'testing-library/await-async-query': 'error'
  },
  settings: {
    react: {
      version: 'detect'
    }
  }
};
```

## Level 2: Unit Tests (Individual Component Testing)

### Purpose
Validate individual components, functions, and modules work correctly in isolation.

### Testing Strategies by Domain

#### API Testing
```bash
# FastAPI/Python API testing
pytest tests/api/ -v --tb=short
pytest tests/api/ --cov=src/api --cov-report=html

# Test specific endpoints
pytest tests/api/test_users.py::test_create_user -v

# Load testing with locust
locust -f tests/load/locustfile.py --headless -u 10 -r 2 -t 60s

# API documentation testing
pytest tests/api/ --doctest-modules
```

#### Database Testing
```bash
# Database integration tests
pytest tests/database/ -v --tb=short

# Test migrations
alembic upgrade head  # Apply all migrations
alembic downgrade -1  # Test rollback
alembic upgrade head  # Re-apply

# Database performance testing
pytest tests/database/test_performance.py -v --benchmark-only

# Data integrity testing
pytest tests/database/test_constraints.py -v
```

#### Frontend Component Testing
```bash
# React component testing
npm test -- --testPathPattern=components --coverage

# Visual regression testing
npm run test:visual
percy exec -- npm test

# Accessibility testing
npm test -- --testNamePattern="accessibility"
```

### Advanced Testing Patterns

#### Property-Based Testing
```python
# Python with Hypothesis
from hypothesis import given, strategies as st

@given(st.emails())
def test_email_validation_accepts_valid_emails(email):
    """Property-based test: all valid emails should pass validation"""
    result = validate_email(email)
    assert result.is_valid

@given(st.text().filter(lambda x: '@' not in x and '.' not in x))
def test_email_validation_rejects_invalid_formats(invalid_text):
    """Property-based test: strings without @ and . should fail"""
    result = validate_email(invalid_text)
    assert not result.is_valid
```

#### Mutation Testing
```bash
# Python mutation testing with mutmut
mutmut run --paths-to-mutate=src/
mutmut results
mutmut show [mutation-id]

# JavaScript mutation testing with Stryker
npx stryker run
```

#### Performance Testing
```python
# Python performance testing with pytest-benchmark
def test_user_creation_performance(benchmark):
    """Benchmark user creation performance"""
    user_data = {"email": "test@example.com", "name": "Test User"}
    
    result = benchmark(create_user, user_data)
    
    assert result.email == "test@example.com"
    # Benchmark automatically measures execution time
```

## Level 3: Integration Testing (System-Level Validation)

### Purpose
Validate that different components work together correctly and that the system behaves properly as a whole.

### Integration Testing Approaches

#### API Integration Testing
```bash
# End-to-end API workflow testing
pytest tests/integration/test_user_workflow.py -v

# Third-party service integration
pytest tests/integration/test_external_apis.py -v --vcr-record=once

# Database integration with real database
pytest tests/integration/ --database-url=postgresql://test:test@localhost/testdb

# Authentication and authorization flow
pytest tests/integration/test_auth_flow.py -v
```

#### Frontend Integration Testing
```bash
# React component integration
npm test -- --testPathPattern=integration --watchAll=false

# API integration from frontend
npm test -- --testNamePattern="API integration" --setupFilesAfterEnv=["<rootDir>/src/setupTests.js"]

# Router and navigation testing
npm test -- --testNamePattern="navigation" --watchAll=false
```

#### Full-Stack Integration
```bash
# Cypress end-to-end testing
npx cypress run --spec "cypress/integration/user-workflow.spec.js"

# Playwright cross-browser testing
npx playwright test tests/e2e/user-journey.spec.ts

# Docker-based integration testing
docker-compose -f docker-compose.test.yml up --build
pytest tests/integration/ --base-url=http://localhost:8000
docker-compose -f docker-compose.test.yml down
```

### Integration Test Patterns

#### Database Integration
```python
# Test database transactions and rollbacks
def test_user_creation_rollback_on_error(db_session):
    """Test that failed user creation rolls back properly"""
    # Arrange
    user1 = User(email="test@example.com", name="User 1")
    user2 = User(email="test@example.com", name="User 2")  # Duplicate email
    
    # Act & Assert
    db_session.add(user1)
    db_session.commit()
    
    db_session.add(user2)
    with pytest.raises(IntegrityError):
        db_session.commit()
    
    # Verify rollback occurred
    db_session.rollback()
    users = db_session.query(User).filter_by(email="test@example.com").all()
    assert len(users) == 1  # Only first user should exist
```

#### API Integration
```python
# Test complete API workflows
def test_complete_user_registration_and_login_flow():
    """Test full user lifecycle: register -> verify -> login -> access"""
    # Registration
    registration_data = {
        "email": "newuser@example.com",
        "name": "New User",
        "password": "SecurePassword123!"
    }
    
    response = client.post("/register", json=registration_data)
    assert response.status_code == 201
    user_id = response.json()["id"]
    
    # Email verification (mock)
    verify_response = client.post(f"/verify/{user_id}/token123")
    assert verify_response.status_code == 200
    
    # Login
    login_response = client.post("/login", json={
        "email": "newuser@example.com",
        "password": "SecurePassword123!"
    })
    assert login_response.status_code == 200
    access_token = login_response.json()["access_token"]
    
    # Protected resource access
    headers = {"Authorization": f"Bearer {access_token}"}
    profile_response = client.get("/profile", headers=headers)
    assert profile_response.status_code == 200
    assert profile_response.json()["email"] == "newuser@example.com"
```

## Level 4: Creative & Domain-Specific Validation

### Purpose
Apply specialized testing approaches tailored to the specific domain, technology, or business requirements.

### Domain-Specific Validation Strategies

#### Security-Focused Applications
```bash
# Security vulnerability scanning
bandit -r src/ -f json -o security-report.json

# Dependency vulnerability checking
safety check --json --output safety-report.json

# OWASP ZAP security testing
zap-baseline.py -t http://localhost:8000 -J zap-report.json

# SQL injection testing
sqlmap -u "http://localhost:8000/api/users?id=1" --batch --risk=3

# Authentication bypass testing
pytest tests/security/test_auth_bypass.py -v
```

#### Performance-Critical Applications
```bash
# Load testing with multiple tools
artillery run load-test-config.yml
k6 run performance-test.js
wrk -t12 -c400 -d30s http://localhost:8000/api/users

# Memory profiling
python -m memory_profiler src/main.py
valgrind --tool=memcheck --leak-check=full python src/main.py

# Database query performance
EXPLAIN ANALYZE SELECT * FROM users WHERE email = 'test@example.com';
pg_stat_statements; -- PostgreSQL query analysis
```

#### Real-Time Applications
```bash
# WebSocket connection testing
python tests/websocket/test_realtime_features.py

# Message queue testing
pytest tests/queue/test_message_processing.py -v

# Event-driven architecture testing
pytest tests/events/test_event_handling.py -v

# Latency and throughput testing
pytest tests/performance/test_realtime_latency.py --benchmark-only
```

#### Machine Learning Applications
```bash
# Model validation and testing
pytest tests/ml/test_model_accuracy.py -v
pytest tests/ml/test_data_pipeline.py -v

# Data quality validation
great_expectations checkpoint run data_quality_checkpoint

# Model performance benchmarking
python tests/ml/benchmark_model_inference.py

# Bias and fairness testing
python tests/ml/test_model_fairness.py
```

### Creative Testing Approaches

#### Chaos Engineering
```python
# Chaos testing with fault injection
def test_system_resilience_with_database_failure():
    """Test system behavior when database becomes unavailable"""
    with patch('database.connection') as mock_db:
        mock_db.side_effect = DatabaseConnectionError("Connection lost")
        
        # System should gracefully handle database failure
        response = client.get("/users")
        assert response.status_code == 503  # Service unavailable
        assert "Database unavailable" in response.json()["message"]

def test_system_resilience_with_high_load():
    """Test system behavior under extreme load"""
    # Simulate high concurrent load
    import concurrent.futures
    
    def make_request():
        return client.get("/users")
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=100) as executor:
        futures = [executor.submit(make_request) for _ in range(1000)]
        responses = [future.result() for future in concurrent.futures.as_completed(futures)]
    
    # System should remain stable under load
    success_responses = [r for r in responses if r.status_code == 200]
    assert len(success_responses) / len(responses) > 0.95  # 95% success rate
```

#### Time-Based Testing
```python
# Test time-dependent behavior
def test_user_session_expiration():
    """Test that user sessions expire correctly"""
    # Create user session
    login_response = client.post("/login", json={
        "email": "test@example.com",
        "password": "password"
    })
    access_token = login_response.json()["access_token"]
    
    # Verify access works initially
    headers = {"Authorization": f"Bearer {access_token}"}
    response = client.get("/profile", headers=headers)
    assert response.status_code == 200
    
    # Fast-forward time using mock
    with patch('datetime.datetime') as mock_datetime:
        mock_datetime.now.return_value = datetime.now() + timedelta(hours=25)  # 1 day + 1 hour
        
        # Session should be expired
        response = client.get("/profile", headers=headers)
        assert response.status_code == 401
        assert "Token expired" in response.json()["message"]
```

#### Cross-Platform Testing
```bash
# Multi-browser testing with Playwright
npx playwright test --project=chromium
npx playwright test --project=firefox  
npx playwright test --project=webkit

# Mobile device testing
npx playwright test --project=mobile-chrome
npx playwright test --project=mobile-safari

# Cross-platform API testing
pytest tests/api/ --platform=linux
pytest tests/api/ --platform=windows
pytest tests/api/ --platform=macos
```

## Validation Automation and CI/CD Integration

### GitHub Actions Example
```yaml
name: 4-Level Validation Pipeline

on: [push, pull_request]

jobs:
  level-0-test-creation:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Validate test existence and structure
        run: |
          pytest --collect-only tests/
          pytest tests/ -v --tb=short || echo "Tests should fail initially (Red phase)"

  level-1-code-quality:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: pip install ruff black mypy bandit
      - name: Code formatting
        run: black --check .
      - name: Linting
        run: ruff check .
      - name: Type checking
        run: mypy src/
      - name: Security scanning
        run: bandit -r src/ -f json

  level-2-unit-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run unit tests
        run: pytest tests/unit/ -v --cov=src --cov-report=xml
      - name: Upload coverage
        uses: codecov/codecov-action@v3

  level-3-integration-tests:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:13
        env:
          POSTGRES_PASSWORD: postgres
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    steps:
      - uses: actions/checkout@v3
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run integration tests
        run: pytest tests/integration/ -v
        env:
          DATABASE_URL: postgresql://postgres:postgres@localhost/testdb

  level-4-domain-specific:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Performance testing
        run: pytest tests/performance/ --benchmark-only
      - name: Security penetration testing
        run: pytest tests/security/ -v
      - name: Load testing
        run: locust -f tests/load/locustfile.py --headless -u 50 -r 5 -t 60s
```

## Best Practices Summary

### Universal Principles
1. **Test First**: Always write tests before implementation (Level 0)
2. **Automate Everything**: Use CI/CD to enforce all validation levels
3. **Fast Feedback**: Keep validation cycles short for rapid iteration
4. **Comprehensive Coverage**: Include happy path, edge cases, and errors
5. **Domain Adaptation**: Customize Level 4 validation for your specific needs

### Validation Thresholds
- **Level 0**: 100% of planned functionality must have tests
- **Level 1**: Zero linting errors, 100% type coverage
- **Level 2**: Minimum 90% test coverage, all tests passing
- **Level 3**: All integration scenarios working, performance acceptable
- **Level 4**: Domain-specific quality metrics met, security validated

### Common Pitfalls to Avoid
- Skipping Level 0 (writing implementation before tests)
- Ignoring Level 1 (poor code quality leads to maintenance issues)
- Weak Level 2 (insufficient unit test coverage)
- Missing Level 3 (components work alone but not together)
- Generic Level 4 (not adapting validation to domain requirements)

This 4-level validation approach ensures that all PRP implementations meet production quality standards while maintaining the TDD discipline that makes AI-assisted development reliable and predictable.