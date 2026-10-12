"""Comprehensive tests for the Nova lexical analyzer (Lexer)."""

import pytest
from nova.tokens import TokenType
from nova.lexer import Lexer
from nova.errors import NovaLexerError


def test_keywords() -> None:
    source = "let Event when otherwise choose option fallback while return true false null and or not"
    lexer = Lexer(source)
    tokens = lexer.tokenize()

    expected = [
        TokenType.LET,
        TokenType.EVENT,
        TokenType.WHEN,
        TokenType.OTHERWISE,
        TokenType.CHOOSE,
        TokenType.OPTION,
        TokenType.FALLBACK,
        TokenType.WHILE,
        TokenType.RETURN,
        TokenType.TRUE,
        TokenType.FALSE,
        TokenType.NULL,
        TokenType.AND,
        TokenType.OR,
        TokenType.NOT,
        TokenType.EOF,
    ]
    assert [t.type for t in tokens] == expected


def test_identifiers_vs_keywords() -> None:
    source = "Events when_ready letter optional fallback_val whileLoop returns not_true"
    lexer = Lexer(source)
    tokens = lexer.tokenize()

    for tok in tokens[:-1]:
        assert tok.type == TokenType.IDENTIFIER


def test_literals() -> None:
    source = '123 0 45.67 0.05 "Hello, World!" "" true false null'
    lexer = Lexer(source)
    tokens = lexer.tokenize()

    assert tokens[0].type == TokenType.INTEGER and tokens[0].literal == 123
    assert tokens[1].type == TokenType.INTEGER and tokens[1].literal == 0
    assert tokens[2].type == TokenType.FLOAT and tokens[2].literal == 45.67
    assert tokens[3].type == TokenType.FLOAT and tokens[3].literal == 0.05
    assert tokens[4].type == TokenType.STRING and tokens[4].literal == "Hello, World!"
    assert tokens[5].type == TokenType.STRING and tokens[5].literal == ""
    assert tokens[6].type == TokenType.TRUE and tokens[6].literal is True
    assert tokens[7].type == TokenType.FALSE and tokens[7].literal is False
    assert tokens[8].type == TokenType.NULL and tokens[8].literal is None


def test_string_escapes() -> None:
    source = r'"Line 1\nLine 2\tTabbed \"Quoted\" \\Backslash\r"'
    lexer = Lexer(source)
    tokens = lexer.tokenize()

    assert tokens[0].type == TokenType.STRING
    assert tokens[0].literal == 'Line 1\nLine 2\tTabbed "Quoted" \\Backslash\r'


def test_operators_and_punctuation() -> None:
    source = "+ - * / % = == != < <= > >= ( ) { } , ;"
    lexer = Lexer(source)
    tokens = lexer.tokenize()

    expected = [
        TokenType.PLUS,
        TokenType.MINUS,
        TokenType.STAR,
        TokenType.SLASH,
        TokenType.PERCENT,
        TokenType.EQUAL,
        TokenType.EQUAL_EQUAL,
        TokenType.BANG_EQUAL,
        TokenType.LESS,
        TokenType.LESS_EQUAL,
        TokenType.GREATER,
        TokenType.GREATER_EQUAL,
        TokenType.LEFT_PAREN,
        TokenType.RIGHT_PAREN,
        TokenType.LEFT_BRACE,
        TokenType.RIGHT_BRACE,
        TokenType.COMMA,
        TokenType.SEMICOLON,
        TokenType.EOF,
    ]
    assert [t.type for t in tokens] == expected


def test_comments_and_whitespace() -> None:
    source = """
    // This is a comment
    let x = 10; // Inline comment
    // Another comment
    display(x);
    """
    lexer = Lexer(source)
    tokens = lexer.tokenize()

    expected = [
        TokenType.LET,
        TokenType.IDENTIFIER,
        TokenType.EQUAL,
        TokenType.INTEGER,
        TokenType.SEMICOLON,
        TokenType.IDENTIFIER,
        TokenType.LEFT_PAREN,
        TokenType.IDENTIFIER,
        TokenType.RIGHT_PAREN,
        TokenType.SEMICOLON,
        TokenType.EOF,
    ]
    assert [t.type for t in tokens] == expected


def test_line_and_column_tracking() -> None:
    source = "let a = 1;\nlet b = 2;"
    lexer = Lexer(source)
    tokens = lexer.tokenize()

    assert tokens[0].line == 1 and tokens[0].column == 1   # let
    assert tokens[1].line == 1 and tokens[1].column == 5   # a
    assert tokens[5].line == 2 and tokens[5].column == 1   # let (line 2)
    assert tokens[6].line == 2 and tokens[6].column == 5   # b


def test_unterminated_string_error() -> None:
    source = 'let s = "unterminated;'
    lexer = Lexer(source)
    with pytest.raises(NovaLexerError) as exc_info:
        lexer.tokenize()
    assert "Unterminated string literal" in str(exc_info.value)


def test_multiline_string_error() -> None:
    source = 'let s = "line1\nline2";'
    lexer = Lexer(source)
    with pytest.raises(NovaLexerError) as exc_info:
        lexer.tokenize()
    assert "Unterminated string literal" in str(exc_info.value)


def test_invalid_escape_sequence_error() -> None:
    source = r'"invalid \x escape"'
    lexer = Lexer(source)
    with pytest.raises(NovaLexerError) as exc_info:
        lexer.tokenize()
    assert "Invalid escape sequence" in str(exc_info.value)


def test_malformed_number_trailing_dot() -> None:
    source = "let x = 12.;"
    lexer = Lexer(source)
    with pytest.raises(NovaLexerError) as exc_info:
        lexer.tokenize()
    assert "Malformed numeric literal" in str(exc_info.value)


def test_malformed_number_letter_suffix() -> None:
    source = "let x = 123abc;"
    lexer = Lexer(source)
    with pytest.raises(NovaLexerError) as exc_info:
        lexer.tokenize()
    assert "Malformed numeric literal" in str(exc_info.value)


def test_unexpected_character_error() -> None:
    source = "let $money = 100;"
    lexer = Lexer(source)
    with pytest.raises(NovaLexerError) as exc_info:
        lexer.tokenize()
    assert "Unexpected character '$'" in str(exc_info.value)


def test_standalone_bang_error() -> None:
    source = "when (!valid) {}"
    lexer = Lexer(source)
    with pytest.raises(NovaLexerError) as exc_info:
        lexer.tokenize()
    assert "Unexpected character '!'" in str(exc_info.value)
