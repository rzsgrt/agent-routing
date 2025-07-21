"""Main agent for routing and handling user queries."""

import httpx
from app.tools.math_tool import MathTool
from app.tools.weather_tool import WeatherTool
from app.tools.general_tool import GeneralTool
from app.models import ToolResult
from app.logging_config import logger
from app import config


class MainAgent:
    """Main agent that routes queries to appropriate tools."""

    def __init__(self):
        """Initialize the main agent with available tools."""
        self.math_tool = MathTool()
        self.weather_tool = WeatherTool()
        self.general_tool = GeneralTool()

        # LLM client for routing
        self.llm_client = httpx.AsyncClient(timeout=config.AGENT_TIMEOUT)

        # Tool mapping
        self.tools = {
            "math": self.math_tool,
            "weather": self.weather_tool,
            "general": self.general_tool,
        }

    async def route_query(self, query: str) -> ToolResult:
        """
        Route a user query to the appropriate tool.

        Args:
            query: The user's query

        Returns:
            ToolResult with the response
        """
        try:
            # Route the query to determine which tool to use
            tool_name = await self._route_with_llm(query)

            # Execute the query with the selected tool
            return await self.execute_query(query, tool_name)

        except Exception as e:
            logger.error(f"Error in route_query: {e}")
            return ToolResult(
                tool_name="error",
                result=f"An error occurred while processing your query: {str(e)}",
                success=False,
            )

    async def _route_with_llm(self, query: str) -> str:
        """
        Use LLM to determine routing.

        Args:
            query: The user query to analyze

        Returns:
            The name of the appropriate tool
        """
        routing_prompt = f"""
You are a query router. Analyze the following query and determine which \
tool should handle it.

Available tools:
- math: For mathematical calculations, equations, arithmetic operations
- weather: For weather information, forecasts, temperature, conditions
- general: For general questions, conversations, explanations, and \
anything else

Query: "{query}"

Respond with ONLY the tool name (math, weather, or general). \
No explanation needed.
"""

        try:
            # Call LLM directly for routing
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {config.LM_STUDIO_API_KEY}",
            }

            payload = {
                "model": config.LM_STUDIO_MODEL,
                "messages": [{"role": "user", "content": routing_prompt}],
                "temperature": 0.0,
                "max_tokens": 10,
                "stream": False,
            }

            response = await self.llm_client.post(
                f"{config.LM_STUDIO_BASE_URL}/chat/completions",
                headers=headers,
                json=payload,
            )

            if response.status_code == 200:
                data = response.json()
                if (
                    data.get("choices")
                    and len(data["choices"]) > 0
                    and data["choices"][0].get("message")
                ):
                    content = data["choices"][0]["message"]["content"]
                    tool_name = content.strip().lower()

                    # Validate tool name
                    if tool_name in self.tools:
                        logger.info(f"Query routed to tool: {tool_name}")
                        return tool_name

            # Fallback to general if routing fails
            logger.warning("LLM routing failed, defaulting to general tool")
            return "general"

        except Exception as e:
            logger.error(f"Error in LLM routing: {e}")
            return "general"

    async def execute_query(self, query: str, tool_name: str) -> ToolResult:
        """
        Execute a query using the specified tool.

        Args:
            query: The user's query
            tool_name: Name of the tool to use

        Returns:
            ToolResult with the response
        """
        try:
            # Get the appropriate tool
            tool = self.tools.get(tool_name)
            if not tool:
                raise ValueError(f"Unknown tool: {tool_name}")

            # Execute the tool
            result = await tool.execute(query)

            logger.info(f"Tool {tool_name} executed successfully")

            return ToolResult(tool_name=tool_name, result=result, success=True)

        except Exception as e:
            logger.error(f"Error executing {tool_name}: {e}")
            return ToolResult(
                tool_name=tool_name,
                result=f"Error: {str(e)}",
                success=False,
            )
