#include "config_io.h"

#include <cmath>
#include <fstream>
#include <sstream>
#include <stdexcept>
#include <string>

#include "geometry.h"

void validateObstacleConfiguration(const std::vector<Obstacle>& obstacles,
                                   const SimulationConfig& config) {
    for (std::size_t i = 0; i < obstacles.size(); ++i) {
        const Obstacle& obstacle = obstacles[i];
        if (!std::isfinite(obstacle.center.x) || !std::isfinite(obstacle.center.y) ||
            !std::isfinite(obstacle.radius)) {
            throw std::invalid_argument("obstaculo " + std::to_string(i) +
                                        ": todos los valores deben ser finitos");
        }
        if (obstacle.radius < config.particleRadius) {
            throw std::invalid_argument("obstaculo " + std::to_string(i) +
                                        ": R debe ser >= al radio de particula");
        }
        if (obstacle.center.x - obstacle.radius < -kGeometryEpsilon ||
            obstacle.center.x + obstacle.radius > config.length + kGeometryEpsilon ||
            obstacle.center.y - obstacle.radius < -kGeometryEpsilon ||
            obstacle.center.y + obstacle.radius > config.width + kGeometryEpsilon) {
            throw std::invalid_argument("obstaculo " + std::to_string(i) +
                                        ": no esta completamente dentro de la mesa");
        }

        for (std::size_t j = 0; j < i; ++j) {
            if (circlesOverlap(obstacle.center, obstacle.radius, obstacles[j].center,
                               obstacles[j].radius)) {
                throw std::invalid_argument("obstaculos " + std::to_string(j) + " y " +
                                            std::to_string(i) + ": se superponen");
            }
        }
    }
}

std::vector<Obstacle> readObstacleConfig(const std::string& path,
                                         const SimulationConfig& config) {
    std::ifstream input(path);
    if (!input) throw std::runtime_error("no se pudo abrir la configuracion de obstaculos: " + path);

    std::vector<Obstacle> obstacles;
    std::string line;
    int lineNumber = 0;
    while (std::getline(input, line)) {
        ++lineNumber;
        const std::size_t first = line.find_first_not_of(" \t\r");
        if (first == std::string::npos || line[first] == '#') continue;

        std::istringstream row(line);
        Obstacle obstacle;
        std::string extra;
        if (!(row >> obstacle.center.x >> obstacle.center.y >> obstacle.radius) || row >> extra) {
            throw std::runtime_error(path + ":" + std::to_string(lineNumber) +
                                     ": se esperaba exactamente 'x y R'");
        }
        obstacles.push_back(obstacle);
    }

    if (obstacles.empty()) {
        throw std::runtime_error(path + ": una configuracion debe contener al menos un obstaculo");
    }
    validateObstacleConfiguration(obstacles, config);
    return obstacles;
}
