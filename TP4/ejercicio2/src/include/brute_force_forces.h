#pragma once

#include <vector>

#include "billiard.h"

// Referencia independiente de computeForces para tp4_test: nunca forma parte del binario billiard.
struct ContactCounts {
    int pairs = 0;
    int wall = 0;
    int obstacle = 0;
};

ContactCounts bruteForceForces(const BilliardParams&, const std::vector<Vec2>& pos,
                               std::vector<Vec2>& force, std::vector<int>& touchingObstacle);
