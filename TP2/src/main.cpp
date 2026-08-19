#include <cmath>
#include <cstdio>
#include <exception>
#include <getopt.h>
#include <string>
#include <vector>

#include "engine/simulation.h"
#include "generator.h"
#include "grid.h"

namespace {

struct Options {
    double rho = 4.0;
    int N = 0;       // 0 means: derive from rho (N = round(rho * L * L))
    double L = 10.0;
    double rc = 1.0;
    int M = 0;       // 0 means: derive via maxValidGridM(L, rc)
    int steps = 100;
    unsigned long long seed = 42;  // explicit constant, never time-seeded
    double v0 = 0.03;
    double dt = 1.0;
    bool periodic = true;
};

void usage() {
    std::printf(
        "TP2 - Motor de Vicsek/Votante - Simulacion de Sistemas\n\n"
        "Uso:\n  ./tp2 [opciones]\n\n"
        "Sistema:\n"
        "  --rho <real>     densidad, N = round(rho*L*L) si --N no se da  (default 4)\n"
        "  --N <int>        cantidad de particulas                       (default: derivado de rho)\n"
        "  --L <real>       lado del area cuadrada                       (default 10)\n"
        "  --rc <real>      radio de interaccion                         (default 1)\n"
        "  --seed <int>     semilla del generador                        (default 42)\n\n"
        "Motor:\n"
        "  --M <int>        celdas por lado de la grilla                 (default: M_max(L,rc))\n"
        "  --steps <int>    cantidad de pasos a integrar                 (default 100)\n"
        "  --v0 <real>      rapidez de cada particula                    (default 0.03)\n"
        "  --dt <real>      paso temporal de integracion                 (default 1.0)\n"
        "  --periodic       contorno periodico                          (default)\n"
        "  --no-periodic    contorno con paredes\n"
        "  -h, --help       esta ayuda\n");
}

[[noreturn]] void fail(const std::string& message) {
    std::fprintf(stderr, "error: %s\n", message.c_str());
    std::exit(1);
}

Options parseArgs(int argc, char** argv) {
    Options o;
    static struct option long_options[] = {
        {"rho", required_argument, nullptr, 'r'},
        {"N", required_argument, nullptr, 'N'},
        {"L", required_argument, nullptr, 'L'},
        {"rc", required_argument, nullptr, 'c'},
        {"M", required_argument, nullptr, 'M'},
        {"steps", required_argument, nullptr, 's'},
        {"seed", required_argument, nullptr, 'S'},
        {"v0", required_argument, nullptr, 'v'},
        {"dt", required_argument, nullptr, 'd'},
        {"periodic", no_argument, nullptr, 'p'},
        {"no-periodic", no_argument, nullptr, 'q'},
        {"help", no_argument, nullptr, 'h'},
        {nullptr, 0, nullptr, 0}
    };

    int opt;
    while ((opt = getopt_long(argc, argv, "h", long_options, nullptr)) != -1) {
        switch (opt) {
            case 'r': o.rho = std::stod(optarg); break;
            case 'N': o.N = std::stoi(optarg); break;
            case 'L': o.L = std::stod(optarg); break;
            case 'c': o.rc = std::stod(optarg); break;
            case 'M': o.M = std::stoi(optarg); break;
            case 's': o.steps = std::stoi(optarg); break;
            case 'S': o.seed = std::stoull(optarg); break;
            case 'v': o.v0 = std::stod(optarg); break;
            case 'd': o.dt = std::stod(optarg); break;
            case 'p': o.periodic = true; break;
            case 'q': o.periodic = false; break;
            case 'h': usage(); std::exit(0);
            default: fail("opcion invalida (probar --help)");
        }
    }

    if (o.steps < 0) fail("--steps debe ser >= 0");
    return o;
}

}  // namespace

int main(int argc, char** argv) try {
    Options o = parseArgs(argc, argv);

    if (o.N == 0) {
        o.N = static_cast<int>(std::round(o.rho * o.L * o.L));
    }
    if (o.M == 0) {
        o.M = maxValidGridM(o.L, o.rc);
    }

    std::vector<VicsekParticle> particles = generateVicsekParticles(o.N, o.L, o.seed);

    Simulation sim(std::move(particles), o.L, o.rc, o.v0, o.dt, o.M, o.periodic);

    for (int step = 0; step < o.steps; ++step) {
        sim.step();
    }

    std::printf("TP2 motor: N=%d L=%.2f rc=%.2f M=%d steps=%d seed=%llu -- OK\n", o.N, o.L, o.rc,
                o.M, o.steps, o.seed);

    return 0;
} catch (const std::exception& e) {
    std::fprintf(stderr, "error: %s\n", e.what());
    return 1;
}
