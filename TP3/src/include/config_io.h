#pragma once

#include <string>
#include <vector>

#include "obstacle.h"
#include "simulation_types.h"

void validateObstacleConfiguration(const std::vector<Obstacle>& obstacles,
                                   const SimulationConfig& config);

std::vector<Obstacle> readObstacleConfig(const std::string& path,
                                         const SimulationConfig& config);
