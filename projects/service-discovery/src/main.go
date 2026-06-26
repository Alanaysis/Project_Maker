package main

import (
	"fmt"
	"os"
)

func main() {
	fmt.Println("=== Service Discovery System ===")
	fmt.Println()
	fmt.Println("This is a learning project implementing service discovery.")
	fmt.Println("Run the examples to see the system in action:")
	fmt.Println()
	fmt.Println("  Go to examples/ and run:")
	fmt.Println("    go run register_discover.go")
	fmt.Println("    go run health_check.go")
	fmt.Println("    go run load_balance.go")
	fmt.Println("    go run failure_recovery.go")
	fmt.Println()
	fmt.Println("Or run all tests:")
	fmt.Println("  go test ./tests/...")
	fmt.Println()

	os.Exit(0)
}
