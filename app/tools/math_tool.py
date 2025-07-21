"""Math tool for evaluating mathematical expressions."""

import ast
import operator
import httpx
from app.tools.base import BaseTool
from app import config


class MathTool(BaseTool):
    """Tool for performing mathematical calculations."""

    def __init__(self):
        """Initialize the math tool."""
        super().__init__("math")

        # Safe operators for mathematical expressions
        self.operators = {
            ast.Add: operator.add,
            ast.Sub: operator.sub,
            ast.Mult: operator.mul,
            ast.Div: operator.truediv,
            ast.Pow: operator.pow,
            ast.BitXor: operator.xor,
            ast.USub: operator.neg,
        }

        # LLM client for expression construction
        self.llm_client = httpx.AsyncClient(timeout=config.AGENT_TIMEOUT)

    async def execute(self, query: str) -> str:
        """
        Execute mathematical calculation from the query.

        Args:
            query: The user's query containing mathematical expression

        Returns:
            The calculation result as a string
        """
        try:
            # Use LLM to construct mathematical expression from the query
            expression = await self._construct_expression_with_llm(query)

            if not expression:
                return (
                    "I couldn't identify a mathematical expression in your "
                    "query. Please provide a clear math problem."
                )

            # Evaluate the expression safely
            result = self._safe_eval(expression)

            if result is None:
                return (
                    f"I couldn't evaluate the expression: {expression}. "
                    "Please check if it's a valid mathematical expression."
                )

            # Format the result nicely
            if isinstance(result, float) and result.is_integer():
                result = int(result)

            return f"{expression} = {result}"

        except Exception as e:
            return f"Error calculating: {str(e)}"

    async def _construct_expression_with_llm(self, query: str) -> str:
        """Use LLM to construct a mathematical expression from natural language."""
        prompt = f"""
You are a math expression constructor. Convert the following natural \
language query into a valid Python mathematical expression.

Rules:
1. Use standard Python operators: +, -, *, /, **, (), etc.
2. Only output the mathematical expression, nothing else
3. Do not include any text, explanations, or formatting
4. If no math is found, return empty string
5. Use ** for exponentiation (not ^)
6. Ensure proper operator precedence with parentheses if needed

Examples:
- "what is 5 plus 3" → "5+3"
- "calculate 42 times 7" → "42*7"  
- "what is 2 to the power of 8" → "2**8"
- "divide 100 by 4" → "100/4"
- "what is (10 plus 5) times 3 minus 8" → "(10+5)*3-8"

Query: "{query}"

Mathematical expression:"""

        try:
            # Call LLM directly
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {config.LM_STUDIO_API_KEY}",
            }

            payload = {
                "model": config.LM_STUDIO_MODEL,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.0,
                "max_tokens": 100,
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
                    expression = content.strip()

                    # Clean up the expression - remove quotes or extra text
                    expression = expression.strip("\"'` \n\t")

                    # Validate it looks like a math expression
                    if self._is_valid_math_expression(expression):
                        return expression

            return ""

        except Exception as e:
            print(f"Error in LLM math construction: {e}")
            return ""

    def _is_valid_math_expression(self, expression: str) -> bool:
        """Check if the expression looks like valid math."""
        if not expression:
            return False

        # Should contain only math characters
        allowed_chars = set("0123456789+-*/().** ")
        if not all(c in allowed_chars for c in expression):
            return False

        # Should contain at least one number and one operator
        has_number = any(c.isdigit() for c in expression)
        has_operator = any(
            op in expression for op in ["+", "-", "*", "/", "**"]
        )

        return has_number and has_operator

    def _safe_eval(self, expression: str):
        """Safely evaluate mathematical expression using AST."""
        try:
            # Parse the expression into an AST
            node = ast.parse(expression, mode="eval")
            return self._eval_node(node.body)
        except (ValueError, SyntaxError, TypeError):
            return None

    def _eval_node(self, node):
        """Recursively evaluate AST nodes."""
        if isinstance(node, ast.Constant):  # For Python 3.8+
            return node.value
        elif isinstance(node, ast.Num):  # For older Python versions
            return node.n
        elif isinstance(node, ast.BinOp):
            left = self._eval_node(node.left)
            right = self._eval_node(node.right)
            op = self.operators.get(type(node.op))
            if op:
                return op(left, right)
        elif isinstance(node, ast.UnaryOp):
            operand = self._eval_node(node.operand)
            op = self.operators.get(type(node.op))
            if op:
                return op(operand)

        raise ValueError(f"Unsupported operation: {type(node)}")
