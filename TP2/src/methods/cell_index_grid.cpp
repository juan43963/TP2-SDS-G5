#include "grid.h"

#include <algorithm>
#include <cmath>
#include <stdexcept>
#include <string>

namespace {

inline int cellIndex(double coord, double cellSize, int M) {
    int c = static_cast<int>(std::floor(coord / cellSize));
    return std::clamp(c, 0, M - 1);
}

inline int wrap(int i, int M) { return ((i % M) + M) % M; }

}  // namespace

int maxValidGridM(double L, double rc) {
    if (L <= 0.0 || rc <= 0.0) return 1;

    const double limit = L / rc;
    int m = static_cast<int>(std::floor(limit));
    if (m > 0 && limit - m < 1e-12) m -= 1;
    return std::max(1, m);
}

Grid::Grid(int M_, double L_, double rc_, bool periodic_)
    : M(M_), L(L_), rc(rc_), periodic(periodic_) {
    if (M < 1) throw std::invalid_argument("M debe ser >= 1 (M=" + std::to_string(M) + ")");
    if (L <= 0.0 || rc <= 0.0) throw std::invalid_argument("L y rc deben ser > 0");

    const int mMax = maxValidGridM(L, rc);
    if (M > mMax) {
        throw std::invalid_argument("M=" + std::to_string(M) + " supera M_max=" + std::to_string(mMax));
    }
    if (periodic && L / 2.0 <= rc) {
        throw std::invalid_argument("con contorno periodico se requiere L/2 > rc");
    }

    cells.resize(static_cast<size_t>(M) * M);
}

void Grid::rebuild(const std::vector<VicsekParticle>& particles) {
    for (auto& cell : cells) cell.clear();

    const int n = static_cast<int>(particles.size());
    const double cellSize = L / M;

    for (int i = 0; i < n; ++i) {
        const int cx = cellIndex(particles[i].x, cellSize, M);
        const int cy = cellIndex(particles[i].y, cellSize, M);
        cells[static_cast<size_t>(cy) * M + cx].push_back(i);
    }

    if (static_cast<int>(neighbors_.size()) != n) {
        neighbors_.assign(static_cast<size_t>(n), std::vector<int>());
    } else {
        for (auto& row : neighbors_) row.clear();
    }

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
                        if (withinRadius(particles[static_cast<size_t>(i)],
                                         particles[static_cast<size_t>(j)], L, rc, periodic)) {
                            neighbors_[static_cast<size_t>(i)].push_back(j);
                            neighbors_[static_cast<size_t>(j)].push_back(i);
                        }
                    }
                }
            }
        }
    }
}
