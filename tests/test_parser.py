"""Comprehensive tests for the Nova Parser."""

import pytest
from nova.lexer import Lexer
from nova.parser import Parser
from nova.ast_nodes import (
    VarDecl,
    FuncDecl,
    WhenStmt,
    ChooseStmt,
    WhileStmt,
    ReturnStmt,
    ExprStmt,
    Block,
    BinaryExpr,
    UnaryExpr,
    LogicalExpr,
    CallExpr,
    Literal,
    VariableRef,
    Assignment,
    GroupingExpr,
)
from nova.errors import NovaSyntaxError


def parse_source(source: str):
    lexer = Lexer(source)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    return parser.parse()


def test_parse_var_decl() -> None:
    ast = parse_source("let x = 42; let y;")
    assert len(ast.statements) == 2

    s0 = ast.statements[0]
    assert isinstance(s0, VarDecl)
    assert s0.name == "x"
    assert isinstance(s0.initializer, Literal)
    assert s0.initializer.value == 42

    s1 = ast.statements[1]
    assert isinstance(s1, VarDecl)
    assert s1.name == "y"
    assert s1.initializer is None


def test_parse_assignment() -> None:
    ast = parse_source("x = 10 + 5;")
    assert len(ast.statements) == 1
    stmt = ast.statements[0]
    assert isinstance(stmt, ExprStmt)
    assert isinstance(stmt.expression, Assignment)
    assert stmt.expression.name == "x"
    assert isinstance(stmt.expression.value, BinaryExpr)


def test_operator_precedence() -> None:
    # 1 + 2 * 3 should be 1 + (2 * 3)
    ast = parse_source("1 + 2 * 3;")
    stmt = ast.statements[0]
    assert isinstance(stmt, ExprStmt)
    bin_expr = stmt.expression
    assert isinstance(bin_expr, BinaryExpr)
    assert bin_expr.operator == "+"
    assert isinstance(bin_expr.left, Literal) and bin_expr.left.value == 1
    assert isinstance(bin_expr.right, BinaryExpr)
    assert bin_expr.right.operator == "*"


def test_parenthesized_precedence() -> None:
    # (1 + 2) * 3
    ast = parse_source("(1 + 2) * 3;")
    stmt = ast.statements[0]
    bin_expr = stmt.expression
    assert isinstance(bin_expr, BinaryExpr)
    assert bin_expr.operator == "*"
    assert isinstance(bin_expr.left, GroupingExpr)
    assert isinstance(bin_expr.right, Literal) and bin_expr.right.value == 3


def test_logical_precedence() -> None:
    # a or b and c should be a or (b and c)
    ast = parse_source("a or b and c;")
    stmt = ast.statements[0]
    expr = stmt.expression
    assert isinstance(expr, LogicalExpr)
    assert expr.operator == "or"
    assert isinstance(expr.left, VariableRef) and expr.left.name == "a"
    assert isinstance(expr.right, LogicalExpr) and expr.right.operator == "and"


def test_parse_event_function() -> None:
    source = """
    Event calculate(a, b) {
        return a + b;
    }
    """
    ast = parse_source(source)
    assert len(ast.statements) == 1
    func = ast.statements[0]
    assert isinstance(func, FuncDecl)
    assert func.name == "calculate"
    assert func.params == ["a", "b"]
    assert len(func.body.statements) == 1
    assert isinstance(func.body.statements[0], ReturnStmt)


def test_parse_when_statement() -> None:
    source = """
    when (x > 10) {
        display("High");
    } otherwise when (x > 5) {
        display("Medium");
    } otherwise {
        display("Low");
    }
    """
    ast = parse_source(source)
    assert len(ast.statements) == 1
    stmt = ast.statements[0]
    assert isinstance(stmt, WhenStmt)
    assert len(stmt.otherwise_whens) == 1
    assert stmt.otherwise_branch is not None


def test_parse_choose_statement() -> None:
    source = """
    choose (x) {
        option 1 { display("One"); }
        option 2 { display("Two"); }
        fallback { display("Other"); }
    }
    """
    ast = parse_source(source)
    assert len(ast.statements) == 1
    stmt = ast.statements[0]
    assert isinstance(stmt, ChooseStmt)
    assert len(stmt.options) == 2
    assert stmt.fallback is not None


def test_parse_while_loop() -> None:
    source = """
    while (count < 5) {
        count = count + 1;
    }
    """
    ast = parse_source(source)
    assert len(ast.statements) == 1
    stmt = ast.statements[0]
    assert isinstance(stmt, WhileStmt)
    assert isinstance(stmt.condition, BinaryExpr)


def test_syntax_error_missing_semicolon() -> None:
    source = "let a = 10"
    with pytest.raises(NovaSyntaxError) as exc_info:
        parse_source(source)
    assert "Expected ';'" in str(exc_info.value)


def test_syntax_error_unmatched_brace() -> None:
    source = "when (true) { display(1);"
    with pytest.raises(NovaSyntaxError) as exc_info:
        parse_source(source)
    assert "Expected '}'" in str(exc_info.value)


def test_syntax_error_option_after_fallback() -> None:
    source = """
    choose (x) {
        fallback { display(0); }
        option 1 { display(1); }
    }
    """
    with pytest.raises(NovaSyntaxError) as exc_info:
        parse_source(source)
    assert "cannot appear after 'fallback'" in str(exc_info.value)


def test_syntax_error_multiple_fallbacks() -> None:
    source = """
    choose (x) {
        fallback { display(1); }
        fallback { display(2); }
    }
    """
    with pytest.raises(NovaSyntaxError) as exc_info:
        parse_source(source)
    assert "Multiple 'fallback' branches" in str(exc_info.value)


def test_syntax_error_invalid_assignment_target() -> None:
    source = "10 + 5 = 20;"
    with pytest.raises(NovaSyntaxError) as exc_info:
        parse_source(source)
    assert "Invalid assignment target" in str(exc_info.value)
