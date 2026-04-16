"""
Standardized error types and exception handling for LegalT pipeline.

Provides a hierarchy of custom exceptions that replace generic Python exceptions
for contract analysis operations, enabling better error tracking, logging, and
recovery strategies.
"""

from typing import Optional


class LegalTError(Exception):
    """
    Base exception for all LegalT system errors.
    
    Provides a standardized error format with error codes, messages,
    and additional context details for logging and recovery.
    
    Attributes:
        code: Machine-readable error code (e.g., "FILE_NOT_FOUND")
        message: Human-readable error message
        details: Additional context dict for debugging
    """
    
    def __init__(
        self,
        code: str,
        message: str,
        details: Optional[dict] = None
    ):
        self.code = code
        self.message = message
        self.details = details or {}
        super().__init__(f"[{code}] {message}")

    def to_dict(self) -> dict:
        """Convert exception to dict for JSON serialization."""
        return {
            "error_code": self.code,
            "error_type": self.__class__.__name__,
            "message": self.message,
            "details": self.details,
        }

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.code}, {self.message!r})"


class FileError(LegalTError):
    """File access, format, size, or encoding errors."""
    pass


class ExtractionError(LegalTError):
    """PDF, DOCX, or text extraction failures."""
    pass


class LLMError(LegalTError):
    """LLM API call failures, parse errors, quota exhaustion, or timeouts."""
    pass


class ValidationError(LegalTError):
    """Schema validation, data quality, or consistency errors."""
    pass


class PipelineError(LegalTError):
    """Multi-stage pipeline orchestration, routing, or configuration errors."""
    pass


class RateLimitError(LLMError):
    """LLM provider rate limiting or quota exhaustion."""
    
    def __init__(
        self,
        message: str,
        provider: Optional[str] = None,
        retry_after_seconds: Optional[int] = None,
        details: Optional[dict] = None
    ):
        full_details = details or {}
        if provider:
            full_details["provider"] = provider
        if retry_after_seconds:
            full_details["retry_after_seconds"] = retry_after_seconds
        
        super().__init__(
            code="RATE_LIMIT_EXCEEDED",
            message=message,
            details=full_details
        )
        self.retry_after_seconds = retry_after_seconds


class TimeoutError(LLMError):
    """Request or operation timeout."""
    
    def __init__(
        self,
        message: str,
        timeout_seconds: Optional[float] = None,
        details: Optional[dict] = None
    ):
        full_details = details or {}
        if timeout_seconds:
            full_details["timeout_seconds"] = timeout_seconds
        
        super().__init__(
            code="TIMEOUT",
            message=message,
            details=full_details
        )
        self.timeout_seconds = timeout_seconds
