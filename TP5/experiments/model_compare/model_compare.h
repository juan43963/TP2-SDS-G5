#pragma once

// Experimento fuera de la allowlist del motor entregable.
#include "evacuation.h"
#include "forces.h"

namespace model_compare {

enum class Model { Sfm, Cpm };

struct CpmParams {
    double radiusMin = 0.10;
    double radiusMax = 0.25;
    double recoveryTime = 0.5;
    double beta = 0.9;
    double desiredSpeed = 1.5;
    double escapeSpeed = 1.5;
    // Baglietto y Parisi (2011), ec. (2). No es un parametro numerico libre.
    double timeStep() const;
};

struct Config {
    Model model = Model::Sfm;
    EvacuationConfig scenario;
    CpmParams cpm;
    Config() { scenario.dt2 = 0.5; }
};

struct Diagnostics {
    long long pairContacts = 0;
    long long wallContacts = 0;
    long long zeroEscapeDirections = 0;
    ContactStats overlaps;
};

struct Workspace {
    ForceWorkspace grid;
    std::vector<Vector2> escape;
    std::vector<unsigned char> touching;
};

void validate(const Config& config);
void validateState(const std::vector<Agent>& agents);
std::vector<Agent> initialState(const Config& config);
Workspace makeWorkspace(double side, const CpmParams& params, std::size_t capacity);
// Contactos evaluados en el mismo estado anterior, antes de modificar radios o posiciones.
void stepCpm(const CpmParams& params, const WallSet& walls, std::vector<Agent>& agents,
             Workspace& workspace, Diagnostics& diagnostics);
// Reglas de cruce/retiro equivalentes a runEvacuation; retorna agentes retirados.
void updateExits(const Room& room, double time, std::vector<Agent>& agents,
                 EvacuationResult& result);
EvacuationResult runCpm(const Config& config, std::vector<Agent> agents,
                        Diagnostics& diagnostics, const FrameSink& sink);

}  // namespace model_compare
