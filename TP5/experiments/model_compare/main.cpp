#include "model_compare.h"

#include <bit>
#include <charconv>
#include <cmath>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <memory>
#include <sstream>
#include <stdexcept>
#include <string>

namespace mc = model_compare;

namespace {

struct Population { double time; int inRoom; int notYetCrossed; int active; };

template <class T> T integer(const std::string& value) {
    T out{};
    const auto [last, ec] = std::from_chars(value.data(), value.data() + value.size(), out);
    if (ec != std::errc{} || last != value.data() + value.size())
        throw std::invalid_argument("entero invalido: " + value);
    return out;
}

double number(const std::string& value) {
    std::size_t last = 0;
    const double out = std::stod(value, &last);
    if (last != value.size() || !std::isfinite(out))
        throw std::invalid_argument("numero invalido: " + value);
    return out;
}

std::string centersHash(const std::vector<Agent>& agents) {
    std::uint64_t hash = UINT64_C(14695981039346656037);
    for (const Agent& a : agents) {
        for (double x : {a.position.x, a.position.y}) {
            hash ^= std::bit_cast<std::uint64_t>(x);
            hash *= UINT64_C(1099511628211);
        }
    }
    std::ostringstream out;
    out << std::hex << hash;
    return out.str();
}

void jsonNumber(std::ostream& out, bool available, double value) {
    if (available) out << value;
    else out << "null";
}

std::string report(const mc::Config& c, const EvacuationResult& r,
                   const mc::Diagnostics& d, const std::string& hash,
                   const Population& last, long long exitingInsideSamples) {
    const auto& s = c.scenario;
    const bool cpm = c.model == mc::Model::Cpm;
    const bool valid = r.wallBreaches == 0;
    std::ostringstream out;
    out << std::setprecision(17) << "{\"model\":\"" << (cpm ? "cpm" : "sfm")
        << "\",\"scheme\":\"tsdmd\",\"N\":" << s.agentCount << ",\"L\":" << s.side
        << ",\"door\":" << s.doorWidth << ",\"seed\":" << s.seed
        << ",\"tmax\":" << s.maxTime << ",\"dt\":" << (cpm ? c.cpm.timeStep() : s.dt)
        << ",\"dt2\":" << s.dt2 << ",\"vd\":" << (cpm ? c.cpm.desiredSpeed : s.sfm.desiredSpeed)
        << ",\"exit_distance\":" << s.exitDistance
        << ",\"radius_min\":" << (cpm ? c.cpm.radiusMin : s.radiusMin)
        << ",\"radius_max\":" << (cpm ? c.cpm.radiusMax : s.radiusMax)
        << ",\"tau\":" << (cpm ? c.cpm.recoveryTime : s.sfm.tau)
        << ",\"beta\":";
    jsonNumber(out, cpm, c.cpm.beta);
    out << ",\"escape_speed\":";
    jsonNumber(out, cpm, c.cpm.escapeSpeed);
    out << ",\"mass\":";
    jsonNumber(out, !cpm, s.sfm.mass);
    out << ",\"k\":";
    jsonNumber(out, !cpm, s.sfm.stiffness);
    out << ",\"kappa\":";
    jsonNumber(out, !cpm, s.sfm.friction);
    out << ",\"initial_speed\":0,\"initial_centers_hash\":\"" << hash
        << "\",\"steps\":" << r.steps << ",\"t_final\":" << r.finalTime
        << ",\"completed\":" << (r.completed ? "true" : "false")
        << ",\"valid\":" << (valid ? "true" : "false") << ",\"status\":\""
        << (!valid ? "invalid" : (r.completed ? "complete" : "censored"))
        << "\",\"t_evac\":";
    // No confundir el ultimo cruce observado con la evacuacion de todos.
    jsonNumber(out, r.crossed == s.agentCount, r.evacuationTime);
    out << ",\"t_clear\":";
    jsonNumber(out, r.completed, r.clearTime);
    out << ",\"last_cross_observed\":";
    jsonNumber(out, r.crossed > 0, r.evacuationTime);
    out << ",\"crossed\":" << r.crossed << ",\"removed\":" << r.removed
        << ",\"in_room_final\":" << last.inRoom
        << ",\"not_yet_crossed_final\":" << r.inRoomFinal
        << ",\"exiting_inside_samples\":" << exitingInsideSamples
        << ",\"wall_breaches\":" << r.wallBreaches
        << ",\"max_agent_overlap\":" << r.maxAgentOverlap
        << ",\"max_wall_overlap\":" << r.maxWallOverlap
        << ",\"simulation_ms\":" << r.simulationMs << ",\"output_ms\":" << r.outputMs
        << ",\"pair_contact_steps\":";
    if (cpm) out << d.pairContacts; else out << "null";
    out << ",\"wall_contact_steps\":";
    if (cpm) out << d.wallContacts; else out << "null";
    out << ",\"zero_escape_directions\":";
    if (cpm) out << d.zeroEscapeDirections; else out << "null";
    out << '}';
    return out.str();
}

}  // namespace

int main(int argc, char** argv) try {
    mc::Config c;
    bool hasModel = false, trajectory = false;
    std::filesystem::path output;
    for (int i = 1; i < argc; ++i) {
        const std::string flag = argv[i];
        if (flag == "--help" || flag == "-h") {
            std::cout << "tp5_model_compare --model sfm|cpm [--N 500] [--L 50] [--door 0.8]\n"
                         "  [--seed 1] [--tmax 3000] [--out DIR] [--trajectory]\n"
                         "SFM: dt=0.0001 s; CPM: dt derivado (1/30 s). dt2=0.5 s.\n"
                         "Sin --out solo emite JSON. --trajectory requiere --out.\n";
            return 0;
        }
        if (flag == "--trajectory") { trajectory = true; continue; }
        if (i + 1 == argc) throw std::invalid_argument("falta valor para " + flag);
        const std::string value = argv[++i];
        if (flag == "--model") {
            if (value != "sfm" && value != "cpm") throw std::invalid_argument("modelo invalido");
            c.model = value == "cpm" ? mc::Model::Cpm : mc::Model::Sfm;
            hasModel = true;
        } else if (flag == "--N") c.scenario.agentCount = integer<int>(value);
        else if (flag == "--L") c.scenario.side = number(value);
        else if (flag == "--door") c.scenario.doorWidth = number(value);
        else if (flag == "--seed") c.scenario.seed = integer<std::uint64_t>(value);
        else if (flag == "--tmax") c.scenario.maxTime = number(value);
        else if (flag == "--out") output = value;
        else throw std::invalid_argument("opcion desconocida: " + flag);
    }
    if (!hasModel) throw std::invalid_argument("se requiere --model sfm|cpm");
    if (trajectory && output.empty()) throw std::invalid_argument("--trajectory requiere --out");
    mc::validate(c);
    auto agents = mc::initialState(c);
    mc::validateState(agents);
    const std::string hash = centersHash(agents);
    const char* model = c.model == mc::Model::Cpm ? "cpm" : "sfm";
    const double dt = c.model == mc::Model::Cpm ? c.cpm.timeStep() : c.scenario.dt;
    std::unique_ptr<std::ofstream> trace;
    if (!output.empty()) {
        std::filesystem::create_directories(output);
        if (std::filesystem::exists(output / "run.json"))
            throw std::runtime_error("la salida ya contiene run.json; elegir otro directorio");
        if (trajectory) {
            trace = std::make_unique<std::ofstream>(output / "trajectory.txt");
            trace->exceptions(std::ios::failbit | std::ios::badbit);
            *trace << std::setprecision(17) << "TP5_TRAJECTORY 1\nmodel " << model
                   << "\nscheme tsdmd\nN " << c.scenario.agentCount << "\nL " << c.scenario.side
                   << "\nd " << c.scenario.doorWidth << "\ndoor_x " << c.scenario.side / 2.0
                   << "\nexit_distance " << c.scenario.exitDistance << "\nseed " << c.scenario.seed
                   << "\ndt " << dt << "\ndt2 " << c.scenario.dt2
                   << "\nCOLUMNS id x y vx vy r scheme\n";
        }
    }
    std::vector<Population> population;
    long long exitingInsideSamples = 0;
    const FrameSink sink = [&](double t, const std::vector<Agent>& frame) {
        mc::validateState(frame);
        int inRoom = 0, notYetCrossed = 0;
        for (const Agent& a : frame) {
            if (a.position.y >= 0.0) {
                ++inRoom;
                if (a.status == AgentStatus::Exiting) ++exitingInsideSamples;
            }
            if (a.status == AgentStatus::InRoom) ++notYetCrossed;
        }
        population.push_back({t, inRoom, notYetCrossed, static_cast<int>(frame.size())});
        if (trace) {
            *trace << "FRAME " << t << ' ' << frame.size() << '\n';
            for (const Agent& a : frame) {
                *trace << a.id << ' ' << a.position.x << ' ' << a.position.y << ' '
                       << a.velocity.x << ' ' << a.velocity.y << ' ' << a.radius << " 0\n";
            }
        }
    };
    mc::Diagnostics diagnostics;
    const auto result = c.model == mc::Model::Cpm ?
        mc::runCpm(c, std::move(agents), diagnostics, sink) :
        runEvacuation(c.scenario, std::move(agents), sink);
    if (trace) { *trace << "END\n"; trace->close(); }
    const std::string json = report(c, result, diagnostics, hash, population.back(), exitingInsideSamples);
    if (!output.empty()) {
        std::ofstream pop(output / "population.csv");
        pop.exceptions(std::ios::failbit | std::ios::badbit);
        pop << std::setprecision(17) << "t,in_room,not_yet_crossed,active\n";
        for (const auto& point : population)
            pop << point.time << ',' << point.inRoom << ',' << point.notYetCrossed << ',' << point.active << '\n';
        pop.close();
        std::ofstream summary(output / "run.json.tmp");
        summary.exceptions(std::ios::failbit | std::ios::badbit);
        summary << json << '\n';
        summary.close();
        std::filesystem::rename(output / "run.json.tmp", output / "run.json");
    }
    std::cout << json << '\n';
    return result.wallBreaches == 0 ? 0 : 2;
} catch (const std::exception& e) {
    std::cerr << "error: " << e.what() << '\n';
    return 1;
}
