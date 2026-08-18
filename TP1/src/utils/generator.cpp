#include "generator.h"

#include <algorithm>
#include <cmath>
#include <random>
#include <stdexcept>
#include <string>

namespace {

class OverlapGrid {
public:
    OverlapGrid(double L, double rMax, bool periodic) : L_(L), periodic_(periodic) {
        const double minCell = 2.0 * rMax;
        M_ = std::max(1, (minCell > 0.0) ? static_cast<int>(std::floor(L / minCell)) : 1);
        cellSize_ = L / M_;
        cells_.resize(static_cast<size_t>(M_) * M_);
    }

    bool overlaps(const std::vector<Particle>& placed, const Particle& candidate) const {
        const int cx = index(candidate.x), cy = index(candidate.y);
        for (int dy = -1; dy <= 1; ++dy) {
            for (int dx = -1; dx <= 1; ++dx) {
                int nx = cx + dx, ny = cy + dy;
                if (periodic_) {
                    nx = ((nx % M_) + M_) % M_;
                    ny = ((ny % M_) + M_) % M_;
                } else if (nx < 0 || nx >= M_ || ny < 0 || ny >= M_) {
                    continue;
                }
                const auto& cell = cells_[static_cast<size_t>(ny) * M_ + nx];
                if (std::any_of(cell.begin(), cell.end(), [&](int i) {
                        return centerDistance(placed[i], candidate, L_, periodic_) <= placed[i].r + candidate.r;
                    })) return true;
            }
        }
        return false;
    }

    void insert(const Particle& p, int index_in_vector) {
        cells_[static_cast<size_t>(index(p.y)) * M_ + index(p.x)].push_back(index_in_vector);
    }

private:
    int index(double coord) const {
        return std::clamp(static_cast<int>(std::floor(coord / cellSize_)), 0, M_ - 1);
    }

    double L_;
    bool periodic_;
    int M_ = 1;
    double cellSize_ = 1.0;
    std::vector<std::vector<int>> cells_;
};

}  // namespace

std::vector<Particle> generateParticles(int N, double L, double rMin, double rMax, uint64_t seed,
                                        bool periodic, int maxAttemptsPerParticle) {
    if (N < 0) throw std::invalid_argument("N debe ser >= 0");
    if (L <= 0.0) throw std::invalid_argument("L debe ser > 0");
    if (rMin < 0.0 || rMax < rMin) throw std::invalid_argument("se requiere 0 <= rMin <= rMax");
    if (!periodic && 2.0 * rMax >= L)
        throw std::invalid_argument("el diametro maximo no entra en el recinto de lado L");

    std::mt19937_64 rng(seed);
    std::uniform_real_distribution<double> radiusDist(rMin, rMax);

    std::vector<Particle> particles;
    particles.reserve(N);
    OverlapGrid grid(L, rMax, periodic);

    for (int i = 0; i < N; ++i) {
        const double r = radiusDist(rng);
        const double lo = periodic ? 0.0 : r;
        const double hi = periodic ? L : L - r;
        std::uniform_real_distribution<double> posDist(lo, std::nextafter(hi, lo));

        bool placed = false;
        for (int attempt = 0; attempt < maxAttemptsPerParticle; ++attempt) {
            Particle candidate{i, posDist(rng), posDist(rng), r};
            if (!grid.overlaps(particles, candidate)) {
                particles.push_back(candidate);
                grid.insert(candidate, i);
                placed = true;
                break;
            }
        }

        if (!placed) {
            throw std::runtime_error("saturacion al generar particulas en L=" + std::to_string(L));
        }
    }

    return particles;
}
