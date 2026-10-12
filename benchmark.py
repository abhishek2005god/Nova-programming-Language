"""Benchmark script for the Nova programming language interpreter."""

import sys
import time
from pathlib import Path

# Add src to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from nova import Lexer, Parser, Interpreter


FIB_BENCHMARK = """
Event fib(n) {
    when (n <= 0) {
        return 0;
    } otherwise when (n == 1) {
        return 1;
    }
    return fib(n - 1) + fib(n - 2);
}

let result = fib(18);
"""

LOOP_BENCHMARK = """
let count = 0;
let i = 0;
while (i < 5000) {
    count = count + i;
    i = i + 1;
}
"""


def benchmark(name: str, source: str) -> None:
    # 1. Lexing
    t0 = time.perf_counter()
    lexer = Lexer(source)
    tokens = lexer.tokenize()
    t_lex = (time.perf_counter() - t0) * 1000

    # 2. Parsing
    t0 = time.perf_counter()
    parser = Parser(tokens)
    ast = parser.parse()
    t_parse = (time.perf_counter() - t0) * 1000

    # 3. Execution
    interpreter = Interpreter(max_steps=500_000)
    t0 = time.perf_counter()
    interpreter.interpret(ast, source_code=source)
    t_exec = (time.perf_counter() - t0) * 1000

    print(f"=== {name} ===")
    print(f"  Lexing:     {t_lex:6.2f} ms")
    print(f"  Parsing:    {t_parse:6.2f} ms")
    print(f"  Execution:  {t_exec:6.2f} ms")
    print(f"  Total:      {t_lex + t_parse + t_exec:6.2f} ms")
    print()


if __name__ == "__main__":
    print("Nova Interpreter Benchmark Suite\n" + "-" * 34)
    benchmark("Recursive Fibonacci(18)", FIB_BENCHMARK)
    benchmark("While Loop (5,000 iterations)", LOOP_BENCHMARK)
