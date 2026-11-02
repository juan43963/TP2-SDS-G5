// Motor EDMD (D-13 a D-20). Heap global con contador de generacion por agente: cola y
// comparador de TP3 (event.h, simulation.cpp). Toda la fisica de trayectoria sale de
// relaxation.h y todos los tiempos de contacto del kernel (edmd_kernel.h); este archivo solo
// decide QUE eventos se programan (celdas, piso de tiempo) y como se procesan.
#include "edmd.h"

#include <algorithm>
#include <chrono>
#include <cmath>
#include <utility>

#include "edmd_kernel.h"

namespace {

constexpr double kProcessSlack = 1e-6;  // [m] holgura de la verificacion al procesar un contacto
// Contacto en reposo: una velocidad normal de aproximacion nula a precision de maquina no es un
// evento inaplicable; se resuelve igual (separacion + piso de tiempo) sin cambiar la velocidad.
constexpr double kRestingSlack = 1e-9;  // [m/s]
// Proyeccion de solapes en cadena (relaxOverlaps): tolerancia (1 mm, 1% del menor radio, muy por
// debajo del umbral de 0.09 m) y presupuesto de vueltas por colision.
constexpr double kProjectionTolerance = 1e-3;  // [m] (piso del tope --overlap-cap)
constexpr int kProjectionBudget = 128;

// w = v_d * e (D-05); con el agente sobre el target se conserva la velocidad.
Vector2 desiredVelocity(const SfmParams& sfm, Vector2 position, Vector2 target, Vector2 fallback) {
    const Vector2 toTarget = target - position;
    const double distance = norm(toTarget);
    if (distance < 1e-12) return fallback;
    return toTarget * (sfm.desiredSpeed / distance);
}

// Normal unitaria del tramo orientada hacia el lado `side` (la misma convencion del kernel).
Vector2 wallNormal(const WallSegment& wall, int side) {
    const Vector2 along = wall.b - wall.a;
    const double length = norm(along);
    const Vector2 tangent = along * (1.0 / length);
    return Vector2{-tangent.y, tangent.x} * (side >= 0 ? 1.0 : -1.0);
}

bool isPhysical(EventType type) {
    return type == EventType::PairContact || type == EventType::WallContact ||
           type == EventType::CornerContact || type == EventType::DoorCross ||
           type == EventType::Retire;
}

}  // namespace

// ---------------------------------------------------------------- construccion

EdmdEngine::EdmdEngine(const EvacuationConfig& config, std::vector<Agent> agents, double leadTime)
    : config_(config), leadTime_(leadTime) {
    validateConfig(config_);
    room_ = makeRoom(config_.side, config_.doorWidth, config_.exitDistance);

    double radiusMax = config_.radiusMax;
    records_.reserve(agents.size());
    for (const Agent& a : agents) {
        Record r;
        r.id = a.id;
        r.radius = a.radius;
        r.status = a.status;
        r.target = a.status == AgentStatus::InRoom ? room_.doorCenter : room_.exitTarget;
        r.motion.x0 = a.position;
        r.motion.v0 = a.velocity;
        r.motion.w = desiredVelocity(config_.sfm, a.position, r.target, a.velocity);
        r.motion.t0 = 0.0;
        radiusMax = std::max(radiusMax, a.radius);
        records_.push_back(r);
    }
    alive_ = static_cast<int>(records_.size());
    movedMask_.assign(records_.size(), 0);

    // Grilla de celdas (D-18): cellSize mayor que cualquier distancia de contacto.
    // Modo con anticipacion: la celda crece con el camino que puede recorrer la velocidad relativa
    // de aproximacion en leadTime, para que el aviso Promote llegue con el adelanto completo.
    cellSize_ = 2.0 * radiusMax + 1e-6;
    if (leadTime_ > 0.0) {
        cellSize_ += kLeadRelativeSpeedFactor * config_.sfm.desiredSpeed * leadTime_;
    }
    const double pad = config_.exitDistance + 2.0 * radiusMax;
    originX_ = -pad;
    originY_ = -pad;
    cols_ = std::max(1, static_cast<int>(std::ceil((config_.side + 2.0 * pad) / cellSize_)));
    rows_ = cols_;
    cells_.assign(static_cast<std::size_t>(cols_) * static_cast<std::size_t>(rows_), {});

    compactBase_ = std::max<std::size_t>(4096, 64 * records_.size());
    compactLimit_ = compactBase_;

    for (std::size_t i = 0; i < records_.size(); ++i) {
        records_[i].cellX = cellCoordX(records_[i].motion.x0.x);
        records_[i].cellY = cellCoordY(records_[i].motion.x0.y);
        cellInsert(i);
    }
    for (std::size_t i = 0; i < records_.size(); ++i) scheduleAgent(i, -1, true);
}

// ---------------------------------------------------------------- cola

void EdmdEngine::push(EdmdEvent event) {
    event.sequence = sequence_++;
    heap_.push_back(event);
    std::push_heap(heap_.begin(), heap_.end(), EventLater{});
}

EdmdEvent EdmdEngine::makeEvent(EventType type, double time, int a, int b) const {
    EdmdEvent event;
    event.type = type;
    event.time = time;
    event.a = a;
    event.b = b;
    event.generationA = records_[static_cast<std::size_t>(a)].collisionCount;
    if (type == EventType::PairContact || (type == EventType::Promote && b >= 0)) {
        event.generationB = records_[static_cast<std::size_t>(b)].collisionCount;
    }
    return event;
}

bool EdmdEngine::isValid(const EdmdEvent& event) const {
    const Record& a = records_[static_cast<std::size_t>(event.a)];
    if (!a.alive || a.collisionCount != event.generationA) return false;
    if (event.type == EventType::PairContact || (event.type == EventType::Promote && event.b >= 0)) {
        const Record& b = records_[static_cast<std::size_t>(event.b)];
        if (!b.alive || b.collisionCount != event.generationB) return false;
    }
    return true;
}

// Reconstruye el heap con solo los eventos validos (T-07-03).
void EdmdEngine::compact() {
    std::erase_if(heap_, [this](const EdmdEvent& e) { return !isValid(e); });
    std::make_heap(heap_.begin(), heap_.end(), EventLater{});
    ++counters_.compactions;
    compactLimit_ = std::max(compactBase_, 2 * heap_.size());
}

double EdmdEngine::nextEventTime() {
    while (!heap_.empty()) {
        if (isValid(heap_.front())) return heap_.front().time;
        std::pop_heap(heap_.begin(), heap_.end(), EventLater{});
        heap_.pop_back();
        ++counters_.stale;
    }
    return kInfinity;
}

bool EdmdEngine::finished() const { return alive_ == 0 || timedOut_ || capped_ || heap_.empty(); }

// ---------------------------------------------------------------- estado por agente

Relaxation EdmdEngine::stateOf(std::size_t index, double time) const {
    const Record& r = records_[index];
    const double tau = config_.sfm.tau;
    Relaxation s;
    s.x0 = relaxedPosition(r.motion, time, tau);
    s.v0 = relaxedVelocity(r.motion, time, tau);
    s.w = r.motion.w;
    s.t0 = time;
    return s;
}

// Estado exacto del agente en now_ pasa a ser el nuevo origen de su trayectoria.
void EdmdEngine::sync(std::size_t index) {
    Record& r = records_[index];
    r.motion = stateOf(index, now_);
}

// Cambia de target (el agente debe estar sincronizado): w se recalcula desde su posicion.
void EdmdEngine::retarget(std::size_t index, Vector2 target) {
    Record& r = records_[index];
    r.target = target;
    r.motion.w = desiredVelocity(config_.sfm, r.motion.x0, target, r.motion.v0);
}

Vector2 EdmdEngine::desiredFrom(const Record& r, Vector2 position, Vector2 fallback) const {
    return desiredVelocity(config_.sfm, position, r.target, fallback);
}

// Tras una colision: nueva posicion/velocidad, w recalculada, piso de tiempo y generacion.
void EdmdEngine::applyCollisionState(std::size_t index, Vector2 position, Vector2 velocity) {
    Record& r = records_[index];
    r.motion.x0 = position;
    r.motion.v0 = velocity;
    r.motion.w = desiredFrom(r, position, velocity);
    r.motion.t0 = now_;
    ++r.collisionCount;
    cellRelocate(index);
}

// ---------------------------------------------------------------- celdas

int EdmdEngine::cellCoordX(double x) const {
    const int c = static_cast<int>(std::floor((x - originX_) / cellSize_));
    return std::clamp(c, 0, cols_ - 1);
}

int EdmdEngine::cellCoordY(double y) const {
    const int c = static_cast<int>(std::floor((y - originY_) / cellSize_));
    return std::clamp(c, 0, rows_ - 1);
}

void EdmdEngine::cellInsert(std::size_t index) {
    const Record& r = records_[index];
    cells_[static_cast<std::size_t>(r.cellY) * static_cast<std::size_t>(cols_) +
           static_cast<std::size_t>(r.cellX)]
        .push_back(static_cast<int>(index));
}

void EdmdEngine::cellErase(std::size_t index) {
    const Record& r = records_[index];
    std::vector<int>& cell = cells_[static_cast<std::size_t>(r.cellY) * static_cast<std::size_t>(cols_) +
                                    static_cast<std::size_t>(r.cellX)];
    const auto it = std::find(cell.begin(), cell.end(), static_cast<int>(index));
    if (it == cell.end()) return;
    *it = cell.back();
    cell.pop_back();
}

// Reasigna la celda segun la posicion actual (la separacion de solapes puede moverla).
void EdmdEngine::cellRelocate(std::size_t index) {
    Record& r = records_[index];
    const int cx = cellCoordX(r.motion.x0.x);
    const int cy = cellCoordY(r.motion.x0.y);
    if (cx == r.cellX && cy == r.cellY) return;
    cellErase(index);
    r.cellX = cx;
    r.cellY = cy;
    cellInsert(index);
}

// ---------------------------------------------------------------- tiempos de evento

// Piso de tiempo anti colapso inelastico (D-16), POR CONTACTO: una colision del mismo par /
// pared / esquina no puede repetirse antes de `eventGap`. Un piso por agente dejaba a los
// contactos de un agente atrapado entre varios vecinos sin servicio (solapes de 0.3 m).
double EdmdEngine::lastContact(std::size_t i, int key) const {
    for (const auto& entry : records_[i].contacts) {
        if (entry.first == key) return entry.second;
    }
    return -kInfinity;
}

void EdmdEngine::markContact(std::size_t i, int key) {
    auto& list = records_[i].contacts;
    const double gap = config_.eventGap;
    const double now = now_;
    std::erase_if(list, [&](const std::pair<int, double>& e) { return e.first != key && e.second + gap <= now; });
    for (auto& entry : list) {
        if (entry.first == key) {
            entry.second = now;
            return;
        }
    }
    list.emplace_back(key, now);
}

double EdmdEngine::floorStart(std::size_t i, int key) const {
    return lastContact(i, key) + config_.eventGap;
}

// Primer contacto con aproximacion del par desde tStart = max(now_, pisos de i y j, notBefore).
double EdmdEngine::pairEventTime(std::size_t i, std::size_t j, double notBefore) const {
    const Record& a = records_[i];
    const Record& b = records_[j];
    const double tau = config_.sfm.tau;
    const Relaxation sa = stateOf(i, now_);
    const Relaxation sb = stateOf(j, now_);
    Relaxation rel;
    rel.x0 = sb.x0 - sa.x0;
    rel.v0 = sb.v0 - sa.v0;
    rel.w = sb.w - sa.w;
    rel.t0 = now_;
    const double tStart = std::max({now_, notBefore, floorStart(i, static_cast<int>(j))});
    return firstBallApproach(rel, a.radius + b.radius, tau, tStart, config_.maxTime);
}

int EdmdEngine::wallSide(std::size_t i, std::size_t segment) const {
    const WallSegment& wall = room_.walls.segments[segment];
    const Vector2 x = relaxedPosition(records_[i].motion, now_, config_.sfm.tau);
    const double signedDistance = dot(wallNormal(wall, +1), x - wall.a);
    return signedDistance < 0.0 ? -1 : +1;
}

double EdmdEngine::wallEventTime(std::size_t i, std::size_t segment, int side) const {
    const Record& r = records_[i];
    const double tStart = std::max(now_, floorStart(i, -1 - static_cast<int>(2 * segment) - (side < 0 ? 1 : 0)));
    return wallContactTime(r.motion, r.radius, room_.walls.segments[segment], side, config_.sfm.tau,
                           tStart, config_.maxTime);
}

// Esquina de la puerta: punto fijo de radio 0 y masa infinita (D-15).
double EdmdEngine::cornerEventTime(std::size_t i, std::size_t corner) const {
    const Record& r = records_[i];
    Relaxation rel = r.motion;
    rel.x0 = rel.x0 - room_.walls.corners[corner];
    const double tStart = std::max(now_, floorStart(i, -100 - static_cast<int>(corner)));
    return firstBallApproach(rel, r.radius, config_.sfm.tau, tStart, config_.maxTime);
}

double EdmdEngine::doorOrRetireTime(std::size_t i) const {
    const Record& r = records_[i];
    const double tau = config_.sfm.tau;
    if (r.status == AgentStatus::InRoom) {
        // Cruce de la linea de la puerta y = 0; el offset -tolerancia compensa la banda del
        // kernel para que la llegada sea exactamente y = 0.
        return firstPlaneCrossing(r.motion, {0.0, 1.0}, -kContactTolerance, tau, now_, config_.maxTime);
    }
    // Retiro a exitDistance del centro de la puerta (movimiento de x - P).
    Relaxation rel = r.motion;
    rel.x0 = rel.x0 - room_.doorCenter;
    return firstBallExit(rel, room_.exitDistance, tau, now_, config_.maxTime);
}

// ---------------------------------------------------------------- programacion

// Modo con anticipacion (D-25): el contacto no se resuelve aca; se avisa leadTime antes (o ya, si
// falta menos) para que el hibrido pase al agente a TSDMD y lo resuelva el resorte SFM (D-24).
void EdmdEngine::pushContact(EventType type, double time, int a, int b) {
    if (leadTime_ > 0.0) {
        push(makeEvent(EventType::Promote, std::max(now_, time - leadTime_), a,
                       type == EventType::PairContact ? b : -1));
    } else {
        push(makeEvent(type, time, a, b));
    }
}

void EdmdEngine::pushPair(std::size_t i, std::size_t j, double notBefore) {
    const double t = pairEventTime(i, j, notBefore);
    if (std::isfinite(t)) {
        pushContact(EventType::PairContact, t, static_cast<int>(i), static_cast<int>(j));
    }
}

// Proxima frontera de celda que cruza el agente (hasta cuatro llamadas al kernel).
void EdmdEngine::pushCellCross(std::size_t i) {
    const Record& r = records_[i];
    const double tau = config_.sfm.tau;
    const double xLo = originX_ + r.cellX * cellSize_;
    const double xHi = originX_ + (r.cellX + 1) * cellSize_;
    const double yLo = originY_ + r.cellY * cellSize_;
    const double yHi = originY_ + (r.cellY + 1) * cellSize_;

    double best = kInfinity;
    int code = -1;
    const auto consider = [&](int c, Vector2 normal, double offset) {
        const double t = firstPlaneCrossing(r.motion, normal, offset, tau, now_, config_.maxTime);
        if (t < best) {
            best = t;
            code = c;
        }
    };
    if (r.cellX > 0) consider(0, {1.0, 0.0}, xLo);
    if (r.cellX < cols_ - 1) consider(1, {-1.0, 0.0}, -xHi);
    if (r.cellY > 0) consider(2, {0.0, 1.0}, yLo);
    if (r.cellY < rows_ - 1) consider(3, {0.0, -1.0}, -yHi);
    if (code >= 0 && std::isfinite(best)) {
        push(makeEvent(EventType::CellCross, best, static_cast<int>(i), code));
    }
}

void EdmdEngine::pushNeighborPairs(std::size_t i, int skip, bool onlyHigher) {
    const Record& r = records_[i];
    for (int dy = -1; dy <= 1; ++dy) {
        const int cy = r.cellY + dy;
        if (cy < 0 || cy >= rows_) continue;
        for (int dx = -1; dx <= 1; ++dx) {
            const int cx = r.cellX + dx;
            if (cx < 0 || cx >= cols_) continue;
            const std::vector<int>& cell =
                cells_[static_cast<std::size_t>(cy) * static_cast<std::size_t>(cols_) +
                       static_cast<std::size_t>(cx)];
            for (const int j : cell) {
                if (j == static_cast<int>(i) || j == skip) continue;
                if (onlyHigher && j < static_cast<int>(i)) continue;
                // Entre dos agentes movidos el par se programa una sola vez (desde el menor).
                if (movedMask_[static_cast<std::size_t>(j)] != 0 && j < static_cast<int>(i)) continue;
                if (!records_[static_cast<std::size_t>(j)].alive) continue;
                pushPair(i, static_cast<std::size_t>(j), 0.0);
            }
        }
    }
}

// Programa todos los eventos del agente `i` con su trayectoria vigente (D-18).
void EdmdEngine::scheduleAgent(std::size_t i, int skip, bool onlyHigher) {
    const Record& r = records_[i];
    if (!r.alive) return;
    const int index = static_cast<int>(i);

    const double door = doorOrRetireTime(i);
    if (std::isfinite(door)) {
        push(makeEvent(r.status == AgentStatus::InRoom ? EventType::DoorCross : EventType::Retire, door,
                       index, -1));
    }

    for (std::size_t k = 0; k < room_.walls.segments.size(); ++k) {
        const int side = wallSide(i, k);
        const double t = wallEventTime(i, k, side);
        if (std::isfinite(t)) {
            pushContact(EventType::WallContact, t, index, static_cast<int>(2 * k) + (side < 0 ? 1 : 0));
        }
    }
    for (std::size_t c = 0; c < room_.walls.corners.size(); ++c) {
        const double t = cornerEventTime(i, c);
        if (std::isfinite(t)) pushContact(EventType::CornerContact, t, index, static_cast<int>(c));
    }

    pushCellCross(i);

    const Relaxation now = stateOf(i, now_);
    if (!isSettled(now, 1e-6 * config_.sfm.desiredSpeed) && now_ + config_.steerInterval <= config_.maxTime) {
        push(makeEvent(EventType::Steer, now_ + config_.steerInterval, index, -1));
    }

    pushNeighborPairs(i, skip, onlyHigher);
}

// ---------------------------------------------------------------- procesamiento

void EdmdEngine::processPair(const EdmdEvent& event) {
    const std::size_t a = static_cast<std::size_t>(event.a);
    const std::size_t b = static_cast<std::size_t>(event.b);
    Record& ra = records_[a];
    Record& rb = records_[b];
    const double tau = config_.sfm.tau;
    const double mass = config_.sfm.mass;

    Vector2 xa = relaxedPosition(ra.motion, now_, tau);
    Vector2 xb = relaxedPosition(rb.motion, now_, tau);
    Vector2 va = relaxedVelocity(ra.motion, now_, tau);
    Vector2 vb = relaxedVelocity(rb.motion, now_, tau);
    const Vector2 delta = xb - xa;
    const double distance = norm(delta);
    const double contact = ra.radius + rb.radius;
    const bool degenerate = distance < 1e-12;
    const Vector2 n = degenerate ? Vector2{1.0, 0.0} : delta * (1.0 / distance);
    const double u = dot(va - vb, n);
    if (degenerate || u < -kRestingSlack || distance > contact + kProcessSlack) {
        ++counters_.inapplicable;
        pushPair(a, b, now_ + config_.eventGap);
        return;
    }

    const double previous = lastContact(a, event.b);
    collidePair(va, vb, n, config_.restitution, mass, mass);
    const double depth = separatePair(xa, xb, n, contact, mass, mass);
    result_.maxAgentOverlap = std::max(result_.maxAgentOverlap, depth);
    ++counters_.collisions;
    if (now_ - previous < config_.eventGap + 1e-12) ++counters_.floorCollisions;

    markContact(a, event.b);
    markContact(b, event.a);
    applyCollisionState(a, xa, va);
    applyCollisionState(b, xb, vb);
    scheduleMoved(relaxOverlaps(a, b));
}

// Tras separar un par, el desplazamiento puede apretar a un agente contra un tercero, una pared o
// una esquina (atascos): sin corregirlo, la cadena de solapes persiste mientras el piso `eventGap`
// demora esos contactos (medido: 0.25 m con N=500). Se proyectan posiciones, con masas
// iguales entre agentes y masa infinita en paredes/esquinas, hasta que todos los solapes de los
// agentes tocados sean menores que kProjectionTolerance, y en cada contacto comprimido se anula la
// aproximacion normal (e = 0): sin eso la presion de un atasco, que el piso `eventGap` no deja
// resolver con colisiones, reaparece como aproximacion y el solape vuelve a crecer. Los contactos
// que no estaban comprimidos los resuelve despues un evento de colision normal.
std::vector<std::size_t> EdmdEngine::relaxOverlaps(std::size_t first, std::size_t second) {
    const double tau = config_.sfm.tau;
    std::vector<std::size_t> moved{first};
    movedMask_[first] = 1;
    if (second != first) {
        moved.push_back(second);
        movedMask_[second] = 1;
    }
    std::vector<std::size_t> work(moved.begin(), moved.end());
    int budget = kProjectionBudget;
    // Solo se corrigen los solapes mayores que overlapCap (el resto es compresion que sostiene la
    // pila); un solape corregido se lleva a la mitad del tope (histeresis). Con tope 0 se proyecta
    // todo solape mayor que la tolerancia hasta el contacto exacto.
    const double trigger = std::max(config_.overlapCap, kProjectionTolerance);
    const double release = config_.overlapCap > kProjectionTolerance ? 0.5 * config_.overlapCap : 0.0;
    const auto touch = [&](std::size_t k) {
        if (movedMask_[k] == 0) {
            sync(k);  // motion pasa a x0 = posicion actual, t0 = now_
            movedMask_[k] = 1;
            moved.push_back(k);
            ++counters_.projectedAgents;
        }
    };
    while (!work.empty()) {
        if (budget-- <= 0) {
            ++counters_.projectionCaps;
            break;
        }
        const std::size_t i = work.back();
        work.pop_back();
        Record& ri = records_[i];
        // agentes
        for (int dy = -1; dy <= 1; ++dy) {
            const int cy = ri.cellY + dy;
            if (cy < 0 || cy >= rows_) continue;
            for (int dx = -1; dx <= 1; ++dx) {
                const int cx = ri.cellX + dx;
                if (cx < 0 || cx >= cols_) continue;
                const std::vector<int> cell = cells_[static_cast<std::size_t>(cy) * static_cast<std::size_t>(cols_) +
                                                    static_cast<std::size_t>(cx)];
                for (const int jj : cell) {
                    const std::size_t j = static_cast<std::size_t>(jj);
                    if (j == i || !records_[j].alive) continue;
                    Record& rj = records_[j];
                    const Vector2 xi = ri.motion.x0;
                    const Vector2 xj = relaxedPosition(rj.motion, now_, tau);
                    const Vector2 delta = xj - xi;
                    const double distance = norm(delta);
                    const double contact = ri.radius + rj.radius;
                    const double deficit = contact - distance;
                    if (deficit <= trigger) continue;
                    touch(j);
                    const Vector2 n = distance < 1e-12 ? Vector2{1.0, 0.0} : delta * (1.0 / distance);
                    ri.motion.x0 = xi - n * ((deficit - release) * 0.5);
                    rj.motion.x0 = xj + n * ((deficit - release) * 0.5);
                    // Contacto comprimido: se anula la aproximacion normal (e = 0). Sin esto la presion
                    // de un atasco (aproximacion que el piso eventGap no deja resolver) reaparece.
                    collidePair(ri.motion.v0, rj.motion.v0, n, 0.0, config_.sfm.mass, config_.sfm.mass);
                    cellRelocate(i);
                    cellRelocate(j);
                    work.push_back(j);
                    work.push_back(i);
                }
            }
        }
        // paredes y bordes de la puerta: el agente se mueve por completo
        const Vector2 xi = ri.motion.x0;
        for (const WallSegment& wall : room_.walls.segments) {
            const Vector2 along = wall.b - wall.a;
            const double length2 = dot(along, along);
            const double s = std::clamp(dot(xi - wall.a, along) / length2, 0.0, 1.0);
            const Vector2 closest = wall.a + along * s;
            const Vector2 delta = xi - closest;
            const double distance = norm(delta);
            const double deficit = ri.radius - distance;
            if (deficit <= trigger) continue;
            Vector2 n;
            if (distance < 1e-12) {
                n = wallNormal(wall, +1);
            } else {
                n = delta * (1.0 / distance);
            }
            ri.motion.x0 = xi + n * (deficit - release);
            collideFixed(ri.motion.v0, n, 0.0);
            cellRelocate(i);
            work.push_back(i);
            break;  // se re-evalua el agente completo en la proxima vuelta
        }
    }
    for (const std::size_t k : moved) movedMask_[k] = 0;
    // Todos los movidos recalculan w desde su posicion final; los proyectados (no los dos de la
    // colision, que ya subieron de generacion) cambian de trayectoria: nueva generacion.
    for (const std::size_t k : moved) {
        Record& r = records_[k];
        r.motion.w = desiredFrom(r, r.motion.x0, r.motion.v0);
        r.motion.t0 = now_;
        if (k != first && k != second) ++r.collisionCount;
    }
    return moved;
}

void EdmdEngine::scheduleMoved(const std::vector<std::size_t>& moved) {
    for (const std::size_t k : moved) movedMask_[k] = 1;
    for (const std::size_t k : moved) scheduleAgent(k, -1, false);
    for (const std::size_t k : moved) movedMask_[k] = 0;
}

void EdmdEngine::finishFixedCollision(std::size_t i, int key, Vector2 position, Vector2 velocity,
                                      double depth) {
    result_.maxWallOverlap = std::max(result_.maxWallOverlap, depth);
    ++counters_.collisions;
    if (now_ - lastContact(i, key) < config_.eventGap + 1e-12) ++counters_.floorCollisions;
    markContact(i, key);
    applyCollisionState(i, position, velocity);
    scheduleMoved(relaxOverlaps(i, i));
}

void EdmdEngine::processWall(const EdmdEvent& event) {
    const std::size_t i = static_cast<std::size_t>(event.a);
    Record& r = records_[i];
    const double tau = config_.sfm.tau;
    const std::size_t segment = static_cast<std::size_t>(event.b / 2);
    const int side = (event.b % 2) != 0 ? -1 : +1;
    const WallSegment& wall = room_.walls.segments[segment];
    const Vector2 n = wallNormal(wall, side);

    Vector2 x = relaxedPosition(r.motion, now_, tau);
    Vector2 v = relaxedVelocity(r.motion, now_, tau);
    const double s = dot(n, x - wall.a);
    const double u = -dot(v, n);
    if (u < -kRestingSlack || s > r.radius + kProcessSlack) {
        // Inalcanzable por construccion: el piso de tiempo corta cualquier repeticion en tiempo cero.
        ++counters_.inapplicable;
        sync(i);
        markContact(i, -1 - event.b);
        ++r.collisionCount;
        scheduleAgent(i, -1, false);
        return;
    }
    collideFixed(v, n, config_.restitution);
    const double depth = separateFixed(x, n, s, r.radius);
    finishFixedCollision(i, -1 - event.b, x, v, depth);
}

void EdmdEngine::processCorner(const EdmdEvent& event) {
    const std::size_t i = static_cast<std::size_t>(event.a);
    Record& r = records_[i];
    const double tau = config_.sfm.tau;
    const Vector2 corner = room_.walls.corners[static_cast<std::size_t>(event.b)];

    Vector2 x = relaxedPosition(r.motion, now_, tau);
    Vector2 v = relaxedVelocity(r.motion, now_, tau);
    const Vector2 delta = x - corner;
    const double distance = norm(delta);
    const bool degenerate = distance < 1e-12;
    const Vector2 n = degenerate ? Vector2{0.0, 1.0} : delta * (1.0 / distance);
    const double u = -dot(v, n);
    if (degenerate || u < -kRestingSlack || distance > r.radius + kProcessSlack) {
        ++counters_.inapplicable;
        sync(i);
        markContact(i, -100 - event.b);
        ++r.collisionCount;
        scheduleAgent(i, -1, false);
        return;
    }
    collideFixed(v, n, config_.restitution);
    const double depth = separateFixed(x, n, distance, r.radius);
    finishFixedCollision(i, -100 - event.b, x, v, depth);
}

bool EdmdEngine::step() {
    if (alive_ == 0 || timedOut_ || capped_) return false;
    if (counters_.processed >= config_.maxEvents) {
        capped_ = true;
        return false;
    }
    const double next = nextEventTime();
    if (!std::isfinite(next)) return false;
    if (next > config_.maxTime) {
        timedOut_ = true;
        return false;
    }

    std::pop_heap(heap_.begin(), heap_.end(), EventLater{});
    const EdmdEvent event = heap_.back();
    heap_.pop_back();

    if (event.time < now_ - 1e-9) ++counters_.timeRegressions;
    now_ = std::max(now_, event.time);
    lastEventTime_ = now_;
    lastEvent_ = event;
    ++counters_.processed;

    const std::size_t i = static_cast<std::size_t>(event.a);
    Record& r = records_[i];

    switch (event.type) {
        case EventType::PairContact:
            processPair(event);
            break;
        case EventType::WallContact:
            processWall(event);
            break;
        case EventType::CornerContact:
            processCorner(event);
            break;
        case EventType::DoorCross: {
            sync(i);
            r.status = AgentStatus::Exiting;
            retarget(i, room_.exitTarget);
            ++result_.crossed;
            result_.evacuationTime = now_;
            if (std::abs(r.motion.x0.x - room_.doorCenter.x) > config_.doorWidth / 2.0) {
                ++result_.wallBreaches;
            }
            ++r.collisionCount;
            scheduleAgent(i, -1, false);
            break;
        }
        case EventType::Retire: {
            cellErase(i);
            r.alive = false;
            --alive_;
            ++result_.removed;
            result_.clearTime = now_;
            ++r.collisionCount;
            break;
        }
        case EventType::CellCross: {
            cellErase(i);
            switch (event.b) {
                case 0: --r.cellX; break;
                case 1: ++r.cellX; break;
                case 2: --r.cellY; break;
                default: ++r.cellY; break;
            }
            cellInsert(i);
            ++counters_.cellCrossings;
            pushCellCross(i);
            pushNeighborPairs(i, -1, false);
            break;
        }
        case EventType::Steer: {
            const Vector2 x = relaxedPosition(r.motion, now_, config_.sfm.tau);
            const Vector2 w = desiredFrom(r, x, r.motion.w);
            if (norm(w - r.motion.w) > 1e-9 * config_.sfm.desiredSpeed) {
                sync(i);
                r.motion.w = w;
                ++r.collisionCount;
                ++counters_.steerEvents;
                scheduleAgent(i, -1, false);
            } else if (!isSettled(stateOf(i, now_), 1e-6 * config_.sfm.desiredSpeed) &&
                       now_ + config_.steerInterval <= config_.maxTime) {
                push(makeEvent(EventType::Steer, now_ + config_.steerInterval, event.a, -1));
            }
            break;
        }
        case EventType::Promote:
            // Solo avisa: no cambia generaciones ni resuelve nada. El contacto lo resuelve el
            // resorte SFM del TSDMD tras el pasaje (D-24, D-25).
            promoted_.push_back(event.a);
            if (event.b >= 0) promoted_.push_back(event.b);
            break;
    }

    if (heap_.size() > compactLimit_) compact();
    return true;
}

// ---------------------------------------------------------------- ganchos del hibrido

std::vector<int> EdmdEngine::takePromotions() {
    std::vector<int> ids;
    ids.swap(promoted_);
    std::sort(ids.begin(), ids.end());
    ids.erase(std::unique(ids.begin(), ids.end()), ids.end());
    std::erase_if(ids, [this](int id) { return !records_[static_cast<std::size_t>(id)].alive; });
    return ids;
}

void EdmdEngine::advanceTo(double t) { now_ = std::max(now_, t); }

Agent EdmdEngine::release(int id) {
    const std::size_t i = static_cast<std::size_t>(id);
    Record& r = records_[i];
    const double tau = config_.sfm.tau;
    Agent a;
    a.id = r.id;
    a.position = relaxedPosition(r.motion, now_, tau);
    a.velocity = relaxedVelocity(r.motion, now_, tau);
    a.target = r.target;
    a.radius = r.radius;
    a.status = r.status;
    a.scheme = 0;
    cellErase(i);
    r.alive = false;
    --alive_;
    ++r.collisionCount;  // invalida todos sus eventos (D-18)
    r.contacts.clear();
    return a;
}

void EdmdEngine::admit(const Agent& agent) {
    const std::size_t i = static_cast<std::size_t>(agent.id);
    Record& r = records_[i];
    r.status = agent.status;
    r.target = agent.status == AgentStatus::InRoom ? room_.doorCenter : room_.exitTarget;
    r.radius = agent.radius;
    r.motion.x0 = agent.position;
    r.motion.v0 = agent.velocity;
    r.motion.w = desiredVelocity(config_.sfm, agent.position, r.target, agent.velocity);
    r.motion.t0 = now_;
    r.contacts.clear();
    r.cellX = cellCoordX(agent.position.x);
    r.cellY = cellCoordY(agent.position.y);
    r.alive = true;
    ++alive_;
    cellInsert(i);
    ++r.collisionCount;  // generacion nueva: ningun evento previo vuelve a ser valido (D-29)
    scheduleAgent(i, -1, false);
}

double EdmdEngine::freeContactTime(const Agent& agent, double horizon) const {
    const double tau = config_.sfm.tau;
    const Vector2 target = agent.status == AgentStatus::InRoom ? room_.doorCenter : room_.exitTarget;
    Relaxation m;
    m.x0 = agent.position;
    m.v0 = agent.velocity;
    m.w = desiredVelocity(config_.sfm, agent.position, target, agent.velocity);
    m.t0 = now_;
    const double tMax = now_ + horizon;

    double best = kInfinity;
    // Filtro de distancia solido: el agente recorre a lo sumo max(|v|, v_d) * horizon (la velocidad es
    // una combinacion convexa de v0 y w, |w| = v_d); un obstaculo fijo mas lejos que eso no se alcanza.
    const double vd = config_.sfm.desiredSpeed;
    const double travel = std::max(norm(agent.velocity), vd) * horizon;
    for (const WallSegment& wall : room_.walls.segments) {
        const Vector2 ab = wall.b - wall.a;
        const double len2 = dot(ab, ab);
        const double s = len2 > 0.0 ? std::clamp(dot(agent.position - wall.a, ab) / len2, 0.0, 1.0) : 0.0;
        if (norm(agent.position - (wall.a + ab * s)) - agent.radius > travel) continue;
        const int side = dot(wallNormal(wall, +1), agent.position - wall.a) < 0.0 ? -1 : +1;
        best = std::min(best, wallContactTime(m, agent.radius, wall, side, tau, now_, tMax));
    }
    for (const Vector2& corner : room_.walls.corners) {
        if (norm(agent.position - corner) - agent.radius > travel) continue;
        Relaxation rel = m;
        rel.x0 = m.x0 - corner;
        best = std::min(best, firstBallApproach(rel, agent.radius, tau, now_, tMax));
    }

    // Vecinos residentes: la ventana de busqueda crece con el camino de la velocidad relativa.
    const double reach = 2.0 * config_.radiusMax + kLeadRelativeSpeedFactor * config_.sfm.desiredSpeed * horizon;
    const int span = std::max(1, static_cast<int>(std::min(std::ceil(reach / cellSize_),
                                                           static_cast<double>(std::max(cols_, rows_)))));
    const int cx0 = cellCoordX(agent.position.x);
    const int cy0 = cellCoordY(agent.position.y);
    for (int cy = std::max(0, cy0 - span); cy <= std::min(rows_ - 1, cy0 + span); ++cy) {
        for (int cx = std::max(0, cx0 - span); cx <= std::min(cols_ - 1, cx0 + span); ++cx) {
            const std::vector<int>& cell = cells_[static_cast<std::size_t>(cy) * static_cast<std::size_t>(cols_) +
                                                  static_cast<std::size_t>(cx)];
            for (const int j : cell) {
                const Record& other = records_[static_cast<std::size_t>(j)];
                if (!other.alive || other.id == agent.id) continue;
                const Relaxation sj = stateOf(static_cast<std::size_t>(j), now_);
                // Mismo filtro solido: el residente recorre a lo sumo max(|v_j|, v_d) * horizon.
                const double gap = norm(sj.x0 - m.x0) - (agent.radius + other.radius);
                if (gap > (std::max(norm(agent.velocity), vd) + std::max(norm(sj.v0), vd)) * std::min(horizon, best - now_)) {
                    continue;
                }
                Relaxation rel;
                rel.x0 = sj.x0 - m.x0;
                rel.v0 = sj.v0 - m.v0;
                rel.w = sj.w - m.w;
                rel.t0 = now_;
                best = std::min(best, firstBallApproach(rel, agent.radius + other.radius, tau, now_,
                                                        std::min(tMax, best)));
            }
        }
    }
    return std::isfinite(best) ? best - now_ : kInfinity;
}

double EdmdEngine::contactTimeWithBody(int id, const Relaxation& body, double bodyRadius,
                                        double horizon) const {
    const double tau = config_.sfm.tau;
    const std::size_t i = static_cast<std::size_t>(id);
    const Relaxation si = stateOf(i, now_);
    // El cuerpo externo se reevalua en now_ (su t0 puede ser anterior) y se toma su w tal cual.
    Relaxation rel;
    rel.x0 = relaxedPosition(body, now_, tau) - si.x0;
    rel.v0 = relaxedVelocity(body, now_, tau) - si.v0;
    rel.w = body.w - si.w;
    rel.t0 = now_;
    const double t = firstBallApproach(rel, records_[i].radius + bodyRadius, tau, now_, now_ + horizon);
    return std::isfinite(t) ? t - now_ : kInfinity;
}

const std::vector<int>& EdmdEngine::cellResidents(int cx, int cy) const {
    static const std::vector<int> kEmpty;
    if (cx < 0 || cx >= cols_ || cy < 0 || cy >= rows_) return kEmpty;
    return cells_[static_cast<std::size_t>(cy) * static_cast<std::size_t>(cols_) +
                  static_cast<std::size_t>(cx)];
}

// ---------------------------------------------------------------- observabilidad

std::optional<EdmdEvent> EdmdEngine::peekNext() {
    if (!std::isfinite(nextEventTime())) return std::nullopt;
    return heap_.front();
}

std::optional<EdmdEvent> EdmdEngine::peekNextPhysical() const {
    std::optional<EdmdEvent> best;
    for (const EdmdEvent& e : heap_) {
        if (!isPhysical(e.type) || !isValid(e)) continue;
        if (!best || EventLater{}(*best, e)) best = e;
    }
    return best;
}

std::optional<EdmdEvent> EdmdEngine::bruteForceNextPhysical() const {
    std::optional<EdmdEvent> best;
    const auto consider = [&](EventType type, double time, int a, int b) {
        if (!std::isfinite(time) || time > config_.maxTime) return;
        if (best && !(time < best->time)) return;
        best = makeEvent(type, time, a, b);
    };
    const std::size_t count = records_.size();
    for (std::size_t i = 0; i < count; ++i) {
        const Record& r = records_[i];
        if (!r.alive) continue;
        const int index = static_cast<int>(i);
        consider(r.status == AgentStatus::InRoom ? EventType::DoorCross : EventType::Retire,
                 doorOrRetireTime(i), index, -1);
        for (std::size_t k = 0; k < room_.walls.segments.size(); ++k) {
            const int side = wallSide(i, k);
            consider(EventType::WallContact, wallEventTime(i, k, side), index,
                     static_cast<int>(2 * k) + (side < 0 ? 1 : 0));
        }
        for (std::size_t c = 0; c < room_.walls.corners.size(); ++c) {
            consider(EventType::CornerContact, cornerEventTime(i, c), index, static_cast<int>(c));
        }
        for (std::size_t j = i + 1; j < count; ++j) {
            if (!records_[j].alive) continue;
            consider(EventType::PairContact, pairEventTime(i, j, 0.0), index, static_cast<int>(j));
        }
    }
    return best;
}

bool EdmdEngine::discardNextPhysicalForTesting() {
    const std::optional<EdmdEvent> next = peekNextPhysical();
    if (!next) return false;
    // Un par puede estar en la cola con (a, b) o con (b, a): se quitan ambas orientaciones.
    std::erase_if(heap_, [&](const EdmdEvent& e) {
        if (!isValid(e) || e.type != next->type) return false;
        if (e.a == next->a && e.b == next->b) return true;
        return e.type == EventType::PairContact && e.a == next->b && e.b == next->a;
    });
    std::make_heap(heap_.begin(), heap_.end(), EventLater{});
    return true;
}

void EdmdEngine::injectEventForTesting(const EdmdEvent& event) { push(event); }

// ---------------------------------------------------------------- salida

std::vector<Agent> EdmdEngine::snapshot(double time) const {
    const double tau = config_.sfm.tau;
    std::vector<Agent> frame;
    frame.reserve(static_cast<std::size_t>(alive_));
    for (const Record& r : records_) {
        if (!r.alive) continue;
        Agent a;
        a.id = r.id;
        a.position = relaxedPosition(r.motion, time, tau);
        a.velocity = relaxedVelocity(r.motion, time, tau);
        a.acceleration = (r.motion.w - a.velocity) * (1.0 / tau);
        a.target = r.target;
        a.radius = r.radius;
        a.status = r.status;
        a.scheme = 1;
        frame.push_back(a);
    }
    std::stable_sort(frame.begin(), frame.end(),
                     [](const Agent& l, const Agent& r) { return l.id < r.id; });
    return frame;
}

EvacuationResult EdmdEngine::result() const {
    EvacuationResult r = result_;
    r.steps = counters_.processed;
    r.events = counters_.processed;
    r.staleEvents = counters_.stale;
    r.collisions = counters_.collisions;
    r.floorCollisions = counters_.floorCollisions;
    r.timeRegressions = counters_.timeRegressions;
    r.completed = alive_ == 0;
    r.finalTime = r.completed ? lastEventTime_ : (capped_ ? now_ : config_.maxTime);
    r.inRoomFinal = 0;
    for (const Record& rec : records_) {
        if (rec.alive && rec.status == AgentStatus::InRoom) ++r.inRoomFinal;
    }
    return r;
}

EvacuationResult runEdmd(const EvacuationConfig& config, std::vector<Agent> agents,
                         const FrameSink& sink) {
    using Clock = std::chrono::steady_clock;

    EdmdEngine engine(config, std::move(agents));
    double outputSeconds = 0.0;
    const auto emit = [&](double time) {
        if (!sink) return;
        const auto t0 = Clock::now();
        sink(time, engine.snapshot(time));
        outputSeconds += std::chrono::duration<double>(Clock::now() - t0).count();
    };

    // D-20: frames en k*dt2 con contador entero; un frame en f refleja todos los eventos con
    // tiempo <= f, asi que se emite antes de procesar solo si f es estrictamente anterior.
    long long nextFrame = 1;
    double lastEmitted = 0.0;
    const auto flush = [&](double limit, bool inclusive) {
        for (;;) {
            const double f = static_cast<double>(nextFrame) * config.dt2;
            if (!(inclusive ? f <= limit : f < limit)) break;
            emit(f);
            lastEmitted = f;
            ++nextFrame;
        }
    };

    const auto loopStart = Clock::now();
    emit(0.0);
    while (!engine.finished()) {
        const double next = engine.nextEventTime();
        if (!std::isfinite(next) || next > config.maxTime) break;
        flush(next, false);
        if (!engine.step()) break;
    }

    EvacuationResult result = engine.result();
    flush(result.finalTime, true);
    if (lastEmitted < result.finalTime) emit(result.finalTime);
    const double totalSeconds = std::chrono::duration<double>(Clock::now() - loopStart).count();

    result.outputMs = outputSeconds * 1e3;
    result.simulationMs = (totalSeconds - outputSeconds) * 1e3;
    return result;
}
