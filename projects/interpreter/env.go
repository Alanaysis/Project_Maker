package main

// Environment stores variable bindings with lexical scoping.
// Each environment has a reference to its parent (outer) scope,
// forming a chain that implements closures and block scoping.
type Environment struct {
	store map[string]Object
	outer *Environment
}

// NewEnvironment creates a new top-level environment.
func NewEnvironment() *Environment {
	return &Environment{
		store: make(map[string]Object),
		outer: nil,
	}
}

// NewEnclosedEnvironment creates a child environment with the given parent.
func NewEnclosedEnvironment(outer *Environment) *Environment {
	env := NewEnvironment()
	env.outer = outer
	return env
}

// Get retrieves a variable by name, walking up the scope chain.
func (e *Environment) Get(name string) (Object, bool) {
	obj, ok := e.store[name]
	if !ok && e.outer != nil {
		obj, ok = e.outer.Get(name)
	}
	return obj, ok
}

// Set creates or updates a variable in the current scope.
func (e *Environment) Set(name string, val Object) Object {
	e.store[name] = val
	return val
}

// Update modifies an existing variable in the closest scope where it was defined.
// Returns false if the variable is not found in any scope.
func (e *Environment) Update(name string, val Object) bool {
	if _, ok := e.store[name]; ok {
		e.store[name] = val
		return true
	}
	if e.outer != nil {
		return e.outer.Update(name, val)
	}
	return false
}
