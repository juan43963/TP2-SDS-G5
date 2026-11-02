// Helpers de parseo y getopt_long adaptados de TP3/src/utils/options.cpp (D-09).
#include "options.h"

#include <cerrno>
#include <cmath>
#include <cstdint>
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

int parseInt(const char* text, const char* flag) {
    if (text == nullptr || *text == '\0') throw std::invalid_argument(std::string(flag) + ": falta valor");
    char* end = nullptr;
    errno = 0;
    const long long value = std::strtoll(text, &end, 10);
    if (errno != 0 || end == text || *end != '\0') {
        throw std::invalid_argument(std::string(flag) + ": valor entero invalido '" + text + "'");
    }
    if (value < std::numeric_limits<int>::min() || value > std::numeric_limits<int>::max()) {
        throw std::invalid_argument(std::string(flag) + ": valor fuera del rango de int");
    }
    return static_cast<int>(value);
}

long long parseLongLong(const char* text, const char* flag) {
    if (text == nullptr || *text == '\0') throw std::invalid_argument(std::string(flag) + ": falta valor");
    char* end = nullptr;
    errno = 0;
    const long long value = std::strtoll(text, &end, 10);
    if (errno != 0 || end == text || *end != '\0') {
        throw std::invalid_argument(std::string(flag) + ": valor entero invalido '" + text + "'");
    }
    return value;
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

Scheme parseScheme(const char* text) {
    const std::string name = text == nullptr ? "" : text;
    if (name == "tsdmd") return Scheme::Tsdmd;
    if (name == "edmd") return Scheme::Edmd;
    if (name == "hybrid") return Scheme::Hybrid;
    throw std::invalid_argument("--scheme: esquema desconocido '" + name +
                                "' (opciones: tsdmd, edmd, hybrid)");
}

}  // namespace

void printUsage() {
    std::printf(
        "TP5 - Evacuacion de una sala con puerta (SFM; esquemas TSDMD, EDMD e hibrido)\n\n"
        "Uso:\n  ./tp5 [opciones]\n\n"
        "Sistema:\n"
        "  --N <int>                      agentes, 1..100000 (500)\n"
        "  --L <m>                        lado de la sala cuadrada (50)\n"
        "  --door <m>                     ancho de la puerta, centrada en y=0 (0.8)\n"
        "  --rmin <m>                     radio minimo de agente (0.18)\n"
        "  --rmax <m>                     radio maximo de agente (0.25)\n"
        "  --exit-distance <m>            distancia de la puerta a la que se retira el agente (1.0)\n"
        "  --seed <int>                   semilla reproducible (1)\n"
        "  --max-placement-attempts <int> intentos por agente del generador (100000)\n\n"
        "Modelo SFM:\n"
        "  --vd <m/s>                     velocidad deseada (1.5)\n"
        "  --k <kg/s^2>                   rigidez del contacto (1.2e5)\n"
        "  --kappa <kg/(m s)>             friccion tangencial (2.4e5)\n"
        "  --mass <kg>                    masa del agente (80)\n"
        "  --tau <s>                      tiempo de relajacion (0.5)\n\n"
        "EDMD (solo --scheme edmd):\n"
        "  --restitution <e>              coeficiente de restitucion de las colisiones, [0,1] (0.5)\n"
        "  --event-gap <s>                piso de tiempo entre colisiones de un agente, [1e-6,0.1] (5e-3)\n"
        "  --steer-dt <s>                 periodo de re-apuntado de la direccion de deseo, [1e-3,10] (0.1)\n"
        "  --overlap-cap <m>              solape en cadena tolerado antes de proyectar, [0,0.08] (0.07)\n"
        "  --max-events <int>             tope de eventos procesados (1e9)\n\n"
        "Hibrido (solo --scheme hybrid):\n"
        "  --hybrid-T <s>                 umbral T: un agente pasa a TSDMD si su tiempo al proximo\n"
        "                                 contacto es < T; 0 o >= 2*dt (0.5). T = 0: EDMD puro;\n"
        "                                 T >= tmax: TSDMD puro\n"
        "  --hybrid-alpha <a>             histeresis: vuelve a EDMD si ese tiempo es > a*T, a >= 1 (2)\n\n"
        "Integracion:\n"
        "  --scheme <tsdmd|edmd|hybrid>   esquema (tsdmd)\n"
        "  --dt <s>                       paso de integracion, <= 0.1*sqrt(m/k) (1e-4)\n"
        "  --dt2 <s>                      intervalo de salida, multiplo entero de dt (0.1)\n"
        "  --tmax <s>                     tiempo fisico maximo (3000)\n\n"
        "Salida:\n"
        "  --out <path>                   archivo de trayectoria TP5_TRAJECTORY (data/trajectory.txt)\n"
        "  --no-output                    no escribir el archivo de trayectoria\n"
        "  --csv                          una linea CSV sin cabecera en lugar de RESULT, columnas:\n"
        "                                 scheme,N,seed,dt,dt2,steps,t_final,t_evac,t_clear,crossed,\n"
        "                                 removed,in_room_final,wall_breaches,max_agent_overlap,\n"
        "                                 max_wall_overlap,simulation_ms,output_ms,completed,events,\n"
        "                                 stale,collisions,floor_collisions,time_regressions,\n"
        "                                 promotions,returns,hybrid_steps,tsdmd_agent_steps,\n"
        "                                 mixed_promotions,quick_repromotions\n"
        "  -h, --help                     mostrar esta ayuda\n");
}

ProgramOptions parseOptions(int argc, char** argv) {
    ProgramOptions options;
    EvacuationConfig& c = options.config;
    enum LongOnly {
        kDoor = 1000, kRmin, kRmax, kVd, kK, kKappa, kMass, kTau, kExitDistance,
        kMaxPlacement, kScheme, kDt, kDt2, kNoOutput, kCsv,
        kRestitution, kEventGap, kSteerDt, kMaxEvents, kOverlapCap, kHybridT, kHybridAlpha
    };
    static option longOptions[] = {
        {"N", required_argument, nullptr, 'N'},
        {"L", required_argument, nullptr, 'L'},
        {"door", required_argument, nullptr, kDoor},
        {"seed", required_argument, nullptr, 's'},
        {"dt", required_argument, nullptr, kDt},
        {"dt2", required_argument, nullptr, kDt2},
        {"tmax", required_argument, nullptr, 't'},
        {"rmin", required_argument, nullptr, kRmin},
        {"rmax", required_argument, nullptr, kRmax},
        {"vd", required_argument, nullptr, kVd},
        {"k", required_argument, nullptr, kK},
        {"kappa", required_argument, nullptr, kKappa},
        {"mass", required_argument, nullptr, kMass},
        {"tau", required_argument, nullptr, kTau},
        {"exit-distance", required_argument, nullptr, kExitDistance},
        {"max-placement-attempts", required_argument, nullptr, kMaxPlacement},
        {"scheme", required_argument, nullptr, kScheme},
        {"restitution", required_argument, nullptr, kRestitution},
        {"event-gap", required_argument, nullptr, kEventGap},
        {"steer-dt", required_argument, nullptr, kSteerDt},
        {"max-events", required_argument, nullptr, kMaxEvents},
        {"overlap-cap", required_argument, nullptr, kOverlapCap},
        {"hybrid-T", required_argument, nullptr, kHybridT},
        {"hybrid-alpha", required_argument, nullptr, kHybridAlpha},
        {"out", required_argument, nullptr, 'o'},
        {"no-output", no_argument, nullptr, kNoOutput},
        {"csv", no_argument, nullptr, kCsv},
        {"help", no_argument, nullptr, 'h'},
        {nullptr, 0, nullptr, 0},
    };

    // getopt mantiene estado global; reiniciarlo permite llamar varias veces.
    optind = 1;
    opterr = 0;
    int parsed;
    while ((parsed = getopt_long(argc, argv, "h", longOptions, nullptr)) != -1) {
        switch (parsed) {
            case 'N': c.agentCount = parseInt(optarg, "--N"); break;
            case 'L': c.side = parseDouble(optarg, "--L"); break;
            case kDoor: c.doorWidth = parseDouble(optarg, "--door"); break;
            case 's': c.seed = parseUnsigned(optarg, "--seed"); break;
            case kDt: c.dt = parseDouble(optarg, "--dt"); break;
            case kDt2: c.dt2 = parseDouble(optarg, "--dt2"); break;
            case 't': c.maxTime = parseDouble(optarg, "--tmax"); break;
            case kRmin: c.radiusMin = parseDouble(optarg, "--rmin"); break;
            case kRmax: c.radiusMax = parseDouble(optarg, "--rmax"); break;
            case kVd: c.sfm.desiredSpeed = parseDouble(optarg, "--vd"); break;
            case kK: c.sfm.stiffness = parseDouble(optarg, "--k"); break;
            case kKappa: c.sfm.friction = parseDouble(optarg, "--kappa"); break;
            case kMass: c.sfm.mass = parseDouble(optarg, "--mass"); break;
            case kTau: c.sfm.tau = parseDouble(optarg, "--tau"); break;
            case kExitDistance: c.exitDistance = parseDouble(optarg, "--exit-distance"); break;
            case kMaxPlacement:
                c.maxPlacementAttemptsPerAgent = parseInt(optarg, "--max-placement-attempts");
                break;
            case kScheme: c.scheme = parseScheme(optarg); break;
            case kRestitution: c.restitution = parseDouble(optarg, "--restitution"); break;
            case kEventGap: c.eventGap = parseDouble(optarg, "--event-gap"); break;
            case kSteerDt: c.steerInterval = parseDouble(optarg, "--steer-dt"); break;
            case kOverlapCap: c.overlapCap = parseDouble(optarg, "--overlap-cap"); break;
            case kMaxEvents: c.maxEvents = parseLongLong(optarg, "--max-events"); break;
            case kHybridT: c.hybridT = parseDouble(optarg, "--hybrid-T"); break;
            case kHybridAlpha: c.hybridAlpha = parseDouble(optarg, "--hybrid-alpha"); break;
            case 'o': options.outputPath = optarg; break;
            case kNoOutput: options.writeOutput = false; break;
            case kCsv: options.csv = true; break;
            case 'h': options.help = true; break;
            case '?':
            default:
                throw std::invalid_argument(
                    std::string("opcion desconocida o sin valor: '") +
                    (optind >= 1 && optind <= argc ? argv[optind - 1] : "?") + "'; usar --help");
        }
    }
    if (optind != argc) {
        throw std::invalid_argument("argumento posicional inesperado '" + std::string(argv[optind]) + "'");
    }
    if (!options.help) {
        if (options.writeOutput && options.outputPath.empty()) {
            throw std::invalid_argument(
                "--out: la ruta no puede ser vacia (usar --no-output para omitir la salida)");
        }
        validateConfig(c);
    }
    return options;
}
