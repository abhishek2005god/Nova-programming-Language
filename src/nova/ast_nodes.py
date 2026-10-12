"""Abstract Syntax Tree (AST) node definitions for the Nova programming language."""

from dataclasses import dataclass
from typing import Any, Optional


@dataclass
class ASTNode:
    """Base class for all AST nodes."""
    line: int = 0
    column: int = 0


# ============================================================================
# Expressions
# ============================================================================

@dataclass
class Expression(ASTNode):
    """Base class for expression AST nodes."""
    pass


@dataclass
class Literal(Expression):
    """Literal values: integers, floats, strings, booleans, null."""
    value: Any = None
    raw: str = ""


@dataclass
class VariableRef(Expression):
    """Reference to a variable identifier."""
    name: str = ""


@dataclass
class Assignment(Expression):
    """Variable reassignment expression (name = value)."""
    name: str = ""
    value: Expression = None  # type: ignore


@dataclass
class UnaryExpr(Expression):
    """Unary expressions: '-' or 'not'."""
    operator: str = ""
    operand: Expression = None  # type: ignore


@dataclass
class BinaryExpr(Expression):
    """Binary expressions: arithmetic (+, -, *, /, %), comparison (<, <=, >, >=), equality (==, !=)."""
    left: Expression = None  # type: ignore
    operator: str = ""
    right: Expression = None  # type: ignore


@dataclass
class LogicalExpr(Expression):
    """Logical expressions with short-circuiting: 'and', 'or'."""
    left: Expression = None  # type: ignore
    operator: str = ""
    right: Expression = None  # type: ignore


@dataclass
class CallExpr(Expression):
    """Function call expression: callee(arguments)."""
    callee: Expression = None  # type: ignore
    arguments: list[Expression] = None  # type: ignore

    def __post_init__(self) -> None:
        if self.arguments is None:
            self.arguments = []


@dataclass
class GroupingExpr(Expression):
    """Parenthesized grouping expression."""
    expression: Expression = None  # type: ignore


@dataclass
class ListLiteral(Expression):
    """List literal expression: [elem1, elem2, ...]."""
    elements: list[Expression] = None  # type: ignore

    def __post_init__(self) -> None:
        if self.elements is None:
            self.elements = []


@dataclass
class IndexExpr(Expression):
    """Index access expression: target[index]."""
    target: Expression = None  # type: ignore
    index: Expression = None   # type: ignore


@dataclass
class IndexAssignment(Expression):
    """Index assignment expression: target[index] = value."""
    target: Expression = None  # type: ignore
    index: Expression = None   # type: ignore
    value: Expression = None   # type: ignore


# ============================================================================
# Statements
# ============================================================================

@dataclass
class Statement(ASTNode):
    """Base class for statement AST nodes."""
    pass


@dataclass
class Block(Statement):
    """Block of statements enclosed in braces { ... }."""
    statements: list[Statement] = None  # type: ignore

    def __post_init__(self) -> None:
        if self.statements is None:
            self.statements = []


@dataclass
class VarDecl(Statement):
    """Variable declaration: let name = initializer;"""
    name: str = ""
    initializer: Optional[Expression] = None


@dataclass
class FuncDecl(Statement):
    """Function declaration: Event name(params) { body }"""
    name: str = ""
    params: list[str] = None  # type: ignore
    body: Block = None  # type: ignore

    def __post_init__(self) -> None:
        if self.params is None:
            self.params = []


@dataclass
class OtherwiseWhenBranch(ASTNode):
    """Branch for 'otherwise when (cond) { body }'."""
    condition: Expression = None  # type: ignore
    body: Block = None  # type: ignore


@dataclass
class WhenStmt(Statement):
    """Conditional statement: when (cond) { then } otherwise when ... otherwise { ... }"""
    condition: Expression = None  # type: ignore
    then_branch: Block = None  # type: ignore
    otherwise_whens: list[OtherwiseWhenBranch] = None  # type: ignore
    otherwise_branch: Optional[Block] = None

    def __post_init__(self) -> None:
        if self.otherwise_whens is None:
            self.otherwise_whens = []


@dataclass
class OptionBranch(ASTNode):
    """Branch for 'option expr { body }' in choose statement."""
    value_expr: Expression = None  # type: ignore
    body: Block = None  # type: ignore


@dataclass
class FallbackBranch(ASTNode):
    """Fallback branch for 'fallback { body }' in choose statement."""
    body: Block = None  # type: ignore


@dataclass
class ChooseStmt(Statement):
    """Switch-style selection statement: choose (expr) { option ... fallback ... }"""
    expression: Expression = None  # type: ignore
    options: list[OptionBranch] = None  # type: ignore
    fallback: Optional[FallbackBranch] = None

    def __post_init__(self) -> None:
        if self.options is None:
            self.options = []


@dataclass
class WhileStmt(Statement):
    """While loop statement: while (condition) { body }"""
    condition: Expression = None  # type: ignore
    body: Block = None  # type: ignore


@dataclass
class ReturnStmt(Statement):
    """Return statement from a function: return value;"""
    value: Optional[Expression] = None


@dataclass
class ExprStmt(Statement):
    """Statement consisting of a single evaluated expression."""
    expression: Expression = None  # type: ignore


@dataclass
class Program(ASTNode):
    """Root node of a parsed Nova program."""
    statements: list[Statement] = None  # type: ignore

    def __post_init__(self) -> None:
        if self.statements is None:
            self.statements = []


# ============================================================================
# AST Formatter for Debugging and Inspection
# ============================================================================

def format_ast(node: ASTNode, indent: int = 0) -> str:
    """Format an AST node into a clean, human-readable indented tree representation."""
    prefix = "  " * indent
    pos = f" [{node.line}:{node.column}]" if node.line > 0 else ""

    if isinstance(node, Program):
        lines = [f"{prefix}Program{pos}"]
        for stmt in node.statements:
            lines.append(format_ast(stmt, indent + 1))
        return "\n".join(lines)

    elif isinstance(node, VarDecl):
        init_str = f"\n{format_ast(node.initializer, indent + 1)}" if node.initializer else " <no initializer>"
        return f"{prefix}VarDecl(name='{node.name}'){pos}{init_str}"

    elif isinstance(node, FuncDecl):
        lines = [f"{prefix}FuncDecl(name='{node.name}', params={node.params}){pos}"]
        lines.append(format_ast(node.body, indent + 1))
        return "\n".join(lines)

    elif isinstance(node, Block):
        lines = [f"{prefix}Block{pos}"]
        for stmt in node.statements:
            lines.append(format_ast(stmt, indent + 1))
        return "\n".join(lines)

    elif isinstance(node, WhenStmt):
        lines = [f"{prefix}WhenStmt{pos}"]
        lines.append(f"{prefix}  Condition:")
        lines.append(format_ast(node.condition, indent + 2))
        lines.append(f"{prefix}  Then:")
        lines.append(format_ast(node.then_branch, indent + 2))
        for ow in node.otherwise_whens:
            lines.append(f"{prefix}  OtherwiseWhen:")
            lines.append(format_ast(ow.condition, indent + 2))
            lines.append(format_ast(ow.body, indent + 2))
        if node.otherwise_branch:
            lines.append(f"{prefix}  Otherwise:")
            lines.append(format_ast(node.otherwise_branch, indent + 2))
        return "\n".join(lines)

    elif isinstance(node, ChooseStmt):
        lines = [f"{prefix}ChooseStmt{pos}"]
        lines.append(f"{prefix}  Target:")
        lines.append(format_ast(node.expression, indent + 2))
        for opt in node.options:
            lines.append(f"{prefix}  Option:")
            lines.append(format_ast(opt.value_expr, indent + 2))
            lines.append(format_ast(opt.body, indent + 2))
        if node.fallback:
            lines.append(f"{prefix}  Fallback:")
            lines.append(format_ast(node.fallback.body, indent + 2))
        return "\n".join(lines)

    elif isinstance(node, WhileStmt):
        lines = [f"{prefix}WhileStmt{pos}"]
        lines.append(f"{prefix}  Condition:")
        lines.append(format_ast(node.condition, indent + 2))
        lines.append(f"{prefix}  Body:")
        lines.append(format_ast(node.body, indent + 2))
        return "\n".join(lines)

    elif isinstance(node, ReturnStmt):
        if node.value:
            return f"{prefix}ReturnStmt{pos}\n{format_ast(node.value, indent + 1)}"
        return f"{prefix}ReturnStmt(value=null){pos}"

    elif isinstance(node, ExprStmt):
        return f"{prefix}ExprStmt{pos}\n{format_ast(node.expression, indent + 1)}"

    elif isinstance(node, Assignment):
        return f"{prefix}Assignment(name='{node.name}'){pos}\n{format_ast(node.value, indent + 1)}"

    elif isinstance(node, BinaryExpr):
        lines = [f"{prefix}BinaryExpr(op='{node.operator}'){pos}"]
        lines.append(format_ast(node.left, indent + 1))
        lines.append(format_ast(node.right, indent + 1))
        return "\n".join(lines)

    elif isinstance(node, LogicalExpr):
        lines = [f"{prefix}LogicalExpr(op='{node.operator}'){pos}"]
        lines.append(format_ast(node.left, indent + 1))
        lines.append(format_ast(node.right, indent + 1))
        return "\n".join(lines)

    elif isinstance(node, UnaryExpr):
        lines = [f"{prefix}UnaryExpr(op='{node.operator}'){pos}"]
        lines.append(format_ast(node.operand, indent + 1))
        return "\n".join(lines)

    elif isinstance(node, CallExpr):
        lines = [f"{prefix}CallExpr{pos}"]
        lines.append(f"{prefix}  Callee:")
        lines.append(format_ast(node.callee, indent + 2))
        lines.append(f"{prefix}  Arguments:")
        for arg in node.arguments:
            lines.append(format_ast(arg, indent + 2))
        return "\n".join(lines)

    elif isinstance(node, VariableRef):
        return f"{prefix}VariableRef(name='{node.name}'){pos}"

    elif isinstance(node, Literal):
        return f"{prefix}Literal(val={node.value!r}){pos}"

    elif isinstance(node, GroupingExpr):
        return f"{prefix}GroupingExpr{pos}\n{format_ast(node.expression, indent + 1)}"

    elif isinstance(node, ListLiteral):
        lines = [f"{prefix}ListLiteral{pos}"]
        for el in node.elements:
            lines.append(format_ast(el, indent + 1))
        return "\n".join(lines)

    elif isinstance(node, IndexExpr):
        lines = [f"{prefix}IndexExpr{pos}"]
        lines.append(f"{prefix}  Target:")
        lines.append(format_ast(node.target, indent + 2))
        lines.append(f"{prefix}  Index:")
        lines.append(format_ast(node.index, indent + 2))
        return "\n".join(lines)

    elif isinstance(node, IndexAssignment):
        lines = [f"{prefix}IndexAssignment{pos}"]
        lines.append(f"{prefix}  Target:")
        lines.append(format_ast(node.target, indent + 2))
        lines.append(f"{prefix}  Index:")
        lines.append(format_ast(node.index, indent + 2))
        lines.append(f"{prefix}  Value:")
        lines.append(format_ast(node.value, indent + 2))
        return "\n".join(lines)

    return f"{prefix}{type(node).__name__}{pos}"
