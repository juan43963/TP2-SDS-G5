#include <algorithm>
#include <cmath>
#include <cstdio>
#include <cstdlib>
#include <limits>
#include <stdexcept>
#include <string>
#include <vector>

#include "osc_cli.h"
#include "oscillator.h"
#include "test_support.h"

namespace {

// ECM = (1/N) * sum_{k=1..N} (r_k - r_analitica(k*dt))^2. El paso 0 no entra: su error
// es cero por construccion.
double ecm(Method method, const OscParams& p, double dt) {
    const long long n = stepCount(dt, p.tf);
    double sum = 0.0;
    integrate(method, p, dt, n, [&](long long step, double r, double) {
        if (step == 0) return;
        const double d = r - analyticPosition(p, static_cast<double>(step) * dt);
        sum += d * d;
    });
    return sum / static_cast<double>(n);
}

double loglogSlope(const std::vector<double>& xs, const std::vector<double>& ys) {
    const double n = static_cast<double>(xs.size());
    double sx = 0.0, sy = 0.0, sxx = 0.0, sxy = 0.0;
    for (std::size_t i = 0; i < xs.size(); ++i) {
        const double x = std::log10(xs[i]);
        const double y = std::log10(ys[i]);
        sx += x;
        sy += y;
        sxx += x * x;
        sxy += x * y;
    }
    return (n * sxy - sx * sy) / (n * sxx - sx * sx);
}

double slopeFor(Method method, const OscParams& p, const std::vector<double>& dts) {
    std::vector<double> errors;
    errors.reserve(dts.size());
    for (const double dt : dts) errors.push_back(ecm(method, p, dt));
    return loglogSlope(dts, errors);
}

void checkSlope(TestSuite& suite, Method method, const OscParams& p,
                const std::vector<double>& dts, double lo, double hi) {
    const double slope = slopeFor(method, p, dts);
    std::printf("pendiente %s = %.3f (ECM a dt=%g: %.3e)\n", methodName(method), slope, dts.front(),
                ecm(method, p, dts.front()));
    suite.check(slope >= lo && slope <= hi,
                std::string("pendiente log-log de ECM vs dt de ") + methodName(method) +
                    " fuera de [" + std::to_string(lo) + ", " + std::to_string(hi) + "]");
}

std::vector<double> positions(Method method, const OscParams& p, double dt) {
    std::vector<double> r;
    integrate(method, p, dt, stepCount(dt, p.tf), [&](long long, double ri, double) { r.push_back(ri); });
    return r;
}

// Devuelve true si parseOscOptions rechaza los argumentos con std::invalid_argument.
bool rejects(const std::vector<std::string>& args) {
    std::vector<std::string> storage = {"osc"};
    storage.insert(storage.end(), args.begin(), args.end());
    std::vector<char*> argv;
    for (std::string& s : storage) argv.push_back(s.data());
    try {
        parseOscOptions(static_cast<int>(argv.size()), argv.data());
    } catch (const std::invalid_argument&) {
        return true;
    }
    return false;
}

bool stepCountThrows(double dt, double tf) {
    try {
        stepCount(dt, tf);
    } catch (const std::invalid_argument&) {
        return true;
    }
    return false;
}

OscOptions parseOk(const std::vector<std::string>& args) {
    std::vector<std::string> storage = {"osc"};
    storage.insert(storage.end(), args.begin(), args.end());
    std::vector<char*> argv;
    for (std::string& s : storage) argv.push_back(s.data());
    return parseOscOptions(static_cast<int>(argv.size()), argv.data());
}

const Method kAllMethods[] = {Method::EulerPC, Method::Verlet, Method::VelocityVerlet,
                              Method::Beeman, Method::Gear5};

void testSlopes(TestSuite& suite) {
    const OscParams p;
    const std::vector<double> dts = {1e-3, 5e-4, 2e-4, 1e-4};
    const std::vector<double> gearDts = {5e-3, 2e-3, 1e-3};
    checkSlope(suite, Method::EulerPC, p, dts, 1.8, 2.2);
    checkSlope(suite, Method::Verlet, p, dts, 3.8, 4.2);
    checkSlope(suite, Method::VelocityVerlet, p, dts, 3.8, 4.2);
    checkSlope(suite, Method::Beeman, p, dts, 3.8, 4.2);
    checkSlope(suite, Method::Gear5, p, gearDts, 9.5, 10.5);
}

void testVelocityVerletMatchesVerlet(TestSuite& suite) {
    const OscParams p;
    const std::vector<double> a = positions(Method::VelocityVerlet, p, 1e-3);
    const std::vector<double> b = positions(Method::Verlet, p, 1e-3);
    double maxDiff = 0.0;
    for (std::size_t i = 0; i < a.size(); ++i) maxDiff = std::max(maxDiff, std::fabs(a[i] - b[i]));
    std::printf("max|r_vv - r_verlet| = %.3e m\n", maxDiff);
    suite.check(a.size() == b.size() && maxDiff <= 1e-10, "Velocity Verlet y Verlet coinciden en <= 1e-10 m");
}

void testIntegrateContract(TestSuite& suite) {
    const OscParams p;
    for (const Method m : kAllMethods) {
        const double dt = 1e-3;
        const long long steps = 200;
        long long calls = 0;
        bool inOrder = true;
        double r0 = 0.0, v0 = 0.0;
        integrate(m, p, dt, steps, [&](long long step, double r, double v) {
            if (step != calls) inOrder = false;
            if (step == 0) {
                r0 = r;
                v0 = v;
            }
            ++calls;
        });
        const std::string name = methodName(m);
        suite.check(calls == steps + 1 && inOrder, "integrate emite steps+1 llamadas en orden: " + name);
        suite.check(r0 == 1.0, "paso 0 con r == 1 exacto: " + name);
        if (m != Method::Verlet) {
            suite.check(v0 == initialVelocity(p), "paso 0 con v == v0 exacto: " + name);
        }
    }
    suite.check(initialVelocity(OscParams{}) == -1.0 * 100.0 / (2.0 * 70.0), "v0 = -A*gamma/(2m)");
    const OscParams p0;
    suite.check(analyticPosition(p0, 0.0) == 1.0, "analyticPosition(0) == 1");
    const double h = 1e-6;
    const double deriv = (analyticPosition(p0, h) - analyticPosition(p0, -h)) / (2.0 * h);
    suite.check(std::fabs(deriv - initialVelocity(p0)) <= 1e-6, "derivada analitica en 0 == v0");
    bool threw = false;
    try {
        integrate(Method::EulerPC, p0, 1e-3, -1, [](long long, double, double) {});
    } catch (const std::invalid_argument&) {
        threw = true;
    }
    suite.check(threw, "integrate rechaza steps < 0");
}

void testStepCount(TestSuite& suite) {
    suite.check(stepCount(1e-3, 5.0) == 5000, "stepCount(1e-3, 5) == 5000");
    suite.check(stepCount(5e-3, 5.0) == 1000, "stepCount(5e-3, 5) == 1000");
    suite.check(stepCount(1e-6, 5.0) == 5000000, "stepCount(1e-6, 5) == 5e6");
    const double nan = std::numeric_limits<double>::quiet_NaN();
    const double inf = std::numeric_limits<double>::infinity();
    suite.check(stepCountThrows(0.0, 5.0), "stepCount rechaza dt = 0");
    suite.check(stepCountThrows(-1e-3, 5.0), "stepCount rechaza dt < 0");
    suite.check(stepCountThrows(nan, 5.0), "stepCount rechaza dt NaN");
    suite.check(stepCountThrows(inf, 5.0), "stepCount rechaza dt inf");
    suite.check(stepCountThrows(3e-3, 5.0), "stepCount rechaza dt que no divide a tf");
    suite.check(stepCountThrows(10.0, 5.0), "stepCount rechaza dt > tf");
    suite.check(stepCountThrows(1e-8, 5.0), "stepCount rechaza mas de 5e7 pasos");
}

void testCli(TestSuite& suite) {
    suite.check(!rejects({"--method", "gear5", "--dt", "1e-3"}), "CLI acepta --method gear5 --dt 1e-3");
    suite.check(!rejects({"--help"}), "CLI acepta --help solo");
    const OscOptions o = parseOk({"--method", "gear5", "--dt", "1e-3"});
    suite.check(o.method == Method::Gear5 && o.dt == 1e-3 && o.tf == 5.0, "CLI parsea metodo, dt y tf por defecto");
    suite.check(parseOk({"--help"}).help, "CLI marca help");
    suite.check(rejects({"--method", "heun", "--dt", "1e-3"}), "CLI rechaza metodo desconocido");
    suite.check(rejects({"--method", "verlet", "--dt", "abc"}), "CLI rechaza dt no numerico");
    suite.check(rejects({"--method", "verlet", "--dt", "nan"}), "CLI rechaza dt nan");
    suite.check(rejects({"--method", "verlet", "--dt"}), "CLI rechaza --dt sin valor");
    suite.check(rejects({"--method", "verlet", "--dt", "1e-3", "--foo", "1"}), "CLI rechaza flag desconocido");
    suite.check(rejects({"--method", "verlet", "--dt", "1e-3", "extra"}), "CLI rechaza argumento posicional");
    suite.check(rejects({"--dt", "1e-3"}), "CLI rechaza falta de --method");
    suite.check(rejects({"--method", "verlet"}), "CLI rechaza falta de --dt");
    suite.check(rejects({"--method", "verlet", "--dt", "3e-3"}), "CLI rechaza dt que no divide a tf");
}

void testOutputFormat(TestSuite& suite) {
    for (const Method m : {Method::Verlet, Method::EulerPC}) {
        const bool fine = m == Method::EulerPC;
        OscOptions o;
        o.method = m;
        o.dt = fine ? 1e-5 : 1e-3;
        std::FILE* f = std::tmpfile();
        suite.check(f != nullptr, "tmpfile disponible");
        if (f == nullptr) return;
        const long long rows = runOscillator(o, f);
        const long long n = stepCount(o.dt, o.tf);
        suite.check(rows == n + 1, std::string("runOscillator devuelve N+1 filas: ") + methodName(m));
        std::rewind(f);
        char line[512];
        bool ok = std::fgets(line, sizeof line, f) != nullptr;
        const std::string expectHead = std::string("# TP4_OSC 1 method=") + methodName(m);
        suite.check(ok && std::string(line).rfind(expectHead, 0) == 0, "encabezado TP4_OSC 1 con metodo");
        ok = std::fgets(line, sizeof line, f) != nullptr;
        suite.check(ok && std::string(line) == "# t r v\n", "segunda linea '# t r v'");

        std::vector<double> ts, rs, vs;
        integrate(o.method, OscParams{}, o.dt, n, [&](long long step, double r, double v) {
            ts.push_back(static_cast<double>(step) * o.dt);
            rs.push_back(r);
            vs.push_back(v);
        });
        long long count = 0;
        bool exact = true;
        double lastT = 0.0;
        while (std::fgets(line, sizeof line, f) != nullptr) {
            char* end = nullptr;
            const double t = std::strtod(line, &end);
            const double r = std::strtod(end, &end);
            const double v = std::strtod(end, &end);
            const std::size_t i = static_cast<std::size_t>(count);
            if (i >= ts.size() || t != ts[i] || r != rs[i] || v != vs[i]) exact = false;
            lastT = t;
            ++count;
        }
        suite.check(count == n + 1, std::string("cantidad de filas escritas: ") + methodName(m));
        suite.check(exact, std::string("round-trip %.17g bit a bit: ") + methodName(m));
        if (fine) suite.check(std::fabs(lastT - 5.0) <= 1e-12, "t final sin deriva a dt=1e-5");
        std::fclose(f);
    }
}

}  // namespace

int main() {
    TestSuite suite;
    testSlopes(suite);
    testVelocityVerletMatchesVerlet(suite);
    testIntegrateContract(suite);
    testStepCount(suite);
    testCli(suite);
    testOutputFormat(suite);
    return suite.finish();
}
