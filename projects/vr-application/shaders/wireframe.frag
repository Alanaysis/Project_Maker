#version 450 core

// 输出颜色
out vec4 FragColor;

// Uniform 变量
uniform vec4 lineColor;

void main()
{
    FragColor = lineColor;
}