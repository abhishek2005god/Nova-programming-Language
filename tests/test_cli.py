"""Comprehensive tests for Nova CLI and REPL."""

import io
import sys
from pathlib import Path
import pytest
from main import run_file
from nova.repl import REPL
from nova.interpreter import Interpreter


def test_cli_run_valid_file(tmp_path: Path, capsys) -> None:
    test_file = tmp_path / "test.nova"
    test_file.write_text('display("CLI Success!");', encoding="utf-8")

    code = run_file(str(test_file))
    assert code == 0

    captured = capsys.readouterr()
    assert "CLI Success!" in captured.out


def test_cli_run_missing_file(capsys) -> None:
    code = run_file("non_existent_file.nova")
    assert code == 1

    captured = capsys.readouterr()
    assert "File not found" in captured.err


def test_cli_tokens_flag(tmp_path: Path, capsys) -> None:
    test_file = tmp_path / "tokens_test.nova"
    test_file.write_text("let a = 10;", encoding="utf-8")

    code = run_file(str(test_file), show_tokens=True)
    assert code == 0

    captured = capsys.readouterr()
    assert "--- Tokens for tokens_test.nova ---" in captured.out
    assert "Token(LET" in captured.out


def test_cli_ast_flag(tmp_path: Path, capsys) -> None:
    test_file = tmp_path / "ast_test.nova"
    test_file.write_text("let a = 10;", encoding="utf-8")

    code = run_file(str(test_file), show_ast=True)
    assert code == 0

    captured = capsys.readouterr()
    assert "--- Abstract Syntax Tree for ast_test.nova ---" in captured.out
    assert "VarDecl(name='a')" in captured.out


def test_cli_syntax_error(tmp_path: Path, capsys) -> None:
    test_file = tmp_path / "syntax_err.nova"
    test_file.write_text("let a = ;", encoding="utf-8")

    code = run_file(str(test_file))
    assert code == 1

    captured = capsys.readouterr()
    assert "Syntax Error:" in captured.err


def test_cli_runtime_error(tmp_path: Path, capsys) -> None:
    test_file = tmp_path / "runtime_err.nova"
    test_file.write_text("display(10 / 0);", encoding="utf-8")

    code = run_file(str(test_file))
    assert code == 1

    captured = capsys.readouterr()
    assert "Runtime Error:" in captured.err
    assert "Division by zero" in captured.err


def test_repl_state_persistence_and_error_recovery() -> None:
    out = io.StringIO()
    interpreter = Interpreter(stdout=out)
    repl = REPL(interpreter=interpreter)

    # First command: declare x
    repl._execute_source("let x = 10;")
    assert interpreter.global_environment.get("x") == 10

    # Second command: trigger a runtime error
    repl._execute_source("display(10 / 0);")

    # Third command: use x (should still be preserved!)
    repl._execute_source("display(x + 5);")
    assert "15" in out.getvalue()


def test_repl_load_file(tmp_path: Path) -> None:
    script = tmp_path / "script.nova"
    script.write_text("let loaded_val = 99;\ndisplay(loaded_val);", encoding="utf-8")

    out = io.StringIO()
    interpreter = Interpreter(stdout=out)
    repl = REPL(interpreter=interpreter)

    repl._load_file(str(script))
    assert "99" in out.getvalue()
    assert interpreter.global_environment.get("loaded_val") == 99
