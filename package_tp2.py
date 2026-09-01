"""Empaqueta y prepara los entregables oficiales de TP2.

Entregables generados segun el formato de entrega:
  - b) SdS_TP2_2026Q2G05CS_Presentación.pdf (desde TP2/presentacion/presentacion.pdf)
  - c) SdS_TP2_2026Q2G05CS_Codigo.zip (solo version final del motor, orden de los KB)
  - d) SdS_TP2_2026Q2G05CS_Informe.pdf (desde TP2/informe/informe.pdf)

El ZIP de codigo incluye unicamente (allowlist-only):
  - README.md (guia de ejecucion e instrucciones)
  - TP2/src/** (codigo fuente C++ del motor)
  - TP2/Makefile
  - TP2/python/*.py (los scripts de analisis/visualizacion)

Excluye explicitamente: TP2/data/, TP2/build/, binarios compilados,
TP2/informe/, TP2/presentacion/, __pycache__ y .git.

Uso: py package_tp2.py   (desde la raiz del repositorio)
"""

import shutil
import sys
import zipfile
from pathlib import Path

# Ensure UTF-8 output on Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

REPO_ROOT = Path(__file__).resolve().parent
TP2_DIR = REPO_ROOT / "TP2"

# Prefijo oficial: Comision S, Grupo 05 -> G05CS
PREFIX = "SdS_TP2_2026Q2G05CS"

OUT_ZIP = REPO_ROOT / f"{PREFIX}_Codigo.zip"
OUT_INFORME = REPO_ROOT / f"{PREFIX}_Informe.pdf"
OUT_PRESENTACION = REPO_ROOT / f"{PREFIX}_Presentación.pdf"

# Legacy alias para compatibilidad interna
LEGACY_ZIP = REPO_ROOT / "TP2_codigo.zip"

SRC_INFORME_PDF = TP2_DIR / "informe" / "informe.pdf"
SRC_PRESENTACION_PDF = TP2_DIR / "presentacion" / "presentacion.pdf"

SIZE_WARNING_BYTES = 500 * 1024
REQUIRED_PYTHON_SCRIPTS = {"sweep.py", "analyze.py", "animate.py", "benchmark.py"}


def collect_code_files() -> list[Path]:
    """Allowlist-only collection: README.md, TP2/src/**, TP2/Makefile, TP2/python/*.py."""
    readme = [REPO_ROOT / "README.md"] if (REPO_ROOT / "README.md").exists() else []
    src_files = sorted(p for p in (TP2_DIR / "src").rglob("*") if p.is_file())
    makefile = [TP2_DIR / "Makefile"] if (TP2_DIR / "Makefile").exists() else []
    python_files = sorted(p for p in (TP2_DIR / "python").glob("*.py") if p.is_file())
    return readme + src_files + makefile + python_files


def build_zip(files: list[Path], out_path: Path) -> None:
    with zipfile.ZipFile(out_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for f in files:
            zf.write(f, arcname=f.relative_to(REPO_ROOT).as_posix())


def check_size(out_path: Path, warn_bytes: int = SIZE_WARNING_BYTES) -> int:
    size = out_path.stat().st_size
    if size > warn_bytes:
        print(f"  [!] ADVERTENCIA: {out_path.name} pesa {size} bytes (> {warn_bytes} bytes / 500KB)")
    else:
        print(f"  [OK] {out_path.name} ({size / 1024:.1f} KB)")
    return size


def verify_zip_contents(files: list[Path], out_path: Path) -> None:
    expected = {f.relative_to(REPO_ROOT).as_posix() for f in files}
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


def copy_pdf(src: Path, dst: Path, name_desc: str) -> None:
    if not src.exists():
        raise FileNotFoundError(f"No se encontro el PDF origen para {name_desc}: {src}")
    shutil.copy2(src, dst)
    size_kb = dst.stat().st_size / 1024
    print(f"  [OK] {dst.name} ({size_kb:.1f} KB)")


def main() -> int:
    print("=" * 65)
    print("EMPAQUETANDO ENTREGABLES TP2 - 72.25 SIMULACION DE SISTEMAS")
    print(f"Comision: S | Grupo: 05 | Prefijo: {PREFIX}")
    print("=" * 65)

    # 1. Codigo ZIP
    print("\n1. Empaquetando Codigo Fuente...")
    files = collect_code_files()
    build_zip(files, OUT_ZIP)
    check_size(OUT_ZIP)
    verify_zip_contents(files, OUT_ZIP)

    # Copia legacy para retrocompatibilidad
    shutil.copy2(OUT_ZIP, LEGACY_ZIP)

    # 2. Presentacion PDF
    print("\n2. Copiando Presentacion PDF...")
    copy_pdf(SRC_PRESENTACION_PDF, OUT_PRESENTACION, "Presentacion")

    # 3. Informe PDF
    print("\n3. Copiando Informe PDF...")
    copy_pdf(SRC_INFORME_PDF, OUT_INFORME, "Informe")

    print("\n" + "=" * 65)
    print("RESUMEN DE ENTREGABLES GENERADOS:")
    print("  a) Presentacion Oral (13 min) -> En clase 04/09/2026")
    print(f"  b) {OUT_PRESENTACION.name}")
    print(f"  c) {OUT_ZIP.name}")
    print(f"  d) {OUT_INFORME.name}")
    print("=" * 65)
    print("Todos los archivos estan listos y verificados.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
