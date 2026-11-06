#!/usr/bin/env python3
"""Guardar evidencia compacta versionable, sin binarios ni trayectorias grandes."""

import argparse
import fcntl
import hashlib
import json
from pathlib import Path
import shutil
import zipfile

from run_comparison import HERE, REPO, specifications


def export(data, output):
    with (data / "study.lock").open("a") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise RuntimeError("el estudio sigue activo; exportar cuando termine") from None
        return export_locked(data, output)


def export_locked(data, output):
    manifest = json.loads((data / "manifest.json").read_text())
    quality = json.loads((data / "timing_quality.json").read_text())
    if not quality["complete"]:
        raise ValueError("no exportar como definitivo sin validar los relojes")
    attempt_count = len(list(specifications(manifest["seeds_preselected"], "full")))
    # La evidencia tiene que corresponder exactamente al codigo disponible.
    for name, expected in manifest["sources_sha256"].items():
        if hashlib.sha256((REPO / name).read_bytes()).hexdigest() != expected:
            raise ValueError(f"la fuente cambio despues de medir: {name}")
    for spec in specifications(manifest["seeds_preselected"], "full"):
        directory = data / "runs" / f"{spec['study']}_{spec['model']}_s{spec['seed']:02d}"
        if not (directory / "run.json").exists() and not (directory / "failure.json").exists():
            raise ValueError("el estudio aun esta incompleto")
    old = output / "manifest.json"
    if old.exists() and json.loads(old.read_text())["fingerprint"] != manifest["fingerprint"]:
        raise ValueError("el destino contiene otro estudio; elegir otro --out")
    output.mkdir(parents=True, exist_ok=True)
    for name in ("manifest.json", "checks.json", "timing_quality.json"):
        if (data / name).exists():
            shutil.copyfile(data / name, output / name)
    for name in ("summary.json", "summary.md", "runs.csv"):
        shutil.copyfile(data / "validated" / name, output / name)
        shutil.copyfile(data / name, output / ("original_" + name))

    # Fechas y orden fijos: el mismo contenido produce el mismo archivo.
    files = [data / name for name in ("manifest.json", "summary.json", "summary.md", "runs.csv", "build.log")]
    files += sorted(p for p in (data / "runs").rglob("*") if p.is_file() and p.suffix in (".json", ".csv"))
    files += [data / "timing_quality.json"]
    files += sorted(p for p in (data / "timing_replays").rglob("*") if p.is_file() and p.suffix in (".json", ".csv"))
    files += sorted(p for p in (data / "validated").iterdir() if p.is_file())
    archive = output / "measurement.zip"
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as bundle:
        for path in sorted(files):
            member = zipfile.ZipInfo(path.relative_to(data).as_posix(), (2026, 11, 5, 0, 0, 0))
            member.compress_type = zipfile.ZIP_DEFLATED
            member.external_attr = 0o100644 << 16
            bundle.writestr(member, path.read_bytes())
    if (data / "figures").exists():
        shutil.copytree(data / "figures", output / "figures", dirs_exist_ok=True)
    for model in ("sfm", "cpm"):
        for name in ("estado_60s.png", "evacuacion.gif", "run.json"):
            path = data / "examples" / model / name
            if path.exists():
                destination = output / "examples" / model / name
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(path, destination)
    if (data / "examples" / "MANIFEST.json").exists():
        shutil.copyfile(data / "examples" / "MANIFEST.json", output / "examples" / "MANIFEST.json")
    atomic = output / "EVIDENCE.json"
    atomic.write_text(json.dumps({
        "study_fingerprint": manifest["fingerprint"],
        "summary_clock_source": "validated/; reemplazos de relojes con fisica reproducida, originales conservados",
        "archive_sha256": hashlib.sha256(archive.read_bytes()).hexdigest(),
        "archive_contains": f"{attempt_count} resultados e invocaciones, poblaciones, manifest y resumen; sin trayectorias",
        "export_script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    }, indent=2) + "\n")
    (output / "README.md").write_text(
        "# Evidencia local de la auditoria SFM / CPM\n\n"
        "`runs.csv` contiene todas las semillas, incluidas las censuradas, con temporizacion validada. "
        "`original_*` conserva las tablas previas; `timing_quality.json` documenta las discrepancias y replays. "
        "`summary.json` conserva precision para recalcular medias y SEM; "
        "`manifest.json` identifica fuentes, compilador y equipo.\n\n"
        "`measurement.zip` conserva resultados, poblaciones e invocaciones sin binarios "
        "ni trayectorias grandes. Para regenerar figuras sin volver a simular, desde la raiz:\n\n"
        "```sh\n"
        "python3 -m zipfile -e TP5/experiments/model_compare/results/measurement.zip /tmp/tp5_model_compare_evidence\n"
        "python3 TP5/experiments/model_compare/make_figures.py --data /tmp/tp5_model_compare_evidence\n"
        "```\n\n"
        "Los GIF de `examples/` son replays de la semilla 1, no nuevas observaciones "
        "estadisticas. Ambos usan la misma escala de reproduccion; el tiempo fisico "
        "aparece en cada cuadro. Ver `TP5/AUDITORIA_TP5.md` para las decisiones y limites.\n")
    print(f"EVIDENCE {output}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=REPO / "data/tp5/model_compare")
    parser.add_argument("--out", type=Path, default=HERE / "results")
    args = parser.parse_args()
    export(args.data, args.out)
