#pragma once

#include <cstdint>
#include <functional>
#include <string>
#include <string_view>
#include <vector>

struct Vec2 {
    double x = 0.0;
    double y = 0.0;
};

inline Vec2 operator+(Vec2 a, Vec2 b) { return {a.x + b.x, a.y + b.y}; }
inline Vec2 operator-(Vec2 a, Vec2 b) { return {a.x - b.x, a.y - b.y}; }
inline Vec2 operator*(double s, Vec2 a) { return {s * a.x, s * a.y}; }
inline Vec2& operator+=(Vec2& a, Vec2 b) {
    a.x += b.x;
    a.y += b.y;
    return a;
}
inline Vec2& operator-=(Vec2& a, Vec2 b) {
    a.x -= b.x;
    a.y -= b.y;
    return a;
}
inline double dot(Vec2 a, Vec2 b) { return a.x * b.x + a.y * b.y; }
inline double norm2(Vec2 a) { return dot(a, a); }

enum class InitMethod { Rsa, Lattice, Auto };
InitMethod parseInitMethod(std::string_view);  // "rsa" | "lattice" | "auto", otro: std::invalid_argument
const char* initMethodName(InitMethod);

// Los defaults son los valores del enunciado. x0 igual a radius deja los dos
// obstaculos en contacto en el centro, que es la configuracion de 2.1b.
struct BilliardParams {
    double R = 0.51;
    double radius = 0.0175;
    double mass = 0.025;
    double k = 1e4;
    double v0 = 1.0;
    int N = 100;
    bool obstacles = true;
    double x0 = 0.0175;
    double dt = 1e-4;
    double tf = 10.0;
    long long every = 100;
    std::uint64_t seed = 1;
    bool stopWhenAllUsed = false;
    bool stopAtT90 = false;
    InitMethod init = InitMethod::Auto;
};

inline constexpr long long kMaxBilliardSteps = 1'000'000'000;
inline constexpr long long kMaxFrameRows = 100'000'000;
inline constexpr int kRsaMaxAttemptsPerParticle = 100'000;
inline constexpr double kX0Tolerance = 1e-12;
// Separacion extra de la red hexagonal: a = 2 radius + kLatticeGap. Con 1 mm hay 666 sitios
// en x0 = radius y queda un jitter de gap/2 por particula; con 0.5 mm no queda lugar para
// el jitter y con 2 mm la capacidad baja de 650.
inline constexpr double kLatticeGap = 1e-3;
// En modo auto, RSA hasta este N y red por encima (RSA satura cerca de N = 440).
inline constexpr int kAutoRsaMaxN = 400;
inline constexpr int kMaxGridSide = 2048;  // acota los arreglos M x M (y la red de la Plan 02-03)

void validateParams(const BilliardParams&);          // std::invalid_argument con flag y valor
long long billiardStepCount(const BilliardParams&);  // K = tf/dt, validado
int cimGridSize(const BilliardParams&);              // floor(2R / (2 radius)), al menos 1; 29 por defecto
int conversionTarget90(int N);                       // (9N + 9) / 10 = ceil(0.9 N) en enteros

struct InitialState {
    std::vector<Vec2> pos;
    std::vector<Vec2> vel;
    std::string method;  // metodo resuelto: "rsa" o "lattice", nunca "auto"
};

// Sitios de la red triangular (a = 2 radius + kLatticeGap) validos para la pared y los
// obstaculos, en orden determinista (filas j ascendentes, luego i ascendente).
std::vector<Vec2> latticeSites(const BilliardParams&);
int latticeCapacity(const BilliardParams&);  // latticeSites(p).size()

// std::invalid_argument ("capacidad") si N > latticeCapacity, para cualquier modo.
InitialState generateInitialState(const BilliardParams&);
void verifyInitialState(const BilliardParams&, const InitialState&);  // std::logic_error ante cualquier violacion

struct ForceWorkspace {
    int M = 0;
    double cellSize = 0.0;
    std::vector<int> head;
    std::vector<int> next;
};

ForceWorkspace makeForceWorkspace(const BilliardParams&, int particleCount);

// Cell Index Method no periodico, reconstruido en cada llamada. touchingObstacle
// queda ordenado por id y sin repetidos.
void computeForces(const BilliardParams&, const std::vector<Vec2>& pos, ForceWorkspace&,
                   std::vector<Vec2>& force, std::vector<int>& touchingObstacle);

enum class StopReason { Tf, AllUsed, T90 };
const char* stopReasonName(StopReason);  // "tf" "all_used" "t90"

using FrameSink = std::function<void(long long step, double t, const std::vector<Vec2>& pos,
                                     const std::vector<Vec2>& vel,
                                     const std::vector<unsigned char>& used)>;
using ConversionSink = std::function<void(long long step, double t, int id)>;

struct SimulationResult {
    long long finalStep = 0;
    double finalTime = 0.0;
    int usedCount = 0;
    StopReason stop = StopReason::Tf;
    double simulationMs = 0.0;
    double frameIoMs = 0.0;
};

// Verlet original. El frame k lleva las posiciones r_k, la velocidad por
// diferencia centrada (r_{k+1} - r_{k-1}) / (2 dt) y el estado posterior a las
// conversiones del paso k. Un FrameSink vacio significa "sin frames".
SimulationResult simulate(const BilliardParams&, const InitialState&, const FrameSink& frames,
                          const ConversionSink& conversions);
