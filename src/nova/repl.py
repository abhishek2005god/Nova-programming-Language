"""Interactive Read-Eval-Print Loop (REPL) for the Nova programming language."""

import os
import sys
from pathlib import Path
from nova.lexer import Lexer
from nova.parser import Parser
from nova.interpreter import Interpreter
from nova.errors import NovaError


VERSION = "0.1.0"

HELP_TEXT = """
Nova Language Interactive REPL
==============================
Custom Keywords:
  let                Declare variables (e.g., let count = 0;)
  Event              Declare functions (e.g., Event add(a, b) { return a + b; })
  display(expr)      Built-in print function (e.g., display("Hello");)
  when / otherwise   Conditional branches (when (...) { ... } otherwise { ... })
  otherwise when     Alternative condition branch
  choose / option    Selection statement (choose (x) { option 1 { ... } fallback { ... } })
  fallback           Default selection branch in choose
  while              Loop statement (while (count < 5) { ... })
  return             Return value from Event function
  true / false       Boolean literals
  null               Null literal

REPL Commands:
  :help              Show this help message
  :quit              Exit the REPL session
  :clear             Clear the terminal screen
  :load <path>       Execute a .nova source file in the current session
"""


class REPL:
    """Manages the interactive Nova REPL session."""

    def __init__(self, interpreter: Interpreter | None = None) -> None:
        self.interpreter: Interpreter = (
            interpreter if interpreter is not None else Interpreter()
        )

    def run(self) -> None:
        """Start the REPL loop."""
        print(f"Nova Language v{VERSION}")
        print("Type :help for commands and :quit to exit.\n")

        while True:
            try:
                line = input("nova> ")
            except (EOFError, KeyboardInterrupt):
                print("\nExiting Nova REPL.")
                break

            stripped = line.strip()
            if not stripped:
                continue

            # Command handling
            if stripped == ":quit":
                break
            elif stripped == ":help":
                print(HELP_TEXT)
                continue
            elif stripped == ":clear":
                os.system("cls" if os.name == "nt" else "clear")
                continue
            elif stripped.startswith(":load"):
                parts = stripped.split(maxsplit=1)
                if len(parts) < 2:
                    print("Usage: :load <filepath>")
                    continue
                file_path = parts[1].strip()
                self._load_file(file_path)
                continue

            # Multi-line statement accumulator
            buffer = [line]
            open_braces = line.count("{") - line.count("}")
            open_parens = line.count("(") - line.count(")")

            while open_braces > 0 or open_parens > 0:
                try:
                    cont_line = input("...   ")
                except (EOFError, KeyboardInterrupt):
                    print("\n[Input cancelled]")
                    buffer.clear()
                    break

                buffer.append(cont_line)
                open_braces += cont_line.count("{") - cont_line.count("}")
                open_parens += cont_line.count("(") - cont_line.count(")")

            if not buffer:
                continue

            code = "\n".join(buffer)
            self._execute_source(code, source_name="<repl>")

    def _execute_source(self, code: str, source_name: str = "<repl>") -> None:
        try:
            lexer = Lexer(code, file_name=source_name)
            tokens = lexer.tokenize()
            parser = Parser(tokens, file_name=source_name)
            program = parser.parse()
            self.interpreter.interpret(
                program, source_code=code, file_name=source_name
            )
        except NovaError as e:
            print(e.format_error(source_code=code), file=sys.stderr)
        except Exception as e:
            print(f"Unexpected internal error: {e}", file=sys.stderr)

    def _load_file(self, file_path_str: str) -> None:
        path = Path(file_path_str)
        if not path.is_file():
            print(f"Error: File '{file_path_str}' does not exist.", file=sys.stderr)
            return

        try:
            source = path.read_text(encoding="utf-8")
            self._execute_source(source, source_name=str(path))
        except Exception as e:
            print(f"Error reading file '{file_path_str}': {e}", file=sys.stderr)
