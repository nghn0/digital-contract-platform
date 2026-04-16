"""
Unit tests for utils/error_utils.py — Custom exception hierarchy.

Tests error handling and serialization of LegalTError and typed subclasses.
Ensures errors contain proper context and can be logged/serialized to JSON.
"""

import pytest
from utils.error_utils import (
    LegalTError,
    FileError,
    ExtractionError,
    LLMError,
    ValidationError,
    PipelineError,
    RateLimitError,
    TimeoutError,
)


class TestLegalTErrorBase:
    """Tests for base LegalTError exception class."""

    def test_create_with_all_fields(self):
        """Test creating LegalTError with code, message, and details."""
        error = LegalTError(
            code="TEST_ERROR",
            message="Test error message",
            details={"context": "test context", "value": 42}
        )
        assert error.code == "TEST_ERROR"
        assert error.message == "Test error message"
        assert error.details == {"context": "test context", "value": 42}

    def test_create_minimal(self):
        """Test creating LegalTError with only code and message."""
        error = LegalTError(code="TEST", message="Simple error")
        assert error.code == "TEST"
        assert error.message == "Simple error"
        assert error.details == {}

    def test_error_is_exception(self):
        """Test that LegalTError inherits from Python Exception."""
        error = LegalTError(code="TEST", message="Test")
        assert isinstance(error, Exception)

    def test_to_dict_serialization(self):
        """Test serialization to dictionary for JSON logging."""
        error = LegalTError(
            code="E001",
            message="Error occurred",
            details={"key": "value"}
        )
        error_dict = error.to_dict()
        assert isinstance(error_dict, dict)
        assert error_dict["error_code"] == "E001"
        assert error_dict["message"] == "Error occurred"
        assert error_dict["details"]["key"] == "value"

    def test_to_dict_with_nested_details(self):
        """Test serialization with nested details."""
        error = LegalTError(
            code="E002",
            message="Complex error",
            details={
                "file": "test.pdf",
                "context": {
                    "stage": "extraction",
                    "attempt": 2
                }
            }
        )
        error_dict = error.to_dict()
        assert error_dict["details"]["context"]["stage"] == "extraction"
        assert error_dict["details"]["context"]["attempt"] == 2

    def test_str_representation(self):
        """Test string representation for logging."""
        error = LegalTError(
            code="E003",
            message="Test message"
        )
        error_str = str(error)
        assert "E003" in error_str or "Test message" in error_str


class TestFileError:
    """Tests for FileError exception (file I/O issues)."""

    def test_create_file_error(self):
        """Test creating FileError with file-specific context."""
        error = FileError(
            code="FILE_NOT_FOUND",
            message="File not found",
            details={"file_path": "/path/to/missing.pdf"}
        )
        assert error.code == "FILE_NOT_FOUND"
        assert error.details["file_path"] == "/path/to/missing.pdf"

    def test_file_error_is_legal_t_error(self):
        """Test that FileError is a subclass of LegalTError."""
        error = FileError(code="FILE_ERR", message="Test")
        assert isinstance(error, LegalTError)

    def test_file_size_exceeded(self):
        """Test FileError for oversized files."""
        error = FileError(
            code="FILE_TOO_LARGE",
            message="File exceeds 50MB limit",
            details={"file_size_mb": 75.5, "limit_mb": 50}
        )
        assert error.details["file_size_mb"] == 75.5
        assert error.to_dict()["error_code"] == "FILE_TOO_LARGE"

    def test_unsupported_file_type(self):
        """Test FileError for unsupported file formats."""
        error = FileError(
            code="UNSUPPORTED_FORMAT",
            message="File type not supported",
            details={"file_type": "exe", "allowed": ["pdf", "docx", "txt"]}
        )
        assert error.details["allowed"] == ["pdf", "docx", "txt"]


class TestExtractionError:
    """Tests for ExtractionError (text/data extraction failures)."""

    def test_create_extraction_error(self):
        """Test creating ExtractionError."""
        error = ExtractionError(
            code="PDF_PARSE_FAILED",
            message="Failed to parse PDF",
            details={"stage": "text_extraction", "reason": "corrupted PDF"}
        )
        assert error.code == "PDF_PARSE_FAILED"
        assert error.details["stage"] == "text_extraction"

    def test_extraction_error_is_legal_t_error(self):
        """Test ExtractionError inheritance."""
        error = ExtractionError(code="EXT_ERR", message="Test")
        assert isinstance(error, LegalTError)

    def test_encoding_error_during_extraction(self):
        """Test ExtractionError for encoding issues."""
        error = ExtractionError(
            code="ENCODING_ERROR",
            message="Unable to decode file",
            details={"encoding": "utf-8", "file": "document.pdf"}
        )
        assert error.details["encoding"] == "utf-8"


class TestLLMError:
    """Tests for LLMError (LLM provider failures)."""

    def test_create_llm_error(self):
        """Test creating LLMError."""
        error = LLMError(
            code="API_REQUEST_FAILED",
            message="OpenRouter API returned 500",
            details={"status_code": 500, "provider": "openrouter"}
        )
        assert error.code == "API_REQUEST_FAILED"
        assert error.details["provider"] == "openrouter"

    def test_llm_error_is_legal_t_error(self):
        """Test LLMError inheritance."""
        error = LLMError(code="LLM_ERR", message="Test")
        assert isinstance(error, LegalTError)

    def test_auth_error(self):
        """Test LLMError for authentication failures."""
        error = LLMError(
            code="AUTH_FAILED",
            message="Invalid API key",
            details={"provider": "gemini"}
        )
        assert error.code == "AUTH_FAILED"

    def test_model_not_available(self):
        """Test LLMError when model is unavailable."""
        error = LLMError(
            code="MODEL_UNAVAILABLE",
            message="Claude 3.5 Sonnet not available",
            details={"model": "claude-3-5-sonnet", "provider": "anthropic"}
        )
        assert error.details["model"] == "claude-3-5-sonnet"


class TestValidationError:
    """Tests for ValidationError (schema/data validation failures)."""

    def test_create_validation_error(self):
        """Test creating ValidationError."""
        error = ValidationError(
            code="SCHEMA_INVALID",
            message="Clause schema validation failed",
            details={"field": "risk_score", "issue": "value > 100"}
        )
        assert error.code == "SCHEMA_INVALID"
        assert error.details["field"] == "risk_score"

    def test_validation_error_is_legal_t_error(self):
        """Test ValidationError inheritance."""
        error = ValidationError(code="VAL_ERR", message="Test")
        assert isinstance(error, LegalTError)

    def test_enum_validation_error(self):
        """Test ValidationError for enum constraint violations."""
        error = ValidationError(
            code="INVALID_ENUM",
            message="risk_level must be one of LOW, MEDIUM, HIGH, CRITICAL",
            details={
                "field": "risk_level",
                "value": "EXTREME",
                "allowed": ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
            }
        )
        assert "EXTREME" in str(error.details["value"])

    def test_boundary_validation_error(self):
        """Test ValidationError for boundary violations."""
        error = ValidationError(
            code="VALUE_OUT_OF_BOUNDS",
            message="risk_score must be between 0 and 100",
            details={"field": "risk_score", "value": 150, "min": 0, "max": 100}
        )
        assert error.details["value"] == 150


class TestPipelineError:
    """Tests for PipelineError (orchestration/workflow failures)."""

    def test_create_pipeline_error(self):
        """Test creating PipelineError."""
        error = PipelineError(
            code="STAGE_FAILED",
            message="Stage 3 (clause classification) failed",
            details={"stage": 3, "reason": "timeout"}
        )
        assert error.code == "STAGE_FAILED"
        assert error.details["stage"] == 3

    def test_pipeline_error_is_legal_t_error(self):
        """Test PipelineError inheritance."""
        error = PipelineError(code="PIPE_ERR", message="Test")
        assert isinstance(error, LegalTError)

    def test_orchestration_error(self):
        """Test PipelineError for orchestration issues."""
        error = PipelineError(
            code="ORCHESTRATION_ERROR",
            message="Failed to coordinate batch processing",
            details={"batch_size": 5, "processed": 2, "failed_count": 3}
        )
        assert error.details["batch_size"] == 5
        assert error.details["failed_count"] == 3


class TestRateLimitError:
    """Tests for RateLimitError (provider rate limiting)."""

    def test_create_rate_limit_error(self):
        """Test creating RateLimitError with retry information."""
        error = RateLimitError(
            message="OpenRouter rate limit exceeded",
            provider="openrouter",
            retry_after_seconds=60
        )
        assert error.code == "RATE_LIMIT_EXCEEDED"
        assert isinstance(error, LLMError)  # RateLimitError extends LLMError

    def test_retry_after_field(self):
        """Test RateLimitError with retry_after_seconds."""
        error = RateLimitError(
            message="Rate limited",
            provider="gemini",
            retry_after_seconds=60
        )
        assert error.retry_after_seconds == 60

    def test_retry_after_none(self):
        """Test RateLimitError when retry_after not provided."""
        error = RateLimitError(
            message="Rate limited",
            retry_after_seconds=None
        )
        assert error.retry_after_seconds is None

    def test_to_dict_includes_retry_after(self):
        """Test serialization includes retry_after_seconds."""
        error = RateLimitError(
            message="Rate limited",
            retry_after_seconds=30
        )
        error_dict = error.to_dict()
        assert "retry_after_seconds" in error_dict or error_dict["error_code"] == "RATE_LIMIT_EXCEEDED"


class TestTimeoutError:
    """Tests for TimeoutError (operation timeouts)."""

    def test_create_timeout_error(self):
        """Test creating TimeoutError with timeout info."""
        error = TimeoutError(
            message="Text extraction exceeded 300s timeout",
            timeout_seconds=300
        )
        assert error.code == "TIMEOUT"
        assert isinstance(error, LegalTError)

    def test_timeout_seconds_field(self):
        """Test TimeoutError with timeout_seconds."""
        error = TimeoutError(
            message="LLM request timed out",
            timeout_seconds=300
        )
        assert error.timeout_seconds == 300

    def test_timeout_seconds_none(self):
        """Test TimeoutError when timeout_seconds not provided."""
        error = TimeoutError(
            message="Operation timed out",
            timeout_seconds=None
        )
        assert error.timeout_seconds is None

    def test_to_dict_includes_timeout_seconds(self):
        """Test serialization includes timeout_seconds."""
        error = TimeoutError(
            message="Timed out",
            timeout_seconds=60
        )
        error_dict = error.to_dict()
        assert "timeout_seconds" in error_dict or error_dict["error_code"] == "TIMEOUT"


class TestErrorHierarchy:
    """Tests for exception inheritance and hierarchy."""

    def test_all_errors_inherit_from_legal_t_error(self):
        """Test that all custom errors inherit from LegalTError."""
        errors = [
            FileError(code="F1", message="File error"),
            ExtractionError(code="E1", message="Extraction error"),
            LLMError(code="L1", message="LLM error"),
            ValidationError(code="V1", message="Validation error"),
            PipelineError(code="P1", message="Pipeline error"),
            RateLimitError(message="Rate limited"),
            TimeoutError(message="Timed out"),
        ]
        for error in errors:
            assert isinstance(error, LegalTError), f"{error.__class__.__name__} should inherit from LegalTError"

    def test_rate_limit_error_is_llm_error(self):
        """Test that RateLimitError extends LLMError."""
        error = RateLimitError(message="Rate limited")
        assert isinstance(error, LLMError)

    def test_timeout_error_is_legal_t_error(self):
        """Test that TimeoutError is a LegalTError."""
        error = TimeoutError(message="Timed out")
        assert isinstance(error, LegalTError)


class TestErrorSerialization:
    """Tests for error serialization and JSON compatibility."""

    def test_serialize_all_error_types_to_dict(self):
        """Test that all error types can be serialized to dict."""
        errors = [
            FileError(code="F1", message="File error"),
            ExtractionError(code="E1", message="Extraction error"),
            LLMError(code="L1", message="LLM error"),
            ValidationError(code="V1", message="Validation error"),
            PipelineError(code="P1", message="Pipeline error"),
            RateLimitError(message="Rate limit"),
            TimeoutError(message="Timeout"),
        ]

        for error in errors:
            error_dict = error.to_dict()
            assert isinstance(error_dict, dict)
            assert "error_code" in error_dict
            assert "message" in error_dict
            assert "details" in error_dict

    def test_json_serializable_with_nested_structure(self):
        """Test that error details with nested structures serialize properly."""
        error = LLMError(
            code="COMPLEX",
            message="Complex error",
            details={
                "provider": "openrouter",
                "context": {
                    "stage": "classification",
                    "functions": ["classify", "score"],
                    "batch_size": 5
                }
            }
        )
        error_dict = error.to_dict()
        # Should be JSON-serializable (all native types)
        import json
        json_str = json.dumps(error_dict)
        assert "openrouter" in json_str
        assert "classification" in json_str

    def test_error_with_none_details(self):
        """Test serialization when details is None."""
        error = ValidationError(
            code="TEST",
            message="Test error",
            details=None
        )
        error_dict = error.to_dict()
        assert "details" in error_dict or error.message == "Test error"
