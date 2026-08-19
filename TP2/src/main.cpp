#include <cmath>
#include <cstdio>
#include <exception>
#include <filesystem>
#include <fstream>
#include <getopt.h>
#include <string>
#include <vector>

#include "engine/simulation.h"
#include "generator.h"
#include "grid.h"
#include "io.h"
#include "observables.h"

namespace {

struct Options {
    double rho = 4.0;
    int N = -1;      // -1 means: derive from rho (N = round(rho * L * L))
    double L = 10.0;
    double rc = 1.0;
    int M = -1;      // -1 means: derive via maxValidGridM(L, rc)
    int steps = 100;
    unsigned long long seed = 42;  // explicit constant, never time-seeded
    double v0 = 0.03;
    double dt = 1.0;
    bool periodic = true;
    std::string model = "vicsek";
    double eta = 0.0;
    std::string out = "data/dynamic.txt";
    std::string scalarLog;  // empty = disabled (default)
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
        "  --model <str>    regla de interaccion: vicsek|voter          (default vicsek)\n"
        "  --eta <real>     amplitud del ruido angular                  (default 0.0)\n"
        "  --out <path>     archivo de trayectoria de salida            (default data/dynamic.txt)\n"
        "  --scalar-log <path>  log escalar opcional '(t va S)' por paso   (default: deshabilitado)\n"
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
        {"model", required_argument, nullptr, 'm'},
        {"eta", required_argument, nullptr, 'e'},
        {"out", required_argument, nullptr, 'o'},
        {"scalar-log", required_argument, nullptr, 'x'},
        {"help", no_argument, nullptr, 'h'},
        {nullptr, 0, nullptr, 0}
    };

    int opt;
    while ((opt = getopt_long(argc, argv, "h", long_options, nullptr)) != -1) try {
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
            case 'm': o.model = optarg; break;
            case 'e': o.eta = std::stod(optarg); break;
            case 'o': o.out = optarg; break;
            case 'x': o.scalarLog = optarg; break;
            case 'h': usage(); std::exit(0);
            default: fail("opcion invalida (probar --help)");
        }
    } catch (const std::exception&) {
        fail("valor numerico invalido: '" + std::string(optarg ? optarg : "") + "'");
    }

    if (o.steps < 0) fail("--steps debe ser >= 0");
    if (o.N != -1 && o.N < 0) fail("--N debe ser >= 0");
    if (o.M != -1 && o.M < 1) fail("--M debe ser >= 1");
    if (o.model != "vicsek" && o.model != "voter") fail("--model debe ser 'vicsek' o 'voter'");
    if (o.eta < 0.0) fail("--eta debe ser >= 0");
    if (o.L <= 0.0) fail("--L debe ser > 0");
    if (o.rho <= 0.0) fail("--rho debe ser > 0");
    return o;
}

}  // namespace

int main(int argc, char** argv) try {
    Options o = parseArgs(argc, argv);

    if (o.N < 0) {
        o.N = static_cast<int>(std::round(o.rho * o.L * o.L));
    }
    if (o.M < 0) {
        o.M = maxValidGridM(o.L, o.rc);
    }

    std::vector<VicsekParticle> particles = generateVicsekParticles(o.N, o.L, o.seed);

    const Model model = (o.model == "voter") ? Model::Voter : Model::Vicsek;
    Simulation sim(std::move(particles), o.L, o.rc, o.v0, o.dt, o.M, o.periodic, model, o.eta,
                   o.seed);

    const std::filesystem::path outPath(o.out);
    if (!outPath.parent_path().empty()) {
        std::filesystem::create_directories(outPath.parent_path());
    }
    std::ofstream trajOut(o.out);
    if (!trajOut) fail("no se pudo abrir " + o.out);

    const bool scalarLogEnabled = !o.scalarLog.empty();
    std::ofstream scalarOut;
    if (scalarLogEnabled) {
        const std::filesystem::path scalarPath(o.scalarLog);
        if (!scalarPath.parent_path().empty()) {
            std::filesystem::create_directories(scalarPath.parent_path());
        }
        scalarOut.open(o.scalarLog);
        if (!scalarOut) fail("no se pudo abrir " + o.scalarLog);
    }

    writeTrajectoryFrame(trajOut, sim.particles(), 0.0, o.v0);
    if (scalarLogEnabled) {
        // The grid never gets populated until a rebuild happens -- reuse the
        // same resync pattern as the post-loop S computation below.
        sim.syncNeighbors();
        scalarOut << 0.0 << ' ' << polarization(sim.particles()) << ' '
                  << giantComponentFraction(sim.neighbors()) << '\n';
    }
    for (int step = 0; step < o.steps; ++step) {
        sim.step();
        writeTrajectoryFrame(trajOut, sim.particles(), static_cast<double>(step + 1) * o.dt, o.v0);
        if (scalarLogEnabled) {
            // step() only rebuilt the grid from the PRE-step snapshot, so
            // neighbors() is one step stale relative to the just-advanced
            // positions -- this resync makes S(t) match the SAME
            // configuration va(t) was just computed from, not a lagged one.
            sim.syncNeighbors();
            const double t = static_cast<double>(step + 1) * o.dt;
            scalarOut << t << ' ' << polarization(sim.particles()) << ' '
                      << giantComponentFraction(sim.neighbors()) << '\n';
        }
    }

    // step() only rebuilds the grid from the PRE-step snapshot, so neighbors()
    // is one step stale relative to particles() after the loop -- resync
    // against the true final positions before computing S (also needed when
    // steps==0, since the Grid constructor never populates neighbors_).
    sim.syncNeighbors();
    const double va = polarization(sim.particles());
    const double S = giantComponentFraction(sim.neighbors());

    std::printf(
        "TP2 motor: N=%d L=%.2f rc=%.2f M=%d steps=%d seed=%llu model=%s eta=%.4f va=%.4f "
        "S=%.4f scalar_log=%s -- OK\n",
        o.N, o.L, o.rc, o.M, o.steps, o.seed, o.model.c_str(), o.eta, va, S,
        scalarLogEnabled ? o.scalarLog.c_str() : "(disabled)");

    return 0;
} catch (const std::exception& e) {
    std::fprintf(stderr, "error: %s\n", e.what());
    return 1;
}
