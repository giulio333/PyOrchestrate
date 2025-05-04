from enum import Enum
from typing import List, Literal, Optional


class ValidationSeverity(Enum):
    """Severity levels for validation errors."""

    WARNING = "warning"  # Error does not block execution
    ERROR = "error"  # Error blocks execution but may be ignored
    CRITICAL = "critical"  # Error always blocks execution


class ValidationResult:
    """Represents the result of a single validation check."""

    def __init__(
        self,
        field: str,
        message: str = "",
        severity: ValidationSeverity = ValidationSeverity.ERROR,
    ):
        """
        Initialize a ValidationResult.

        Args:
            field (str): The configuration field being validated.
            message (str): Detailed message about the validation outcome.
            severity (ValidationSeverity): Severity level of this validation result.
        """
        self.field = field
        self.is_valid = False
        self.message = message
        self.severity = severity

    def __str__(self):
        """Return a human-readable representation of the validation result."""
        return f"{self.severity.value.upper()}: [{self.field}] - {self.message}"


class ConfigValidationError(Exception):
    """Base exception for configuration validation errors."""

    def __init__(
        self, message: str, results: List[ValidationResult], config_class: str = ""
    ):
        """
        Initialize a ConfigValidationError.

        Args:
            message (str): Summary message for the validation failure.
            results (List[ValidationResult]): Detailed list of validation results.
            config_class (str): Name of the configuration class being validated.
        """
        self.message = message
        self.results = results
        self.config_class = config_class

        # Group results by severity
        self.errors = [r for r in results if r.severity == ValidationSeverity.ERROR]
        self.warnings = [r for r in results if r.severity == ValidationSeverity.WARNING]
        self.criticals = [
            r for r in results if r.severity == ValidationSeverity.CRITICAL
        ]

        # Build detailed message
        detailed_message = f"{message} in {config_class}:\n"
        for r in results:
            detailed_message += f"  - {str(r)}\n"

        super().__init__(detailed_message)


class ConfigValidationWarning(Warning):
    """Warning for configuration validation issues that don't block execution."""

    def __init__(
        self, message: str, results: List[ValidationResult], config_class: str = ""
    ):
        """
        Initialize a ConfigValidationWarning.

        Args:
            message (str): Summary message for the validation issues.
            results (List[ValidationResult]): Detailed list of validation results.
            config_class (str): Name of the configuration class being validated.
        """
        self.message = message
        self.results = results
        self.config_class = config_class

        # Group results by severity
        self.errors = []
        self.warnings = [r for r in results if r.severity == ValidationSeverity.WARNING]

        # Build detailed message
        detailed_message = f"{message} in {config_class}:\n"
        for r in results:
            detailed_message += f"  - {str(r)}\n"

        super().__init__(detailed_message)


class ValidationPolicy:
    """
    Policy that determines when to raise an exception on validation failures.

    The validation policy determines how to handle errors and warnings during validation:

    - If `ignore_warnings` is True: warnings are logged as ConfigValidationWarning (logged but don't block execution)
    - If `ignore_warnings` is False: warnings are treated as errors (`ConfigValidationError`, blocking execution)

    - If `ignore_errors` is True: errors are completely ignored
    - If `ignore_errors` is False: errors raise `ConfigValidationError` (blocking execution)

    Critical errors (CRITICAL) always raise `ConfigValidationError`, regardless of the policy settings.
    """

    def __init__(
        self,
        ignore_warnings: bool = True,
        ignore_errors: bool = False,
    ):
        """
        Initialize the ValidationPolicy.

        Args:
            ignore_warnings (bool): If True, warnings are ignored.
            ignore_errors (bool): If True, errors are ignored.
        """
        self.ignore_warnings = ignore_warnings
        self.ignore_errors = ignore_errors

    def should_raise(
        self, results: List[ValidationResult]
    ) -> Optional[Literal["error", "warning"]]:
        """
        Determine what kind of exception should be raised based on validation results and policy.

        Args:
            results (List[ValidationResult]): List of validation results.

        Returns:
            Optional[Literal["error", "warning"]]:
                - "error" if a ConfigValidationError should be raised
                - "warning" if a ConfigValidationWarning should be raised
                - None if no exception should be raised
        """
        has_criticals = any(r.severity == ValidationSeverity.CRITICAL for r in results)
        has_errors = any(r.severity == ValidationSeverity.ERROR for r in results)
        has_warnings = any(r.severity == ValidationSeverity.WARNING for r in results)

        # Always raise error on critical failures
        if has_criticals:
            return "error"

        # Raise error on errors if not set to ignore them
        if has_errors and not self.ignore_errors:
            return "error"

        # If there are warnings and we're not ignoring them, treat them as errors
        if has_warnings and not self.ignore_warnings:
            return "error"

        # Raise warning if there are warnings
        if has_warnings:
            return "warning"

        return None
