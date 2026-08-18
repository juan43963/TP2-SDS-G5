#include <algorithm>
#include <chrono>
#include <cmath>
#include <cstdio>
#include <exception>
#include <filesystem>
#include <getopt.h>
#include <numeric>
#include <random>
#include <string>
#include <vector>

#include "generator.h"
#include "io.h"
#include "neighbor_method.h"

namespace {

struct Options {
    int N = 100;
    double L = 20.0;
    int M = -1;
    double rc = 1.0;
    double rMin = 0.23;
    double rMax = 0.26;
    unsigned long long seed = 0;
    bool seedGiven = false;
    bool periodic = false;
    bool bruteForce = false;
    int highlight = 0;
    int repeat = 1;
    bool csv = false;
    std::string outdir = "data";
    std::string staticPath;
    std::string dynamicPath;
};

void usage() {
    std::printf(
        "Cell Index Method - TP1 Simulacion de Sistemas\n\n"
        "Uso:\n  ./cim [opciones]\n\n"
        "Sistema:\n"
        "  --N <int>        cantidad de particulas a generar      (default 100)\n"
        "  --L <real>       lado del area cuadrada                (default 20)\n"
        "  --rc <real>      radio de interaccion                  (default 1)\n"
        "  --rmin <real>    radio minimo de particula             (default 0.23)\n"
        "  --rmax <real>    radio maximo de particula             (default 0.26)\n"
        "  --seed <int>     semilla del generador                 (default aleatoria)\n\n"
        "Metodo:\n"
        "  --M <int>        celdas por lado de la grilla          (default: M_max)\n"
        "  --periodic       con condiciones periodicas de contorno (variante b)\n"
        "  --brute          usar fuerza bruta en lugar del CIM\n"
        "  --repeat <int>   repetir la busqueda y reportar media y desvio (default 1)\n"
        "  --csv            salida en una linea CSV\n\n"
        "Entrada/Salida:\n"
        "  --static <path>  leer el sistema de un archivo estatico\n"
        "  --dynamic <path> archivo dinamico correspondiente\n"
        "  --outdir <path>  carpeta de salida                     (default data)\n"
        "  --highlight <id> particula a destacar en el reporte    (default 0)\n"
        "  -h, --help       esta ayuda\n");
}

[[noreturn]] void fail(const std::string& message) {
    std::fprintf(stderr, "error: %s\n", message.c_str());
    std::exit(1);
}

Options parseArgs(int argc, char** argv) {
    Options o;
    static struct option long_options[] = {
        {"N", required_argument, nullptr, 'N'},
        {"L", required_argument, nullptr, 'L'},
        {"M", required_argument, nullptr, 'M'},
        {"rc", required_argument, nullptr, 'c'},
        {"rmin", required_argument, nullptr, 'n'},
        {"rmax", required_argument, nullptr, 'x'},
        {"seed", required_argument, nullptr, 's'},
        {"periodic", no_argument, nullptr, 'p'},
        {"brute", no_argument, nullptr, 'b'},
        {"repeat", required_argument, nullptr, 'r'},
        {"csv", no_argument, nullptr, 'v'},
        {"highlight", required_argument, nullptr, 'i'},
        {"outdir", required_argument, nullptr, 'o'},
        {"static", required_argument, nullptr, 'S'},
        {"dynamic", required_argument, nullptr, 'D'},
        {"help", no_argument, nullptr, 'h'},
        {nullptr, 0, nullptr, 0}
    };

    int opt;
    while ((opt = getopt_long(argc, argv, "h", long_options, nullptr)) != -1) {
        switch (opt) {
            case 'N': o.N = std::stoi(optarg); break;
            case 'L': o.L = std::stod(optarg); break;
            case 'M': o.M = std::stoi(optarg); break;
            case 'c': o.rc = std::stod(optarg); break;
            case 'n': o.rMin = std::stod(optarg); break;
            case 'x': o.rMax = std::stod(optarg); break;
            case 's': o.seed = std::stoull(optarg); o.seedGiven = true; break;
            case 'p': o.periodic = true; break;
            case 'b': o.bruteForce = true; break;
            case 'r': o.repeat = std::stoi(optarg); break;
            case 'v': o.csv = true; break;
            case 'i': o.highlight = std::stoi(optarg); break;
            case 'o': o.outdir = optarg; break;
            case 'S': o.staticPath = optarg; break;
            case 'D': o.dynamicPath = optarg; break;
            case 'h': usage(); std::exit(0);
            default: fail("opcion invalida (probar --help)");
        }
    }

    if (!o.seedGiven) {
        std::random_device rd;
        o.seed = (static_cast<unsigned long long>(rd()) << 32) ^ rd();
    }

    if (o.repeat < 1) fail("--repeat debe ser >= 1");
    if (o.staticPath.empty() != o.dynamicPath.empty())
        fail("--static y --dynamic se usan juntos");
    return o;
}

size_t countPairs(const NeighborList& neighbors) {
    return std::accumulate(neighbors.begin(), neighbors.end(), size_t{0},
                           [](size_t sum, const auto& row) { return sum + row.size(); }) / 2;
}

}  // namespace

int main(int argc, char** argv) try {
    const Options o = parseArgs(argc, argv);

    std::vector<Particle> particles;
    double L = o.L;
    if (!o.staticPath.empty()) {
        particles = readSystem(o.staticPath, o.dynamicPath, L);
    } else {
        particles = generateParticles(o.N, o.L, o.rMin, o.rMax, o.seed, o.periodic);
    }
    const int N = static_cast<int>(particles.size());

    const double rMaxRef = o.staticPath.empty() ? o.rMax : maxRadius(particles);
    const int mMax = maxValidM(L, o.rc, rMaxRef);
    const int M = (o.M > 0) ? o.M : mMax;

    if (N > 0 && (o.highlight < 0 || o.highlight >= N))
        fail("--highlight debe estar entre 0 y " + std::to_string(N - 1));

    const auto search = [&]() {
        return o.bruteForce ? computeBruteForce(particles, L, o.rc, o.periodic)
                            : computeCIM(particles, L, M, o.rc, o.periodic);
    };

    if (o.repeat > 1) search();

    NeighborList neighbors;
    std::vector<double> timesMs;
    timesMs.reserve(o.repeat);

    for (int rep = 0; rep < o.repeat; ++rep) {
        const auto t0 = std::chrono::steady_clock::now();
        neighbors = search();
        const auto t1 = std::chrono::steady_clock::now();
        timesMs.push_back(std::chrono::duration<double, std::milli>(t1 - t0).count());
    }

    int discarded = 0;
    if (o.repeat >= 100) {
        std::sort(timesMs.begin(), timesMs.end());
        discarded = static_cast<int>(timesMs.size() / 100);
        timesMs.resize(timesMs.size() - discarded);
    }

    double mean = std::accumulate(timesMs.begin(), timesMs.end(), 0.0) / timesMs.size();

    double stdev = 0.0;
    if (timesMs.size() > 1) {
        double sqSum = std::accumulate(timesMs.begin(), timesMs.end(), 0.0,
                                       [mean](double sum, double t) { return sum + (t - mean) * (t - mean); });
        stdev = std::sqrt(sqSum / (timesMs.size() - 1));
    }

    if (o.csv) {
        std::printf("%d,%.10g,%d,%.10g,%d,%s,%zu,%d,%.6f,%.6f,%d\n", N, L, o.bruteForce ? 0 : M, o.rc,
                    o.periodic ? 1 : 0, o.bruteForce ? "brute" : "cim", countPairs(neighbors),
                    o.repeat, mean, stdev, discarded);
        return 0;
    }

    const char* method = o.bruteForce ? "fuerza bruta" : "Cell Index Method";
    std::printf("%s\n\n", method);
    std::printf("  N              %d\n", N);
    std::printf("  L              %.4g\n", L);
    std::printf("  rc             %.4g\n", o.rc);
    std::printf("  contorno       %s\n", o.periodic ? "periodico" : "paredes");
    if (!o.bruteForce) {
        std::printf("  M              %d   (M_max = %d)\n", M, mMax);
        std::printf("  L/M            %.4g   (criterio: L/M > rc + 2*rMax = %.4g)\n", L / M,
                    o.rc + 2.0 * rMaxRef);
    }

    const size_t pairs = countPairs(neighbors);
    std::printf("\n  pares vecinos  %zu\n", pairs);
    std::printf("  vecinos/part.  %.3f\n", N > 0 ? 2.0 * pairs / N : 0.0);

    if (o.repeat == 1) {
        std::printf("\n  tiempo         %.4g ms\n", mean);
    } else {
        std::printf("\n  tiempo         %.4g +/- %.2g ms   (%d corridas", mean, stdev, o.repeat);
        if (discarded > 0) std::printf(", %d descartadas por atipicas", discarded);
        std::printf(")\n");
    }

    std::filesystem::create_directories(o.outdir);
    const std::string sPath = o.outdir + "/static.txt";
    const std::string dPath = o.outdir + "/dynamic.txt";
    const std::string nPath = o.outdir + "/neighbors.txt";
    writeStatic(sPath, particles, L);
    writeDynamic(dPath, particles);
    writeNeighbors(nPath, neighbors);
    std::printf("\n  archivos       %s\n                 %s\n                 %s\n", sPath.c_str(),
                dPath.c_str(), nPath.c_str());

    if (N > 0) {
        std::vector<int> row = neighbors[o.highlight];
        std::sort(row.begin(), row.end());
        std::printf("\n  particula %d en (%.3f, %.3f) r=%.3f -> %zu vecinos\n", o.highlight,
                    particles[o.highlight].x, particles[o.highlight].y, particles[o.highlight].r,
                    row.size());
        if (!row.empty()) {
            std::printf("   ");
            for (const int j : row) std::printf(" %d", j);
            std::printf("\n");
        }
    }

    return 0;
} catch (const std::exception& e) {
    std::fprintf(stderr, "error: %s\n", e.what());
    return 1;
}
