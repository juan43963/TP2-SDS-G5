#pragma once

// Tipos y constantes del dominio (sin logica). Parametros de Helbing, Farkas y
// Vicsek (2000), Nature 407; el modelo se usa sin fuerza social (D-01).
#include <cstdint>
#include <vector>

#include "vector2.h"

struct SfmParams {
    double stiffness = 1.2e5;   // k [kg/s^2]
    double friction = 0.0;      // kappa [kg/(m s)]
    double mass = 80.0;         // [kg]
    double tau = 0.5;           // [s]
    double desiredSpeed = 1.5;  // v_d [m/s]
};

enum class AgentStatus { InRoom, Exiting };
enum class Scheme { Tsdmd = 0, Edmd = 1, Hybrid = 2 };

struct Agent {
    int id = 0;
    Vector2 position;
    Vector2 velocity;
    Vector2 acceleration;
    Vector2 target;
    double radius = 0.0;
    AgentStatus status = AgentStatus::InRoom;
    int scheme = 0;  // columna `scheme` de la salida: 0 TSDMD, 1 EDMD
};

struct WallSegment {
    Vector2 a;
    Vector2 b;
};

struct WallSet {
    std::vector<WallSegment> segments;
    std::vector<Vector2> corners;  // bordes de la puerta, como puntos explicitos
};

struct Room {
    double side = 0.0;
    double doorWidth = 0.0;
    double exitDistance = 0.0;
    Vector2 doorCenter;
    Vector2 exitTarget;
    WallSet walls;
};

struct EvacuationConfig {
    int agentCount = 500;
    double side = 50.0;
    double doorWidth = 0.8;
    double radiusMin = 0.18;
    double radiusMax = 0.25;
    double exitDistance = 1.0;
    SfmParams sfm;
    double dt = 1e-4;
    double dt2 = 0.1;
    double maxTime = 3000.0;
    std::uint64_t seed = 1;
    Scheme scheme = Scheme::Tsdmd;
    int maxPlacementAttemptsPerAgent = 100000;
    // Parametros del motor EDMD (D-15, D-16, D-17); TSDMD los ignora.
    double eventGap = 5e-3;         // [s] piso de tiempo entre colisiones de un agente
    double steerInterval = 0.1;     // [s] duracion del pulso post-colision y periodo de re-apuntado
    double doorAimBelow = 0.0;      // [m] el agente en sala apunta a la puerta desplazada hacia afuera (la CLI usa 0.01; evita Zeno sobre la linea)
    bool separateOverlaps = true;   // correccion de posicion tras un choque (false = solo para mostrar el "antes")
    long long maxEvents = 1000000000LL;  // valvula de seguridad del lazo de eventos
    // Parametros del hibrido (D-26, D-28); solo --scheme hybrid.
    double hybridT = 0.5;      // [s] umbral T: TSDMD si tau_c < T (0 = EDMD puro, >= tmax = TSDMD puro)
    double hybridAlpha = 2.0;  // histeresis (D-28): vuelve a EDMD solo si tau_c > alpha*T
    // El retorno TSDMD -> EDMD se evalua cada `returnStride` pasos dt. Es el lado seguro: quedarse en TSDMD
    // de mas nunca pierde un contacto (lo resuelve el resorte). La promocion y el escaneo de pares
    // mixtos siguen en cada limite. 1 = evaluar en todos los limites.
    int returnStride = 20;
};

struct EvacuationResult {
    long long steps = 0;
    double finalTime = 0.0;
    double evacuationTime = -1.0;  // instante en que el ultimo agente cruza la puerta
    double clearTime = -1.0;       // instante del ultimo retiro
    int crossed = 0;
    int removed = 0;
    int inRoomFinal = 0;
    int wallBreaches = 0;
    double maxAgentOverlap = 0.0;
    double maxWallOverlap = 0.0;
    double simulationMs = 0.0;
    double outputMs = 0.0;
    bool completed = false;
    // Contadores del motor EDMD (0 en TSDMD).
    long long events = 0;
    long long staleEvents = 0;
    long long collisions = 0;
    long long floorCollisions = 0;
    long long timeRegressions = 0;  // debe ser 0: la cola nunca entrega un evento en el pasado
    // Contadores del hibrido (0 en TSDMD y EDMD).
    long long hybridPromotions = 0;          // pasajes EDMD -> TSDMD
    long long hybridReturns = 0;             // pasajes TSDMD -> EDMD
    long long hybridSteps = 0;               // pasos dt del subconjunto TSDMD
    long long tsdmdAgentSteps = 0;           // suma de agentes TSDMD por paso (costo del lado TSDMD)
    long long hybridMixedPromotions = 0;     // promociones por par mixto (las llena el Plan 02)
    long long hybridQuickRepromotions = 0;   // re-promociones tras un retorno rapido (Plan 02)
};

// Sala [0,side]^2 con puerta centrada en la pared inferior (D-07).
Room makeRoom(double side, double doorWidth, double exitDistance);

// Lanza std::invalid_argument nombrando el flag y el valor.
void validateConfig(const EvacuationConfig& config);
