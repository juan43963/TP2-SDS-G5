#include <algorithm>
#include <cmath>
#include <numbers>
#include <numeric>
#include <random>
#include <stdexcept>
#include <string>

#include "billiard.h"

namespace {

struct RsaGrid {
    int M;
    double R;
    double cellSize;
    std::vector<std::vector<int>> cells;

    explicit RsaGrid(const BilliardParams& p)
        : M(cimGridSize(p)),
          R(p.R),
          cellSize(2.0 * p.R / static_cast<double>(cimGridSize(p))),
          cells(static_cast<std::size_t>(M) * static_cast<std::size_t>(M)) {}

    int bin(double coordinate) const {
        const double raw = std::floor((coordinate + R) / cellSize);
        return static_cast<int>(std::clamp(raw, 0.0, static_cast<double>(M) - 1.0));
    }
    std::size_t index(int cx, int cy) const {
        return static_cast<std::size_t>(cy) * static_cast<std::size_t>(M) +
               static_cast<std::size_t>(cx);
    }
};

// Rejection sampling con acelerador de celdas: solo se miran las 3x3 celdas
// alrededor del candidato (la celda mide al menos 2 radius).
bool placeRsa(const BilliardParams& p, std::mt19937_64& rng, std::vector<Vec2>& pos,
              int& failedIndex) {
    std::uniform_real_distribution<double> unit(0.0, 1.0);
    const double limit = p.R - p.radius;
    const double limit2 = limit * limit;
    const double contact2 = 4.0 * p.radius * p.radius;
    RsaGrid grid(p);
    pos.clear();
    pos.reserve(static_cast<std::size_t>(p.N));

    for (int i = 0; i < p.N; ++i) {
        bool placed = false;
        for (int attempt = 0; attempt < kRsaMaxAttemptsPerParticle && !placed; ++attempt) {
            const double rho = limit * std::sqrt(unit(rng));
            const double phi = 2.0 * std::numbers::pi * unit(rng);
            const Vec2 c{rho * std::cos(phi), rho * std::sin(phi)};
            if (norm2(c) > limit2) continue;
            if (p.obstacles) {
                if (norm2(c - Vec2{-p.x0, 0.0}) < contact2) continue;
                if (norm2(c - Vec2{p.x0, 0.0}) < contact2) continue;
            }
            const int cx = grid.bin(c.x);
            const int cy = grid.bin(c.y);
            bool overlap = false;
            for (int dy = -1; dy <= 1 && !overlap; ++dy) {
                for (int dx = -1; dx <= 1 && !overlap; ++dx) {
                    const int nx = cx + dx;
                    const int ny = cy + dy;
                    if (nx < 0 || nx >= grid.M || ny < 0 || ny >= grid.M) continue;
                    for (const int j : grid.cells[grid.index(nx, ny)]) {
                        if (norm2(c - pos[static_cast<std::size_t>(j)]) < contact2) {
                            overlap = true;
                            break;
                        }
                    }
                }
            }
            if (overlap) continue;
            grid.cells[grid.index(cx, cy)].push_back(i);
            pos.push_back(c);
            placed = true;
        }
        if (!placed) {
            failedIndex = i;
            return false;
        }
    }
    return true;
}

// N sitios de la red elegidos al azar sin reposicion, cada uno corrido uniformemente dentro
// de un disco de radio J = gap/2 (estrictamente menor): la distancia entre dos particulas
// queda > a - 2J = 2 radius, asi que el estado nunca solapa.
void placeLattice(const BilliardParams& p, std::mt19937_64& rng, std::vector<Vec2>& pos) {
    const std::vector<Vec2> sites = latticeSites(p);
    std::vector<int> order(sites.size());
    std::iota(order.begin(), order.end(), 0);
    std::shuffle(order.begin(), order.end(), rng);
    const double jitter = kLatticeGap / 2.0;
    std::uniform_real_distribution<double> unit(0.0, 1.0);
    pos.clear();
    pos.reserve(static_cast<std::size_t>(p.N));
    for (int i = 0; i < p.N; ++i) {
        const Vec2 site = sites[static_cast<std::size_t>(order[static_cast<std::size_t>(i)])];
        const double rho = jitter * std::sqrt(unit(rng));
        const double phi = 2.0 * std::numbers::pi * unit(rng);
        pos.push_back(site + Vec2{rho * std::cos(phi), rho * std::sin(phi)});
    }
}

}  // namespace

InitMethod parseInitMethod(std::string_view name) {
    if (name == "rsa") return InitMethod::Rsa;
    if (name == "lattice") return InitMethod::Lattice;
    if (name == "auto") return InitMethod::Auto;
    throw std::invalid_argument("--init desconocido '" + std::string(name) +
                                "' (validos: rsa, lattice, auto)");
}

const char* initMethodName(InitMethod method) {
    switch (method) {
        case InitMethod::Rsa: return "rsa";
        case InitMethod::Lattice: return "lattice";
        case InitMethod::Auto: return "auto";
    }
    return "auto";
}

std::vector<Vec2> latticeSites(const BilliardParams& p) {
    validateParams(p);
    const double a = 2.0 * p.radius + kLatticeGap;
    const double jitter = kLatticeGap / 2.0;
    const double h = a * std::sqrt(3.0) / 2.0;
    const int jmax = static_cast<int>(std::ceil(p.R / h)) + 1;
    const int imax = static_cast<int>(std::ceil(p.R / a)) + 2;
    const double wall = p.R - p.radius - jitter;
    const double wall2 = wall * wall;
    const double obstacle = 2.0 * p.radius + jitter;
    const double obstacle2 = obstacle * obstacle;
    std::vector<Vec2> sites;
    for (int j = -jmax; j <= jmax; ++j) {
        const double shift = (j % 2 != 0) ? a / 2.0 : 0.0;
        for (int i = -imax; i <= imax; ++i) {
            const Vec2 s{static_cast<double>(i) * a + shift, static_cast<double>(j) * h};
            if (norm2(s) > wall2) continue;
            if (p.obstacles && (norm2(s - Vec2{-p.x0, 0.0}) < obstacle2 ||
                                norm2(s - Vec2{p.x0, 0.0}) < obstacle2)) {
                continue;
            }
            sites.push_back(s);
        }
    }
    return sites;
}

int latticeCapacity(const BilliardParams& p) {
    return static_cast<int>(latticeSites(p).size());
}


InitialState generateInitialState(const BilliardParams& p) {
    validateParams(p);
    const int capacity = latticeCapacity(p);
    if (p.N > capacity) {
        throw std::invalid_argument("--N " + std::to_string(p.N) +
                                    " excede la capacidad de la red hexagonal: " +
                                    std::to_string(capacity) + " sitios (x0 = " +
                                    std::to_string(p.x0) + ", obstaculos = " +
                                    (p.obstacles ? "1" : "0") + ")");
    }
    std::mt19937_64 rng(p.seed);
    InitialState state;
    bool lattice = false;
    int failedIndex = 0;
    switch (p.init) {
        case InitMethod::Rsa:
            if (!placeRsa(p, rng, state.pos, failedIndex)) {
                throw std::runtime_error("RSA: no se pudo ubicar la particula " +
                                         std::to_string(failedIndex) + " de " +
                                         std::to_string(p.N) + " tras " +
                                         std::to_string(kRsaMaxAttemptsPerParticle) +
                                         " intentos; usar --init lattice");
            }
            break;
        case InitMethod::Lattice:
            placeLattice(p, rng, state.pos);
            lattice = true;
            break;
        case InitMethod::Auto:
            if (p.N <= kAutoRsaMaxN && placeRsa(p, rng, state.pos, failedIndex)) break;
            // RSA agotada (o N alto): red con un generador re-sembrado, identico a --init lattice.
            rng.seed(p.seed);
            placeLattice(p, rng, state.pos);
            lattice = true;
            break;
    }
    // Las velocidades se sortean despues de todas las posiciones, asi que la
    // condicion inicial no depende de dt, tf ni every.
    std::uniform_real_distribution<double> angle(0.0, 2.0 * std::numbers::pi);
    state.vel.reserve(static_cast<std::size_t>(p.N));
    for (int i = 0; i < p.N; ++i) {
        const double theta = angle(rng);
        state.vel.push_back(p.v0 * Vec2{std::cos(theta), std::sin(theta)});
    }
    state.method = lattice ? "lattice" : "rsa";
    verifyInitialState(p, state);
    return state;
}

void verifyInitialState(const BilliardParams& p, const InitialState& s) {
    const std::size_t n = static_cast<std::size_t>(p.N);
    if (s.pos.size() != n || s.vel.size() != n) {
        throw std::logic_error("estado inicial: se esperaban " + std::to_string(p.N) +
                               " particulas");
    }
    const double limit = p.R - p.radius;
    const double limit2 = limit * limit;
    const double contact2 = 4.0 * p.radius * p.radius;
    for (std::size_t i = 0; i < n; ++i) {
        const Vec2 r = s.pos[i];
        const Vec2 v = s.vel[i];
        if (!std::isfinite(r.x) || !std::isfinite(r.y) || !std::isfinite(v.x) ||
            !std::isfinite(v.y)) {
            throw std::logic_error("estado inicial: coordenada no finita en la particula " +
                                   std::to_string(i));
        }
        if (norm2(r) > limit2) {
            throw std::logic_error("estado inicial: la particula " + std::to_string(i) +
                                   " sale de la pared");
        }
        if (p.obstacles && (norm2(r - Vec2{-p.x0, 0.0}) < contact2 ||
                            norm2(r - Vec2{p.x0, 0.0}) < contact2)) {
            throw std::logic_error("estado inicial: la particula " + std::to_string(i) +
                                   " solapa un obstaculo");
        }
        if (std::fabs(std::sqrt(norm2(v)) - p.v0) > 1e-12 * p.v0) {
            throw std::logic_error("estado inicial: |v| distinto de v0 en la particula " +
                                   std::to_string(i));
        }
        for (std::size_t j = i + 1; j < n; ++j) {
            if (norm2(r - s.pos[j]) < contact2) {
                throw std::logic_error("estado inicial: solapamiento entre las particulas " +
                                       std::to_string(i) + " y " + std::to_string(j));
            }
        }
    }
}
