package tests

import (
	"os"
	"os/exec"
	"path/filepath"
	"strings"
	"testing"
)

// buildInterpreter compiles the interpreter binary and returns its path.
func buildInterpreter(t *testing.T) string {
	t.Helper()

	// Find the project root (parent of tests/)
	wd, err := os.Getwd()
	if err != nil {
		t.Fatalf("failed to get working directory: %v", err)
	}
	projectRoot := filepath.Dir(wd)

	binary := filepath.Join(t.TempDir(), "interpreter")
	cmd := exec.Command("go", "build", "-o", binary, ".")
	cmd.Dir = projectRoot
	output, err := cmd.CombinedOutput()
	if err != nil {
		t.Fatalf("failed to build interpreter: %v\n%s", err, output)
	}
	return binary
}

func TestExampleHello(t *testing.T) {
	binary := buildInterpreter(t)
	projectRoot := filepath.Dir(filepath.Join(binary, "..")) // not needed, use wd

	wd, _ := os.Getwd()
	projectRoot = filepath.Dir(wd)

	cmd := exec.Command(binary, filepath.Join(projectRoot, "examples", "hello.mini"))
	output, err := cmd.CombinedOutput()
	if err != nil {
		t.Fatalf("failed to run hello.mini: %v\n%s", err, output)
	}

	result := strings.TrimSpace(string(output))
	lines := strings.Split(result, "\n")
	if lines[0] != "Hello, World!" {
		t.Errorf("expected first line %q, got %q", "Hello, World!", lines[0])
	}
}

func TestExampleFactorial(t *testing.T) {
	binary := buildInterpreter(t)
	wd, _ := os.Getwd()
	projectRoot := filepath.Dir(wd)

	cmd := exec.Command(binary, filepath.Join(projectRoot, "examples", "factorial.mini"))
	output, err := cmd.CombinedOutput()
	if err != nil {
		t.Fatalf("failed to run factorial.mini: %v\n%s", err, output)
	}

	result := strings.TrimSpace(string(output))
	if !strings.Contains(result, "120") {
		t.Errorf("expected output to contain '120', got %q", result)
	}
}

func TestExampleFibonacci(t *testing.T) {
	binary := buildInterpreter(t)
	wd, _ := os.Getwd()
	projectRoot := filepath.Dir(wd)

	cmd := exec.Command(binary, filepath.Join(projectRoot, "examples", "fibonacci.mini"))
	output, err := cmd.CombinedOutput()
	if err != nil {
		t.Fatalf("failed to run fibonacci.mini: %v\n%s", err, output)
	}

	result := strings.TrimSpace(string(output))
	if !strings.Contains(result, "55") {
		t.Errorf("expected output to contain '55', got %q", result)
	}
}

func TestExampleFizzBuzz(t *testing.T) {
	binary := buildInterpreter(t)
	wd, _ := os.Getwd()
	projectRoot := filepath.Dir(wd)

	cmd := exec.Command(binary, filepath.Join(projectRoot, "examples", "fizzbuzz.mini"))
	output, err := cmd.CombinedOutput()
	if err != nil {
		t.Fatalf("failed to run fizzbuzz.mini: %v\n%s", err, output)
	}

	result := strings.TrimSpace(string(output))
	if !strings.Contains(result, "Fizz") || !strings.Contains(result, "Buzz") {
		t.Errorf("expected output to contain 'Fizz' and 'Buzz', got %q", result)
	}
}

func TestExampleClosure(t *testing.T) {
	binary := buildInterpreter(t)
	wd, _ := os.Getwd()
	projectRoot := filepath.Dir(wd)

	cmd := exec.Command(binary, filepath.Join(projectRoot, "examples", "closure.mini"))
	output, err := cmd.CombinedOutput()
	if err != nil {
		t.Fatalf("failed to run closure.mini: %v\n%s", err, output)
	}

	result := strings.TrimSpace(string(output))
	if result == "" {
		t.Error("expected non-empty output from closure.mini")
	}
}

func TestExamplePrimes(t *testing.T) {
	binary := buildInterpreter(t)
	wd, _ := os.Getwd()
	projectRoot := filepath.Dir(wd)

	cmd := exec.Command(binary, filepath.Join(projectRoot, "examples", "primes.mini"))
	output, err := cmd.CombinedOutput()
	if err != nil {
		t.Fatalf("failed to run primes.mini: %v\n%s", err, output)
	}

	result := strings.TrimSpace(string(output))
	if !strings.Contains(result, "2") || !strings.Contains(result, "3") {
		t.Errorf("expected output to contain prime numbers, got %q", result)
	}
}

func TestExampleHigherOrder(t *testing.T) {
	binary := buildInterpreter(t)
	wd, _ := os.Getwd()
	projectRoot := filepath.Dir(wd)

	cmd := exec.Command(binary, filepath.Join(projectRoot, "examples", "higherorder.mini"))
	output, err := cmd.CombinedOutput()
	if err != nil {
		t.Fatalf("failed to run higherorder.mini: %v\n%s", err, output)
	}

	result := strings.TrimSpace(string(output))
	if result == "" {
		t.Error("expected non-empty output from higherorder.mini")
	}
}

func TestExampleStringOps(t *testing.T) {
	binary := buildInterpreter(t)
	wd, _ := os.Getwd()
	projectRoot := filepath.Dir(wd)

	cmd := exec.Command(binary, filepath.Join(projectRoot, "examples", "stringops.mini"))
	output, err := cmd.CombinedOutput()
	if err != nil {
		t.Fatalf("failed to run stringops.mini: %v\n%s", err, output)
	}

	result := strings.TrimSpace(string(output))
	if result == "" {
		t.Error("expected non-empty output from stringops.mini")
	}
}

func TestExampleBuiltins(t *testing.T) {
	binary := buildInterpreter(t)
	wd, _ := os.Getwd()
	projectRoot := filepath.Dir(wd)

	cmd := exec.Command(binary, filepath.Join(projectRoot, "examples", "builtins.mini"))
	output, err := cmd.CombinedOutput()
	if err != nil {
		t.Fatalf("failed to run builtins.mini: %v\n%s", err, output)
	}

	result := strings.TrimSpace(string(output))
	if result == "" {
		t.Error("expected non-empty output from builtins.mini")
	}
}

func TestExampleSorting(t *testing.T) {
	binary := buildInterpreter(t)
	wd, _ := os.Getwd()
	projectRoot := filepath.Dir(wd)

	cmd := exec.Command(binary, filepath.Join(projectRoot, "examples", "sorting.mini"))
	output, err := cmd.CombinedOutput()
	if err != nil {
		t.Fatalf("failed to run sorting.mini: %v\n%s", err, output)
	}

	result := strings.TrimSpace(string(output))
	if result == "" {
		t.Error("expected non-empty output from sorting.mini")
	}
}

func TestExampleLogic(t *testing.T) {
	binary := buildInterpreter(t)
	wd, _ := os.Getwd()
	projectRoot := filepath.Dir(wd)

	cmd := exec.Command(binary, filepath.Join(projectRoot, "examples", "logic.mini"))
	output, err := cmd.CombinedOutput()
	if err != nil {
		t.Fatalf("failed to run logic.mini: %v\n%s", err, output)
	}

	result := strings.TrimSpace(string(output))
	if result == "" {
		t.Error("expected non-empty output from logic.mini")
	}
}

func TestNonexistentFile(t *testing.T) {
	binary := buildInterpreter(t)

	cmd := exec.Command(binary, "/tmp/nonexistent_file_12345.mini")
	_, err := cmd.CombinedOutput()
	if err == nil {
		t.Error("expected error for nonexistent file")
	}
}

func TestInvalidScript(t *testing.T) {
	binary := buildInterpreter(t)

	// Write an invalid script to a temp file
	tmpFile := filepath.Join(t.TempDir(), "bad.mini")
	err := os.WriteFile(tmpFile, []byte("let 5 = x;"), 0644)
	if err != nil {
		t.Fatalf("failed to write temp file: %v", err)
	}

	cmd := exec.Command(binary, tmpFile)
	_, err = cmd.CombinedOutput()
	if err == nil {
		t.Error("expected error for invalid script")
	}
}
