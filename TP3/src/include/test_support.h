#pragma once

#include <cstdio>
#include <string_view>

class TestSuite {
public:
    void check(bool condition, std::string_view description) {
        ++checks_;
        if (!condition) {
            ++failures_;
            std::printf("  [FALLA] %.*s\n", static_cast<int>(description.size()),
                        description.data());
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
