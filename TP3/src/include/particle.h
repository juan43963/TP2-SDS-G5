#pragma once

#include <cstdint>

#include "vector2.h"

enum class ParticleState { Fresh, Used };

struct Particle {
    int id = -1;
    Vector2 position;
    Vector2 velocity;
    double radius = 0.0;
    double mass = 0.0;
    ParticleState state = ParticleState::Fresh;
    std::uint64_t collisionCount = 0;
};
