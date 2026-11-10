#pragma once

#include <functional>
#include <vector>

#include "sfm.h"

using FrameSink = std::function<void(double time, const std::vector<Agent>&)>;

// Corre la evacuacion TSDMD hasta que no queden agentes o se alcance maxTime.
// El sink recibe un frame en t = 0, cada dt2 y uno final.
EvacuationResult runEvacuation(const EvacuationConfig& config, std::vector<Agent> agents,
                               const FrameSink& sink);
