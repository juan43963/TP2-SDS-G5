#!/usr/bin/env python3
"""Animacion caracteristica por esquema con semilla comun desde los CSV de estudio (OUT-03, D-40).

Lee las corridas del estudio (`<data-dir>/runs/*.csv`), elige la menor semilla completa comun
a TSDMD, EDMD y el hibrido, vuelve a correr cada esquema con `--out` y exactamente los
parametros de la fila CSV (N, L, tmax, T, alpha, dt2), y exige que la corrida complete y
reproduzca el t_evac de la estadistica (D-31). Con el archivo de texto genera por esquema un
GIF, un MP4 (si hay ffmpeg) y las instantaneas en t = 0 y a mitad de la evacuacion, mas
`anim_summary.csv` con los observables escalares calculados desde el archivo (file_observables).
Reutiliza lo ya generado salvo --force (D-34).

Uso tipico:
    python3 python/make_animations.py --data-dir data/studies --N 500
    python3 python/make_animations.py --data-dir build/study_smoke --source-study smoke \\
        --N 60 --L 10 --target-frames 40 --fps 10 --formats gif
"""

import argparse
import csv
import dataclasses
import math
import os
import re
import subprocess
import sys

import matplotlib

matplotlib.use("Agg")

import animate  # noqa: E402
import run_studies as rs  # noqa: E402
import study_common as sc  # noqa: E402

SUMMARY_FIELDS = ("scheme", "N", "L", "seed", "common_seed", "tmax", "t_evac_engine",
                  "t_evac_file", "frames_file", "frames_gif", "pop_first", "frac_tsdmd_mean",
                  "gif", "mp4")
SOURCE_STUDIES = ("bc", "sweep", "smoke")
FORMATS = ("gif", "mp4")
REPRO_TOL = 1e-6  # |t_evac(--out) - t_evac(CSV)|: el motor es determinista


class AnimError(Exception):
    """Falla que corta la generacion (se imprime como `ANIMATIONS FAIL <motivo>`)."""


def _say(text):
    print(text, flush=True)


def _same(a, b, tol=1e-6):
    return a is not None and abs(a - b) <= tol


def source_rows(args):
    """Filas completas candidatas: N y L pedidos; hibrido con --hybrid-T; modo segun el estudio."""
    mode = "time" if args.source_study == "sweep" else "stat"
    rows = sc.collect_runs(os.path.join(args.data_dir, "runs"), study=args.source_study,
                           mode=mode)
    out = []
    for r in rows:
        if r["N"] != args.N or not _same(r["L"], args.L):
            continue
        if r["scheme"] == "hybrid" and not _same(r["hybrid_T"], args.hybrid_T, 1e-9):
            continue
        out.append(r)
    return out


def choose_rows(args, rows):
    """Fila elegida por esquema y common_seed (1 si todos comparten semilla, 0 si no)."""
    done = sc.completed_rows(rows)

    def by_seed(scheme):
        found = {}
        for r in done:
            if r["scheme"] == scheme:
                found.setdefault(r["seed"], r)
        return found

    table = {scheme: by_seed(scheme) for scheme in sc.SCHEMES}
    if args.seed is not None:
        chosen = {}
        for scheme in sc.SCHEMES:
            if args.seed not in table[scheme]:
                raise AnimError(f"scheme={scheme} no tiene una corrida completa con "
                                f"seed={args.seed} en el estudio {args.source_study}")
            chosen[scheme] = table[scheme][args.seed]
        return chosen, 1
    empty = [s for s in sc.SCHEMES if not table[s]]
    if empty:
        raise AnimError("sin corridas completas en el estudio "
                        f"{args.source_study} (N={args.N}, L={args.L:g}) para scheme="
                        + ",".join(empty))
    common = sc.common_completed_seeds(done, sc.SCHEMES)
    if common:
        return {s: table[s][common[0]] for s in sc.SCHEMES}, 1
    chosen = {s: table[s][min(table[s])] for s in sc.SCHEMES}
    _say("ANIMATIONS WARN sin semilla completa comun a los tres esquemas: se usa la menor de "
         "cada uno (" + " ".join(f"{s}={chosen[s]['seed']}" for s in sc.SCHEMES)
         + ") common_seed=0")
    return chosen, 0


def _simulate(row, args, base):
    """Corre el motor con los parametros de la fila y deja `<base>.txt` y `<base>.result`."""
    # Misma linea de comandos que la corrida estadistica (modo stat => --out), solo cambia la ruta.
    spec = dataclasses.replace(sc.spec_from_row(row), mode="stat")
    txt, res = base + ".txt", base + ".result"
    _discard(res)  # el .result es la marca de "archivo completo": se escribe al final
    argv = rs.build_argv(spec, args.tp5, txt)
    try:
        proc = subprocess.run(argv, capture_output=True, text=True, timeout=args.run_timeout)
    except subprocess.TimeoutExpired:
        _discard(txt)
        raise AnimError(f"scheme={row['scheme']} seed={row['seed']} supero --run-timeout "
                        f"{args.run_timeout:g} s")
    if proc.returncode != 0:
        _discard(txt)
        first = (proc.stderr or "").strip().splitlines()
        raise AnimError(f"scheme={row['scheme']} seed={row['seed']} el motor fallo: "
                        f"{first[0] if first else 'codigo ' + str(proc.returncode)}")
    with open(res + ".tmp", "w") as f:
        f.write(proc.stdout)
    os.replace(res + ".tmp", res)
    return sc.parse_result_line(proc.stdout)


def _discard(path):
    if os.path.exists(path):
        os.remove(path)


def _load_result(res):
    with open(res) as f:
        return sc.parse_result_line(f.read())


def _check_reproduces(row, result):
    scheme, seed = row["scheme"], row["seed"]
    if result.get("completed") != 1:
        raise AnimError(f"scheme={scheme} seed={seed} no reproduce la estadistica: la corrida "
                        f"con --out no completa (completed={result.get('completed')})")
    diff = abs(result["t_evac"] - row["t_evac"])
    if diff > REPRO_TOL:
        raise AnimError(f"scheme={scheme} seed={seed} no reproduce la estadistica: "
                        f"t_evac={result['t_evac']:.6f} contra {row['t_evac']:.6f} del CSV "
                        f"(|dif|={diff:.2e} > {REPRO_TOL:g})")


def _need(path, force):
    return force or not os.path.exists(path)


def _render(label, inp, out, **kw):
    try:
        return animate.render(inp, out, **kw)
    except animate.FfmpegUnavailable:
        raise
    except (ValueError, OSError, subprocess.CalledProcessError) as exc:
        raise AnimError(f"scheme={label} no se pudo escribir {out}: {exc}")


def make_one(row, args, common_seed, formats):
    scheme, seed = row["scheme"], row["seed"]
    base = os.path.join(args.out_dir, f"{scheme}_N{row['N']}_s{seed}")
    txt, res = base + ".txt", base + ".result"
    simulated = args.force or not (os.path.exists(txt) and os.path.exists(res))
    result = _simulate(row, args, base) if simulated else _load_result(res)
    _check_reproduces(row, result)

    obs = sc.file_observables(txt)
    t_file = obs["t_evac_file"]
    if t_file is None:
        raise AnimError(f"scheme={scheme} seed={seed}: el archivo {txt} no llega a poblacion 0")
    gap = t_file - row["t_evac"]
    if not (0.0 <= gap < row["dt2"] + 1e-6):
        raise AnimError(f"scheme={scheme} seed={seed}: t_evac del archivo ({t_file:.4f}) fuera "
                        f"de [t_evac, t_evac + dt2) con t_evac={row['t_evac']:.4f}")

    frames_file = len(obs["times"])
    every = max(1, math.ceil(frames_file / args.target_frames))
    frames_gif = math.ceil(frames_file / every)
    gif, mp4 = "", ""
    if "gif" in formats:
        path = base + ".gif"
        if _need(path, args.force):
            line = _render(scheme, txt, path, target_frames=args.target_frames, fps=args.fps,
                           max_frames=args.max_frames)
            frames_gif = int(re.search(r"frames=(\d+)", line).group(1))
        gif = path
    if "mp4" in formats:
        path = base + ".mp4"
        try:
            if _need(path, args.force):
                _render(scheme, txt, path, target_frames=args.target_frames, fps=args.fps,
                        max_frames=args.max_frames, ffmpeg_path=args.ffmpeg_path)
            mp4 = path
        except animate.FfmpegUnavailable as exc:
            _say(f"ANIMATIONS SKIP mp4 scheme={scheme} reason={exc}")
    for suffix, when in (("_t0.png", 0.0), ("_mid.png", t_file / 2.0)):
        path = base + suffix
        if _need(path, args.force):
            _render(scheme, txt, path, snapshot=repr(float(when)))

    _say(f"ANIMATIONS scheme={scheme} seed={seed} N={row['N']} simulated={int(simulated)} "
         f"t_evac={row['t_evac']:.4f} t_evac_file={t_file:.4f} frames_file={frames_file} "
         f"frames_gif={frames_gif} pop_first={int(obs['pop'][0])} "
         f"frac_tsdmd_mean={obs['frac_tsdmd_mean']:.4f} gif={gif or 'none'} "
         f"mp4={mp4 or 'none'}")
    return {"scheme": scheme, "N": row["N"], "L": row["L"], "seed": seed,
            "common_seed": common_seed, "tmax": row["tmax"], "t_evac_engine": row["t_evac"],
            "t_evac_file": t_file, "frames_file": frames_file, "frames_gif": frames_gif,
            "pop_first": int(obs["pop"][0]), "frac_tsdmd_mean": obs["frac_tsdmd_mean"],
            "gif": gif, "mp4": mp4}


def write_summary(path, rows):
    tmp = path + ".tmp"
    with open(tmp, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(SUMMARY_FIELDS)
        for r in rows:
            w.writerow([repr(r[k]) if isinstance(r[k], float) else r[k] for k in SUMMARY_FIELDS])
    os.replace(tmp, path)


def parse_formats(text):
    formats = [p.strip().lower() for p in text.split(",") if p.strip()]
    if not formats:
        raise AnimError("--formats: lista vacia")
    for f in formats:
        if f not in FORMATS:
            raise AnimError(f"--formats: formato desconocido {f!r} (validos: gif, mp4)")
    return set(formats)


def run(args):
    if args.N < 1:
        raise AnimError("--N debe ser >= 1")
    if args.L is None:
        args.L = sc.scaled_L(args.N)
    if args.L <= 0:
        raise AnimError("--L debe ser positivo")
    if args.target_frames < 1 or args.target_frames > args.max_frames:
        raise AnimError(f"--target-frames debe estar en [1, --max-frames={args.max_frames}]")
    if args.fps <= 0:
        raise AnimError("--fps debe ser positivo")
    if args.run_timeout <= 0:
        raise AnimError("--run-timeout debe ser positivo")
    formats = parse_formats(args.formats)
    if args.out_dir is None:
        args.out_dir = os.path.join(args.data_dir, "anim")

    rows = source_rows(args)
    chosen, common_seed = choose_rows(args, rows)
    os.makedirs(args.out_dir, exist_ok=True)
    summary = [make_one(chosen[s], args, common_seed, formats) for s in sc.SCHEMES]
    write_summary(os.path.join(args.out_dir, "anim_summary.csv"), summary)
    seeds = sorted({r["seed"] for r in summary}, key=int)
    seed_text = ",".join(str(chosen[s]["seed"]) for s in sc.SCHEMES) if common_seed == 0 \
        else str(seeds[0])
    _say(f"ANIMATIONS n={len(summary)} N={args.N} seed={seed_text} common_seed={common_seed} "
         f"gif={sum(1 for r in summary if r['gif'])} mp4={sum(1 for r in summary if r['mp4'])} "
         f"out_dir={args.out_dir}")
    return 0


def build_parser():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--data-dir", default="data/studies", help="directorio de estudio")
    ap.add_argument("--out-dir", default=None, help="salida (default <data-dir>/anim)")
    ap.add_argument("--tp5", default="./tp5", help="comando del simulador")
    ap.add_argument("--source-study", choices=SOURCE_STUDIES, default="bc",
                    help="estudio del que se eligen las corridas")
    ap.add_argument("--N", type=int, default=500, help="agentes")
    ap.add_argument("--L", type=float, default=None, help="lado de la sala (default 50*sqrt(N/500))")
    ap.add_argument("--hybrid-T", dest="hybrid_T", type=float, default=0.5,
                    help="T del hibrido a animar")
    ap.add_argument("--seed", type=int, default=None, help="fuerza la semilla de los tres esquemas")
    ap.add_argument("--formats", default="gif,mp4", help="gif, mp4 o gif,mp4 (mp4 si hay ffmpeg)")
    ap.add_argument("--target-frames", type=int, default=400, help="frames objetivo por animacion")
    ap.add_argument("--fps", type=float, default=15.0, help="cuadros por segundo")
    ap.add_argument("--max-frames", type=int, default=600, help="cota de frames por animacion")
    ap.add_argument("--ffmpeg-path", default=None, help="ruta de un ffmpeg que no esta en el PATH")
    ap.add_argument("--run-timeout", type=float, default=7200.0, help="segundos por corrida")
    ap.add_argument("--force", action="store_true", help="vuelve a simular y a renderizar todo")
    return ap


def main(argv):
    args = build_parser().parse_args(argv)
    try:
        return run(args)
    except KeyboardInterrupt:
        _say("ANIMATIONS FAIL interrumpido: lo generado queda guardado")
        return 1
    except (AnimError, ValueError, OSError, subprocess.CalledProcessError) as exc:
        _say(f"ANIMATIONS FAIL {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
