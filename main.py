"""Command-Line Interface entry point for the Nova programming language."""

import argparse
import sys
from pathlib import Path

# Ensure src/ is on Python search path
ROOT_DIR = Path(__file__).resolve().parent
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from nova import (
    Lexer,
    Parser,
    Interpreter,
    REPL,
    format_ast,
    NovaError,
    __version__,
)


def run_file(
    file_path_str: str,
    show_tokens: bool = False,
    show_ast: bool = False,
    max_steps: int = 100_000,
    max_call_depth: int = 500,
) -> int:
    """Execute or inspect a Nova source file."""
    path = Path(file_path_str)
    if not path.is_file():
        print(f"Error: File not found: '{file_path_str}'", file=sys.stderr)
        return 1

    try:
        source_code = path.read_text(encoding="utf-8")
    except Exception as e:
        print(f"Error reading file '{file_path_str}': {e}", file=sys.stderr)
        return 1

    # Lexical Analysis
    try:
        lexer = Lexer(source_code, file_name=str(path))
        tokens = lexer.tokenize()
    except NovaError as e:
        print(e.format_error(source_code), file=sys.stderr)
        return 1

    if show_tokens:
        print(f"--- Tokens for {path.name} ---")
        for tok in tokens:
            print(tok)
        return 0

    # Parsing to AST
    try:
        parser = Parser(tokens, file_name=str(path))
        program = parser.parse()
    except NovaError as e:
        print(e.format_error(source_code), file=sys.stderr)
        return 1

    if show_ast:
        print(f"--- Abstract Syntax Tree for {path.name} ---")
        print(format_ast(program))
        return 0

    # Interpretation
    try:
        interpreter = Interpreter(
            max_steps=max_steps,
            max_call_depth=max_call_depth,
            file_name=str(path),
        )
        interpreter.interpret(
            program, source_code=source_code, file_name=str(path)
        )
        return 0
    except NovaError as e:
        print(e.format_error(source_code), file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Unexpected internal error: {e}", file=sys.stderr)
        return 1


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="nova",
        description="Nova Programming Language Interpreter",
    )
    parser.add_argument(
        "file",
        nargs="?",
        help="Path to the .nova source file to execute",
    )
    parser.add_argument(
        "--tokens",
        action="store_true",
        help="Display lexical tokens and exit",
    )
    parser.add_argument(
        "--ast",
        action="store_true",
        help="Display the Abstract Syntax Tree (AST) and exit",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"Nova Language v{__version__}",
    )
    parser.add_argument(
        "--max-steps",
        type=int,
        default=100_000,
        help="Maximum loop/execution step limit before timeout (default: 100,000)",
    )
    parser.add_argument(
        "--max-call-depth",
        type=int,
        default=500,
        help="Maximum function call recursion depth (default: 500)",
    )

    args = parser.parse_args()

    if args.file:
        sys.exit(
            run_file(
                file_path_str=args.file,
                show_tokens=args.tokens,
                show_ast=args.ast,
                max_steps=args.max_steps,
                max_call_depth=args.max_call_depth,
            )
        )
    else:
        # Launch REPL when no file is supplied
        repl = REPL()
        repl.run()
        sys.exit(0)


if __name__ == "__main__":
    main()
