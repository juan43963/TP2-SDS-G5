#pragma once

#include <cstdint>
#include <limits>

enum class EventType {
    ParticleParticle,
    VerticalWall,
    HorizontalWall,
    Corner,
    ParticleObstacle,
};

struct Event {
    double time = std::numeric_limits<double>::infinity();
    EventType type = EventType::ParticleParticle;
    int particleA = -1;
    int particleB = -1;
    int obstacle = -1;
    std::uint64_t collisionCountA = 0;
    std::uint64_t collisionCountB = 0;
    std::uint64_t sequence = 0;
};

// std::priority_queue coloca primero el elemento considerado "mayor". Este
// comparador invierte tiempo y secuencia para obtener un min-heap determinista.
struct EventLater {
    bool operator()(const Event& lhs, const Event& rhs) const {
        if (lhs.time != rhs.time) return lhs.time > rhs.time;
        return lhs.sequence > rhs.sequence;
    }
};
