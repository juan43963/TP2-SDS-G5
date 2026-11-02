#!/usr/bin/env python3
"""Driver reanudable de los estudios de la Fase 9 (D-31, D-32, D-34).

Cada corrida ejecuta ./tp5, lee la linea RESULT y deja un CSV propio con semilla,
completed, t_evac y simulation_ms (D-32). En modo stat tambien guarda la curva de
poblacion `t,pop` reducida desde la trayectoria, que se borra enseguida. Repetir el
comando no vuelve a simular las corridas ya terminadas (D-34).

Modos:
    smoke     tres esquemas, N = 60, L = 10 (rebanada fina de punta a punta)
    bc-stat   estudio b/c: escalera de semillas consecutivas por esquema hasta 10 corridas
              completas, en paralelo (unico modo paralelo, D-31, D-33, D-35)
    bc-time   re-mide con --no-output las primeras K semillas completas de bc-stat, en serie
    sweep     barrido de T del hibrido a N = 200 mas TSDMD/EDMD de referencia, en serie (D-36)
    scale     escalado en N de las variantes a (L = 50*sqrt(N/500)) y b (L = 50), en serie
              (D-37, D-38)
Los modos de tiempo corren un proceso a la vez (D-33) y exigen una sola computadora
(`machine.txt`).

Uso tipico:
    make tp5
    python3 python/run_studies.py --mode smoke --data-dir data/studies
    python3 python/run_studies.py --mode bc-stat --data-dir data/studies --workers 4
    python3 python/run_studies.py --mode bc-time --data-dir data/studies
"""

import argparse
import concurrent.futures
import os
import platform
import shlex
import socket
import subprocess
import sys
from datetime import datetime, timezone

import study_common as sc
from population_compare import first_zero_time, read_population

SMOKE_TMAX = {"tsdmd": 3000.0, "edmd": 3000.0, "hybrid": 400.0}
SMOKE_N = 60
SMOKE_L = 10.0
SMOKE_T = 0.5
SMOKE_ALPHA = 2.0

ENGINE_DT = 1e-4  # paso del motor: el hibrido rechaza 0 < T < 2*dt
MAX_T = 3.0  # Fase 8: oscilacion de esquema con T >= 5 (D-36)
TIME_TOLERANCE = 1e-6  # |t_evac(time) - t_evac(stat)| tolerado: el motor es determinista
DEFAULT_T_LIST = "0,0.1,0.25,0.5,1,2,3"
DEFAULT_N_LIST = "100,200,400,700,1000"
BC_N = 500
SWEEP_N = 200
SCALE_L_B = 50.0
MAKEFILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir, "Makefile")


def build_argv(spec, tp5_cmd, out_path):
    """Lista de argumentos (sin shell) para una corrida. Los numeros pasan por int()/float()."""
    argv = shlex.split(tp5_cmd)
    argv += ["--scheme", str(spec.scheme), "--N", str(int(spec.N)),
             "--L", f"{float(spec.L):.4f}", "--seed", str(int(spec.seed)),
             "--tmax", f"{float(spec.tmax):g}", "--dt2", f"{float(spec.dt2):g}"]
    if spec.scheme == "hybrid":
        if spec.T is not None:
            argv += ["--hybrid-T", f"{float(spec.T):g}"]
        if spec.alpha is not None:
            argv += ["--hybrid-alpha", f"{float(spec.alpha):g}"]
    if spec.mode == "stat":
        argv += ["--out", str(out_path)]
    else:
        argv += ["--no-output"]
    return argv


def _paths(spec, runs_dir, tmp_dir):
    key = sc.run_key(spec)
    return (os.path.join(runs_dir, key + ".csv"), os.path.join(runs_dir, key + ".pop.csv"),
            os.path.join(tmp_dir, key + ".txt"))


def _already_done(spec, run_path, pop_path):
    """Fila valida de una corrida terminada (ok o timeout) o None (D-34)."""
    row = sc.read_run_csv(run_path)
    if row is None or row["status"] not in ("ok", "timeout"):
        return None
    if spec.mode == "stat" and row["status"] == "ok":
        try:
            sc.read_pop_csv(pop_path)
        except (OSError, ValueError, IndexError):
            return None
    return row


def execute_run(spec, tp5_cmd, runs_dir, tmp_dir, timeout, workers=1, keep_trajectory=False):
    """Ejecuta (o reanuda) una corrida. Devuelve (fila, simulo).

    `keep_trajectory` deja la trayectoria completa en tmp_dir (por defecto se borra tras
    reducirla a poblacion).
    """
    os.makedirs(runs_dir, exist_ok=True)
    os.makedirs(tmp_dir, exist_ok=True)
    run_path, pop_path, traj_path = _paths(spec, runs_dir, tmp_dir)
    done = _already_done(spec, run_path, pop_path)
    if done is not None:
        return done, False

    load1 = os.getloadavg()[0] if hasattr(os, "getloadavg") else None
    argv = build_argv(spec, tp5_cmd, traj_path)
    result = None
    status = "ok"
    try:
        proc = subprocess.run(argv, capture_output=True, text=True, timeout=timeout)
        if proc.returncode != 0:
            status = "error"
            first = (proc.stderr or "").strip().splitlines()
            print(f"STUDY error scheme={spec.scheme} seed={spec.seed} "
                  f"msg={first[0] if first else 'codigo ' + str(proc.returncode)}")
        else:
            result = sc.parse_result_line(proc.stdout)
    except subprocess.TimeoutExpired:
        status = "timeout"
    except ValueError as exc:
        status = "error"
        print(f"STUDY error scheme={spec.scheme} seed={spec.seed} msg={exc}")

    try:
        if status == "ok" and spec.mode == "stat":
            try:
                times, pops, _ = read_population(traj_path)
                sc.write_pop_csv(pop_path, times, pops)
            except (ValueError, OSError) as exc:
                status = "error"
                print(f"STUDY error scheme={spec.scheme} seed={spec.seed} msg={exc}")
    finally:
        if os.path.exists(traj_path) and not keep_trajectory:
            os.remove(traj_path)

    row = sc.row_from_result(spec, result, status, load1, workers)
    sc.write_run_csv(run_path, row)
    return row, True


def run_smoke(args):
    """Una corrida corta por esquema; exige completed=1 y t_evac del archivo coherente."""
    runs_dir = os.path.join(args.data_dir, "runs")
    tmp_dir = os.path.join(args.data_dir, "tmp")
    completed = skipped = 0
    for scheme in sc.SCHEMES:
        hybrid = scheme == "hybrid"
        spec = sc.RunSpec(study="smoke", mode="stat", scheme=scheme, N=SMOKE_N, L=SMOKE_L,
                          seed=args.smoke_seed, T=SMOKE_T if hybrid else None,
                          alpha=SMOKE_ALPHA if hybrid else None, tmax=SMOKE_TMAX[scheme],
                          dt2=sc.DEFAULT_DT2)
        row, ran = execute_run(spec, args.tp5, runs_dir, tmp_dir, args.run_timeout)
        if row["status"] != "ok" or row["completed"] != 1:
            print(f"STUDY FAIL scheme={scheme} seed={spec.seed} status={row['status']} "
                  f"completed={row['completed']}")
            return 1
        _, pop_path, _ = _paths(spec, runs_dir, tmp_dir)
        times, pops = sc.read_pop_csv(pop_path)
        t_file = first_zero_time(times, pops)
        t_eng = row["t_evac"]
        if t_file is None or not (t_eng - 1e-6 <= t_file <= t_eng + spec.dt2 + 1e-6):
            print(f"STUDY FAIL scheme={scheme} t_evac={t_eng} t_evac_file={t_file} "
                  f"fuera de [t_evac, t_evac + dt2]")
            return 1
        completed += 1
        skipped += 0 if ran else 1
        print(f"STUDY run scheme={scheme} completed={row['completed']} t_evac={t_eng:.4f} "
              f"t_evac_file={t_file:.4f} simulation_ms={row['simulation_ms']:.3f} "
              f"skipped={0 if ran else 1}")
    print(f"STUDY mode=smoke runs={len(sc.SCHEMES)} completed={completed} skipped={skipped} "
          f"data_dir={args.data_dir}")
    return 0


# --------------------------------------------------------------------------- utilidades comunes

def _say(text):
    print(text, flush=True)


def _fmt(value, spec=".4f"):
    return "na" if value is None else format(value, spec)


def _dirs(args):
    return os.path.join(args.data_dir, "runs"), os.path.join(args.data_dir, "tmp")


def _bad(option, reason):
    raise ValueError(f"{option}: {reason}")


def _parse_schemes(args):
    if args.schemes is None:
        return list(sc.SCHEMES)
    schemes = [s.strip() for s in args.schemes.split(",") if s.strip()]
    if not schemes:
        _bad("--schemes", "lista vacia")
    for s in schemes:
        if s not in sc.SCHEMES:
            _bad("--schemes", f"esquema desconocido {s!r} (validos: {', '.join(sc.SCHEMES)})")
    if len(set(schemes)) != len(schemes):
        _bad("--schemes", "esquemas repetidos")
    return schemes


def _parse_list(option, text, cast):
    try:
        values = [cast(v) for v in text.split(",") if v.strip() != ""]
    except ValueError:
        _bad(option, f"lista invalida {text!r}")
    if not values:
        _bad(option, "lista vacia")
    return values


def _check_common(args):
    if args.run_timeout <= 0:
        _bad("--run-timeout", "debe ser positivo")
    if args.dt2 <= 0:
        _bad("--dt2", "debe ser positivo")
    if args.hybrid_alpha <= 0:
        _bad("--hybrid-alpha", "debe ser positivo")
    if args.hybrid_T < 0 or 0 < args.hybrid_T < 2 * ENGINE_DT:
        _bad("--hybrid-T", f"{args.hybrid_T:g} invalido (0 o >= 2*dt = {2 * ENGINE_DT:g})")
    for name in ("tmax_tsdmd", "tmax_edmd", "tmax_hybrid", "tmax_sweep"):
        if getattr(args, name) <= 0:
            _bad("--" + name.replace("_", "-"), "debe ser positivo")


def _base_tmax(args):
    return {"tsdmd": args.tmax_tsdmd, "edmd": args.tmax_edmd, "hybrid": args.tmax_hybrid}


def _hybrid_params(args, scheme):
    return (args.hybrid_T, args.hybrid_alpha) if scheme == "hybrid" else (None, None)


def _print_run(spec, row, ran):
    t = "na" if spec.T is None else f"{spec.T:g}"
    _say(f"STUDY run study={spec.study} mode={spec.mode} scheme={spec.scheme} N={spec.N} "
         f"seed={spec.seed} T={t} completed={row['completed']} status={row['status']} "
         f"t_evac={_fmt(row['t_evac'])} simulation_ms={_fmt(row['simulation_ms'], '.3f')} "
         f"skipped={0 if ran else 1}")


# --------------------------------------------------------------------------- bc-stat (paralelo)

def _check_bc_options(args):
    _check_common(args)
    n = BC_N if args.N is None else args.N
    if n < 1:
        _bad("--N", "debe ser >= 1")
    length = sc.scaled_L(n) if args.L is None else args.L
    if length <= 0:
        _bad("--L", "debe ser positivo")
    return n, length


def run_bc_stat(args):
    """Escalera de semillas por esquema hasta target_complete corridas completas (D-31)."""
    n, length = _check_bc_options(args)
    schemes = _parse_schemes(args)
    workers = args.workers if args.workers is not None else max(1, (os.cpu_count() or 2) // 2)
    if workers < 1:
        _bad("--workers", "debe ser >= 1")
    if args.target_complete < 1:
        _bad("--target-complete", "debe ser >= 1")
    if args.max_attempts < args.target_complete:
        _bad("--max-attempts", f"{args.max_attempts} < --target-complete {args.target_complete}")
    if args.seed_start < 1:
        _bad("--seed-start", "debe ser >= 1")
    runs_dir, tmp_dir = _dirs(args)
    base = _base_tmax(args)

    def make_spec(scheme, seed):
        t, a = _hybrid_params(args, scheme)
        return sc.RunSpec(study="bc", mode="stat", scheme=scheme, N=n, L=length, seed=seed,
                          T=t, alpha=a, tmax=base[scheme], dt2=args.dt2)

    state = {s: {"next": args.seed_start, "rows": [], "executed": 0, "skipped": 0}
             for s in schemes}
    executor = concurrent.futures.ProcessPoolExecutor(max_workers=workers)
    try:
        while True:
            batch = []
            for scheme in schemes:
                st = state[scheme]
                done, attempted, _ = sc.success_rate(st["rows"])
                if done >= args.target_complete or attempted >= args.max_attempts:
                    continue
                pending = sum(1 for sp in batch if sp.scheme == scheme)
                take = min(workers, args.max_attempts - attempted - pending)
                for _ in range(take):
                    batch.append(make_spec(scheme, st["next"]))
                    st["next"] += 1
            if not batch:
                break
            futures = {executor.submit(execute_run, spec, args.tp5, runs_dir, tmp_dir,
                                       args.run_timeout, workers, args.keep_trajectories): spec
                       for spec in batch}
            for fut in concurrent.futures.as_completed(futures):
                spec = futures[fut]
                row, ran = fut.result()
                st = state[spec.scheme]
                st["rows"].append(row)
                st["executed" if ran else "skipped"] += 1
                _print_run(spec, row, ran)
    except KeyboardInterrupt:
        executor.shutdown(wait=False, cancel_futures=True)
        raise
    executor.shutdown(wait=True)

    reached_all = True
    executed = skipped = 0
    for scheme in schemes:
        st = state[scheme]
        done, attempted, rate = sc.success_rate(st["rows"])
        reached = done >= args.target_complete
        reached_all = reached_all and reached
        executed += st["executed"]
        skipped += st["skipped"]
        if not reached:
            _say(f"STUDY WARN scheme={scheme} completed={done} attempted={attempted} "
                 f"target_reached=0 (complementar con --N 200, D-35)")
        _say(f"STUDY mode=bc-stat N={n} scheme={scheme} attempted={attempted} completed={done} "
             f"skipped={st['skipped']} success_rate={rate:.4f} target_reached={int(reached)}")
    _say(f"STUDY mode=bc-stat N={n} workers={workers} executed={executed} skipped={skipped} "
         f"target_reached={int(reached_all)}")
    return 0


# --------------------------------------------------------------------------- modos de tiempo (serie)

def machine_info(makefile_path=MAKEFILE):
    """Datos de la computadora y del build que fijan la validez del wall-clock (STUDY-04)."""
    cpu_model = "unknown"
    try:
        with open("/proc/cpuinfo") as f:
            for line in f:
                if line.lower().startswith("model name") and ":" in line:
                    cpu_model = line.split(":", 1)[1].strip()
                    break
    except OSError:
        pass
    compiler = "unknown"
    try:
        proc = subprocess.run([os.environ.get("CXX", "c++"), "--version"], capture_output=True,
                              text=True, timeout=20)
        if proc.returncode == 0 and proc.stdout.strip():
            compiler = proc.stdout.strip().splitlines()[0]
    except (OSError, subprocess.SubprocessError):
        pass
    cxxflags = "unknown"
    try:
        with open(makefile_path) as f:
            for line in f:
                if line.startswith("CXXFLAGS") and "=" in line:
                    cxxflags = line.split("=", 1)[1].strip()
                    break
    except OSError:
        pass
    return {
        "hostname": socket.gethostname(), "platform": platform.platform(),
        "machine": platform.machine(), "cpu_count": str(os.cpu_count()), "cpu_model": cpu_model,
        "python": sys.version.split()[0], "compiler": compiler, "cxxflags": cxxflags,
        "date_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }


def write_machine_file(data_dir, makefile_path=MAKEFILE):
    """Crea `machine.txt` la primera vez; si existe de otra computadora, ValueError (D-33)."""
    os.makedirs(data_dir, exist_ok=True)
    path = os.path.join(data_dir, "machine.txt")
    info = machine_info(makefile_path)
    if os.path.exists(path):
        saved = {}
        with open(path) as f:
            for line in f:
                key, sep, value = line.rstrip("\n").partition("=")
                if sep:
                    saved[key] = value
        for key in ("hostname", "cpu_model"):
            if saved.get(key) != info[key]:
                raise ValueError(
                    f"{path} fue creado en otra maquina ({key}: {saved.get(key)!r} vs "
                    f"{info[key]!r}); las mediciones de tiempo deben salir de la misma "
                    f"computadora (STUDY-04)")
        return path
    tmp = path + ".tmp"
    with open(tmp, "w") as f:
        for key, value in info.items():
            f.write(f"{key}={value}\n")
    os.replace(tmp, path)
    return path


def _prepare_time_mode(args):
    """Validaciones comunes de los modos de tiempo: serie estricta y una sola computadora."""
    if args.workers is not None and args.workers > 1:
        _bad("--workers", "los modos de tiempo corren en serie (D-33)")
    if args.workers is not None and args.workers < 1:
        _bad("--workers", "debe ser >= 1")
    _check_common(args)
    return _dirs(args)


def run_serial(specs, tp5_cmd, runs_dir, tmp_dir, timeout):
    """Un proceso a la vez: cada corrida termina antes de empezar la siguiente (D-33).

    Devuelve (filas en el orden de specs, ejecutadas, saltadas). Sin pool ni hilos.
    """
    rows = []
    executed = skipped = 0
    for spec in specs:
        row, ran = execute_run(spec, tp5_cmd, runs_dir, tmp_dir, timeout, workers=1)
        rows.append(row)
        executed += 1 if ran else 0
        skipped += 0 if ran else 1
        _print_run(spec, row, ran)
    return rows, executed, skipped


def run_bc_time(args):
    runs_dir, tmp_dir = _prepare_time_mode(args)
    n, length = _check_bc_options(args)
    schemes = _parse_schemes(args)
    if args.timing_seeds < 1:
        _bad("--timing-seeds", "debe ser >= 1")
    write_machine_file(args.data_dir)
    stat_rows = sc.completed_rows(sc.collect_runs(runs_dir, study="bc", mode="stat"))
    specs, refs = [], []
    for scheme in schemes:
        cand = sorted((r for r in stat_rows if r["scheme"] == scheme and r["N"] == n
                       and abs(r["L"] - length) < 5e-5), key=lambda r: r["seed"])
        if len(cand) < args.timing_seeds:
            _say(f"STUDY WARN scheme={scheme} timing_seeds={len(cand)} < {args.timing_seeds}")
        for r in cand[:args.timing_seeds]:
            specs.append(sc.RunSpec(study="bc", mode="time", scheme=scheme, N=n, L=r["L"],
                                    seed=r["seed"], T=r["hybrid_T"], alpha=r["hybrid_alpha"],
                                    tmax=r["tmax"], dt2=r["dt2"]))
            refs.append(r)
    if not specs:
        _bad("bc-time", f"no hay corridas estadisticas completas para N={n} L={length:g} en "
                        f"{args.data_dir} (correr antes --mode bc-stat)")
    rows, executed, skipped = run_serial(specs, args.tp5, runs_dir, tmp_dir, args.run_timeout)
    mismatches = 0
    for spec, row, ref in zip(specs, rows, refs):
        t_new, t_ref = row["t_evac"], ref["t_evac"]
        same_t = (t_new is None and t_ref is None) or (
            t_new is not None and t_ref is not None and abs(t_new - t_ref) <= TIME_TOLERANCE)
        if row["completed"] != ref["completed"] or not same_t:
            mismatches += 1
            _say(f"STUDY FAIL bc-time scheme={spec.scheme} seed={spec.seed}: t_evac/completed "
                 f"difieren de la corrida estadistica (stat t_evac={_fmt(t_ref)} "
                 f"completed={ref['completed']}, time t_evac={_fmt(t_new)} "
                 f"completed={row['completed']})")
    _say(f"STUDY mode=bc-time N={n} runs={len(specs)} executed={executed} skipped={skipped} "
         f"mismatches={mismatches}")
    if mismatches:
        _say("STUDY FAIL bc-time: t_evac/completed difieren de la corrida estadistica "
             "(esquema, semilla)")
        return 1
    return 0


def _count_completed(rows):
    done = sum(1 for r in rows if sc.is_completed(r))
    return done, len(rows) - done


def run_sweep(args):
    runs_dir, tmp_dir = _prepare_time_mode(args)
    n = SWEEP_N if args.N is None else args.N
    if n < 1:
        _bad("--N", "debe ser >= 1")
    length = sc.scaled_L(n) if args.L is None else args.L
    if length <= 0:
        _bad("--L", "debe ser positivo")
    temps = _parse_list("--T-list", args.T_list, float)
    for t in temps:
        if t < 0:
            _bad("--T-list", f"T = {t:g} negativo")
        if 0 < t < 2 * ENGINE_DT:
            _bad("--T-list", f"T = {t:g} menor que 2*dt = {2 * ENGINE_DT:g}")
        if t > MAX_T and not args.allow_large_T:
            _bad("--T-list", f"T = {t:g} > {MAX_T:g}: oscilacion de esquema en la Fase 8 "
                             f"(usar --allow-large-T para forzarlo)")
    seeds_n = 5 if args.seeds is None else args.seeds
    if seeds_n < 1:
        _bad("--seeds", "debe ser >= 1")
    write_machine_file(args.data_dir)
    specs = []
    for seed in range(1, seeds_n + 1):
        for t in temps:
            specs.append(sc.RunSpec(study="sweep", mode="time", scheme="hybrid", N=n, L=length,
                                    seed=seed, T=t, alpha=args.hybrid_alpha,
                                    tmax=args.tmax_sweep, dt2=args.dt2))
        for scheme in ("tsdmd", "edmd"):
            specs.append(sc.RunSpec(study="sweep", mode="time", scheme=scheme, N=n, L=length,
                                    seed=seed, tmax=args.tmax_sweep, dt2=args.dt2))
    rows, executed, skipped = run_serial(specs, args.tp5, runs_dir, tmp_dir, args.run_timeout)
    done, non = _count_completed(rows)
    _say(f"STUDY mode=sweep N={n} runs={len(specs)} executed={executed} skipped={skipped} "
         f"completed={done} non_completed={non}")
    return 0


def run_scale(args):
    runs_dir, tmp_dir = _prepare_time_mode(args)
    schemes = _parse_schemes(args)
    sizes = sorted(set(_parse_list("--N-list", args.N_list, int)))
    if sizes[0] < 1:
        _bad("--N-list", "N debe ser >= 1")
    seeds_n = 3 if args.seeds is None else args.seeds
    if seeds_n < 1:
        _bad("--seeds", "debe ser >= 1")
    variants = ("a", "b") if args.variant == "both" else (args.variant,)
    base = _base_tmax(args)
    write_machine_file(args.data_dir)
    for variant in variants:
        specs = []
        for n in sizes:
            length = sc.scaled_L(n) if variant == "a" else SCALE_L_B
            for scheme in schemes:
                t, a = _hybrid_params(args, scheme)
                for seed in range(1, seeds_n + 1):
                    specs.append(sc.RunSpec(study=f"scale_{variant}", mode="time", scheme=scheme,
                                            N=n, L=length, seed=seed, T=t, alpha=a,
                                            tmax=sc.scaled_tmax(base[scheme], n), dt2=args.dt2))
        rows, executed, skipped = run_serial(specs, args.tp5, runs_dir, tmp_dir, args.run_timeout)
        done, non = _count_completed(rows)
        _say(f"STUDY mode=scale variant={variant} runs={len(specs)} executed={executed} "
             f"skipped={skipped} completed={done} non_completed={non}")
    return 0


# --------------------------------------------------------------------------- CLI

def build_parser():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0], allow_abbrev=False)
    ap.add_argument("--mode", choices=("smoke", "bc-stat", "bc-time", "sweep", "scale"),
                    required=True, help="modo de ejecucion")
    ap.add_argument("--data-dir", default="data/studies", help="directorio de estudio")
    ap.add_argument("--tp5", default="./tp5", help="comando del simulador")
    ap.add_argument("--smoke-seed", type=int, default=5, help="semilla del modo smoke")
    ap.add_argument("--run-timeout", type=float, default=3600.0,
                    help="tiempo maximo por corrida [s]")
    ap.add_argument("--dt2", type=float, default=sc.DEFAULT_DT2, help="intervalo de salida")
    ap.add_argument("--tmax-tsdmd", type=float, default=sc.DEFAULT_TMAX["tsdmd"])
    ap.add_argument("--tmax-edmd", type=float, default=sc.DEFAULT_TMAX["edmd"])
    ap.add_argument("--tmax-hybrid", type=float, default=sc.DEFAULT_TMAX["hybrid"])
    ap.add_argument("--hybrid-T", dest="hybrid_T", type=float, default=SMOKE_T,
                    help="T del hibrido (D-35)")
    ap.add_argument("--hybrid-alpha", dest="hybrid_alpha", type=float, default=SMOKE_ALPHA,
                    help="alpha del hibrido (D-35)")
    ap.add_argument("--N", type=int, default=None, help="agentes (bc: 500, sweep: 200)")
    ap.add_argument("--L", type=float, default=None, help="lado de la sala (default 50*sqrt(N/500))")
    ap.add_argument("--schemes", default=None, help="esquemas separados por coma (default los tres)")
    ap.add_argument("--workers", type=int, default=None,
                    help="procesos en paralelo (solo bc-stat; los modos de tiempo son en serie)")
    ap.add_argument("--target-complete", type=int, default=10, help="bc-stat: corridas completas")
    ap.add_argument("--max-attempts", type=int, default=80, help="bc-stat: tope de semillas")
    ap.add_argument("--seed-start", type=int, default=1, help="bc-stat: primera semilla")
    ap.add_argument("--keep-trajectories", action="store_true",
                    help="bc-stat: conservar las trayectorias en <data-dir>/tmp")
    ap.add_argument("--timing-seeds", type=int, default=10, help="bc-time: semillas a re-medir")
    ap.add_argument("--T-list", dest="T_list", default=DEFAULT_T_LIST, help="sweep: valores de T")
    ap.add_argument("--allow-large-T", dest="allow_large_T", action="store_true",
                    help="sweep: permitir T > 3")
    ap.add_argument("--tmax-sweep", type=float, default=600.0, help="sweep: tmax comun")
    ap.add_argument("--seeds", type=int, default=None, help="sweep (5) y scale (3): semillas 1..K")
    ap.add_argument("--variant", choices=("a", "b", "both"), default="both",
                    help="scale: a (L = 50*sqrt(N/500)), b (L = 50)")
    ap.add_argument("--N-list", dest="N_list", default=DEFAULT_N_LIST, help="scale: valores de N")
    return ap


def main(argv):
    args = build_parser().parse_args(argv)
    runners = {"smoke": run_smoke, "bc-stat": run_bc_stat, "bc-time": run_bc_time,
               "sweep": run_sweep, "scale": run_scale}
    try:
        return runners[args.mode](args)
    except KeyboardInterrupt:
        _say("STUDY FAIL interrumpido: lo terminado queda guardado")
        return 1
    except (ValueError, OSError) as exc:
        _say(f"STUDY FAIL {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
