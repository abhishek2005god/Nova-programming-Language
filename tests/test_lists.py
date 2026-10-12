"""Comprehensive tests for Nova List/Array data structure and indexing."""

import io
import pytest
from nova.lexer import Lexer
from nova.parser import Parser
from nova.interpreter import Interpreter
from nova.errors import NovaRuntimeError


def run_code(source: str):
    out = io.StringIO()
    lexer = Lexer(source)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    program = parser.parse()
    interpreter = Interpreter(stdout=out)
    interpreter.interpret(program, source_code=source)
    return out.getvalue()


def test_list_creation_and_display() -> None:
    source = """
    let empty = [];
    display(empty);
    let items = [1, "two", true, null];
    display(items);
    """
    output = run_code(source)
    lines = output.strip().splitlines()
    assert lines == ["[]", "[1, two, true, null]"]


def test_list_indexing() -> None:
    source = """
    let arr = [10, 20, 30];
    display(arr[0]);
    display(arr[1]);
    display(arr[2]);
    """
    output = run_code(source)
    lines = output.strip().splitlines()
    assert lines == ["10", "20", "30"]


def test_nested_list_indexing() -> None:
    source = """
    let matrix = [[1, 2], [3, 4]];
    display(matrix[0][1]);
    display(matrix[1][0]);
    """
    output = run_code(source)
    lines = output.strip().splitlines()
    assert lines == ["2", "3"]


def test_string_indexing() -> None:
    source = """
    let s = "Nova";
    display(s[0]);
    display(s[3]);
    """
    output = run_code(source)
    lines = output.strip().splitlines()
    assert lines == ["N", "a"]


def test_index_assignment() -> None:
    source = """
    let arr = [1, 2, 3];
    arr[1] = 99;
    display(arr);
    """
    output = run_code(source)
    assert output.strip() == "[1, 99, 3]"


def test_list_concatenation() -> None:
    source = """
    let a = [1, 2];
    let b = [3, 4];
    display(a + b);
    """
    output = run_code(source)
    assert output.strip() == "[1, 2, 3, 4]"


def test_list_equality() -> None:
    source = """
    display([1, 2] == [1, 2]);
    display([1, 2] == [1, 3]);
    display([1, 2] != [1, 2]);
    """
    output = run_code(source)
    lines = output.strip().splitlines()
    assert lines == ["true", "false", "false"]


def test_builtin_len_on_list() -> None:
    source = """
    let arr = [10, 20, 30, 40];
    display(len(arr));
    """
    output = run_code(source)
    assert output.strip() == "4"


def test_builtin_push_and_pop() -> None:
    source = """
    let arr = [1];
    push(arr, 2);
    push(arr, 3);
    display(arr);
    let last = pop(arr);
    display(last);
    display(arr);
    """
    output = run_code(source)
    lines = output.strip().splitlines()
    assert lines == [
        "[1, 2, 3]",
        "3",
        "[1, 2]",
    ]


def test_index_out_of_bounds_error() -> None:
    source = """
    let arr = [1, 2];
    display(arr[5]);
    """
    with pytest.raises(NovaRuntimeError) as exc_info:
        run_code(source)
    assert "out of bounds" in str(exc_info.value)


def test_non_integer_index_error() -> None:
    source = """
    let arr = [1, 2];
    display(arr["0"]);
    """
    with pytest.raises(NovaRuntimeError) as exc_info:
        run_code(source)
    assert "Index must be an integer" in str(exc_info.value)


def test_index_into_non_indexable_error() -> None:
    source = """
    let n = 123;
    display(n[0]);
    """
    with pytest.raises(NovaRuntimeError) as exc_info:
        run_code(source)
    assert "Cannot index into 'integer'" in str(exc_info.value)


def test_pop_from_empty_list_error() -> None:
    source = """
    let empty = [];
    pop(empty);
    """
    with pytest.raises(NovaRuntimeError) as exc_info:
        run_code(source)
    assert "Cannot pop from an empty list" in str(exc_info.value)
