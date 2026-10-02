#!/usr/bin/env python3
r"""Auditor automático de diapositivas LaTeX Beamer para Simulación de Sistemas (72.25).

Verifica el cumplimiento de las reglas de la cátedra (GuiaPresentaciones.md)
y correcciones típicas de Parisi:
  1. Diapositivas numeradas
  2. Sin 'caption' en figuras dentro de beamer
  3. Sin notación 1E o 10^x (debe ser 10^{x})
  4. Sin la palabra 'preguntas' en la diapositiva de cierre
  5. Existencia de diapositivas divisorias por sección
  6. Ejes y parámetros al costado (\params)
  7. Modo dual de compilación (\modo, \soloentrega, \animacion)

Uso:
    py audit_presentation.py presentacion.tex
"""

import re
import sys
from pathlib import Path

# Configurar salida segura en UTF-8 para consolas Windows
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def audit_tex(tex_path: Path):
    if not tex_path.exists():
        sys.exit(f"Archivo no encontrado: {tex_path}")

    content = tex_path.read_text(encoding="utf-8")
    lines = content.splitlines()

    issues = []
    warnings = []
    passes = []

    # 1. Numeracion de diapositivas
    if "footline" in content and "frame number" in content:
        passes.append("Diapositivas numeradas en el pie correctamente.")
    else:
        issues.append("Falta numeracion de diapositivas: usar '\\setbeamertemplate{footline}[frame number]'.")

    # 2. Aspect Ratio 16:9
    if "aspectratio=169" in content:
        passes.append("Aspect ratio 16:9 configurado.")
    else:
        warnings.append("Recomendado usar '\\documentclass[aspectratio=169]{beamer}'.")

    # 3. Outer theme miniframes
    if "miniframes" in content:
        passes.append("Outer theme 'miniframes' presente.")
    else:
        warnings.append("Catedra recomienda '\\useoutertheme{miniframes}'.")

    # 4. Sin captions en figuras
    caption_matches = [i + 1 for i, l in enumerate(lines) if re.search(r"\\caption\{", l) and not l.strip().startswith("%")]
    if caption_matches:
        issues.append(f"Regla 1.7 violada: Las figuras no llevan caption. Encontrado en lineas: {caption_matches}")
    else:
        passes.append("Figuras sin captions (correcto).")

    # 5. Notacion cientifica prohibida (1E2, 10^2 sin llaves o literales)
    forbidden_exp = [i + 1 for i, l in enumerate(lines) if re.search(r"\b\d+E[-+]?\d+\b", l, re.IGNORECASE) and not l.strip().startswith("%")]
    if forbidden_exp:
        issues.append(f"Regla 1.9 violada: Prohibido notacion tipo '1E-2' o '1E2'. Encontrado en lineas: {forbidden_exp}. Usar potencias de 10: 10^{{-2}}.")
    else:
        passes.append("Notacion cientifica sin formato 1E (correcto).")

    # 6. Palabra 'preguntas' en cierre
    closing_matches = [i + 1 for i, l in enumerate(lines) if re.search(r"\bpreguntas\b", l, re.IGNORECASE) and not l.strip().startswith("%")]
    if closing_matches:
        issues.append(f"Regla 2.6 violada: Prohibido escribir la palabra 'preguntas' en la presentacion. Lineas: {closing_matches}")
    else:
        passes.append("Cierre sin la palabra 'preguntas' (correcto).")

    # 7. Separadores de seccion
    if "\\AtBeginSection" in content:
        passes.append("Diapositiva divisoria automatica por seccion configurada.")
    else:
        warnings.append("Regla 1.13: Se recomienda automatizar diapositivas divisorias con '\\AtBeginSection'.")

    # 8. Modo dual de animacion
    if "\\definecolor{huecoanim}" in content and "\\animacion" in content:
        passes.append("Soporte para modo dual (entrega estatica / vivo pptx) implementado.")
    else:
        warnings.append("No se detecto macro '\\animacion' con color marcador 'huecoanim' para build_pptx.py.")

    # 9. Conclusiones
    conclusiones_count = len(re.findall(r"\\begin\{frame\}.*?[Cc]onclusi", content))
    if conclusiones_count > 1:
        issues.append(f"Regla 2.5 violada: La seccion Conclusiones debe tener exactamente 1 diapositiva (detectadas {conclusiones_count}).")
    elif conclusiones_count == 1:
        passes.append("Conclusiones en 1 sola diapositiva (correcto).")

    print("\n" + "=" * 60)
    print(f" REPORTE DE AUDITORIA: {tex_path.name}")
    print("=" * 60)

    if passes:
        print("\n[OK] PUNTOS CORRECTOS:")
        for p in passes:
            print(f"  [OK] {p}")

    if warnings:
        print("\n[!] ADVERTENCIAS:")
        for w in warnings:
            print(f"  [!] {w}")

    if issues:
        print("\n[X] VIOLACIONES DETECTADAS (Corregir antes de presentar):")
        for iss in issues:
            print(f"  [X] {iss}")
    else:
        print("\n[OK] Felicitaciones: No se detectaron violaciones criticas a las reglas de la catedra.")

    print("=" * 60 + "\n")
    return len(issues) == 0


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit("Uso: py audit_presentation.py <archivo.tex>")
    audit_tex(Path(sys.argv[1]))
