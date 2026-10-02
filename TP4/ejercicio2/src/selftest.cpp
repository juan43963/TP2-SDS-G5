#include <algorithm>
#include <cmath>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <numbers>
#include <random>
#include <stdexcept>
#include <string>
#include <vector>

#include "billiard.h"
#include "billiard_cli.h"
#include "brute_force_forces.h"
#include "test_support.h"

namespace {

std::string fmt(const char* format, int a, int b) {
    char buffer[160];
    std::snprintf(buffer, sizeof buffer, format, a, b);
    return buffer;
}

// count posiciones uniformes en el disco de radio radiusMax.
std::vector<Vec2> randomDisk(std::mt19937_64& rng, double radiusMax, int count) {
    std::uniform_real_distribution<double> unit(0.0, 1.0);
    std::vector<Vec2> pos;
    pos.reserve(static_cast<std::size_t>(count));
    for (int i = 0; i < count; ++i) {
        const double rho = radiusMax * std::sqrt(unit(rng));
        const double phi = 2.0 * std::numbers::pi * unit(rng);
        pos.push_back({rho * std::cos(phi), rho * std::sin(phi)});
    }
    return pos;
}


std::vector<char*> toArgv(std::vector<std::string>& storage) {
    std::vector<char*> argv;
    for (std::string& s : storage) argv.push_back(s.data());
    return argv;
}

// true si parseBilliardOptions rechaza los argumentos con std::invalid_argument.
bool rejects(const std::vector<std::string>& args) {
    std::vector<std::string> storage = {"billiard"};
    storage.insert(storage.end(), args.begin(), args.end());
    std::vector<char*> argv = toArgv(storage);
    try {
        parseBilliardOptions(static_cast<int>(argv.size()), argv.data());
    } catch (const std::invalid_argument&) {
        return true;
    }
    return false;
}

BilliardOptions parseOk(const std::vector<std::string>& args) {
    std::vector<std::string> storage = {"billiard"};
    storage.insert(storage.end(), args.begin(), args.end());
    std::vector<char*> argv = toArgv(storage);
    return parseBilliardOptions(static_cast<int>(argv.size()), argv.data());
}

std::vector<std::string> readLines(const std::filesystem::path& path) {
    std::vector<std::string> lines;
    std::ifstream in(path);
    std::string line;
    while (std::getline(in, line)) lines.push_back(line);
    return lines;
}

bool startsWith(const std::string& text, const char* prefix) {
    return text.rfind(prefix, 0) == 0;
}

bool endsWith(const std::string& text, const std::string& suffix) {
    return text.size() >= suffix.size() &&
           text.compare(text.size() - suffix.size(), suffix.size(), suffix) == 0;
}

// Lee el contenido de un FILE* de lectura/escritura (std::tmpfile) desde el inicio.
std::string slurp(std::FILE* f) {
    std::rewind(f);
    std::string text;
    char buffer[4096];
    std::size_t got = 0;
    while ((got = std::fread(buffer, 1, sizeof buffer, f)) > 0) text.append(buffer, got);
    return text;
}

struct Frame {
    long long step = 0;
    double t = 0.0;
    std::vector<Vec2> pos;
    std::vector<Vec2> vel;
    std::vector<unsigned char> used;
};

struct Conversion {
    long long step = 0;
    double t = 0.0;
    int id = -1;
};

struct CaseRun {
    std::vector<Frame> frames;
    std::vector<Conversion> conversions;
    SimulationResult result;
};

// Corre simulate con un estado armado a mano, capturando cada frame y cada conversion.
CaseRun runCase(const BilliardParams& p, const std::vector<Vec2>& pos,
                const std::vector<Vec2>& vel) {
    CaseRun run;
    const InitialState state{pos, vel, "test"};
    const FrameSink frames = [&](long long step, double t, const std::vector<Vec2>& q,
                                 const std::vector<Vec2>& v,
                                 const std::vector<unsigned char>& used) {
        run.frames.push_back({step, t, q, v, used});
    };
    const ConversionSink conversions = [&](long long step, double t, int id) {
        run.conversions.push_back({step, t, id});
    };
    run.result = simulate(p, state, frames, conversions);
    return run;
}

// Un episodio empieza en un frame donde la condicion pasa de falsa a verdadera.
int countEpisodes(const std::vector<bool>& flags) {
    int episodes = 0;
    bool previous = false;
    for (const bool flag : flags) {
        if (flag && !previous) ++episodes;
        previous = flag;
    }
    return episodes;
}

double kineticEnergy(const BilliardParams& p, const Frame& f) {
    double sum = 0.0;
    for (const Vec2& v : f.vel) sum += norm2(v);
    return 0.5 * p.mass * sum;
}

bool validates(const BilliardParams& p) {
    try {
        validateParams(p);
    } catch (const std::invalid_argument&) {
        return false;
    }
    return true;
}

bool containsText(const std::exception& e, const char* text) {
    return std::string(e.what()).find(text) != std::string::npos;
}

bool sameState(const InitialState& a, const InitialState& b) {
    if (a.pos.size() != b.pos.size() || a.vel.size() != b.vel.size()) return false;
    for (std::size_t i = 0; i < a.pos.size(); ++i) {
        if (a.pos[i].x != b.pos[i].x || a.pos[i].y != b.pos[i].y || a.vel[i].x != b.vel[i].x ||
            a.vel[i].y != b.vel[i].y) {
            return false;
        }
    }
    return true;
}

bool allFiniteInside(const CaseRun& run, double R) {
    for (const Frame& f : run.frames) {
        for (const Vec2& q : f.pos) {
            if (!std::isfinite(q.x) || !std::isfinite(q.y) || !(norm2(q) < R * R)) return false;
        }
        for (const Vec2& v : f.vel) {
            if (!std::isfinite(v.x) || !std::isfinite(v.y)) return false;
        }
    }
    return true;
}

// Fuerzas por CIM contra el oraculo O(N^2) con la particula imagen literal.
void testForceKernel(TestSuite& suite) {
    const BilliardParams defaults;
    suite.check(cimGridSize(defaults) == 29, "cimGridSize con los defaults es 29");

    ContactCounts total;
    const double r = defaults.radius;
    const double x0s[4] = {r, 0.25, defaults.R - r, 0.0};
    for (int cfg = 0; cfg < 4; ++cfg) {
        for (int seed = 1; seed <= 3; ++seed) {
            BilliardParams p;
            p.obstacles = cfg < 3;
            p.x0 = x0s[cfg];
            std::mt19937_64 rng(static_cast<std::uint64_t>(1000 * cfg + seed));
            std::vector<Vec2> pos = randomDisk(rng, p.R, 400);
            for (int a = 0; a < 4; ++a) {  // fuera del cuadrado [-R, R]^2
                const double angle = a * std::numbers::pi / 2.0;
                pos.push_back({0.52 * std::cos(angle), 0.52 * std::sin(angle)});
            }

            ForceWorkspace ws = makeForceWorkspace(p, static_cast<int>(pos.size()));
            std::vector<Vec2> fCim;
            std::vector<int> touchCim;
            computeForces(p, pos, ws, fCim, touchCim);
            std::vector<Vec2> fRef;
            std::vector<int> touchRef;
            const ContactCounts counts = bruteForceForces(p, pos, fRef, touchRef);

            double maxRef = 0.0;
            for (const Vec2& f : fRef) maxRef = std::max(maxRef, std::sqrt(norm2(f)));
            double maxDiff = 0.0;
            for (std::size_t i = 0; i < pos.size(); ++i) {
                maxDiff = std::max(maxDiff, std::sqrt(norm2(fCim[i] - fRef[i])));
            }
            suite.check(maxDiff <= 1e-9 * (1.0 + maxRef),
                        fmt("fuerzas CIM = oraculo (config %d, semilla %d)", cfg, seed));
            suite.check(touchCim == touchRef,
                        fmt("contactos con obstaculos identicos (config %d, semilla %d)", cfg,
                            seed));
            suite.check(counts.pairs >= 50 && counts.wall >= 1,
                        fmt("la config %d, semilla %d ejercita pares y pared", cfg, seed));
            if (p.obstacles) {
                suite.check(counts.obstacle >= 1,
                            fmt("la config %d, semilla %d ejercita obstaculos", cfg, seed));
            }
            total.pairs += counts.pairs;
            total.wall += counts.wall;
            total.obstacle += counts.obstacle;
        }
    }
    std::printf("billiard: contactos oraculo pares=%d pared=%d obstaculo=%d\n", total.pairs,
                total.wall, total.obstacle);

    // Newton 3 sin obstaculos y lejos de la pared.
    {
        BilliardParams p;
        p.obstacles = false;
        std::mt19937_64 rng(77);
        const std::vector<Vec2> pos = randomDisk(rng, p.R - p.radius - 0.002, 300);
        ForceWorkspace ws = makeForceWorkspace(p, static_cast<int>(pos.size()));
        std::vector<Vec2> force;
        std::vector<int> touching;
        computeForces(p, pos, ws, force, touching);
        Vec2 sum;
        double sumAbs = 0.0;
        for (const Vec2& f : force) {
            sum += f;
            sumAbs += std::sqrt(norm2(f));
        }
        suite.check(sumAbs > 0.0, "Newton 3: hay contactos de pares");
        suite.check(std::sqrt(norm2(sum)) <= 1e-9 * sumAbs, "Newton 3: la suma de fuerzas es nula");
    }

    // Contacto exacto: R = 0.5, radius = 1/64 (2r = 0.03125 exacto), xi = 0 no hace fuerza.
    {
        BilliardParams p;
        p.R = 0.5;
        p.radius = 1.0 / 64.0;
        p.x0 = 0.25;
        const auto run = [&](const std::vector<Vec2>& pos, std::vector<Vec2>& force,
                             std::vector<int>& touching) {
            ForceWorkspace ws = makeForceWorkspace(p, static_cast<int>(pos.size()));
            computeForces(p, pos, ws, force, touching);
        };
        std::vector<Vec2> force;
        std::vector<int> touching;

        run({{0.28125, 0.0}}, force, touching);
        suite.check(force[0].x == 0.0 && force[0].y == 0.0 && touching.empty(),
                    "contacto exacto con un obstaculo: sin fuerza ni contacto");

        run({{0.0, 0.1}, {0.03125, 0.1}}, force, touching);
        suite.check(force[0].x == 0.0 && force[0].y == 0.0 && force[1].x == 0.0 &&
                        force[1].y == 0.0,
                    "contacto exacto entre dos particulas: sin fuerza");

        run({{0.484375, 0.0}}, force, touching);
        suite.check(force[0].x == 0.0 && force[0].y == 0.0,
                    "contacto exacto con la pared (|r| = R - r): sin fuerza");

        const double eps = std::ldexp(1.0, -20);
        run({{0.484375 + eps, 0.0}}, force, touching);
        const double expected = -p.k * eps;
        suite.check(std::fabs(force[0].x - expected) <= 1e-12 * std::fabs(expected) &&
                        force[0].y == 0.0,
                    "pared con xi = 2^-20: F = -k*xi hacia adentro");
    }
}


void testDynamics(TestSuite& suite) {
    // Choque frontal de dos particulas, sin obstaculos.
    {
        BilliardParams p;
        p.N = 2;
        p.obstacles = false;
        p.dt = 1e-5;
        p.tf = 0.1;
        p.every = 1;
        const CaseRun run = runCase(p, {{-0.1, 0.0}, {0.1, 0.0}}, {{1.0, 0.0}, {-1.0, 0.0}});
        int inContact = 0;
        double maxOverlap = 0.0;
        double maxMomentum = 0.0;
        double maxEnergyDev = 0.0;
        for (const Frame& f : run.frames) {
            const double sep = std::sqrt(norm2(f.pos[1] - f.pos[0]));
            if (sep < 2.0 * p.radius) ++inContact;
            maxOverlap = std::max(maxOverlap, 2.0 * p.radius - sep);
            // E = KE + k*xi^2/2 en cada frame: con la velocidad centrada el error es O(dt^2);
            // una diferencia hacia adelante lo llevaria a O(dt) (4.5e-3 a este dt).
            const double xi = std::max(0.0, 2.0 * p.radius - sep);
            const double energy = kineticEnergy(p, f) + 0.5 * p.k * xi * xi;
            maxEnergyDev = std::max(maxEnergyDev, std::fabs(energy - 0.025) / 0.025);
            const Vec2 momentum = p.mass * (f.vel[0] + f.vel[1]);
            maxMomentum = std::max({maxMomentum, std::fabs(momentum.x), std::fabs(momentum.y)});
        }
        const double tc = static_cast<double>(inContact) * p.dt;
        std::printf("billiard: tc par = %.6e s\n", tc);
        suite.check(std::fabs(tc - 3.5124e-3) <= 3e-5, "choque frontal: tc = pi*sqrt(mu/k) = 3.5124 ms");
        const double ke0 = 0.025;
        const double keLast = kineticEnergy(p, run.frames.back());
        suite.check(std::fabs(keLast - ke0) / ke0 <= 1e-4, "choque frontal: |dKE|/KE0 <= 1e-4");
        suite.check(maxMomentum <= 1e-12, "choque frontal: |sum m v| <= 1e-12 en todo frame");
        suite.check(maxEnergyDev <= 1e-4,
                    "choque frontal: KE + potencial constante en todo frame (velocidad centrada)");
        const Frame& last = run.frames.back();
        suite.check(last.vel[0].x >= -1.0001 && last.vel[0].x <= -0.9999 &&
                        last.vel[1].x >= 0.9999 && last.vel[1].x <= 1.0001,
                    "choque frontal: las velocidades se intercambian");
        suite.check(std::fabs(maxOverlap - 2.2361e-3) <= 0.02 * 2.2361e-3,
                    "choque frontal: solapamiento maximo 2.2361 mm +- 2 %");
        suite.check(run.conversions.empty(), "choque frontal sin obstaculos: no hay conversiones");
    }

    // Rebote radial en la pared.
    {
        BilliardParams p;
        p.N = 1;
        p.obstacles = false;
        p.dt = 1e-5;
        p.tf = 0.5;
        p.every = 1;
        const CaseRun run = runCase(p, {{0.3, 0.0}}, {{1.0, 0.0}});
        const double limit = p.R - p.radius;
        int inContact = 0;
        double maxOverlap = 0.0;
        double maxRadius = 0.0;
        for (const Frame& f : run.frames) {
            const double rho = std::sqrt(norm2(f.pos[0]));
            if (rho > limit) ++inContact;
            maxOverlap = std::max(maxOverlap, rho - limit);
            maxRadius = std::max(maxRadius, rho);
        }
        const double tc = static_cast<double>(inContact) * p.dt;
        std::printf("billiard: tc pared = %.6e s\n", tc);
        std::printf("billiard: solapamiento max pared = %.6e m\n", maxOverlap);
        suite.check(std::fabs(tc - 4.9673e-3) <= 3e-5, "pared radial: tc = pi*sqrt(m/k) = 4.9673 ms");
        const Vec2 vEnd = run.frames.back().vel[0];
        suite.check(vEnd.x >= -1.0001 && vEnd.x <= -0.9999 && std::fabs(vEnd.y) <= 1e-9,
                    "pared radial: v_salida = -v_entrada");
        suite.check(std::fabs(maxOverlap - 1.5811e-3) <= 0.02 * 1.5811e-3,
                    "pared radial: solapamiento maximo 1.5811 mm +- 2 %");
        suite.check(maxRadius < p.R, "pared radial: la particula nunca sale del circulo");
    }

    // Rebote tangencial (rasante): el momento angular respecto del origen se conserva.
    {
        BilliardParams p;
        p.N = 1;
        p.obstacles = false;
        p.dt = 1e-5;
        p.tf = 1.0;
        p.every = 1;
        const CaseRun run = runCase(p, {{0.0, 0.45}}, {{1.0, 0.0}});
        const double limit = p.R - p.radius;
        const double l0 = -0.01125;
        double maxRel = 0.0;
        double maxRadius = 0.0;
        double worstSpeed = 0.0;
        std::vector<bool> contact;
        for (const Frame& f : run.frames) {
            const Vec2 q = f.pos[0];
            const Vec2 v = f.vel[0];
            const double angular = p.mass * (q.x * v.y - q.y * v.x);
            maxRel = std::max(maxRel, std::fabs(angular - l0) / std::fabs(l0));
            const double rho = std::sqrt(norm2(q));
            maxRadius = std::max(maxRadius, rho);
            contact.push_back(rho > limit);
            if (rho <= limit) worstSpeed = std::max(worstSpeed, std::fabs(std::sqrt(norm2(v)) - 1.0));
        }
        std::printf("billiard: dL/L tangencial = %.3e\n", maxRel);
        suite.check(maxRel <= 1e-9, "pared tangencial: |L - L0|/|L0| <= 1e-9 en todo frame");
        suite.check(countEpisodes(contact) >= 2, "pared tangencial: al menos 2 rebotes");
        suite.check(maxRadius < p.R, "pared tangencial: la particula nunca sale del circulo");
        suite.check(worstSpeed <= 1e-4, "pared tangencial: |v| = 1 fuera del contacto");
    }

    // Conversion unica e irreversible contra un obstaculo; varios rebotes.
    {
        BilliardParams p;
        p.N = 1;
        p.x0 = 0.2;
        p.dt = 1e-5;
        p.tf = 1.0;
        p.every = 1;
        const CaseRun run = runCase(p, {{0.0, 0.0}}, {{1.0, 0.0}});
        const double tConv = run.conversions.empty() ? -1.0 : run.conversions[0].t;
        std::printf("billiard: t conversion = %.6e s\n", tConv);
        suite.check(run.conversions.size() == 1 && run.conversions[0].id == 0,
                    "conversion: exactamente una, con id 0");
        suite.check(std::fabs(tConv - 0.165) <= 2e-5, "conversion: t = 0.165 s +- 2e-5");
        std::vector<bool> contact;
        bool stateOk = true;
        const long long convStep = run.conversions.empty() ? -1 : run.conversions[0].step;
        for (const Frame& f : run.frames) {
            const Vec2 q = f.pos[0];
            contact.push_back(norm2(q - Vec2{-p.x0, 0.0}) < 4.0 * p.radius * p.radius ||
                              norm2(q - Vec2{p.x0, 0.0}) < 4.0 * p.radius * p.radius);
            const unsigned char expected = f.step >= convStep ? 1 : 0;
            if (f.used[0] != expected) stateOk = false;
        }
        suite.check(countEpisodes(contact) >= 3, "conversion: al menos 3 episodios de contacto");
        suite.check(stateOk, "conversion: estado 0 antes del paso de conversion y 1 desde ahi");
    }

    // El contacto entre dos particulas nunca convierte.
    {
        BilliardParams p;
        p.N = 2;
        p.x0 = p.R - p.radius;
        p.dt = 1e-5;
        p.tf = 0.1;
        p.every = 1;
        const CaseRun run = runCase(p, {{-0.1, 0.3}, {0.1, 0.3}}, {{1.0, 0.0}, {-1.0, 0.0}});
        double minSep = 1e9;
        for (const Frame& f : run.frames) {
            minSep = std::min(minSep, std::sqrt(norm2(f.pos[1] - f.pos[0])));
        }
        suite.check(minSep < 2.0 * p.radius, "contacto de pares: las particulas llegan a tocarse");
        suite.check(run.conversions.empty() && run.result.usedCount == 0,
                    "contacto de pares: no convierte");
    }

    // Limites de x0: r y R - r exactos validos, +-1e-6 afuera rechazados.
    {
        BilliardParams base;
        for (const double x0 : {base.radius, base.R - base.radius}) {
            BilliardParams p;
            p.N = 100;
            p.seed = 1;
            p.x0 = x0;
            bool generated = false;
            bool verified = false;
            InitialState state;
            try {
                state = generateInitialState(p);
                generated = state.method == "rsa";
                verifyInitialState(p, state);
                verified = true;
            } catch (const std::exception&) {
            }
            suite.check(generated && verified, "x0 en el borde: N = 100 se genera sin solapes (rsa)");
            p.tf = 0.2;
            p.every = 100;
            bool finite = false;
            try {
                finite = allFiniteInside(runCase(p, state.pos, state.vel), p.R);
            } catch (const std::exception&) {
            }
            suite.check(finite, "x0 en el borde: ninguna particula sale del circulo en 0.2 s");
        }
        BilliardParams p;
        p.x0 = p.radius - 1e-13;
        suite.check(validates(p), "x0 = r - 1e-13 se acepta (tolerancia 1e-12)");
        p.x0 = p.R - p.radius + 1e-13;
        suite.check(validates(p), "x0 = R - r + 1e-13 se acepta (tolerancia 1e-12)");
        p.x0 = p.radius - 1e-6;
        suite.check(!validates(p), "x0 = r - 1e-6 se rechaza");
        p.x0 = p.R - p.radius + 1e-6;
        suite.check(!validates(p), "x0 = R - r + 1e-6 se rechaza");
    }

    // Guarda de no finitos: nunca se repara el estado en silencio.
    {
        BilliardParams p;
        p.N = 1;
        p.obstacles = false;
        p.dt = 1.0;
        p.tf = 10.0;
        bool threw = false;
        bool message = false;
        try {
            runCase(p, {{0.0, 0.0}}, {{1e200, 0.0}});
        } catch (const std::runtime_error& e) {
            threw = true;
            message = containsText(e, "no finita");
        }
        suite.check(threw && message, "guarda: velocidad 1e200 lanza runtime_error con 'no finita'");
    }

    // Generador: determinista por semilla, independiente de dt, falla limpio si satura.
    {
        BilliardParams p;
        p.seed = 7;
        const InitialState a = generateInitialState(p);
        const InitialState b = generateInitialState(p);
        suite.check(sameState(a, b), "generador: misma semilla, estado identico bit a bit");
        BilliardParams q = p;
        q.dt = 1e-5;
        suite.check(sameState(a, generateInitialState(q)), "generador: cambiar solo dt no cambia el estado");
        BilliardParams other = p;
        other.seed = 8;
        suite.check(!sameState(a, generateInitialState(other)), "generador: otra semilla, otro estado");

        BilliardParams crowded;
        crowded.N = 600;
        crowded.init = InitMethod::Rsa;  // con Auto caeria a la red y ya no lanzaria
        bool threw = false;
        bool message = false;
        try {
            generateInitialState(crowded);
        } catch (const std::runtime_error& e) {
            threw = true;
            message = containsText(e, "RSA");
        }
        suite.check(threw && message, "generador: N = 600 por RSA lanza runtime_error con 'RSA'");

        BilliardParams two;
        two.N = 2;
        const InitialState overlapping{{{0.0, 0.3}, {0.01, 0.3}}, {{1.0, 0.0}, {0.0, 1.0}}, "test"};
        bool logicError = false;
        try {
            verifyInitialState(two, overlapping);
        } catch (const std::logic_error&) {
            logicError = true;
        }
        suite.check(logicError, "verifyInitialState rechaza un par solapado con logic_error");
    }
}


// Estado de 10 particulas armado a mano: 9 tocan un obstaculo en el paso 0 y la id 9 no.
CaseRun runCrafted(bool stopAtT90, bool stopWhenAllUsed) {
    BilliardParams p;
    p.N = 10;
    p.x0 = 0.2;
    p.dt = 1e-4;
    p.tf = 0.01;
    p.every = 1;
    p.stopAtT90 = stopAtT90;
    p.stopWhenAllUsed = stopWhenAllUsed;
    std::vector<Vec2> pos(10);
    const std::vector<Vec2> vel(10);
    const double deg = std::numbers::pi / 180.0;
    const double ringRadius = 0.034;
    const double anglesRight[5] = {0.0, 72.0, 144.0, 216.0, 288.0};
    const double anglesLeft[4] = {0.0, 90.0, 180.0, 270.0};
    for (int a = 0; a < 5; ++a) {
        pos[static_cast<std::size_t>(2 * a)] = {0.2 + ringRadius * std::cos(anglesRight[a] * deg),
                                                ringRadius * std::sin(anglesRight[a] * deg)};
    }
    for (int a = 0; a < 4; ++a) {
        pos[static_cast<std::size_t>(2 * a + 1)] = {-0.2 + ringRadius * std::cos(anglesLeft[a] * deg),
                                                    ringRadius * std::sin(anglesLeft[a] * deg)};
    }
    pos[9] = {0.0, 0.4};
    return runCase(p, pos, vel);
}

BilliardOptions roundTripOptions(const std::filesystem::path& dir, bool trajectory) {
    BilliardOptions o;
    o.params.N = 5;
    o.params.tf = 0.01;
    o.params.dt = 1e-4;
    o.params.every = 10;
    o.params.seed = 3;
    o.framesPath = (dir / "frames.txt").string();
    o.conversionsPath = (dir / "conversions.txt").string();
    o.trajectory = trajectory;
    return o;
}

void testSweepAndCli(TestSuite& suite) {
    // Umbral entero de t90.
    suite.check(conversionTarget90(1) == 1 && conversionTarget90(10) == 9 &&
                    conversionTarget90(20) == 18 && conversionTarget90(100) == 90 &&
                    conversionTarget90(650) == 585,
                "conversionTarget90: 1 -> 1, 10 -> 9, 20 -> 18, 100 -> 90, 650 -> 585");

    // Conversiones simultaneas y reglas de corte.
    {
        const CaseRun t90 = runCrafted(true, false);
        bool idsAscending = t90.conversions.size() == 9;
        for (std::size_t i = 0; i < t90.conversions.size(); ++i) {
            idsAscending = idsAscending && t90.conversions[i].id == static_cast<int>(i) &&
                           t90.conversions[i].t == 0.0 && t90.conversions[i].step == 0;
        }
        suite.check(t90.result.finalStep == 0 && t90.result.stop == StopReason::T90 &&
                        t90.result.usedCount == 9,
                    "stop-at-t90: corta en el paso 0 con stop=t90 y 9 usadas");
        suite.check(idsAscending, "stop-at-t90: nueve conversiones en t = 0 con ids 0..8 ascendentes");

        const CaseRun all = runCrafted(false, true);
        suite.check(all.result.stop == StopReason::Tf && all.result.finalStep == 100 &&
                        all.result.usedCount == 9,
                    "stop-when-all-used con 9 de 10 usadas: no corta, stop=tf en el paso 100");
        const CaseRun none = runCrafted(false, false);
        suite.check(none.result.stop == StopReason::Tf && none.result.finalStep == 100,
                    "sin flags: stop=tf");
    }
    {
        BilliardParams p;
        p.N = 1;
        p.x0 = 0.2;
        p.dt = 1e-5;
        p.tf = 1.0;
        p.every = 1;
        p.stopWhenAllUsed = true;
        const CaseRun run = runCase(p, {{0.0, 0.0}}, {{1.0, 0.0}});
        suite.check(run.result.stop == StopReason::AllUsed && run.conversions.size() == 1 &&
                        run.result.finalStep == run.conversions[0].step &&
                        std::fabs(run.result.finalTime - 0.165) <= 2e-5,
                    "stop-when-all-used con N = 1: corta en el paso de la conversion (t = 0.165 s)");
    }

    // Matriz de aceptacion de la CLI.
    {
        const BilliardOptions defaults = parseOk({});
        const BilliardParams ref;
        suite.check(defaults.params.N == ref.N && defaults.params.R == ref.R &&
                        defaults.params.radius == ref.radius && defaults.params.mass == ref.mass &&
                        defaults.params.k == ref.k && defaults.params.v0 == ref.v0 &&
                        defaults.params.dt == ref.dt && defaults.params.tf == ref.tf &&
                        defaults.params.every == ref.every && defaults.params.seed == ref.seed &&
                        defaults.params.obstacles && defaults.params.x0 == 0.0175 &&
                        defaults.trajectory,
                    "CLI sin flags: defaults del enunciado con x0 = 0.0175");
        suite.check(parseOk({"--radius", "0.02"}).params.x0 == 0.02, "CLI: --radius 0.02 lleva x0 a 0.02");
        const BilliardOptions noObs = parseOk({"--no-obstacles", "--x0", "0.9"});
        suite.check(!noObs.params.obstacles && noObs.params.x0 == 0.9, "CLI: --no-obstacles --x0 0.9 se acepta");
        const BilliardOptions light = parseOk({"--no-trajectory", "--every", "1", "--dt", "1e-6", "--tf", "100"});
        suite.check(!light.trajectory && light.params.dt == 1e-6 && light.params.every == 1,
                    "CLI: --no-trajectory --every 1 --dt 1e-6 --tf 100 se acepta");
    }

    // Matriz de rechazo de la CLI.
    {
        const std::vector<std::vector<std::string>> bad = {
            {"--N", "0"}, {"--N", "-3"}, {"--N", "1.5"}, {"--N", "abc"},
            {"--dt", "0"}, {"--dt", "-1e-4"}, {"--dt", "nan"}, {"--dt", "3e-4"},
            {"--tf", "0"},
            {"--every", "0"}, {"--every", "-1"},
            {"--x0", "0.0174"}, {"--x0", "0.4926"},
            {"--seed", "-1"},
            {"--R", "0.03"}, {"--R", "1e6"}, {"--k", "0"}, {"--mass", "-1"}, {"--v0", "0"},
            {"--foo", "1"}, {"extra"}, {"--dt"},
            {"--no-obstacles", "--stop-when-all-used"}, {"--no-obstacles", "--stop-at-t90"},
            {"--frames", "a.txt", "--conversions", "a.txt"},
            {"--every", "1", "--dt", "1e-6", "--tf", "100"},
        };
        for (const std::vector<std::string>& args : bad) {
            std::string joined;
            for (const std::string& a : args) joined += (joined.empty() ? "" : " ") + a;
            suite.check(rejects(args), "CLI rechaza: " + joined);
        }
    }

    // Ida y vuelta de runBilliard: formato de texto, %.17g bit a bit, resumen y no-trajectory.
    {
        namespace fs = std::filesystem;
        const fs::path dir = fs::temp_directory_path() /
                             ("tp4_test_roundtrip_" + std::to_string(static_cast<long long>(std::rand())));
        fs::create_directories(dir);

        const BilliardOptions o = roundTripOptions(dir, true);
        std::FILE* summary = std::tmpfile();
        const SimulationResult result = runBilliard(o, summary);
        const std::string summaryText = slurp(summary);
        std::fclose(summary);

        const std::vector<std::string> frames = readLines(o.framesPath);
        suite.check(!frames.empty() && startsWith(frames[0], "# TP4_FRAMES 1 N=5 ") &&
                        frames[0].find("stop_when_all_used=0 stop_at_t90=0 init=rsa") !=
                            std::string::npos,
                    "frames: encabezado versionado con N, flags de corte e init");
        int frameLines = 0;
        int dataRows = 0;
        for (const std::string& line : frames) {
            if (startsWith(line, "FRAME ")) {
                ++frameLines;
            } else if (!line.empty() && line[0] != '#') {
                ++dataRows;
            }
        }
        suite.check(frameLines == 11 && dataRows == 55, "frames: 11 lineas FRAME y 55 filas de datos");
        suite.check(!frames.empty() && startsWith(frames.back(), "# END frames=11 "),
                    "frames: trailer '# END frames=11'");

        // Frame k = 10 releido con strtod contra una segunda corrida del mismo estado.
        std::vector<Frame> reference;
        {
            const InitialState state = generateInitialState(o.params);
            const FrameSink sink = [&](long long step, double t, const std::vector<Vec2>& q,
                                       const std::vector<Vec2>& v,
                                       const std::vector<unsigned char>& used) {
                reference.push_back({step, t, q, v, used});
            };
            simulate(o.params, state, sink, ConversionSink());
        }
        const Frame* frame10 = nullptr;
        for (const Frame& f : reference) {
            if (f.step == 10) frame10 = &f;
        }
        bool bitExact = frame10 != nullptr;
        for (std::size_t i = 0; i < frames.size() && bitExact; ++i) {
            if (!startsWith(frames[i], "FRAME 10 ")) continue;
            for (std::size_t row = 0; row < 5; ++row) {
                const char* cursor = frames[i + 1 + row].c_str();
                double values[4];
                for (double& value : values) {
                    char* end = nullptr;
                    value = std::strtod(cursor, &end);
                    cursor = end;
                }
                const long state = std::strtol(cursor, nullptr, 10);
                bitExact = bitExact && values[0] == frame10->pos[row].x &&
                           values[1] == frame10->pos[row].y && values[2] == frame10->vel[row].x &&
                           values[3] == frame10->vel[row].y &&
                           state == static_cast<long>(frame10->used[row]);
            }
            break;
        }
        suite.check(bitExact, "frames: el frame k = 10 releido con strtod coincide bit a bit");

        const std::vector<std::string> conversions = readLines(o.conversionsPath);
        suite.check(!conversions.empty() && startsWith(conversions.front(), "# TP4_CONVERSIONS 1 ") &&
                        startsWith(conversions.back(), "# END used=") &&
                        endsWith(conversions.back(), " stop=tf"),
                    "conversiones: encabezado versionado y trailer con stop=tf");
        suite.check(startsWith(summaryText, "TP4_SUMMARY 1 N=5 ") &&
                        summaryText.find(" stop=tf simulation_ms=") != std::string::npos,
                    "resumen: TP4_SUMMARY 1 con stop=tf y simulation_ms");
        suite.check(result.stop == StopReason::Tf && result.finalStep == 100,
                    "runBilliard: stop=tf en el paso 100");

        // Sin trayectoria no se escribe el archivo de frames (el log de conversiones si).
        const fs::path lightDir = dir / "light";
        fs::create_directories(lightDir);
        const BilliardOptions light = roundTripOptions(lightDir, false);
        std::FILE* lightSummary = std::tmpfile();
        runBilliard(light, lightSummary);
        std::fclose(lightSummary);
        suite.check(!fs::exists(light.framesPath) && fs::exists(light.conversionsPath),
                    "no-trajectory: no hay archivo de frames y si el de conversiones");

        // Estado no finito: el binario no deja trailer ni linea de resumen.
        BilliardOptions blow = roundTripOptions(dir / "blow", true);
        blow.params.N = 2;
        blow.params.v0 = 1e100;  // 1e200 desbordaria norm2 ya en verifyInitialState
        blow.params.dt = 1.0;
        blow.params.tf = 100.0;
        blow.params.every = 1;
        std::FILE* blowSummary = std::tmpfile();
        bool threw = false;
        try {
            runBilliard(blow, blowSummary);
        } catch (const std::runtime_error& e) {
            threw = containsText(e, "no finita");
        }
        const std::string blowText = slurp(blowSummary);
        std::fclose(blowSummary);
        const std::vector<std::string> blowFrames = readLines(blow.framesPath);
        suite.check(threw && blowText.empty() &&
                        (blowFrames.empty() || !startsWith(blowFrames.back(), "# END")),
                    "estado no finito: runBilliard lanza, sin linea de resumen ni trailer");

        fs::remove_all(dir);
    }
}

// Distancia minima de cada particula a algun sitio de la red <= jitter (con holgura numerica).
bool withinJitterOfSites(const BilliardParams& p, const std::vector<Vec2>& pos) {
    const std::vector<Vec2> sites = latticeSites(p);
    const double jitter = kLatticeGap / 2.0;
    for (const Vec2& q : pos) {
        double best = 1e300;
        for (const Vec2& s : sites) best = std::min(best, norm2(q - s));
        if (!(best <= jitter * jitter * (1.0 + 1e-9))) return false;
    }
    return true;
}

// true si generateInitialState lanza E con un mensaje que contiene text.
template <class E>
bool generateThrows(const BilliardParams& p, const char* text) {
    try {
        generateInitialState(p);
    } catch (const E& e) {
        return containsText(e, text);
    }
    return false;
}

void testLattice(TestSuite& suite) {
    const double defaultR = BilliardParams{}.R;
    const double defaultRadius = BilliardParams{}.radius;

    // Capacidad de la red con los parametros del enunciado.
    {
        const double x0s[] = {0.0175, 0.04125, 0.25, 0.4925};
        bool all = true;
        for (const double x0 : x0s) {
            BilliardParams p;
            p.x0 = x0;
            const int cap = latticeCapacity(p);
            std::printf("red: capacidad x0=%.5f = %d\n", x0, cap);
            all = all && cap >= 650;
        }
        BilliardParams none;
        none.obstacles = false;
        const int capNone = latticeCapacity(none);
        std::printf("red: capacidad sin obstaculos = %d\n", capNone);
        suite.check(all && capNone >= 650, "red: capacidad >= 650 en x0 = 0.0175, 0.04125, 0.25, 0.4925 y sin obstaculos");
    }

    // Sitios: dentro de la pared, lejos de los obstaculos y separados al menos a.
    {
        BilliardParams p;
        const std::vector<Vec2> sites = latticeSites(p);
        const double a = 2.0 * p.radius + kLatticeGap;
        const double jitter = kLatticeGap / 2.0;
        const double wallLimit = p.R - p.radius - jitter;
        const double obstacleLimit = 2.0 * p.radius + jitter;
        bool inside = true;
        bool apart = true;
        for (std::size_t i = 0; i < sites.size(); ++i) {
            inside = inside && norm2(sites[i]) <= wallLimit * wallLimit &&
                     norm2(sites[i] - Vec2{-p.x0, 0.0}) >= obstacleLimit * obstacleLimit &&
                     norm2(sites[i] - Vec2{p.x0, 0.0}) >= obstacleLimit * obstacleLimit;
            for (std::size_t j = i + 1; j < sites.size(); ++j) {
                const double d = std::sqrt(norm2(sites[i] - sites[j]));
                apart = apart && d >= a * (1.0 - 1e-12);
            }
        }
        suite.check(static_cast<int>(sites.size()) == latticeCapacity(p) && inside,
                    "red: sitios dentro de R - r - J y a >= 2r + J de ambos obstaculos");
        suite.check(apart, "red: todo par de sitios a distancia >= a = 2r + gap");
    }

    // N = 650 sin solapes, con jitter acotado, para tres semillas y tres configuraciones.
    {
        bool ok = true;
        bool labelled = true;
        bool jittered = true;
        for (int config = 0; config < 3; ++config) {
            for (std::uint64_t seed = 1; seed <= 3; ++seed) {
                BilliardParams p;
                p.N = 650;
                p.init = InitMethod::Lattice;
                p.seed = seed;
                if (config == 1) p.x0 = defaultR - defaultRadius;
                if (config == 2) p.obstacles = false;
                try {
                    const InitialState s = generateInitialState(p);
                    verifyInitialState(p, s);
                    labelled = labelled && s.method == "lattice";
                    jittered = jittered && withinJitterOfSites(p, s.pos);
                } catch (const std::exception&) {
                    ok = false;
                }
            }
        }
        suite.check(ok, "red: N = 650 sin solapes (x0 = r, x0 = R - r, sin obstaculos; semillas 1-3)");
        suite.check(labelled, "red: el metodo resuelto es 'lattice'");
        suite.check(jittered, "red: cada particula a menos de J = 5e-4 de un sitio");
    }

    // Bordes de capacidad.
    {
        BilliardParams p;
        p.init = InitMethod::Lattice;
        p.N = latticeCapacity(p);
        bool atCapacity = true;
        try {
            const InitialState s = generateInitialState(p);
            verifyInitialState(p, s);
        } catch (const std::exception&) {
            atCapacity = false;
        }
        suite.check(atCapacity, "red: N = capacidad se genera sin solapes");
        p.N = latticeCapacity(p) + 1;
        const InitMethod modes[] = {InitMethod::Rsa, InitMethod::Lattice, InitMethod::Auto};
        bool rejected = true;
        for (const InitMethod mode : modes) {
            BilliardParams q = p;
            q.init = mode;
            rejected = rejected && generateThrows<std::invalid_argument>(q, "capacidad");
        }
        suite.check(rejected, "capacidad + 1 lanza invalid_argument con 'capacidad' en rsa, lattice y auto");
    }

    // Modo auto y fallback.
    {
        BilliardParams low;
        low.N = 100;
        BilliardParams high;
        high.N = kAutoRsaMaxN + 1;
        suite.check(generateInitialState(low).method == "rsa" &&
                        generateInitialState(high).method == "lattice",
                    "auto: N = 100 resuelve a rsa y N = 401 a lattice");

        BilliardParams dense;
        dense.radius = 0.03;
        dense.x0 = 0.03;
        dense.N = 180;
        const InitialState viaAuto = generateInitialState(dense);
        BilliardParams explicitLattice = dense;
        explicitLattice.init = InitMethod::Lattice;
        suite.check(viaAuto.method == "lattice" &&
                        sameState(viaAuto, generateInitialState(explicitLattice)),
                    "auto: si RSA se agota cae a la red, identico a --init lattice con la misma semilla");
        BilliardParams explicitRsa = dense;
        explicitRsa.init = InitMethod::Rsa;
        suite.check(generateThrows<std::runtime_error>(explicitRsa, "--init lattice"),
                    "rsa explicito nunca cae a la red: lanza runtime_error que sugiere --init lattice");
    }

    // Determinismo de la red.
    {
        BilliardParams p;
        p.N = 300;
        p.init = InitMethod::Lattice;
        p.seed = 5;
        const InitialState a = generateInitialState(p);
        suite.check(sameState(a, generateInitialState(p)), "red: misma semilla, estado identico bit a bit");
        BilliardParams q = p;
        q.dt = 1e-5;
        q.every = 7;
        suite.check(sameState(a, generateInitialState(q)), "red: cambiar solo dt y every no cambia el estado");
        BilliardParams other = p;
        other.seed = 6;
        suite.check(!sameState(a, generateInitialState(other)), "red: otra semilla, otro estado");
    }

    // parseInitMethod y la CLI.
    {
        bool names = parseInitMethod("rsa") == InitMethod::Rsa &&
                     parseInitMethod("lattice") == InitMethod::Lattice &&
                     parseInitMethod("auto") == InitMethod::Auto &&
                     std::string(initMethodName(InitMethod::Lattice)) == "lattice";
        bool rejectedHex = false;
        bool rejectedEmpty = false;
        try {
            parseInitMethod("hex");
        } catch (const std::invalid_argument&) {
            rejectedHex = true;
        }
        try {
            parseInitMethod("");
        } catch (const std::invalid_argument&) {
            rejectedEmpty = true;
        }
        suite.check(names && rejectedHex && rejectedEmpty,
                    "parseInitMethod: acepta rsa, lattice y auto; rechaza 'hex' y ''");
        suite.check(parseOk({"--init", "lattice"}).params.init == InitMethod::Lattice &&
                        parseOk({}).params.init == InitMethod::Auto &&
                        rejects({"--init"}) && rejects({"--init", "hex"}),
                    "CLI: --init lattice, default auto, '--init' sin valor y '--init hex' rechazados");
    }

    // Corrida densa: N = 650 sobre la red, finita y dentro del circulo.
    {
        BilliardParams p;
        p.N = 650;
        p.init = InitMethod::Lattice;
        p.tf = 0.05;
        p.every = 50;
        const InitialState s = generateInitialState(p);
        const CaseRun run = runCase(p, s.pos, s.vel);
        bool speeds = !run.frames.empty();
        if (speeds) {
            for (const Vec2& v : run.frames.front().vel) {
                speeds = speeds && std::fabs(std::sqrt(norm2(v)) - p.v0) < 1e-9;
            }
        }
        suite.check(run.frames.size() == 11 && allFiniteInside(run, p.R) && speeds,
                    "corrida densa N = 650: 11 frames finitos dentro del circulo, rapidez inicial v0");
    }
}

}  // namespace

int main() {
    TestSuite suite;
    testForceKernel(suite);
    testDynamics(suite);
    testSweepAndCli(suite);
    testLattice(suite);
    return suite.finish();
}
