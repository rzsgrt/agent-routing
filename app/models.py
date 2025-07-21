"""Pydantic models for API requests and responses."""

from typing import Optional
from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    """Request model for the /query endpoint."""

    query: str = Field(
        ...,
        description="The user's natural language query",
        min_length=1,
        max_length=1000,
    )


class QueryResponse(BaseModel):
    """Response model for the /query endpoint."""

    query: str = Field(..., description="The original user query")
    tool_used: str = Field(..., description="The tool that processed the query")
    result: str = Field(..., description="The result from the tool execution")


class ToolResult(BaseModel):
    """Result from tool execution."""

    tool_name: str = Field(
        ..., description="Name of the tool that was executed"
    )
    result: str = Field(..., description="The result from the tool execution")
    success: bool = Field(
        ..., description="Whether the execution was successful"
    )


class ErrorResponse(BaseModel):
    """Response model for error cases."""

    error: str = Field(..., description="Error message")
    detail: Optional[str] = Field(
        default=None, description="Additional error details"
    )
    query: Optional[str] = Field(
        default=None, description="The original query that caused the error"
    )
