"""Lexical analyzer (tokenizer) for the Nova programming language."""

from typing import Any, Optional
from nova.tokens import Token, TokenType, KEYWORDS
from nova.errors import NovaLexerError


class Lexer:
    """Converts Nova source code into a stream of lexical tokens."""

    def __init__(self, source: str, file_name: str = "<source>") -> None:
        self.source: str = source
        self.file_name: str = file_name
        self.tokens: list[Token] = []

        self.start: int = 0
        self.current: int = 0
        self.line: int = 1
        self.column: int = 1
        self.token_start_column: int = 1

    def tokenize(self) -> list[Token]:
        """Scan and return all tokens from the source string."""
        self.tokens.clear()
        self.start = 0
        self.current = 0
        self.line = 1
        self.column = 1

        while not self._is_at_end():
            self.start = self.current
            self.token_start_column = self.column
            self._scan_token()

        self.tokens.append(
            Token(
                type=TokenType.EOF,
                lexeme="",
                literal=None,
                line=self.line,
                column=self.column,
            )
        )
        return self.tokens

    def _is_at_end(self) -> bool:
        return self.current >= len(self.source)

    def _advance(self) -> str:
        char = self.source[self.current]
        self.current += 1
        self.column += 1
        return char

    def _peek(self) -> str:
        if self._is_at_end():
            return "\0"
        return self.source[self.current]

    def _peek_next(self) -> str:
        if self.current + 1 >= len(self.source):
            return "\0"
        return self.source[self.current + 1]

    def _match(self, expected: str) -> bool:
        if self._is_at_end():
            return False
        if self.source[self.current] != expected:
            return False
        self.current += 1
        self.column += 1
        return True

    def _add_token(self, token_type: TokenType, literal: Any = None) -> None:
        lexeme = self.source[self.start : self.current]
        self.tokens.append(
            Token(
                type=token_type,
                lexeme=lexeme,
                literal=literal,
                line=self.line,
                column=self.token_start_column,
            )
        )

    def _scan_token(self) -> None:
        char = self._advance()

        # Whitespace
        if char == " " or char == "\r" or char == "\t":
            return
        elif char == "\n":
            self.line += 1
            self.column = 1
            return

        # Comments or Slash
        elif char == "/":
            if self._match("/"):
                # Single-line comment: comment continues until newline or EOF
                while self._peek() != "\n" and not self._is_at_end():
                    self._advance()
                return
            else:
                self._add_token(TokenType.SLASH)
                return

        # Single-character tokens
        elif char == "(":
            self._add_token(TokenType.LEFT_PAREN)
        elif char == ")":
            self._add_token(TokenType.RIGHT_PAREN)
        elif char == "[":
            self._add_token(TokenType.LEFT_BRACKET)
        elif char == "]":
            self._add_token(TokenType.RIGHT_BRACKET)
        elif char == "{":
            self._add_token(TokenType.LEFT_BRACE)
        elif char == "}":
            self._add_token(TokenType.RIGHT_BRACE)
        elif char == ",":
            self._add_token(TokenType.COMMA)
        elif char == ";":
            self._add_token(TokenType.SEMICOLON)
        elif char == "+":
            self._add_token(TokenType.PLUS)
        elif char == "-":
            self._add_token(TokenType.MINUS)
        elif char == "*":
            self._add_token(TokenType.STAR)
        elif char == "%":
            self._add_token(TokenType.PERCENT)

        # One or two character tokens
        elif char == "=":
            if self._match("="):
                self._add_token(TokenType.EQUAL_EQUAL)
            else:
                self._add_token(TokenType.EQUAL)
        elif char == "!":
            if self._match("="):
                self._add_token(TokenType.BANG_EQUAL)
            else:
                raise NovaLexerError(
                    "Unexpected character '!' (use 'not' for logical negation or '!=' for inequality)",
                    self.line,
                    self.token_start_column,
                    self.file_name,
                )
        elif char == "<":
            if self._match("="):
                self._add_token(TokenType.LESS_EQUAL)
            else:
                self._add_token(TokenType.LESS)
        elif char == ">":
            if self._match("="):
                self._add_token(TokenType.GREATER_EQUAL)
            else:
                self._add_token(TokenType.GREATER)

        # String literals
        elif char == '"':
            self._string()

        # Numbers
        elif char.isdigit():
            self._number()

        # Identifiers and keywords
        elif char.isalpha() or char == "_":
            self._identifier()

        else:
            raise NovaLexerError(
                f"Unexpected character '{char}'",
                self.line,
                self.token_start_column,
                self.file_name,
            )

    def _string(self) -> None:
        result_chars: list[str] = []
        while not self._is_at_end() and self._peek() != '"':
            if self._peek() == "\n":
                raise NovaLexerError(
                    "Unterminated string literal (multiline strings not permitted)",
                    self.line,
                    self.token_start_column,
                    self.file_name,
                )
            if self._peek() == "\\":
                self._advance()  # consume backslash
                if self._is_at_end():
                    raise NovaLexerError(
                        "Unterminated string literal at escape sequence",
                        self.line,
                        self.token_start_column,
                        self.file_name,
                    )
                esc = self._advance()
                if esc == '"':
                    result_chars.append('"')
                elif esc == "\\":
                    result_chars.append("\\")
                elif esc == "n":
                    result_chars.append("\n")
                elif esc == "t":
                    result_chars.append("\t")
                elif esc == "r":
                    result_chars.append("\r")
                else:
                    raise NovaLexerError(
                        f"Invalid escape sequence '\\{esc}' in string literal",
                        self.line,
                        self.column - 2,
                        self.file_name,
                    )
            else:
                result_chars.append(self._advance())

        if self._is_at_end():
            raise NovaLexerError(
                "Unterminated string literal",
                self.line,
                self.token_start_column,
                self.file_name,
            )

        # Consume closing quote
        self._advance()

        value = "".join(result_chars)
        self._add_token(TokenType.STRING, value)

    def _number(self) -> None:
        while self._peek().isdigit():
            self._advance()

        is_float = False
        # Look for a fractional part
        if self._peek() == ".":
            if self._peek_next().isdigit():
                is_float = True
                self._advance()  # Consume '.'
                while self._peek().isdigit():
                    self._advance()
            else:
                # Malformed number like 12. without digits
                self._advance()  # Consume '.'
                raise NovaLexerError(
                    "Malformed numeric literal: expected digits after decimal point",
                    self.line,
                    self.token_start_column,
                    self.file_name,
                )

        # Check if an identifier immediately follows a number (e.g. 123abc or 12.3.4)
        if self._peek().isalpha() or self._peek() == "_" or self._peek() == ".":
            # Consume offending chars for clear error
            err_col = self.column
            while self._peek().isalnum() or self._peek() in ("_", "."):
                self._advance()
            raise NovaLexerError(
                f"Malformed numeric literal: invalid suffix on number",
                self.line,
                self.token_start_column,
                self.file_name,
            )

        lexeme = self.source[self.start : self.current]
        if is_float:
            self._add_token(TokenType.FLOAT, float(lexeme))
        else:
            self._add_token(TokenType.INTEGER, int(lexeme))

    def _identifier(self) -> None:
        while self._peek().isalnum() or self._peek() == "_":
            self._advance()

        lexeme = self.source[self.start : self.current]
        token_type = KEYWORDS.get(lexeme, TokenType.IDENTIFIER)

        literal = None
        if token_type == TokenType.TRUE:
            literal = True
        elif token_type == TokenType.FALSE:
            literal = False
        elif token_type == TokenType.NULL:
            literal = None

        self._add_token(token_type, literal)
