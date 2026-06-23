// Loop Examples
// Demonstrates while loops and nested control flow

// Count from 1 to 5
print("Counting:");
let i = 1;
while i <= 5 {
    print(i);
    i = i + 1;
}

// Nested loops: multiplication table
print("\nMultiplication Table:");
let row = 1;
while row <= 5 {
    let col = 1;
    while col <= 5 {
        print(row * col, "\t");
        col = col + 1;
    }
    print("");
    row = row + 1;
}

// Sum of numbers
let sum = 0;
let n = 1;
while n <= 100 {
    sum = sum + n;
    n = n + 1;
}
print("\nSum of 1 to 100 = ", sum);
