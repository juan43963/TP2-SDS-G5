#include <cstdio>
#include <exception>
#include <stdexcept>
#include <string>

#include "osc_cli.h"

namespace {
// Duracion estatica: el buffer debe sobrevivir al FILE* hasta el fclose/exit.
char gOutBuffer[1 << 20];
}  // namespace

int main(int argc, char** argv) try {
    const OscOptions options = parseOscOptions(argc, argv);
    if (options.help) {
        printOscUsage(stdout);
        return 0;
    }
    std::FILE* out = stdout;
    if (!options.outPath.empty()) {
        out = std::fopen(options.outPath.c_str(), "w");
        if (out == nullptr) {
            throw std::runtime_error("no se pudo abrir '" + options.outPath + "' para escritura");
        }
    }
    std::setvbuf(out, gOutBuffer, _IOFBF, sizeof gOutBuffer);
    runOscillator(options, out);
    if (out != stdout && std::fclose(out) != 0) {
        throw std::runtime_error("error al cerrar '" + options.outPath + "'");
    }
    return 0;
} catch (const std::exception& e) {
    std::fprintf(stderr, "error: %s\n", e.what());
    return 1;
}
