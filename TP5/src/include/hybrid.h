#pragma once

// Esquema hibrido EDMD+TSDMD (Fase 8). Cada agente vive en exactamente uno de los dos esquemas:
// los residentes en EDMD estan en un EdmdEngine en modo con anticipacion y los agentes en TSDMD en
// un vector propio que se integra con Velocity Verlet (D-21: un unico reloj, paso dt con eventos
// EDMD entre pasos).
//
//   * Criterio (D-26): tau_c es el tiempo hasta el proximo contacto del agente (vecinos, paredes,
//     esquinas) sobre la trayectoria predicha. EDMD -> TSDMD si tau_c < T; TSDMD -> EDMD solo si
//     tau_c > alpha*T, sin contacto ni solape y sin colapso (D-28, D-29): histeresis.
//   * Pares mixtos (D-24, D-25, D-27): un residente EDMD que se acerca a un agente TSDMD no tiene
//     eventos que lo avisen; en cada limite de grilla un escaneo recorre los residentes de las 3x3
//     celdas EDMD de cada agente TSDMD y promueve al que ya toca o va a tocar dentro de T (filtro de
//     distancia solido + EdmdEngine::contactTimeWithBody con el agente TSDMD a velocidad constante).
//   * El retorno usa las banderas de contacto del paso de fuerzas (ForceWorkspace::touching) y se
//     decide un agente por vez, en orden de id, reconstruyendo las fuerzas tras cada retorno.
//   * El contacto agente-agente / agente-pared / agente-esquina NUNCA lo resuelve EDMD con
//     restitucion cuando T > 0: lo resuelve el resorte SFM del TSDMD, por promocion previa al
//     contacto (D-24, D-25). T = 0 es el EDMD puro.
//   * Sincronizacion (D-21): se procesan todos los eventos EDMD con tiempo < (k+1)*dt, despues se
//     integra solo el subconjunto TSDMD y recien en el limite de la grilla se hacen los pasajes.
//     Con el conjunto TSDMD vacio y sin promociones pendientes no hay limites: el reloj salta de
//     evento en evento (D-22).
//   * Extremos (D-23, HYB-05): T >= tmax significa que todo agente cumple tau_c < T en todo
//     instante (tau_c solo se busca hasta tmax), es decir 100% TSDMD; T = 0 significa que ningun
//     agente cumple tau_c < 0, es decir 100% EDMD; en ambos extremos el resultado es el del
//     esquema puro con la misma semilla (runHybrid delega en runEvacuation / runEdmd).
#include <cstddef>
#include <vector>

#include "edmd.h"
#include "edmd_kernel.h"
#include "evacuation.h"
#include "forces.h"
#include "sfm.h"

// D-29: un vecino a menos de kNearGap [m] que se acerca a mas de kClosingTolerance [m/s] bloquea el
// retorno a EDMD (velocidad de colapso).
inline constexpr double kNearGap = 0.02;
inline constexpr double kClosingTolerance = 0.05;

// D-26: promocion EDMD -> TSDMD (estricta).
bool promoteCriterion(double tauC, double T);
// D-28 y D-29: retorno TSDMD -> EDMD. `touching`: contacto o solape vigente (agente, pared o
// esquina). `minGap` [m]: menor huelgo a un vecino; `closingSpeed` [m/s]: mayor velocidad de
// acercamiento entre los vecinos con huelgo menor que kNearGap (colapso si > kClosingTolerance).
bool returnCriterion(double tauC, double T, double alpha, bool touching, double minGap,
                     double closingSpeed);

struct HybridCounters {
    long long promotions = 0;
    long long returns = 0;
    long long gridSteps = 0;
    long long tsdmdAgentSteps = 0;
    long long mixedPromotions = 0;    // promociones por el escaneo de pares mixtos (EDMD que se acerca a TSDMD)
    long long quickRepromotions = 0;  // promociones a menos de T de su propio retorno (oscilacion, HYB-02)
    double maxSpeedSeen = 0.0;        // mayor |v| de un agente TSDMD en un limite de grilla
};

class HybridEngine {
public:
    HybridEngine(const EvacuationConfig& config, std::vector<Agent> agents);

    // Avanza UNA cosa: un evento EDMD (si su tiempo es estrictamente menor que el proximo limite
    // de grilla) o un limite de grilla. false si termino, se paso de tmax o se alcanzo maxEvents.
    bool step();
    // Tiempo de la proxima cosa (evento o limite) o kInfinity.
    double nextTime();
    // Tiempo del ultimo evento procesado o limite ejecutado.
    double now() const { return now_; }
    bool finished() const;
    bool lastStepWasBoundary() const { return lastStepWasBoundary_; }
    // Indice k del ultimo limite de grilla ejecutado (tiempo k*dt).
    long long boundaryIndex() const { return lastBoundary_; }
    // Verdadero si la proxima cosa es un limite de grilla (y no un evento EDMD) y su indice.
    bool nextIsBoundary();
    long long nextBoundaryIndex() const { return nextBoundary_; }

    std::size_t tsdmdCount() const { return s_.size(); }
    // 0 TSDMD, 1 EDMD, -1 retirado.
    int schemeOf(int id) const;
    // Todos los agentes vivos ordenados por id con su `scheme`. Con el conjunto TSDMD vacio es
    // valido para cualquier time >= now(); si no, solo en time == now() (los agentes TSDMD se
    // devuelven en su estado vigente, el del ultimo limite).
    std::vector<Agent> snapshot(double time) const;

    // Ganchos de prueba (Plan 02): pide que el agente `id` pase a TSDMD en el proximo limite (como un
    // aviso Promote) y activa/desactiva el escaneo de pares mixtos (control negativo de D-25).
    void requestPromotionForTesting(int id);
    void setMixedScanEnabledForTesting(bool enabled) { mixedScanEnabled_ = enabled; }
    // Control negativo de D-29 (Plan 04): con falso el retorno ignora el contacto, el huelgo y la
    // velocidad de acercamiento (touching = false, minGap = kInfinity, closingSpeed = 0); el resto del
    // criterio (tau_c > alpha*T) no cambia. Por defecto verdadero.
    void setReturnGuardEnabledForTesting(bool enabled) { returnGuard_ = enabled; }

    const HybridCounters& counters() const { return counters_; }
    const EdmdEngine& edmd() const { return edmd_; }
    EvacuationResult result() const;

private:
    struct Proximity {
        bool touching = false;
        double minGap = kInfinity;
        double closingSpeed = 0.0;
    };

    void runBoundary();
    void gatherPromotions();
    void promote(int id);
    void rebuildForces();
    Proximity proximityOf(std::size_t index) const;
    double tsdmdContactTime(std::size_t index, double horizon) const;
    bool tryReturn(std::size_t index);
    // Agentes EDMD que deben pasar a TSDMD por un par mixto (D-24, D-25, D-26, D-27), ordenados por id.
    std::vector<int> scanMixedPairs();

    // El orden de declaracion es el de inicializacion: inTsdmd_ y ws_ dependen del numero de
    // agentes, que edmd_ consume (move) del vector de entrada.
    EvacuationConfig config_;
    Room room_;
    std::vector<char> inTsdmd_;      // por id: 1 si esta en el subconjunto TSDMD
    std::vector<double> lastReturnTime_;  // por id: instante de su ultimo retorno a EDMD (-inf si nunca)
    std::vector<char> scanMark_;     // por id: marca transitoria del escaneo de pares mixtos
    ForceWorkspace ws_;
    EdmdEngine edmd_;
    std::vector<Agent> s_;           // subconjunto TSDMD, ordenado por id
    ContactStats stats_;
    std::vector<int> pending_;      // ids avisados por Promote, a pasar en el proximo limite
    HybridCounters counters_;

    // Contadores del lado TSDMD para result().
    int crossed_ = 0;
    int removed_ = 0;
    int wallBreaches_ = 0;
    double evacuationTime_ = -1.0;
    double clearTime_ = -1.0;

    long long nextBoundary_ = 0;
    long long lastBoundary_ = 0;
    double now_ = 0.0;
    bool mixedScanEnabled_ = true;
    bool returnGuard_ = true;
    bool gridMode_ = false;
    bool lastStepWasBoundary_ = false;
    bool timedOut_ = false;
    bool capped_ = false;
};

EvacuationResult runHybrid(const EvacuationConfig& config, std::vector<Agent> agents,
                           const FrameSink& sink);
