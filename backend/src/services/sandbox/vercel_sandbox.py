"""Vercel Sandbox-based code execution using ephemeral microVMs.

Replaces DockerSandbox when running on Vercel (VERCEL=1), where Docker is
unavailable. Each execution spins up a fresh python3.13 microVM, runs the
student's code, then stops the VM.
"""

import logging
import time
from typing import Optional, Tuple

from .base import ExecutionResult, SandboxInterface
from .error_parser import ErrorParser
from .import_validator import ImportValidator

logger = logging.getLogger(__name__)


def _classify_error(stderr: str) -> str:
    for label in (
        "SyntaxError", "IndentationError", "NameError", "TypeError",
        "ValueError", "AttributeError", "ImportError", "IndexError",
        "KeyError", "ZeroDivisionError", "RecursionError", "MemoryError",
    ):
        if label in stderr:
            return label
    return "RuntimeError"


class VercelSandbox(SandboxInterface):
    """Code execution via Vercel Sandbox ephemeral microVMs."""

    def __init__(self):
        self.import_validator = ImportValidator()
        self.error_parser = ErrorParser()

    async def validate_imports(self, code: str) -> Tuple[bool, Optional[str]]:
        return self.import_validator.validate_imports(code)

    async def execute_code(
        self, code: str, timeout_seconds: int = 5, memory_limit: str = "50MB"
    ) -> ExecutionResult:
        start_time = time.time()

        is_valid, error_msg = await self.validate_imports(code)
        if not is_valid:
            execution_time = int((time.time() - start_time) * 1000)
            logger.warning(f"Import validation failed: {error_msg}")
            return ExecutionResult(
                success=False,
                output="",
                error_message=error_msg,
                error_type="SecurityViolation",
                execution_time_ms=execution_time,
                status="blocked",
            )

        from vercel.sandbox import AsyncSandbox, WriteFile

        # Give the sandbox extra time beyond the code timeout for startup/teardown
        sandbox_lifetime_ms = (timeout_seconds + 15) * 1000

        sandbox = None
        try:
            sandbox = await AsyncSandbox.create(
                runtime="python3.13",
                timeout=sandbox_lifetime_ms,
                network_policy="deny-all",
            )

            await sandbox.write_files(
                [WriteFile(path="/vercel/sandbox/code.py", content=code.encode())]
            )

            # `timeout` exits with code 124 on expiry — detected below
            result = await sandbox.run_command(
                "timeout",
                [str(timeout_seconds), "python3", "/vercel/sandbox/code.py"],
            )

            execution_time = int((time.time() - start_time) * 1000)
            stdout = await result.stdout()
            stderr = await result.stderr()
            exit_code = result.exit_code

            if exit_code == 124:
                return ExecutionResult(
                    success=False,
                    output=stdout,
                    error_message="Execution timed out",
                    error_type="TimeoutError",
                    execution_time_ms=timeout_seconds * 1000,
                    status="timeout",
                )

            if exit_code != 0:
                return ExecutionResult(
                    success=False,
                    output=stdout,
                    error_message=stderr or "Runtime error",
                    error_type=_classify_error(stderr),
                    execution_time_ms=execution_time,
                    status="error",
                )

            return ExecutionResult(
                success=True,
                output=stdout,
                error_message=None,
                error_type=None,
                execution_time_ms=execution_time,
                status="success",
            )

        except Exception as e:
            execution_time = int((time.time() - start_time) * 1000)
            error_msg = str(e)
            logger.error(f"Unexpected error during Vercel Sandbox execution: {error_msg}")
            return ExecutionResult(
                success=False,
                output="",
                error_message=error_msg,
                error_type="InfrastructureError",
                execution_time_ms=execution_time,
                status="infrastructure_failure",
            )
        finally:
            if sandbox is not None:
                try:
                    await sandbox.stop()
                except Exception:
                    pass
