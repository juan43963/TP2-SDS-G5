#pragma once

#include <algorithm>

#include "vector2.h"

inline constexpr double kGeometryEpsilon = 1e-12;

inline double distanceSquared(Vector2 a, Vector2 b) { return normSquared(a - b); }

inline bool circlesOverlap(Vector2 centerA, double radiusA, Vector2 centerB, double radiusB) {
    const double reach = radiusA + radiusB;
    const double scale = std::max(1.0, reach * reach);
    return distanceSquared(centerA, centerB) < reach * reach - kGeometryEpsilon * scale;
}
