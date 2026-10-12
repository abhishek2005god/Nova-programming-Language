"""Comprehensive tests for Nova Error formatting and error categories."""

import pytest
from nova.errors import (
    NovaLexerError,
    NovaSyntaxError,
    NovaRuntimeError,
)
from nova.lexer import Lexer
from nova.parser import Parser
from nova.interpreter import Interpreter


def test_lexer_error_formatting() -> None:
    source = 'let x = "unterminated;'
    lexer = Lexer(source, file_name="test.nova")
    with pytest.raises(NovaLexerError) as exc_info:
        lexer.tokenize()
    formatted = exc_info.value.format_error(source)
    assert "Lexer Error:" in formatted
    assert "--> test.nova:1:9" in formatted
    assert 'let x = "unterminated;' in formatted
    assert "^" in formatted


def test_syntax_error_formatting() -> None:
    source = "let x = ;"
    lexer = Lexer(source, file_name="syntax.nova")
    tokens = lexer.tokenize()
    parser = Parser(tokens, file_name="syntax.nova")
    with pytest.raises(NovaSyntaxError) as exc_info:
        parser.parse()
    formatted = exc_info.value.format_error(source)
    assert "Syntax Error:" in formatted
    assert "--> syntax.nova:1:9" in formatted


def test_runtime_error_formatting() -> None:
    source = "display(undefined_var);"
    lexer = Lexer(source, file_name="runtime.nova")
    tokens = lexer.tokenize()
    parser = Parser(tokens, file_name="runtime.nova")
    program = parser.parse()
    interpreter = Interpreter(file_name="runtime.nova")
    with pytest.raises(NovaRuntimeError) as exc_info:
        interpreter.interpret(program, source_code=source, file_name="runtime.nova")
    formatted = exc_info.value.format_error(source)
    assert "Runtime Error:" in formatted
    assert "Undefined variable 'undefined_var'" in formatted
    assert "--> runtime.nova:1:9" in formatted
