"""Comprehensive tests for extended Nova standard library built-ins."""

import io
import pytest
from nova.lexer import Lexer
from nova.parser import Parser
from nova.interpreter import Interpreter
from nova.errors import NovaRuntimeError


def run_code(source: str):
    out = io.StringIO()
    lexer = Lexer(source)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    program = parser.parse()
    interpreter = Interpreter(stdout=out)
    interpreter.interpret(program, source_code=source)
    return out.getvalue()


def test_builtin_abs() -> None:
    source = """
    display(abs(-42));
    display(abs(15));
    display(abs(-3.14));
    """
    output = run_code(source)
    lines = output.strip().splitlines()
    assert lines == ["42", "15", "3.14"]


def test_builtin_min_and_max() -> None:
    source = """
    display(min(10, 20));
    display(max(10, 20));
    display(min(-5, -15));
    display(max(-5, -15));
    """
    output = run_code(source)
    lines = output.strip().splitlines()
    assert lines == ["10", "20", "-15", "-5"]


def test_builtin_floor_and_ceil() -> None:
    source = """
    display(floor(4.9));
    display(ceil(4.1));
    display(floor(-3.2));
    display(ceil(-3.8));
    """
    output = run_code(source)
    lines = output.strip().splitlines()
    assert lines == ["4", "5", "-4", "-3"]


def test_builtin_sqrt() -> None:
    source = """
    display(sqrt(25));
    display(sqrt(2));
    """
    output = run_code(source)
    lines = output.strip().splitlines()
    assert lines[0] == "5"
    assert lines[1].startswith("1.414")


def test_builtin_sqrt_negative_error() -> None:
    source = "display(sqrt(-4));"
    with pytest.raises(NovaRuntimeError) as exc_info:
        run_code(source)
    assert "Cannot compute square root of negative number" in str(exc_info.value)


def test_builtin_string_utilities() -> None:
    source = """
    display(trim("  Nova Language   "));
    display(lower("HeLLo WoRLd"));
    display(upper("nova"));
    """
    output = run_code(source)
    lines = output.strip().splitlines()
    assert lines == ["Nova Language", "hello world", "NOVA"]


def test_builtin_split_and_join() -> None:
    source = """
    let parts = split("apple,banana,cherry", ",");
    display(parts);
    let rejoined = join(parts, " - ");
    display(rejoined);
    """
    output = run_code(source)
    lines = output.strip().splitlines()
    assert lines == ["[apple, banana, cherry]", "apple - banana - cherry"]
