package main

import "testing"

func TestEnvironmentSetAndGet(t *testing.T) {
	env := NewEnvironment()

	env.Set("x", &Number{Value: 10})
	val, ok := env.Get("x")

	if !ok {
		t.Fatal("expected to find variable 'x'")
	}
	num, ok := val.(*Number)
	if !ok {
		t.Fatalf("expected *Number, got %T", val)
	}
	if num.Value != 10 {
		t.Errorf("expected 10, got %f", num.Value)
	}
}

func TestEnvironmentGetUndefined(t *testing.T) {
	env := NewEnvironment()

	_, ok := env.Get("missing")
	if ok {
		t.Error("expected variable 'missing' to not be found")
	}
}

func TestEnvironmentOverwrite(t *testing.T) {
	env := NewEnvironment()

	env.Set("x", &Number{Value: 1})
	env.Set("x", &Number{Value: 2})

	val, ok := env.Get("x")
	if !ok {
		t.Fatal("expected to find variable 'x'")
	}
	if val.(*Number).Value != 2 {
		t.Errorf("expected 2, got %f", val.(*Number).Value)
	}
}

func TestEnvironmentEnclosedScoping(t *testing.T) {
	outer := NewEnvironment()
	outer.Set("x", &Number{Value: 10})

	inner := NewEnclosedEnvironment(outer)
	inner.Set("y", &Number{Value: 20})

	// inner can see both x and y
	val, ok := inner.Get("x")
	if !ok || val.(*Number).Value != 10 {
		t.Error("expected inner scope to see outer variable 'x' = 10")
	}

	val, ok = inner.Get("y")
	if !ok || val.(*Number).Value != 20 {
		t.Error("expected inner scope to see own variable 'y' = 20")
	}

	// outer cannot see y
	_, ok = outer.Get("y")
	if ok {
		t.Error("expected outer scope to not see inner variable 'y'")
	}
}

func TestEnvironmentShadowing(t *testing.T) {
	outer := NewEnvironment()
	outer.Set("x", &Number{Value: 10})

	inner := NewEnclosedEnvironment(outer)
	inner.Set("x", &Number{Value: 20})

	// inner sees its own x
	val, _ := inner.Get("x")
	if val.(*Number).Value != 20 {
		t.Errorf("expected inner x = 20, got %f", val.(*Number).Value)
	}

	// outer still sees original x
	val, _ = outer.Get("x")
	if val.(*Number).Value != 10 {
		t.Errorf("expected outer x = 10, got %f", val.(*Number).Value)
	}
}

func TestEnvironmentUpdate(t *testing.T) {
	env := NewEnvironment()
	env.Set("x", &Number{Value: 1})

	ok := env.Update("x", &Number{Value: 2})
	if !ok {
		t.Fatal("expected Update to succeed")
	}

	val, _ := env.Get("x")
	if val.(*Number).Value != 2 {
		t.Errorf("expected 2, got %f", val.(*Number).Value)
	}
}

func TestEnvironmentUpdateUndefined(t *testing.T) {
	env := NewEnvironment()

	ok := env.Update("missing", &Number{Value: 1})
	if ok {
		t.Error("expected Update to fail for undefined variable")
	}
}

func TestEnvironmentUpdateOuterScope(t *testing.T) {
	outer := NewEnvironment()
	outer.Set("x", &Number{Value: 10})

	inner := NewEnclosedEnvironment(outer)

	// Update x through inner scope -- should find it in outer
	ok := inner.Update("x", &Number{Value: 20})
	if !ok {
		t.Fatal("expected Update to succeed via outer scope")
	}

	// Verify it was updated in the outer scope
	val, _ := outer.Get("x")
	if val.(*Number).Value != 20 {
		t.Errorf("expected outer x = 20, got %f", val.(*Number).Value)
	}
}

func TestEnvironmentMultipleVariables(t *testing.T) {
	env := NewEnvironment()
	env.Set("a", &Number{Value: 1})
	env.Set("b", &Str{Value: "hello"})
	env.Set("c", &Boolean{Value: true})

	a, ok := env.Get("a")
	if !ok || a.(*Number).Value != 1 {
		t.Error("expected a = 1")
	}

	b, ok := env.Get("b")
	if !ok || b.(*Str).Value != "hello" {
		t.Error("expected b = 'hello'")
	}

	c, ok := env.Get("c")
	if !ok || c.(*Boolean).Value != true {
		t.Error("expected c = true")
	}
}

func TestEnvironmentDeepNesting(t *testing.T) {
	env1 := NewEnvironment()
	env1.Set("x", &Number{Value: 1})

	env2 := NewEnclosedEnvironment(env1)
	env2.Set("y", &Number{Value: 2})

	env3 := NewEnclosedEnvironment(env2)
	env3.Set("z", &Number{Value: 3})

	// env3 can see all variables
	val, ok := env3.Get("x")
	if !ok || val.(*Number).Value != 1 {
		t.Error("expected deep scope to see x = 1")
	}
	val, ok = env3.Get("y")
	if !ok || val.(*Number).Value != 2 {
		t.Error("expected deep scope to see y = 2")
	}
	val, ok = env3.Get("z")
	if !ok || val.(*Number).Value != 3 {
		t.Error("expected deep scope to see z = 3")
	}

	// env1 can only see x
	_, ok = env1.Get("y")
	if ok {
		t.Error("expected env1 to not see y")
	}
	_, ok = env1.Get("z")
	if ok {
		t.Error("expected env1 to not see z")
	}
}
