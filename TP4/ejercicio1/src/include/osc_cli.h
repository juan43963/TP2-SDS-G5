#pragma once

#include <cstdio>
#include <string>

#include "oscillator.h"

struct OscOptions {
    Method method = Method::EulerPC;
    double dt = 0.0;
    double tf = 5.0;
    std::string outPath;
    bool help = false;
    bool methodGiven = false;
    bool dtGiven = false;
};

OscOptions parseOscOptions(int argc, char** argv);
void printOscUsage(std::FILE* out);
void writeOscHeader(std::FILE* out, Method method, const OscParams& params, double dt,
                    long long steps);
void writeOscRow(std::FILE* out, double t, double r, double v);

// Devuelve la cantidad de filas de datos escritas (N+1).
long long runOscillator(const OscOptions& options, std::FILE* out);
