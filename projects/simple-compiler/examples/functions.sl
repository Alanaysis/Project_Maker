// Function Examples
// Demonstrates function definitions and calls

// Simple function
fn greet(name) {
    print("Hello, " + name + "!");
}

// Function with multiple parameters
fn add(a, b) {
    return a + b;
}

// Function with conditional logic
fn max(a, b) {
    if a > b {
        return a;
    }
    return b;
}

// Recursive function: power
fn power(base, exp) {
    if exp == 0 {
        return 1;
    }
    return base * power(base, exp - 1);
}

// Use the functions
greet("World");

let sum = add(3, 4);
print("3 + 4 = ", sum);

let maximum = max(10, 20);
print("max(10, 20) = ", maximum);

let result = power(2, 10);
print("2^10 = ", result);
