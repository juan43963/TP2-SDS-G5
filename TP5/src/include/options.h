#pragma once

#include <string>

#include "sfm.h"

struct ProgramOptions {
    EvacuationConfig config;
    std::string outputPath = "data/trajectory.txt";
    bool writeOutput = true;
    bool csv = false;
    bool help = false;
};

void printUsage();

// Lanza std::invalid_argument ante opciones invalidas; valida la configuracion
// salvo con --help.
ProgramOptions parseOptions(int argc, char** argv);
