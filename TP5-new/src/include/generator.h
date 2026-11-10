#pragma once

#include <vector>

#include "sfm.h"

// Rejection sampling sin solapes; mismo seed produce la misma configuracion.
std::vector<Agent> generateAgents(const EvacuationConfig& config);
