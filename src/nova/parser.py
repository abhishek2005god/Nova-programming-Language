"""Recursive-descent parser for the Nova programming language."""

from typing import Optional
from nova.tokens import Token, TokenType
from nova.errors import NovaSyntaxError
from nova.ast_nodes import (
    Program,
    Statement,
    Expression,
    VarDecl,
    FuncDecl,
    WhenStmt,
    OtherwiseWhenBranch,
    ChooseStmt,
    OptionBranch,
    FallbackBranch,
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


class Parser:
    """Parses a stream of Nova tokens into an Abstract Syntax Tree (AST)."""

    def __init__(self, tokens: list[Token], file_name: str = "<source>") -> None:
        self.tokens: list[Token] = tokens
        self.file_name: str = file_name
        self.current: int = 0
        self.errors: list[NovaSyntaxError] = []

    def parse(self) -> Program:
        """Parse all tokens into a Program AST node."""
        statements: list[Statement] = []
        while not self._is_at_end():
            # Skip stray semicolons
            if self._match(TokenType.SEMICOLON):
                continue
            stmt = self._statement()
            if stmt is not None:
                statements.append(stmt)

        if self.errors:
            # Raise the first syntax error encountered
            raise self.errors[0]

        start_line = statements[0].line if statements else 1
        start_col = statements[0].column if statements else 1
        return Program(statements=statements, line=start_line, column=start_col)

    # ========================================================================
    # Statement Parsing
    # ========================================================================

    def _statement(self) -> Optional[Statement]:
        try:
            if self._match(TokenType.LET):
                return self._var_declaration()
            if self._match(TokenType.EVENT):
                return self._func_declaration()
            if self._match(TokenType.WHEN):
                return self._when_statement()
            if self._match(TokenType.CHOOSE):
                return self._choose_statement()
            if self._match(TokenType.WHILE):
                return self._while_statement()
            if self._match(TokenType.RETURN):
                return self._return_statement()
            if self._match(TokenType.LEFT_BRACE):
                return self._block()
            if self._match(TokenType.SEMICOLON):
                return None
            return self._expression_statement()
        except NovaSyntaxError as e:
            self.errors.append(e)
            self._synchronize()
            return None

    def _var_declaration(self) -> VarDecl:
        let_token = self._previous()
        name_token = self._consume(
            TokenType.IDENTIFIER, "Expected variable name after 'let'"
        )

        initializer: Optional[Expression] = None
        if self._match(TokenType.EQUAL):
            initializer = self._expression()

        self._consume(TokenType.SEMICOLON, "Expected ';' after variable declaration")
        return VarDecl(
            name=name_token.lexeme,
            initializer=initializer,
            line=let_token.line,
            column=let_token.column,
        )

    def _func_declaration(self) -> FuncDecl:
        event_token = self._previous()
        name_token = self._consume(
            TokenType.IDENTIFIER, "Expected function name after 'Event'"
        )

        self._consume(TokenType.LEFT_PAREN, "Expected '(' after function name")
        params: list[str] = []
        if not self._check(TokenType.RIGHT_PAREN):
            first_param = self._consume(
                TokenType.IDENTIFIER, "Expected parameter name"
            )
            params.append(first_param.lexeme)
            while self._match(TokenType.COMMA):
                next_param = self._consume(
                    TokenType.IDENTIFIER, "Expected parameter name after ','"
                )
                params.append(next_param.lexeme)

        self._consume(TokenType.RIGHT_PAREN, "Expected ')' after parameter list")
        self._consume(TokenType.LEFT_BRACE, "Expected '{' before function body")
        body = self._block()

        return FuncDecl(
            name=name_token.lexeme,
            params=params,
            body=body,
            line=event_token.line,
            column=event_token.column,
        )

    def _when_statement(self) -> WhenStmt:
        when_token = self._previous()
        self._consume(TokenType.LEFT_PAREN, "Expected '(' after 'when'")
        condition = self._expression()
        self._consume(TokenType.RIGHT_PAREN, "Expected ')' after 'when' condition")
        self._consume(TokenType.LEFT_BRACE, "Expected '{' before 'when' body")
        then_branch = self._block()

        otherwise_whens: list[OtherwiseWhenBranch] = []
        otherwise_branch: Optional[Block] = None

        while self._match(TokenType.OTHERWISE):
            other_token = self._previous()
            if self._match(TokenType.WHEN):
                self._consume(
                    TokenType.LEFT_PAREN, "Expected '(' after 'otherwise when'"
                )
                ow_cond = self._expression()
                self._consume(
                    TokenType.RIGHT_PAREN,
                    "Expected ')' after 'otherwise when' condition",
                )
                self._consume(
                    TokenType.LEFT_BRACE, "Expected '{' before 'otherwise when' body"
                )
                ow_body = self._block()
                otherwise_whens.append(
                    OtherwiseWhenBranch(
                        condition=ow_cond,
                        body=ow_body,
                        line=other_token.line,
                        column=other_token.column,
                    )
                )
            else:
                self._consume(
                    TokenType.LEFT_BRACE, "Expected '{' before 'otherwise' body"
                )
                otherwise_branch = self._block()
                break

        return WhenStmt(
            condition=condition,
            then_branch=then_branch,
            otherwise_whens=otherwise_whens,
            otherwise_branch=otherwise_branch,
            line=when_token.line,
            column=when_token.column,
        )

    def _choose_statement(self) -> ChooseStmt:
        choose_token = self._previous()
        self._consume(TokenType.LEFT_PAREN, "Expected '(' after 'choose'")
        expr = self._expression()
        self._consume(TokenType.RIGHT_PAREN, "Expected ')' after 'choose' expression")
        self._consume(TokenType.LEFT_BRACE, "Expected '{' before 'choose' options")

        options: list[OptionBranch] = []
        fallback: Optional[FallbackBranch] = None

        while not self._check(TokenType.RIGHT_BRACE) and not self._is_at_end():
            if self._match(TokenType.OPTION):
                opt_token = self._previous()
                if fallback is not None:
                    raise NovaSyntaxError(
                        "'option' branch cannot appear after 'fallback' in 'choose' statement",
                        opt_token.line,
                        opt_token.column,
                        self.file_name,
                    )
                val_expr = self._expression()
                self._consume(
                    TokenType.LEFT_BRACE, "Expected '{' before 'option' body"
                )
                body = self._block()
                options.append(
                    OptionBranch(
                        value_expr=val_expr,
                        body=body,
                        line=opt_token.line,
                        column=opt_token.column,
                    )
                )
            elif self._match(TokenType.FALLBACK):
                fb_token = self._previous()
                if fallback is not None:
                    raise NovaSyntaxError(
                        "Multiple 'fallback' branches in 'choose' statement",
                        fb_token.line,
                        fb_token.column,
                        self.file_name,
                    )
                self._consume(
                    TokenType.LEFT_BRACE, "Expected '{' before 'fallback' body"
                )
                fb_body = self._block()
                fallback = FallbackBranch(
                    body=fb_body, line=fb_token.line, column=fb_token.column
                )
            else:
                tok = self._peek()
                raise NovaSyntaxError(
                    f"Expected 'option' or 'fallback' inside 'choose' block, got '{tok.lexeme}'",
                    tok.line,
                    tok.column,
                    self.file_name,
                )

        self._consume(TokenType.RIGHT_BRACE, "Expected '}' after 'choose' block")
        return ChooseStmt(
            expression=expr,
            options=options,
            fallback=fallback,
            line=choose_token.line,
            column=choose_token.column,
        )

    def _while_statement(self) -> WhileStmt:
        while_token = self._previous()
        self._consume(TokenType.LEFT_PAREN, "Expected '(' after 'while'")
        condition = self._expression()
        self._consume(TokenType.RIGHT_PAREN, "Expected ')' after 'while' condition")
        self._consume(TokenType.LEFT_BRACE, "Expected '{' before 'while' body")
        body = self._block()

        return WhileStmt(
            condition=condition,
            body=body,
            line=while_token.line,
            column=while_token.column,
        )

    def _return_statement(self) -> ReturnStmt:
        ret_token = self._previous()
        value: Optional[Expression] = None
        if not self._check(TokenType.SEMICOLON):
            value = self._expression()

        self._consume(TokenType.SEMICOLON, "Expected ';' after return statement")
        return ReturnStmt(
            value=value, line=ret_token.line, column=ret_token.column
        )

    def _block(self) -> Block:
        # Assumes '{' has just been consumed
        brace_token = self._previous()
        statements: list[Statement] = []

        while not self._check(TokenType.RIGHT_BRACE) and not self._is_at_end():
            if self._match(TokenType.SEMICOLON):
                continue
            stmt = self._statement()
            if stmt is not None:
                statements.append(stmt)

        self._consume(TokenType.RIGHT_BRACE, "Expected '}' after block")
        return Block(
            statements=statements,
            line=brace_token.line,
            column=brace_token.column,
        )

    def _expression_statement(self) -> ExprStmt:
        expr = self._expression()
        self._consume(TokenType.SEMICOLON, "Expected ';' after expression")
        return ExprStmt(
            expression=expr, line=expr.line, column=expr.column
        )

    # ========================================================================
    # Expression Parsing (Precedence Hierarchy)
    # ========================================================================

    def _expression(self) -> Expression:
        return self._assignment()

    def _assignment(self) -> Expression:
        expr = self._logic_or()

        if self._match(TokenType.EQUAL):
            equals_token = self._previous()
            value = self._assignment()  # Right-associative

            if isinstance(expr, VariableRef):
                return Assignment(
                    name=expr.name,
                    value=value,
                    line=expr.line,
                    column=expr.column,
                )
            elif isinstance(expr, IndexExpr):
                return IndexAssignment(
                    target=expr.target,
                    index=expr.index,
                    value=value,
                    line=expr.line,
                    column=expr.column,
                )

            raise NovaSyntaxError(
                "Invalid assignment target",
                equals_token.line,
                equals_token.column,
                self.file_name,
            )

        return expr

    def _logic_or(self) -> Expression:
        expr = self._logic_and()

        while self._match(TokenType.OR):
            operator = self._previous()
            right = self._logic_and()
            expr = LogicalExpr(
                left=expr,
                operator=operator.lexeme,
                right=right,
                line=operator.line,
                column=operator.column,
            )

        return expr

    def _logic_and(self) -> Expression:
        expr = self._equality()

        while self._match(TokenType.AND):
            operator = self._previous()
            right = self._equality()
            expr = LogicalExpr(
                left=expr,
                operator=operator.lexeme,
                right=right,
                line=operator.line,
                column=operator.column,
            )

        return expr

    def _equality(self) -> Expression:
        expr = self._comparison()

        while self._match(TokenType.EQUAL_EQUAL, TokenType.BANG_EQUAL):
            operator = self._previous()
            right = self._comparison()
            expr = BinaryExpr(
                left=expr,
                operator=operator.lexeme,
                right=right,
                line=operator.line,
                column=operator.column,
            )

        return expr

    def _comparison(self) -> Expression:
        expr = self._term()

        while self._match(
            TokenType.LESS,
            TokenType.LESS_EQUAL,
            TokenType.GREATER,
            TokenType.GREATER_EQUAL,
        ):
            operator = self._previous()
            right = self._term()
            expr = BinaryExpr(
                left=expr,
                operator=operator.lexeme,
                right=right,
                line=operator.line,
                column=operator.column,
            )

        return expr

    def _term(self) -> Expression:
        expr = self._factor()

        while self._match(TokenType.PLUS, TokenType.MINUS):
            operator = self._previous()
            right = self._factor()
            expr = BinaryExpr(
                left=expr,
                operator=operator.lexeme,
                right=right,
                line=operator.line,
                column=operator.column,
            )

        return expr

    def _factor(self) -> Expression:
        expr = self._unary()

        while self._match(TokenType.STAR, TokenType.SLASH, TokenType.PERCENT):
            operator = self._previous()
            right = self._unary()
            expr = BinaryExpr(
                left=expr,
                operator=operator.lexeme,
                right=right,
                line=operator.line,
                column=operator.column,
            )

        return expr

    def _unary(self) -> Expression:
        if self._match(TokenType.MINUS, TokenType.NOT):
            operator = self._previous()
            operand = self._unary()
            return UnaryExpr(
                operator=operator.lexeme,
                operand=operand,
                line=operator.line,
                column=operator.column,
            )

        return self._call()

    def _call(self) -> Expression:
        expr = self._primary()

        while True:
            if self._match(TokenType.LEFT_PAREN):
                paren = self._previous()
                arguments: list[Expression] = []
                if not self._check(TokenType.RIGHT_PAREN):
                    arguments.append(self._expression())
                    while self._match(TokenType.COMMA):
                        arguments.append(self._expression())
                self._consume(
                    TokenType.RIGHT_PAREN, "Expected ')' after arguments"
                )
                expr = CallExpr(
                    callee=expr,
                    arguments=arguments,
                    line=paren.line,
                    column=paren.column,
                )
            elif self._match(TokenType.LEFT_BRACKET):
                bracket = self._previous()
                index = self._expression()
                self._consume(
                    TokenType.RIGHT_BRACKET, "Expected ']' after index expression"
                )
                expr = IndexExpr(
                    target=expr,
                    index=index,
                    line=bracket.line,
                    column=bracket.column,
                )
            else:
                break

        return expr

    def _primary(self) -> Expression:
        if self._match(TokenType.FALSE):
            tok = self._previous()
            return Literal(
                value=False, raw="false", line=tok.line, column=tok.column
            )
        if self._match(TokenType.TRUE):
            tok = self._previous()
            return Literal(
                value=True, raw="true", line=tok.line, column=tok.column
            )
        if self._match(TokenType.NULL):
            tok = self._previous()
            return Literal(
                value=None, raw="null", line=tok.line, column=tok.column
            )

        if self._match(TokenType.INTEGER, TokenType.FLOAT, TokenType.STRING):
            tok = self._previous()
            return Literal(
                value=tok.literal,
                raw=tok.lexeme,
                line=tok.line,
                column=tok.column,
            )

        if self._match(TokenType.IDENTIFIER):
            tok = self._previous()
            return VariableRef(
                name=tok.lexeme, line=tok.line, column=tok.column
            )

        if self._match(TokenType.LEFT_BRACKET):
            bracket = self._previous()
            elements: list[Expression] = []
            if not self._check(TokenType.RIGHT_BRACKET):
                elements.append(self._expression())
                while self._match(TokenType.COMMA):
                    if self._check(TokenType.RIGHT_BRACKET):
                        break
                    elements.append(self._expression())
            self._consume(
                TokenType.RIGHT_BRACKET, "Expected ']' after list elements"
            )
            return ListLiteral(
                elements=elements, line=bracket.line, column=bracket.column
            )

        if self._match(TokenType.LEFT_PAREN):
            paren = self._previous()
            expr = self._expression()
            self._consume(
                TokenType.RIGHT_PAREN, "Expected ')' after parenthesized expression"
            )
            return GroupingExpr(
                expression=expr, line=paren.line, column=paren.column
            )

        tok = self._peek()
        raise NovaSyntaxError(
            f"Unexpected token '{tok.lexeme or tok.type.name}'",
            tok.line,
            tok.column,
            self.file_name,
        )

    # ========================================================================
    # Parser Navigation & Helper Methods
    # ========================================================================

    def _match(self, *types: TokenType) -> bool:
        for t in types:
            if self._check(t):
                self._advance()
                return True
        return False

    def _check(self, token_type: TokenType) -> bool:
        if self._is_at_end():
            return False
        return self._peek().type == token_type

    def _advance(self) -> Token:
        if not self._is_at_end():
            self.current += 1
        return self._previous()

    def _is_at_end(self) -> bool:
        return self._peek().type == TokenType.EOF

    def _peek(self) -> Token:
        return self.tokens[self.current]

    def _previous(self) -> Token:
        return self.tokens[self.current - 1]

    def _consume(self, token_type: TokenType, message: str) -> Token:
        if self._check(token_type):
            return self._advance()
        tok = self._peek()
        raise NovaSyntaxError(message, tok.line, tok.column, self.file_name)

    def _synchronize(self) -> None:
        """Skip tokens until the next statement boundary after a syntax error."""
        self._advance()
        while not self._is_at_end():
            if self._previous().type == TokenType.SEMICOLON:
                return
            if self._peek().type in (
                TokenType.LET,
                TokenType.EVENT,
                TokenType.WHEN,
                TokenType.CHOOSE,
                TokenType.WHILE,
                TokenType.RETURN,
                TokenType.LEFT_BRACE,
            ):
                return
            self._advance()
