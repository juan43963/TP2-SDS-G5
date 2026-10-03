"""Genera las animaciones y los fotogramas de la presentacion (DEL-02).

Para cada caso de `CASES` corre el motor congelado `ejercicio2/billiard` (texto
plano en `ejercicio2/data/animation/`), y con ese texto el animador independiente
`ejercicio2/python/animate.py` escribe un MP4 H.264 (`animaciones/<id>.mp4`) y un
PNG representativo (`frames/<id>.png`). Nada se anima desde el estado en memoria
de la simulacion: el animador solo lee los archivos de texto.

Los MP4 NO se versionan ni se entregan (el enunciado prohibe mandar animaciones):
estan en `presentacion/.gitignore` y se suben a YouTube/Vimeo, cuyo link va como
texto en el PDF (ver `links.py`). Los PNG, el manifiesto y las semillas si se
versionan.

Etapas (`--stage`): `sim` solo corre el motor (por ejemplo en WSL); `render` solo
renderiza desde los frames ya escritos (por ejemplo en Windows con `py -3.14`);
`all` hace las dos. La semilla de cada caso con obstaculos es la de t90 mas
cercano a la media de las semillas 1 a 10 (`--pick-seeds`).

    python3 presentacion/make_animations.py --pick-seeds
    python3 presentacion/make_animations.py --force
    python3 presentacion/make_animations.py --verify
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path

PRES_DIR = Path(__file__).resolve().parent
TP4_DIR = PRES_DIR.parent
sys.path.insert(0, str(TP4_DIR / "ejercicio2" / "python"))

import numpy as np  # noqa: E402
from matplotlib.colors import to_rgb  # noqa: E402
from PIL import Image  # noqa: E402

import animate  # noqa: E402
import dt_star  # noqa: E402
import engine  # noqa: E402
import study_density  # noqa: E402
import tp4io  # noqa: E402

VIDEO_DIR = PRES_DIR / "animaciones"
FRAMES_DIR = PRES_DIR / "frames"
DATA_ROOT = engine.DATA_ROOT
BINARY = engine.BINARY

STUDY = "animation"
PICK_STUDY = "animation_pick"
N = 100
INIT = "rsa"
DEFAULT_SEED = 1
PICK_SEEDS = tuple(range(1, 11))
PICK_TMAX = 100.0
COLOR_TOL = 12
MIN_COLOR_PIXELS = 150
PNG_SIZE = (800, 800)
MIN_MP4_BYTES = 100 * 1024
MAX_MP4_BYTES = 200 * 1024 * 1024
DURATION_TOL_S = 0.5
SEED_RULE = "t90 mas cercano a la media de las semillas 1 a 10"

# Tres posiciones tipicas de 2.2 (Fase 5, typical_source = auto) y el caso sin
# obstaculos de 2.3. Reloj en tiempo real (fps = 1 / dt2) salvo sin obstaculos, que
# va a la mitad de velocidad para que la relajacion de 0.34 s dure unos 17 s.
CASES = {
    "x0_central": dict(title="Billar con obstáculos, x0 = 0.20 m", obstacles=True, x0=0.20,
                       tf=40.0, dt2=0.04, fps=25, png_rule="fu_half"),
    "x0_r": dict(title="Billar con obstáculos, x0 = 0.0175 m (x0 = r)", obstacles=True,
                 x0=0.0175, tf=40.0, dt2=0.04, fps=25, png_rule="fu_half"),
    "x0_Rmr": dict(title="Billar con obstáculos, x0 = 0.4925 m (x0 = R - r)", obstacles=True,
                   x0=0.4925, tf=40.0, dt2=0.04, fps=25, png_rule="fu_half"),
    "sin_obstaculos": dict(title="Billar sin obstáculos", obstacles=False, x0=None,
                           tf=10.0, dt2=0.02, fps=25, png_rule=2.0),
}

SEEDS_PATH = VIDEO_DIR / "seeds.json"
MANIFEST_PATH = VIDEO_DIR / "manifest.json"


class AnimationError(RuntimeError):
    """Falla esperable del flujo (el CLI la muestra como `error: ...`)."""


# --------------------------------------------------------------------------- semillas


def load_seeds(path=None) -> dict:
    """Semilla por caso: la de seeds.json si existe, y `DEFAULT_SEED` si no."""
    seeds = {case_id: DEFAULT_SEED for case_id in CASES}
    path = Path(SEEDS_PATH if path is None else path)
    if path.is_file():
        data = json.loads(path.read_text(encoding="utf-8"))
        for case_id, entry in data.get("cases", {}).items():
            if case_id in seeds:
                seeds[case_id] = int(entry["seed"])
    return seeds


def build_spec(case_id: str, seed: int, *, study: str = STUDY) -> engine.RunSpec:
    case = CASES[case_id]
    return engine.RunSpec(
        study=study,
        N=case.get("N", N),
        dt=dt_star.DT_STAR,
        tf=case["tf"],
        every=engine.every_for(dt_star.DT_STAR, case["dt2"]),
        seed=int(seed),
        obstacles=case["obstacles"],
        x0=case["x0"],
        init=INIT,
        trajectory=True,
        stop="none",
    )


def _pick_spec(case_id: str, seed: int) -> engine.RunSpec:
    case = CASES[case_id]
    return engine.RunSpec(
        study=PICK_STUDY,
        N=case.get("N", N),
        dt=dt_star.DT_STAR,
        tf=PICK_TMAX,
        every=engine.every_for(dt_star.DT_STAR, case["dt2"]),
        seed=int(seed),
        obstacles=True,
        x0=case["x0"],
        init=INIT,
        trajectory=False,
        stop="t90",
    )


def pick_seeds(workers: int = 4, case_ids=None) -> dict:
    """Elige por caso con obstaculos la semilla de t90 mas cercano a la media."""
    obstacle_cases = [c for c, v in CASES.items() if v["obstacles"]
                      and (case_ids is None or c in case_ids)]
    workers = max(1, min(int(workers), os.cpu_count() or 1))
    specs = [_pick_spec(c, s) for c in obstacle_cases for s in PICK_SEEDS]
    if specs:
        report = engine.run_batch(specs, binary=BINARY, data_root=DATA_ROOT, workers=workers)
        for res in report.results:
            if res.status not in ("done", "skipped"):
                raise AnimationError(
                    f"pre-corrida {res.spec.name()}: {res.status} {res.message}")
    chosen = {}
    for case_id in obstacle_cases:
        k = study_density.k90(CASES[case_id].get("N", N))
        t90 = {}
        for seed in PICK_SEEDS:
            spec = _pick_spec(case_id, seed)
            conv = tp4io.read_conversions(engine.run_dir(spec, DATA_ROOT) / "conversions.txt")
            if conv.used >= k:
                t90[seed] = float(conv.t[k - 1])
        if not t90:
            raise AnimationError(f"{case_id}: ninguna semilla llego a t90 en {PICK_TMAX} s")
        mean = float(np.mean(list(t90.values())))
        seed = min(t90, key=lambda s: (abs(t90[s] - mean), s))
        chosen[case_id] = {"seed": seed, "t90": t90[seed], "mean_t90": mean,
                           "n_reached": len(t90), "n_seeds": len(PICK_SEEDS)}
    previous = {}
    if SEEDS_PATH.is_file():
        previous = json.loads(SEEDS_PATH.read_text(encoding="utf-8")).get("cases", {})
    cases = {}
    for case_id, case in CASES.items():
        if case_id in chosen:
            cases[case_id] = chosen[case_id]
        elif not case["obstacles"]:
            cases[case_id] = {"seed": DEFAULT_SEED, "rule": "fija"}
        elif case_id in previous:
            cases[case_id] = previous[case_id]
    payload = {"version": 1, "rule": SEED_RULE, "cases": cases}
    SEEDS_PATH.parent.mkdir(parents=True, exist_ok=True)
    SEEDS_PATH.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return cases


# --------------------------------------------------------------------------- utilidades


def png_time(case_id: str, conv) -> float:
    """Instante del PNG: la conversion ceil(N/2) (Fu ~ 0.5) o un tiempo fijo."""
    case = CASES[case_id]
    rule = case["png_rule"]
    if isinstance(rule, (int, float)) and not isinstance(rule, bool):
        return float(rule)
    if rule != "fu_half":
        raise ValueError(f"png_rule desconocida: {rule!r}")
    k = (int(conv.header.N) + 1) // 2
    times = np.asarray(conv.t)
    if len(times) >= k:
        return float(times[k - 1])
    return case["tf"] / 2.0


def frame_time(t: float, dt2: float) -> float:
    """Primer instante de salida (multiplo de dt2) en o despues de t."""
    return math.ceil(t / dt2 - 1e-9) * dt2


def probe_video(path) -> dict:
    """Hechos del primer stream de video segun ffprobe."""
    argv = ["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
            "stream=codec_name,pix_fmt,width,height,nb_frames,duration", "-of", "json",
            str(path)]
    try:
        proc = subprocess.run(argv, capture_output=True, text=True, check=False)
    except OSError as exc:
        raise RuntimeError(f"ffprobe no encontrado: {exc}") from exc
    if proc.returncode != 0:
        raise RuntimeError(f"ffprobe fallo sobre {path}: {proc.stderr.strip()[:200]}")
    streams = json.loads(proc.stdout).get("streams", [])
    if not streams:
        raise RuntimeError(f"{path}: sin stream de video")
    s = streams[0]
    return {
        "codec": s.get("codec_name"),
        "pix_fmt": s.get("pix_fmt"),
        "width": int(s["width"]),
        "height": int(s["height"]),
        "nb_frames": int(s["nb_frames"]),
        "duration": float(s["duration"]),
    }


def count_color_pixels(png_path) -> dict:
    """Pixeles de cada color de particula (azul fresca, roja usada) en un PNG."""
    with Image.open(png_path) as img:
        rgb = np.asarray(img.convert("RGB")).astype(int)
    out = {}
    for name, color in (("blue", animate.COLOR_FRESH), ("red", animate.COLOR_USED)):
        target = np.array([round(255 * c) for c in to_rgb(color)])
        out[name] = int(np.all(np.abs(rgb - target) <= COLOR_TOL, axis=2).sum())
    return out


def _sha256(path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _load_manifest() -> dict:
    if MANIFEST_PATH.is_file():
        return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    return {"version": 1, "cases": {}}


def _case_params(case_id: str, seed: int) -> dict:
    case = CASES[case_id]
    return {"seed": int(seed), "N": case.get("N", N), "x0": case["x0"], "tf": case["tf"],
            "dt": dt_star.DT_STAR, "dt2": case["dt2"], "fps": case["fps"]}


# --------------------------------------------------------------------------- casos


def run_case(case_id: str, stage: str = "all", force: bool = False, *, workers: int = 1) -> dict:
    """Corre el motor y/o renderiza un caso; devuelve su entrada del manifiesto."""
    if case_id not in CASES:
        raise AnimationError(f"caso desconocido: {case_id}")
    if stage not in ("sim", "render", "all"):
        raise AnimationError(f"stage invalido: {stage}")
    case = CASES[case_id]
    seed = load_seeds()[case_id]
    spec = build_spec(case_id, seed)
    directory = engine.run_dir(spec, DATA_ROOT)

    if stage in ("sim", "all"):
        report = engine.run_batch([spec], binary=BINARY, data_root=DATA_ROOT, workers=1)
        res = report.results[0]
        if res.status not in ("done", "skipped"):
            raise AnimationError(f"{case_id}: el motor termino {res.status}: {res.message}")
        print(f"sim   {case_id} seed={seed} {res.status}", flush=True)
    if stage == "sim":
        return {}

    mp4 = VIDEO_DIR / f"{case_id}.mp4"
    png = FRAMES_DIR / f"{case_id}.png"
    manifest = _load_manifest()
    old = manifest.get("cases", {}).get(case_id, {})
    params = _case_params(case_id, seed)
    if (not force and mp4.is_file() and png.is_file()
            and all(old.get(k) == v for k, v in params.items())):
        print(f"skip  {case_id} (mp4 y png ya generados con la misma semilla)", flush=True)
        return old

    frames_path = directory / "frames.txt"
    conv_path = directory / "conversions.txt"
    if not frames_path.is_file() or not conv_path.is_file():
        raise AnimationError(f"{case_id}: faltan frames.txt/conversions.txt en la corrida; "
                             "correr --stage sim primero")
    conv = tp4io.read_conversions(conv_path)
    t_png = png_time(case_id, conv)
    t_frame = frame_time(t_png, case["dt2"])

    video = animate.render_video(frames_path, mp4, fmt="mp4", fps=case["fps"], stride=1,
                                 max_frames=1_000_000, dpi=100)
    info = animate.render_png(frames_path, png, time=t_frame, dpi=100)
    facts = probe_video(mp4)
    print(f"video {case_id} frames={video['frames']} png_t={info['t']:.3f} "
          f"png_used={info['used']}", flush=True)

    entry = {
        **params,
        "frames": video["frames"],
        "every": spec.every,
        "init": INIT,
        "png_t": info["t"],
        "png_used": info["used"],
        "mp4": f"animaciones/{case_id}.mp4",
        "mp4_sha256": _sha256(mp4),
        "mp4_bytes": mp4.stat().st_size,
        "png": f"frames/{case_id}.png",
        "png_sha256": _sha256(png),
        "png_bytes": png.stat().st_size,
        "probe": facts,
        "engine_sha256": _sha256(BINARY),
        "platform": platform.platform(),
    }
    manifest.setdefault("cases", {})[case_id] = entry
    manifest["version"] = 1
    MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n",
                             encoding="utf-8")
    return entry


# --------------------------------------------------------------------------- verificacion


def _verify_case(case_id: str) -> tuple[str, str | None]:
    """Linea de resumen y primer problema (o None) de un caso."""
    case = CASES[case_id]
    mp4 = VIDEO_DIR / f"{case_id}.mp4"
    png = FRAMES_DIR / f"{case_id}.png"
    if not mp4.is_file():
        return "", f"falta {mp4.name}"
    if not png.is_file():
        return "", f"falta {png.name}"
    try:
        p = probe_video(mp4)
    except RuntimeError as exc:
        return "", str(exc)
    colors = count_color_pixels(png)
    seed = load_seeds()[case_id]
    line = (f"case={case_id} codec={p['codec']} pix_fmt={p['pix_fmt']} "
            f"size={p['width']}x{p['height']} frames={p['nb_frames']} "
            f"duration={p['duration']:.2f} seed={seed} blue={colors['blue']} "
            f"red={colors['red']}")
    expected = round(case["tf"] / case["dt2"]) + 1
    if p["codec"] != "h264":
        return line, f"codec {p['codec']} != h264"
    if p["pix_fmt"] != "yuv420p":
        return line, f"pix_fmt {p['pix_fmt']} != yuv420p"
    if p["width"] % 2 or p["height"] % 2:
        return line, f"dimensiones impares {p['width']}x{p['height']}"
    if p["nb_frames"] != expected:
        return line, f"frames {p['nb_frames']} != {expected}"
    if abs(p["duration"] - p["nb_frames"] / case["fps"]) > DURATION_TOL_S:
        return line, f"duracion {p['duration']:.2f} s lejos de {p['nb_frames'] / case['fps']:.2f} s"
    size = mp4.stat().st_size
    if not MIN_MP4_BYTES <= size <= MAX_MP4_BYTES:
        return line, f"tamano del mp4 {size} B fuera de [{MIN_MP4_BYTES}, {MAX_MP4_BYTES}]"
    with Image.open(png) as img:
        if img.size != PNG_SIZE:
            return line, f"png de {img.size[0]}x{img.size[1]}, se esperaba {PNG_SIZE[0]}x{PNG_SIZE[1]}"
    if colors["blue"] < MIN_COLOR_PIXELS:
        return line, f"png con {colors['blue']} pixeles azules (< {MIN_COLOR_PIXELS})"
    if case["obstacles"]:
        if colors["red"] < MIN_COLOR_PIXELS:
            return line, f"png con {colors['red']} pixeles rojos (< {MIN_COLOR_PIXELS})"
    elif colors["red"] != 0:
        return line, f"png sin obstaculos con {colors['red']} pixeles rojos"
    return line, None


def verify(case_ids) -> int:
    """Verifica MP4 y PNG de cada caso; imprime una linea por caso. 0 si todo OK."""
    case_ids = list(case_ids)
    failed = False
    for case_id in case_ids:
        line, problem = _verify_case(case_id)
        if line:
            print(line)
        if problem:
            print(f"error: {case_id}: {problem}")
            failed = True
    if failed:
        return 1
    print(f"ANIMATIONS OK cases={len(case_ids)}")
    return 0


# --------------------------------------------------------------------------- CLI


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Animaciones y fotogramas de la presentacion.")
    p.add_argument("--case", action="append", dest="cases",
                   help="id de caso (repetible); por defecto todos")
    p.add_argument("--stage", choices=("sim", "render", "all"), default="all")
    p.add_argument("--pick-seeds", action="store_true",
                   help="elige y guarda las semillas representativas (animaciones/seeds.json)")
    p.add_argument("--verify", action="store_true", help="verifica MP4 y PNG ya generados")
    p.add_argument("--force", action="store_true", help="re-renderiza aunque ya existan")
    p.add_argument("--workers", type=int, default=4, help="procesos de la pre-corrida de semillas")
    return p


def main(argv=None) -> int:
    args = _build_parser().parse_args(argv)
    case_ids = list(args.cases) if args.cases else list(CASES)
    unknown = [c for c in case_ids if c not in CASES]
    if unknown:
        print(f"error: caso desconocido: {', '.join(unknown)} (validos: {', '.join(CASES)})")
        return 1
    try:
        if args.verify:
            return verify(case_ids)
        if args.pick_seeds:
            chosen = pick_seeds(args.workers, case_ids=set(case_ids))
            for case_id, entry in chosen.items():
                print(f"seed  {case_id} {entry}")
            return 0
        if args.stage in ("render", "all"):
            if not animate.ffmpeg_available() or shutil.which("ffprobe") is None:
                print("error: ffmpeg no encontrado")
                return 1
        for case_id in case_ids:
            run_case(case_id, args.stage, args.force)
    except (AnimationError, RuntimeError, ValueError, OSError) as exc:
        print(f"error: {exc}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
