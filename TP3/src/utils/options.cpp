#include "options.h"

#include <cerrno>
#include <cmath>
#include <cstdio>
#include <cstdlib>
#include <getopt.h>
#include <limits>
#include <stdexcept>
#include <string>

namespace {

double parseDouble(const char* text, const char* flag) {
    if (text == nullptr || *text == '\0') throw std::invalid_argument(std::string(flag) + ": falta valor");
    char* end = nullptr;
    errno = 0;
    const double value = std::strtod(text, &end);
    if (errno != 0 || end == text || *end != '\0' || !std::isfinite(value)) {
        throw std::invalid_argument(std::string(flag) + ": valor real invalido '" + text + "'");
    }
    return value;
}

long long parseInteger(const char* text, const char* flag) {
    if (text == nullptr || *text == '\0') throw std::invalid_argument(std::string(flag) + ": falta valor");
    char* end = nullptr;
    errno = 0;
    const long long value = std::strtoll(text, &end, 10);
    if (errno != 0 || end == text || *end != '\0') {
        throw std::invalid_argument(std::string(flag) + ": valor entero invalido '" + text + "'");
    }
    return value;
}

int parseInt(const char* text, const char* flag) {
    const long long value = parseInteger(text, flag);
    if (value < std::numeric_limits<int>::min() || value > std::numeric_limits<int>::max()) {
        throw std::invalid_argument(std::string(flag) + ": valor fuera del rango de int");
    }
    return static_cast<int>(value);
}

std::uint64_t parseUnsigned(const char* text, const char* flag) {
    if (text == nullptr || *text == '\0' || *text == '-') {
        throw std::invalid_argument(std::string(flag) + ": se esperaba un entero no negativo");
    }
    char* end = nullptr;
    errno = 0;
    const unsigned long long value = std::strtoull(text, &end, 10);
    if (errno != 0 || end == text || *end != '\0') {
        throw std::invalid_argument(std::string(flag) + ": valor entero invalido '" + text + "'");
    }
    return static_cast<std::uint64_t>(value);
}

}  // namespace

void printUsage() {
    std::printf(
        "TP3 - Billar-Metegol dirigido por eventos\n\n"
        "Uso:\n  ./tp3 [opciones]\n\n"
        "Sistema (defaults oficiales):\n"
        "  --N <int>                 particulas (100)\n"
        "  --L <m>                   largo de la mesa (1.20)\n"
        "  --W <m>                   ancho de la mesa (0.68)\n"
        "  --goal-size <m>           longitud de cada arco (0.20)\n"
        "  --radius <m>              radio de particula (0.0175)\n"
        "  --mass <kg>               masa de particula (0.025)\n"
        "  --v0 <m/s>                rapidez inicial (1.0)\n"
        "  --tmax <s>                tiempo fisico maximo (100)\n"
        "  --seed <int>              semilla reproducible (42)\n"
        "  --config <path>           obstaculos: una fila 'x y R'\n"
        "  --max-placement-attempts <int> intentos por particula (100000)\n\n"
        "Salida:\n"
        "  --static-output <path>    datos estaticos (data/static.txt)\n"
        "  --trajectory <path>       trayectoria (data/trajectory.txt)\n"
        "  --output-every-events <n> guardar cada n eventos fisicos (10)\n"
        "  --no-trajectory           no escribir salida pesada\n"
        "  --goals-output <path>      serie liviana de goles y Fu\n"
        "  --summary <path>          resumen machine-readable opcional\n"
        "  --csv                     imprimir el resumen como CSV\n"
        "  -h, --help                mostrar esta ayuda\n");
}

void validateOptions(const ProgramOptions& options) {
    const SimulationConfig& c = options.simulation;
    if (c.particleCount <= 0) throw std::invalid_argument("--N debe ser > 0");
    if (c.length <= 0.0) throw std::invalid_argument("--L debe ser > 0");
    if (c.width <= 0.0) throw std::invalid_argument("--W debe ser > 0");
    if (c.goalSize <= 0.0 || c.goalSize > c.width) {
        throw std::invalid_argument("--goal-size debe pertenecer a (0, W]");
    }
    if (c.particleRadius <= 0.0 || 2.0 * c.particleRadius >= c.length ||
        2.0 * c.particleRadius >= c.width) {
        throw std::invalid_argument("--radius debe ser > 0 y su diametro debe entrar en la mesa");
    }
    if (c.particleMass <= 0.0) throw std::invalid_argument("--mass debe ser > 0");
    if (c.initialSpeed <= 0.0) throw std::invalid_argument("--v0 debe ser > 0");
    if (c.maxTime <= 0.0) throw std::invalid_argument("--tmax debe ser > 0");
    if (c.maxPlacementAttemptsPerParticle <= 0) {
        throw std::invalid_argument("--max-placement-attempts debe ser > 0");
    }
    if (options.outputEveryEvents <= 0) {
        throw std::invalid_argument("--output-every-events debe ser > 0");
    }
    if (options.trajectoryEnabled) {
        if (options.staticOutputPath.empty() || options.trajectoryPath.empty()) {
            throw std::invalid_argument("las rutas de salida no pueden estar vacias");
        }
        if (options.staticOutputPath == options.trajectoryPath) {
            throw std::invalid_argument("--static-output y --trajectory deben ser distintos");
        }
    }
    if (options.trajectoryEnabled && !options.summaryPath.empty() &&
        (options.summaryPath == options.staticOutputPath || options.summaryPath == options.trajectoryPath)) {
        throw std::invalid_argument("--summary debe usar una ruta distinta de las otras salidas");
    }
    if (!options.goalsOutputPath.empty()) {
        if ((!options.summaryPath.empty() && options.goalsOutputPath == options.summaryPath) ||
            (options.trajectoryEnabled &&
             (options.goalsOutputPath == options.staticOutputPath ||
              options.goalsOutputPath == options.trajectoryPath))) {
            throw std::invalid_argument("--goals-output debe usar una ruta distinta de las otras salidas");
        }
    }
}

ProgramOptions parseOptions(int argc, char** argv) {
    ProgramOptions options;
    static option longOptions[] = {
        {"N", required_argument, nullptr, 'N'},
        {"L", required_argument, nullptr, 'L'},
        {"W", required_argument, nullptr, 'W'},
        {"goal-size", required_argument, nullptr, 'g'},
        {"radius", required_argument, nullptr, 'r'},
        {"mass", required_argument, nullptr, 'm'},
        {"v0", required_argument, nullptr, 'v'},
        {"tmax", required_argument, nullptr, 't'},
        {"seed", required_argument, nullptr, 's'},
        {"config", required_argument, nullptr, 'c'},
        {"max-placement-attempts", required_argument, nullptr, 'a'},
        {"static-output", required_argument, nullptr, 'S'},
        {"trajectory", required_argument, nullptr, 'T'},
        {"output-every-events", required_argument, nullptr, 'e'},
        {"no-trajectory", no_argument, nullptr, 'q'},
        {"goals-output", required_argument, nullptr, 'G'},
        {"summary", required_argument, nullptr, 'o'},
        {"csv", no_argument, nullptr, 'C'},
        {"help", no_argument, nullptr, 'h'},
        {nullptr, 0, nullptr, 0},
    };

    // getopt mantiene estado global; reiniciarlo permite probar parseOptions
    // varias veces dentro del mismo proceso.
    optind = 1;
    opterr = 0;
    int parsed;
    while ((parsed = getopt_long(argc, argv, "h", longOptions, nullptr)) != -1) {
        switch (parsed) {
            case 'N': options.simulation.particleCount = parseInt(optarg, "--N"); break;
            case 'L': options.simulation.length = parseDouble(optarg, "--L"); break;
            case 'W': options.simulation.width = parseDouble(optarg, "--W"); break;
            case 'g': options.simulation.goalSize = parseDouble(optarg, "--goal-size"); break;
            case 'r': options.simulation.particleRadius = parseDouble(optarg, "--radius"); break;
            case 'm': options.simulation.particleMass = parseDouble(optarg, "--mass"); break;
            case 'v': options.simulation.initialSpeed = parseDouble(optarg, "--v0"); break;
            case 't': options.simulation.maxTime = parseDouble(optarg, "--tmax"); break;
            case 's': options.simulation.seed = parseUnsigned(optarg, "--seed"); break;
            case 'c': options.obstacleConfigPath = optarg; break;
            case 'a': options.simulation.maxPlacementAttemptsPerParticle =
                          parseInt(optarg, "--max-placement-attempts"); break;
            case 'S': options.staticOutputPath = optarg; break;
            case 'T': options.trajectoryPath = optarg; break;
            case 'e': options.outputEveryEvents = parseInt(optarg, "--output-every-events"); break;
            case 'q': options.trajectoryEnabled = false; break;
            case 'G': options.goalsOutputPath = optarg; break;
            case 'o': options.summaryPath = optarg; break;
            case 'C': options.csv = true; break;
            case 'h': options.help = true; break;
            case '?':
            default:
                throw std::invalid_argument("opcion invalida o argumento faltante; usar --help");
        }
    }
    if (optind != argc) {
        throw std::invalid_argument("argumento posicional inesperado '" + std::string(argv[optind]) + "'");
    }
    if (!options.help) validateOptions(options);
    return options;
}
