"""Token definitions and TokenType enumeration for the Nova programming language."""

from enum import Enum, auto
from dataclasses import dataclass
from typing import Any, Optional


class TokenType(Enum):
    # Single-character tokens
    LEFT_PAREN = auto()       # (
    RIGHT_PAREN = auto()      # )
    LEFT_BRACKET = auto()     # [
    RIGHT_BRACKET = auto()    # ]
    LEFT_BRACE = auto()       # {
    RIGHT_BRACE = auto()      # }
    COMMA = auto()            # ,
    SEMICOLON = auto()        # ;

    # Arithmetic operators
    PLUS = auto()             # +
    MINUS = auto()            # -
    STAR = auto()             # *
    SLASH = auto()            # /
    PERCENT = auto()          # %

    # Assignment & Comparison operators
    EQUAL = auto()            # =
    EQUAL_EQUAL = auto()      # ==
    BANG_EQUAL = auto()       # !=
    LESS = auto()             # <
    LESS_EQUAL = auto()       # <=
    GREATER = auto()          # >
    GREATER_EQUAL = auto()    # >=

    # Literals
    IDENTIFIER = auto()
    STRING = auto()
    INTEGER = auto()
    FLOAT = auto()

    # Reserved Keywords
    LET = auto()              # let
    EVENT = auto()            # Event
    WHEN = auto()             # when
    OTHERWISE = auto()        # otherwise
    CHOOSE = auto()           # choose
    OPTION = auto()           # option
    FALLBACK = auto()         # fallback
    WHILE = auto()            # while
    RETURN = auto()           # return
    TRUE = auto()             # true
    FALSE = auto()            # false
    NULL = auto()             # null
    AND = auto()              # and
    OR = auto()               # or
    NOT = auto()              # not

    # End of File
    EOF = auto()


# Reserved keywords in Nova
KEYWORDS: dict[str, TokenType] = {
    "let": TokenType.LET,
    "Event": TokenType.EVENT,
    "when": TokenType.WHEN,
    "otherwise": TokenType.OTHERWISE,
    "choose": TokenType.CHOOSE,
    "option": TokenType.OPTION,
    "fallback": TokenType.FALLBACK,
    "while": TokenType.WHILE,
    "return": TokenType.RETURN,
    "true": TokenType.TRUE,
    "false": TokenType.FALSE,
    "null": TokenType.NULL,
    "and": TokenType.AND,
    "or": TokenType.OR,
    "not": TokenType.NOT,
}


@dataclass
class Token:
    """Represents a lexical token in Nova source code."""
    type: TokenType
    lexeme: str
    literal: Any
    line: int
    column: int

    def __repr__(self) -> str:
        if self.literal is not None:
            return f"Token({self.type.name}, {self.lexeme!r}, {self.literal!r}, {self.line}:{self.column})"
        return f"Token({self.type.name}, {self.lexeme!r}, {self.line}:{self.column})"
