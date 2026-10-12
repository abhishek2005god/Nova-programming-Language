"""Environment and lexical scoping implementation for the Nova programming language."""

from typing import Any, Optional
from nova.errors import NovaRuntimeError


class Environment:
    """Manages variable storage, lexical scoping, shadowing, and parent lookups."""

    def __init__(self, parent: Optional["Environment"] = None) -> None:
        self.values: dict[str, Any] = {}
        self.parent: Optional["Environment"] = parent

    def define(
        self,
        name: str,
        value: Any,
        line: int = 0,
        column: int = 0,
        file: str = "<source>",
    ) -> None:
        """Declare and bind a new variable in the current scope.

        Raises NovaRuntimeError if the variable is already declared in the current scope.
        """
        if name in self.values:
            raise NovaRuntimeError(
                f"Variable '{name}' is already declared in this scope",
                line,
                column,
                file,
            )
        self.values[name] = value

    def get(
        self,
        name: str,
        line: int = 0,
        column: int = 0,
        file: str = "<source>",
    ) -> Any:
        """Retrieve a variable value by looking up the current and parent scopes."""
        if name in self.values:
            return self.values[name]
        if self.parent is not None:
            return self.parent.get(name, line, column, file)

        raise NovaRuntimeError(
            f"Undefined variable '{name}'", line, column, file
        )

    def assign(
        self,
        name: str,
        value: Any,
        line: int = 0,
        column: int = 0,
        file: str = "<source>",
    ) -> None:
        """Reassign an existing variable in the scope where it was defined."""
        if name in self.values:
            self.values[name] = value
            return
        if self.parent is not None:
            self.parent.assign(name, value, line, column, file)
            return

        raise NovaRuntimeError(
            f"Undefined variable '{name}'", line, column, file
        )

    def is_defined_current(self, name: str) -> bool:
        """Check if a variable is declared in the immediate local scope."""
        return name in self.values

    def is_defined(self, name: str) -> bool:
        """Check if a variable is defined in this scope or any ancestor scope."""
        if name in self.values:
            return True
        if self.parent is not None:
            return self.parent.is_defined(name)
        return False
