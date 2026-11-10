#include "trajectory_reader.h"

#include <cerrno>
#include <cmath>
#include <cstdlib>
#include <fstream>
#include <map>
#include <sstream>
#include <stdexcept>
#include <utility>

namespace {

[[noreturn]] void fail(const std::string& path, int lineNumber, const std::string& what) {
    throw std::runtime_error(path + ":" + std::to_string(lineNumber) + ": " + what);
}

std::vector<std::string> split(const std::string& line) {
    std::vector<std::string> tokens;
    std::istringstream in(line);
    std::string token;
    while (in >> token) tokens.push_back(token);
    return tokens;
}

double toDouble(const std::string& text, const std::string& path, int lineNumber) {
    char* end = nullptr;
    errno = 0;
    const double value = std::strtod(text.c_str(), &end);
    if (errno != 0 || end == text.c_str() || *end != '\0' || !std::isfinite(value)) {
        fail(path, lineNumber, "valor no numerico '" + text + "'");
    }
    return value;
}

long long toInteger(const std::string& text, const std::string& path, int lineNumber) {
    char* end = nullptr;
    errno = 0;
    const long long value = std::strtoll(text.c_str(), &end, 10);
    if (errno != 0 || end == text.c_str() || *end != '\0') {
        fail(path, lineNumber, "entero invalido '" + text + "'");
    }
    return value;
}

const std::string& requireKey(const std::map<std::string, std::string>& values,
                              const std::string& key, const std::string& path, int lineNumber) {
    const auto it = values.find(key);
    if (it == values.end()) fail(path, lineNumber, "falta la clave obligatoria '" + key + "'");
    return it->second;
}

}  // namespace

Trajectory readTrajectory(const std::string& path) {
    std::ifstream in(path);
    if (!in) throw std::runtime_error("no se pudo abrir '" + path + "'");

    Trajectory trajectory;
    std::string line;
    int lineNumber = 0;

    if (!std::getline(in, line)) fail(path, 1, "archivo vacio");
    lineNumber = 1;
    if (line != "TP5_TRAJECTORY 1") fail(path, lineNumber, "se esperaba 'TP5_TRAJECTORY 1'");

    // Cabecera: pares clave valor hasta la linea COLUMNS.
    std::map<std::string, std::string> values;
    bool columnsSeen = false;
    while (std::getline(in, line)) {
        ++lineNumber;
        const std::vector<std::string> tokens = split(line);
        if (tokens.empty()) fail(path, lineNumber, "linea vacia en la cabecera");
        if (tokens[0] == "COLUMNS") {
            const std::vector<std::string> expected{"COLUMNS", "id", "x", "y", "vx", "vy", "r", "scheme"};
            if (tokens != expected) fail(path, lineNumber, "columnas distintas de 'id x y vx vy r scheme'");
            columnsSeen = true;
            break;
        }
        if (tokens.size() != 2) fail(path, lineNumber, "se esperaba 'clave valor'");
        values[tokens[0]] = tokens[1];
    }
    if (!columnsSeen) fail(path, lineNumber, "falta la linea COLUMNS");

    TrajectoryHeader& h = trajectory.header;
    h.scheme = requireKey(values, "scheme", path, lineNumber);
    h.agentCount = static_cast<int>(toInteger(requireKey(values, "N", path, lineNumber), path, lineNumber));
    h.side = toDouble(requireKey(values, "L", path, lineNumber), path, lineNumber);
    h.doorWidth = toDouble(requireKey(values, "d", path, lineNumber), path, lineNumber);
    h.doorX = toDouble(requireKey(values, "door_x", path, lineNumber), path, lineNumber);
    h.exitDistance = toDouble(requireKey(values, "exit_distance", path, lineNumber), path, lineNumber);
    h.seed = static_cast<std::uint64_t>(
        toInteger(requireKey(values, "seed", path, lineNumber), path, lineNumber));
    h.dt = toDouble(requireKey(values, "dt", path, lineNumber), path, lineNumber);
    h.dt2 = toDouble(requireKey(values, "dt2", path, lineNumber), path, lineNumber);
    h.desiredSpeed = toDouble(requireKey(values, "vd", path, lineNumber), path, lineNumber);
    h.tau = toDouble(requireKey(values, "tau", path, lineNumber), path, lineNumber);
    h.mass = toDouble(requireKey(values, "mass", path, lineNumber), path, lineNumber);
    h.stiffness = toDouble(requireKey(values, "k", path, lineNumber), path, lineNumber);
    h.friction = toDouble(requireKey(values, "kappa", path, lineNumber), path, lineNumber);
    h.radiusMin = toDouble(requireKey(values, "rmin", path, lineNumber), path, lineNumber);
    h.radiusMax = toDouble(requireKey(values, "rmax", path, lineNumber), path, lineNumber);

    // Frames: sin reservar memoria a partir del conteo declarado (T-06-03).
    while (std::getline(in, line)) {
        ++lineNumber;
        if (line == "END") {
            trajectory.complete = true;
            break;
        }
        const std::vector<std::string> head = split(line);
        if (head.size() != 3 || head[0] != "FRAME") fail(path, lineNumber, "se esperaba 'FRAME t n' o END");
        TrajectoryFrame frame;
        frame.time = toDouble(head[1], path, lineNumber);
        const long long declared = toInteger(head[2], path, lineNumber);
        if (declared < 0) fail(path, lineNumber, "cantidad de filas negativa");
        const int frameLine = lineNumber;

        for (long long i = 0; i < declared; ++i) {
            if (!std::getline(in, line)) {
                fail(path, lineNumber, "el FRAME de la linea " + std::to_string(frameLine) + " declara " +
                                           std::to_string(declared) + " filas y el archivo termina antes");
            }
            ++lineNumber;
            const std::vector<std::string> f = split(line);
            if (!f.empty() && (f[0] == "FRAME" || f[0] == "END")) {
                fail(path, lineNumber, "el FRAME de la linea " + std::to_string(frameLine) + " declara " +
                                           std::to_string(declared) + " filas pero trae " +
                                           std::to_string(i));
            }
            if (f.size() != 7) {
                fail(path, lineNumber, "la fila tiene " + std::to_string(f.size()) + " campos, se esperaban 7");
            }
            TrajectoryRow row;
            row.id = static_cast<int>(toInteger(f[0], path, lineNumber));
            row.x = toDouble(f[1], path, lineNumber);
            row.y = toDouble(f[2], path, lineNumber);
            row.vx = toDouble(f[3], path, lineNumber);
            row.vy = toDouble(f[4], path, lineNumber);
            row.r = toDouble(f[5], path, lineNumber);
            row.scheme = static_cast<int>(toInteger(f[6], path, lineNumber));
            frame.rows.push_back(row);
        }
        trajectory.frames.push_back(std::move(frame));
    }
    return trajectory;
}

int roomPopulation(const TrajectoryFrame& frame) {
    int count = 0;
    for (const TrajectoryRow& row : frame.rows) {
        if (row.y >= 0.0) ++count;
    }
    return count;
}
