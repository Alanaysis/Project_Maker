package game

import "math"

// Vector2 表示 2D 向量，用于位置、速度等
type Vector2 struct {
	X float64
	Y float64
}

// NewVector2 创建新的 2D 向量
func NewVector2(x, y float64) Vector2 {
	return Vector2{X: x, Y: y}
}

// Add 向量加法
func (v Vector2) Add(other Vector2) Vector2 {
	return Vector2{
		X: v.X + other.X,
		Y: v.Y + other.Y,
	}
}

// Sub 向量减法
func (v Vector2) Sub(other Vector2) Vector2 {
	return Vector2{
		X: v.X - other.X,
		Y: v.Y - other.Y,
	}
}

// Scale 标量乘法
func (v Vector2) Scale(scalar float64) Vector2 {
	return Vector2{
		X: v.X * scalar,
		Y: v.Y * scalar,
	}
}

// Length 向量长度
func (v Vector2) Length() float64 {
	return math.Sqrt(v.X*v.X + v.Y*v.Y)
}

// Normalize 归一化向量
func (v Vector2) Normalize() Vector2 {
	length := v.Length()
	if length == 0 {
		return Vector2{}
	}
	return Vector2{
		X: v.X / length,
		Y: v.Y / length,
	}
}

// Distance 计算两点距离
func (v Vector2) Distance(other Vector2) float64 {
	return v.Sub(other).Length()
}

// Equals 比较两个向量是否近似相等
func (v Vector2) Equals(other Vector2, epsilon float64) bool {
	return math.Abs(v.X-other.X) < epsilon &&
		math.Abs(v.Y-other.Y) < epsilon
}

// Lerp 线性插值
func Lerp(a, b Vector2, t float64) Vector2 {
	return Vector2{
		X: a.X + (b.X-a.X)*t,
		Y: a.Y + (b.Y-a.Y)*t,
	}
}
