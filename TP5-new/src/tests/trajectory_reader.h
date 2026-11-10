#pragma once

// Lector independiente del formato TP5_TRAJECTORY 1 (D-12). Solo para tests y para el
// chequeo de archivos del Plan 04: no incluye ningun encabezado del motor, de modo que
// demuestra que la salida se entiende sin ejecutar el simulador.
#include <cstdint>
#include <string>
#include <vector>

struct TrajectoryHeader {
    std::string scheme;
    int agentCount = 0;
    double side = 0.0;
    double doorWidth = 0.0;
    double doorX = 0.0;
    double exitDistance = 0.0;
    std::uint64_t seed = 0;
    double dt = 0.0;
    double dt2 = 0.0;
    double desiredSpeed = 0.0;
    double tau = 0.0;
    double mass = 0.0;
    double stiffness = 0.0;
    double friction = 0.0;
    double radiusMin = 0.0;
    double radiusMax = 0.0;
};

struct TrajectoryRow {
    int id = 0;
    double x = 0.0;
    double y = 0.0;
    double vx = 0.0;
    double vy = 0.0;
    double r = 0.0;
    int scheme = 0;
};

struct TrajectoryFrame {
    double time = 0.0;
    std::vector<TrajectoryRow> rows;
};

struct Trajectory {
    TrajectoryHeader header;
    std::vector<TrajectoryFrame> frames;
    bool complete = false;  // verdadero solo si se leyo la linea END
};

// Lanza std::runtime_error con el numero de linea ante un archivo malformado. Un
// archivo sin END no es error: devuelve complete == false con los frames leidos.
Trajectory readTrajectory(const std::string& path);

// Filas con y >= 0: agentes aun dentro de la sala (el motor cuenta el cruce con y < 0).
int roomPopulation(const TrajectoryFrame& frame);
