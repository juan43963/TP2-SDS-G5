#include <algorithm>
#include <cstdio>
#include <string>
#include <vector>

#include "grid.h"
#include "particle.h"

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

}  // namespace

int main() {
    std::printf("Self-test del motor TP2\n");

    std::printf("- estructura de la grilla persistente (CIM)\n");
    testGridStructural();

    std::printf("\n%d verificaciones, %d fallas\n", checks, failures);
    if (failures == 0) std::printf("OK\n");
    return failures == 0 ? 0 : 1;
}
