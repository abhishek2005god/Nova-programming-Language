"""Comprehensive tests for the Nova Interpreter and Evaluator."""

import io
import pytest
from nova.lexer import Lexer
from nova.parser import Parser
from nova.interpreter import Interpreter
from nova.errors import NovaRuntimeError


def run_code(source: str, stdout=None, stdin=None, max_steps=100_000, max_call_depth=500):
    out = stdout if stdout is not None else io.StringIO()
    inp = stdin if stdin is not None else io.StringIO()
    lexer = Lexer(source)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    program = parser.parse()
    interpreter = Interpreter(
        stdout=out,
        stdin=inp,
        max_steps=max_steps,
        max_call_depth=max_call_depth,
    )
    result = interpreter.interpret(program, source_code=source)
    return out.getvalue(), result


def test_arithmetic_evaluation() -> None:
    source = """
    display(10 + 5);
    display(20 - 7);
    display(6 * 7);
    display(12 / 4);
    display(7 / 2);
    display(10 % 3);
    display(-42);
    """
    output, _ = run_code(source)
    lines = output.strip().splitlines()
    assert lines == ["15", "13", "42", "3", "3.5", "1", "-42"]


def test_string_concatenation() -> None:
    source = 'display("Hello, " + "Nova!");'
    output, _ = run_code(source)
    assert output.strip() == "Hello, Nova!"


def test_comparisons_and_equality() -> None:
    source = """
    display(10 > 5);
    display(5 >= 5);
    display(3 < 2);
    display(4 <= 4);
    display(10 == 10);
    display(10 != 5);
    display(true == true);
    display(true == 1);     // Distinct types in Nova
    display(null == null);
    display(null == 0);
    """
    output, _ = run_code(source)
    lines = output.strip().splitlines()
    assert lines == [
        "true",
        "true",
        "false",
        "true",
        "true",
        "true",
        "true",
        "false",
        "true",
        "false",
    ]


def test_logical_operators_and_short_circuit() -> None:
    source = """
    display(true and false);
    display(true or false);
    display(not false);

    // Short-circuit: if right is not evaluated, error is not triggered
    let x = false;
    display(x and (10 / 0 == 0));
    let y = true;
    display(y or (10 / 0 == 0));
    """
    output, _ = run_code(source)
    lines = output.strip().splitlines()
    assert lines == ["false", "true", "true", "false", "true"]


def test_when_conditional_branches() -> None:
    source = """
    let val = 25;
    when (val > 50) {
        display("High");
    } otherwise when (val > 20) {
        display("Medium");
    } otherwise {
        display("Low");
    }
    """
    output, _ = run_code(source)
    assert output.strip() == "Medium"


def test_choose_statement_matching_and_fallback() -> None:
    source = """
    let x = 2;
    choose (x) {
        option 1 { display("One"); }
        option 2 { display("Two"); }
        fallback { display("Other"); }
    }

    let y = 99;
    choose (y) {
        option 1 { display("One"); }
        option 2 { display("Two"); }
        fallback { display("Fallback matched"); }
    }
    """
    output, _ = run_code(source)
    lines = output.strip().splitlines()
    assert lines == ["Two", "Fallback matched"]


def test_choose_no_fallthrough() -> None:
    source = """
    let count = 0;
    choose (1) {
        option 1 { count = count + 1; }
        option 2 { count = count + 10; }
        fallback { count = count + 100; }
    }
    display(count);
    """
    output, _ = run_code(source)
    assert output.strip() == "1"


def test_choose_reject_duplicate_options() -> None:
    source = """
    choose (1) {
        option 1 { display("First"); }
        option 1 { display("Second"); }
    }
    """
    with pytest.raises(NovaRuntimeError) as exc_info:
        run_code(source)
    assert "Duplicate option value" in str(exc_info.value)


def test_while_loop_execution() -> None:
    source = """
    let sum = 0;
    let i = 1;
    while (i <= 4) {
        sum = sum + i;
        i = i + 1;
    }
    display(sum);
    """
    output, _ = run_code(source)
    assert output.strip() == "10"


def test_infinite_loop_step_protection() -> None:
    source = """
    while (true) {
        // Infinite loop
    }
    """
    with pytest.raises(NovaRuntimeError) as exc_info:
        run_code(source, max_steps=100)
    assert "Maximum execution steps exceeded" in str(exc_info.value)


def test_division_by_zero_error() -> None:
    source = "let x = 10 / 0;"
    with pytest.raises(NovaRuntimeError) as exc_info:
        run_code(source)
    assert "Division by zero" in str(exc_info.value)


def test_modulo_by_zero_error() -> None:
    source = "let x = 10 % 0;"
    with pytest.raises(NovaRuntimeError) as exc_info:
        run_code(source)
    assert "Modulo by zero" in str(exc_info.value)


def test_non_boolean_condition_error() -> None:
    source = 'when (100) { display("hello"); }'
    with pytest.raises(NovaRuntimeError) as exc_info:
        run_code(source)
    assert "Condition for 'when' must evaluate to a boolean" in str(exc_info.value)


def test_builtin_len() -> None:
    source = 'display(len("Nova Language"));'
    output, _ = run_code(source)
    assert output.strip() == "13"


def test_builtin_len_type_error() -> None:
    source = "len(123);"
    with pytest.raises(NovaRuntimeError) as exc_info:
        run_code(source)
    assert "Argument to 'len' must be a string" in str(exc_info.value)


def test_builtin_input() -> None:
    source = """
    let name = input("Enter name: ");
    display("Welcome, " + name);
    """
    fake_stdin = io.StringIO("Alice\n")
    output, _ = run_code(source, stdin=fake_stdin)
    assert "Enter name: " in output
    assert "Welcome, Alice" in output
