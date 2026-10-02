#include "osc_cli.h"

#include <cerrno>
#include <cmath>
#include <cstdlib>
#include <stdexcept>
#include <string>
#include <string_view>

namespace {

double parseDouble(const char* text, const char* flag) {
    if (text == nullptr || *text == '\0') throw std::invalid_argument(std::string(flag) + ": falta valor");
    char* end = nullptr;
    errno = 0;
    const double value = std::strtod(text, &end);
    if (errno != 0 || end == text || *end != '\0' || !std::isfinite(value)) {
        throw std::invalid_argument(std::string(flag) + ": valor real invalido '" + text + "'");
    }
    return value;
}

}  // namespace

OscOptions parseOscOptions(int argc, char** argv) {
    OscOptions o;
    for (int i = 1; i < argc; ++i) {
        const std::string_view tok = argv[i];
        if (tok == "--help" || tok == "-h") {
            o.help = true;
            continue;
        }
        const bool isValueFlag = tok == "--method" || tok == "--dt" || tok == "--tf" || tok == "--out";
        if (!isValueFlag) {
            throw std::invalid_argument("argumento desconocido '" + std::string(tok) +
                                        "'; usar --help");
        }
        if (i + 1 >= argc) throw std::invalid_argument(std::string(tok) + ": falta valor");
        const char* value = argv[++i];
        if (tok == "--method") {
            o.method = parseMethod(value);
            o.methodGiven = true;
        } else if (tok == "--dt") {
            o.dt = parseDouble(value, "--dt");
            o.dtGiven = true;
        } else if (tok == "--tf") {
            o.tf = parseDouble(value, "--tf");
        } else {
            o.outPath = value;
        }
    }
    if (!o.help) {
        if (!o.methodGiven) throw std::invalid_argument("falta --method");
        if (!o.dtGiven) throw std::invalid_argument("falta --dt");
        stepCount(o.dt, o.tf);
    }
    return o;
}

void printOscUsage(std::FILE* out) {
    std::fprintf(out,
        "TP4 - Sistema 1: oscilador amortiguado (Teorica 4, p. 37)\n\n"
        "Uso:\n  ./osc --method <nombre> --dt <s> [--tf <s>] [--out <path>]\n\n"
        "Metodos:\n"
        "  eulerpc   Euler predictor-corrector (Teorica 4, diap. 23)\n"
        "  verlet    Verlet original, velocidad centrada implicita (diap. 13-15)\n"
        "  vverlet   Velocity Verlet, amortiguamiento implicito (diap. 17)\n"
        "  beeman    Beeman predictor-corrector (diap. 20)\n"
        "  gear5     Gear predictor-corrector de orden 5 (diap. 25-30)\n\n"
        "Opciones:\n"
        "  --dt <s>      paso temporal; debe dividir a tf (max 5e7 pasos)\n"
        "  --tf <s>      tiempo final (5)\n"
        "  --out <path>  escribir en un archivo (sobrescribe); por defecto stdout\n"
        "  --help, -h    esta ayuda\n\n"
        "Salida (texto, %%.17g, t = k*dt):\n"
        "  # TP4_OSC 1 method=... dt=... tf=... steps=N m=... k=... gamma=... A=...\n"
        "  # t r v\n"
        "  <t> <r> <v>     (N+1 filas)\n");
}

void writeOscHeader(std::FILE* out, Method method, const OscParams& params, double dt,
                    long long steps) {
    std::fprintf(out,
                 "# TP4_OSC 1 method=%s dt=%.17g tf=%.17g steps=%lld m=%.17g k=%.17g gamma=%.17g A=%.17g\n",
                 methodName(method), dt, params.tf, steps, params.m, params.k, params.gamma,
                 params.A);
    std::fprintf(out, "# t r v\n");
}

void writeOscRow(std::FILE* out, double t, double r, double v) {
    std::fprintf(out, "%.17g %.17g %.17g\n", t, r, v);
}

long long runOscillator(const OscOptions& options, std::FILE* out) {
    OscParams params;
    params.tf = options.tf;
    const long long n = stepCount(options.dt, options.tf);
    writeOscHeader(out, options.method, params, options.dt, n);
    const double dt = options.dt;
    // El tiempo sale de multiplicar el contador entero, nunca de sumas repetidas.
    integrate(options.method, params, dt, n, [&](long long step, double r, double v) {
        writeOscRow(out, static_cast<double>(step) * dt, r, v);
    });
    std::fflush(out);
    if (std::ferror(out)) throw std::runtime_error("error de escritura en la salida");
    return n + 1;
}
