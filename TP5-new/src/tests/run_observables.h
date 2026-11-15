#pragma once

// Observables de una corrida calculados FUERA del motor (post-proceso del lado de los tests),
// a partir del registro crudo de cruces y retiros que devuelve el motor. El motor no calcula
// t_evac, agentes en sala ni si la evacuacion se completo.
#include <algorithm>
#include <cmath>

#include "sfm.h"

struct ObservedRun : EvacuationResult {
    double evacuationTime = -1.0;  // ultimo cruce de la linea de la puerta
    double clearTime = -1.0;       // ultimo retiro
    int crossed = 0;
    int removed = 0;
    int inRoomFinal = 0;
    int wallBreaches = 0;  // cruces fuera del hueco de la puerta
    bool completed = false;
};

inline ObservedRun observe(const EvacuationResult& r, const EvacuationConfig& config, int agentCount) {
    ObservedRun o;
    static_cast<EvacuationResult&>(o) = r;
    const double doorX = config.side / 2.0;
    for (const ExitRecord& e : r.doorCrossings) {
        ++o.crossed;
        o.evacuationTime = std::max(o.evacuationTime, e.time);
        if (std::abs(e.x - doorX) > config.doorWidth / 2.0) ++o.wallBreaches;
    }
    for (const ExitRecord& e : r.removals) {
        ++o.removed;
        o.clearTime = std::max(o.clearTime, e.time);
    }
    o.inRoomFinal = agentCount - o.crossed;
    o.completed = o.removed == agentCount;
    return o;
}
