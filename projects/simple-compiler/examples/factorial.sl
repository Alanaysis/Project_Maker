// Factorial Calculator
// Demonstrates recursion and conditionals

fn factorial(n) {
    if n <= 1 {
        return 1;
    }
    return n * factorial(n - 1);
}

// Print factorials from 0 to 10
let i = 0;
while i <= 10 {
    print(i, "! = ", factorial(i));
    i = i + 1;
}
