#pragma once

// TestSuite adaptado de TP3/src/include/test_support.h (D-09) mas un registro
// estatico: cada archivo de suite declara un TestRegistration de ambito de
// archivo y selftest.cpp las ejecuta sin necesidad de editarlo.
#include <cstdio>
#include <string_view>
#include <vector>

class TestSuite {
public:
    void check(bool condition, std::string_view description) {
        ++checks_;
        if (!condition) {
            ++failures_;
            std::printf("  [FALLA] %.*s\n", static_cast<int>(description.size()), description.data());
        }
    }

    int finish() const {
        std::printf("%d verificaciones, %d fallas\n", checks_, failures_);
        if (failures_ == 0) {
            std::puts("OK");
            return 0;
        }
        return 1;
    }

private:
    int checks_ = 0;
    int failures_ = 0;
};

using TestFunction = void (*)(TestSuite&);

struct NamedTest {
    const char* name;
    TestFunction function;
};

inline std::vector<NamedTest>& testRegistry() {
    static std::vector<NamedTest> registry;
    return registry;
}

struct TestRegistration {
    TestRegistration(const char* name, TestFunction function) {
        testRegistry().push_back({name, function});
    }
};
