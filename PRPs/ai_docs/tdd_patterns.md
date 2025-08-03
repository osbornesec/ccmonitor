# TDD Patterns and Best Practices for AI Development

This document provides comprehensive TDD (Test-Driven Development) patterns and best practices specifically tailored for AI-assisted development workflows.

## Core TDD Methodology

### Red-Green-Refactor Cycle

The fundamental TDD cycle that must be followed for all implementations:

```
RED: Write a failing test that specifies the desired behavior
GREEN: Write the minimal code to make the test pass
REFACTOR: Improve the code while keeping tests green
```

### Test-First Principles

1. **No Production Code Without a Test**: Never write implementation code without a failing test first
2. **Minimal Implementation**: Write only enough code to make the current test pass
3. **Comprehensive Testing**: Cover happy path, edge cases, and error conditions
4. **Fast Feedback**: Tests should run quickly to enable rapid iteration

## Language-Specific TDD Patterns

### Python TDD Patterns

```python
# Test Pattern - Using pytest
def test_user_validation_with_valid_email():
    """Test that user validation passes with valid email"""
    # Arrange
    user_data = {"email": "test@example.com", "name": "Test User"}
    
    # Act
    result = validate_user(user_data)
    
    # Assert
    assert result.is_valid
    assert result.errors == []

def test_user_validation_with_invalid_email():
    """Test that user validation fails with invalid email"""
    # Arrange
    user_data = {"email": "invalid-email", "name": "Test User"}
    
    # Act
    result = validate_user(user_data)
    
    # Assert
    assert not result.is_valid
    assert "Invalid email format" in result.errors

# Implementation Pattern - Minimal first implementation
@dataclass
class ValidationResult:
    is_valid: bool
    errors: List[str]

def validate_user(user_data: dict) -> ValidationResult:
    """Validate user data"""
    errors = []
    
    # Email validation
    email = user_data.get("email", "")
    if not email or "@" not in email:
        errors.append("Invalid email format")
    
    return ValidationResult(
        is_valid=len(errors) == 0,
        errors=errors
    )
```

### JavaScript/TypeScript TDD Patterns

```javascript
// Test Pattern - Using Jest
describe('UserValidator', () => {
  test('should validate user with correct email', () => {
    // Arrange
    const userData = { email: 'test@example.com', name: 'Test User' };
    
    // Act
    const result = validateUser(userData);
    
    // Assert
    expect(result.isValid).toBe(true);
    expect(result.errors).toEqual([]);
  });

  test('should reject user with invalid email', () => {
    // Arrange
    const userData = { email: 'invalid-email', name: 'Test User' };
    
    // Act
    const result = validateUser(userData);
    
    // Assert
    expect(result.isValid).toBe(false);
    expect(result.errors).toContain('Invalid email format');
  });
});

// Implementation Pattern
interface ValidationResult {
  isValid: boolean;
  errors: string[];
}

function validateUser(userData: any): ValidationResult {
  const errors: string[] = [];
  
  // Email validation
  const email = userData.email || '';
  if (!email || !email.includes('@')) {
    errors.push('Invalid email format');
  }
  
  return {
    isValid: errors.length === 0,
    errors
  };
}
```

### React Component TDD Patterns

```javascript
// Test Pattern - Using React Testing Library
import { render, screen, fireEvent } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import LoginForm from './LoginForm';

describe('LoginForm', () => {
  test('should display validation error for invalid email', async () => {
    // Arrange
    const mockOnSubmit = jest.fn();
    render(<LoginForm onSubmit={mockOnSubmit} />);
    
    // Act
    const emailInput = screen.getByLabelText(/email/i);
    const submitButton = screen.getByRole('button', { name: /login/i });
    
    await userEvent.type(emailInput, 'invalid-email');
    fireEvent.click(submitButton);
    
    // Assert
    expect(screen.getByText(/invalid email format/i)).toBeInTheDocument();
    expect(mockOnSubmit).not.toHaveBeenCalled();
  });

  test('should submit form with valid data', async () => {
    // Arrange
    const mockOnSubmit = jest.fn();
    render(<LoginForm onSubmit={mockOnSubmit} />);
    
    // Act
    await userEvent.type(screen.getByLabelText(/email/i), 'test@example.com');
    await userEvent.type(screen.getByLabelText(/password/i), 'password123');
    fireEvent.click(screen.getByRole('button', { name: /login/i }));
    
    // Assert
    expect(mockOnSubmit).toHaveBeenCalledWith({
      email: 'test@example.com',
      password: 'password123'
    });
  });
});

// Implementation Pattern - Component with validation
import React, { useState } from 'react';

interface LoginFormProps {
  onSubmit: (data: { email: string; password: string }) => void;
}

const LoginForm: React.FC<LoginFormProps> = ({ onSubmit }) => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [errors, setErrors] = useState<string[]>([]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    const validationErrors: string[] = [];
    
    // Email validation
    if (!email || !email.includes('@')) {
      validationErrors.push('Invalid email format');
    }
    
    // Password validation
    if (!password || password.length < 6) {
      validationErrors.push('Password must be at least 6 characters');
    }
    
    setErrors(validationErrors);
    
    if (validationErrors.length === 0) {
      onSubmit({ email, password });
    }
  };

  return (
    <form onSubmit={handleSubmit}>
      <div>
        <label htmlFor="email">Email:</label>
        <input
          id="email"
          type="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
        />
      </div>
      
      <div>
        <label htmlFor="password">Password:</label>
        <input
          id="password"
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
        />
      </div>
      
      {errors.length > 0 && (
        <div role="alert">
          {errors.map((error, index) => (
            <div key={index}>{error}</div>
          ))}
        </div>
      )}
      
      <button type="submit">Login</button>
    </form>
  );
};

export default LoginForm;
```

## API Development TDD Patterns

### FastAPI/Python API TDD

```python
# Test Pattern - API endpoint testing
import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_create_user_with_valid_data():
    """Test user creation with valid data"""
    # Arrange
    user_data = {
        "email": "test@example.com",
        "name": "Test User",
        "password": "securepassword"
    }
    
    # Act
    response = client.post("/users", json=user_data)
    
    # Assert
    assert response.status_code == 201
    assert response.json()["email"] == "test@example.com"
    assert "password" not in response.json()  # Password should not be returned

def test_create_user_with_invalid_email():
    """Test user creation fails with invalid email"""
    # Arrange
    user_data = {
        "email": "invalid-email",
        "name": "Test User",
        "password": "securepassword"
    }
    
    # Act
    response = client.post("/users", json=user_data)
    
    # Assert
    assert response.status_code == 422
    assert "Invalid email format" in response.json()["detail"]

# Implementation Pattern - FastAPI endpoint
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, EmailStr

app = FastAPI()

class UserCreate(BaseModel):
    email: EmailStr
    name: str
    password: str

class UserResponse(BaseModel):
    id: int
    email: str
    name: str

@app.post("/users", response_model=UserResponse, status_code=201)
async def create_user(user: UserCreate):
    """Create a new user"""
    # Validation is handled by Pydantic
    
    # Minimal implementation for green phase
    return UserResponse(
        id=1,
        email=user.email,
        name=user.name
    )
```

## Database TDD Patterns

### Database Integration Testing

```python
# Test Pattern - Database operations
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import User, Base

@pytest.fixture
def db_session():
    """Create a test database session"""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    yield session
    session.close()

def test_user_creation_in_database(db_session):
    """Test user can be created and retrieved from database"""
    # Arrange
    user_data = {
        "email": "test@example.com",
        "name": "Test User",
        "password_hash": "hashed_password"
    }
    
    # Act
    user = User(**user_data)
    db_session.add(user)
    db_session.commit()
    
    retrieved_user = db_session.query(User).filter_by(email="test@example.com").first()
    
    # Assert
    assert retrieved_user is not None
    assert retrieved_user.email == "test@example.com"
    assert retrieved_user.name == "Test User"

def test_user_email_uniqueness_constraint(db_session):
    """Test that duplicate emails are not allowed"""
    # Arrange
    user1 = User(email="test@example.com", name="User 1", password_hash="hash1")
    user2 = User(email="test@example.com", name="User 2", password_hash="hash2")
    
    # Act & Assert
    db_session.add(user1)
    db_session.commit()
    
    db_session.add(user2)
    with pytest.raises(IntegrityError):
        db_session.commit()
```

## Advanced TDD Patterns

### Mocking External Dependencies

```python
# Test Pattern - Mocking external services
import pytest
from unittest.mock import Mock, patch
from services import EmailService, UserService

def test_user_registration_sends_welcome_email():
    """Test that user registration sends welcome email"""
    # Arrange
    mock_email_service = Mock(spec=EmailService)
    user_service = UserService(email_service=mock_email_service)
    
    user_data = {
        "email": "test@example.com",
        "name": "Test User"
    }
    
    # Act
    user_service.register_user(user_data)
    
    # Assert
    mock_email_service.send_welcome_email.assert_called_once_with(
        "test@example.com", "Test User"
    )

@patch('services.external_api_client')
def test_user_validation_with_external_service(mock_api_client):
    """Test user validation that depends on external API"""
    # Arrange
    mock_api_client.validate_email.return_value = {"valid": True}
    user_service = UserService()
    
    # Act
    result = user_service.validate_user_email("test@example.com")
    
    # Assert
    assert result is True
    mock_api_client.validate_email.assert_called_once_with("test@example.com")
```

### Property-Based Testing

```python
# Test Pattern - Property-based testing with Hypothesis
from hypothesis import given, strategies as st
import pytest

@given(st.emails())
def test_email_validation_with_valid_emails(email):
    """Test that all valid emails pass validation"""
    # Act
    result = validate_email(email)
    
    # Assert  
    assert result.is_valid

@given(st.text().filter(lambda x: '@' not in x))
def test_email_validation_rejects_invalid_emails(invalid_email):
    """Test that strings without @ are rejected"""
    # Act
    result = validate_email(invalid_email)
    
    # Assert
    assert not result.is_valid
```

## TDD Best Practices for AI Development

### 1. Write Tests That Document Behavior

```python
def test_password_hashing_produces_different_hash_for_same_password():
    """
    Test that hashing the same password twice produces different hashes
    due to salt randomization, but both hashes verify correctly.
    """
    password = "test_password"
    
    hash1 = hash_password(password)
    hash2 = hash_password(password)
    
    # Hashes should be different due to salt
    assert hash1 != hash2
    
    # But both should verify correctly
    assert verify_password(password, hash1)
    assert verify_password(password, hash2)
```

### 2. Test Edge Cases and Error Conditions

```python
def test_user_creation_with_extremely_long_name():
    """Test that user creation handles very long names appropriately"""
    long_name = "a" * 1000
    
    with pytest.raises(ValidationError) as exc_info:
        create_user(email="test@example.com", name=long_name)
    
    assert "Name too long" in str(exc_info.value)

def test_user_creation_with_empty_email():
    """Test that user creation fails gracefully with empty email"""
    with pytest.raises(ValidationError) as exc_info:
        create_user(email="", name="Test User")
    
    assert "Email required" in str(exc_info.value)
```

### 3. Use Fixtures for Test Data Management

```python
@pytest.fixture
def valid_user_data():
    """Provide consistent valid user data for tests"""
    return {
        "email": "test@example.com",
        "name": "Test User",
        "password": "SecurePassword123!"
    }

@pytest.fixture
def created_user(db_session, valid_user_data):
    """Provide a user that's already created in the database"""
    user = User(**valid_user_data)
    db_session.add(user)
    db_session.commit()
    return user

def test_user_deletion(db_session, created_user):
    """Test that user can be deleted"""
    user_id = created_user.id
    
    delete_user(db_session, user_id)
    
    deleted_user = db_session.query(User).filter_by(id=user_id).first()
    assert deleted_user is None
```

### 4. Integration Testing Patterns

```python
def test_complete_user_registration_flow():
    """Test the complete user registration workflow end-to-end"""
    # Arrange
    registration_data = {
        "email": "newuser@example.com",
        "name": "New User",
        "password": "SecurePassword123!"
    }
    
    # Act - Complete registration flow
    response = client.post("/register", json=registration_data)
    
    # Assert - Registration succeeded
    assert response.status_code == 201
    user_data = response.json()
    assert user_data["email"] == "newuser@example.com"
    
    # Assert - User can login with credentials
    login_response = client.post("/login", json={
        "email": "newuser@example.com",
        "password": "SecurePassword123!"
    })
    assert login_response.status_code == 200
    assert "access_token" in login_response.json()
    
    # Assert - User appears in database
    user = get_user_by_email("newuser@example.com")
    assert user is not None
    assert user.name == "New User"
```

## Common TDD Antipatterns to Avoid

### ❌ Testing Implementation Details

```python
# BAD - Testing internal implementation
def test_user_service_calls_database_query():
    """This test is too focused on implementation"""
    with patch('user_service.db.query') as mock_query:
        user_service.get_user(1)
        mock_query.assert_called_once()  # Testing implementation, not behavior
```

```python
# GOOD - Testing behavior
def test_user_service_returns_user_for_valid_id():
    """This test focuses on the desired behavior"""
    # Arrange
    expected_user = User(id=1, email="test@example.com")
    
    # Act
    result = user_service.get_user(1)
    
    # Assert
    assert result.id == 1
    assert result.email == "test@example.com"
```

### ❌ Writing Tests That Are Too Large

```python
# BAD - Test doing too much
def test_complete_application_workflow():
    """This test is trying to test too many things at once"""
    # 50 lines of setup
    # Multiple API calls
    # Database assertions
    # Email verification
    # File system checks
    # etc...
```

```python
# GOOD - Focused, single-purpose tests
def test_user_registration_creates_user():
    """Focus on one specific behavior"""
    registration_data = {"email": "test@example.com", "name": "Test"}
    
    result = register_user(registration_data)
    
    assert result.email == "test@example.com"
    assert result.name == "Test"

def test_user_registration_sends_welcome_email():
    """Separate test for email behavior"""
    with patch('email_service.send_welcome_email') as mock_send:
        register_user({"email": "test@example.com", "name": "Test"})
        mock_send.assert_called_once()
```

### ❌ Skipping the Red Phase

```python
# BAD - Writing implementation first
def create_user(user_data):
    # Implementation written before test
    return User(**user_data)

def test_create_user():
    # Test written after implementation
    result = create_user({"email": "test@example.com"})
    assert result.email == "test@example.com"
```

```python
# GOOD - Red-Green-Refactor cycle
def test_create_user():
    """RED: Write failing test first"""
    result = create_user({"email": "test@example.com"})
    assert result.email == "test@example.com"
    # This test should fail initially

def create_user(user_data):
    """GREEN: Write minimal implementation to make test pass"""
    return User(email=user_data["email"])
    # Minimal implementation

def create_user(user_data):
    """REFACTOR: Improve implementation while keeping tests green"""
    # Validate data
    if not user_data.get("email"):
        raise ValueError("Email required")
    
    # Enhanced implementation
    return User(
        email=user_data["email"],
        name=user_data.get("name", ""),
        created_at=datetime.now()
    )
```

This comprehensive guide provides the patterns and practices needed for effective TDD in AI-assisted development. Remember: **Always write the test first, make it pass with minimal code, then refactor for quality.**