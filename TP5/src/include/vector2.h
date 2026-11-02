#pragma once

// Adaptado de TP3/src/include/vector2.h (D-09).
#include <cmath>

struct Vector2 {
    double x = 0.0;
    double y = 0.0;
};

inline Vector2 operator+(Vector2 a, Vector2 b) { return {a.x + b.x, a.y + b.y}; }
inline Vector2 operator-(Vector2 a, Vector2 b) { return {a.x - b.x, a.y - b.y}; }
inline Vector2 operator-(Vector2 v) { return {-v.x, -v.y}; }
inline Vector2 operator*(Vector2 v, double scalar) { return {v.x * scalar, v.y * scalar}; }
inline Vector2 operator*(double scalar, Vector2 v) { return v * scalar; }

inline Vector2& operator+=(Vector2& a, Vector2 b) {
    a.x += b.x;
    a.y += b.y;
    return a;
}
inline Vector2& operator-=(Vector2& a, Vector2 b) {
    a.x -= b.x;
    a.y -= b.y;
    return a;
}

inline double dot(Vector2 a, Vector2 b) { return a.x * b.x + a.y * b.y; }
inline double cross(Vector2 a, Vector2 b) { return a.x * b.y - a.y * b.x; }
inline double normSquared(Vector2 v) { return dot(v, v); }
inline double norm(Vector2 v) { return std::sqrt(dot(v, v)); }
