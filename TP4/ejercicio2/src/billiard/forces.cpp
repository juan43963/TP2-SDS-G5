#include <algorithm>
#include <cmath>
#include <stdexcept>
#include <string>

#include "billiard.h"

namespace {

// El indice se acota en double antes del cast a int. El acotado es monotono y
// mueve un indice a lo sumo una celda, asi que los contactos siguen siendo
// exactos aun para particulas fuera de la caja.
int binIndex(double coordinate, double R, double cellSize, int M) {
    const double raw = std::floor((coordinate + R) / cellSize);
    return static_cast<int>(std::clamp(raw, 0.0, static_cast<double>(M) - 1.0));
}

}  // namespace

ForceWorkspace makeForceWorkspace(const BilliardParams& p, int particleCount) {
    ForceWorkspace ws;
    ws.M = cimGridSize(p);
    ws.cellSize = 2.0 * p.R / static_cast<double>(ws.M);
    ws.head.assign(static_cast<std::size_t>(ws.M) * static_cast<std::size_t>(ws.M), -1);
    ws.next.assign(static_cast<std::size_t>(particleCount), -1);
    return ws;
}

void computeForces(const BilliardParams& p, const std::vector<Vec2>& pos, ForceWorkspace& ws,
                   std::vector<Vec2>& force, std::vector<int>& touchingObstacle) {
    const std::size_t n = pos.size();
    force.assign(n, Vec2{});
    touchingObstacle.clear();
    std::fill(ws.head.begin(), ws.head.end(), -1);
    ws.next.assign(n, -1);

    const int M = ws.M;
    for (std::size_t i = 0; i < n; ++i) {
        if (!std::isfinite(pos[i].x) || !std::isfinite(pos[i].y)) {
            throw std::invalid_argument("posicion no finita en la particula " + std::to_string(i));
        }
        const int cx = binIndex(pos[i].x, p.R, ws.cellSize, M);
        const int cy = binIndex(pos[i].y, p.R, ws.cellSize, M);
        const std::size_t cell = static_cast<std::size_t>(cy) * static_cast<std::size_t>(M) +
                                 static_cast<std::size_t>(cx);
        ws.next[i] = ws.head[cell];
        ws.head[cell] = static_cast<int>(i);
    }

    const double contact2 = 4.0 * p.radius * p.radius;
    const double contact = 2.0 * p.radius;

    // F_i = -k * xi * e_ij con e_ij = (r_j - r_i) / |r_j - r_i|: una evaluacion
    // por par no ordenado, aplicada con signo opuesto a cada extremo (Newton 3).
    const auto pairForce = [&](int i, int j) {
        const Vec2 d = pos[static_cast<std::size_t>(j)] - pos[static_cast<std::size_t>(i)];
        const double d2 = norm2(d);
        if (d2 >= contact2) return;
        if (d2 == 0.0) {
            throw std::runtime_error("centros coincidentes entre las particulas " +
                                     std::to_string(i) + " y " + std::to_string(j));
        }
        const double dist = std::sqrt(d2);
        const double xi = contact - dist;
        const Vec2 f = (p.k * xi / dist) * d;
        force[static_cast<std::size_t>(i)] -= f;
        force[static_cast<std::size_t>(j)] += f;
    };

    // Half stencil: la celda propia (solo j posterior en la lista) y 4 vecinas.
    static constexpr int kHalfDx[4] = {1, 1, 0, -1};
    static constexpr int kHalfDy[4] = {0, 1, 1, 1};
    for (int cy = 0; cy < M; ++cy) {
        for (int cx = 0; cx < M; ++cx) {
            const std::size_t cell = static_cast<std::size_t>(cy) * static_cast<std::size_t>(M) +
                                     static_cast<std::size_t>(cx);
            for (int i = ws.head[cell]; i >= 0; i = ws.next[static_cast<std::size_t>(i)]) {
                for (int j = ws.next[static_cast<std::size_t>(i)]; j >= 0;
                     j = ws.next[static_cast<std::size_t>(j)]) {
                    pairForce(i, j);
                }
                for (int s = 0; s < 4; ++s) {
                    const int nx = cx + kHalfDx[s];
                    const int ny = cy + kHalfDy[s];
                    if (nx < 0 || nx >= M || ny < 0 || ny >= M) continue;
                    const std::size_t other = static_cast<std::size_t>(ny) *
                                                  static_cast<std::size_t>(M) +
                                              static_cast<std::size_t>(nx);
                    for (int j = ws.head[other]; j >= 0; j = ws.next[static_cast<std::size_t>(j)]) {
                        pairForce(i, j);
                    }
                }
            }
        }
    }

    // Obstaculos fijos (masa infinita): fuerza solo sobre la particula. Ni los
    // obstaculos ni la pared entran en la grilla.
    if (p.obstacles) {
        const Vec2 centres[2] = {{-p.x0, 0.0}, {p.x0, 0.0}};
        for (std::size_t i = 0; i < n; ++i) {
            bool touching = false;
            for (const Vec2& c : centres) {
                const Vec2 d = c - pos[i];
                const double d2 = norm2(d);
                if (d2 >= contact2) continue;
                const double dist = std::sqrt(d2);
                if (dist == 0.0) {
                    throw std::runtime_error("la particula " + std::to_string(i) +
                                             " coincide con el centro de un obstaculo");
                }
                const double xi = contact - dist;
                force[i] -= (p.k * xi / dist) * d;
                touching = true;
            }
            if (touching) touchingObstacle.push_back(static_cast<int>(i));
        }
    }

    // Pared: resorte contra la particula imagen r_img = (R + r) * n, recalculada
    // en cada llamada. Se escribe en forma cerrada, xi = |r_i| + r - R, para que
    // siga siendo restituyente aun pasado R + r (la forma literal 2r - |r_img - r_i|
    // cambiaria de signo ahi).
    const double wallLimit = p.R - p.radius;
    const double wallLimit2 = wallLimit * wallLimit;
    for (std::size_t i = 0; i < n; ++i) {
        const double r2 = norm2(pos[i]);
        if (r2 <= wallLimit2) continue;
        const double rn = std::sqrt(r2);
        const double xi = rn + p.radius - p.R;
        force[i] -= (p.k * xi / rn) * pos[i];
    }
}
