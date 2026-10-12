"""Built-in functions and runtime values for the Nova programming language."""

import sys
from typing import Any, Callable, Optional, TextIO
from nova.errors import NovaRuntimeError


def nova_type_name(val: Any) -> str:
    """Return the Nova type name for a runtime value."""
    if val is None:
        return "null"
    if isinstance(val, bool):
        return "boolean"
    if isinstance(val, int):
        return "integer"
    if isinstance(val, float):
        return "float"
    if isinstance(val, str):
        return "string"
    if isinstance(val, list):
        return "list"
    if hasattr(val, "is_nova_callable"):
        return "function"
    return type(val).__name__


def nova_repr(val: Any) -> str:
    """Return the Nova string representation for a runtime value."""
    if val is None:
        return "null"
    if isinstance(val, bool):
        return "true" if val else "false"
    if isinstance(val, (int, float)):
        return str(val)
    if isinstance(val, str):
        return val
    if isinstance(val, list):
        return "[" + ", ".join(nova_repr(x) for x in val) + "]"
    if hasattr(val, "name"):
        return f"<Event {getattr(val, 'name')}>"
    return str(val)


class NovaBuiltin:
    """Represents a built-in function in the Nova runtime."""

    is_nova_callable: bool = True

    def __init__(
        self,
        name: str,
        func: Callable[..., Any],
        min_arity: int = 1,
        max_arity: int = 1,
    ) -> None:
        self.name: str = name
        self.func: Callable[..., Any] = func
        self.min_arity: int = min_arity
        self.max_arity: int = max_arity

    def call(
        self,
        args: list[Any],
        line: int = 0,
        column: int = 0,
        file: str = "<source>",
    ) -> Any:
        """Invoke the built-in function after validating argument counts."""
        arg_count = len(args)
        if self.min_arity == self.max_arity:
            if arg_count != self.min_arity:
                raise NovaRuntimeError(
                    f"Function '{self.name}' expects {self.min_arity} argument(s), got {arg_count}",
                    line,
                    column,
                    file,
                )
        else:
            if arg_count < self.min_arity or arg_count > self.max_arity:
                raise NovaRuntimeError(
                    f"Function '{self.name}' expects between {self.min_arity} and {self.max_arity} arguments, got {arg_count}",
                    line,
                    column,
                    file,
                )
        return self.func(args, line, column, file)

    def __repr__(self) -> str:
        return f"<builtin {self.name}>"


def create_builtins(
    stdout: Optional[TextIO] = None,
    stdin: Optional[TextIO] = None,
) -> dict[str, NovaBuiltin]:
    """Create and return a dictionary of standard built-in functions."""
    out_stream = stdout if stdout is not None else sys.stdout
    in_stream = stdin if stdin is not None else sys.stdin

    def _builtin_display(
        args: list[Any], line: int, col: int, file: str
    ) -> None:
        val = args[0]
        out_stream.write(nova_repr(val) + "\n")
        out_stream.flush()
        return None  # Nova null

    def _builtin_len(
        args: list[Any], line: int, col: int, file: str
    ) -> int:
        val = args[0]
        if not isinstance(val, (str, list)):
            raise NovaRuntimeError(
                f"Argument to 'len' must be a string or list, got '{nova_type_name(val)}'",
                line,
                col,
                file,
            )
        return len(val)

    def _builtin_push(
        args: list[Any], line: int, col: int, file: str
    ) -> Any:
        target_list = args[0]
        if not isinstance(target_list, list):
            raise NovaRuntimeError(
                f"First argument to 'push' must be a list, got '{nova_type_name(target_list)}'",
                line,
                col,
                file,
            )
        target_list.append(args[1])
        return args[1]

    def _builtin_pop(
        args: list[Any], line: int, col: int, file: str
    ) -> Any:
        target_list = args[0]
        if not isinstance(target_list, list):
            raise NovaRuntimeError(
                f"Argument to 'pop' must be a list, got '{nova_type_name(target_list)}'",
                line,
                col,
                file,
            )
        if len(target_list) == 0:
            raise NovaRuntimeError(
                "Cannot pop from an empty list",
                line,
                col,
                file,
            )
        return target_list.pop()

    def _builtin_input(
        args: list[Any], line: int, col: int, file: str
    ) -> str:
        prompt = ""
        if len(args) == 1:
            if not isinstance(args[0], str):
                raise NovaRuntimeError(
                    f"Prompt argument to 'input' must be a string, got '{nova_type_name(args[0])}'",
                    line,
                    col,
                    file,
                )
            prompt = args[0]

        if prompt:
            out_stream.write(prompt)
            out_stream.flush()

        line_str = in_stream.readline()
        if not line_str and not line_str.endswith("\n"):
            return ""
        return line_str.rstrip("\r\n")

    def _builtin_abs(
        args: list[Any], line: int, col: int, file: str
    ) -> Any:
        x = args[0]
        if isinstance(x, bool) or not isinstance(x, (int, float)):
            raise NovaRuntimeError(
                f"Argument to 'abs' must be a number, got '{nova_type_name(x)}'",
                line,
                col,
                file,
            )
        return abs(x)

    def _builtin_min(
        args: list[Any], line: int, col: int, file: str
    ) -> Any:
        a, b = args[0], args[1]
        if (
            isinstance(a, bool)
            or isinstance(b, bool)
            or not isinstance(a, (int, float))
            or not isinstance(b, (int, float))
        ):
            raise NovaRuntimeError(
                f"Arguments to 'min' must be numbers, got '{nova_type_name(a)}' and '{nova_type_name(b)}'",
                line,
                col,
                file,
            )
        return a if a <= b else b

    def _builtin_max(
        args: list[Any], line: int, col: int, file: str
    ) -> Any:
        a, b = args[0], args[1]
        if (
            isinstance(a, bool)
            or isinstance(b, bool)
            or not isinstance(a, (int, float))
            or not isinstance(b, (int, float))
        ):
            raise NovaRuntimeError(
                f"Arguments to 'max' must be numbers, got '{nova_type_name(a)}' and '{nova_type_name(b)}'",
                line,
                col,
                file,
            )
        return a if a >= b else b

    def _builtin_floor(
        args: list[Any], line: int, col: int, file: str
    ) -> int:
        import math
        x = args[0]
        if isinstance(x, bool) or not isinstance(x, (int, float)):
            raise NovaRuntimeError(
                f"Argument to 'floor' must be a number, got '{nova_type_name(x)}'",
                line,
                col,
                file,
            )
        return math.floor(x)

    def _builtin_ceil(
        args: list[Any], line: int, col: int, file: str
    ) -> int:
        import math
        x = args[0]
        if isinstance(x, bool) or not isinstance(x, (int, float)):
            raise NovaRuntimeError(
                f"Argument to 'ceil' must be a number, got '{nova_type_name(x)}'",
                line,
                col,
                file,
            )
        return math.ceil(x)

    def _builtin_sqrt(
        args: list[Any], line: int, col: int, file: str
    ) -> Any:
        import math
        x = args[0]
        if isinstance(x, bool) or not isinstance(x, (int, float)):
            raise NovaRuntimeError(
                f"Argument to 'sqrt' must be a number, got '{nova_type_name(x)}'",
                line,
                col,
                file,
            )
        if x < 0:
            raise NovaRuntimeError(
                "Cannot compute square root of negative number",
                line,
                col,
                file,
            )
        res = math.sqrt(x)
        return int(res) if res.is_integer() else res

    def _builtin_trim(
        args: list[Any], line: int, col: int, file: str
    ) -> str:
        s = args[0]
        if not isinstance(s, str):
            raise NovaRuntimeError(
                f"Argument to 'trim' must be a string, got '{nova_type_name(s)}'",
                line,
                col,
                file,
            )
        return s.strip()

    def _builtin_lower(
        args: list[Any], line: int, col: int, file: str
    ) -> str:
        s = args[0]
        if not isinstance(s, str):
            raise NovaRuntimeError(
                f"Argument to 'lower' must be a string, got '{nova_type_name(s)}'",
                line,
                col,
                file,
            )
        return s.lower()

    def _builtin_upper(
        args: list[Any], line: int, col: int, file: str
    ) -> str:
        s = args[0]
        if not isinstance(s, str):
            raise NovaRuntimeError(
                f"Argument to 'upper' must be a string, got '{nova_type_name(s)}'",
                line,
                col,
                file,
            )
        return s.upper()

    def _builtin_split(
        args: list[Any], line: int, col: int, file: str
    ) -> list[str]:
        s = args[0]
        sep = args[1]
        if not isinstance(s, str) or not isinstance(sep, str):
            raise NovaRuntimeError(
                f"Arguments to 'split' must be strings, got '{nova_type_name(s)}' and '{nova_type_name(sep)}'",
                line,
                col,
                file,
            )
        return s.split(sep)

    def _builtin_join(
        args: list[Any], line: int, col: int, file: str
    ) -> str:
        lst = args[0]
        sep = args[1]
        if not isinstance(lst, list) or not isinstance(sep, str):
            raise NovaRuntimeError(
                f"Arguments to 'join' must be list and string, got '{nova_type_name(lst)}' and '{nova_type_name(sep)}'",
                line,
                col,
                file,
            )
        for item in lst:
            if not isinstance(item, str):
                raise NovaRuntimeError(
                    f"All items in list passed to 'join' must be strings, found '{nova_type_name(item)}'",
                    line,
                    col,
                    file,
                )
        return sep.join(lst)

    def _builtin_str(
        args: list[Any], line: int, col: int, file: str
    ) -> str:
        return nova_repr(args[0])

    return {
        "display": NovaBuiltin("display", _builtin_display, min_arity=1, max_arity=1),
        "len": NovaBuiltin("len", _builtin_len, min_arity=1, max_arity=1),
        "push": NovaBuiltin("push", _builtin_push, min_arity=2, max_arity=2),
        "pop": NovaBuiltin("pop", _builtin_pop, min_arity=1, max_arity=1),
        "input": NovaBuiltin("input", _builtin_input, min_arity=0, max_arity=1),
        "str": NovaBuiltin("str", _builtin_str, min_arity=1, max_arity=1),
        "abs": NovaBuiltin("abs", _builtin_abs, min_arity=1, max_arity=1),
        "min": NovaBuiltin("min", _builtin_min, min_arity=2, max_arity=2),
        "max": NovaBuiltin("max", _builtin_max, min_arity=2, max_arity=2),
        "floor": NovaBuiltin("floor", _builtin_floor, min_arity=1, max_arity=1),
        "ceil": NovaBuiltin("ceil", _builtin_ceil, min_arity=1, max_arity=1),
        "sqrt": NovaBuiltin("sqrt", _builtin_sqrt, min_arity=1, max_arity=1),
        "trim": NovaBuiltin("trim", _builtin_trim, min_arity=1, max_arity=1),
        "lower": NovaBuiltin("lower", _builtin_lower, min_arity=1, max_arity=1),
        "upper": NovaBuiltin("upper", _builtin_upper, min_arity=1, max_arity=1),
        "split": NovaBuiltin("split", _builtin_split, min_arity=2, max_arity=2),
        "join": NovaBuiltin("join", _builtin_join, min_arity=2, max_arity=2),
    }
