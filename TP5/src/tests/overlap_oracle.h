#pragma once

// Oraculo de superposicion O(n^2) para los tests de TP5 (D-11). Se compila solo en
// tp5_test (y en el chequeo de archivos de trayectoria): nunca en el motor.
// Es deliberadamente independiente del motor: no incluye ningun encabezado de
// src/include/ y deriva la geometria de la sala solo de `side` y `doorWidth`, asi
// un error de geometria del contacto de forces.cpp no puede ocultarse a si mismo.
#include <string>
#include <vector>

// En el modelo granular de D-01 los solapes pequenos y elasticos son legitimos
// (p. ej. 0.039 m en un choque a 1.5 m/s). Una violacion es una profundidad mayor
// que esta fraccion del menor radio involucrado en una muestra de frame.
inline constexpr double kSustainedOverlapFraction = 0.5;

struct OracleRow {
    int id = 0;
    double x = 0.0;
    double y = 0.0;
    double r = 0.0;
};

struct OracleRoom {
    double side = 50.0;
    double doorWidth = 0.8;
    double exitDistance = 1.0;
};

struct OverlapReport {
    int violations = 0;
    int agentPairViolations = 0;
    int wallViolations = 0;
    int escapeViolations = 0;
    double maxAgentDepth = 0.0;
    double maxWallDepth = 0.0;
    std::string firstViolation;
};

// Revisa un frame: pares agente-agente, agente-segmento de pared (los extremos de
// los tramos inferiores son los bordes de la puerta) y agentes que escaparon de la
// sala por un lugar que no es la puerta.
OverlapReport checkOverlaps(const std::vector<OracleRow>& rows, const OracleRoom& room,
                            double depthFraction = kSustainedOverlapFraction);

// Suma contadores, toma maximos y conserva la primera descripcion.
void mergeReports(OverlapReport& total, const OverlapReport& frame);
