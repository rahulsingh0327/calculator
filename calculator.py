from mcp.server.fastmcp import FastMCP
import ast

mcp = FastMCP("UtilityTools")


# -------------------------------------------------------------------
# Safe Calculator Logic (with semantic-search-ready docstrings)
# -------------------------------------------------------------------

def _ensure_allowed(node: ast.AST):
    """
    Validate that an AST expression contains ONLY safe mathematical operations.

    This function inspects each AST node and verifies that:
    - Only basic arithmetic operators are used (+, -, *, /, %, **, //)
    - Only unary + and unary - operations are allowed
    - No variables, function calls, attribute access, loops, or names exist

    This ensures the calculator cannot execute unsafe Python code.
    """
    for n in ast.walk(node):
        if isinstance(n, ast.BinOp):
            if type(n.op) not in {ast.Add, ast.Sub, ast.Mult, ast.Div, ast.Mod, ast.Pow, ast.FloorDiv}:
                raise ValueError("Operator not allowed in safe calculator.")
        elif isinstance(n, ast.UnaryOp):
            if type(n.op) not in {ast.UAdd, ast.USub}:
                raise ValueError("Unary operator not allowed in safe calculator.")
        elif isinstance(n, (ast.Expression, ast.Constant, ast.Num, ast.Load)):
            continue
        else:
            raise ValueError(f"Unsupported expression component: {type(n).__name__}")


def safe_eval(expr: str) -> float:
    """
    Safely evaluate a mathematical expression using a restricted AST parser.

    The expression must contain:
    - Only numbers
    - Only basic math operators
    - No variable names, no function calls, no attribute access

    Returns:
        float: The computed numerical result.
    Raises:
        ValueError: If the expression is malformed or unsafe.
    """
    node = ast.parse(expr, mode="eval")
    _ensure_allowed(node)
    compiled = compile(node, "<safe_eval>", "eval")
    return eval(compiled, {"__builtins__": {}}, {})


# -------------------------------------------------------------------
# MCP Tool
# -------------------------------------------------------------------

@mcp.tool()
def calculator(expression: str) -> float:
    """
    Evaluate a mathematical expression using a secure, sandboxed evaluator.

    This tool allows:
        - Arithmetic operations: +, -, *, /, %, **, //
        - Unary operations: +x, -x
        - Integer and floating-point numbers
    This tool is useful for:
        - Quick calculations
        - Embedded evaluation within larger workflows
        - Any system requiring safe computational capabilities

    Args:
        expression (str): A mathematical formula as text.

    Returns:
        float: The computed result.
    """
    return safe_eval(expression)
