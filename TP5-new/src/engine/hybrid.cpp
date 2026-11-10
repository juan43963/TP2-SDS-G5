// Esquema hibrido EDMD+TSDMD (D-21 a D-30). Compone runEdmd (frames analiticos entre eventos) y
// runEvacuation (Velocity Verlet con cruce de puerta y retiro): ver la regla de sincronizacion y los
// extremos en hybrid.h. Toda la fisica de trayectoria sale de relaxation.h y de edmd_kernel.h; la
// fuerza de contacto, de forces.cpp.
#include "hybrid.h"

#include <algorithm>
#include <chrono>
#include <cmath>
#include <utility>

#include "edmd_kernel.h"

namespace {

constexpr double kBoundarySlack = 1e-9;  // tolerancia (en pasos) al ubicar el limite de un evento

// w = v_d * e (D-05); con el agente sobre el target se conserva la velocidad. Misma ley que
// forces.cpp y edmd.cpp.
Vector2 desiredOf(const SfmParams& sfm, const Room& room, const Agent& a) {
    const Vector2 target = a.status == AgentStatus::InRoom ? room.doorCenter : room.exitTarget;
    const Vector2 toTarget = target - a.position;
    const double distance = norm(toTarget);
    if (distance < 1e-12) return a.velocity;
    return toTarget * (sfm.desiredSpeed / distance);
}

// Mismo acotado que forces.cpp (binIndex): monotono, nunca agranda la diferencia de indices.
int cellIndex(double coordinate, double cellSize, int M) {
    const double raw = std::floor(coordinate / cellSize);
    return static_cast<int>(std::clamp(raw, 0.0, static_cast<double>(M) - 1.0));
}

bool byId(const Agent& l, const Agent& r) { return l.id < r.id; }

EvacuationConfig validated(const EvacuationConfig& config) {
    validateConfig(config);
    return config;
}

}  // namespace

bool promoteCriterion(double tauC, double T) { return tauC < T; }

bool returnCriterion(double tauC, double T, double alpha, bool touching, double minGap,
                     double closingSpeed) {
    if (touching) return false;
    if (minGap < kNearGap && closingSpeed > kClosingTolerance) return false;
    return tauC > alpha * T;
}

// ---------------------------------------------------------------- construccion

HybridEngine::HybridEngine(const EvacuationConfig& config, std::vector<Agent> agents)
    : config_(validated(config)),
      room_(makeRoom(config.side, config.doorWidth, config.exitDistance)),
      inTsdmd_(agents.size(), 0),
      lastReturnTime_(agents.size(), -kInfinity),
      scanMark_(agents.size(), 0),
      ws_(makeForceWorkspace(config.side, 2.0 * config.radiusMax, agents.size())),
      edmd_(config, std::move(agents), config.hybridT) {
    ws_.trackContacts = true;  // banderas de contacto del paso de fuerzas para el criterio de retorno
    // Estado inicial: los eventos de t = 0 (promociones de agentes que ya van a tocarse) se procesan
    // ahora y, si hay pendientes, el limite 0 hace los pasajes para que el frame de t = 0 ya refleje
    // la clasificacion inicial.
    while (edmd_.nextEventTime() <= 0.0) {
        if (!edmd_.step()) {
            capped_ = true;
            break;
        }
        gatherPromotions();
    }
    if (!pending_.empty()) {
        gridMode_ = true;
        nextBoundary_ = 0;
        runBoundary();
    }
    lastStepWasBoundary_ = false;
}

bool HybridEngine::finished() const {
    return timedOut_ || capped_ || (edmd_.residentCount() == 0 && s_.empty());
}

int HybridEngine::schemeOf(int id) const {
    if (inTsdmd_[static_cast<std::size_t>(id)] != 0) return 0;
    return edmd_.isResident(id) ? 1 : -1;
}

bool HybridEngine::nextIsBoundary() {
    if (!gridMode_) return false;
    return static_cast<double>(nextBoundary_) * config_.dt <= edmd_.nextEventTime();
}

double HybridEngine::nextTime() {
    const double grid = gridMode_ ? static_cast<double>(nextBoundary_) * config_.dt : kInfinity;
    return std::min(edmd_.nextEventTime(), grid);
}

// ---------------------------------------------------------------- avance

void HybridEngine::gatherPromotions() {
    for (const int id : edmd_.takePromotions()) pending_.push_back(id);
    std::sort(pending_.begin(), pending_.end());
    pending_.erase(std::unique(pending_.begin(), pending_.end()), pending_.end());
}

bool HybridEngine::step() {
    lastStepWasBoundary_ = false;
    if (finished()) return false;

    const double tEvent = edmd_.nextEventTime();
    const double tGrid = gridMode_ ? static_cast<double>(nextBoundary_) * config_.dt : kInfinity;
    const double tNext = std::min(tEvent, tGrid);
    if (!std::isfinite(tNext)) return false;
    if (tNext > config_.maxTime) {
        timedOut_ = true;
        return false;
    }

    if (tEvent < tGrid) {
        // D-21: los eventos EDMD con tiempo estrictamente menor que el limite van primero.
        if (!edmd_.step()) {
            capped_ = true;
            return false;
        }
        now_ = std::max(now_, edmd_.now());
        gatherPromotions();
        if (!pending_.empty() && !gridMode_) {
            // El pasaje ocurre en el primer limite igual o posterior al evento.
            gridMode_ = true;
            const long long k = static_cast<long long>(std::ceil(edmd_.now() / config_.dt - kBoundarySlack));
            nextBoundary_ = std::max({nextBoundary_, k, 0LL});
        }
        return true;
    }
    runBoundary();
    lastStepWasBoundary_ = true;
    return true;
}

void HybridEngine::rebuildForces() {
    computeAccelerations(config_.sfm, room_.walls, s_, ws_, stats_);
}

void HybridEngine::promote(int id) {
    Agent agent = edmd_.release(id);
    const auto at = std::lower_bound(s_.begin(), s_.end(), agent, byId);
    s_.insert(at, agent);
    inTsdmd_[static_cast<std::size_t>(id)] = 1;
    ++counters_.promotions;
    // Oscilacion (HYB-02): una promocion a menos de T de su propio retorno es una repromocion rapida.
    if (now_ - lastReturnTime_[static_cast<std::size_t>(id)] < config_.hybridT) ++counters_.quickRepromotions;
}

void HybridEngine::requestPromotionForTesting(int id) {
    pending_.push_back(id);
    std::sort(pending_.begin(), pending_.end());
    pending_.erase(std::unique(pending_.begin(), pending_.end()), pending_.end());
    if (!gridMode_) {
        gridMode_ = true;
        const long long k = static_cast<long long>(std::ceil(std::max(now_, edmd_.now()) / config_.dt - kBoundarySlack));
        nextBoundary_ = std::max({nextBoundary_, k, 0LL});
    }
}

// Un limite de grilla k*dt: integra el subconjunto TSDMD, adelanta el reloj EDMD, cruza la puerta y
// retira, y hace los pasajes (D-21, D-26, D-28, D-29).
// Tope de repeticiones del escaneo de pares mixtos en un limite (cada vuelta promueve al menos un agente).
constexpr int kMaxScanPasses = 16;

void HybridEngine::runBoundary() {
    const long long k = nextBoundary_;
    const double tb = static_cast<double>(k) * config_.dt;

    // a) un paso Velocity Verlet solo del subconjunto TSDMD.
    if (!s_.empty()) {
        stepTsdmd(config_.sfm, room_.walls, s_, ws_, config_.dt, stats_);
        ++counters_.gridSteps;
        counters_.tsdmdAgentSteps += static_cast<long long>(s_.size());
        for (const Agent& a : s_) counters_.maxSpeedSeen = std::max(counters_.maxSpeedSeen, norm(a.velocity));
    }

    // b) todos los eventos EDMD con tiempo menor que tb ya se procesaron.
    edmd_.advanceTo(tb);
    now_ = tb;

    // c) cruce de la puerta y retiro del subconjunto TSDMD, igual que runEvacuation.
    const double halfDoor = config_.doorWidth / 2.0;
    for (Agent& a : s_) {
        if (a.status == AgentStatus::InRoom && a.position.y < 0.0) {
            a.status = AgentStatus::Exiting;
            a.target = room_.exitTarget;
            ++crossed_;
            evacuationTime_ = tb;
            if (std::abs(a.position.x - room_.doorCenter.x) > halfDoor) ++wallBreaches_;
        }
    }
    const std::size_t before = s_.size();
    std::erase_if(s_, [&](const Agent& a) {
        const bool gone = a.status == AgentStatus::Exiting &&
                          norm(a.position - room_.doorCenter) >= room_.exitDistance;
        if (gone) inTsdmd_[static_cast<std::size_t>(a.id)] = 0;
        return gone;
    });
    bool membershipChanged = s_.size() != before;
    if (membershipChanged) {
        removed_ += static_cast<int>(before - s_.size());
        clearTime_ = tb;
    }

    // d) pasajes EDMD -> TSDMD.
    gatherPromotions();
    std::vector<int> promotedNow;
    for (const int id : pending_) {
        if (!edmd_.isResident(id)) continue;
        promote(id);
        promotedNow.push_back(id);
    }
    pending_.clear();

    // d2) escaneo de pares mixtos (D-24, D-25, D-27): en cada limite, todo residente EDMD que va a
    // tocar a un agente TSDMD dentro de T (o ya lo toca) pasa a TSDMD antes del contacto. Los recien
    // promovidos ya estan en s_. Un agente promovido por este mismo escaneo puede ser a su vez el
    // TSDMD que un vecino residente va a tocar dentro de T: se repite el escaneo hasta que no haya
    // mas promociones (punto fijo, acotado), asi ningun contacto previsto dentro de T queda para el
    // limite siguiente.
    for (int pass = 0; pass < kMaxScanPasses; ++pass) {
        const std::vector<int> found = scanMixedPairs();
        if (found.empty()) break;
        for (const int id : found) {
            promote(id);
            ++counters_.mixedPromotions;
            promotedNow.push_back(id);
        }
    }
    std::sort(promotedNow.begin(), promotedNow.end());
    if (membershipChanged || !promotedNow.empty()) rebuildForces();

    // e) pasajes TSDMD -> EDMD, uno por vez en orden de id: cada retorno se aplica (y la grilla de
    // fuerzas se reconstruye) antes de decidir el siguiente. Asi dos vecinos que se estan por separar
    // se evaluan con el modelo del EDMD (relajacion de ambos), el mismo que usara el motor al
    // programar sus eventos; decidirlos a la vez con el vecino TSDMD a velocidad constante
    // reprogramaba un aviso Promote inmediato y los dos agentes oscilaban entre esquemas en cada paso.
    std::vector<int> candidates;
    candidates.reserve(s_.size());
    for (const Agent& a : s_) {
        if (!std::binary_search(promotedNow.begin(), promotedNow.end(), a.id)) candidates.push_back(a.id);
    }
    for (const int id : candidates) {
        const auto at = std::lower_bound(s_.begin(), s_.end(), id,
                                         [](const Agent& a, int value) { return a.id < value; });
        if (!tryReturn(static_cast<std::size_t>(at - s_.begin()))) continue;
        const Agent agent = *at;
        s_.erase(at);
        inTsdmd_[static_cast<std::size_t>(id)] = 0;
        edmd_.admit(agent);
        lastReturnTime_[static_cast<std::size_t>(id)] = tb;
        ++counters_.returns;
        rebuildForces();
    }

    // f) siguiente limite; con el subconjunto vacio y sin pendientes el reloj vuelve a saltar (D-22).
    lastBoundary_ = k;
    ++nextBoundary_;
    if (s_.empty() && pending_.empty()) gridMode_ = false;
}

// ---------------------------------------------------------------- criterio de retorno

// Huelgo, contacto y velocidad de acercamiento del agente `index` contra sus vecinos TSDMD de las
// 3x3 celdas de ws_ y contra paredes y esquinas (D-29). Usa la grilla de la ultima computeAccelerations.
HybridEngine::Proximity HybridEngine::proximityOf(std::size_t index) const {
    Proximity p;
    const Agent& a = s_[index];
    const auto consider = [&](double gap, double closing) {
        if (gap <= 0.0) p.touching = true;
        p.minGap = std::min(p.minGap, gap);
        if (gap < kNearGap) p.closingSpeed = std::max(p.closingSpeed, closing);
    };

    const int M = ws_.M;
    const int cx0 = cellIndex(a.position.x, ws_.cellSize, M);
    const int cy0 = cellIndex(a.position.y, ws_.cellSize, M);
    for (int cy = std::max(0, cy0 - 1); cy <= std::min(M - 1, cy0 + 1); ++cy) {
        for (int cx = std::max(0, cx0 - 1); cx <= std::min(M - 1, cx0 + 1); ++cx) {
            const std::size_t cell = static_cast<std::size_t>(cy) * static_cast<std::size_t>(M) +
                                     static_cast<std::size_t>(cx);
            for (int j = ws_.head[cell]; j >= 0; j = ws_.next[static_cast<std::size_t>(j)]) {
                if (static_cast<std::size_t>(j) == index) continue;
                const Agent& b = s_[static_cast<std::size_t>(j)];
                const Vector2 d = b.position - a.position;
                const double dist = norm(d);
                const double gap = dist - (a.radius + b.radius);
                if (dist < 1e-12) {
                    consider(gap, 0.0);
                    p.touching = true;
                    continue;
                }
                const Vector2 n = d * (1.0 / dist);
                consider(gap, -dot(b.velocity - a.velocity, n));
            }
        }
    }

    // Paredes y bordes de puerta (los extremos acotados de los tramos son las esquinas).
    for (const WallSegment& wall : room_.walls.segments) {
        const Vector2 ab = wall.b - wall.a;
        const double len2 = normSquared(ab);
        const double s = len2 > 0.0 ? std::clamp(dot(a.position - wall.a, ab) / len2, 0.0, 1.0) : 0.0;
        const Vector2 delta = a.position - (wall.a + ab * s);
        const double dist = norm(delta);
        const double gap = dist - a.radius;
        if (dist < 1e-12) {
            p.touching = true;
            p.minGap = std::min(p.minGap, gap);
            continue;
        }
        consider(gap, -dot(a.velocity, delta * (1.0 / dist)));
    }
    return p;
}

// Escaneo de pares mixtos (D-24, D-25, D-26, D-27). Para cada agente j de TSDMD se recorren los
// residentes EDMD de las 3x3 celdas del motor EDMD alrededor de j: la celda mide al menos
// 2 r_max + kLeadRelativeSpeedFactor v_d T, asi que la ventana cubre todo contacto posible dentro de T.
// Un residente i se promueve si ya toca o se solapa con j (huelgo <= 0: red de seguridad) o si,
// pasado el filtro de distancia solido (el acercamiento de i en T esta acotado por
// max(|v_i|, v_d) T y el de j, a velocidad constante, por |v_j| T), el tiempo de contacto exacto
// de i con j extrapolado a velocidad constante es menor que T. La extrapolacion es la correcta para
// pilas: un agente comprimido tiene v cercana a 0, no v_d.
std::vector<int> HybridEngine::scanMixedPairs() {
    std::vector<int> marked;
    if (!mixedScanEnabled_ || s_.empty() || edmd_.residentCount() == 0) return marked;
    const double T = config_.hybridT;
    const double vd = config_.sfm.desiredSpeed;
    for (const Agent& j : s_) {
        const double speedJ = norm(j.velocity);
        const Relaxation body{j.position, j.velocity, j.velocity, edmd_.now()};
        const int cx0 = edmd_.cellCoordX(j.position.x);
        const int cy0 = edmd_.cellCoordY(j.position.y);
        for (int cy = cy0 - 1; cy <= cy0 + 1; ++cy) {
            for (int cx = cx0 - 1; cx <= cx0 + 1; ++cx) {
                for (const int i : edmd_.cellResidents(cx, cy)) {
                    if (scanMark_[static_cast<std::size_t>(i)] != 0) continue;
                    const Relaxation m = edmd_.motionOf(i);
                    const double gap = norm(j.position - m.x0) - (edmd_.radiusOf(i) + j.radius);
                    bool promoteIt = gap <= 0.0;
                    if (!promoteIt && gap <= (std::max(norm(m.v0), vd) + speedJ) * T) {
                        promoteIt = edmd_.contactTimeWithBody(i, body, j.radius, T) < T;
                    }
                    if (promoteIt) {
                        scanMark_[static_cast<std::size_t>(i)] = 1;
                        marked.push_back(i);
                    }
                }
            }
        }
    }
    for (const int i : marked) scanMark_[static_cast<std::size_t>(i)] = 0;
    std::sort(marked.begin(), marked.end());
    return marked;
}

// Primer contacto con aproximacion contra los vecinos TSDMD, dentro de `horizon`: el agente sigue
// su movimiento libre (relajacion a v_d) y el vecino se extrapola a velocidad constante. Ventana de
// `rings` celdas de ws_ a cada lado (la extension de una celda EDMD, acotada a 4: lo que quede mas
// lejos lo atrapa el escaneo de pares mixtos cuando se acerque) y filtro de distancia solido.
double HybridEngine::tsdmdContactTime(std::size_t index, double horizon) const {
    const double tau = config_.sfm.tau;
    const double vd = config_.sfm.desiredSpeed;
    const Agent& a = s_[index];
    const int M = ws_.M;
    const int rings = std::clamp(static_cast<int>(std::ceil(edmd_.cellSize() / ws_.cellSize)), 1, 4);
    const int cx0 = cellIndex(a.position.x, ws_.cellSize, M);
    const int cy0 = cellIndex(a.position.y, ws_.cellSize, M);
    const Vector2 wa = desiredOf(config_.sfm, room_, a);
    const double speedA = std::max(norm(a.velocity), vd);

    double best = kInfinity;
    for (int cy = std::max(0, cy0 - rings); cy <= std::min(M - 1, cy0 + rings); ++cy) {
        for (int cx = std::max(0, cx0 - rings); cx <= std::min(M - 1, cx0 + rings); ++cx) {
            const std::size_t cell = static_cast<std::size_t>(cy) * static_cast<std::size_t>(M) +
                                     static_cast<std::size_t>(cx);
            for (int j = ws_.head[cell]; j >= 0; j = ws_.next[static_cast<std::size_t>(j)]) {
                if (static_cast<std::size_t>(j) == index) continue;
                const Agent& b = s_[static_cast<std::size_t>(j)];
                const double gap = norm(b.position - a.position) - (a.radius + b.radius);
                const double speedB = std::max(norm(b.velocity), vd);
                if (gap > (speedA + speedB) * std::min(horizon, best)) continue;
                Relaxation rel;
                rel.x0 = b.position - a.position;
                rel.v0 = b.velocity - a.velocity;
                rel.w = b.velocity - wa;  // vecino a velocidad constante (w = v)
                rel.t0 = 0.0;
                best = std::min(best, firstBallApproach(rel, a.radius + b.radius, tau, 0.0,
                                                        std::min(horizon, best)));
                // Tambien el vecino relajando a su velocidad deseada: es el modelo con el que el motor EDMD
                // programa los avisos del par (los dos agentes en EDMD). Un retorno que solo viera el
                // vecino a velocidad constante podia ver un par ya avisado como libre y el agente volvia
                // a EDMD un limite despues de su promocion (oscilacion, HYB-02). El retorno exige que
                // ambos modelos dejen el contacto mas alla de alpha*T.
                rel.w = desiredOf(config_.sfm, room_, b) - wa;
                best = std::min(best, firstBallApproach(rel, a.radius + b.radius, tau, 0.0,
                                                        std::min(horizon, best)));
            }
        }
    }
    return best;
}

// D-28, D-29: el agente `index` vuelve a EDMD si no toca nada, no colapsa y su proximo contacto
// (paredes, esquinas, residentes EDMD y vecinos TSDMD) esta mas alla de alpha*T. El contacto sale de
// las banderas del paso de fuerzas (ws_.touching: agentes, paredes, esquinas); la evaluacion es en
// cada limite (D-27), con salida temprana por contacto y por los descartes baratos.
bool HybridEngine::tryReturn(std::size_t index) {
    if (returnGuard_ && index < ws_.touching.size() && ws_.touching[index] != 0) return false;
    Proximity p = proximityOf(index);
    if (!returnGuard_) {
        // Control negativo (D-29): sin contacto, huelgo ni colapso que impidan el retorno.
        p.touching = false;
        p.minGap = kInfinity;
        p.closingSpeed = 0.0;
    }
    // Descartes baratos primero: el tau_c solo se calcula si el resto del criterio ya se cumple.
    if (!returnCriterion(kInfinity, config_.hybridT, config_.hybridAlpha, p.touching, p.minGap,
                         p.closingSpeed)) {
        return false;
    }
    const double window = config_.hybridAlpha * config_.hybridT;
    double tauC = edmd_.freeContactTime(s_[index], window);
    if (!(tauC > window)) return false;
    tauC = std::min(tauC, tsdmdContactTime(index, window));
    return returnCriterion(tauC, config_.hybridT, config_.hybridAlpha, p.touching, p.minGap,
                           p.closingSpeed);
}

// ---------------------------------------------------------------- salida

std::vector<Agent> HybridEngine::snapshot(double time) const {
    std::vector<Agent> frame = edmd_.snapshot(time);
    for (const Agent& a : s_) {
        Agent copy = a;
        copy.scheme = 0;
        frame.push_back(copy);
    }
    std::sort(frame.begin(), frame.end(), byId);
    return frame;
}

EvacuationResult HybridEngine::result() const {
    EvacuationResult r = edmd_.result();
    r.crossed += crossed_;
    r.removed += removed_;
    r.wallBreaches += wallBreaches_;
    r.evacuationTime = std::max(r.evacuationTime, evacuationTime_);
    r.clearTime = std::max(r.clearTime, clearTime_);
    r.maxAgentOverlap = std::max(r.maxAgentOverlap, stats_.maxAgentOverlap);
    r.maxWallOverlap = std::max(r.maxWallOverlap, stats_.maxWallOverlap);
    for (const Agent& a : s_) {
        if (a.status == AgentStatus::InRoom) ++r.inRoomFinal;
    }
    r.completed = edmd_.residentCount() == 0 && s_.empty();
    r.finalTime = r.completed ? r.clearTime : (capped_ ? now_ : config_.maxTime);
    r.steps = counters_.gridSteps;
    r.hybridPromotions = counters_.promotions;
    r.hybridReturns = counters_.returns;
    r.hybridSteps = counters_.gridSteps;
    r.tsdmdAgentSteps = counters_.tsdmdAgentSteps;
    r.hybridMixedPromotions = counters_.mixedPromotions;
    r.hybridQuickRepromotions = counters_.quickRepromotions;
    return r;
}

// ---------------------------------------------------------------- corrida completa

EvacuationResult runHybrid(const EvacuationConfig& config, std::vector<Agent> agents,
                           const FrameSink& sink) {
    using Clock = std::chrono::steady_clock;
    validateConfig(config);

    // D-23, HYB-05: los extremos de T son los esquemas puros, exactamente.
    if (config.hybridT <= 0.0) return runEdmd(config, std::move(agents), sink);
    if (config.hybridT >= config.maxTime) return runEvacuation(config, std::move(agents), sink);

    HybridEngine engine(config, std::move(agents));
    const long long stepsPerFrame = std::llround(config.dt2 / config.dt);
    double outputSeconds = 0.0;
    const auto emit = [&](double label, double evalTime) {
        if (!sink) return;
        const auto t0 = Clock::now();
        sink(label, engine.snapshot(evalTime));
        outputSeconds += std::chrono::duration<double>(Clock::now() - t0).count();
    };

    // D-30: frames en k*dt2 con contador entero. Con el subconjunto TSDMD vacio un frame es la
    // evaluacion analitica del EDMD (como runEdmd); con TSDMD activo solo se emiten en los limites
    // de grilla que son multiplos de dt2. `boundaryLimit` >= 0 corta por indice entero los frames
    // que pertenecen al limite que sigue (los emite ese limite, nunca dos veces).
    long long nextFrame = 1;
    double lastEmitted = 0.0;
    const auto flush = [&](double limit, bool inclusive, long long boundaryLimit) {
        for (;;) {
            const double f = static_cast<double>(nextFrame) * config.dt2;
            if (!(inclusive ? f <= limit : f < limit)) break;
            if (boundaryLimit >= 0 && nextFrame * stepsPerFrame >= boundaryLimit) break;
            emit(f, f);
            lastEmitted = f;
            ++nextFrame;
        }
    };

    const auto loopStart = Clock::now();
    emit(0.0, 0.0);
    while (!engine.finished()) {
        const double next = engine.nextTime();
        if (!std::isfinite(next) || next > config.maxTime) break;
        if (engine.tsdmdCount() == 0) {
            flush(next, false, engine.nextIsBoundary() ? engine.nextBoundaryIndex() : -1);
        }
        if (!engine.step()) break;
        if (engine.lastStepWasBoundary() && engine.boundaryIndex() % stepsPerFrame == 0) {
            const long long frame = engine.boundaryIndex() / stepsPerFrame;
            const double f = static_cast<double>(frame) * config.dt2;
            emit(f, engine.now());
            lastEmitted = f;
            nextFrame = frame + 1;
        }
    }

    EvacuationResult result = engine.result();
    if (engine.tsdmdCount() == 0) {
        flush(result.finalTime, true, -1);
        if (lastEmitted < result.finalTime) emit(result.finalTime, result.finalTime);
    } else if (lastEmitted < result.finalTime) {
        // Corrida cortada con agentes en TSDMD: su estado vigente es el del ultimo limite.
        emit(result.finalTime, engine.now());
    }
    const double totalSeconds = std::chrono::duration<double>(Clock::now() - loopStart).count();

    result.outputMs = outputSeconds * 1e3;
    result.simulationMs = (totalSeconds - outputSeconds) * 1e3;
    return result;
}
