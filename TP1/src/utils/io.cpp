#include "io.h"

#include <algorithm>
#include <fstream>
#include <iomanip>
#include <stdexcept>

void writeStatic(const std::string& path, const std::vector<Particle>& particles, double L) {
    std::ofstream out(path);
    if (!out) throw std::runtime_error("error al escribir: " + path);
    out << std::setprecision(12) << particles.size() << '\n' << L << '\n';
    for (const auto& p : particles) out << p.r << " 0\n";
}

void writeDynamic(const std::string& path, const std::vector<Particle>& particles, double t0) {
    std::ofstream out(path);
    if (!out) throw std::runtime_error("error al escribir: " + path);
    out << std::setprecision(12) << t0 << '\n';
    for (const auto& p : particles) out << p.x << ' ' << p.y << " 0 0\n";
}

void writeNeighbors(const std::string& path, const NeighborList& neighbors) {
    std::ofstream out(path);
    if (!out) throw std::runtime_error("error al escribir: " + path);
    for (size_t i = 0; i < neighbors.size(); ++i) {
        auto row = neighbors[i];
        std::sort(row.begin(), row.end());
        out << i;
        for (int j : row) out << ' ' << j;
        out << '\n';
    }
}

std::vector<Particle> readSystem(const std::string& staticPath, const std::string& dynamicPath, double& L) {
    std::ifstream sIn(staticPath), dIn(dynamicPath);
    if (!sIn || !dIn) throw std::runtime_error("error al abrir archivos de entrada");

    size_t n;
    if (!(sIn >> n >> L) || L <= 0) throw std::runtime_error(staticPath + ": formato invalido");

    std::vector<Particle> particles(n);
    for (size_t i = 0; i < n; ++i) {
        double dummy;
        particles[i].id = static_cast<int>(i);
        if (!(sIn >> particles[i].r >> dummy))
            throw std::runtime_error(staticPath + ": lectura de radio fallida en fila " + std::to_string(i));
    }

    double t0;
    if (!(dIn >> t0)) throw std::runtime_error(dynamicPath + ": formato invalido");
    for (size_t i = 0; i < n; ++i) {
        double vx, vy;
        if (!(dIn >> particles[i].x >> particles[i].y >> vx >> vy))
            throw std::runtime_error(dynamicPath + ": lectura de posicion fallida en fila " + std::to_string(i));
    }

    return particles;
}
