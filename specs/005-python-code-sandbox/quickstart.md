# Quickstart Guide: Python Code Sandbox

## Overview
This guide covers the setup and usage of the Python code execution sandbox for LearnPyByAI. The sandbox allows students to safely execute Python code in an isolated environment with strict security and resource limits.

## Architecture Components

### 1. Sandbox Execution Service
- **Location**: `backend/src/services/sandbox/`
- **Purpose**: Isolated code execution with resource limits and security controls
- **Implementation**: Docker container with Python runtime and import validation

### 2. Code Execution Service
- **Location**: `backend/src/services/code_execution_service.py`
- **Purpose**: Orchestrates execution, handles validation, manages results
- **Responsibilities**:
  - Validates code before execution
  - Runs code in sandbox
  - Parses results and errors
  - Persists successful executions

### 3. API Endpoint
- **Location**: `backend/src/api/v1/code_execution.py`
- **Path**: `POST /api/v1/code-execution`
- **Purpose**: Exposes code execution functionality to frontend
- **Security**: JWT authentication required

### 4. Data Models & Repositories
- **Model**: `CodeSubmission` (from F02)
- **Repository**: `CodeSubmissionRepository` (from F02)
- **Purpose**: Stores successful code executions for progress tracking

## Setup Instructions

### 1. Docker Configuration
```bash
# Ensure Docker daemon is running
sudo systemctl start docker

# Verify Docker is accessible
docker run hello-world
```

### 2. Environment Variables
Add to your `.env` file:
```bash
# Sandbox configuration
SANDBOX_TIMEOUT_SECONDS=5
SANDBOX_MEMORY_LIMIT=50MB
SANDBOX_PYTHON_IMAGE=python:3.11-alpine
SANDBOX_NETWORK_DISABLED=true
SANDBOX_FILESYSTEM_READONLY=true
```

### 3. Import Whitelist Configuration
The system includes a predefined whitelist of safe standard library modules. This is configured in the `ImportWhitelist` model and validated during code execution.

## Usage Examples

### 1. Executing Simple Code
```python
# Request
{
  "code": "print('Hello, World!')\nresult = 2 + 2\nprint(f'Result: {result}')"
}

# Response
{
  "id": "uuid-string",
  "status": "success",
  "execution_time_ms": 12,
  "output": "Hello, World!\nResult: 4",
  "memory_used_bytes": 24576
}
```

### 2. Handling Errors
```python
# Request with error
{
  "code": "print(undefined_variable)"
}

# Response
{
  "id": "uuid-string",
  "status": "error",
  "execution_time_ms": 15,
  "error_message": "Name Error on line 1: Variable 'undefined_variable' is not defined. Did you forget to create it?",
  "error_type": "NameError"
}
```

### 3. Blocked Imports
```python
# Request with blocked import
{
  "code": "import os\nprint(os.getcwd())"
}

# Response
{
  "id": "uuid-string",
  "status": "blocked",
  "execution_time_ms": 8,
  "error_message": "Import blocked for security: 'os' module is restricted. Use allowed modules like 'math', 'json', 'datetime' instead.",
  "error_type": "SecurityViolation"
}
```

## Security Features

### 1. Resource Limits
- **Timeout**: 5 seconds maximum execution time
- **Memory**: 50MB maximum memory usage
- **Concurrency**: Isolated containers prevent interference

### 2. Import Validation
- Pre-execution AST parsing to identify imports
- Strict whitelist of allowed standard library modules
- Blocking of dangerous modules (os, sys, subprocess, etc.)

### 3. Network & File System Restrictions
- Network access disabled in execution containers
- File system access limited to temporary directory only
- No persistent storage between executions

## Testing

### 1. Unit Tests
```bash
# Test error parsing
pytest tests/unit/test_error_parser.py

# Test sandbox validation
pytest tests/unit/test_sandbox_validation.py
```

### 2. Integration Tests
```bash
# Test API endpoint
pytest tests/integration/test_code_execution_api.py

# Test repository operations
pytest tests/integration/test_code_submission_repository.py
```

## Error Handling

### Common Error Types
- **SyntaxError**: Invalid Python syntax
- **NameError**: Undefined variables/functions
- **TypeError**: Incompatible type operations
- **SecurityViolation**: Attempted use of blocked modules
- **TimeoutError**: Execution exceeded time limit
- **MemoryError**: Execution exceeded memory limit

### Error Message Format
All error messages are parsed and converted to student-friendly format with:
- Clear error type identification
- Line number where error occurred
- Beginner-friendly explanation
- Suggestions for fixing the error

## Deployment

### Container Configuration
The sandbox runs in Docker containers with the following security measures:
- No network access
- Read-only root filesystem
- Limited memory and CPU
- Temporary writable directory only
- Restricted system calls via seccomp

### Monitoring
- Execution time tracking
- Memory usage monitoring
- Error rate analysis
- Successful execution logging
