"""Comprehensive tests for Nova Functions (Event), Scoping, and Closures."""

import io
import pytest
from nova.lexer import Lexer
from nova.parser import Parser
from nova.interpreter import Interpreter
from nova.errors import NovaRuntimeError


def run_code(source: str, max_call_depth=500):
    out = io.StringIO()
    lexer = Lexer(source)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    program = parser.parse()
    interpreter = Interpreter(stdout=out, max_call_depth=max_call_depth)
    interpreter.interpret(program, source_code=source)
    return out.getvalue()


def test_basic_function() -> None:
    source = """
    Event add(a, b) {
        return a + b;
    }
    display(add(15, 27));
    """
    output = run_code(source)
    assert output.strip() == "42"


def test_function_implicit_return_null() -> None:
    source = """
    Event do_something() {
        let x = 10;
    }
    display(do_something());
    """
    output = run_code(source)
    assert output.strip() == "null"


def test_return_from_nested_control_flow() -> None:
    source = """
    Event find_first_even(limit) {
        let n = 1;
        while (n <= limit) {
            when (n % 2 == 0) {
                return n;
            }
            n = n + 1;
        }
        return -1;
    }
    display(find_first_even(10));
    """
    output = run_code(source)
    assert output.strip() == "2"


def test_incorrect_argument_count() -> None:
    source = """
    Event greet(name) {
        return "Hi " + name;
    }
    greet();
    """
    with pytest.raises(NovaRuntimeError) as exc_info:
        run_code(source)
    assert "expects 1 argument(s), got 0" in str(exc_info.value)


def test_closure_lexical_scoping() -> None:
    source = """
    Event make_multiplier(factor) {
        Event multiplier(x) {
            return x * factor;
        }
        return multiplier;
    }

    let double = make_multiplier(2);
    let triple = make_multiplier(3);

    display(double(5));
    display(triple(5));
    """
    output = run_code(source)
    lines = output.strip().splitlines()
    assert lines == ["10", "15"]


def test_recursion_factorial() -> None:
    source = """
    Event fact(n) {
        when (n <= 1) {
            return 1;
        }
        return n * fact(n - 1);
    }
    display(fact(6));
    """
    output = run_code(source)
    assert output.strip() == "720"


def test_recursion_fibonacci() -> None:
    source = """
    Event fib(n) {
        when (n <= 0) {
            return 0;
        } otherwise when (n == 1) {
            return 1;
        }
        return fib(n - 1) + fib(n - 2);
    }
    display(fib(6));
    """
    output = run_code(source)
    assert output.strip() == "8"


def test_infinite_recursion_call_depth_protection() -> None:
    source = """
    Event infinite_loop(n) {
        return infinite_loop(n + 1);
    }
    infinite_loop(1);
    """
    with pytest.raises(NovaRuntimeError) as exc_info:
        run_code(source, max_call_depth=20)
    assert "Maximum call depth exceeded" in str(exc_info.value)


def test_calling_non_callable_error() -> None:
    source = """
    let not_a_func = 123;
    not_a_func();
    """
    with pytest.raises(NovaRuntimeError) as exc_info:
        run_code(source)
    assert "is not callable" in str(exc_info.value)


def test_return_outside_function_error() -> None:
    source = "return 10;"
    with pytest.raises(NovaRuntimeError) as exc_info:
        run_code(source)
    assert "Cannot return outside of an Event function" in str(exc_info.value)
