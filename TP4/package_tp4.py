"""Empaqueta y prepara los entregables oficiales de TP4.

Entregables generados (carpeta TP4/entrega/):
  - SdS_TP4_2026Q2G05CS_Presentación.pdf (desde TP4/presentacion/presentacion.pdf)
  - SdS_TP4_2026Q2G05CS_Codigo.zip (solo motor final; lo construye y verifica
    TP4/entrega/package_tp4.py: allowlist, zip determinista, build limpio con -Werror)

Uso: py package_tp4.py   (desde TP4/)
"""

import shutil
import subprocess
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

TP4_DIR = Path(__file__).resolve().parent
ENTREGA = TP4_DIR / "entrega"
PREFIX = "SdS_TP4_2026Q2G05CS"

SRC_PRESENTACION_PDF = TP4_DIR / "presentacion" / "presentacion.pdf"
OUT_PRESENTACION = ENTREGA / f"{PREFIX}_Presentación.pdf"
OUT_ZIP = ENTREGA / f"{PREFIX}_Codigo.zip"


def main() -> int:
    print("=" * 65)
    print("EMPAQUETANDO ENTREGABLES TP4 - 72.25 SIMULACION DE SISTEMAS")
    print(f"Comision: S | Grupo: 05 | Prefijo: {PREFIX}")
    print("=" * 65)

    print("\n1. Empaquetando Codigo Fuente...")
    cmd = [sys.executable, str(ENTREGA / "package_tp4.py"), "--no-git-check"]
    if shutil.which("make") is None:
        print("  [!] make no disponible: se omite el build de verificacion")
        cmd.append("--skip-build")
    res = subprocess.run(cmd, cwd=TP4_DIR)
    if res.returncode != 0:
        print("  [!] Fallo el empaquetado del codigo")
        return res.returncode
    print(f"  [OK] {OUT_ZIP.name} ({OUT_ZIP.stat().st_size / 1024:.1f} KB)")

    print("\n2. Copiando Presentacion PDF...")
    if not SRC_PRESENTACION_PDF.exists():
        raise FileNotFoundError(f"No se encontro la presentacion: {SRC_PRESENTACION_PDF}")
    shutil.copy2(SRC_PRESENTACION_PDF, OUT_PRESENTACION)
    print(f"  [OK] {OUT_PRESENTACION.name} ({OUT_PRESENTACION.stat().st_size / 1024:.1f} KB)")

    print("\n" + "=" * 65)
    print("RESUMEN DE ENTREGABLES GENERADOS (TP4/entrega/):")
    print(f"  a) {OUT_PRESENTACION.name}")
    print(f"  b) {OUT_ZIP.name}")
    print("=" * 65)
    return 0


if __name__ == "__main__":
    sys.exit(main())
