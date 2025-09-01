"""
Error handling utilities for Gemini URL Search Tool.
"""

import logging
import time
from typing import Dict, Any, Optional, Callable
from dataclasses import dataclass
from enum import Enum


logger = logging.getLogger(__name__)


class ErrorType(Enum):
    """Types of errors that can occur."""
    API_ERROR = "api_error"
    RATE_LIMIT = "rate_limit"
    AUTHENTICATION = "authentication"
    NETWORK = "network"
    TIMEOUT = "timeout"
    VALIDATION = "validation"
    CONTENT_PROCESSING = "content_processing"
    DATABASE = "database"
    UNKNOWN = "unknown"


@dataclass
class ErrorContext:
    """Context information for error handling."""
    operation: str
    timestamp: float
    retry_count: int = 0
    model_used: Optional[str] = None
    additional_info: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.additional_info is None:
            self.additional_info = {}


class GeminiAPIError(Exception):
    """Base exception for Gemini API related errors."""
    
    def __init__(self, message: str, error_type: ErrorType = ErrorType.API_ERROR, context: Optional[ErrorContext] = None):
        super().__init__(message)
        self.error_type = error_type
        self.context = context or ErrorContext(operation="unknown", timestamp=time.time())


class RateLimitError(GeminiAPIError):
    """Exception raised when API rate limit is exceeded."""
    
    def __init__(self, message: str, retry_after: Optional[int] = None, context: Optional[ErrorContext] = None):
        super().__init__(message, ErrorType.RATE_LIMIT, context)
        self.retry_after = retry_after


class AuthenticationError(GeminiAPIError):
    """Exception raised when API authentication fails."""
    
    def __init__(self, message: str, context: Optional[ErrorContext] = None):
        super().__init__(message, ErrorType.AUTHENTICATION, context)


class NetworkError(GeminiAPIError):
    """Exception raised for network-related issues."""
    
    def __init__(self, message: str, context: Optional[ErrorContext] = None):
        super().__init__(message, ErrorType.NETWORK, context)


class TimeoutError(GeminiAPIError):
    """Exception raised when operations timeout."""
    
    def __init__(self, message: str, timeout_duration: Optional[float] = None, context: Optional[ErrorContext] = None):
        super().__init__(message, ErrorType.TIMEOUT, context)
        self.timeout_duration = timeout_duration


class ValidationError(GeminiAPIError):
    """Exception raised for input validation errors."""
    
    def __init__(self, message: str, field: Optional[str] = None, context: Optional[ErrorContext] = None):
        super().__init__(message, ErrorType.VALIDATION, context)
        self.field = field


class ContentProcessingError(GeminiAPIError):
    """Exception raised during content processing."""
    
    def __init__(self, message: str, url: Optional[str] = None, context: Optional[ErrorContext] = None):
        super().__init__(message, ErrorType.CONTENT_PROCESSING, context)
        self.url = url


class ContentFetchError(GeminiAPIError):
    """Exception raised when content cannot be fetched from URL."""
    
    def __init__(self, message: str, url: Optional[str] = None, context: Optional[ErrorContext] = None):
        super().__init__(message, ErrorType.NETWORK, context)
        self.url = url


class DatabaseError(GeminiAPIError):
    """Exception raised for database operations."""
    
    def __init__(self, message: str, operation: Optional[str] = None, context: Optional[ErrorContext] = None):
        super().__init__(message, ErrorType.DATABASE, context)
        self.operation = operation


class SearchError(GeminiAPIError):
    """Exception raised for search operation errors."""
    
    def __init__(self, message: str, query: Optional[str] = None, context: Optional[ErrorContext] = None):
        super().__init__(message, ErrorType.API_ERROR, context)
        self.query = query


class ErrorHandler:
    """
    Centralized error handling and retry logic.
    """
    
    def __init__(self):
        self.retry_config = {
            ErrorType.RATE_LIMIT: {
                'max_retries': 5,
                'backoff_factor': 2.0,
                'base_delay': 1.0,
                'max_delay': 60.0
            },
            ErrorType.NETWORK: {
                'max_retries': 3,
                'backoff_factor': 1.5,
                'base_delay': 1.0,
                'max_delay': 30.0
            },
            ErrorType.TIMEOUT: {
                'max_retries': 2,
                'backoff_factor': 2.0,
                'base_delay': 2.0,
                'max_delay': 30.0
            },
            ErrorType.API_ERROR: {
                'max_retries': 2,
                'backoff_factor': 1.5,
                'base_delay': 1.0,
                'max_delay': 15.0
            },
            ErrorType.AUTHENTICATION: {
                'max_retries': 0,  # No retries for auth errors
                'backoff_factor': 1.0,
                'base_delay': 0.0,
                'max_delay': 0.0
            },
            ErrorType.VALIDATION: {
                'max_retries': 0,  # No retries for validation errors
                'backoff_factor': 1.0,
                'base_delay': 0.0,
                'max_delay': 0.0
            },
            ErrorType.CONTENT_PROCESSING: {
                'max_retries': 2,  # Limited retries for content processing
                'backoff_factor': 1.5,
                'base_delay': 1.0,
                'max_delay': 10.0
            }
        }
        
        self.error_stats = {
            error_type: {
                'count': 0,
                'last_occurrence': None,
                'total_retry_time': 0.0
            }
            for error_type in ErrorType
        }
    
    def handle_error(self, error: Exception, context: ErrorContext) -> Dict[str, Any]:
        """
        Handle an error and determine appropriate response.
        
        Args:
            error: The exception that occurred
            context: Context information about the error
            
        Returns:
            Dictionary with error handling recommendations
        """
        error_type = self._classify_error(error)
        
        # Update statistics
        self._update_error_stats(error_type)
        
        # Log the error
        self._log_error(error, error_type, context)
        
        # Determine retry strategy
        retry_info = self._get_retry_strategy(error_type, context.retry_count)
        
        return {
            'error_type': error_type,
            'should_retry': retry_info['should_retry'],
            'delay': retry_info['delay'],
            'max_retries_reached': retry_info['max_retries_reached'],
            'user_message': self._get_user_friendly_message(error, error_type),
            'technical_details': str(error),
            'context': context
        }
    
    def _classify_error(self, error: Exception) -> ErrorType:
        """Classify an error into an ErrorType."""
        if isinstance(error, GeminiAPIError):
            return error.error_type
        
        error_str = str(error).lower()
        
        # Check for specific error patterns
        if any(keyword in error_str for keyword in ['rate', 'quota', 'limit']):
            return ErrorType.RATE_LIMIT
        elif any(keyword in error_str for keyword in ['auth', 'key', 'permission', 'unauthorized']):
            return ErrorType.AUTHENTICATION
        elif any(keyword in error_str for keyword in ['timeout', 'timed out']):
            return ErrorType.TIMEOUT
        elif any(keyword in error_str for keyword in ['network', 'connection', 'dns', 'resolve']):
            return ErrorType.NETWORK
        elif any(keyword in error_str for keyword in ['validation', 'invalid', 'malformed']):
            return ErrorType.VALIDATION
        elif any(keyword in error_str for keyword in ['content', 'parse', 'decode']):
            return ErrorType.CONTENT_PROCESSING
        elif any(keyword in error_str for keyword in ['database', 'sql', 'sqlite']):
            return ErrorType.DATABASE
        else:
            return ErrorType.UNKNOWN
    
    def _get_retry_strategy(self, error_type: ErrorType, current_retry_count: int) -> Dict[str, Any]:
        """
        Determine retry strategy for an error type.
        
        Args:
            error_type: Type of error
            current_retry_count: Current number of retries attempted
            
        Returns:
            Dictionary with retry strategy information
        """
        config = self.retry_config.get(error_type, {
            'max_retries': 1,
            'backoff_factor': 1.0,
            'base_delay': 1.0,
            'max_delay': 10.0
        })
        
        max_retries = config['max_retries']
        should_retry = current_retry_count < max_retries
        max_retries_reached = current_retry_count >= max_retries
        
        if should_retry:
            # Calculate exponential backoff delay
            delay = min(
                config['base_delay'] * (config['backoff_factor'] ** current_retry_count),
                config['max_delay']
            )
        else:
            delay = 0.0
        
        return {
            'should_retry': should_retry,
            'delay': delay,
            'max_retries_reached': max_retries_reached,
            'max_retries': max_retries
        }
    
    def _update_error_stats(self, error_type: ErrorType) -> None:
        """Update error statistics."""
        stats = self.error_stats[error_type]
        stats['count'] += 1
        stats['last_occurrence'] = time.time()
    
    def _log_error(self, error: Exception, error_type: ErrorType, context: ErrorContext) -> None:
        """Log error with appropriate level and context."""
        log_message = (
            f"Error in {context.operation}: {str(error)} "
            f"(type: {error_type.value}, retry: {context.retry_count})"
        )
        
        if context.model_used:
            log_message += f", model: {context.model_used}"
        
        if context.additional_info:
            log_message += f", info: {context.additional_info}"
        
        # Log with appropriate level based on error type
        if error_type in [ErrorType.AUTHENTICATION, ErrorType.DATABASE]:
            logger.error(log_message, exc_info=True)
        elif error_type in [ErrorType.RATE_LIMIT, ErrorType.TIMEOUT]:
            logger.warning(log_message)
        else:
            logger.info(log_message)
    
    def _get_user_friendly_message(self, error: Exception, error_type: ErrorType) -> str:
        """Generate user-friendly error message."""
        messages = {
            ErrorType.RATE_LIMIT: "API使用量の制限に達しました。しばらく待ってから再試行してください。",
            ErrorType.AUTHENTICATION: "API認証に失敗しました。APIキーの設定を確認してください。",
            ErrorType.NETWORK: "ネットワーク接続に問題があります。インターネット接続を確認してください。",
            ErrorType.TIMEOUT: "処理がタイムアウトしました。しばらく待ってから再試行してください。",
            ErrorType.VALIDATION: "入力データに問題があります。入力内容を確認してください。",
            ErrorType.CONTENT_PROCESSING: "コンテンツの処理中にエラーが発生しました。",
            ErrorType.DATABASE: "データベース操作でエラーが発生しました。",
            ErrorType.API_ERROR: "API呼び出しでエラーが発生しました。",
            ErrorType.UNKNOWN: "予期しないエラーが発生しました。"
        }
        
        return messages.get(error_type, "エラーが発生しました。")
    
    def get_error_statistics(self) -> Dict[str, Any]:
        """Get error statistics summary."""
        total_errors = sum(stats['count'] for stats in self.error_stats.values())
        
        return {
            'total_errors': total_errors,
            'by_type': {
                error_type.value: {
                    'count': stats['count'],
                    'percentage': (stats['count'] / total_errors * 100) if total_errors > 0 else 0,
                    'last_occurrence': stats['last_occurrence']
                }
                for error_type, stats in self.error_stats.items()
                if stats['count'] > 0
            }
        }
    
    def reset_statistics(self) -> None:
        """Reset error statistics."""
        for stats in self.error_stats.values():
            stats['count'] = 0
            stats['last_occurrence'] = None
            stats['total_retry_time'] = 0.0


# Global error handler instance
error_handler = ErrorHandler()


def handle_api_error(func: Callable) -> Callable:
    """
    Decorator for handling API errors with automatic retry logic.
    
    Args:
        func: Function to wrap with error handling
        
    Returns:
        Wrapped function with error handling
    """
    async def wrapper(*args, **kwargs):
        context = ErrorContext(
            operation=func.__name__,
            timestamp=time.time()
        )
        
        max_attempts = 3
        for attempt in range(max_attempts):
            try:
                context.retry_count = attempt
                return await func(*args, **kwargs)
            
            except Exception as e:
                error_info = error_handler.handle_error(e, context)
                
                if not error_info['should_retry'] or attempt == max_attempts - 1:
                    raise e
                
                # Wait before retry
                if error_info['delay'] > 0:
                    import asyncio
                    await asyncio.sleep(error_info['delay'])
    
    return wrapper


def validate_input(value: Any, field_name: str, validator: Callable[[Any], bool], error_message: str = None) -> None:
    """
    Validate input value and raise ValidationError if invalid.
    
    Args:
        value: Value to validate
        field_name: Name of the field being validated
        validator: Function that returns True if value is valid
        error_message: Custom error message
        
    Raises:
        ValidationError: If validation fails
    """
    if not validator(value):
        message = error_message or f"Invalid value for {field_name}: {value}"
        raise ValidationError(message, field=field_name)


def validate_url(url: str) -> bool:
    """Validate URL format."""
    import re
    url_pattern = re.compile(
        r'^https?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    return url_pattern.match(url) is not None


def validate_api_key(api_key: str) -> bool:
    """Validate API key format."""
    return isinstance(api_key, str) and len(api_key.strip()) > 0


def validate_search_query(query: str) -> bool:
    """Validate search query."""
    return isinstance(query, str) and len(query.strip()) > 0 and len(query.strip()) <= 1000