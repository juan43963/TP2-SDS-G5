#include <cstdio>
#include <string>

#include "test_support.h"

// Sin argumentos corre todas las suites registradas; con argv[1] solo las cuyo
// nombre lo contiene.
int main(int argc, char** argv) {
    const std::string filter = argc > 1 ? argv[1] : "";
    TestSuite suite;
    int ran = 0;
    for (const NamedTest& test : testRegistry()) {
        if (!filter.empty() && std::string(test.name).find(filter) == std::string::npos) continue;
        std::printf("== %s ==\n", test.name);
        test.function(suite);
        ++ran;
    }
    if (ran == 0) {
        std::fprintf(stderr, "error: ninguna suite coincide con '%s'\n", filter.c_str());
        return 2;
    }
    return suite.finish();
}
