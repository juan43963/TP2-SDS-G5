#pragma once

#include <string>
#include <vector>

#include "neighbor_method.h"
#include "particle.h"

void writeStatic(const std::string& path, const std::vector<Particle>& particles, double L);

void writeDynamic(const std::string& path, const std::vector<Particle>& particles, double t0 = 0.0);

void writeNeighbors(const std::string& path, const NeighborList& neighbors);

std::vector<Particle> readSystem(const std::string& staticPath, const std::string& dynamicPath,
                                 double& L);
