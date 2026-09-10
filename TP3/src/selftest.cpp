#include <cmath>
#include <filesystem>
#include <fstream>
#include <limits>
#include <queue>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>

#include "collision.h"
#include "brute_force_oracle.h"
#include "config_io.h"
#include "event.h"
#include "generator.h"
#include "geometry.h"
#include "io.h"
#include "options.h"
#include "particle.h"
#include "simulation_types.h"
#include "simulation.h"
#include "test_support.h"

namespace {

ProgramOptions parse(std::vector<std::string> arguments) {
    std::vector<char*> argv;
    argv.reserve(arguments.size());
    for (std::string& argument : arguments) argv.push_back(argument.data());
    return parseOptions(static_cast<int>(argv.size()), argv.data());
}

void testOfficialDefaults(TestSuite& suite) {
    const ProgramOptions options = parse({"tp3"});
    const SimulationConfig& c = options.simulation;
    suite.check(c.particleCount == 100, "N oficial debe ser 100");
    suite.check(std::abs(c.length - 1.20) < 1e-15, "L oficial debe ser 1.20 m");
    suite.check(std::abs(c.width - 0.68) < 1e-15, "W oficial debe ser 0.68 m");
    suite.check(std::abs(c.goalSize - 0.20) < 1e-15, "el arco oficial debe medir 0.20 m");
    suite.check(std::abs(c.particleRadius - 0.0175) < 1e-15,
                "el radio oficial debe ser 0.0175 m");
    suite.check(std::abs(c.particleMass - 0.025) < 1e-15, "la masa oficial debe ser 0.025 kg");
    suite.check(std::abs(c.initialSpeed - 1.0) < 1e-15, "v0 oficial debe ser 1 m/s");
    suite.check(std::abs(c.maxTime - 100.0) < 1e-15, "tmax de competencia debe ser 100 s");
    suite.check(c.seed == 42, "la semilla default debe ser explicita");
    suite.check(options.trajectoryEnabled, "la ejecucion interactiva debe guardar trayectoria");
    suite.check(options.outputEveryEvents == 10, "la trayectoria debe muestrear cada 10 eventos");
}

void testArgumentParsing(TestSuite& suite) {
    const ProgramOptions options = parse({
        "tp3", "--N", "25", "--L", "2.5", "--W", "1.5", "--goal-size", "0.3",
        "--radius", "0.01", "--mass", "0.5", "--v0", "2", "--tmax", "30",
        "--seed", "987", "--config", "obstacles.txt", "--max-placement-attempts", "1234",
        "--static-output", "s.txt", "--trajectory", "d.txt", "--output-every-events", "1",
        "--goals-output", "goals.txt", "--events-output", "events.txt",
        "--summary", "summary.csv", "--no-trajectory", "--csv",
    });
    suite.check(options.simulation.particleCount == 25, "--N debe reemplazar el default");
    suite.check(std::abs(options.simulation.length - 2.5) < 1e-15, "--L debe parsearse");
    suite.check(std::abs(options.simulation.width - 1.5) < 1e-15, "--W debe parsearse");
    suite.check(options.simulation.seed == 987, "--seed debe aceptar uint64");
    suite.check(options.obstacleConfigPath == "obstacles.txt", "--config debe conservar la ruta");
    suite.check(options.simulation.maxPlacementAttemptsPerParticle == 1234,
                "debe configurarse el maximo de intentos");
    suite.check(!options.trajectoryEnabled, "--no-trajectory debe desactivar la trayectoria");
    suite.check(options.csv, "--csv debe activar salida machine-readable");
    suite.check(options.summaryPath == "summary.csv", "--summary debe conservar la ruta");
    suite.check(options.goalsOutputPath == "goals.txt",
                "--goals-output debe conservar la ruta");
    suite.check(options.eventsOutputPath == "events.txt",
                "--events-output debe conservar la ruta");
}

void testInvalidArguments(TestSuite& suite) {
    auto rejects = [](std::vector<std::string> args) {
        try {
            (void)parse(std::move(args));
            return false;
        } catch (const std::invalid_argument&) {
            return true;
        }
    };
    suite.check(rejects({"tp3", "--N", "0"}), "N=0 debe rechazarse");
    suite.check(rejects({"tp3", "--goal-size", "1"}), "un arco mayor que W debe rechazarse");
    suite.check(rejects({"tp3", "--radius", "abc"}), "un real invalido debe rechazarse");
    suite.check(rejects({"tp3", "--v0", "nan"}), "NaN debe rechazarse");
    suite.check(rejects({"tp3", "--tmax", "inf"}), "infinito debe rechazarse");
    suite.check(rejects({"tp3", "--seed", "-1"}), "una semilla negativa debe rechazarse");
    suite.check(rejects({"tp3", "--N", "999999999999999999"}),
                "un entero fuera de rango debe rechazarse");
    suite.check(rejects({"tp3", "--output-every-events", "0"}),
                "una frecuencia de salida nula debe rechazarse");
    suite.check(rejects({"tp3", "--goals-output", "same.txt", "--summary", "same.txt"}),
                "el registro de goles no debe sobrescribir el resumen");
    suite.check(rejects({"tp3", "--goals-output", "same.txt", "--events-output", "same.txt"}),
                "los dos logs livianos deben usar rutas distintas");
    suite.check(rejects({"tp3", "archivo-suelto"}), "argumentos posicionales deben rechazarse");
}

void testModelContracts(TestSuite& suite) {
    Particle particle{7, {0.2, 0.3}, {1.0, 0.0}, 0.0175, 0.025};
    suite.check(particle.state == ParticleState::Fresh, "una particula nueva debe estar fresca");
    suite.check(particle.collisionCount == 0, "una particula nueva no debe tener colisiones");

    std::priority_queue<Event, std::vector<Event>, EventLater> events;
    events.push(Event{2.0, EventType::VerticalWall, 0, -1, -1, 0, 0, 8});
    events.push(Event{1.0, EventType::HorizontalWall, 1, -1, -1, 0, 0, 9});
    events.push(Event{1.0, EventType::ParticleObstacle, 2, -1, 0, 0, 0, 3});
    suite.check(events.top().time == 1.0 && events.top().sequence == 3,
                "la cola debe ordenar por tiempo y luego por secuencia");

    SimulationResult result;
    suite.check(!result.t90.has_value(), "t90 debe poder representar una corrida censurada");
}

void testObstacleValidation(TestSuite& suite) {
    SimulationConfig config;
    config.particleCount = 1;

    validateObstacleConfiguration({{{0.10, 0.10}, 0.05}, {{0.20, 0.10}, 0.05}}, config);
    suite.check(true, "dos obstaculos tangentes deben ser validos");

    auto rejects = [&](const std::vector<Obstacle>& obstacles) {
        try {
            validateObstacleConfiguration(obstacles, config);
            return false;
        } catch (const std::invalid_argument&) {
            return true;
        }
    };
    suite.check(rejects({{{0.10, 0.10}, 0.06}, {{0.20, 0.10}, 0.05}}),
                "obstaculos superpuestos deben rechazarse");
    suite.check(rejects({{{0.01, 0.10}, 0.05}}),
                "un obstaculo que atraviesa la pared debe rechazarse");
    suite.check(rejects({{{0.10, 0.10}, 0.01}}),
                "un obstaculo menor que la particula debe rechazarse");
}

void testObstacleFile(TestSuite& suite) {
    const std::filesystem::path path = std::filesystem::path("build") / "obstacles-selftest.txt";
    {
        std::ofstream output(path);
        output << "# configuracion sintetica\n"
               << "0.20 0.20 0.05\n"
               << "\n"
               << "0.40 0.30 0.06\n";
    }

    SimulationConfig config;
    const std::vector<Obstacle> obstacles = readObstacleConfig(path.string(), config);
    suite.check(obstacles.size() == 2, "el lector debe ignorar comentarios y lineas vacias");
    suite.check(std::abs(obstacles[1].center.y - 0.30) < 1e-15,
                "el lector debe preservar las coordenadas");

    {
        std::ofstream output(path);
        output << "0.2 0.2 0.05 dato_extra\n";
    }
    bool malformedRejected = false;
    try {
        (void)readObstacleConfig(path.string(), config);
    } catch (const std::runtime_error&) {
        malformedRejected = true;
    }
    suite.check(malformedRejected, "una fila con mas de tres columnas debe rechazarse");
    std::filesystem::remove(path);
}

void testGenerator(TestSuite& suite) {
    SimulationConfig config;
    config.seed = 123456;
    config.obstacles = {{{0.60, 0.34}, 0.08}};

    const std::vector<Particle> first = generateParticles(config);
    const std::vector<Particle> second = generateParticles(config);
    suite.check(first.size() == 100, "el generador debe crear exactamente N particulas");

    bool reproducible = first.size() == second.size();
    bool valid = true;
    for (std::size_t i = 0; i < first.size(); ++i) {
        const Particle& particle = first[i];
        const Particle& copy = second[i];
        reproducible = reproducible && particle.position.x == copy.position.x &&
                       particle.position.y == copy.position.y &&
                       particle.velocity.x == copy.velocity.x &&
                       particle.velocity.y == copy.velocity.y;
        valid = valid && particle.id == static_cast<int>(i) &&
                particle.state == ParticleState::Fresh && particle.collisionCount == 0 &&
                particle.position.x >= particle.radius &&
                particle.position.x <= config.length - particle.radius &&
                particle.position.y >= particle.radius &&
                particle.position.y <= config.width - particle.radius &&
                std::abs(normSquared(particle.velocity) -
                         config.initialSpeed * config.initialSpeed) < 1e-12 &&
                !circlesOverlap(particle.position, particle.radius, config.obstacles[0].center,
                                config.obstacles[0].radius);
        for (std::size_t j = 0; j < i; ++j) {
            valid = valid && !circlesOverlap(particle.position, particle.radius, first[j].position,
                                             first[j].radius);
        }
    }
    suite.check(reproducible, "la misma semilla debe reproducir exactamente la condicion inicial");
    suite.check(valid, "las particulas deben quedar dentro, separadas y con rapidez v0");
}

void testGeneratorSaturation(TestSuite& suite) {
    SimulationConfig config;
    config.particleCount = 1;
    config.length = 1.0;
    config.width = 1.0;
    config.particleRadius = 0.20;
    config.maxPlacementAttemptsPerParticle = 20;
    config.obstacles = {{{0.50, 0.50}, 0.30}};

    bool rejected = false;
    try {
        (void)generateParticles(config);
    } catch (const std::runtime_error&) {
        rejected = true;
    }
    suite.check(rejected, "una geometria sin area disponible debe fallar con limite de intentos");
}

double kineticEnergy(const Particle& particle) {
    return 0.5 * particle.mass * normSquared(particle.velocity);
}

Vector2 momentum(const Particle& particle) {
    return particle.velocity * particle.mass;
}

bool near(double actual, double expected, double tolerance = 1e-12) {
    return std::abs(actual - expected) <= tolerance;
}

void testWallPredictionAndResolution(TestSuite& suite) {
    SimulationConfig config;
    config.length = 1.0;
    config.width = 1.0;

    Particle right{0, {0.20, 0.50}, {1.0, 0.0}, 0.05, 1.0};
    suite.check(near(timeToVerticalWall(right, config), 0.75),
                "tiempo a pared derecha debe considerar el radio");
    suite.check(std::isinf(timeToHorizontalWall(right, config)),
                "velocidad horizontal no debe predecir pared horizontal");
    advanceParticle(right, timeToVerticalWall(right, config));
    resolveVerticalWall(right);
    suite.check(near(right.position.x, 0.95) && near(right.velocity.x, -1.0),
                "pared vertical debe invertir vx en el contacto");

    Particle left{1, {0.20, 0.50}, {-1.0, 0.0}, 0.05, 1.0};
    suite.check(near(timeToVerticalWall(left, config), 0.15),
                "tiempo a pared izquierda debe ser positivo");

    Particle corner{2, {0.50, 0.50}, {1.0, 1.0}, 0.10, 1.0};
    const WallCollision prediction = nextWallCollision(corner, config);
    suite.check(prediction.type == EventType::Corner && near(prediction.time, 0.40),
                "tiempos de pared iguales deben producir evento esquina");
    advanceParticle(corner, prediction.time);
    resolveCorner(corner);
    suite.check(near(corner.velocity.x, -1.0) && near(corner.velocity.y, -1.0),
                "la esquina debe invertir ambas componentes");
}

void testHeadOnParticleCollision(TestSuite& suite) {
    Particle first{0, {0.30, 0.50}, {1.0, 0.0}, 0.05, 1.0};
    Particle second{1, {0.70, 0.50}, {-1.0, 0.0}, 0.05, 1.0};
    const double time = timeToParticle(first, second);
    suite.check(near(time, 0.15), "dos particulas frontales deben colisionar en t=0.15");
    advanceParticle(first, time);
    advanceParticle(second, time);
    resolveParticleCollision(first, second);
    suite.check(near(first.velocity.x, -1.0) && near(second.velocity.x, 1.0),
                "masas iguales deben intercambiar velocidades en choque frontal");
    suite.check(std::isinf(timeToParticle(first, second)),
                "particulas que se separan no deben generar otro choque inmediato");
}

void testObliqueParticleCollision(TestSuite& suite) {
    Particle first{0, {0.20, 0.20}, {1.0, 0.20}, 0.05, 2.0};
    Particle second{1, {0.60, 0.26}, {-0.25, -0.10}, 0.05, 1.0};
    const double time = timeToParticle(first, second);
    suite.check(std::isfinite(time), "el caso oblicuo elegido debe producir una colision");
    advanceParticle(first, time);
    advanceParticle(second, time);

    const double energyBefore = kineticEnergy(first) + kineticEnergy(second);
    const Vector2 momentumBefore = momentum(first) + momentum(second);
    resolveParticleCollision(first, second);
    const double energyAfter = kineticEnergy(first) + kineticEnergy(second);
    const Vector2 momentumAfter = momentum(first) + momentum(second);

    suite.check(near(energyAfter, energyBefore, 1e-11),
                "choque oblicuo debe conservar energia cinetica");
    suite.check(near(momentumAfter.x, momentumBefore.x, 1e-11) &&
                    near(momentumAfter.y, momentumBefore.y, 1e-11),
                "choque oblicuo debe conservar momento lineal");
}

void testObstacleCollision(TestSuite& suite) {
    const Obstacle obstacle{{0.50, 0.50}, 0.10};
    Particle particle{0, {0.20, 0.50}, {1.0, 0.0}, 0.05, 1.0};
    const double time = timeToObstacle(particle, obstacle);
    suite.check(near(time, 0.15), "tiempo a obstaculo debe usar R+r");
    advanceParticle(particle, time);
    const double energyBefore = kineticEnergy(particle);
    resolveObstacleCollision(particle, obstacle);
    suite.check(near(particle.velocity.x, -1.0) && near(particle.velocity.y, 0.0),
                "obstaculo frontal debe reflejar la velocidad");
    suite.check(near(kineticEnergy(particle), energyBefore),
                "obstaculo fijo elastico debe conservar energia");
}

void testGoalGeometry(TestSuite& suite) {
    SimulationConfig config;
    Particle particle;
    particle.position.y = config.width / 2.0;
    suite.check(isGoalContact(particle, config), "el centro del arco debe contar como gol");
    particle.position.y = config.width / 2.0 + config.goalSize / 2.0;
    suite.check(isGoalContact(particle, config), "el borde del arco debe incluirse");
    particle.position.y += 1e-6;
    suite.check(!isGoalContact(particle, config), "un contacto fuera del arco no debe contar");
}

void testSingleParticleEventLoop(TestSuite& suite) {
    SimulationConfig config;
    config.particleCount = 1;
    config.length = 1.0;
    config.width = 1.0;
    config.goalSize = 0.20;
    config.maxTime = 3.0;

    Particle particle{0, {0.50, 0.50}, {1.0, 0.0}, 0.05, 1.0};
    Simulation simulation(config, {particle});
    std::vector<double> observedTimes;
    const SimulationResult result = simulation.run(
        [&](double time, const Event&, const std::vector<Particle>&, int) {
            observedTimes.push_back(time);
        });

    suite.check(result.t90.has_value() && near(*result.t90, 0.45),
                "una particula debe fijar t90 en su primer contacto con el arco");
    suite.check(result.goals == 1 && near(result.usedFraction, 1.0),
                "una particula usada debe sumar exactamente un gol");
    suite.check(result.processedEvents == 3,
                "en tres segundos deben ocurrir tres rebotes verticales");
    suite.check(simulation.particles()[0].collisionCount == 3,
                "cada rebote valido debe incrementar el contador una vez");
    suite.check(simulation.particles()[0].state == ParticleState::Used,
                "el estado usado debe persistir despues de nuevos contactos");
    suite.check(near(simulation.particles()[0].position.x, 0.20),
                "el motor debe avanzar desde el ultimo evento hasta tmax");
    const bool expectedTimes =
        observedTimes.size() == 3 && near(observedTimes[0], 0.45) &&
        near(observedTimes[1], 1.35) && near(observedTimes[2], 2.25);
    suite.check(expectedTimes, "el observador debe recibir eventos en orden cronologico");

    bool secondRunRejected = false;
    try {
        (void)simulation.run();
    } catch (const std::logic_error&) {
        secondRunRejected = true;
    }
    suite.check(secondRunRejected, "una simulacion terminada no debe poder ejecutarse de nuevo");
}

void testWallOutsideGoalDoesNotScore(TestSuite& suite) {
    SimulationConfig config;
    config.particleCount = 1;
    config.length = 1.0;
    config.width = 1.0;
    config.goalSize = 0.20;
    config.maxTime = 0.50;

    Particle particle{0, {0.50, 0.20}, {1.0, 0.0}, 0.05, 1.0};
    Simulation simulation(config, {particle});
    const SimulationResult result = simulation.run();
    suite.check(!result.t90.has_value() && result.goals == 0,
                "un rebote en pared corta fuera del arco no debe sumar");
}

void testLazyInvalidation(TestSuite& suite) {
    SimulationConfig config;
    config.particleCount = 2;
    config.length = 1.0;
    config.width = 1.0;
    config.goalSize = 0.20;
    config.maxTime = 1.0;

    std::vector<Particle> particles = {
        {0, {0.30, 0.20}, {1.0, 0.0}, 0.05, 1.0},
        {1, {0.70, 0.20}, {-1.0, 0.0}, 0.05, 1.0},
    };
    const double energyBefore = kineticEnergy(particles[0]) + kineticEnergy(particles[1]);
    Simulation simulation(config, particles);
    const SimulationResult result = simulation.run();
    const double energyAfter =
        kineticEnergy(simulation.particles()[0]) + kineticEnergy(simulation.particles()[1]);

    suite.check(result.discardedEvents >= 2,
                "el choque entre particulas debe invalidar predicciones anteriores de pared");
    suite.check(result.scheduledEvents > result.processedEvents,
                "la cola perezosa debe poder contener eventos futuros u obsoletos");
    suite.check(near(energyAfter, energyBefore, 1e-11),
                "el loop completo debe conservar energia en un sistema cerrado");
}

void testLongEventDrivenRun(TestSuite& suite) {
    SimulationConfig config;
    config.particleCount = 20;
    config.maxTime = 10.0;
    config.seed = 20260910;
    config.obstacles = {{{0.60, 0.34}, 0.08}};

    const std::vector<Particle> initial = generateParticles(config);
    double energyBefore = 0.0;
    for (const Particle& particle : initial) energyBefore += kineticEnergy(particle);

    Simulation simulation(config, initial);
    double previousTime = -1.0;
    bool monotonic = true;
    const SimulationResult result = simulation.run(
        [&](double time, const Event&, const std::vector<Particle>&, int) {
            monotonic = monotonic && time + kTimeEpsilon >= previousTime;
            previousTime = time;
        });

    double energyAfter = 0.0;
    bool finiteAndInside = true;
    for (const Particle& particle : simulation.particles()) {
        energyAfter += kineticEnergy(particle);
        finiteAndInside =
            finiteAndInside && std::isfinite(particle.position.x) &&
            std::isfinite(particle.position.y) && std::isfinite(particle.velocity.x) &&
            std::isfinite(particle.velocity.y) &&
            particle.position.x >= particle.radius - 1e-9 &&
            particle.position.x <= config.length - particle.radius + 1e-9 &&
            particle.position.y >= particle.radius - 1e-9 &&
            particle.position.y <= config.width - particle.radius + 1e-9;
    }

    suite.check(monotonic, "los eventos de una corrida larga deben ser monotonos");
    suite.check(result.processedEvents > 0 && near(result.finalTime, config.maxTime),
                "la corrida larga debe procesar eventos y finalizar exactamente en tmax");
    suite.check(finiteAndInside, "la corrida larga debe mantener estados finitos dentro de la mesa");
    suite.check(near(energyAfter, energyBefore, 1e-9),
                "la energia total debe conservarse durante una corrida larga");
}

std::string readWholeFile(const std::filesystem::path& path) {
    std::ifstream input(path);
    return {std::istreambuf_iterator<char>(input), std::istreambuf_iterator<char>()};
}

void testOutputFormats(TestSuite& suite) {
    const std::filesystem::path directory =
        std::filesystem::path("build") / "io-selftest" / "nested";
    const std::filesystem::path staticPath = directory / "static.txt";
    const std::filesystem::path trajectoryPath = directory / "trajectory.txt";
    const std::filesystem::path goalsPath = directory / "goals.txt";
    const std::filesystem::path eventsPath = directory / "events.txt";
    const std::filesystem::path summaryPath = directory / "summary.csv";

    SimulationConfig config;
    config.particleCount = 2;
    config.obstacles = {{{0.60, 0.34}, 0.08}};
    std::vector<Particle> particles = {
        {0, {0.20, 0.20}, {1.0, 0.0}, config.particleRadius, config.particleMass},
        {1, {0.80, 0.40}, {-1.0, 0.0}, config.particleRadius, config.particleMass,
         ParticleState::Used, 3},
    };

    writeStaticSystem(staticPath.string(), config, particles);
    {
        TrajectoryWriter writer(trajectoryPath.string(), config.particleCount);
        writer.writeFrame(0.0, 0, 1, particles);
        particles[0].position.x = 0.25;
        writer.writeFrame(0.05, 1, 1, particles);
    }
    {
        GoalLogWriter writer(goalsPath.string(), config.particleCount);
        writer.writeSample(0.0, 0);
        writer.writeSample(0.25, 1);
        writer.writeSample(100.0, 1);
    }
    {
        EventLogWriter writer(eventsPath.string(), particles);
        const Event wall{0.25, EventType::VerticalWall, 0, -1, -1, 0, 0, 1};
        writer.writeEvent(1, 0.25, wall, 1, particles);
        const Event pair{0.50, EventType::ParticleParticle, 0, 1, -1, 0, 3, 2};
        writer.writeEvent(2, 0.50, pair, 1, particles);
        writer.writeEnd(1.0, 2, 1);
    }

    SimulationResult censored;
    censored.finalTime = 100.0;
    censored.goals = 1;
    censored.usedFraction = 0.5;
    censored.processedEvents = 20;
    censored.scheduledEvents = 50;
    censored.discardedEvents = 10;
    censored.simulationMilliseconds = 1.25;
    writeSummaryFile(summaryPath.string(), config, censored);

    const std::string staticText = readWholeFile(staticPath);
    suite.check(staticText.find("TP3_STATIC 1") != std::string::npos &&
                    staticText.find("N 2") != std::string::npos &&
                    staticText.find("K 1") != std::string::npos,
                "el archivo estatico debe declarar version, N y K");
    suite.check(staticText.find("OBSTACLES id x y radius") != std::string::npos,
                "el archivo estatico debe incluir la geometria de obstaculos");

    const std::string trajectoryText = readWholeFile(trajectoryPath);
    const std::size_t firstFrame = trajectoryText.find("FRAME ");
    const std::size_t secondFrame = trajectoryText.find("FRAME ", firstFrame + 1);
    suite.check(trajectoryText.find("TP3_TRAJECTORY 1") != std::string::npos &&
                    secondFrame != std::string::npos,
                "la trayectoria debe ser versionada y admitir multiples frames");
    suite.check(trajectoryText.find("fresh") != std::string::npos &&
                    trajectoryText.find("used") != std::string::npos,
                "la trayectoria debe conservar el color logico de cada particula");

    const std::string goalsText = readWholeFile(goalsPath);
    suite.check(goalsText.find("TP3_GOALS 1\nN 2\nTIME goals used_fraction\n") == 0,
                "el registro de goles debe declarar version, N y columnas");
    suite.check(goalsText.find("0.25 1 0.5") != std::string::npos &&
                    goalsText.find("100 1 0.5") != std::string::npos,
                "el registro liviano debe conservar cambios de Fu y estado final");
    bool invalidGoalSampleRejected = false;
    try {
        GoalLogWriter writer((directory / "invalid-goals.txt").string(), 2);
        writer.writeSample(std::numeric_limits<double>::quiet_NaN(), 0);
    } catch (const std::invalid_argument&) {
        invalidGoalSampleRejected = true;
    }
    suite.check(invalidGoalSampleRejected,
                "el registro de goles debe rechazar tiempos no finitos");

    const std::string eventsText = readWholeFile(eventsPath);
    suite.check(eventsText.find("TP3_EVENTS 1\nN 2\nINITIAL id x y vx vy\n") == 0 &&
                    eventsText.find("END_INITIAL\n") != std::string::npos,
                "el log compacto debe incluir la condicion inicial completa");
    suite.check(eventsText.find("EVENT 1 0.25 vertical_wall 0 -1 -1 1") !=
                        std::string::npos &&
                    eventsText.find("EVENT 2 0.5 particle_particle 0 1 -1 1") !=
                        std::string::npos &&
                    eventsText.find("END 1 2 1") != std::string::npos,
                "el log compacto debe conservar eventos, participantes y cierre");

    const std::string summaryText = readWholeFile(summaryPath);
    suite.check(summaryText.find("seed,N,K,tmax") == 0,
                "el archivo resumen debe incluir un encabezado estable");
    suite.check(summaryText.find(",NA,1,0.5,") != std::string::npos,
                "una corrida censurada debe escribir t90 como NA");

    std::ostringstream human;
    printHumanSummary(human, config, censored);
    suite.check(human.str().find("t90=NA") != std::string::npos,
                "el resumen humano debe distinguir una corrida censurada");

    std::ostringstream csv;
    censored.t90 = 12.5;
    writeSummaryCsv(csv, config, censored, false);
    suite.check(csv.str().find(",12.5,") != std::string::npos,
                "el resumen CSV debe escribir un t90 alcanzado");

    bool wrongFrameRejected = false;
    try {
        TrajectoryWriter writer((directory / "wrong.txt").string(), 1);
        writer.writeFrame(0.0, 0, 0, particles);
    } catch (const std::invalid_argument&) {
        wrongFrameRejected = true;
    }
    suite.check(wrongFrameRejected, "un frame con N incorrecto debe rechazarse");
    std::filesystem::remove_all(directory.parent_path());
}

RecordedEvent normalizeEvent(RecordedEvent event) {
    if (event.type == EventType::ParticleParticle && event.particleA > event.particleB) {
        std::swap(event.particleA, event.particleB);
    }
    return event;
}

void testPriorityQueueMatchesBruteForceOracle(TestSuite& suite) {
    for (const std::uint64_t seed : {11ULL, 22ULL, 33ULL, 44ULL, 55ULL}) {
        SimulationConfig config;
        config.particleCount = 6;
        config.maxTime = 4.0;
        config.seed = seed;
        config.obstacles = {{{0.60, 0.34}, 0.07}};
        const std::vector<Particle> initial = generateParticles(config);

        const OracleRun oracle = runBruteForceOracle(config, initial);
        Simulation optimized(config, initial);
        std::vector<RecordedEvent> optimizedEvents;
        const SimulationResult result = optimized.run(
            [&](double time, const Event& event, const std::vector<Particle>&, int) {
                optimizedEvents.push_back(
                    {time, event.type, event.particleA, event.particleB, event.obstacle});
            });

        const std::string context = "oraculo seed=" + std::to_string(seed);
        suite.check(optimizedEvents.size() == oracle.events.size(),
                    context + ": ambos motores deben procesar igual cantidad de eventos");
        bool sameEvents = optimizedEvents.size() == oracle.events.size();
        for (std::size_t i = 0; sameEvents && i < optimizedEvents.size(); ++i) {
            const RecordedEvent actual = normalizeEvent(optimizedEvents[i]);
            const RecordedEvent expected = normalizeEvent(oracle.events[i]);
            // El oraculo vuelve a materializar todas las posiciones en cada
            // evento; la cola conserva tiempos absolutos calculados antes de
            // colisiones no relacionadas. Son algebraicamente equivalentes,
            // pero acumulan redondeo en distinto orden.
            sameEvents = near(actual.time, expected.time, 1e-7) &&
                         actual.type == expected.type &&
                         actual.particleA == expected.particleA &&
                         actual.particleB == expected.particleB &&
                         actual.obstacle == expected.obstacle;
            if (!sameEvents) {
                std::printf(
                    "  [DIAG] seed=%llu evento=%zu cola=(%.15g,%d,%d,%d,%d) "
                    "oraculo=(%.15g,%d,%d,%d,%d)\n",
                    static_cast<unsigned long long>(seed), i, actual.time,
                    static_cast<int>(actual.type), actual.particleA, actual.particleB,
                    actual.obstacle, expected.time, static_cast<int>(expected.type),
                    expected.particleA, expected.particleB, expected.obstacle);
            }
        }
        suite.check(sameEvents, context + ": la secuencia fisica debe coincidir evento por evento");

        bool sameParticles = optimized.particles().size() == oracle.particles.size();
        double maximumStateDifference = 0.0;
        for (std::size_t i = 0; sameParticles && i < oracle.particles.size(); ++i) {
            const Particle& actual = optimized.particles()[i];
            const Particle& expected = oracle.particles[i];
            maximumStateDifference =
                std::max({maximumStateDifference,
                          std::abs(actual.position.x - expected.position.x),
                          std::abs(actual.position.y - expected.position.y),
                          std::abs(actual.velocity.x - expected.velocity.x),
                          std::abs(actual.velocity.y - expected.velocity.y)});
            sameParticles =
                near(actual.position.x, expected.position.x, 1e-6) &&
                near(actual.position.y, expected.position.y, 1e-6) &&
                near(actual.velocity.x, expected.velocity.x, 1e-6) &&
                near(actual.velocity.y, expected.velocity.y, 1e-6) &&
                actual.state == expected.state &&
                actual.collisionCount == expected.collisionCount;
        }
        if (!sameParticles) {
            std::printf("  [DIAG] seed=%llu diferencia_estado_max=%.15g\n",
                        static_cast<unsigned long long>(seed), maximumStateDifference);
        }
        suite.check(sameParticles, context + ": el estado final debe coincidir con fuerza bruta");
        suite.check(result.goals == oracle.result.goals &&
                        result.t90.has_value() == oracle.result.t90.has_value() &&
                        (!result.t90.has_value() ||
                         near(*result.t90, *oracle.result.t90, 1e-7)),
                    context + ": goles y t90 deben coincidir con fuerza bruta");
    }
}

bool validClosedSystemState(const SimulationConfig& config,
                            const std::vector<Particle>& particles) {
    for (std::size_t i = 0; i < particles.size(); ++i) {
        const Particle& particle = particles[i];
        if (!std::isfinite(particle.position.x) || !std::isfinite(particle.position.y) ||
            !std::isfinite(particle.velocity.x) || !std::isfinite(particle.velocity.y) ||
            particle.position.x < particle.radius - 1e-8 ||
            particle.position.x > config.length - particle.radius + 1e-8 ||
            particle.position.y < particle.radius - 1e-8 ||
            particle.position.y > config.width - particle.radius + 1e-8) {
            return false;
        }
        for (std::size_t j = 0; j < i; ++j) {
            const double reach = particle.radius + particles[j].radius;
            if (distanceSquared(particle.position, particles[j].position) <
                reach * reach - 1e-8) {
                return false;
            }
        }
        for (const Obstacle& obstacle : config.obstacles) {
            const double reach = particle.radius + obstacle.radius;
            if (distanceSquared(particle.position, obstacle.center) <
                reach * reach - 1e-8) {
                return false;
            }
        }
    }
    return true;
}

void testStressInvariants(TestSuite& suite) {
    for (const std::uint64_t seed : {101ULL, 202ULL, 303ULL}) {
        SimulationConfig config;
        config.particleCount = 30;
        config.maxTime = 20.0;
        config.seed = seed;
        config.obstacles = {
            {{0.40, 0.22}, 0.05},
            {{0.80, 0.46}, 0.05},
        };
        const std::vector<Particle> initial = generateParticles(config);
        double energyBefore = 0.0;
        for (const Particle& particle : initial) energyBefore += kineticEnergy(particle);

        Simulation simulation(config, initial);
        bool everyEventValid = true;
        int lastGoals = 0;
        const SimulationResult result = simulation.run(
            [&](double, const Event&, const std::vector<Particle>& particles, int goals) {
                everyEventValid = everyEventValid &&
                                  validClosedSystemState(config, particles) &&
                                  goals >= lastGoals && goals <= config.particleCount;
                lastGoals = goals;
            });

        double energyAfter = 0.0;
        int used = 0;
        for (const Particle& particle : simulation.particles()) {
            energyAfter += kineticEnergy(particle);
            if (particle.state == ParticleState::Used) ++used;
        }
        const std::string context = "stress seed=" + std::to_string(seed);
        suite.check(everyEventValid, context + ": invariantes deben valer despues de cada evento");
        suite.check(validClosedSystemState(config, simulation.particles()),
                    context + ": el estado final debe ser geometricamente valido");
        suite.check(near(energyAfter, energyBefore, 1e-8),
                    context + ": la energia no debe derivar");
        suite.check(used == result.goals &&
                        near(result.usedFraction,
                             static_cast<double>(used) / config.particleCount),
                    context + ": estado, goles y Fu deben ser consistentes");
    }
}

void testSimulationRejectsEmptySystem(TestSuite& suite) {
    SimulationConfig config;
    config.particleCount = 0;
    bool rejected = false;
    try {
        Simulation simulation(config, {});
    } catch (const std::invalid_argument&) {
        rejected = true;
    }
    suite.check(rejected, "el motor debe rechazar un sistema sin particulas");
}

void testSimulationReproducibility(TestSuite& suite) {
    SimulationConfig config;
    config.particleCount = 12;
    config.maxTime = 5.0;
    config.seed = 9090;
    config.obstacles = {{{0.60, 0.34}, 0.06}};
    const std::vector<Particle> initial = generateParticles(config);

    Simulation first(config, initial);
    Simulation second(config, initial);
    std::vector<RecordedEvent> firstEvents;
    std::vector<RecordedEvent> secondEvents;
    const SimulationResult firstResult = first.run(
        [&](double time, const Event& event, const std::vector<Particle>&, int) {
            firstEvents.push_back(
                {time, event.type, event.particleA, event.particleB, event.obstacle});
        });
    const SimulationResult secondResult = second.run(
        [&](double time, const Event& event, const std::vector<Particle>&, int) {
            secondEvents.push_back(
                {time, event.type, event.particleA, event.particleB, event.obstacle});
        });

    bool sameEvents = firstEvents.size() == secondEvents.size();
    for (std::size_t i = 0; sameEvents && i < firstEvents.size(); ++i) {
        sameEvents = firstEvents[i].time == secondEvents[i].time &&
                     firstEvents[i].type == secondEvents[i].type &&
                     firstEvents[i].particleA == secondEvents[i].particleA &&
                     firstEvents[i].particleB == secondEvents[i].particleB &&
                     firstEvents[i].obstacle == secondEvents[i].obstacle;
    }
    suite.check(sameEvents, "dos corridas identicas deben producir la misma secuencia exacta");

    bool sameParticles = first.particles().size() == second.particles().size();
    for (std::size_t i = 0; sameParticles && i < first.particles().size(); ++i) {
        const Particle& a = first.particles()[i];
        const Particle& b = second.particles()[i];
        sameParticles = a.position.x == b.position.x && a.position.y == b.position.y &&
                        a.velocity.x == b.velocity.x && a.velocity.y == b.velocity.y &&
                        a.state == b.state && a.collisionCount == b.collisionCount;
    }
    suite.check(sameParticles, "dos corridas identicas deben terminar bit a bit iguales");
    suite.check(firstResult.t90 == secondResult.t90 &&
                    firstResult.goals == secondResult.goals &&
                    firstResult.processedEvents == secondResult.processedEvents &&
                    firstResult.scheduledEvents == secondResult.scheduledEvents &&
                    firstResult.discardedEvents == secondResult.discardedEvents,
                "los observables deterministas no deben depender del tiempo de CPU");
}

}  // namespace

int main() {
    TestSuite suite;

    suite.check(__cplusplus >= 202002L, "el motor debe compilar como C++20");
    suite.check(std::numeric_limits<double>::is_iec559,
                "double debe ofrecer aritmetica IEEE-754 para infinitos y NaN");
    suite.check(std::numeric_limits<double>::digits >= 53,
                "double debe tener precision suficiente para tiempos de colision");

    testOfficialDefaults(suite);
    testArgumentParsing(suite);
    testInvalidArguments(suite);
    testModelContracts(suite);
    testObstacleValidation(suite);
    testObstacleFile(suite);
    testGenerator(suite);
    testGeneratorSaturation(suite);
    testWallPredictionAndResolution(suite);
    testHeadOnParticleCollision(suite);
    testObliqueParticleCollision(suite);
    testObstacleCollision(suite);
    testGoalGeometry(suite);
    testSingleParticleEventLoop(suite);
    testWallOutsideGoalDoesNotScore(suite);
    testLazyInvalidation(suite);
    testLongEventDrivenRun(suite);
    testOutputFormats(suite);
    testPriorityQueueMatchesBruteForceOracle(suite);
    testStressInvariants(suite);
    testSimulationRejectsEmptySystem(suite);
    testSimulationReproducibility(suite);

    return suite.finish();
}
