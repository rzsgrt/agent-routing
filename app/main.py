"""Main FastAPI application for the AI Agent Backend."""

import logging
from contextlib import asynccontextmanager
from typing import Dict, Any

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse

from .agents.main_agent import MainAgent
from .models import QueryRequest, QueryResponse
from .logging_config import log_request_start, log_tool_execution

logger = logging.getLogger(__name__)

# Global agent instance
router_agent = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    global router_agent
    logger.info("Starting AI Agent Backend...")

    # Initialize the agent
    router_agent = MainAgent()

    yield

    # Cleanup on shutdown
    logger.info("Shutting down AI Agent Backend...")


# Create FastAPI app
app = FastAPI(
    title="AI Agent Backend",
    description="An AI agent that routes queries to appropriate tools",
    version="1.0.0",
    lifespan=lifespan,
)


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler for unhandled errors."""
    logger.error(f"Unhandled error: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": "An unexpected error occurred",
        },
    )


@app.get("/")
async def root() -> Dict[str, Any]:
    """Root endpoint providing API information."""
    return {
        "name": "AI Agent Backend",
        "version": "1.0.0",
        "description": (
            "An intelligent agent that routes queries to " "specialized tools"
        ),
        "endpoints": {
            "health": "GET /health - Health check",
            "query": "POST /query - Process a user query",
        },
    }


@app.get("/health")
async def health_check() -> Dict[str, str]:
    """Health check endpoint."""
    return {"status": "healthy"}


@app.post("/query", response_model=QueryResponse)
async def process_query(request: QueryRequest) -> QueryResponse:
    """Process a user query through the AI agent."""
    if not request.query or not request.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")

    if not router_agent:
        raise HTTPException(status_code=503, detail="Agent not initialized")

    try:
        # Log the request
        log_request_start(request.query)

        # Execute the query
        import time

        start_time = time.time()
        result = await router_agent.route_query(request.query)
        end_time = time.time()

        duration = end_time - start_time

        # Log successful execution
        log_tool_execution(result.tool_name, duration, "success")

        return QueryResponse(
            query=request.query,
            result=result.result,
            tool_used=result.tool_name,
        )

    except Exception as e:
        logger.error(f"Error processing query: {str(e)}")

        # Log failed execution
        if "start_time" in locals():
            duration = time.time() - start_time
            log_tool_execution("unknown", duration, "error")

        return QueryResponse(
            query=request.query, result=f"Error: {str(e)}", tool_used="error"
        )
