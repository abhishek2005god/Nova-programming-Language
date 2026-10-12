"""Tree-walking evaluator and runtime for the Nova programming language."""

import sys
from typing import Any, Optional, TextIO
from nova.tokens import TokenType
from nova.ast_nodes import (
    Program,
    Statement,
    Expression,
    VarDecl,
    FuncDecl,
    WhenStmt,
    ChooseStmt,
    WhileStmt,
    ReturnStmt,
    Block,
    ExprStmt,
    Literal,
    VariableRef,
    Assignment,
    UnaryExpr,
    BinaryExpr,
    LogicalExpr,
    CallExpr,
    GroupingExpr,
    ListLiteral,
    IndexExpr,
    IndexAssignment,
)
from nova.environment import Environment
from nova.builtins import create_builtins, nova_repr, nova_type_name, NovaBuiltin
from nova.errors import NovaRuntimeError, NovaReturnSignal


class NovaFunction:
    """Represents a user-defined Nova function (declared using Event)."""

    is_nova_callable: bool = True

    def __init__(self, declaration: FuncDecl, closure: Environment) -> None:
        self.declaration: FuncDecl = declaration
        self.closure: Environment = closure
        self.name: str = declaration.name
        self.arity: int = len(declaration.params)

    def call(
        self,
        interpreter: "Interpreter",
        args: list[Any],
        line: int = 0,
        column: int = 0,
        file: str = "<source>",
    ) -> Any:
        """Invoke the Nova function in a fresh child environment of its closure."""
        if len(args) != self.arity:
            raise NovaRuntimeError(
                f"Function '{self.name}' expects {self.arity} argument(s), got {len(args)}",
                line,
                column,
                file,
            )

        if interpreter.call_depth >= interpreter.max_call_depth:
            raise NovaRuntimeError(
                f"Maximum call depth exceeded ({interpreter.max_call_depth}) (possible infinite recursion)",
                line,
                column,
                file,
            )

        env = Environment(parent=self.closure)
        for param_name, arg_val in zip(self.declaration.params, args):
            env.define(param_name, arg_val, line, column, file)

        prev_env = interpreter.environment
        interpreter.environment = env
        interpreter.call_depth += 1

        try:
            for stmt in self.declaration.body.statements:
                interpreter.execute(stmt)
        except NovaReturnSignal as signal:
            return signal.value
        finally:
            interpreter.call_depth -= 1
            interpreter.environment = prev_env

        return None  # Nova null

    def __repr__(self) -> str:
        return f"<Event {self.name}>"


class Interpreter:
    """Tree-walking AST evaluator for Nova programs."""

    def __init__(
        self,
        stdout: Optional[TextIO] = None,
        stdin: Optional[TextIO] = None,
        max_steps: int = 100_000,
        max_call_depth: int = 500,
        file_name: str = "<source>",
    ) -> None:
        self.stdout: TextIO = stdout if stdout is not None else sys.stdout
        self.stdin: TextIO = stdin if stdin is not None else sys.stdin
        self.max_steps: int = max_steps
        self.max_call_depth: int = max_call_depth
        self.step_count: int = 0
        self.call_depth: int = 0
        self.file_name: str = file_name

        self.global_environment: Environment = Environment()
        self.environment: Environment = self.global_environment

        # Register standard built-in functions
        builtins = create_builtins(self.stdout, self.stdin)
        for name, builtin_fn in builtins.items():
            self.global_environment.define(name, builtin_fn)

    def interpret(
        self,
        program: Program,
        source_code: str = "",
        file_name: Optional[str] = None,
    ) -> Any:
        """Execute a parsed AST Program."""
        if file_name is not None:
            self.file_name = file_name
        self.step_count = 0
        self.call_depth = 0

        last_val: Any = None
        try:
            for stmt in program.statements:
                last_val = self.execute(stmt)
        except NovaReturnSignal as signal:
            raise NovaRuntimeError(
                "Cannot return outside of an Event function",
                signal.line,
                signal.column,
                self.file_name,
            )
        return last_val

    def _tick(self, line: int = 0, column: int = 0) -> None:
        """Step counter tick to prevent infinite loops."""
        self.step_count += 1
        if self.step_count > self.max_steps:
            raise NovaRuntimeError(
                f"Maximum execution steps exceeded ({self.max_steps}) (possible infinite loop)",
                line,
                column,
                self.file_name,
            )

    # ========================================================================
    # Statement Execution
    # ========================================================================

    def execute(self, stmt: Statement) -> Any:
        """Dispatch statement execution."""
        self._tick(stmt.line, stmt.column)

        if isinstance(stmt, VarDecl):
            return self._execute_var_decl(stmt)
        elif isinstance(stmt, FuncDecl):
            return self._execute_func_decl(stmt)
        elif isinstance(stmt, WhenStmt):
            return self._execute_when_stmt(stmt)
        elif isinstance(stmt, ChooseStmt):
            return self._execute_choose_stmt(stmt)
        elif isinstance(stmt, WhileStmt):
            return self._execute_while_stmt(stmt)
        elif isinstance(stmt, ReturnStmt):
            return self._execute_return_stmt(stmt)
        elif isinstance(stmt, Block):
            return self._execute_block(stmt)
        elif isinstance(stmt, ExprStmt):
            return self._execute_expr_stmt(stmt)
        else:
            raise NovaRuntimeError(
                f"Unknown statement type: {type(stmt).__name__}",
                stmt.line,
                stmt.column,
                self.file_name,
            )

    def _execute_var_decl(self, stmt: VarDecl) -> None:
        val = None
        if stmt.initializer is not None:
            val = self.evaluate(stmt.initializer)
        self.environment.define(
            stmt.name, val, stmt.line, stmt.column, self.file_name
        )

    def _execute_func_decl(self, stmt: FuncDecl) -> None:
        func = NovaFunction(declaration=stmt, closure=self.environment)
        self.environment.define(
            stmt.name, func, stmt.line, stmt.column, self.file_name
        )

    def _execute_when_stmt(self, stmt: WhenStmt) -> None:
        cond = self.evaluate(stmt.condition)
        if not isinstance(cond, bool):
            raise NovaRuntimeError(
                f"Condition for 'when' must evaluate to a boolean, got '{nova_type_name(cond)}'",
                stmt.condition.line,
                stmt.condition.column,
                self.file_name,
            )

        if cond is True:
            self._execute_block(stmt.then_branch)
            return

        for ow in stmt.otherwise_whens:
            ow_cond = self.evaluate(ow.condition)
            if not isinstance(ow_cond, bool):
                raise NovaRuntimeError(
                    f"Condition for 'otherwise when' must evaluate to a boolean, got '{nova_type_name(ow_cond)}'",
                    ow.condition.line,
                    ow.condition.column,
                    self.file_name,
                )
            if ow_cond is True:
                self._execute_block(ow.body)
                return

        if stmt.otherwise_branch is not None:
            self._execute_block(stmt.otherwise_branch)

    def _execute_choose_stmt(self, stmt: ChooseStmt) -> None:
        target_val = self.evaluate(stmt.expression)

        # Validate duplicate options and evaluate option conditions
        evaluated_options: list[tuple[Any, Block]] = []
        seen_values: list[Any] = []

        for opt in stmt.options:
            opt_val = self.evaluate(opt.value_expr)
            for seen in seen_values:
                if self._nova_equals(opt_val, seen):
                    raise NovaRuntimeError(
                        f"Duplicate option value '{nova_repr(opt_val)}' in 'choose' statement",
                        opt.line,
                        opt.column,
                        self.file_name,
                    )
            seen_values.append(opt_val)
            evaluated_options.append((opt_val, opt.body))

        # Match first matching option (no fallthrough)
        for opt_val, opt_body in evaluated_options:
            if self._nova_equals(target_val, opt_val):
                self._execute_block(opt_body)
                return

        if stmt.fallback is not None:
            self._execute_block(stmt.fallback.body)

    def _execute_while_stmt(self, stmt: WhileStmt) -> None:
        while True:
            self._tick(stmt.line, stmt.column)
            cond = self.evaluate(stmt.condition)
            if not isinstance(cond, bool):
                raise NovaRuntimeError(
                    f"Condition for 'while' must evaluate to a boolean, got '{nova_type_name(cond)}'",
                    stmt.condition.line,
                    stmt.condition.column,
                    self.file_name,
                )
            if not cond:
                break
            self._execute_block(stmt.body)

    def _execute_return_stmt(self, stmt: ReturnStmt) -> None:
        if self.call_depth <= 0:
            raise NovaRuntimeError(
                "Cannot return outside of an Event function",
                stmt.line,
                stmt.column,
                self.file_name,
            )

        val = None
        if stmt.value is not None:
            val = self.evaluate(stmt.value)
        raise NovaReturnSignal(val, stmt.line, stmt.column)

    def _execute_block(self, block: Block) -> None:
        block_env = Environment(parent=self.environment)
        prev_env = self.environment
        self.environment = block_env
        try:
            for s in block.statements:
                self.execute(s)
        finally:
            self.environment = prev_env

    def _execute_expr_stmt(self, stmt: ExprStmt) -> Any:
        return self.evaluate(stmt.expression)

    # ========================================================================
    # Expression Evaluation
    # ========================================================================

    def evaluate(self, expr: Expression) -> Any:
        """Dispatch expression evaluation."""
        if isinstance(expr, Literal):
            return expr.value

        elif isinstance(expr, VariableRef):
            return self.environment.get(
                expr.name, expr.line, expr.column, self.file_name
            )

        elif isinstance(expr, Assignment):
            val = self.evaluate(expr.value)
            self.environment.assign(
                expr.name, val, expr.line, expr.column, self.file_name
            )
            return val

        elif isinstance(expr, GroupingExpr):
            return self.evaluate(expr.expression)

        elif isinstance(expr, UnaryExpr):
            return self._evaluate_unary(expr)

        elif isinstance(expr, BinaryExpr):
            return self._evaluate_binary(expr)

        elif isinstance(expr, LogicalExpr):
            return self._evaluate_logical(expr)

        elif isinstance(expr, CallExpr):
            return self._evaluate_call(expr)

        elif isinstance(expr, ListLiteral):
            return [self.evaluate(el) for el in expr.elements]

        elif isinstance(expr, IndexExpr):
            return self._evaluate_index(expr)

        elif isinstance(expr, IndexAssignment):
            return self._evaluate_index_assignment(expr)

        else:
            raise NovaRuntimeError(
                f"Unknown expression type: {type(expr).__name__}",
                expr.line,
                expr.column,
                self.file_name,
            )

    def _evaluate_index(self, expr: IndexExpr) -> Any:
        target = self.evaluate(expr.target)
        index = self.evaluate(expr.index)

        if not isinstance(target, (list, str)):
            raise NovaRuntimeError(
                f"Cannot index into '{nova_type_name(target)}'",
                expr.line,
                expr.column,
                self.file_name,
            )

        if isinstance(index, bool) or not isinstance(index, int):
            raise NovaRuntimeError(
                f"Index must be an integer, got '{nova_type_name(index)}'",
                expr.line,
                expr.column,
                self.file_name,
            )

        target_len = len(target)
        if index < 0 or index >= target_len:
            raise NovaRuntimeError(
                f"Index {index} out of bounds for {nova_type_name(target)} of length {target_len}",
                expr.line,
                expr.column,
                self.file_name,
            )

        return target[index]

    def _evaluate_index_assignment(self, expr: IndexAssignment) -> Any:
        target = self.evaluate(expr.target)
        index = self.evaluate(expr.index)

        if not isinstance(target, list):
            raise NovaRuntimeError(
                f"Cannot assign to index of '{nova_type_name(target)}'",
                expr.line,
                expr.column,
                self.file_name,
            )

        if isinstance(index, bool) or not isinstance(index, int):
            raise NovaRuntimeError(
                f"Index must be an integer, got '{nova_type_name(index)}'",
                expr.line,
                expr.column,
                self.file_name,
            )

        target_len = len(target)
        if index < 0 or index >= target_len:
            raise NovaRuntimeError(
                f"Index {index} out of bounds for list of length {target_len}",
                expr.line,
                expr.column,
                self.file_name,
            )

        val = self.evaluate(expr.value)
        target[index] = val
        return val

    def _evaluate_unary(self, expr: UnaryExpr) -> Any:
        operand = self.evaluate(expr.operand)

        if expr.operator == "-":
            # Booleans must not be silently treated as numbers
            if isinstance(operand, bool) or not isinstance(operand, (int, float)):
                raise NovaRuntimeError(
                    f"Unary '-' operand must be a number, got '{nova_type_name(operand)}'",
                    expr.line,
                    expr.column,
                    self.file_name,
                )
            return -operand

        elif expr.operator == "not":
            if not isinstance(operand, bool):
                raise NovaRuntimeError(
                    f"Operand to 'not' must be a boolean, got '{nova_type_name(operand)}'",
                    expr.line,
                    expr.column,
                    self.file_name,
                )
            return not operand

        raise NovaRuntimeError(
            f"Unsupported unary operator '{expr.operator}'",
            expr.line,
            expr.column,
            self.file_name,
        )

    def _evaluate_binary(self, expr: BinaryExpr) -> Any:
        left = self.evaluate(expr.left)
        right = self.evaluate(expr.right)
        op = expr.operator

        # String and list concatenation
        if op == "+":
            if isinstance(left, str) and isinstance(right, str):
                return left + right
            if isinstance(left, list) and isinstance(right, list):
                return left + right
            if (
                not isinstance(left, bool)
                and not isinstance(right, bool)
                and isinstance(left, (int, float))
                and isinstance(right, (int, float))
            ):
                res = left + right
                return int(res) if isinstance(left, int) and isinstance(right, int) else res
            raise NovaRuntimeError(
                f"Cannot concatenate/add '{nova_type_name(left)}' and '{nova_type_name(right)}'",
                expr.line,
                expr.column,
                self.file_name,
            )

        # Arithmetic operators
        if op in ("-", "*", "/", "%"):
            if (
                isinstance(left, bool)
                or isinstance(right, bool)
                or not isinstance(left, (int, float))
                or not isinstance(right, (int, float))
            ):
                raise NovaRuntimeError(
                    f"Operator '{op}' requires numbers, got '{nova_type_name(left)}' and '{nova_type_name(right)}'",
                    expr.line,
                    expr.column,
                    self.file_name,
                )

            if op == "-":
                res = left - right
                return int(res) if isinstance(left, int) and isinstance(right, int) else res
            elif op == "*":
                res = left * right
                return int(res) if isinstance(left, int) and isinstance(right, int) else res
            elif op == "/":
                if right == 0:
                    raise NovaRuntimeError(
                        "Division by zero", expr.line, expr.column, self.file_name
                    )
                # If both are integers and divisible exactly, return integer; else float
                if isinstance(left, int) and isinstance(right, int):
                    if left % right == 0:
                        return left // right
                    return left / right
                return left / right
            elif op == "%":
                if right == 0:
                    raise NovaRuntimeError(
                        "Modulo by zero", expr.line, expr.column, self.file_name
                    )
                res = left % right
                return int(res) if isinstance(left, int) and isinstance(right, int) else res

        # Comparisons
        if op in ("<", "<=", ">", ">="):
            if (
                isinstance(left, bool)
                or isinstance(right, bool)
                or not isinstance(left, (int, float))
                or not isinstance(right, (int, float))
            ):
                raise NovaRuntimeError(
                    f"Comparison '{op}' not supported between '{nova_type_name(left)}' and '{nova_type_name(right)}'",
                    expr.line,
                    expr.column,
                    self.file_name,
                )
            if op == "<":
                return left < right
            elif op == "<=":
                return left <= right
            elif op == ">":
                return left > right
            elif op == ">=":
                return left >= right

        # Equality
        if op == "==":
            return self._nova_equals(left, right)
        elif op == "!=":
            return not self._nova_equals(left, right)

        raise NovaRuntimeError(
            f"Unsupported binary operator '{op}'",
            expr.line,
            expr.column,
            self.file_name,
        )

    def _evaluate_logical(self, expr: LogicalExpr) -> bool:
        left = self.evaluate(expr.left)
        if not isinstance(left, bool):
            raise NovaRuntimeError(
                f"Left operand of '{expr.operator}' must be a boolean, got '{nova_type_name(left)}'",
                expr.line,
                expr.column,
                self.file_name,
            )

        # Short-circuiting evaluation
        if expr.operator == "and":
            if left is False:
                return False
            right = self.evaluate(expr.right)
            if not isinstance(right, bool):
                raise NovaRuntimeError(
                    f"Right operand of 'and' must be a boolean, got '{nova_type_name(right)}'",
                    expr.line,
                    expr.column,
                    self.file_name,
                )
            return right

        elif expr.operator == "or":
            if left is True:
                return True
            right = self.evaluate(expr.right)
            if not isinstance(right, bool):
                raise NovaRuntimeError(
                    f"Right operand of 'or' must be a boolean, got '{nova_type_name(right)}'",
                    expr.line,
                    expr.column,
                    self.file_name,
                )
            return right

        raise NovaRuntimeError(
            f"Unsupported logical operator '{expr.operator}'",
            expr.line,
            expr.column,
            self.file_name,
        )

    def _evaluate_call(self, expr: CallExpr) -> Any:
        callee = self.evaluate(expr.callee)
        args = [self.evaluate(arg) for arg in expr.arguments]

        if isinstance(callee, NovaFunction):
            return callee.call(
                self, args, expr.line, expr.column, self.file_name
            )
        elif isinstance(callee, NovaBuiltin):
            return callee.call(
                args, expr.line, expr.column, self.file_name
            )
        else:
            raise NovaRuntimeError(
                f"'{nova_repr(callee)}' is not callable",
                expr.line,
                expr.column,
                self.file_name,
            )

    def _nova_equals(self, a: Any, b: Any) -> bool:
        """Determine equality between two values using Nova language semantics."""
        # Booleans must never be equal to numbers
        if isinstance(a, bool) or isinstance(b, bool):
            return isinstance(a, bool) and isinstance(b, bool) and a == b

        # Null check
        if a is None or b is None:
            return a is None and b is None

        # Numbers
        if isinstance(a, (int, float)) and isinstance(b, (int, float)):
            return a == b

        # Strings
        if isinstance(a, str) and isinstance(b, str):
            return a == b

        # Lists
        if isinstance(a, list) and isinstance(b, list):
            if len(a) != len(b):
                return False
            return all(self._nova_equals(x, y) for x, y in zip(a, b))

        return False
