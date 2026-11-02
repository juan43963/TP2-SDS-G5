#pragma once

#include <cstddef>
#include <vector>

#include "sfm.h"

struct ForceWorkspace {
    int M = 1;
    double cellSize = 1.0;
    std::vector<int> head;
    std::vector<int> next;
    std::vector<Vector2> savedAcceleration;
    std::vector<Vector2> savedVelocity;
    // Fase 8: si trackContacts, computeAccelerations deja en `touching` (un byte por agente del
    // vector) 1 para todo agente con solape contra otro agente, una pared o una esquina. No cambia
    // ninguna cuenta de la numerica; con false (por defecto) el codigo hace exactamente lo de antes.
    bool trackContacts = false;
    std::vector<unsigned char> touching;
};

struct ContactStats {
    double maxAgentOverlap = 0.0;
    double maxWallOverlap = 0.0;
};

// M = max(1, floor(side / maxContactDistance)); cellSize = side / M >= maxContactDistance.
ForceWorkspace makeForceWorkspace(double side, double maxContactDistance, std::size_t capacity);

// Escribe `acceleration` de cada agente: fuerza de deseo + contacto granular con
// otros agentes, paredes y bordes de puerta.
void computeAccelerations(const SfmParams& params, const WallSet& walls,
                          std::vector<Agent>& agents, ForceWorkspace& workspace,
                          ContactStats& stats);

// Un paso de Velocity Verlet (D-02). Entrada: `acceleration` = a(t).
void stepTsdmd(const SfmParams& params, const WallSet& walls, std::vector<Agent>& agents,
               ForceWorkspace& workspace, double dt, ContactStats& stats);
