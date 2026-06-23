// Prime Number Finder
// Demonstrates nested loops and conditionals

fn is_prime(n) {
    if n <= 1 {
        return false;
    }
    if n <= 3 {
        return true;
    }
    if n % 2 == 0 {
        return false;
    }

    let i = 3;
    while i * i <= n {
        if n % i == 0 {
            return false;
        }
        i = i + 2;
    }
    return true;
}

// Find all primes up to 50
print("Prime numbers up to 50:");
let n = 2;
while n <= 50 {
    if is_prime(n) {
        print(n);
    }
    n = n + 1;
}

// Count primes
let count = 0;
let n = 2;
while n <= 100 {
    if is_prime(n) {
        count = count + 1;
    }
    n = n + 1;
}
print("\nNumber of primes up to 100: ", count);
