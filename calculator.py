"""Safe mathematical expression evaluator.

Allowed:
 - numeric literals (ints, floats)
 - binary ops: + - * / // % **
 - unary ops: + -
 - parentheses (handled by AST structure)

Disallowed:
 - names, attribute access, function calls, subscriptions, comprehensions, etc.
"""
from __future__ import annotations
import ast
from typing import Union

_ALLOWED_BINOP = {
    ast.Add,
    ast.Sub,
    ast.Mult,
    ast.Div,
    ast.Mod,
    ast.Pow,
    ast.FloorDiv,
}
_ALLOWED_UNARYOP = {ast.UAdd, ast.USub}
_ALLOWED_NODES = {
    ast.Expression,
    ast.BinOp,
    ast.UnaryOp,
    ast.Constant,  # Python 3.8+ numeric constants
    ast.Num,       # older Python versions
    ast.Load,
}

def _ensure_allowed(node: ast.AST) -> None:
    """Walk AST subtree and raise ValueError if any node is not allowed."""
    for n in ast.walk(node):
        t = type(n)
        if t in (ast.BinOp,):
            if type(n.op) not in _ALLOWED_BINOP:
                raise ValueError(f"Disallowed binary operator: {type(n.op).__name__}")
        elif t in (ast.UnaryOp,):
            if type(n.op) not in _ALLOWED_UNARYOP:
                raise ValueError(f"Disallowed unary operator: {type(n.op).__name__}")
        elif t in (ast.Constant, ast.Num, ast.Expression, ast.Load):
            continue
        else:
            # Any other node types are disallowed (Name, Call, Attribute, Subscript, etc.)
            raise ValueError(f"Disallowed expression element: {t.__name__}")

def _eval_node(node: ast.AST) -> Union[int, float]:
    """Recursively evaluate a validated AST node."""
    if isinstance(node, ast.Expression):
        return _eval_node(node.body)
    if isinstance(node, ast.Constant):
        if isinstance(node.value, (int, float)):
            return node.value
        raise ValueError("Only numeric constants are allowed")
    # For compatibility with older Python AST
    if isinstance(node, ast.Num):
        return node.n
    if isinstance(node, ast.BinOp):
        left = _eval_node(node.left)
        right = _eval_node(node.right)
        op = node.op
        if isinstance(op, ast.Add):
            return left + right
        if isinstance(op, ast.Sub):
            return left - right
        if isinstance(op, ast.Mult):
            return left * right
        if isinstance(op, ast.Div):
            return left / right
        if isinstance(op, ast.FloorDiv):
            return left // right
        if isinstance(op, ast.Mod):
            return left % right
        if isinstance(op, ast.Pow):
            return left ** right
        # unreachable due to validation
        raise ValueError(f"Unsupported binary operator: {type(op).__name__}")
    if isinstance(node, ast.UnaryOp):
        operand = _eval_node(node.operand)
        if isinstance(node.op, ast.UAdd):
            return +operand
        if isinstance(node.op, ast.USub):
            return -operand
        raise ValueError(f"Unsupported unary operator: {type(node.op).__name__}")
    raise ValueError(f"Unsupported AST node: {type(node).__name__}")

def eval_expr(expr: str) -> Union[int, float]:
    """Safely evaluate a math expression string and return a numeric result.

    Raises ValueError for invalid/unsafe expressions.
    """
    if not isinstance(expr, str) or not expr.strip():
        raise ValueError("Expression must be a non-empty string")
    try:
        node = ast.parse(expr, mode="eval")
    except SyntaxError as e:
        raise ValueError(f"Syntax error in expression: {e}") from e

    _ensure_allowed(node)
    # compile then eval in restricted globals/locals for safety
    compiled = compile(node, "<safe_eval>", "eval")
    try:
        # Evaluate in empty builtins and empty globals to avoid access to names
        return eval(compiled, {"__builtins__": {}}, {})
    except ZeroDivisionError as e:
        raise ValueError("Division by zero") from e
    except Exception as e:
        # Convert any runtime exception to ValueError for consistent API
        raise ValueError(f"Error evaluating expression: {e}") from e
