#include <algorithm>
#include <cmath>
#include <cstdio>
#include <string>
#include <vector>

#include "engine/simulation.h"
#include "generator.h"
#include "grid.h"
#include "particle.h"

namespace {

constexpr double kPi = 3.14159265358979323846;

int failures = 0;
int checks = 0;

void check(bool condition, const std::string& what) {
    ++checks;
    if (!condition) {
        ++failures;
        std::printf("  [FALLA] %s\n", what.c_str());
    }
}

void checkStructure(const NeighborList& list, const std::string& ctx) {
    const int n = static_cast<int>(list.size());
    for (int i = 0; i < n; ++i) {
        std::vector<int> row = list[static_cast<size_t>(i)];
        std::sort(row.begin(), row.end());

        check(std::find(row.begin(), row.end(), i) == row.end(),
              ctx + ": la particula " + std::to_string(i) + " es vecina de si misma");
        check(std::adjacent_find(row.begin(), row.end()) == row.end(),
              ctx + ": vecinos duplicados en la particula " + std::to_string(i));

        for (const int j : row) {
            check(j >= 0 && j < n, ctx + ": id de vecino fuera de rango");
            const bool reciprocal =
                std::find(list[static_cast<size_t>(j)].begin(), list[static_cast<size_t>(j)].end(), i) !=
                list[static_cast<size_t>(j)].end();
            check(reciprocal, ctx + ": lista no simetrica entre " + std::to_string(i) + " y " +
                                  std::to_string(j));
        }
    }
}

void testGridStructural() {
    const double L = 10.0, rc = 1.5;
    const int M = maxValidGridM(L, rc);

    // p0-p1 y p0-p2 estan dentro de rc; p1-p2 no; p3 esta aislada.
    const std::vector<VicsekParticle> particles = {
        {0, 1.0, 1.0, 0.0},
        {1, 2.0, 1.0, 0.0},
        {2, 1.0, 2.4, 0.0},
        {3, 8.0, 8.0, 0.0},
    };

    for (const bool periodic : {false, true}) {
        Grid grid(M, L, rc, periodic);
        grid.rebuild(particles);
        const NeighborList& neighbors = grid.neighbors();
        const std::string ctx = periodic ? "periodico" : "con paredes";

        checkStructure(neighbors, ctx);

        auto hasNeighbor = [&](int i, int j) {
            return std::find(neighbors[static_cast<size_t>(i)].begin(),
                              neighbors[static_cast<size_t>(i)].end(), j) !=
                   neighbors[static_cast<size_t>(i)].end();
        };

        check(hasNeighbor(0, 1), ctx + ": p0 y p1 deberian ser vecinos");
        check(hasNeighbor(0, 2), ctx + ": p0 y p2 deberian ser vecinos");
        check(!hasNeighbor(1, 2), ctx + ": p1 y p2 no deberian ser vecinos");
        check(neighbors[3].empty(), ctx + ": p3 deberia estar aislada");
    }
}

NeighborList sorted(NeighborList list) {
    for (std::vector<int>& row : list) std::sort(row.begin(), row.end());
    return list;
}

NeighborList bruteForceReference(const std::vector<VicsekParticle>& particles, double L, double rc,
                                 bool periodic) {
    const int n = static_cast<int>(particles.size());
    NeighborList result(static_cast<size_t>(n));
    for (int i = 0; i < n; ++i) {
        for (int j = i + 1; j < n; ++j) {
            if (withinRadius(particles[static_cast<size_t>(i)], particles[static_cast<size_t>(j)], L, rc,
                             periodic)) {
                result[static_cast<size_t>(i)].push_back(j);
                result[static_cast<size_t>(j)].push_back(i);
            }
        }
    }
    return result;
}

void testGenerator() {
    const double L = 10.0;

    const std::vector<VicsekParticle> a = generateVicsekParticles(50, L, 42);
    const std::vector<VicsekParticle> b = generateVicsekParticles(50, L, 42);

    check(a.size() == 50, "el generador deberia devolver N particulas");

    bool badId = false, outside = false, identical = true;
    for (size_t i = 0; i < a.size(); ++i) {
        if (a[i].id != static_cast<int>(i)) badId = true;
        if (a[i].x < 0.0 || a[i].x >= L || a[i].y < 0.0 || a[i].y >= L) outside = true;
        if (a[i].theta < -kPi || a[i].theta >= kPi) outside = true;
        if (a[i].x != b[i].x || a[i].y != b[i].y || a[i].theta != b[i].theta) identical = false;
    }
    check(!badId, "el id debe coincidir con el indice");
    check(!outside, "x,y deben estar en [0,L) y theta en [-pi,pi)");
    check(identical, "la misma semilla deberia dar la misma configuracion");
}

void testGridMatchesBruteForce() {
    const double L = 10.0, rc = 1.0;
    const int mMax = maxValidGridM(L, rc);

    for (const int N : {10, 100}) {
        for (const bool periodic : {false, true}) {
            const std::vector<VicsekParticle> particles = generateVicsekParticles(N, L, 7);
            const NeighborList expected = sorted(bruteForceReference(particles, L, rc, periodic));
            const std::string bfCtx =
                "fuerza bruta N=" + std::to_string(N) + (periodic ? " periodico" : " con paredes");
            checkStructure(expected, bfCtx);

            for (int M = 1; M <= mMax; ++M) {
                const std::string ctx =
                    "N=" + std::to_string(N) + " M=" + std::to_string(M) + (periodic ? " periodico" : " con paredes");
                Grid grid(M, L, rc, periodic);
                grid.rebuild(particles);
                const NeighborList actual = sorted(grid.neighbors());
                checkStructure(actual, ctx);
                check(actual == expected, ctx + ": el grid no coincide con fuerza bruta");
            }
        }
    }
}

void testGridPersistentBuffers() {
    const double L = 10.0, rc = 1.0;
    const int M = maxValidGridM(L, rc);
    Grid grid(M, L, rc, false);

    const std::vector<VicsekParticle> first = generateVicsekParticles(10, L, 1);
    grid.rebuild(first);
    const void* cellsPtr1 = static_cast<const void*>(grid.cells.data());

    const std::vector<VicsekParticle> second = generateVicsekParticles(10, L, 2);
    grid.rebuild(second);
    const void* cellsPtr2 = static_cast<const void*>(grid.cells.data());

    check(cellsPtr1 == cellsPtr2, "grid.cells no deberia reasignarse entre llamadas a rebuild()");
}

void testSynchronousUpdateNoBias() {
    // Hand-computed 3-particle case (see 01-02-PLAN.md Task 1 <behavior>):
    // p0={1,1,0}, p1={2,1,pi/2}, p2={1,2,pi}; mutual distances 1.0, 1.0,
    // sqrt(2) are all < rc=2.0, so all three are mutual neighbors.
    // Self-inclusive circular mean gives sin-sum=1, cos-sum=0 for every
    // particle, so the expected new heading is atan2(1, 0) = pi/2 exactly.
    const double L = 10.0, rc = 2.0;
    const int M = maxValidGridM(L, rc);
    const double expected = 1.5707963267948966;  // pi/2, hand-derived above

    auto findThetaById = [](const std::vector<VicsekParticle>& particles, int id) {
        for (const VicsekParticle& p : particles) {
            if (p.id == id) return p.theta;
        }
        return std::nan("");
    };

    // Forward insertion order: p0, p1, p2.
    const std::vector<VicsekParticle> forward = {
        {0, 1.0, 1.0, 0.0},
        {1, 2.0, 1.0, kPi / 2.0},
        {2, 1.0, 2.0, kPi},
    };
    Simulation simForward(forward, L, rc, /*v0=*/0.0, /*dt=*/1.0, M, /*periodic=*/false);
    simForward.step();

    for (const int id : {0, 1, 2}) {
        const double theta = findThetaById(simForward.particles(), id);
        check(std::abs(theta - expected) < 1e-9,
              "actualizacion sincronica: particula " + std::to_string(id) +
                  " deberia converger a pi/2 (orden directo)");
    }

    // Reverse insertion order: p2, p1, p0 -- proves no iteration-order bias.
    const std::vector<VicsekParticle> reverse = {
        {2, 1.0, 2.0, kPi},
        {1, 2.0, 1.0, kPi / 2.0},
        {0, 1.0, 1.0, 0.0},
    };
    Simulation simReverse(reverse, L, rc, /*v0=*/0.0, /*dt=*/1.0, M, /*periodic=*/false);
    simReverse.step();

    for (const int id : {0, 1, 2}) {
        const double forwardTheta = findThetaById(simForward.particles(), id);
        const double reverseTheta = findThetaById(simReverse.particles(), id);
        check(std::abs(reverseTheta - expected) < 1e-9,
              "actualizacion sincronica: particula " + std::to_string(id) +
                  " deberia converger a pi/2 (orden inverso)");
        check(std::abs(reverseTheta - forwardTheta) < 1e-9,
              "actualizacion sincronica: particula " + std::to_string(id) +
                  " no deberia depender del orden de insercion");
    }
}

void testLongRunStaysWrapped() {
    // 5000-step run under periodic boundary conditions: every particle's
    // position must remain strictly inside [0, L) after every single step,
    // not just checked at the end (PITFALLS.md Pitfall 3).
    const double L = 10.0, rc = 1.0;
    const int M = maxValidGridM(L, rc);

    std::vector<VicsekParticle> particles = generateVicsekParticles(50, L, 123);
    Simulation sim(std::move(particles), L, rc, /*v0=*/0.5, /*dt=*/1.0, M, /*periodic=*/true);

    bool everyStepWrapped = true;
    for (int step = 0; step < 5000; ++step) {
        sim.step();
        for (const VicsekParticle& p : sim.particles()) {
            if (!(p.x >= 0.0 && p.x < L && p.y >= 0.0 && p.y < L)) {
                everyStepWrapped = false;
            }
        }
    }
    check(everyStepWrapped,
          "5000 pasos bajo PBC: todas las posiciones deben permanecer en [0, L)");
}

}  // namespace

int main() {
    std::printf("Self-test del motor TP2\n");

    std::printf("- estructura de la grilla persistente (CIM)\n");
    testGridStructural();
    std::printf("- generador de particulas puntuales\n");
    testGenerator();
    std::printf("- grid == fuerza bruta para todo M valido\n");
    testGridMatchesBruteForce();
    std::printf("- buffers persistentes del grid entre llamadas a rebuild()\n");
    testGridPersistentBuffers();
    std::printf("- actualizacion sincronica double-buffered (sin sesgo de orden)\n");
    testSynchronousUpdateNoBias();
    std::printf("- posiciones permanecen en [0,L) tras 5000 pasos con PBC\n");
    testLongRunStaysWrapped();

    std::printf("\n%d verificaciones, %d fallas\n", checks, failures);
    if (failures == 0) std::printf("OK\n");
    return failures == 0 ? 0 : 1;
}
