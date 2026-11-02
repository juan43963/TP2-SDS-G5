// Suite `trajectory_io`: ida y vuelta motor -> archivo -> lector independiente (OUT-01),
// archivo truncado y archivos malformados.
#include <algorithm>
#include <cmath>
#include <cstdio>
#include <filesystem>
#include <fstream>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>

#include "evacuation.h"
#include "generator.h"
#include "io.h"
#include "test_support.h"
#include "trajectory_reader.h"

namespace {

const char* const kRoundTripPath = "build/test_trajectory_io.txt";

bool near(double a, double b, double tolerance) { return std::abs(a - b) <= tolerance; }

struct StoredFrame {
    double time;
    std::vector<Agent> agents;
};

std::string readWholeFile(const std::string& path) {
    std::ifstream in(path);
    std::ostringstream text;
    text << in.rdbuf();
    return text.str();
}

void writeTextFile(const std::string& path, const std::string& text) {
    std::ofstream out(path);
    out << text;
}

template <typename Function>
bool throwsRuntimeError(Function&& function) {
    try {
        function();
    } catch (const std::runtime_error&) {
        return true;
    } catch (...) {
        return false;
    }
    return false;
}

EvacuationConfig smallConfig() {
    EvacuationConfig config;
    config.agentCount = 40;
    config.side = 10.0;
    config.seed = 5;
    config.dt2 = 0.1;
    return config;
}

// Corre el motor, escribe el archivo y devuelve los frames que vio el sink.
std::vector<StoredFrame> runAndWrite(const EvacuationConfig& config, const std::string& path) {
    std::filesystem::create_directories("build");
    std::vector<StoredFrame> stored;
    TrajectoryWriter writer(path, config);
    const FrameSink sink = [&](double time, const std::vector<Agent>& agents) {
        stored.push_back({time, agents});
        writer.writeFrame(time, agents);
    };
    runEvacuation(config, generateAgents(config), sink);
    writer.finish();
    return stored;
}

void testRoundTrip(TestSuite& suite) {
    const EvacuationConfig config = smallConfig();
    const std::vector<StoredFrame> stored = runAndWrite(config, kRoundTripPath);
    const Trajectory t = readTrajectory(kRoundTripPath);

    const TrajectoryHeader& h = t.header;
    suite.check(h.scheme == "tsdmd", "cabecera: scheme tsdmd");
    suite.check(h.agentCount == config.agentCount, "cabecera: N");
    suite.check(near(h.side, config.side, 1e-12), "cabecera: L");
    suite.check(near(h.doorWidth, config.doorWidth, 1e-12), "cabecera: d");
    suite.check(near(h.doorX, config.side / 2.0, 1e-12), "cabecera: door_x = L/2");
    suite.check(near(h.exitDistance, config.exitDistance, 1e-12), "cabecera: exit_distance");
    suite.check(h.seed == config.seed, "cabecera: seed");
    suite.check(near(h.dt, config.dt, 1e-15), "cabecera: dt");
    suite.check(near(h.dt2, config.dt2, 1e-15), "cabecera: dt2");
    suite.check(near(h.desiredSpeed, config.sfm.desiredSpeed, 1e-12), "cabecera: vd");
    suite.check(near(h.tau, config.sfm.tau, 1e-12), "cabecera: tau");
    suite.check(near(h.mass, config.sfm.mass, 1e-12), "cabecera: mass");
    suite.check(near(h.stiffness, config.sfm.stiffness, 1e-6), "cabecera: k");
    suite.check(near(h.friction, config.sfm.friction, 1e-6), "cabecera: kappa");
    suite.check(near(h.radiusMin, config.radiusMin, 1e-12), "cabecera: rmin");
    suite.check(near(h.radiusMax, config.radiusMax, 1e-12), "cabecera: rmax");

    suite.check(t.complete, "el archivo termina con END");
    suite.check(t.frames.size() == stored.size(), "misma cantidad de frames que el sink");
    suite.check(t.frames.size() > 10, "la corrida produce mas de 10 frames");

    bool timesMatch = true;
    bool countsMatch = true;
    bool fieldsMatch = true;
    bool populationMatches = true;
    bool schemeColumn = true;
    const std::size_t common = std::min(t.frames.size(), stored.size());
    for (std::size_t f = 0; f < common; ++f) {
        const TrajectoryFrame& read = t.frames[f];
        const StoredFrame& mem = stored[f];
        if (!near(read.time, mem.time, 5e-7)) timesMatch = false;
        if (read.rows.size() != mem.agents.size()) {
            countsMatch = false;
            continue;
        }
        int inRoom = 0;
        for (std::size_t i = 0; i < read.rows.size(); ++i) {
            const TrajectoryRow& row = read.rows[i];
            const Agent& a = mem.agents[i];
            if (row.id != a.id || !near(row.x, a.position.x, 6e-6) || !near(row.y, a.position.y, 6e-6) ||
                !near(row.vx, a.velocity.x, 6e-6) || !near(row.vy, a.velocity.y, 6e-6) ||
                !near(row.r, a.radius, 6e-6)) {
                fieldsMatch = false;
            }
            if (row.scheme != 0) schemeColumn = false;
            if (a.status == AgentStatus::InRoom) ++inRoom;
        }
        if (roomPopulation(read) != inRoom) populationMatches = false;
    }
    suite.check(timesMatch, "cada frame conserva el tiempo (tolerancia 5e-7)");
    suite.check(countsMatch, "cada frame conserva la cantidad de filas");
    suite.check(fieldsMatch, "cada campo coincide con el estado del motor (tolerancia 6e-6)");
    suite.check(schemeColumn, "la columna scheme vale 0 en todas las filas");
    suite.check(populationMatches, "roomPopulation = agentes InRoom en memoria, en cada frame");

    // D-04: tiempos en multiplos enteros de dt2 (salvo el ultimo) y estrictamente crecientes.
    bool multiples = true;
    bool increasing = true;
    for (std::size_t f = 0; f + 1 < t.frames.size(); ++f) {
        const double ratio = t.frames[f].time / config.dt2;
        if (std::abs(ratio - std::round(ratio)) > 1e-6) multiples = false;
    }
    for (std::size_t f = 1; f < t.frames.size(); ++f) {
        if (!(t.frames[f].time > t.frames[f - 1].time)) increasing = false;
    }
    suite.check(multiples, "los tiempos (salvo el ultimo) son multiplos enteros de dt2");
    suite.check(increasing, "los tiempos crecen estrictamente");
    suite.check(!t.frames.empty() && t.frames.front().time == 0.0, "el primer frame es t = 0");
    suite.check(!t.frames.empty() && static_cast<int>(t.frames.front().rows.size()) == config.agentCount,
                "el primer frame trae los N agentes");
    suite.check(!t.frames.empty() && t.frames.back().rows.empty(), "el ultimo frame no tiene filas");
}

void testTruncatedFile(TestSuite& suite) {
    const std::string text = readWholeFile(kRoundTripPath);
    const Trajectory full = readTrajectory(kRoundTripPath);
    suite.check(text.size() > 4 && text.compare(text.size() - 4, 4, "END\n") == 0, "el archivo original termina en END");

    const std::string truncatedPath = "build/test_trajectory_io_truncated.txt";
    writeTextFile(truncatedPath, text.substr(0, text.size() - 4));
    bool threw = false;
    Trajectory truncated;
    try {
        truncated = readTrajectory(truncatedPath);
    } catch (...) {
        threw = true;
    }
    suite.check(!threw, "un archivo sin END no lanza");
    suite.check(!truncated.complete, "un archivo sin END informa complete == false");
    suite.check(truncated.frames.size() == full.frames.size(), "el truncado conserva todos los frames");
}

void testMalformedFiles(TestSuite& suite) {
    const std::string header =
        "TP5_TRAJECTORY 1\nscheme tsdmd\nN 3\nL 10\nd 0.8\ndoor_x 5\nexit_distance 1\nseed 1\n"
        "dt 0.0001\n";
    const std::string tail =
        "vd 1.5\ntau 0.5\nmass 80\nk 120000\nkappa 240000\nrmin 0.18\nrmax 0.25\n"
        "COLUMNS id x y vx vy r scheme\n";
    const std::string row = "0 1.00000 2.00000 0.10000 0.20000 0.20000 0\n";

    {
        // Control positivo: la misma estructura bien formada se lee.
        writeTextFile("build/test_trajectory_io_ok.txt",
                      header + "dt2 0.1\n" + tail + "FRAME 0.000000 2\n" + row + row + "END\n");
        const Trajectory ok = readTrajectory("build/test_trajectory_io_ok.txt");
        suite.check(ok.complete && ok.frames.size() == 1 && ok.frames[0].rows.size() == 2,
                    "control: archivo bien formado se lee");
    }
    {
        writeTextFile("build/test_trajectory_io_bad_count.txt",
                      header + "dt2 0.1\n" + tail + "FRAME 0.000000 3\n" + row + row + "END\n");
        suite.check(throwsRuntimeError([] { readTrajectory("build/test_trajectory_io_bad_count.txt"); }),
                    "FRAME que declara 3 filas y trae 2 lanza");
    }
    {
        writeTextFile("build/test_trajectory_io_no_dt2.txt",
                      header + tail + "FRAME 0.000000 1\n" + row + "END\n");
        suite.check(throwsRuntimeError([] { readTrajectory("build/test_trajectory_io_no_dt2.txt"); }),
                    "cabecera sin la clave dt2 lanza");
    }
    {
        writeTextFile("build/test_trajectory_io_short_row.txt",
                      header + "dt2 0.1\n" + tail + "FRAME 0.000000 1\n" +
                          "0 1.00000 2.00000 0.10000 0.20000 0.20000\n" + "END\n");
        suite.check(throwsRuntimeError([] { readTrajectory("build/test_trajectory_io_short_row.txt"); }),
                    "fila con 6 campos lanza");
    }
    {
        writeTextFile("build/test_trajectory_io_bad_first.txt", "OTRO 1\n");
        suite.check(throwsRuntimeError([] { readTrajectory("build/test_trajectory_io_bad_first.txt"); }),
                    "primera linea distinta lanza");
    }
    {
        writeTextFile("build/test_trajectory_io_bad_columns.txt",
                      header + "dt2 0.1\nvd 1.5\ntau 0.5\nmass 80\nk 1\nkappa 1\nrmin 0.18\nrmax 0.25\n"
                               "COLUMNS id x y\n");
        suite.check(throwsRuntimeError([] { readTrajectory("build/test_trajectory_io_bad_columns.txt"); }),
                    "columnas distintas de las esperadas lanza");
    }
    {
        writeTextFile("build/test_trajectory_io_nan.txt",
                      header + "dt2 0.1\n" + tail + "FRAME 0.000000 1\n" +
                          "0 abc 2.00000 0.10000 0.20000 0.20000 0\n" + "END\n");
        suite.check(throwsRuntimeError([] { readTrajectory("build/test_trajectory_io_nan.txt"); }),
                    "valor no numerico lanza");
    }
    suite.check(throwsRuntimeError([] { readTrajectory("build/no_existe_este_archivo.txt"); }),
                "archivo inexistente lanza");
}

void testWriterRejectsBadPath(TestSuite& suite) {
    std::filesystem::create_directories("build");
    const EvacuationConfig config = smallConfig();
    suite.check(throwsRuntimeError([&] { TrajectoryWriter writer("build", config); }),
                "TrajectoryWriter con un directorio como ruta lanza std::runtime_error");
}

void runTrajectoryIoTests(TestSuite& suite) {
    testRoundTrip(suite);
    testTruncatedFile(suite);
    testMalformedFiles(suite);
    testWriterRejectsBadPath(suite);
}

const TestRegistration registration("trajectory_io", runTrajectoryIoTests);

}  // namespace
