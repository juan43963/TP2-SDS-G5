# Sobre una copia ya parcheada con patch_cluster.py: tolerancia y tope de pasadas de Gauss-Seidel por entorno
# (GS_TOL, GS_MAXSWEEP; defaults = los de la regla actual) + contadores impresos a stderr al terminar.
p = 'src/engine/edmd.cpp'
s = open(p, encoding='utf8').read()
s = s.replace('#include <cstdlib>', '#include <cstdlib>\n#include <cstdio>\n#include <map>', 1)
helper = r'''struct GsStats {
    unsigned long long calls = 0, sweeps = 0, capHits = 0, members = 0, maxMembers = 0;
    std::map<int, unsigned long long> hist;
    ~GsStats() {
        if (!std::getenv("GS_STATS")) return;
        std::fprintf(stderr, "GSSTATS calls=%llu sweeps=%llu sweeps_per_call=%.2f capHits=%llu members_mean=%.2f maxMembers=%llu\n",
                     calls, sweeps, calls ? double(sweeps) / calls : 0.0, capHits, calls ? double(members) / calls : 0.0, maxMembers);
        for (auto& kv : hist) std::fprintf(stderr, "GSHIST sweeps<=%d: %llu\n", kv.first, kv.second);
    }
};
static GsStats gsStats;
static double gsTol() { static const double v = std::getenv("GS_TOL") ? std::atof(std::getenv("GS_TOL")) : 1e-12; return v; }
static int gsMax() { static const int v = std::getenv("GS_MAXSWEEP") ? std::atoi(std::getenv("GS_MAXSWEEP")) : 2000; return v; }
static bool clusterRule() {'''
assert 'static bool clusterRule() {' in s
s = s.replace('static bool clusterRule() {', helper, 1)
old = '    for (int sweep = 0; sweep < 2000; ++sweep) {'
assert old in s
s = s.replace(old, '    int usedSweeps = 0;\n    const int gsMaxSweeps = gsMax();\n    const double gsTolerance = gsTol();\n    for (int sweep = 0; sweep < gsMaxSweeps; ++sweep) {\n        ++usedSweeps;', 1)
old = '        if (worst < 1e-12) break;\n    }\n'
assert old in s
s = s.replace(old, '        if (worst < gsTolerance) break;\n    }\n'
              '    ++gsStats.calls; gsStats.sweeps += usedSweeps; gsStats.members += members.size();\n'
              '    if (members.size() > gsStats.maxMembers) gsStats.maxMembers = members.size();\n'
              '    if (usedSweeps >= gsMaxSweeps) ++gsStats.capHits;\n'
              '    { int b = 1; while (b < usedSweeps) b *= 2; ++gsStats.hist[b]; }\n', 1)
open(p, 'w', encoding='utf8').write(s)
print('gs patched')
