"""General tool for handling conversations and queries using LM Studio."""

import httpx
from app.tools.base import BaseTool
from app import config


class GeneralTool(BaseTool):
    """Tool for handling general questions and conversations."""

    def __init__(self):
        """Initialize the general tool."""
        super().__init__("general")
        self.client = httpx.AsyncClient(timeout=config.AGENT_TIMEOUT)

    async def execute(self, query: str) -> str:
        """
        Execute general query using LM Studio.

        Args:
            query: The user's general query

        Returns:
            The response from the LLM
        """
        try:
            # Call LM Studio with the user query
            response = await self._call_lm_studio(query)

            if response:
                return response
            else:
                return (
                    "I'm sorry, I couldn't process your request at the "
                    "moment. The LM Studio service might be unavailable."
                )

        except Exception as e:
            return f"Error processing request: {str(e)}"

    async def _call_lm_studio(self, query: str) -> str:
        """
        Call LM Studio API with the user query.

        Args:
            query: The user's query

        Returns:
            The response from LM Studio or None if failed
        """
        try:
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {config.LM_STUDIO_API_KEY}",
            }

            payload = {
                "model": config.LM_STUDIO_MODEL,
                "messages": [
                    {
                        "role": "system",
                        "content": (
                            "You are a helpful AI assistant. Provide clear, "
                            "accurate, and helpful responses to user "
                            "questions. Be concise but informative."
                        ),
                    },
                    {
                        "role": "user",
                        "content": query,
                    },
                ],
                "temperature": 0.1,
                "max_tokens": 500,
                "stream": False,
            }

            response = await self.client.post(
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
                    return content.strip()

            return None

        except Exception as e:
            print(f"Error calling LM Studio: {e}")
            return None
