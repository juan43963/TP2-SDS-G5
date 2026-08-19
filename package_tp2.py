"""Empaqueta la version final del motor de TP2 en TP2_codigo.zip.

Incluye unicamente:
  - TP2/src/** (codigo fuente C++ del motor)
  - TP2/Makefile
  - TP2/python/*.py (los 4 scripts de analisis/visualizacion)

Excluye explicitamente (allowlist-only, nunca blacklist): TP2/data/,
TP2/build/, los binarios compilados TP2/tp2 y TP2/tp2_test,
TP2/informe/, TP2/presentacion/, __pycache__/ y cualquier rastro de .git.

Uso: python3 package_tp2.py   (desde la raiz del repositorio)
"""

from __future__ import annotations

import sys
import zipfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent
TP2_DIR = REPO_ROOT / "TP2"
OUT_ZIP = REPO_ROOT / "TP2_codigo.zip"
SIZE_WARNING_BYTES = 500 * 1024

REQUIRED_PYTHON_SCRIPTS = {"sweep.py", "analyze.py", "animate.py", "benchmark.py"}


def collect_files() -> list[Path]:
    """Allowlist-only collection: TP2/src/**, TP2/Makefile, TP2/python/*.py.

    Nunca incluye TP2/data, TP2/build, TP2/tp2, TP2/tp2_test, TP2/informe
    ni TP2/presentacion -- esos directorios/archivos simplemente no
    aparecen en ninguno de los tres globs de abajo.
    """
    src_files = sorted(p for p in (TP2_DIR / "src").rglob("*") if p.is_file())
    makefile = [TP2_DIR / "Makefile"]
    python_files = sorted(p for p in (TP2_DIR / "python").glob("*.py") if p.is_file())
    return src_files + makefile + python_files


def build_zip(files: list[Path], out_path: Path) -> None:
    with zipfile.ZipFile(out_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for f in files:
            zf.write(f, arcname=str(f.relative_to(REPO_ROOT)))


def check_size(out_path: Path, warn_bytes: int = SIZE_WARNING_BYTES) -> int:
    """Informativo, nunca aborta el empaquetado -- el enunciado pide 'orden de kb'."""
    size = out_path.stat().st_size
    if size > warn_bytes:
        print(f"ADVERTENCIA: {out_path.name} pesa {size} bytes (> {warn_bytes} bytes / 500KB)")
    else:
        print(f"OK: {out_path.name} pesa {size} bytes")
    return size


def verify_contents(files: list[Path], out_path: Path) -> None:
    """Reabre el zip y confirma que su contenido es EXACTAMENTE el esperado.

    - Ni de mas ni de menos: set(namelist) == set(expected arcnames).
    - Los 4 scripts Python deben estar todos presentes bajo TP2/python/ --
      si benchmark.py faltara por una dependencia rota con 05-01, esto
      debe fallar fuerte en vez de empaquetar silenciosamente solo 3 de 4.
    """
    expected = {str(f.relative_to(REPO_ROOT)) for f in files}
    with zipfile.ZipFile(out_path) as zf:
        actual = set(zf.namelist())

    if actual != expected:
        missing = expected - actual
        extra = actual - expected
        raise AssertionError(
            f"Contenido del zip no coincide con lo esperado. Faltantes: {missing} Sobrantes: {extra}"
        )

    python_entries = [n for n in actual if n.startswith("TP2/python/")]
    python_bases = {n.rsplit("/", 1)[-1] for n in python_entries}
    if python_bases != REQUIRED_PYTHON_SCRIPTS:
        raise AssertionError(
            f"Faltan scripts Python requeridos en el zip. Esperados: {REQUIRED_PYTHON_SCRIPTS}, encontrados: {python_bases}"
        )


def main() -> int:
    files = collect_files()
    build_zip(files, OUT_ZIP)
    check_size(OUT_ZIP)
    verify_contents(files, OUT_ZIP)
    print(f"{OUT_ZIP} generado con {len(files)} archivos")
    return 0


if __name__ == "__main__":
    sys.exit(main())
