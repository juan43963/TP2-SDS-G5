#include <algorithm>
#include <cmath>
#include <stdexcept>
#include <string>

#include "neighbor_method.h"

namespace {

inline int cellIndex(double coord, double cellSize, int M) {
    int c = static_cast<int>(std::floor(coord / cellSize));
    return std::clamp(c, 0, M - 1);
}

inline int wrap(int i, int M) { return ((i % M) + M) % M; }

}  // namespace

double maxRadius(const std::vector<Particle>& particles) {
    if (particles.empty()) return 0.0;
    return std::max_element(particles.begin(), particles.end(),
                            [](const Particle& a, const Particle& b) { return a.r < b.r; })->r;
}

int maxValidM(double L, double rc, double rMax) {
    const double rcEff = rc + 2.0 * rMax;
    if (L <= 0.0 || rcEff <= 0.0) return 1;

    const double limit = L / rcEff;
    int m = static_cast<int>(std::floor(limit));
    if (m > 0 && limit - m < 1e-12) m -= 1;
    return std::max(1, m);
}

NeighborList computeCIM(const std::vector<Particle>& particles, double L, int M, double rc,
                        bool periodic) {
    if (M < 1) throw std::invalid_argument("M debe ser >= 1 (M=" + std::to_string(M) + ")");
    if (L <= 0.0 || rc <= 0.0) throw std::invalid_argument("L y rc deben ser > 0");

    const double rMax = maxRadius(particles);
    const int mMax = maxValidM(L, rc, rMax);
    if (M > mMax) {
        throw std::invalid_argument("M=" + std::to_string(M) + " supera M_max=" + std::to_string(mMax));
    }
    if (periodic && L / 2.0 <= rc + 2.0 * rMax) {
        throw std::invalid_argument("con contorno periodico se requiere L/2 > rc + 2*rMax");
    }

    const int n = static_cast<int>(particles.size());
    const double cellSize = L / M;

    std::vector<std::vector<int>> cells(static_cast<size_t>(M) * M);
    for (int i = 0; i < n; ++i) {
        const int cx = cellIndex(particles[i].x, cellSize, M);
        const int cy = cellIndex(particles[i].y, cellSize, M);
        cells[static_cast<size_t>(cy) * M + cx].push_back(i);
    }

    NeighborList neighbors(n);
    const bool halfNeighborhood = !periodic || M >= 3;

    static const int HALF[5][2] = {{0, 0}, {1, 0}, {1, 1}, {0, 1}, {-1, 1}};
    static const int FULL[9][2] = {{-1, -1}, {0, -1}, {1, -1}, {-1, 0}, {0, 0},
                                   {1, 0},   {-1, 1}, {0, 1},  {1, 1}};

    const int (*offsets)[2] = halfNeighborhood ? HALF : FULL;
    const int offsetCount = halfNeighborhood ? 5 : 9;

    for (int cy = 0; cy < M; ++cy) {
        for (int cx = 0; cx < M; ++cx) {
            const int self = cy * M + cx;
            if (cells[self].empty()) continue;

            int candidates[9], count = 0;
            for (int o = 0; o < offsetCount; ++o) {
                int nx = cx + offsets[o][0], ny = cy + offsets[o][1];
                if (periodic) {
                    nx = wrap(nx, M);
                    ny = wrap(ny, M);
                } else if (nx < 0 || nx >= M || ny < 0 || ny >= M) {
                    continue;
                }
                const int idx = ny * M + nx;
                if (std::find(candidates, candidates + count, idx) == candidates + count) {
                    candidates[count++] = idx;
                }
            }

            const auto& own = cells[self];
            for (int k = 0; k < count; ++k) {
                const auto& other = cells[candidates[k]];
                const bool sameCell = (candidates[k] == self);

                for (size_t a = 0; a < own.size(); ++a) {
                    const int i = own[a];
                    const size_t start = (halfNeighborhood && sameCell) ? a + 1 : 0;
                    for (size_t b = start; b < other.size(); ++b) {
                        const int j = other[b];
                        if (!halfNeighborhood && i >= j) continue;
                        if (areNeighbors(particles[i], particles[j], L, rc, periodic)) {
                            neighbors[i].push_back(j);
                            neighbors[j].push_back(i);
                        }
                    }
                }
            }
        }
    }

    return neighbors;
}
