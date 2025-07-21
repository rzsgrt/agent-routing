"""Base tool class for all agent tools."""

from abc import ABC, abstractmethod


class BaseTool(ABC):
    """Abstract base class for all tools."""

    def __init__(self, name: str):
        """Initialize the tool with a name."""
        self.name = name

    @abstractmethod
    async def execute(self, query: str) -> str:
        """
        Execute the tool with the given query.

        Args:
            query: The user's natural language query

        Returns:
            The result as a string
        """
        pass
