#include "billiard_cli.h"

#include <cerrno>
#include <climits>
#include <cmath>
#include <cstdlib>
#include <cstdint>
#include <filesystem>
#include <memory>
#include <stdexcept>
#include <string>
#include <string_view>
#include <system_error>
#include <vector>

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

long long parseLongLong(const char* text, const char* flag) {
    if (text == nullptr || *text == '\0') throw std::invalid_argument(std::string(flag) + ": falta valor");
    char* end = nullptr;
    errno = 0;
    const long long value = std::strtoll(text, &end, 10);
    if (errno != 0 || end == text || *end != '\0') {
        throw std::invalid_argument(std::string(flag) + ": entero invalido '" + text + "'");
    }
    return value;
}

std::uint64_t parseUint64(const char* text, const char* flag) {
    if (text == nullptr || *text == '\0') throw std::invalid_argument(std::string(flag) + ": falta valor");
    // strtoull acepta un '-' inicial y lo envuelve: se rechaza a mano.
    if (*text == '-' || *text == ' ' || *text == '\t') {
        throw std::invalid_argument(std::string(flag) + ": entero sin signo invalido '" + text + "'");
    }
    char* end = nullptr;
    errno = 0;
    const unsigned long long value = std::strtoull(text, &end, 10);
    if (errno != 0 || end == text || *end != '\0') {
        throw std::invalid_argument(std::string(flag) + ": entero sin signo invalido '" + text + "'");
    }
    return static_cast<std::uint64_t>(value);
}

int parseInt(const char* text, const char* flag) {
    const long long value = parseLongLong(text, flag);
    if (value < INT_MIN || value > INT_MAX) {
        throw std::invalid_argument(std::string(flag) + ": fuera de rango '" + text + "'");
    }
    return static_cast<int>(value);
}

bool isValueFlag(std::string_view tok) {
    static constexpr std::string_view kFlags[] = {
        "--N",     "--x0", "--dt",     "--every",  "--tf",     "--seed",   "--R",
        "--radius", "--mass", "--k",    "--v0",     "--init",   "--frames", "--conversions", "--summary"};
    for (const std::string_view f : kFlags) {
        if (tok == f) return true;
    }
    return false;
}

void createParentDirectory(const std::string& path) {
    const std::filesystem::path parent = std::filesystem::path(path).parent_path();
    if (parent.empty()) return;
    std::error_code ec;
    std::filesystem::create_directories(parent, ec);
    if (ec) {
        throw std::runtime_error("no se pudo crear el directorio '" + parent.string() +
                                 "': " + ec.message());
    }
}

// Archivo de salida con buffer de 1 MiB. El buffer se declara antes que el
// FILE* para que sobreviva a su fclose.
class OutFile {
public:
    explicit OutFile(const std::string& path) : buffer_(1 << 20), path_(path) {
        createParentDirectory(path);
        fp_ = std::fopen(path.c_str(), "w");
        if (fp_ == nullptr) {
            throw std::runtime_error("no se pudo abrir '" + path + "' para escritura");
        }
        std::setvbuf(fp_, buffer_.data(), _IOFBF, buffer_.size());
    }
    OutFile(const OutFile&) = delete;
    OutFile& operator=(const OutFile&) = delete;
    ~OutFile() {
        if (fp_ != nullptr) std::fclose(fp_);
    }

    std::FILE* get() const { return fp_; }

    void close() {
        if (fp_ == nullptr) return;
        const bool writeFailed = std::ferror(fp_) != 0;
        const int rc = std::fclose(fp_);
        fp_ = nullptr;
        if (writeFailed || rc != 0) {
            throw std::runtime_error("error de escritura en '" + path_ + "'");
        }
    }

private:
    std::vector<char> buffer_;
    std::string path_;
    std::FILE* fp_ = nullptr;
};

class FrameWriter {
public:
    FrameWriter(const std::string& path, const BilliardParams& p, const std::string& init)
        : file_(path) {
        std::fprintf(file_.get(), "# TP4_FRAMES 1 ");
        writeParamFields(file_.get(), p, init);
        std::fprintf(file_.get(), "\n");
        std::fprintf(file_.get(),
                     "# FRAME <k> <t>, luego N filas: x y vx vy estado (0 = fresca, 1 = usada)\n");
    }

    void writeFrame(long long step, double t, const std::vector<Vec2>& pos,
                    const std::vector<Vec2>& vel, const std::vector<unsigned char>& used) {
        std::fprintf(file_.get(), "FRAME %lld %.17g\n", step, t);
        for (std::size_t i = 0; i < pos.size(); ++i) {
            std::fprintf(file_.get(), "%.17g %.17g %.17g %.17g %d\n", pos[i].x, pos[i].y, vel[i].x,
                         vel[i].y, static_cast<int>(used[i]));
        }
        ++frames_;
    }

    void finish(const SimulationResult& r) {
        std::fprintf(file_.get(), "# END frames=%lld final_step=%lld final_time=%.17g\n", frames_,
                     r.finalStep, r.finalTime);
        file_.close();
    }

private:
    OutFile file_;
    long long frames_ = 0;
};

class ConversionLogWriter {
public:
    ConversionLogWriter(const std::string& path, const BilliardParams& p, const std::string& init)
        : file_(path) {
        std::fprintf(file_.get(), "# TP4_CONVERSIONS 1 ");
        writeParamFields(file_.get(), p, init);
        std::fprintf(file_.get(), "\n");
        std::fprintf(file_.get(), "# t id\n");
    }

    void writeRow(double t, int id) { std::fprintf(file_.get(), "%.17g %d\n", t, id); }

    void finish(const SimulationResult& r) {
        std::fprintf(file_.get(), "# END used=%d final_step=%lld final_time=%.17g stop=%s\n",
                     r.usedCount, r.finalStep, r.finalTime, stopReasonName(r.stop));
        file_.close();
    }

private:
    OutFile file_;
};

}  // namespace

BilliardOptions parseBilliardOptions(int argc, char** argv) {
    BilliardOptions o;
    BilliardParams& p = o.params;
    bool x0Given = false;
    for (int i = 1; i < argc; ++i) {
        const std::string_view tok = argv[i];
        if (tok == "--help" || tok == "-h") {
            o.help = true;
            continue;
        }
        if (tok == "--no-obstacles") {
            p.obstacles = false;
            continue;
        }
        if (tok == "--no-trajectory") {
            o.trajectory = false;
            continue;
        }
        if (tok == "--stop-when-all-used") {
            p.stopWhenAllUsed = true;
            continue;
        }
        if (tok == "--stop-at-t90") {
            p.stopAtT90 = true;
            continue;
        }
        if (!isValueFlag(tok)) {
            throw std::invalid_argument("argumento desconocido '" + std::string(tok) +
                                        "'; usar --help");
        }
        if (i + 1 >= argc) throw std::invalid_argument(std::string(tok) + ": falta valor");
        const char* value = argv[++i];
        const std::string flag(tok);
        if (tok == "--N") {
            p.N = parseInt(value, flag.c_str());
        } else if (tok == "--x0") {
            p.x0 = parseDouble(value, flag.c_str());
            x0Given = true;
        } else if (tok == "--dt") {
            p.dt = parseDouble(value, flag.c_str());
        } else if (tok == "--every") {
            p.every = parseLongLong(value, flag.c_str());
        } else if (tok == "--tf") {
            p.tf = parseDouble(value, flag.c_str());
        } else if (tok == "--seed") {
            p.seed = parseUint64(value, flag.c_str());
        } else if (tok == "--R") {
            p.R = parseDouble(value, flag.c_str());
        } else if (tok == "--radius") {
            p.radius = parseDouble(value, flag.c_str());
        } else if (tok == "--mass") {
            p.mass = parseDouble(value, flag.c_str());
        } else if (tok == "--k") {
            p.k = parseDouble(value, flag.c_str());
        } else if (tok == "--v0") {
            p.v0 = parseDouble(value, flag.c_str());
        } else if (tok == "--init") {
            p.init = parseInitMethod(value);
        } else if (tok == "--frames") {
            o.framesPath = value;
        } else if (tok == "--conversions") {
            o.conversionsPath = value;
        } else {
            o.summaryPath = value;
        }
    }
    if (!x0Given) p.x0 = p.radius;

    if (!o.help) {
        validateParams(p);
        const long long steps = billiardStepCount(p);
        if (o.trajectory) {
            const long long frames = steps / p.every + 1;
            if (frames * static_cast<long long>(p.N) > kMaxFrameRows) {
                throw std::invalid_argument("la trayectoria tendria " +
                                            std::to_string(frames * static_cast<long long>(p.N)) +
                                            " filas (> " + std::to_string(kMaxFrameRows) +
                                            "); usar un --every mayor o --no-trajectory");
            }
        }
        if (o.framesPath == o.conversionsPath) {
            throw std::invalid_argument("--frames y --conversions apuntan a la misma ruta '" +
                                        o.framesPath + "'");
        }
        if (!o.summaryPath.empty() &&
            (o.summaryPath == o.framesPath || o.summaryPath == o.conversionsPath)) {
            throw std::invalid_argument("--summary repite otra ruta de salida '" + o.summaryPath +
                                        "'");
        }
    }
    return o;
}

void printBilliardUsage(std::FILE* out) {
    std::fprintf(out,
        "TP4 - Sistema 2: billar circular, Verlet original + Cell Index Method\n\n"
        "Uso:\n  ./billiard [opciones]\n\n"
        "Sistema (valores del enunciado):\n"
        "  --R <m>        radio del billar (0.51)\n"
        "  --radius <m>   radio de cada particula y obstaculo (0.0175)\n"
        "  --mass <kg>    masa de cada particula (0.025)\n"
        "  --k <N/m>      constante del resorte de contacto (1e4)\n"
        "  --v0 <m/s>     rapidez inicial (1)\n\n"
        "Corrida:\n"
        "  --N <n>        cantidad de particulas, >= 1 (100)\n"
        "  --x0 <m>       obstaculos en (+-x0, 0), x0 en [radius, R - radius] (radius)\n"
        "  --no-obstacles sin obstaculos (no se puede combinar con cortes tempranos)\n"
        "  --dt <s>       paso temporal; debe dividir a tf (1e-4)\n"
        "  --tf <s>       tiempo final (10)\n"
        "  --every <n>    escribir un frame cada n pasos, dt2 = every*dt (100)\n"
        "  --seed <n>     semilla del generador (1)\n"
        "  --init <modo>  condicion inicial: rsa | lattice | auto (auto)\n"
        "                   rsa      rejection sampling; falla (sin caer a la red) si se satura\n"
        "                            (cerca de N = 440)\n"
        "                   lattice  red triangular con gap de 1 mm y jitter < 0.5 mm; capacidad\n"
        "                            ~666 sitios en x0 = radius (N mayor: error 'capacidad')\n"
        "                   auto     rsa si N <= 400, red si N > 400 (o si rsa se satura)\n"
        "                 init= en cada encabezado y resumen registra el metodo realmente usado.\n"
        "                 Los tiempos 2.1b/2.4a usan --init lattice para todo N.\n\n"
        "Modos de barrido:\n"
        "  --no-trajectory        no escribe frames; si escribe el log de conversiones y el resumen\n"
        "  --stop-when-all-used   corta en el paso en que Nu = N (stop=all_used)\n"
        "  --stop-at-t90          corta en el paso en que Nu >= (9N + 9)/10 (stop=t90)\n"
        "  Los cortes tempranos son solo para los barridos 2.2/2.4b; nunca se usan en los\n"
        "  tiempos de 2.1b, que necesitan el tf fijo. Sin cortes, stop=tf.\n\n"
        "Salidas (texto, %%.17g, t = k*dt):\n"
        "  --frames <path>       trayectoria (data/billiard/frames.txt)\n"
        "  --conversions <path>  log de conversiones, siempre se escribe\n"
        "                        (data/billiard/conversions.txt)\n"
        "  --summary <path>      ademas de stdout, guarda la linea TP4_SUMMARY\n"
        "  --help, -h            esta ayuda\n\n"
        "Formatos:\n"
        "  frames:       # TP4_FRAMES 1 <parametros>, luego por cada frame\n"
        "                FRAME <k> <t> y N filas 'x y vx vy estado' (0 fresca, 1 usada),\n"
        "                y el cierre '# END frames=... final_step=... final_time=...'\n"
        "  conversiones: # TP4_CONVERSIONS 1 <parametros>, filas '<t> <id>' y\n"
        "                '# END used=... final_step=... final_time=... stop=...'\n"
        "  stdout:       una linea 'TP4_SUMMARY 1 <parametros> final_step=... final_time=...\n"
        "                used=... stop=... simulation_ms=... frame_io_ms=...'\n");
}

void writeParamFields(std::FILE* out, const BilliardParams& p, const std::string& initMethod) {
    std::fprintf(out,
                 "N=%d R=%.17g radius=%.17g mass=%.17g k=%.17g v0=%.17g obstacles=%d x0=%.17g "
                 "dt=%.17g tf=%.17g every=%lld max_steps=%lld seed=%llu stop_when_all_used=%d stop_at_t90=%d init=%s",
                 p.N, p.R, p.radius, p.mass, p.k, p.v0, p.obstacles ? 1 : 0, p.x0, p.dt, p.tf,
                 p.every, billiardStepCount(p), static_cast<unsigned long long>(p.seed), p.stopWhenAllUsed ? 1 : 0,
                 p.stopAtT90 ? 1 : 0, initMethod.c_str());
}

void writeSummaryLine(std::FILE* out, const BilliardParams& p, const std::string& initMethod,
                      const SimulationResult& r) {
    std::fprintf(out, "TP4_SUMMARY 1 ");
    writeParamFields(out, p, initMethod);
    std::fprintf(out,
                 " final_step=%lld final_time=%.17g used=%d stop=%s simulation_ms=%.17g frame_io_ms=%.17g\n",
                 r.finalStep, r.finalTime, r.usedCount, stopReasonName(r.stop), r.simulationMs,
                 r.frameIoMs);
}

SimulationResult runBilliard(const BilliardOptions& options, std::FILE* summaryOut) {
    const BilliardParams& p = options.params;
    const InitialState state = generateInitialState(p);

    ConversionLogWriter conversionLog(options.conversionsPath, p, state.method);
    std::unique_ptr<FrameWriter> frameLog;
    if (options.trajectory) frameLog = std::make_unique<FrameWriter>(options.framesPath, p, state.method);

    FrameSink frameSink;
    if (frameLog) {
        frameSink = [&](long long step, double t, const std::vector<Vec2>& pos,
                        const std::vector<Vec2>& vel, const std::vector<unsigned char>& used) {
            frameLog->writeFrame(step, t, pos, vel, used);
        };
    }
    const ConversionSink conversionSink = [&](long long, double t, int id) {
        conversionLog.writeRow(t, id);
    };

    const SimulationResult result = simulate(p, state, frameSink, conversionSink);

    conversionLog.finish(result);
    if (frameLog) frameLog->finish(result);

    writeSummaryLine(summaryOut, p, state.method, result);
    if (!options.summaryPath.empty()) {
        OutFile summaryFile(options.summaryPath);
        writeSummaryLine(summaryFile.get(), p, state.method, result);
        summaryFile.close();
    }
    return result;
}
