package game

import (
	"math"
	"testing"
)

func TestVector2Add(t *testing.T) {
	v1 := Vector2{X: 1, Y: 2}
	v2 := Vector2{X: 3, Y: 4}
	result := v1.Add(v2)

	if result.X != 4 || result.Y != 6 {
		t.Errorf("Add failed: got (%.1f, %.1f), want (4, 6)", result.X, result.Y)
	}
}

func TestVector2Sub(t *testing.T) {
	v1 := Vector2{X: 5, Y: 7}
	v2 := Vector2{X: 2, Y: 3}
	result := v1.Sub(v2)

	if result.X != 3 || result.Y != 4 {
		t.Errorf("Sub failed: got (%.1f, %.1f), want (3, 4)", result.X, result.Y)
	}
}

func TestVector2Scale(t *testing.T) {
	v := Vector2{X: 2, Y: 3}
	result := v.Scale(2.0)

	if result.X != 4 || result.Y != 6 {
		t.Errorf("Scale failed: got (%.1f, %.1f), want (4, 6)", result.X, result.Y)
	}
}

func TestVector2Length(t *testing.T) {
	v := Vector2{X: 3, Y: 4}
	length := v.Length()

	if math.Abs(length-5.0) > 0.001 {
		t.Errorf("Length failed: got %.3f, want 5.0", length)
	}
}

func TestVector2Normalize(t *testing.T) {
	v := Vector2{X: 3, Y: 4}
	normalized := v.Normalize()

	length := normalized.Length()
	if math.Abs(length-1.0) > 0.001 {
		t.Errorf("Normalize failed: length is %.3f, want 1.0", length)
	}

	expectedX := 3.0 / 5.0
	expectedY := 4.0 / 5.0
	if math.Abs(normalized.X-expectedX) > 0.001 || math.Abs(normalized.Y-expectedY) > 0.001 {
		t.Errorf("Normalize failed: got (%.3f, %.3f), want (%.3f, %.3f)",
			normalized.X, normalized.Y, expectedX, expectedY)
	}
}

func TestVector2NormalizeZero(t *testing.T) {
	v := Vector2{X: 0, Y: 0}
	normalized := v.Normalize()

	if normalized.X != 0 || normalized.Y != 0 {
		t.Errorf("Normalize zero vector failed: got (%.1f, %.1f), want (0, 0)",
			normalized.X, normalized.Y)
	}
}

func TestVector2Distance(t *testing.T) {
	v1 := Vector2{X: 0, Y: 0}
	v2 := Vector2{X: 3, Y: 4}
	distance := v1.Distance(v2)

	if math.Abs(distance-5.0) > 0.001 {
		t.Errorf("Distance failed: got %.3f, want 5.0", distance)
	}
}

func TestVector2Equals(t *testing.T) {
	v1 := Vector2{X: 1.0, Y: 2.0}
	v2 := Vector2{X: 1.0001, Y: 2.0001}

	if !v1.Equals(v2, 0.001) {
		t.Error("Equals failed: should be equal with epsilon 0.001")
	}

	if v1.Equals(v2, 0.00001) {
		t.Error("Equals failed: should not be equal with epsilon 0.00001")
	}
}

func TestLerp(t *testing.T) {
	a := Vector2{X: 0, Y: 0}
	b := Vector2{X: 10, Y: 10}

	// 中间点
	mid := Lerp(a, b, 0.5)
	if math.Abs(mid.X-5.0) > 0.001 || math.Abs(mid.Y-5.0) > 0.001 {
		t.Errorf("Lerp failed: got (%.1f, %.1f), want (5, 5)", mid.X, mid.Y)
	}

	// 起点
	start := Lerp(a, b, 0)
	if !start.Equals(a, 0.001) {
		t.Errorf("Lerp at 0 failed: got (%.1f, %.1f), want (0, 0)", start.X, start.Y)
	}

	// 终点
	end := Lerp(a, b, 1)
	if !end.Equals(b, 0.001) {
		t.Errorf("Lerp at 1 failed: got (%.1f, %.1f), want (10, 10)", end.X, end.Y)
	}
}
