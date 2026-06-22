package main

import (
	"bufio"
	"fmt"
	"os"
	"strings"
)

const VERSION = "0.1.0"

const BANNER = `
  ___       _                            _
 |_ _|_ __ | |_ ___ _ __ _ __  _ __ ___| |_ ___ _ __
  | || '_ \| __/ _ \ '__| '_ \| '__/ _ \ __/ _ \ '__|
  | || | | | ||  __/ |  | |_) | | |  __/ ||  __/ |
 |___|_| |_|\__\___|_|  | .__/|_|  \___|\__\___|_|
                        |_|
  v%s - A simple scripting language interpreter
  Type "help" for commands, "quit" to exit.
`

const HELP = `
Commands:
  help          Show this help message
  version       Show interpreter version
  quit / exit   Exit the REPL
  run <file>    Execute a script file

Language Syntax:
  let x = 10;              Variable declaration
  x = 20;                  Variable assignment
  print x;                 Print a value
  fn add(a, b) {           Function declaration
    return a + b;
  }
  let result = add(1, 2);  Function call
  if x > 5 {               Conditional
    print "big";
  } else {
    print "small";
  }
  while x > 0 {            Loop
    x = x - 1;
  }

Operators:
  + - * / %                 Arithmetic
  == != < > <= >=           Comparison
  and or not                Logical
`

func main() {
	if len(os.Args) > 1 {
		switch os.Args[1] {
		case "version":
			fmt.Printf("Interpreter v%s\n", VERSION)
			return
		case "run":
			if len(os.Args) < 3 {
				fmt.Fprintln(os.Stderr, "Usage: interpreter run <filename>")
				os.Exit(1)
			}
			err := RunFile(os.Args[2])
			if err != nil {
				fmt.Fprintf(os.Stderr, "Error: %s\n", err)
				os.Exit(1)
			}
			return
		case "help":
			fmt.Print(HELP)
			return
		default:
			// Treat as a file to run
			err := RunFile(os.Args[1])
			if err != nil {
				fmt.Fprintf(os.Stderr, "Error: %s\n", err)
				os.Exit(1)
			}
			return
		}
	}

	runREPL()
}

// runREPL starts an interactive Read-Eval-Print Loop.
func runREPL() {
	fmt.Printf(BANNER, VERSION)

	reader := bufio.NewReader(os.Stdin)
	interp := NewInterpreter()

	for {
		fmt.Print(">> ")
		input, err := reader.ReadString('\n')
		if err != nil {
			fmt.Println()
			break
		}

		input = strings.TrimSpace(input)
		if input == "" {
			continue
		}

		switch input {
		case "quit", "exit":
			fmt.Println("Goodbye!")
			return
		case "help":
			fmt.Print(HELP)
			continue
		case "version":
			fmt.Printf("Interpreter v%s\n", VERSION)
			continue
		}

		err = interp.Run(input)
		if err != nil {
			fmt.Fprintf(os.Stderr, "Error: %s\n", err)
			continue
		}

		output := interp.Output()
		if output != "" {
			fmt.Print(output)
			// Reset output buffer
			interp.output.Reset()
		}
	}
}
