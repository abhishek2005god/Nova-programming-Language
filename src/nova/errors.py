"""Error definitions and formatting for the Nova programming language."""

from typing import Any, Optional


class NovaError(Exception):
    """Base class for all Nova language errors."""

    def __init__(
        self,
        message: str,
        line: int = 0,
        column: int = 0,
        file: str = "<source>",
    ) -> None:
        super().__init__(message)
        self.message = message
        self.line = line
        self.column = column
        self.file = file

    def format_error(self, source_code: Optional[str] = None) -> str:
        """Format the error message with source context and caret pointers."""
        name = self.__class__.__name__
        if name.startswith("Nova"):
            name = name[4:]
        # Insert a space before Error if not present, e.g., RuntimeError
        if name.endswith("Error"):
            category = name[:-5] + " Error"
        else:
            category = name

        loc = f"  --> {self.file}:{self.line}:{self.column}" if self.line > 0 else f"  --> {self.file}"
        lines = [f"{category}: {self.message}", loc]

        if source_code and self.line > 0:
            src_lines = source_code.splitlines()
            if 0 < self.line <= len(src_lines):
                line_content = src_lines[self.line - 1]
                gutter = f"{self.line:>4} | "
                lines.append(f"{gutter}{line_content}")
                if self.column > 0:
                    indent = " " * (len(gutter) + self.column - 1)
                    lines.append(f"{indent}^")

        return "\n".join(lines)

    def __str__(self) -> str:
        return self.format_error()


class NovaLexerError(NovaError):
    """Errors encountered during lexical analysis."""
    pass


class NovaSyntaxError(NovaError):
    """Errors encountered during syntax parsing."""
    pass


class NovaRuntimeError(NovaError):
    """Errors encountered during program evaluation/execution."""
    pass


class NovaReturnSignal(BaseException):
    """Internal control signal used by the evaluator to unwind the call stack on function return.

    Inherits from BaseException so standard 'except Exception' handlers do not catch it.
    """

    def __init__(self, value: Any, line: int = 0, column: int = 0) -> None:
        super().__init__()
        self.value = value
        self.line = line
        self.column = column
