import re
from typing import Dict, Optional


class ErrorParser:
    """Parses Python error messages and converts them to student-friendly format."""

    def __init__(self):
        # Map of error patterns to student-friendly explanations
        self.error_patterns = {
            "SyntaxError": [
                (
                    r"invalid syntax",
                    "Syntax Error: There's a mistake in your code syntax. Check for missing colons, parentheses, quotes, or incorrect indentation.",
                ),
                (
                    r"unexpected EOF while parsing",
                    "Syntax Error: Your code is incomplete. You might be missing closing parentheses, brackets, or quotes.",
                ),
                (
                    r"invalid character",
                    "Syntax Error: You have an invalid character in your code. Check for special characters that don't belong.",
                ),
            ],
            "IndentationError": [
                (
                    r"expected an indented block",
                    "Indentation Error: Python expects an indented block after statements like 'if', 'for', 'while', 'def', or 'class'.",
                ),
                (
                    r"unindent does not match",
                    "Indentation Error: Your indentation doesn't match the expected level. Make sure consistent spacing is used.",
                ),
                (
                    r"unexpected indent",
                    "Indentation Error: There's unexpected indentation in your code. Check your spacing.",
                ),
            ],
            "NameError": [
                (
                    r"name '(\w+)' is not defined",
                    r"Name Error: Variable '\1' is not defined. Did you forget to create it or did you misspell its name?",
                ),
                (
                    r"global name '(\w+)' is not defined",
                    r"Name Error: Global variable '\1' is not defined. Did you forget to create it?",
                ),
            ],
            "TypeError": [
                (
                    r"unsupported operand type",
                    "Type Error: You're trying to perform an operation on incompatible types. For example, adding a string to a number.",
                ),
                (
                    r"object of type '(\w+)' has no attribute '(\w+)'",
                    r"Type Error: '\1' object has no attribute '\2'. Are you sure this method exists for this type?",
                ),
                (
                    r"'(\w+)' object is not callable",
                    r"Type Error: '\1' object is not callable. Are you trying to call a variable as a function?",
                ),
            ],
            "ValueError": [
                (
                    r"invalid literal for int",
                    "Value Error: Cannot convert the value to an integer. Make sure the value represents a valid number.",
                ),
                (
                    r"could not convert string to float",
                    "Value Error: Cannot convert the string to a float. Make sure the value represents a valid number.",
                ),
                (
                    r"math domain error",
                    "Value Error: Math domain error. You're trying to perform an operation that's not mathematically valid.",
                ),
            ],
            "IndexError": [
                (
                    r"list index out of range",
                    "Index Error: You're trying to access an index that doesn't exist in the list. Check if your index is within bounds.",
                ),
                (
                    r"string index out of range",
                    "Index Error: You're trying to access an index that doesn't exist in the string. Check if your index is within bounds.",
                ),
                (
                    r"tuple index out of range",
                    "Index Error: You're trying to access an index that doesn't exist in the tuple. Check if your index is within bounds.",
                ),
            ],
            "KeyError": [
                (
                    r"key error: '(\w+)'",
                    r"Key Error: Dictionary key '\1' does not exist. Check if the key exists in your dictionary.",
                ),
                (
                    r"key error: (\d+)",
                    r"Key Error: Dictionary key \1 does not exist. Check if the key exists in your dictionary.",
                ),
            ],
            "AttributeError": [
                (
                    r"'(\w+)' object has no attribute '(\w+)'",
                    r"Attribute Error: '\1' object has no attribute '\2'. Check if this attribute or method exists for this type.",
                ),
            ],
            "ZeroDivisionError": [
                (
                    r"division by zero",
                    "Zero Division Error: You're trying to divide by zero, which is mathematically undefined.",
                ),
            ],
            "ImportError": [
                (
                    r"No module named '(\w+)'",
                    r"Import Error: No module named '\1'. This module is not available or not allowed in the learning environment.",
                ),
            ],
            "ModuleNotFoundError": [
                (
                    r"No module named '(\w+)'",
                    r"Module Not Found Error: No module named '\1'. This module is not available or not allowed in the learning environment.",
                ),
            ],
        }

    def parse_error(self, error_message: str, error_type: str = "Unknown") -> str:
        """Parse an error message and return a student-friendly explanation.

        Args:
            error_message: The raw Python error message
            error_type: The type of error (e.g., SyntaxError, NameError)

        Returns:
            A student-friendly error message with explanation and suggestions
        """
        if not error_message:
            return "An unknown error occurred during execution."

        # First, try to find a specific pattern for the error type
        if error_type in self.error_patterns:
            for pattern, explanation in self.error_patterns[error_type]:
                match = re.search(pattern, error_message, re.IGNORECASE)
                if match:
                    # Replace placeholders in the explanation
                    result = explanation
                    for i, group in enumerate(match.groups(), 1):
                        result = result.replace(f"\\{i}", group)
                    return result

        # If no specific pattern matches, try all patterns
        for err_type, patterns in self.error_patterns.items():
            for pattern, explanation in patterns:
                match = re.search(pattern, error_message, re.IGNORECASE)
                if match:
                    result = explanation
                    for i, group in enumerate(match.groups(), 1):
                        result = result.replace(f"\\{i}", group)
                    return result

        # If no patterns match, provide a generic message
        return self._create_generic_error_message(error_message, error_type)

    def enhance_error_message(
        self,
        error_message: str,
        error_type: str = "Unknown",
        line_number: Optional[int] = None,
    ) -> str:
        """Enhance error messages with additional student-friendly context.

        Args:
            error_message: The raw Python error message
            error_type: The type of error
            line_number: The line number where the error occurred

        Returns:
            Enhanced student-friendly error message
        """
        # First, parse the error normally
        basic_message = self.parse_error(error_message, error_type)

        # Add line number context if available
        if line_number:
            basic_message += f" (occurred around line {line_number})"

        # Add suggestions based on the error type
        suggestions = self._get_suggestions_for_error(error_type)
        if suggestions:
            basic_message += f"\n\n💡 Suggestion: {suggestions}"

        return basic_message

    def _get_suggestions_for_error(self, error_type: str) -> str:
        """Get helpful suggestions for specific error types."""
        suggestions_map = {
            "SyntaxError": "Check for missing colons, parentheses, quotes, or incorrect indentation. Make sure your code follows Python syntax rules.",
            "IndentationError": "Review your indentation. Python requires consistent spacing, typically 4 spaces per indentation level.",
            "NameError": "Make sure you've defined the variable before using it, and check for typos in variable names.",
            "TypeError": "Verify that you're using compatible data types for the operation you're trying to perform.",
            "ValueError": "Ensure the values you're using are appropriate for the operation (e.g., converting strings to numbers).",
            "IndexError": "Check that the index you're using is within the valid range for the sequence.",
            "KeyError": "Verify that the key exists in the dictionary before accessing it.",
            "AttributeError": "Confirm that the attribute or method exists for the object type you're working with.",
            "ZeroDivisionError": "Avoid dividing by zero. Add a check to ensure the divisor is not zero.",
            "ImportError": "The requested module is not available in this environment. Use only allowed standard library modules.",
        }

        return suggestions_map.get(
            error_type, "Review your code and check for common mistakes."
        )

    def _create_generic_error_message(self, error_message: str, error_type: str) -> str:
        """Create a generic student-friendly error message."""
        if error_type == "TimeoutError":
            return "Timeout Error: Your code took too long to execute (maximum 5 seconds). Check for infinite loops or very slow operations."

        if error_type == "SecurityViolation":
            return (
                error_message  # Security violations should already have clear messages
            )

        # Extract line number if available
        line_match = re.search(r"line (\d+)", error_message)
        line_info = f" on line {line_match.group(1)}" if line_match else ""

        return f"{error_type}{line_info}: {error_message}. This error occurred during code execution. Please review your code for syntax or logic issues."

    def extract_line_number(self, error_message: str) -> Optional[int]:
        """Extract the line number from an error message if available."""
        match = re.search(r'File "<string>", line (\d+)', error_message)
        if match:
            return int(match.group(1))
        matches = re.findall(r"line (\d+)", error_message)
        return int(matches[-1]) if matches else None

    def classify_error_type(self, error_message: str) -> str:
        """Classify the error type from the error message."""
        for error_type in self.error_patterns.keys():
            if error_type in error_message:
                return error_type

        # Additional common error types not in patterns
        if "timeout" in error_message.lower():
            return "TimeoutError"
        elif "permission" in error_message.lower():
            return "PermissionError"
        elif (
            "network" in error_message.lower() or "connection" in error_message.lower()
        ):
            return "ConnectionError"

        return "UnknownError"
