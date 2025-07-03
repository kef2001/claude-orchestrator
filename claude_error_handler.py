"""Claude API error handling module"""
import re
import time
import random
from typing import Dict, Any, Optional, Callable
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class ClaudeError:
    """Represents a Claude API error"""
    type: str
    message: str
    http_code: Optional[int] = None
    request_id: Optional[str] = None
    is_retryable: bool = False
    retry_after: Optional[int] = None


class ClaudeErrorHandler:
    """Handles errors from Claude API responses"""
    
    # Error type mappings based on HTTP codes
    ERROR_MAPPINGS = {
        400: ("invalid_request_error", "Request format or content issue", False),
        401: ("authentication_error", "API key issue", False),
        403: ("permission_error", "API key lacks permission", False),
        404: ("not_found_error", "Resource not found", False),
        413: ("request_too_large", "Request exceeds size limit", False),
        429: ("rate_limit_error", "Rate limit reached", True),
        500: ("api_error", "Internal server error", True),
        529: ("overloaded_error", "API temporarily overloaded", True),
    }
    
    # Retry configuration
    DEFAULT_MAX_RETRIES = 3
    DEFAULT_BASE_DELAY = 1.0  # seconds
    DEFAULT_MAX_DELAY = 60.0  # seconds
    
    def __init__(self, max_retries: int = DEFAULT_MAX_RETRIES,
                 base_delay: float = DEFAULT_BASE_DELAY,
                 max_delay: float = DEFAULT_MAX_DELAY):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
    
    def parse_streaming_error(self, error_event: str) -> ClaudeError:
        """Parse error from streaming SSE event"""
        # Streaming errors come after 200 OK, so we need different parsing
        error_type = "streaming_error"
        message = error_event
        request_id = None
        is_retryable = False
        
        # Common streaming error patterns
        if "rate_limit" in error_event.lower():
            error_type = "rate_limit_error"
            is_retryable = True
        elif "overloaded" in error_event.lower():
            error_type = "overloaded_error"
            is_retryable = True
        elif "timeout" in error_event.lower():
            error_type = "timeout_error"
            is_retryable = True
        
        # Extract error details from SSE event format
        error_match = re.search(r'"error":\s*{[^}]+}', error_event)
        if error_match:
            try:
                import json
                error_data = json.loads('{' + error_match.group(0) + '}')
                if 'error' in error_data:
                    error_info = error_data['error']
                    error_type = error_info.get('type', error_type)
                    message = error_info.get('message', message)
            except:
                pass
        
        return ClaudeError(
            type=error_type,
            message=message,
            request_id=request_id,
            is_retryable=is_retryable
        )
    
    def parse_error(self, output: str, return_code: int) -> ClaudeError:
        """Parse error from Claude CLI output"""
        error_type = "unknown_error"
        message = output
        request_id = None
        is_retryable = False
        retry_after = None
        http_code = None
        
        # Extract request ID if present
        request_id_match = re.search(r'request[-_]id[:\s]+([a-zA-Z0-9_]+)', output, re.IGNORECASE)
        if request_id_match:
            request_id = request_id_match.group(1)
        
        # Check for specific error patterns in output
        error_patterns = [
            # HTTP error codes
            (r'4\d{2}\s+error|http\s+4\d{2}', 400),
            (r'401\s+unauthorized|authentication\s+error', 401),
            (r'403\s+forbidden|permission\s+denied', 403),
            (r'404\s+not\s+found', 404),
            (r'413\s+payload\s+too\s+large|request\s+too\s+large', 413),
            (r'429\s+too\s+many\s+requests|rate\s+limit', 429),
            (r'5\d{2}\s+error|server\s+error', 500),
            (r'529|overloaded|temporarily\s+unavailable', 529),
            
            # Other error patterns
            (r'invalid\s+request', 400),
            (r'invalid\s+api\s+key|authentication\s+failed', 401),
            (r'insufficient\s+permissions?|access\s+denied', 403),
            (r'resource\s+not\s+found|model\s+not\s+found', 404),
            (r'rate\s+limit\s+exceeded|too\s+many\s+requests', 429),
            (r'internal\s+server\s+error|unexpected\s+error', 500),
            (r'service\s+overloaded|api\s+overloaded', 529),
        ]
        
        for pattern, code in error_patterns:
            if re.search(pattern, output, re.IGNORECASE):
                http_code = code
                error_info = self.ERROR_MAPPINGS.get(code, ("unknown_error", "Unknown error", False))
                error_type, default_message, is_retryable = error_info
                break
        
        # Extract retry-after header if present
        retry_after_match = re.search(r'retry[-_]after[:\s]+(\d+)', output, re.IGNORECASE)
        if retry_after_match:
            retry_after = int(retry_after_match.group(1))
        
        # Extract more specific error message if available
        error_msg_patterns = [
            r'"message"\s*:\s*"([^"]+)"',
            r'error:\s*(.+?)(?:\n|$)',
            r'message:\s*(.+?)(?:\n|$)',
        ]
        
        for pattern in error_msg_patterns:
            match = re.search(pattern, output, re.IGNORECASE)
            if match:
                message = match.group(1).strip()
                break
        
        return ClaudeError(
            type=error_type,
            message=message,
            http_code=http_code,
            request_id=request_id,
            is_retryable=is_retryable,
            retry_after=retry_after
        )
    
    def calculate_retry_delay(self, attempt: int, error: ClaudeError) -> float:
        """Calculate delay before retry using exponential backoff with jitter"""
        if error.retry_after:
            # Use server-provided retry-after value
            return float(error.retry_after)
        
        # Exponential backoff with jitter
        delay = min(self.base_delay * (2 ** attempt), self.max_delay)
        jitter = random.uniform(0, delay * 0.1)  # Add up to 10% jitter
        return delay + jitter
    
    def should_retry(self, error: ClaudeError, attempt: int) -> bool:
        """Determine if request should be retried"""
        if attempt >= self.max_retries:
            return False
        
        return error.is_retryable
    
    def execute_with_retry(self, func: Callable, *args, **kwargs) -> Dict[str, Any]:
        """Execute a function with retry logic for Claude API calls"""
        attempt = 0
        last_error = None
        
        while attempt <= self.max_retries:
            try:
                result = func(*args, **kwargs)
                
                # Check if the result indicates an error
                if isinstance(result, dict) and not result.get('success', True):
                    error_msg = result.get('error', '')
                    error = self.parse_error(error_msg, result.get('return_code', 1))
                    
                    if self.should_retry(error, attempt):
                        delay = self.calculate_retry_delay(attempt, error)
                        logger.warning(
                            f"Retryable error ({error.type}): {error.message}. "
                            f"Retrying in {delay:.1f}s (attempt {attempt + 1}/{self.max_retries})"
                        )
                        if error.request_id:
                            logger.warning(f"Request ID: {error.request_id}")
                        
                        time.sleep(delay)
                        attempt += 1
                        last_error = error
                        continue
                    else:
                        # Non-retryable error
                        logger.error(
                            f"Non-retryable error ({error.type}): {error.message}"
                        )
                        if error.request_id:
                            logger.error(f"Request ID: {error.request_id}")
                        return result
                
                # Success
                return result
                
            except Exception as e:
                # Handle unexpected exceptions
                logger.error(f"Unexpected error during execution: {e}")
                if attempt < self.max_retries:
                    delay = self.calculate_retry_delay(attempt, ClaudeError(
                        type="unexpected_error",
                        message=str(e),
                        is_retryable=True
                    ))
                    logger.warning(f"Retrying in {delay:.1f}s (attempt {attempt + 1}/{self.max_retries})")
                    time.sleep(delay)
                    attempt += 1
                    continue
                else:
                    return {
                        'success': False,
                        'error': f"Unexpected error: {e}"
                    }
        
        # Max retries exceeded
        if last_error:
            return {
                'success': False,
                'error': f"Max retries exceeded. Last error: {last_error.message}",
                'request_id': last_error.request_id
            }
        else:
            return {
                'success': False,
                'error': "Max retries exceeded"
            }