"""Logging configuration for the AI Agent Backend."""

import logging
import sys
from typing import Dict, Any


def setup_logging(level: str = "INFO") -> logging.Logger:
    """
    Set up logging configuration for the application.

    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)

    Returns:
        Configured logger instance
    """
    # Configure logging format
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    # Configure logging
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format=log_format,
        handlers=[logging.StreamHandler(sys.stdout)],
    )

    # Get the root logger
    logger = logging.getLogger("ai_agent")

    # Set specific loggers
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)

    return logger


# Initialize default logger for the module
logger = setup_logging()


def log_request_start(query: str) -> Dict[str, Any]:
    """
    Log the start of a request.

    Args:
        query: The user query

    Returns:
        Log data dictionary
    """
    logger.info(f"Processing query: {query}")
    return {"query": query}


def log_tool_execution(tool_name: str, duration: float, status: str) -> None:
    """
    Log tool execution results.

    Args:
        tool_name: Name of the tool that was executed
        duration: Execution duration in seconds
        status: Execution status (success/error)
    """
    logger.info(
        f"Tool execution completed: {tool_name} "
        f"(duration: {duration:.3f}s, status: {status})"
    )
