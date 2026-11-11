// Suite `options`: defaults (D-03 y enunciado), parseo de cada flag y rechazos.
#include <cmath>
#include <stdexcept>
#include <string>
#include <vector>

#include "options.h"
#include "test_support.h"

namespace {

ProgramOptions parse(const std::vector<std::string>& args) {
    std::vector<std::string> storage{"tp5"};
    storage.insert(storage.end(), args.begin(), args.end());
    std::vector<char*> argv;
    for (std::string& s : storage) argv.push_back(s.data());
    argv.push_back(nullptr);
    return parseOptions(static_cast<int>(storage.size()), argv.data());
}

// Devuelve el mensaje de std::invalid_argument, o "" si no lanzo (o lanzo otra cosa).
std::string rejection(const std::vector<std::string>& args) {
    try {
        parse(args);
    } catch (const std::invalid_argument& e) {
        return e.what();
    } catch (...) {
        return "";
    }
    return "";
}

bool contains(const std::string& text, const std::string& part) {
    return !text.empty() && text.find(part) != std::string::npos;
}

void testDefaults(TestSuite& suite) {
    const ProgramOptions o = parse({});
    const EvacuationConfig& c = o.config;
    suite.check(c.agentCount == 500, "default N = 500");
    suite.check(c.side == 50.0, "default L = 50");
    suite.check(c.doorWidth == 0.8, "default door = 0.8");
    suite.check(c.sfm.desiredSpeed == 1.5, "default vd = 1.5");
    suite.check(c.radiusMin == 0.18, "default rmin = 0.18");
    suite.check(c.radiusMax == 0.25, "default rmax = 0.25");
    suite.check(c.exitDistance == 1.0, "default exit-distance = 1");
    suite.check(c.sfm.stiffness == 1.2e5, "default k = 1.2e5");
    suite.check(c.sfm.friction == 0.0, "default kappa = 0 (sin rozamiento tangencial)");
    suite.check(c.sfm.mass == 80.0, "default mass = 80");
    suite.check(c.sfm.tau == 0.5, "default tau = 0.5");
    suite.check(c.dt == 1e-4, "default dt = 1e-4");
    suite.check(c.dt2 == 0.1, "default dt2 = 0.1");
    suite.check(c.maxTime == 3000.0, "default tmax = 3000");
    suite.check(c.seed == 1, "default seed = 1");
    suite.check(c.eventGap == 5e-3, "default event-gap = 5e-3");
    suite.check(c.steerInterval == 0.1, "default steer-dt = 0.1");
    suite.check(c.maxEvents == 1000000000LL, "default max-events = 1e9");
    suite.check(c.hybridT == 0.5, "default hybrid-T = 0.5");
    suite.check(c.hybridAlpha == 2.0, "default hybrid-alpha = 2");
    suite.check(c.returnStride == 20, "default return-stride = 20");
    suite.check(c.scheme == Scheme::Tsdmd, "default scheme = tsdmd");
    suite.check(o.writeOutput, "writeOutput verdadero por defecto");
    suite.check(!o.csv, "csv falso por defecto");
    suite.check(!o.help, "help falso por defecto");
    suite.check(!o.outputPath.empty(), "ruta de salida por defecto no vacia");
}

void testEveryFlagParses(TestSuite& suite) {
    const ProgramOptions o = parse({"--N", "120", "--L", "20", "--door", "1.2", "--seed", "42", "--dt",
                                    "5e-5", "--dt2", "0.05", "--tmax", "500", "--rmin", "0.2", "--rmax",
                                    "0.3", "--vd", "1.2", "--k", "1e5", "--kappa", "2e5", "--mass", "70",
                                    "--tau", "0.4", "--exit-distance", "1.5", "--max-placement-attempts",
                                    "5000", "--scheme", "hybrid", "--out", "build/otro.txt", "--no-output",
                                    "--csv"});
    const EvacuationConfig& c = o.config;
    suite.check(c.agentCount == 120, "--N");
    suite.check(c.side == 20.0, "--L");
    suite.check(c.doorWidth == 1.2, "--door");
    suite.check(c.seed == 42, "--seed");
    suite.check(c.dt == 5e-5, "--dt");
    suite.check(c.dt2 == 0.05, "--dt2");
    suite.check(c.maxTime == 500.0, "--tmax");
    suite.check(c.radiusMin == 0.2, "--rmin");
    suite.check(c.radiusMax == 0.3, "--rmax");
    suite.check(c.sfm.desiredSpeed == 1.2, "--vd");
    suite.check(c.sfm.stiffness == 1e5, "--k");
    suite.check(c.sfm.friction == 2e5, "--kappa");
    suite.check(c.sfm.mass == 70.0, "--mass");
    suite.check(c.sfm.tau == 0.4, "--tau");
    suite.check(c.exitDistance == 1.5, "--exit-distance");
    suite.check(c.maxPlacementAttemptsPerAgent == 5000, "--max-placement-attempts");
    suite.check(c.scheme == Scheme::Hybrid, "--scheme hybrid");
    suite.check(o.outputPath == "build/otro.txt", "--out");
    suite.check(!o.writeOutput, "--no-output");
    suite.check(o.csv, "--csv");

    {
        const EvacuationConfig e = parse({"--event-gap", "0.01", "--steer-dt",
                                          "0.25", "--max-events", "5000000000"})
                                       .config;
        suite.check(e.eventGap == 0.01, "--event-gap");
        suite.check(e.steerInterval == 0.25, "--steer-dt");
        suite.check(e.maxEvents == 5000000000LL, "--max-events (long long)");
    }

    suite.check(parse({"--hybrid-T", "1.25"}).config.hybridT == 1.25, "--hybrid-T");
    suite.check(parse({"--hybrid-alpha", "3"}).config.hybridAlpha == 3.0, "--hybrid-alpha");
    suite.check(parse({"--return-stride", "5"}).config.returnStride == 5, "--return-stride");
    suite.check(parse({"--scheme", "edmd"}).config.scheme == Scheme::Edmd, "--scheme edmd");
    suite.check(parse({"--scheme", "tsdmd"}).config.scheme == Scheme::Tsdmd, "--scheme tsdmd");
    suite.check(parse({"--help"}).help, "--help");
    suite.check(parse({"-h"}).help, "-h");
}

void testRejections(TestSuite& suite) {
    suite.check(contains(rejection({"--return-stride", "0"}), "--return-stride"), "return-stride = 0 rechazado");
    suite.check(contains(rejection({"--N", "0"}), "--N"), "N = 0 rechazado");
    suite.check(contains(rejection({"--N", "100001"}), "--N"), "N = 100001 rechazado");
    suite.check(contains(rejection({"--dt2", "0.00015"}), "--dt2"), "dt2 no multiplo de dt rechazado (D-04)");
    suite.check(contains(rejection({"--dt2", "0.00005"}), "--dt2"), "dt2 menor que dt rechazado");
    suite.check(contains(rejection({"--dt", "0.005"}), "--dt"), "dt sobre la cota de estabilidad rechazado");
    suite.check(contains(rejection({"--tmax", "1e6"}), "--tmax"), "tmax con mas de 2e9 pasos rechazado");
    suite.check(contains(rejection({"--rmin", "0.3", "--rmax", "0.2"}), "--rmax"), "rmin > rmax rechazado");
    suite.check(contains(rejection({"--door", "60"}), "--door"), "puerta mayor que L rechazada");
    suite.check(contains(rejection({"--L", "0.4"}), "--door"), "L = 0.4 rechazado (la puerta no entra)");
    suite.check(contains(rejection({"--L", "0.4", "--door", "0.1"}), "--rmax"),
                "L = 0.4 con puerta chica rechazado (2*rmax no entra)");
    suite.check(contains(rejection({"--N", "abc"}), "--N"), "valor no numerico rechazado");
    suite.check(contains(rejection({"--dt", "1e-4x"}), "--dt"), "valor con basura al final rechazado");
    suite.check(contains(rejection({"--N"}), "--N"), "flag sin valor rechazado");
    suite.check(contains(rejection({"--no-existe", "3"}), "--no-existe"), "flag desconocido rechazado");
    suite.check(contains(rejection({"suelto"}), "posicional"), "argumento posicional rechazado");
    suite.check(contains(rejection({"--scheme", "foo"}), "--scheme"), "esquema desconocido rechazado");
    suite.check(contains(rejection({"--seed", "-3"}), "--seed"), "semilla negativa rechazada");
    suite.check(contains(rejection({"--out", ""}), "--out"), "--out vacio con salida activa rechazado");
    suite.check(rejection({"--out", "", "--no-output"}).empty(), "--out vacio con --no-output es valido");
    suite.check(contains(rejection({"--mass", "0"}), "--mass"), "masa cero rechazada");
    suite.check(contains(rejection({"--max-placement-attempts", "0"}), "--max-placement-attempts"),
                "max-placement-attempts cero rechazado");
    suite.check(contains(rejection({"--event-gap", "0"}), "--event-gap"), "event-gap 0 rechazado");
    suite.check(contains(rejection({"--event-gap", "1e-7"}), "--event-gap"), "event-gap 1e-7 rechazado");
    suite.check(contains(rejection({"--event-gap", "0.5"}), "--event-gap"), "event-gap 0.5 rechazado");
    suite.check(contains(rejection({"--steer-dt", "0"}), "--steer-dt"), "steer-dt 0 rechazado");
    suite.check(contains(rejection({"--max-events", "0"}), "--max-events"), "max-events 0 rechazado");
    suite.check(contains(rejection({"--max-events", "abc"}), "--max-events"), "max-events no numerico rechazado");
    suite.check(contains(rejection({"--hybrid-T", "-1"}), "--hybrid-T"), "hybrid-T negativo rechazado");
    suite.check(contains(rejection({"--hybrid-T", "1e-5"}), "--hybrid-T"), "hybrid-T entre 0 y 2*dt rechazado");
    suite.check(contains(rejection({"--hybrid-alpha", "0.5"}), "--hybrid-alpha"), "hybrid-alpha < 1 rechazado");
    suite.check(rejection({"--hybrid-T", "0"}).empty(), "hybrid-T 0 (EDMD puro) aceptado");
    suite.check(rejection({"--hybrid-T", "1e9"}).empty(), "hybrid-T 1e9 (TSDMD puro) aceptado");
}

void testHelpSkipsValidation(TestSuite& suite) {
    bool threw = false;
    bool help = false;
    try {
        help = parse({"--help", "--N", "0"}).help;
    } catch (...) {
        threw = true;
    }
    suite.check(!threw, "--help no lanza aunque otro valor sea invalido");
    suite.check(help, "--help devuelve help == true");
}

void runOptionsTests(TestSuite& suite) {
    testDefaults(suite);
    testEveryFlagParses(suite);
    testRejections(suite);
    testHelpSkipsValidation(suite);
}

const TestRegistration registration("options", runOptionsTests);

}  // namespace
