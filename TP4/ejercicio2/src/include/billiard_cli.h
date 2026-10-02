#pragma once

#include <cstdio>
#include <string>

#include "billiard.h"

struct BilliardOptions {
    BilliardParams params;
    std::string framesPath = "data/billiard/frames.txt";
    std::string conversionsPath = "data/billiard/conversions.txt";
    std::string summaryPath;
    bool trajectory = true;
    bool help = false;
};

// Lanza std::invalid_argument ante cualquier valor invalido, antes de tocar archivos.
BilliardOptions parseBilliardOptions(int argc, char** argv);
void printBilliardUsage(std::FILE* out);

// Campos de parametros compartidos por los encabezados y la linea de resumen
// (sin '#' inicial, cada real en %.17g).
void writeParamFields(std::FILE* out, const BilliardParams&, const std::string& initMethod);
void writeSummaryLine(std::FILE* out, const BilliardParams&, const std::string& initMethod,
                      const SimulationResult&);

// Genera el estado inicial, corre la simulacion, escribe frames/conversiones y
// la linea de resumen en summaryOut (y en --summary si se pidio).
SimulationResult runBilliard(const BilliardOptions&, std::FILE* summaryOut);
