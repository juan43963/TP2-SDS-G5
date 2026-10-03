"""Importa las 14 figuras oficiales a presentacion/figuras (DEL-03).

Los datos oficiales (`ejercicio1/data`, `ejercicio2/data`) no se versionan, asi que
las figuras de los estudios 2.1a a 2.4b y la del oscilador viven en la maquina que
corrio los barridos. Este script las copia al directorio que lee la presentacion y
deja un MANIFEST.json con la procedencia (ruta RELATIVA a su raiz de datos, sha256,
tamano y hora UTC; nunca rutas absolutas ni nombres de usuario).

    python3 presentacion/sync_figuras.py --list
    python3 presentacion/sync_figuras.py
    python3 presentacion/sync_figuras.py --strict --ej2-data /ruta/a/ejercicio2/data

Solo se leen las 14 rutas de la tabla FIGURES. Cada archivo se resuelve (symlinks
incluidos) y se rechaza si cae fuera de su raiz, si no es un PNG de al menos
600 x 400 px o si pesa mas de 20 MB.
"""

from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import shutil
import struct
import sys
from pathlib import Path

PRES_DIR = Path(__file__).resolve().parent
TP4_DIR = PRES_DIR.parent
DEFAULT_DEST = PRES_DIR / "figuras"
DEFAULT_ROOTS = {1: TP4_DIR / "ejercicio1" / "data", 2: TP4_DIR / "ejercicio2" / "data"}

# (ejercicio, ruta relativa a su data/, nombre del archivo), en el orden del enunciado.
FIGURES = (
    (1, "oscillator/ecm_vs_dt.png"),
    (2, "energy/figures/energy_vs_time.png"),
    (2, "energy/figures/eps_vs_dt.png"),
    (2, "timing/figures/timing_vs_N.png"),
    (2, "timing/figures/cost_per_particle_step.png"),
    (2, "density/figures/t90_t100_vs_density.png"),
    (2, "density/figures/success_fu_vs_density.png"),
    (2, "conversion/figures/fu_vs_t_N100.png"),
    (2, "conversion/figures/t90_vs_x0_compare.png"),
    (2, "thermal/figures/ratio_vs_t.png"),
    (2, "thermal/figures/fv_evolution.png"),
    (2, "thermal/figures/fv_stationary_fit.png"),
    (2, "thermal/figures/fit_error_kbt.png"),
    (2, "heatmap/figures/heatmap_t90.png"),
)

PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
MIN_WIDTH, MIN_HEIGHT = 600, 400
MAX_BYTES = 20 * 1024 * 1024


class FigureError(Exception):
    """Un archivo candidato no cumple las condiciones de seguridad o de formato."""


def figure_name(rel: str) -> str:
    return rel.rsplit("/", 1)[-1]


def source_label(exercise: int, rel: str) -> str:
    """Etiqueta de procedencia: ejercicio y ruta relativa, sin rutas absolutas."""
    return f"ejercicio{exercise}/data/{rel}"


def png_size(path: Path) -> tuple[int, int]:
    """(ancho, alto) leidos del chunk IHDR; FigureError si no es un PNG valido."""
    with path.open("rb") as fh:
        head = fh.read(24)
    if len(head) < 24 or head[:8] != PNG_SIGNATURE or head[12:16] != b"IHDR":
        raise FigureError("no es un PNG valido")
    width, height = struct.unpack(">II", head[16:24])
    return width, height


def check_candidate(path: Path, root: Path) -> Path:
    """Valida un candidato y devuelve su ruta resuelta; FigureError si se rechaza."""
    resolved = path.resolve()
    root_resolved = root.resolve()
    if resolved != root_resolved and root_resolved not in resolved.parents:
        raise FigureError("el archivo resuelve fuera de su raiz de datos")
    if not resolved.is_file():
        raise FigureError("no es un archivo regular")
    size = resolved.stat().st_size
    if size > MAX_BYTES:
        raise FigureError(f"pesa {size} bytes (maximo {MAX_BYTES})")
    width, height = png_size(resolved)
    if width < MIN_WIDTH or height < MIN_HEIGHT:
        raise FigureError(f"imagen de {width} x {height} px (minimo {MIN_WIDTH} x {MIN_HEIGHT})")
    return resolved


def find_source(exercise: int, rel: str, roots: dict[int, list[Path]]):
    """Primera raiz que tiene el archivo y lo acepta: (ruta resuelta, raiz) o (None, motivo)."""
    reasons = []
    for root in roots[exercise]:
        candidate = root / rel
        if not candidate.exists() and not candidate.is_symlink():
            continue
        try:
            return check_candidate(candidate, root), root
        except FigureError as exc:
            reasons.append(f"{exc}")
    return None, "; ".join(reasons)


def sha256_of(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def sync(roots: dict[int, list[Path]], dest: Path, list_only: bool = False):
    """Copia lo que existe. Devuelve (lineas de estado, nombres faltantes)."""
    dest = Path(dest)
    manifest_path = dest / "MANIFEST.json"
    manifest = {}
    if manifest_path.exists():
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8")).get("figures", {})
        except (ValueError, OSError):
            manifest = {}
    lines, missing = [], []
    for exercise, rel in FIGURES:
        name = figure_name(rel)
        label = source_label(exercise, rel)
        found, root = find_source(exercise, rel, roots)
        if found is None:
            local = dest / name
            if local.exists() and name in manifest:
                lines.append(f"figure={name} status=present src={manifest[name]['source']}")
            else:
                suffix = f" ({root})" if root else ""
                lines.append(f"figure={name} status=missing src={label}{suffix}")
                missing.append(name)
            continue
        if list_only:
            lines.append(f"figure={name} status=available src={label}")
            continue
        dest.mkdir(parents=True, exist_ok=True)
        target = dest / name
        shutil.copyfile(found, target)
        manifest[name] = {
            "source": label,
            "sha256": sha256_of(target),
            "bytes": target.stat().st_size,
            "copied_utc": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        }
        lines.append(f"figure={name} status=copied src={label}")
    if not list_only and manifest:
        dest.mkdir(parents=True, exist_ok=True)
        ordered = {figure_name(rel): manifest[figure_name(rel)]
                   for _, rel in FIGURES if figure_name(rel) in manifest}
        manifest_path.write_text(
            json.dumps({"version": 1, "figures": ordered}, indent=2, sort_keys=True) + "\n",
            encoding="utf-8")
    return lines, missing


def build_roots(ej1_data, ej2_data) -> dict[int, list[Path]]:
    """Raices dadas por linea de comandos primero, despues las locales."""
    return {
        1: [Path(p) for p in (ej1_data or [])] + [DEFAULT_ROOTS[1]],
        2: [Path(p) for p in (ej2_data or [])] + [DEFAULT_ROOTS[2]],
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--list", action="store_true", help="solo imprime el inventario")
    parser.add_argument("--strict", action="store_true", help="sale con 1 si falta alguna figura")
    parser.add_argument("--ej1-data", action="append", default=[], metavar="DIR",
                        help="raiz de datos del ejercicio 1 (repetible)")
    parser.add_argument("--ej2-data", action="append", default=[], metavar="DIR",
                        help="raiz de datos del ejercicio 2 (repetible)")
    parser.add_argument("--dest", default=str(DEFAULT_DEST), metavar="DIR")
    args = parser.parse_args(argv)

    lines, missing = sync(build_roots(args.ej1_data, args.ej2_data), Path(args.dest),
                          list_only=args.list)
    for line in lines:
        print(line)
    if args.list:
        return 0
    if missing:
        print(f"SYNC INCOMPLETE missing={len(missing)}: {' '.join(missing)}")
        return 1 if args.strict else 0
    print(f"SYNC OK figures={len(FIGURES)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
