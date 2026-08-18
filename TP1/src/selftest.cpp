#include <algorithm>
#include <cstdio>
#include <exception>
#include <filesystem>
#include <string>
#include <vector>

#include "generator.h"
#include "io.h"
#include "neighbor_method.h"

namespace {

int failures = 0;
int checks = 0;

void check(bool condition, const std::string& what) {
    ++checks;
    if (!condition) {
        ++failures;
        std::printf("  [FALLA] %s\n", what.c_str());
    }
}

NeighborList sorted(NeighborList list) {
    for (std::vector<int>& row : list) std::sort(row.begin(), row.end());
    return list;
}

std::string describe(int N, int M, bool periodic) {
    return "N=" + std::to_string(N) + " M=" + std::to_string(M) +
           (periodic ? " periodico" : " con paredes");
}

void checkStructure(const NeighborList& list, const std::string& ctx) {
    const int n = static_cast<int>(list.size());
    for (int i = 0; i < n; ++i) {
        std::vector<int> row = list[i];
        std::sort(row.begin(), row.end());

        check(std::find(row.begin(), row.end(), i) == row.end(),
              ctx + ": la particula " + std::to_string(i) + " es vecina de si misma");
        check(std::adjacent_find(row.begin(), row.end()) == row.end(),
              ctx + ": vecinos duplicados en la particula " + std::to_string(i));

        for (const int j : row) {
            check(j >= 0 && j < n, ctx + ": id de vecino fuera de rango");
            const bool reciprocal =
                std::find(list[j].begin(), list[j].end(), i) != list[j].end();
            check(reciprocal, ctx + ": lista no simetrica entre " + std::to_string(i) + " y " +
                                  std::to_string(j));
        }
    }
}

void testCimMatchesBruteForce() {
    const double L = 20.0, rc = 1.0, rMin = 0.23, rMax = 0.26;

    for (const int N : {10, 100, 500}) {
        for (const bool periodic : {false, true}) {
            const std::vector<Particle> particles =
                generateParticles(N, L, rMin, rMax, 42, periodic);

            const NeighborList expected = sorted(computeBruteForce(particles, L, rc, periodic));
            checkStructure(expected, "fuerza bruta " + describe(N, 0, periodic));

            const int mMax = maxValidM(L, rc, maxRadius(particles));
            for (int M = 1; M <= mMax; ++M) {
                const std::string ctx = describe(N, M, periodic);
                const NeighborList actual = sorted(computeCIM(particles, L, M, rc, periodic));
                checkStructure(actual, ctx);
                check(actual == expected, ctx + ": el CIM no coincide con fuerza bruta");
            }
        }
    }
}

void testMaxM() {
    check(maxValidM(20.0, 1.0, 0.26) == 13, "M_max con los defaults del enunciado deberia ser 13");
    check(maxValidM(20.0, 1.0, 0.0) == 19, "con particulas puntuales el criterio es L/M > rc");
    check(maxValidM(20.0, 1.0, 0.5) == 9, "el criterio L/M > rcEff es estricto");
    check(maxValidM(20.0, 100.0, 0.26) == 1, "M_max nunca puede ser menor a 1");

    const std::vector<Particle> particles = generateParticles(50, 20.0, 0.23, 0.26, 7, false);
    const int mMax = maxValidM(20.0, 1.0, maxRadius(particles));

    bool threw = false;
    try {
        computeCIM(particles, 20.0, mMax + 1, 1.0, false);
    } catch (const std::exception&) {
        threw = true;
    }
    check(threw, "pedir M > M_max deberia dar error");

    threw = false;
    try {
        computeCIM(particles, 20.0, 0, 1.0, false);
    } catch (const std::exception&) {
        threw = true;
    }
    check(threw, "pedir M < 1 deberia dar error");
}

void testMinimumImageGuard() {
    const std::vector<Particle> particles = generateParticles(20, 20.0, 0.23, 0.26, 3, true);
    bool threw = false;
    try {
        computeCIM(particles, 20.0, 1, 9.5, true);
    } catch (const std::exception&) {
        threw = true;
    }
    check(threw, "minima imagen mal definida deberia dar error");
}

void testGenerator() {
    const double L = 20.0;

    for (const bool periodic : {false, true}) {
        const std::vector<Particle> ps = generateParticles(400, L, 0.23, 0.26, 99, periodic);
        check(ps.size() == 400, "el generador deberia devolver N particulas");

        bool overlap = false, outside = false, badId = false;
        for (size_t i = 0; i < ps.size(); ++i) {
            if (ps[i].id != static_cast<int>(i)) badId = true;
            if (ps[i].r < 0.23 || ps[i].r > 0.26) outside = true;
            if (!periodic) {
                if (ps[i].x < ps[i].r || ps[i].x > L - ps[i].r) outside = true;
                if (ps[i].y < ps[i].r || ps[i].y > L - ps[i].r) outside = true;
            } else if (ps[i].x < 0.0 || ps[i].x >= L || ps[i].y < 0.0 || ps[i].y >= L) {
                outside = true;
            }
            for (size_t j = i + 1; j < ps.size(); ++j) {
                if (centerDistance(ps[i], ps[j], L, periodic) <= ps[i].r + ps[j].r) overlap = true;
            }
        }
        const std::string ctx = periodic ? "periodico" : "con paredes";
        check(!badId, ctx + ": el id debe coincidir con el indice");
        check(!overlap, ctx + ": hay particulas superpuestas");
        check(!outside, ctx + ": hay particulas fuera del recinto o con radio invalido");
    }

    bool threw = false;
    try {
        generateParticles(100000, 20.0, 0.23, 0.26, 1, false, 2000);
    } catch (const std::exception&) {
        threw = true;
    }
    check(threw, "una densidad imposible deberia dar error de saturacion");

    const std::vector<Particle> a = generateParticles(100, L, 0.23, 0.26, 12345, false);
    const std::vector<Particle> b = generateParticles(100, L, 0.23, 0.26, 12345, false);
    bool identical = true;
    for (size_t i = 0; i < a.size(); ++i) {
        if (a[i].x != b[i].x || a[i].y != b[i].y || a[i].r != b[i].r) identical = false;
    }
    check(identical, "la misma semilla deberia dar la misma configuracion");
}

void testIoRoundTrip() {
    const double L = 20.0, rc = 1.0;
    const std::filesystem::path dir = std::filesystem::temp_directory_path() / "cim_selftest";
    std::filesystem::create_directories(dir);
    const std::string sPath = (dir / "static.txt").string();
    const std::string dPath = (dir / "dynamic.txt").string();

    for (const bool periodic : {false, true}) {
        const std::vector<Particle> original = generateParticles(300, L, 0.23, 0.26, 55, periodic);
        writeStatic(sPath, original, L);
        writeDynamic(dPath, original);

        double readL = 0.0;
        const std::vector<Particle> reread = readSystem(sPath, dPath, readL);

        const std::string ctx = periodic ? "periodico" : "con paredes";
        check(readL == L, ctx + ": L no sobrevive el round-trip");
        check(reread.size() == original.size(), ctx + ": cambio la cantidad de particulas");

        bool sameIds = true;
        for (size_t i = 0; i < reread.size(); ++i) {
            if (reread[i].id != static_cast<int>(i)) sameIds = false;
        }
        check(sameIds, ctx + ": el id debe seguir siendo el indice tras leer");

        const int M = maxValidM(L, rc, maxRadius(original));
        check(sorted(computeCIM(original, L, M, rc, periodic)) ==
                  sorted(computeCIM(reread, L, M, rc, periodic)),
              ctx + ": el sistema releido da otra lista de vecinos");
    }

    bool threw = false;
    try {
        double dummy = 0.0;
        readSystem("/no/existe/static.txt", "/no/existe/dynamic.txt", dummy);
    } catch (const std::exception&) {
        threw = true;
    }
    check(threw, "leer un archivo inexistente deberia dar error");

    std::filesystem::remove_all(dir);
}

}  // namespace

int main() {
    std::printf("Self-test del nucleo CIM\n");

    std::printf("- generador de particulas no superpuestas\n");
    testGenerator();
    std::printf("- criterio L/M > rc + 2*rMax y validaciones de M\n");
    testMaxM();
    std::printf("- guarda de minima imagen (contorno periodico)\n");
    testMinimumImageGuard();
    std::printf("- round-trip de archivos estatico/dinamico\n");
    testIoRoundTrip();
    std::printf("- CIM == fuerza bruta para todo M valido\n");
    testCimMatchesBruteForce();

    std::printf("\n%d verificaciones, %d fallas\n", checks, failures);
    if (failures == 0) std::printf("OK\n");
    return failures == 0 ? 0 : 1;
}
