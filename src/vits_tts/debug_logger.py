import logging
import time
from datetime import datetime
from typing import Any, Dict, Optional

class DebugLogger:
    """
    A debug logger that provides structured logging with additional context
    for debugging purposes. Wraps around the standard logging module.
    """

    def __init__(self, name: str = "debug_logger", level: int = logging.DEBUG):
        """
        Initialize the debug logger.
        
        Args:
            name: Name of the logger
            level: Logging level
        """
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)
        
        # Create console handler if not already exists
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
    
    def _log_with_context(
        self,
        level: int,
        message: str,
        extra: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> None:
        """
        Log a message with additional context.
        
        Args:
            level: Logging level
            message: Log message
            extra: Additional context dictionary
            **kwargs: Additional key-value pairs to include in context
        """
        # Create context dictionary
        context = {
            "timestamp": datetime.utcnow().isoformat(),
            "epoch_time": time.time(),
        }
        
        # Add extra context if provided
        if extra:
            context.update(extra)
        
        # Add any additional keyword arguments
        context.update(kwargs)
        
        # Log the message with context
        self.logger.log(level, message, extra={"context": context})
    
    def debug(self, message: str, extra: Optional[Dict[str, Any]] = None, **kwargs) -> None:
        """Log a debug message with context."""
        self._log_with_context(logging.DEBUG, message, extra, **kwargs)
    
    def info(self, message: str, extra: Optional[Dict[str, Any]] = None, **kwargs) -> None:
        """Log an info message with context."""
        self._log_with_context(logging.INFO, message, extra, **kwargs)
    
    def warning(self, message: str, extra: Optional[Dict[str, Any]] = None, **kwargs) -> None:
        """Log a warning message with context."""
        self._log_with_context(logging.WARNING, message, extra, **kwargs)
    
    def error(self, message: str, extra: Optional[Dict[str, Any]] = None, **kwargs) -> None:
        """Log an error message with context."""
        self._log_with_context(logging.ERROR, message, extra, **kwargs)
    
    def critical(self, message: str, extra: Optional[Dict[str, Any]] = None, **kwargs) -> None:
        """Log a critical message with context."""
        self._log_with_context(logging.CRITICAL, message, extra, **kwargs)
    
    def log_function_call(
        self,
        func_name: str,
        args: tuple = (),
        kwargs: Optional[Dict[str, Any]] = None,
        result: Any = None,
        error: Optional[Exception] = None,
        execution_time: Optional[float] = None
    ) -> None:
        """
        Log a function call with its parameters and result.
        
        Args:
            func_name: Name of the function being called
            args: Positional arguments passed to the function
            kwargs: Keyword arguments passed to the function
            result: Return value of the function
            error: Exception if function call failed
            execution_time: Time taken to execute the function
        """
        context = {
            "function": func_name,
            "args": str(args),
            "kwargs": str(kwargs or {}),
        }
        
        if result is not None:
            context["result"] = str(result)
        
        if error is not None:
            context["error"] = str(error)
            self.error(f"Function {func_name} failed", extra=context)
        else:
            if execution_time is not None:
                context["execution_time"] = execution_time
            self.debug(f"Function {func_name} called", extra=context)
    
    def log_performance(
        self,
        operation: str,
        duration: float,
        units: str = "seconds",
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Log performance metrics.
        
        Args:
            operation: Name of the operation
            duration: Duration of the operation
            units: Units of the duration (default: seconds)
            metadata: Additional metadata about the operation
        """
        context = {
            "operation": operation,
            "duration": duration,
            "units": units,
        }
        
        if metadata:
            context.update(metadata)
        
        self.info(f"Performance metric: {operation}", extra=context)
    
    def log_state_change(
        self,
        component: str,
        old_state: str,
        new_state: str,
        reason: Optional[str] = None
    ) -> None:
        """
        Log a state change in a component.
        
        Args:
            component: Name of the component
            old_state: Previous state
            new_state: New state
            reason: Reason for the state change
        """
        context = {
            "component": component,
            "old_state": old_state,
            "new_state": new_state,
        }
        
        if reason:
            context["reason"] = reason
        
        self.info(f"State change: {component}", extra=context)

# Global debug logger instance
debug_logger = DebugLogger("tts_debug")

def get_debug_logger(name: str = None) -> DebugLogger:
    """
    Get a debug logger instance.
    
    Args:
        name: Name of the logger. If None, returns the default instance.
        
    Returns:
        DebugLogger instance
    """
    if name is None:
        return debug_logger
    return DebugLogger(name)

# Example usage and testing
if __name__ == "__main__":
    # Test the debug logger
    logger = get_debug_logger()
    
    # Basic logging
    logger.debug("This is a debug message", user_id="123")
    logger.info("This is an info message", request_id="456")
    logger.warning("This is a warning message", threshold=0.8)
    logger.error("This is an error message", error_code="500")
    
    # Function call logging
    try:
        result = sum([1, 2, 3])
        logger.log_function_call("sum", args=([1, 2, 3],), result=result)
    except Exception as e:
        logger.log_function_call("sum", args=([1, 2, 3],), error=e)
    
    # Performance logging
    start_time = time.time()
    time.sleep(0.1)  # Simulate some work
    end_time = time.time()
    logger.log_performance("test_operation", end_time - start_time)
    
    # State change logging
    logger.log_state_change("audio_processor", "idle", "processing", "new_request")