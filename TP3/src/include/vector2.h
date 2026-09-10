#pragma once

struct Vector2 {
    double x = 0.0;
    double y = 0.0;
};

inline Vector2 operator+(Vector2 a, Vector2 b) { return {a.x + b.x, a.y + b.y}; }
inline Vector2 operator-(Vector2 a, Vector2 b) { return {a.x - b.x, a.y - b.y}; }
inline Vector2 operator*(Vector2 v, double scalar) { return {v.x * scalar, v.y * scalar}; }
inline Vector2 operator*(double scalar, Vector2 v) { return v * scalar; }

inline double dot(Vector2 a, Vector2 b) { return a.x * b.x + a.y * b.y; }
inline double normSquared(Vector2 v) { return dot(v, v); }
