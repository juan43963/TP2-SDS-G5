#include <cstdio>
#include <exception>

#include "billiard_cli.h"

// Unica frontera de errores del binario: cualquier excepcion termina en una
// linea "error:" por stderr y codigo 1.
int main(int argc, char** argv) try {
    const BilliardOptions options = parseBilliardOptions(argc, argv);
    if (options.help) {
        printBilliardUsage(stdout);
        return 0;
    }
    runBilliard(options, stdout);
    return 0;
} catch (const std::exception& e) {
    std::fprintf(stderr, "error: %s\n", e.what());
    return 1;
}
