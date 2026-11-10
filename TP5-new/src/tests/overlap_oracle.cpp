#include "overlap_oracle.h"

#include <algorithm>
#include <cmath>
#include <cstdio>

namespace {

struct Segment {
    double ax;
    double ay;
    double bx;
    double by;
};

// Distancia de un punto al segmento, con proyeccion acotada escrita aca.
double distanceToSegment(double px, double py, const Segment& s) {
    const double dx = s.bx - s.ax;
    const double dy = s.by - s.ay;
    const double len2 = dx * dx + dy * dy;
    double t = 0.0;
    if (len2 > 0.0) {
        t = ((px - s.ax) * dx + (py - s.ay) * dy) / len2;
        t = std::min(1.0, std::max(0.0, t));
    }
    const double qx = s.ax + t * dx;
    const double qy = s.ay + t * dy;
    return std::hypot(px - qx, py - qy);
}

void noteViolation(OverlapReport& report, const char* text) {
    if (report.firstViolation.empty()) report.firstViolation = text;
}

}  // namespace

OverlapReport checkOverlaps(const std::vector<OracleRow>& rows, const OracleRoom& room,
                            double depthFraction) {
    OverlapReport report;
    char text[160];

    // (a) todos los pares.
    for (std::size_t i = 0; i < rows.size(); ++i) {
        for (std::size_t j = i + 1; j < rows.size(); ++j) {
            const double distance = std::hypot(rows[i].x - rows[j].x, rows[i].y - rows[j].y);
            const double depth = rows[i].r + rows[j].r - distance;
            if (depth <= 0.0) continue;
            report.maxAgentDepth = std::max(report.maxAgentDepth, depth);
            if (depth > depthFraction * std::min(rows[i].r, rows[j].r)) {
                ++report.violations;
                ++report.agentPairViolations;
                std::snprintf(text, sizeof text, "par %d-%d: profundidad %.6f (distancia %.6f)",
                              rows[i].id, rows[j].id, depth, distance);
                noteViolation(report, text);
            }
        }
    }

    // (b) cinco segmentos de pared; la puerta esta centrada en la pared inferior.
    const double xa = room.side / 2.0 - room.doorWidth / 2.0;
    const double xb = room.side / 2.0 + room.doorWidth / 2.0;
    const Segment walls[5] = {
        {0.0, 0.0, xa, 0.0},
        {xb, 0.0, room.side, 0.0},
        {room.side, 0.0, room.side, room.side},
        {room.side, room.side, 0.0, room.side},
        {0.0, room.side, 0.0, 0.0},
    };
    for (const OracleRow& row : rows) {
        for (int w = 0; w < 5; ++w) {
            const double depth = row.r - distanceToSegment(row.x, row.y, walls[w]);
            if (depth <= 0.0) continue;
            report.maxWallDepth = std::max(report.maxWallDepth, depth);
            if (depth > depthFraction * row.r) {
                ++report.violations;
                ++report.wallViolations;
                std::snprintf(text, sizeof text, "agente %d con el segmento %d: profundidad %.6f",
                              row.id, w, depth);
                noteViolation(report, text);
            }
        }
    }

    // (c) escape: dentro de la sala o, si y < 0, a lo sumo en la zona de salida.
    const double doorX = room.side / 2.0;
    for (const OracleRow& row : rows) {
        bool escaped = false;
        if (row.y >= 0.0) {
            escaped = !(row.x >= 0.0 && row.x <= room.side && row.y <= room.side);
        } else {
            escaped = std::hypot(row.x - doorX, row.y) > room.exitDistance + 1e-3;
        }
        if (escaped) {
            ++report.violations;
            ++report.escapeViolations;
            std::snprintf(text, sizeof text, "agente %d escapo de la sala en (%.6f, %.6f)", row.id,
                          row.x, row.y);
            noteViolation(report, text);
        }
    }
    return report;
}

void mergeReports(OverlapReport& total, const OverlapReport& frame) {
    total.violations += frame.violations;
    total.agentPairViolations += frame.agentPairViolations;
    total.wallViolations += frame.wallViolations;
    total.escapeViolations += frame.escapeViolations;
    total.maxAgentDepth = std::max(total.maxAgentDepth, frame.maxAgentDepth);
    total.maxWallDepth = std::max(total.maxWallDepth, frame.maxWallDepth);
    if (total.firstViolation.empty()) total.firstViolation = frame.firstViolation;
}
