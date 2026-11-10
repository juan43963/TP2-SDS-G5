// tp5_check: chequeo independiente de un archivo de trayectoria TP5_TRAJECTORY 1 (D-11, D-12).
// Lee solo el archivo de texto (no ejecuta el simulador) y aplica el oraculo de superposicion
// a cada frame. Herramienta de verificacion: no forma parte del motor entregable.
#include <cstdio>
#include <cstdlib>
#include <exception>
#include <stdexcept>
#include <string>
#include <vector>

#include "../tests/overlap_oracle.h"
#include "../tests/trajectory_reader.h"

namespace {

struct Args {
    std::string path;
    double fraction = kSustainedOverlapFraction;
};

// Devuelve false ante uso incorrecto.
bool parseArgs(int argc, char** argv, Args& args) {
    for (int i = 1; i < argc; ++i) {
        const std::string a = argv[i];
        if (a == "--fraction") {
            if (i + 1 >= argc) return false;
            char* end = nullptr;
            const double v = std::strtod(argv[++i], &end);
            if (end == argv[i] || *end != '\0' || !(v > 0.0)) return false;
            args.fraction = v;
        } else if (!a.empty() && a[0] == '-') {
            return false;
        } else if (args.path.empty()) {
            args.path = a;
        } else {
            return false;
        }
    }
    return !args.path.empty();
}

}  // namespace

int main(int argc, char** argv) try {
    Args args;
    if (!parseArgs(argc, argv, args)) {
        std::fprintf(stderr, "uso: tp5_check ARCHIVO [--fraction F]\n");
        return 2;
    }

    const Trajectory traj = readTrajectory(args.path);
    const TrajectoryHeader& h = traj.header;

    OracleRoom room;
    room.side = h.side;
    room.doorWidth = h.doorWidth;
    room.exitDistance = h.exitDistance;

    OverlapReport total;
    std::size_t rowsMax = 0;
    int popFirst = -1;
    int popPrev = -1;
    int popIncreases = 0;
    double tEvacFile = -1.0;
    std::vector<OracleRow> rows;

    for (const TrajectoryFrame& frame : traj.frames) {
        rows.clear();
        rows.reserve(frame.rows.size());
        for (const TrajectoryRow& r : frame.rows) rows.push_back({r.id, r.x, r.y, r.r});
        mergeReports(total, checkOverlaps(rows, room, args.fraction));

        if (frame.rows.size() > rowsMax) rowsMax = frame.rows.size();
        const int pop = roomPopulation(frame);
        if (popFirst < 0) popFirst = pop;
        if (popPrev >= 0 && pop > popPrev) ++popIncreases;
        popPrev = pop;
        if (pop == 0 && tEvacFile < 0.0) tEvacFile = frame.time;
    }

    const std::size_t rowsLast = traj.frames.empty() ? 0 : traj.frames.back().rows.size();
    const bool ok = traj.complete && !traj.frames.empty() && popFirst == h.agentCount &&
                    rowsLast == 0 && total.violations == 0;

    std::printf(
        "CHECK file=%s N=%d frames=%zu rows_max=%zu pop_first=%d rows_last=%zu pop_increases=%d "
        "max_agent_depth=%.6g max_wall_depth=%.6g violations=%d t_evac_file=%.6f complete=%d\n",
        args.path.c_str(), h.agentCount, traj.frames.size(), rowsMax, popFirst, rowsLast,
        popIncreases, total.maxAgentDepth, total.maxWallDepth, total.violations, tEvacFile,
        traj.complete ? 1 : 0);
    if (total.violations > 0) std::printf("firstViolation %s\n", total.firstViolation.c_str());
    return ok ? 0 : 1;
} catch (const std::exception& e) {
    std::fprintf(stderr, "error: %s\n", e.what());
    return 2;
}
