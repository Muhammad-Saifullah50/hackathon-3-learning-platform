# Research: Python Code Sandbox Implementation

## Decision: Sandbox Execution Engine Choice
**Rationale**: After researching various Python sandbox solutions, Docker containers are the most secure and reliable approach for our use case.

**Alternatives considered**:
1. **RestrictedPython** - Limited and doesn't handle all security concerns (subprocess, network access, etc.)
2. **PyPy's sandboxing** - Complex to set up and maintain
3. **Custom AST parsing** - Would require significant development effort and still have security gaps
4. **Piston API** - Managed service but adds external dependency and potential cost
5. **Docker containers** - Most mature, well-tested isolation mechanism

**Chosen approach**: Docker-based sandbox with pre-built Python image and strict resource limits.

## Decision: Import Whitelist Strategy
**Rationale**: Based on the LearnPyByAI curriculum structure and security requirements, we need a comprehensive whitelist of safe standard library modules.

### Safe Modules (Allowed)
- **Core Language**: `builtins`, `__future__`, `keyword`, `token`, `tokenize`
- **Data Types**: `bool`, `int`, `float`, `str`, `bytes`, `list`, `tuple`, `dict`, `set`, `frozenset`
- **Mathematics**: `math`, `cmath`, `decimal`, `fractions`, `random`, `statistics`, `numbers`
- **Collections**: `collections`, `collections.abc`, `heapq`, `bisect`, `array`
- **Text Processing**: `string`, `re`, `difflib`, `stringprep`, `textwrap`, `unicodedata`
- **Data Formats**: `json`, `pickle` (with restrictions), `marshal`, `csv`, `xml.etree.ElementTree`
- **Date/Time**: `datetime`, `calendar`, `time` (with restrictions)
- **Algorithms**: `hashlib`, `hmac`, `copy`, `pprint`, `reprlib`
- **File Formats**: `configparser`, `urllib.parse` (for parsing only, no network access)
- **Generic OS Services**: `os.path`, `tempfile` (restricted to temp dir)
- **Data Persistence**: `sqlite3` (with restrictions)
- **Structural Patterns**: `enum`, `dataclasses`, `types`
- **Functional Programming**: `functools`, `operator`, `itertools`, `operator`
- **Error Handling**: `warnings`, `traceback` (read-only), `logging` (to stdout only)
- **Internationalization**: `locale`, `gettext`
- **Binary Data**: `struct`, `codecs`, `encodings`
- **File Handling**: `io`, `pathlib` (restricted), `linecache`

### Dangerous Modules (Blocked)
- **System Interaction**: `os`, `sys`, `subprocess`, `ctypes`, `ctypes.util`
- **Networking**: `socket`, `urllib.request`, `urllib.urlopen`, `http.client`, `ftplib`, `smtpd`, `telnetlib`
- **File System**: `shutil`, `glob`, `fnmatch`, `filecmp`, `fileinput`
- **Process Management**: `multiprocessing`, `threading` (limited), `concurrent.futures`
- **Code Execution**: `exec`, `eval`, `compile`, `code`, `codeop`, `imp`, `importlib` (restricted)
- **Platform Access**: `platform`, `sysconfig`, `site`, `distutils`
- **Debugging**: `pdb`, `profile`, `cProfile`, `trace`
- **Low-Level**: `gc`, `weakref`, `sys` attributes, `builtins` manipulation

### Curriculum-Specific Module Mapping
- **Basics**: `builtins`, `math`, `random`, `string`, `datetime`
- **Control Flow**: `builtins`, `math`, `random`
- **Data Structures**: `collections`, `collections.abc`, `heapq`, `array`
- **Functions**: `functools`, `operator`, `itertools`, `dataclasses`
- **OOP**: `types`, `enum`, `dataclasses`
- **Files**: `json`, `csv`, `io`, `pathlib` (restricted)
- **Errors**: `traceback`, `warnings`
- **Libraries**: `urllib.parse` (URL parsing only), `json`, `xml.etree.ElementTree`

## Decision: Error Message Parsing
**Rationale**: Raw Python tracebacks are intimidating for students. We need to parse common error types and provide student-friendly explanations.

**Common Error Types**:
1. **SyntaxError** - Missing colons, parentheses, quotes
2. **IndentationError** - Incorrect indentation
3. **NameError** - Undefined variables/functions
4. **TypeError** - Operation on incompatible types
5. **ValueError** - Valid type but inappropriate value
6. **IndexError** - Accessing out-of-bounds sequence index
7. **KeyError** - Accessing non-existent dictionary key
8. **AttributeError** - Accessing non-existent object attribute

**Implementation Strategy**: Custom error parser that extracts error type, line number, and message, then provides beginner-friendly explanations.

## Decision: Execution Environment Implementation
**Rationale**: Need a secure, isolated execution environment that enforces resource limits and prevents sandbox escapes.

**Technical Approach**:
- Docker container with minimal Python installation
- Custom Python wrapper that validates imports before execution
- Resource limits enforced by Docker (CPU, memory, time)
- Network disabled via Docker configuration
- File system access restricted via Docker volume mounts
- stdin redirected to EOF to prevent hanging on input()

## Decision: Integration with Existing Architecture
**Rationale**: Must integrate seamlessly with existing FastAPI backend and SQLAlchemy models.

**Integration Points**:
- FastAPI endpoint: `/api/v1/code-execution`
- SQLAlchemy model: `CodeSubmission` (from F02)
- Repository: `CodeSubmissionRepository` (from F02)
- Authentication: Uses existing JWT middleware from F01
- Rate limiting: Handled at API Gateway level (F03)

## Security Considerations Resolved
- **Sandbox Escapes**: Prevented by Docker isolation
- **Resource Exhaustion**: Prevented by Docker resource limits
- **Import Bypass**: Prevented by AST parsing of imports before execution
- **Network Access**: Prevented by Docker network configuration
- **File System Access**: Prevented by Docker volume restrictions
- **Process Spawning**: Prevented by Docker containerization
