#pragma once

#include <cstdio>
#include <string>
#include <vector>

#include "sfm.h"

// Escritor en streaming del formato TP5_TRAJECTORY 1 (D-12). Un archivo sin la
// linea END final esta truncado.
class TrajectoryWriter {
public:
    TrajectoryWriter(const std::string& path, const EvacuationConfig& config);
    ~TrajectoryWriter();
    TrajectoryWriter(const TrajectoryWriter&) = delete;
    TrajectoryWriter& operator=(const TrajectoryWriter&) = delete;

    void writeFrame(double time, const std::vector<Agent>& agents);
    void finish();

private:
    std::FILE* file_ = nullptr;
    std::vector<char> buffer_;
    std::string path_;
};
