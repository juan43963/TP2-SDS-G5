#pragma once

// Esquema EDMD: el tiempo avanza de evento en evento sobre la trayectoria exacta de
// relaxation.h (D-13). Cola global (min-heap) con contador de generacion por agente
// para invalidar eventos obsoletos (D-18); celdas con eventos de cruce para acotar los
// vecinos candidatos; colision v2 (n_alejar + e_target, pulso de steerInterval) y piso de tiempo `eventGap`
// entre colisiones de un agente (D-16, evita el colapso inelastico).
#include <cstddef>
#include <cstdint>
#include <optional>
#include <utility>
#include <vector>

#include "evacuation.h"
#include "relaxation.h"
#include "sfm.h"

// Promote solo existe en modo con anticipacion (leadTime > 0, Fase 8): aviso de que el agente `a` (y
// `b`, si es >= 0) tendra un contacto dentro de leadTime y debe pasar a TSDMD.
enum class EventType { PairContact, WallContact, CornerContact, DoorCross, Retire, CellCross, Steer, Promote };

// Cota de la velocidad relativa de aproximacion de dos agentes, en unidades de v_d (Fase 8): con ella
// el tamano de celda del modo con anticipacion garantiza que todo par que pueda tocarse dentro de
// leadTime esta en celdas vecinas, de modo que el aviso llega con el adelanto completo.
inline constexpr double kLeadRelativeSpeedFactor = 2.0;

// Para PairContact (y Promote de un par) `b` es el segundo agente; para Promote de pared/esquina b = -1; para WallContact `b` = 2*segmento + (lado < 0);
// para CornerContact `b` es el indice de esquina; para CellCross `b` es la frontera
// (0 -x, 1 +x, 2 -y, 3 +y). `a` es siempre el indice (== id) del agente principal.
struct EdmdEvent {
    double time = 0.0;
    EventType type = EventType::DoorCross;
    int a = -1;
    int b = -1;
    std::uint64_t generationA = 0;
    std::uint64_t generationB = 0;
    std::uint64_t sequence = 0;
};

// Comparador de min-heap (std::push_heap): menor tiempo primero, empate por menor `sequence`.
struct EventLater {
    bool operator()(const EdmdEvent& l, const EdmdEvent& r) const {
        if (l.time != r.time) return l.time > r.time;
        return l.sequence > r.sequence;
    }
};

struct EdmdCounters {
    long long processed = 0;
    long long stale = 0;
    long long collisions = 0;
    long long floorCollisions = 0;
    long long steerEvents = 0;
    long long cellCrossings = 0;
    long long compactions = 0;
    long long inapplicable = 0;
    long long projectedAgents = 0;   // agentes vecinos desplazados por separateOverlaps
    long long projectionCaps = 0;    // correcciones que agotaron su presupuesto
    long long timeRegressions = 0;
};

class EdmdEngine {
public:
    // leadTime > 0 (modo con anticipacion, hibrido): ningun contacto se resuelve por colision; cada
    // contacto predicho se programa como un evento Promote en t_contacto - leadTime (D-25). Con 0 el
    // motor es el EDMD puro de la Fase 7.
    EdmdEngine(const EvacuationConfig& config, std::vector<Agent> agents, double leadTime = 0.0);

    // Procesa el proximo evento valido; false si no quedan agentes o eventos, se pasa maxTime
    // o se alcanza maxEvents.
    bool step();
    // Tiempo del proximo evento valido (descarta obsoletos de la cima) o kInfinity.
    double nextEventTime();

    double now() const { return now_; }
    bool finished() const;
    // Estado exacto en `time` (trayectoria de D-13, sin mutar), scheme = 1, orden por id.
    std::vector<Agent> snapshot(double time) const;
    const EdmdCounters& counters() const { return counters_; }
    EvacuationResult result() const;

    // ---- Ganchos del hibrido (Fase 8): traspaso de agentes entre EDMD y TSDMD ----
    // Ids (ordenados, sin duplicados, residentes) avisados por eventos Promote desde la ultima llamada.
    std::vector<int> takePromotions();
    // Fija el reloj en `t` (precondicion: ningun evento valido con tiempo menor que t); no toca
    // el tiempo del ultimo evento. Nunca retrocede.
    void advanceTo(double t);
    // EDMD -> TSDMD: devuelve el estado exacto en now() (scheme = 0, aceleracion 0) y saca al agente
    // del motor invalidando todos sus eventos (sube su generacion, D-18, D-29).
    Agent release(int id);
    // TSDMD -> EDMD: reinstala al agente en now() conservando x y v; la relajacion a v_d arranca con
    // la v actual (SCEN-06, D-29) y se reprograman sus eventos.
    void admit(const Agent& agent);
    std::size_t residentCount() const { return static_cast<std::size_t>(alive_); }
    bool isResident(int id) const { return records_[static_cast<std::size_t>(id)].alive; }
    Relaxation motionOf(int id) const { return stateOf(static_cast<std::size_t>(id), now_); }
    double radiusOf(int id) const { return records_[static_cast<std::size_t>(id)].radius; }
    double cellSize() const { return cellSize_; }
    // Tiempo relativo a now() hasta el primer contacto con aproximacion, dentro de `horizon`, de un
    // agente con movimiento libre (Relaxation{x, v, v_d*versor al target segun status, now()}) contra
    // paredes, esquinas y agentes residentes; kInfinity si no hay (tau_c de D-26).
    double freeContactTime(const Agent& agent, double horizon) const;
    // Tiempo relativo a now() hasta el primer contacto con aproximacion, dentro de `horizon`, entre el
    // residente `id` (trayectoria exacta) y un cuerpo externo de radio `bodyRadius` cuyo movimiento
    // `body` se evalua en now() (escaneo de pares mixtos, D-24, D-25); kInfinity si no hay. Usa el mismo
    // kernel que pairEventTime.
    double contactTimeWithBody(int id, const Relaxation& body, double bodyRadius, double horizon) const;
    // Celdas del motor (D-18): ids residentes de la celda (cx, cy); vacio fuera de rango.
    const std::vector<int>& cellResidents(int cx, int cy) const;
    int cellCoordX(double x) const;
    int cellCoordY(double y) const;
    int gridCols() const { return cols_; }
    int gridRows() const { return rows_; }

    // ---- Soporte de verificacion (Plan 03, D-19): el motor no usa nada de lo que sigue. ----
    // Recorrer la cola sin consumirla.
    const std::vector<EdmdEvent>& queue() const { return heap_; }
    // Primer evento valido de la cola de cualquier tipo (descarta obsoletos de la cima).
    std::optional<EdmdEvent> peekNext();
    // Evento valido de menor tiempo entre los tipos fisicos (par, pared, esquina, puerta,
    // retiro) recorriendo todo el heap; no modifica la cola. CellCross y Steer no cuentan.
    std::optional<EdmdEvent> peekNextPhysical() const;
    // Lo mismo sin celdas ni cola: enumera todos los agentes vivos y pares i < j con los
    // mismos helpers de tiempo y el estado actual.
    std::optional<EdmdEvent> bruteForceNextPhysical() const;
    const EdmdEvent& lastEvent() const { return lastEvent_; }
    std::uint64_t generation(int id) const { return records_[static_cast<std::size_t>(id)].collisionCount; }
    std::size_t heapSize() const { return heap_.size(); }
    // Control negativo de evento perdido: quita de la cola todas las entradas validas con la
    // identidad tipo/a/b del proximo evento fisico (incluidos duplicados del cruce de celda).
    bool discardNextPhysicalForTesting();
    // Control negativo de evento espurio: empuja un evento arbitrario.
    void injectEventForTesting(const EdmdEvent& event);

private:
    struct Record {
        Relaxation motion;
        Vector2 target;
        AgentStatus status = AgentStatus::InRoom;
        double radius = 0.0;
        double pulseEnd = -1.0;  // fin del pulso post-colision (< 0: sin pulso vigente)
        int id = 0;
        bool alive = true;
        std::uint64_t collisionCount = 0;      // generacion vigente (D-18)
        // Ultima colision de cada contacto vigente (clave: otro agente >= 0, pared -(1+codigo),
        // esquina -(100+indice)); solo se conservan los que todavia restringen el piso eventGap.
        std::vector<std::pair<int, double>> contacts;
        int cellX = 0;
        int cellY = 0;
    };

    // cola
    void push(EdmdEvent event);
    EdmdEvent makeEvent(EventType type, double time, int a, int b) const;
    bool isValid(const EdmdEvent& event) const;
    void compact();

    // estado
    Relaxation stateOf(std::size_t index, double time) const;
    void sync(std::size_t index);
    void retarget(std::size_t index, Vector2 target);
    // Punto al que apuntan los agentes en sala: el centro de la puerta apenas por debajo de la linea
    // (sin ese margen, un agente sobre la linea apunta en horizontal y nunca cruza: Zeno en y -> 0).
    Vector2 doorAim() const { return {room_.doorCenter.x, room_.doorCenter.y - config_.doorAimBelow}; }
    Vector2 desiredFrom(const Record& r, Vector2 position, Vector2 fallback) const;
    void applyCollisionState(std::size_t index, Vector2 position, Vector2 velocity);

    // celdas
    void cellInsert(std::size_t index);
    void cellErase(std::size_t index);
    void cellRelocate(std::size_t index);

    // tiempos de evento (unica fuente de tiempos de contacto: scheduleAgent y fuerza bruta)
    double lastContact(std::size_t i, int key) const;
    void markContact(std::size_t i, int key);
    double floorStart(std::size_t i, int key) const;
    double pairEventTime(std::size_t i, std::size_t j, double notBefore) const;
    int wallSide(std::size_t i, std::size_t segment) const;
    double wallEventTime(std::size_t i, std::size_t segment, int side) const;
    double cornerEventTime(std::size_t i, std::size_t corner) const;
    double doorOrRetireTime(std::size_t i) const;

    // programacion
    // Programa un contacto predicho: colision en el EDMD puro, aviso Promote en modo con anticipacion.
    void pushContact(EventType type, double time, int a, int b);
    void pushPair(std::size_t i, std::size_t j, double notBefore);
    void pushCellCross(std::size_t i);
    void pushNeighborPairs(std::size_t i, int skip, bool onlyHigher);
    void scheduleAgent(std::size_t i, int skip, bool onlyHigher);
    void scheduleMoved(const std::vector<std::size_t>& moved);

    // procesamiento
    void processPair(const EdmdEvent& event);
    void processWall(const EdmdEvent& event);
    void processCorner(const EdmdEvent& event);
    // Correccion de posicion tras un choque (solo posiciones, v2): devuelve los agentes movidos
    // (incluye first y second).
    std::vector<std::size_t> separateOverlaps(std::size_t first, std::size_t second);
    void finishFixedCollision(std::size_t i, int key, Vector2 position, Vector2 velocity, double depth);

    EvacuationConfig config_;
    Room room_;
    std::vector<Record> records_;
    std::vector<EdmdEvent> heap_;
    std::vector<std::vector<int>> cells_;
    EdmdCounters counters_;
    EvacuationResult result_;
    EdmdEvent lastEvent_;
    std::vector<int> promoted_;    // avisos Promote pendientes de takePromotions()
    std::vector<char> movedMask_;  // marca de los agentes reprogramados juntos (evita programar dos veces un par)
    std::uint64_t sequence_ = 0;
    double leadTime_ = 0.0;
    double now_ = 0.0;
    double lastEventTime_ = 0.0;
    double cellSize_ = 0.0;
    double originX_ = 0.0;
    double originY_ = 0.0;
    int cols_ = 0;
    int rows_ = 0;
    std::size_t compactLimit_ = 0;
    std::size_t compactBase_ = 0;
    int alive_ = 0;
    bool timedOut_ = false;
    bool capped_ = false;
};

EvacuationResult runEdmd(const EvacuationConfig& config, std::vector<Agent> agents,
                         const FrameSink& sink);
