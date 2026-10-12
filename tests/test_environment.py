"""Comprehensive tests for the Nova Environment and Scoping."""

import pytest
from nova.environment import Environment
from nova.errors import NovaRuntimeError


def test_define_and_get() -> None:
    env = Environment()
    env.define("x", 42)
    assert env.get("x") == 42


def test_undefined_get_raises_error() -> None:
    env = Environment()
    with pytest.raises(NovaRuntimeError) as exc_info:
        env.get("unknown")
    assert "Undefined variable 'unknown'" in str(exc_info.value)


def test_reassignment() -> None:
    env = Environment()
    env.define("x", 10)
    env.assign("x", 20)
    assert env.get("x") == 20


def test_undefined_assign_raises_error() -> None:
    env = Environment()
    with pytest.raises(NovaRuntimeError) as exc_info:
        env.assign("not_declared", 100)
    assert "Undefined variable 'not_declared'" in str(exc_info.value)


def test_disallow_redeclaration_in_same_scope() -> None:
    env = Environment()
    env.define("x", 1)
    with pytest.raises(NovaRuntimeError) as exc_info:
        env.define("x", 2)
    assert "already declared in this scope" in str(exc_info.value)


def test_nested_environment_lookup() -> None:
    parent = Environment()
    parent.define("global_var", "hello")

    child = Environment(parent=parent)
    child.define("local_var", "world")

    assert child.get("local_var") == "world"
    assert child.get("global_var") == "hello"


def test_shadowing_and_isolation() -> None:
    parent = Environment()
    parent.define("x", 10)

    child = Environment(parent=parent)
    child.define("x", 20)  # Shadows parent x

    assert child.get("x") == 20
    assert parent.get("x") == 10  # Outer remains unaffected


def test_assign_to_parent_variable() -> None:
    parent = Environment()
    parent.define("x", 10)

    child = Environment(parent=parent)
    child.assign("x", 50)  # Reassigns parent x

    assert child.get("x") == 50
    assert parent.get("x") == 50


def test_sibling_scope_isolation() -> None:
    root = Environment()
    child1 = Environment(parent=root)
    child2 = Environment(parent=root)

    child1.define("secret", 123)
    assert not child2.is_defined("secret")
    with pytest.raises(NovaRuntimeError):
        child2.get("secret")
