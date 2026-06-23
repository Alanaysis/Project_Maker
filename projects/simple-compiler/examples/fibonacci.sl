// Fibonacci Sequence
// Demonstrates recursion

fn fib(n) {
    if n <= 1 {
        return n;
    }
    return fib(n - 1) + fib(n - 2);
}

// Print first 10 Fibonacci numbers
let i = 0;
while i < 10 {
    print("fib(", i, ") = ", fib(i));
    i = i + 1;
}
