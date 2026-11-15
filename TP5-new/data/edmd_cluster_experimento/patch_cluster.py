import re

# ---- edmd.h: declarar el metodo
p = 'src/include/edmd.h'
s = open(p, encoding='utf8').read()
s = s.replace("    void processPair(const EdmdEvent& event);",
              "    void resolveCluster(const std::vector<std::size_t>& seeds, const std::vector<Vector2>& seedPos);\n"
              "    void processPair(const EdmdEvent& event);", 1)
open(p, 'w', encoding='utf8').write(s)

# ---- edmd.cpp
p = 'src/engine/edmd.cpp'
s = open(p, encoding='utf8').read()
if '#include <cstdlib>' not in s:
    s = s.replace('#include <cmath>', '#include <cmath>\n#include <cstdlib>', 1)

helper = '''static bool clusterRule() {
    static const bool on = std::getenv("EDMD_RULE") && std::atoi(std::getenv("EDMD_RULE")) == 3;
    return on;
}

// Experimento: tras un choque se resuelve TODO el grupo de agentes en contacto a la vez. Cada miembro parte
// de su velocidad deseada v_d*e_target y se proyecta (Gauss-Seidel) sobre las velocidades que no acercan a
// ningun par en contacto ni a ninguna pared (aproximacion <= 0, con un margen de 1e-9 m/s).
void EdmdEngine::resolveCluster(const std::vector<std::size_t>& seeds, const std::vector<Vector2>& seedPos) {
    const double tau = config_.sfm.tau;
    const double vd = config_.sfm.desiredSpeed;
    constexpr double band = 1e-6;
    constexpr double margin = 1e-9;
    std::vector<std::size_t> members(seeds.begin(), seeds.end());
    std::vector<Vector2> pos(seedPos.begin(), seedPos.end());
    std::vector<int> slot(records_.size(), -1);
    for (std::size_t k = 0; k < members.size(); ++k) slot[members[k]] = static_cast<int>(k);
    for (std::size_t m = 0; m < members.size(); ++m) {
        const Record& rm = records_[members[m]];
        for (int dy = -1; dy <= 1; ++dy) {
            const int cy = rm.cellY + dy;
            if (cy < 0 || cy >= rows_) continue;
            for (int dx = -1; dx <= 1; ++dx) {
                const int cx = rm.cellX + dx;
                if (cx < 0 || cx >= cols_) continue;
                for (const int jj : cells_[static_cast<std::size_t>(cy) * static_cast<std::size_t>(cols_) +
                                           static_cast<std::size_t>(cx)]) {
                    const std::size_t j = static_cast<std::size_t>(jj);
                    if (slot[j] >= 0 || !records_[j].alive) continue;
                    const Vector2 xj = relaxedPosition(records_[j].motion, now_, tau);
                    if (norm(xj - pos[m]) <= rm.radius + records_[j].radius + band) {
                        slot[j] = static_cast<int>(members.size());
                        members.push_back(j);
                        pos.push_back(xj);
                    }
                }
            }
        }
    }
    struct PairC { std::size_t i, j; Vector2 n; };
    struct WallC { std::size_t i; Vector2 n; };
    std::vector<PairC> pairs;
    std::vector<WallC> walls;
    for (std::size_t i = 0; i < members.size(); ++i) {
        for (std::size_t j = i + 1; j < members.size(); ++j) {
            const Vector2 d = pos[j] - pos[i];
            const double dist = norm(d);
            if (dist > 1e-12 && dist <= records_[members[i]].radius + records_[members[j]].radius + band) {
                pairs.push_back({i, j, d * (1.0 / dist)});
            }
        }
        for (const WallSegment& wall : room_.walls.segments) {
            const Vector2 along = wall.b - wall.a;
            const double sp = std::clamp(dot(pos[i] - wall.a, along) / dot(along, along), 0.0, 1.0);
            const Vector2 d = pos[i] - (wall.a + along * sp);
            const double dist = norm(d);
            if (dist > 1e-12 && dist <= records_[members[i]].radius + band) walls.push_back({i, d * (1.0 / dist)});
        }
    }
    std::vector<Vector2> v(members.size());
    for (std::size_t i = 0; i < members.size(); ++i) {
        const Vector2 toTarget = records_[members[i]].target - pos[i];
        const double d = norm(toTarget);
        v[i] = d < 1e-12 ? Vector2{0.0, 0.0} : toTarget * (vd / d);
    }
    for (int sweep = 0; sweep < 2000; ++sweep) {
        double worst = 0.0;
        for (const PairC& pc : pairs) {
            const double s = dot(v[pc.i] - v[pc.j], pc.n) + margin;  // se quiere (vi - vj).n <= -margin
            if (s > 0.0) {
                v[pc.i] = v[pc.i] - pc.n * (0.5 * s);
                v[pc.j] = v[pc.j] + pc.n * (0.5 * s);
                worst = std::max(worst, s);
            }
        }
        for (const WallC& wc : walls) {
            const double s = margin - dot(v[wc.i], wc.n);
            if (s > 0.0) {
                v[wc.i] = v[wc.i] + wc.n * s;
                worst = std::max(worst, s);
            }
        }
        if (worst < 1e-12) break;
    }
    for (std::size_t k = 0; k < members.size(); ++k) applyCollisionState(members[k], pos[k], v[k]);
    scheduleMoved(members);
}

void EdmdEngine::processPair('''
s = s.replace('void EdmdEngine::processPair(', helper, 1)

# processPair: despues del chequeo de validez, usar el cluster
old = "    const double previous = lastContact(a, event.b);\n"
new = old + '''    if (clusterRule()) {
        const double depthC = separatePair(xa, xb, n, contact, mass, mass);
        result_.maxAgentOverlap = std::max(result_.maxAgentOverlap, depthC);
        ++counters_.collisions;
        if (now_ - previous < config_.eventGap + 1e-12) ++counters_.floorCollisions;
        markContact(a, event.b);
        markContact(b, event.a);
        resolveCluster({a, b}, {xa, xb});
        return;
    }
'''
assert old in s
s = s.replace(old, new, 1)

# finishFixedCollision: pared / esquina
old2 = "    markContact(i, key);\n    applyCollisionState(i, position, velocity);\n"
assert old2 in s
new2 = "    markContact(i, key);\n    if (clusterRule()) {\n        resolveCluster({i}, {position});\n        return;\n    }\n    applyCollisionState(i, position, velocity);\n"
s = s.replace(old2, new2, 1)
open(p, 'w', encoding='utf8').write(s)
print('patched')
