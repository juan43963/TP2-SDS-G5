// Suites `hybrid_brute` y `hybrid_audit` (HYB-02, HYB-03, HYB-04; D-24, D-25, D-28, D-29): auditor
// independiente por fuerza bruta O(N^2) de toda una corrida hibrida. En cada limite de la grilla
// (lastStepWasBoundary) recorre todos los pares sin celdas ni ventanas y comprueba:
//
//   * Superposicion nueva: con T > 0 un residente EDMD nunca esta solapado con nada, porque todo
//     contacto lo resuelve el resorte SFM de TSDMD tras la promocion previa al contacto (D-24, D-25).
//     Todo par con al menos un residente EDMD debe tener una profundidad de solape menor o igual que
//     kResidentTolerance. Ademas el oraculo del proyecto (checkOverlaps, que no comparte codigo con el
//     motor) no debe reportar violaciones (profundidad > 0.5 veces el menor radio).
//   * Contacto perdido: un par con al menos un residente EDMD cuyo primer contacto con aproximacion,
//     calculado por fuerza bruta (firstBallApproach con el movimiento exacto del residente y, para un
//     vecino TSDMD, la velocidad constante del vecino, el mismo modelo que usa el motor), ocurre antes
//     de T - 2 dt desde ahora. El hibrido debia haberlo promovido antes (D-25); 2 dt de margen absorbe
//     el desfase de un limite. Las paredes y esquinas se cubren por la regla de residente y el oraculo.
//   * Oscilacion: dos cambios de esquema del mismo agente en limites consecutivos (D-28, histeresis
//     alpha*T); la guarda de retorno (D-29) evita volver estando en contacto.
//
// Tres defensas contra una prueba vacia: contadores de no-vacuidad (pares mixtos cercanos,
// promociones, retornos), controles negativos (escaneo mixto apagado, guarda de retorno apagada y
// horizonte de auditoria mayor que T deben ser detectados) y el oraculo independiente.
#include <algorithm>
#include <cmath>
#include <cstdio>
#include <cstdlib>
#include <string>
#include <vector>

#include "edmd_kernel.h"
#include "generator.h"
#include "hybrid.h"
#include "overlap_oracle.h"
#include "relaxation.h"
#include "test_support.h"

namespace {

// Tolerancia de solape [m] de un residente EDMD (invariante: con T > 0 vale 0; 1e-6 absorbe redondeo).
constexpr double kResidentTolerance = 1e-6;
// Margen del horizonte de contactos perdidos, en pasos dt: el horizonte es T - 2 dt.
constexpr int kTauMarginSteps = 2;
// Salto maximo de posicion [m] de un agente que cambia de esquema (los pasajes conservan x).
constexpr double kPassJumpLimit = 1e-3;
// Cada cuantos limites se calculan los contactos previstos en la corrida densa de N = 60.
constexpr long long kTauStride = 50;
// Cota de la rapidez de un agente [m/s] para descontar el avance de un paso dt en la continuidad.
constexpr double kSpeedBound = 5.0;

// Alcance trasero (como hybrid_tracer): lado 30 (puerta en (15, 0)), agentes de radio 0.2 en x = 15,
// el 0 en y = 20 a 1.5 m/s y el 1 en y = 21 a 3.0 m/s; contacto analitico t_c = 0.5*ln(5) = 0.80472 s.
constexpr double kSide = 30.0;
constexpr double kRadius = 0.2;
constexpr double kLead = 0.3;
const double kContactTime = 0.5 * std::log(5.0);

// Corrida densa de N = 60: semilla 1 de L = 10 con T y alpha por defecto (la misma que hybrid-smoke:
// completa, t_evac = 88.32 s, mixed_promotions = 93).
constexpr int kDenseAgents = 60;
constexpr double kDenseSide = 10.0;
constexpr unsigned long long kDenseSeed = 1;
constexpr double kDenseMaxTime = 400.0;
// Corrida pesada de N = 200 (hybrid-scale: L = 31.6, semilla 1, completa en t_evac = 345.63 s).
constexpr int kHeavyAgents = 200;
constexpr double kHeavySide = 31.6;
constexpr unsigned long long kHeavySeed = 1;
constexpr double kHeavyMaxTime = 500.0;

Agent makeAgent(int id, Vector2 position, Vector2 velocity, int scheme) {
    Agent a;
    a.id = id;
    a.position = position;
    a.velocity = velocity;
    a.radius = kRadius;
    a.target = {kSide / 2.0, 0.0};
    a.status = AgentStatus::InRoom;
    a.scheme = scheme;
    return a;
}

EvacuationConfig scenarioConfig(int agents, double lead, double alpha) {
    EvacuationConfig c;
    c.scheme = Scheme::Hybrid;
    c.agentCount = agents;
    c.side = kSide;
    c.hybridT = lead;
    c.hybridAlpha = alpha;
    c.maxTime = 100.0;
    return c;
}

// ---------------------------------------------------------------- auditor

struct AuditParams {
    EvacuationConfig config;
    OracleRoom room;
    double tauHorizon = 0.0;
    long long depthStride = 1;
    long long tauStride = 1;
    bool trackFlips = false;
};

struct AuditState {
    long long audited = 0;                 // limites auditados hasta ahora
    long long lastPromotions = 0;
    long long lastReturns = 0;
    std::vector<int> lastScheme;           // por id: esquema en el limite anterior (-1 retirado)
    std::vector<long long> lastChange;     // por id: indice de limite del ultimo cambio
    std::vector<double> lastChangeTime;    // por id: instante del ultimo cambio (-1: ninguno)
    std::vector<Vector2> lastPos;          // por id: posicion en el limite anterior
    std::vector<char> hasLastPos;
    std::vector<Vector2> prePos;           // por id: posicion EDMD exacta en el limite, antes del pasaje
    std::vector<char> hasPre;
};

struct AuditTotals {
    long long boundaries = 0;
    long long depthChecks = 0;
    long long tauChecks = 0;
    long long pairsExamined = 0;
    long long mixedPairBoundaries = 0;
    long long residentOverlaps = 0;
    long long lostContacts = 0;
    long long oracleViolations = 0;
    long long consecutiveFlips = 0;
    long long schemeChanges = 0;
    double maxResidentDepth = 0.0;
    double maxPassJump = 0.0;
    double minDwellSeconds = 1e300;
    std::string firstProblem;
};

void noteProblem(AuditTotals& totals, const char* kind, long long boundary, int a, int b, double value) {
    if (!totals.firstProblem.empty()) return;
    char text[160];
    std::snprintf(text, sizeof(text), "%s en el limite %lld: agentes %d y %d, valor %.6g", kind, boundary, a, b, value);
    totals.firstProblem = text;
}

AuditParams makeParams(const EvacuationConfig& config, long long depthStride, long long tauStride, bool trackFlips) {
    AuditParams p;
    p.config = config;
    p.room.side = config.side;
    p.room.doorWidth = config.doorWidth;
    p.room.exitDistance = config.exitDistance;
    p.tauHorizon = config.hybridT - kTauMarginSteps * config.dt;
    p.depthStride = depthStride;
    p.tauStride = tauStride;
    p.trackFlips = trackFlips;
    return p;
}

// a) solape de residentes, pares mixtos cercanos y oraculo de superposicion.
void auditDepth(const std::vector<Agent>& frame, const AuditParams& params, long long boundary,
                AuditTotals& totals) {
    ++totals.depthChecks;
    const double mixedRange = 2.0 * params.config.radiusMax + 2.0 * params.config.sfm.desiredSpeed * params.config.hybridT;
    bool mixedNear = false;
    for (std::size_t i = 0; i < frame.size(); ++i) {
        for (std::size_t j = i + 1; j < frame.size(); ++j) {
            ++totals.pairsExamined;
            const double distance = std::hypot(frame[i].position.x - frame[j].position.x,
                                               frame[i].position.y - frame[j].position.y);
            const double depth = frame[i].radius + frame[j].radius - distance;
            const bool anyResident = frame[i].scheme == 1 || frame[j].scheme == 1;
            if (depth > kResidentTolerance && anyResident) {
                ++totals.residentOverlaps;
                totals.maxResidentDepth = std::max(totals.maxResidentDepth, depth);
                noteProblem(totals, "solape de residente", boundary, frame[i].id, frame[j].id, depth);
            }
            if (frame[i].scheme != frame[j].scheme && distance < mixedRange) mixedNear = true;
        }
    }
    if (mixedNear) ++totals.mixedPairBoundaries;

    std::vector<OracleRow> rows;
    rows.reserve(frame.size());
    for (const Agent& a : frame) rows.push_back({a.id, a.position.x, a.position.y, a.radius});
    const OverlapReport report = checkOverlaps(rows, params.room);
    totals.oracleViolations += report.violations;
    if (report.violations > 0) noteProblem(totals, "violacion del oraculo", boundary, -1, -1, report.maxAgentDepth);
}

// b) contactos previstos por fuerza bruta: pares con al menos un residente EDMD y primer contacto con
// aproximacion antes de tauHorizon, con la trayectoria exacta del residente y la velocidad constante
// del vecino TSDMD (el mismo modelo que el motor).
void auditTau(const HybridEngine& engine, const std::vector<Agent>& frame, const AuditParams& params,
              long long boundary, AuditTotals& totals) {
    ++totals.tauChecks;
    const double now = engine.now();
    const double tau = params.config.sfm.tau;
    std::vector<Relaxation> motion;
    std::vector<double> speed;
    motion.reserve(frame.size());
    speed.reserve(frame.size());
    for (const Agent& a : frame) {
        Relaxation m = a.scheme == 1 ? engine.edmd().motionOf(a.id)
                                     : Relaxation{a.position, a.velocity, a.velocity, now};
        motion.push_back(m);
        speed.push_back(std::max(norm(m.v0), norm(m.w)));  // cota de la rapidez en la relajacion
    }
    for (std::size_t i = 0; i < frame.size(); ++i) {
        for (std::size_t j = i + 1; j < frame.size(); ++j) {
            if (frame[i].scheme != 1 && frame[j].scheme != 1) continue;
            const double contact = frame[i].radius + frame[j].radius;
            const double gap = norm(motion[j].x0 - motion[i].x0) - contact;
            if (gap > (speed[i] + speed[j]) * params.tauHorizon) continue;  // filtro solido
            Relaxation rel;
            rel.x0 = motion[j].x0 - motion[i].x0;
            rel.v0 = motion[j].v0 - motion[i].v0;
            rel.w = motion[j].w - motion[i].w;
            rel.t0 = now;
            const double t = firstBallApproach(rel, contact, tau, now, now + params.tauHorizon);
            if (std::isfinite(t)) {
                ++totals.lostContacts;
                noteProblem(totals, "contacto perdido", boundary, frame[i].id, frame[j].id, t - now);
            }
        }
    }
}

// c) oscilacion y continuidad de posicion en los pasajes.
void auditFlips(const HybridEngine& engine, const std::vector<Agent>& frame, const AuditParams& params,
                AuditState& state, AuditTotals& totals) {
    const long long k = engine.boundaryIndex();
    const double now = engine.now();
    for (const Agent& a : frame) {
        const std::size_t id = static_cast<std::size_t>(a.id);
        const int scheme = engine.schemeOf(a.id);
        const int before = state.lastScheme[id];
        if (before >= 0 && scheme >= 0 && before != scheme) {
            ++totals.schemeChanges;
            double jump = 0.0;
            if (before == 1 && state.hasPre[id] != 0) {
                jump = norm(a.position - state.prePos[id]);  // promocion: estado exacto en el limite
            } else if (before == 0 && state.hasLastPos[id] != 0) {
                jump = std::max(0.0, norm(a.position - state.lastPos[id]) - kSpeedBound * params.config.dt);
            }
            totals.maxPassJump = std::max(totals.maxPassJump, jump);
            if (state.lastChange[id] >= 0 && k - state.lastChange[id] == 1) {
                ++totals.consecutiveFlips;
                noteProblem(totals, "cambio de esquema consecutivo", k, a.id, a.id, 0.0);
            }
            if (state.lastChangeTime[id] >= 0.0) {
                totals.minDwellSeconds = std::min(totals.minDwellSeconds, now - state.lastChangeTime[id]);
            }
            state.lastChange[id] = k;
            state.lastChangeTime[id] = now;
        }
        state.lastScheme[id] = scheme;
        state.lastPos[id] = a.position;
        state.hasLastPos[id] = 1;
    }
}

void auditBoundary(const HybridEngine& engine, const AuditParams& params, AuditState& state, AuditTotals& totals) {
    const long long index = state.audited++;
    const long long k = engine.boundaryIndex();
    ++totals.boundaries;
    const HybridCounters& counters = engine.counters();
    const bool changed = counters.promotions != state.lastPromotions || counters.returns != state.lastReturns;
    state.lastPromotions = counters.promotions;
    state.lastReturns = counters.returns;
    const bool doDepth = index % params.depthStride == 0;
    const bool doTau = index % params.tauStride == 0 || changed;
    if (!doDepth && !doTau && !params.trackFlips) return;

    const std::vector<Agent> frame = engine.snapshot(engine.now());
    if (doDepth) auditDepth(frame, params, k, totals);
    if (doTau) auditTau(engine, frame, params, k, totals);
    if (params.trackFlips) auditFlips(engine, frame, params, state, totals);
}

struct Hooks {
    bool mixedScan = true;
    bool returnGuard = true;
    std::vector<int> promoteAtStart;
};

EvacuationResult runAudited(const EvacuationConfig& config, std::vector<Agent> agents, const AuditParams& params,
                            AuditTotals& totals, const Hooks& hooks) {
    int maxId = 0;
    for (const Agent& a : agents) maxId = std::max(maxId, a.id);
    const std::size_t n = static_cast<std::size_t>(maxId) + 1;

    HybridEngine engine(config, std::move(agents));
    engine.setMixedScanEnabledForTesting(hooks.mixedScan);
    engine.setReturnGuardEnabledForTesting(hooks.returnGuard);
    for (const int id : hooks.promoteAtStart) engine.requestPromotionForTesting(id);

    AuditState state;
    state.lastScheme.assign(n, -1);
    state.lastChange.assign(n, -1);
    state.lastChangeTime.assign(n, -1.0);
    state.lastPos.assign(n, Vector2{});
    state.hasLastPos.assign(n, 0);
    state.prePos.assign(n, Vector2{});
    state.hasPre.assign(n, 0);
    state.lastPromotions = engine.counters().promotions;
    state.lastReturns = engine.counters().returns;
    for (std::size_t id = 0; id < n; ++id) state.lastScheme[id] = engine.schemeOf(static_cast<int>(id));
    for (const Agent& a : engine.snapshot(engine.now())) {
        state.lastPos[static_cast<std::size_t>(a.id)] = a.position;
        state.hasLastPos[static_cast<std::size_t>(a.id)] = 1;
    }

    while (!engine.finished()) {
        if (params.trackFlips && engine.nextIsBoundary()) {
            // Estado de los residentes EDMD en el limite que sigue, antes del pasaje (valido para
            // cualquier tiempo >= now() del motor EDMD).
            std::fill(state.hasPre.begin(), state.hasPre.end(), 0);
            const double tb = static_cast<double>(engine.nextBoundaryIndex()) * config.dt;
            for (const Agent& a : engine.edmd().snapshot(tb)) {
                state.prePos[static_cast<std::size_t>(a.id)] = a.position;
                state.hasPre[static_cast<std::size_t>(a.id)] = 1;
            }
        }
        if (!engine.step()) break;
        if (engine.lastStepWasBoundary()) auditBoundary(engine, params, state, totals);
    }
    return engine.result();
}

void printAudit(const char* label, const AuditTotals& t, const EvacuationResult& r) {
    std::printf("HYBRID_AUDIT label=%s boundaries=%lld depth_checks=%lld tau_checks=%lld pairs_examined=%lld "
                "mixed_pair_boundaries=%lld resident_overlaps=%lld lost_contacts=%lld oracle_violations=%lld "
                "promotions=%lld returns=%lld mixed_promotions=%lld quick_repromotions=%lld "
                "consecutive_flips=%lld max_resident_depth=%.3g max_pass_jump=%.3g min_dwell_s=%.3g "
                "collisions=%lld completed=%d\n",
                label, t.boundaries, t.depthChecks, t.tauChecks, t.pairsExamined, t.mixedPairBoundaries,
                t.residentOverlaps, t.lostContacts, t.oracleViolations, r.hybridPromotions, r.hybridReturns,
                r.hybridMixedPromotions, r.hybridQuickRepromotions, t.consecutiveFlips, t.maxResidentDepth,
                t.maxPassJump, t.minDwellSeconds < 1e299 ? t.minDwellSeconds : -1.0, r.collisions,
                r.completed ? 1 : 0);
    if (!t.firstProblem.empty()) std::printf("  primer problema: %s\n", t.firstProblem.c_str());
    std::fflush(stdout);
}

void printControl(const char* name, bool detected) {
    std::printf("CONTROL name=%s detected=%d\n", name, detected ? 1 : 0);
    std::fflush(stdout);
}

// ---------------------------------------------------------------- escenarios

std::vector<Agent> rearEndAgents() {
    return {makeAgent(0, {15.0, 20.0}, {0.0, -1.5}, 1), makeAgent(1, {15.0, 21.0}, {0.0, -3.0}, 1)};
}

// Escenario mixto (como hybrid_mixed): agente 0 forzado a TSDMD en reposo y agente 1 EDMD a 1.5 m/s,
// alpha = 4 para que el 0 no vuelva a EDMD antes de que llegue el 1.
std::vector<Agent> mixedAgents() {
    return {makeAgent(0, {15.0, 20.0}, {0.0, 0.0}, 1), makeAgent(1, {15.0, 21.0}, {0.0, -1.5}, 1)};
}

void checkZeros(TestSuite& suite, const char* label, const AuditTotals& t) {
    const std::string name = label;
    suite.check(t.residentOverlaps == 0, (name + ": ningun solape de residente EDMD (0 superposiciones nuevas)").c_str());
    suite.check(t.lostContacts == 0, (name + ": 0 contactos perdidos").c_str());
    suite.check(t.oracleViolations == 0, (name + ": el oraculo de superposicion no reporta nada").c_str());
    suite.check(t.boundaries > 0 && t.pairsExamined > 0, (name + ": la auditoria no es vacia").c_str());
}

void testRearEnd(TestSuite& suite) {
    const EvacuationConfig c = scenarioConfig(2, kLead, 2.0);
    AuditTotals totals;
    const EvacuationResult r = runAudited(c, rearEndAgents(), makeParams(c, 1, 1, true), totals, Hooks{});
    printAudit("rear_end", totals, r);
    checkZeros(suite, "rear_end", totals);
    suite.check(r.completed, "rear_end: la corrida completa");
    suite.check(r.hybridPromotions == 2 && r.hybridReturns == 2, "rear_end: 2 promociones y 2 retornos");
    suite.check(totals.maxPassJump < kPassJumpLimit, "rear_end: salto de posicion en los pasajes < 1e-3 m");
    suite.check(totals.consecutiveFlips == 0, "rear_end: sin cambios de esquema consecutivos");
    suite.check(r.collisions == 0, "rear_end: collisions == 0");
}

void testMixed(TestSuite& suite) {
    const EvacuationConfig c = scenarioConfig(2, kLead, 4.0);
    AuditTotals totals;
    Hooks hooks;
    hooks.promoteAtStart = {0};
    const EvacuationResult r = runAudited(c, mixedAgents(), makeParams(c, 1, 1, true), totals, hooks);
    printAudit("mixed", totals, r);
    checkZeros(suite, "mixed", totals);
    suite.check(r.hybridMixedPromotions == 1, "mixed: mixed_promotions == 1");
    suite.check(totals.mixedPairBoundaries > 0, "mixed: hay limites con pares EDMD-TSDMD cercanos");
    suite.check(totals.maxPassJump < kPassJumpLimit, "mixed: salto de posicion en los pasajes < 1e-3 m");
    suite.check(totals.consecutiveFlips == 0, "mixed: sin cambios de esquema consecutivos");
    suite.check(r.collisions == 0, "mixed: collisions == 0");
}

EvacuationConfig denseConfig(int agents, double side, unsigned long long seed, double maxTime) {
    EvacuationConfig c;
    c.scheme = Scheme::Hybrid;
    c.agentCount = agents;
    c.side = side;
    c.seed = seed;
    c.maxTime = maxTime;
    return c;
}

void testDense60(TestSuite& suite) {
    const EvacuationConfig c = denseConfig(kDenseAgents, kDenseSide, kDenseSeed, kDenseMaxTime);
    AuditTotals totals;
    const EvacuationResult r = runAudited(c, generateAgents(c), makeParams(c, 1, kTauStride, true), totals, Hooks{});
    printAudit("dense_n60", totals, r);
    checkZeros(suite, "dense_n60", totals);
    suite.check(r.completed, "dense_n60: la corrida completa");
    suite.check(totals.mixedPairBoundaries > 0, "dense_n60: hay limites con pares EDMD-TSDMD cercanos");
    suite.check(r.hybridPromotions > 0 && r.hybridReturns > 0, "dense_n60: hubo promociones y retornos");
    suite.check(r.hybridMixedPromotions > 0, "dense_n60: hubo promociones por el escaneo mixto");
    suite.check(r.collisions == 0, "dense_n60: collisions == 0");
    suite.check(totals.consecutiveFlips == 0, "dense_n60: ningun agente cambia de esquema en dos limites consecutivos");
    suite.check(totals.maxPassJump < kPassJumpLimit, "dense_n60: salto de posicion en los pasajes < 1e-3 m");
    suite.check(totals.tauChecks > 0, "dense_n60: se calcularon contactos previstos");
}

// ---------------------------------------------------------------- controles negativos

void testControls(TestSuite& suite) {
    // A: escaneo de pares mixtos apagado (D-25): el agente EDMD atraviesa al TSDMD.
    {
        const EvacuationConfig c = scenarioConfig(2, kLead, 4.0);
        AuditTotals totals;
        Hooks hooks;
        hooks.mixedScan = false;
        hooks.promoteAtStart = {0};
        const EvacuationResult r = runAudited(c, mixedAgents(), makeParams(c, 1, 1, false), totals, hooks);
        printAudit("control_A", totals, r);
        const bool detected = totals.lostContacts > 0 && totals.residentOverlaps > 0 && totals.oracleViolations > 0;
        printControl("scan_off", detected);
        suite.check(totals.lostContacts > 0, "control A: sin escaneo mixto el auditor reporta contactos perdidos");
        suite.check(totals.residentOverlaps > 0, "control A: sin escaneo mixto el auditor reporta solape de residente");
        suite.check(totals.oracleViolations > 0, "control A: sin escaneo mixto el oraculo reporta violaciones");
    }
    // B: guarda de retorno apagada (D-29): un agente vuelve a EDMD estando solapado.
    {
        const EvacuationConfig c = scenarioConfig(2, kLead, 2.0);
        AuditTotals totals;
        Hooks hooks;
        hooks.returnGuard = false;
        const EvacuationResult r = runAudited(c, rearEndAgents(), makeParams(c, 1, 1, false), totals, hooks);
        printAudit("control_B", totals, r);
        printControl("return_guard_off", totals.residentOverlaps > 0);
        suite.check(totals.residentOverlaps > 0, "control B: sin guarda de retorno el auditor reporta solape de residente");
    }
    // C: horizonte de auditoria (0.6 s) mayor que T (0.3 s): un residente que se aproxima a un agente
    // TSDMD y todavia no fue promovido tiene un contacto previsto dentro del horizonte. Se usa el
    // escenario mixto: en el alcance trasero los dos agentes se promueven en el mismo limite y nunca hay
    // un par con residente EDMD que auditar antes del pasaje.
    {
        const EvacuationConfig c = scenarioConfig(2, kLead, 4.0);
        AuditParams params = makeParams(c, 1, 1, false);
        params.tauHorizon = 2.0 * kLead;
        AuditTotals totals;
        Hooks hooks;
        hooks.promoteAtStart = {0};
        const EvacuationResult r = runAudited(c, mixedAgents(), params, totals, hooks);
        printAudit("control_C", totals, r);
        printControl("horizon_gt_T", totals.lostContacts > 0);
        suite.check(totals.lostContacts > 0, "control C: con horizonte 0.6 > T = 0.3 el auditor reporta contactos previstos");
    }
}

void runHybridBruteTests(TestSuite& suite) {
    std::printf("  alcance trasero: t_c = %.5f s, T = %.2f s\n", kContactTime, kLead);
    testRearEnd(suite);
    testMixed(suite);
    testDense60(suite);
    testControls(suite);
}

// Corrida pesada de N = 200: gobernada por TP5_HEAVY para que `make test` no pague minutos. Una
// superposicion o un contacto perdido persiste mas de 20 pasos (un contacto elastico dura unos 800
// pasos), asi que el muestreo depthStride = 20 y tauStride = 200 es valido.
void runHybridAuditTests(TestSuite& suite) {
    if (std::getenv("TP5_HEAVY") == nullptr) {
        std::puts("hybrid_audit omitida (definir TP5_HEAVY=1)");
        return;
    }
    const EvacuationConfig c = denseConfig(kHeavyAgents, kHeavySide, kHeavySeed, kHeavyMaxTime);
    AuditTotals totals;
    const EvacuationResult r = runAudited(c, generateAgents(c), makeParams(c, 20, 200, false), totals, Hooks{});
    printAudit("dense_n200", totals, r);
    checkZeros(suite, "dense_n200", totals);
    suite.check(r.completed, "dense_n200: la corrida completa");
    suite.check(r.hybridPromotions > 0 && r.hybridReturns > 0, "dense_n200: hubo promociones y retornos");
    suite.check(r.collisions == 0, "dense_n200: collisions == 0");
}

const TestRegistration registration("hybrid_brute", runHybridBruteTests);
const TestRegistration auditRegistration("hybrid_audit", runHybridAuditTests);

}  // namespace
