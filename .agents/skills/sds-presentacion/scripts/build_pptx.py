#!/usr/bin/env python3
"""Generador de presentaciones PowerPoint (.pptx) con animaciones GIF embebidas.

Cátedra 72.25 Simulación de Sistemas (ITBA).
Permite cumplir con el requerimiento docente:
  1. El PDF de entrega tiene imágenes estáticas con links.
  2. La presentación oral en vivo corre animaciones nativas sin salir de PowerPoint.

Modo de uso:
    py build_pptx.py --tex presentacion.tex --gif-dir ./gifs --out presentacion_vivo.pptx
"""

import argparse
import subprocess
import sys
from pathlib import Path
from typing import List, Tuple

try:
    import fitz  # PyMuPDF
    import numpy as np
    from PIL import Image
    from pptx import Presentation
    from pptx.util import Inches
except ImportError as err:
    sys.exit(f"Error: faltan librerias requeridas ({err}). Instalar con: pip install pymupdf python-pptx pillow numpy")

MARKER_RGB = (255, 0, 255)  # Color magenta puro #FF00FF
MARKER_TOL = 15

SLIDE_W = Inches(13.333)
SLIDE_H = Inches(7.5)


def compile_live_pdf(tex_path: Path, output_pdf: Path) -> Path:
    """Compila LaTeX Beamer en modo 'vivo' (reemplaza fotogramas por rectangulos magenta)."""
    tex_dir = tex_path.resolve().parent
    base_name = tex_path.stem
    job_name = f"{base_name}_vivo"

    cmd = [
        "pdflatex",
        "-interaction=nonstopmode",
        f"-jobname={job_name}",
        f"\\def\\modo{{vivo}}\\input{{{tex_path.name}}}",
    ]

    print(f"[*] Compilando LaTeX en modo vivo: {job_name}.pdf ...")
    # Dos pasadas para resolver miniframes y referencias cruzadas
    for p in range(1, 3):
        res = subprocess.run(cmd, cwd=tex_dir, capture_output=True, text=True)
        if res.returncode != 0:
            print(f"Error en pasada {p} de LaTeX:\n", res.stderr or res.stdout[-800:])
            raise RuntimeError("Fallo la compilacion de pdflatex.")

    pdf_res = tex_dir / f"{job_name}.pdf"
    if not pdf_res.exists():
        raise FileNotFoundError(f"No se genero {pdf_res}")
    return pdf_res


def find_markers(pix_image: Image.Image) -> List[Tuple[int, int, int, int]]:
    """Encuentra los rectangulos magenta en la imagen renderizada de la pagina."""
    arr = np.array(pix_image)
    if arr.ndim < 3:
        return []

    r, g, b = arr[..., 0], arr[..., 1], arr[..., 2]
    mask = (
        (np.abs(r.astype(int) - MARKER_RGB[0]) <= MARKER_TOL)
        & (np.abs(g.astype(int) - MARKER_RGB[1]) <= MARKER_TOL)
        & (np.abs(b.astype(int) - MARKER_RGB[2]) <= MARKER_TOL)
    )

    if not np.any(mask):
        return []

    rows = np.any(mask, axis=1)
    cols = np.any(mask, axis=0)
    rmin, rmax = np.where(rows)[0][[0, -1]]
    cmin, cmax = np.where(cols)[0][[0, -1]]

    return [(cmin, rmin, cmax - cmin + 1, rmax - rmin + 1)]


def build_pptx(pdf_path: Path, gif_list: List[Path], output_pptx: Path, dpi: int = 150):
    doc = fitz.open(pdf_path)
    prs = Presentation()
    prs.slide_width = SLIDE_W
    prs.slide_height = SLIDE_H
    blank_layout = prs.slide_layouts[6]

    gif_idx = 0
    total_slides = len(doc)
    print(f"[*] Procesando {total_slides} diapositivas a {dpi} DPI...")

    for page_idx in range(total_slides):
        page = doc[page_idx]
        zoom = dpi / 72.0
        mat = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=mat, alpha=False)

        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        markers = find_markers(img)

        # Guardar temporalmente la pagina rasterizada
        tmp_slide_path = pdf_path.parent / f"_tmp_slide_{page_idx}.png"
        img.save(tmp_slide_path)

        slide = prs.slides.add_slide(blank_layout)
        slide.shapes.add_picture(str(tmp_slide_path), Inches(0), Inches(0), width=SLIDE_W, height=SLIDE_H)

        if markers:
            for (mx, my, mw, mh) in markers:
                if gif_idx < len(gif_list):
                    gif_to_embed = gif_list[gif_idx]
                    left = Inches(mx / pix.width * 13.333)
                    top = Inches(my / pix.height * 7.5)
                    width = Inches(mw / pix.width * 13.333)
                    height = Inches(mh / pix.height * 7.5)
                    slide.shapes.add_picture(str(gif_to_embed), left, top, width=width, height=height)
                    print(f"  [+] Diapo {page_idx + 1}: Embebido GIF '{gif_to_embed.name}'")
                    gif_idx += 1

        if tmp_slide_path.exists():
            tmp_slide_path.unlink()

    prs.save(output_pptx)
    print(f"[✓] Presentacion generada exitosamente: {output_pptx}")


def main():
    parser = argparse.ArgumentParser(description="Arma la presentacion .pptx con animaciones embebidas.")
    parser.add_argument("--tex", type=Path, default=Path("presentacion.tex"), help="Ruta al archivo .tex")
    parser.add_argument("--gifs", nargs="*", default=[], help="Lista de rutas a los archivos GIF en orden de aparicion")
    parser.add_argument("--out", type=Path, default=Path("presentacion_vivo.pptx"), help="Ruta de salida del archivo .pptx")
    parser.add_argument("--dpi", type=int, default=150, help="Resolucion de renderizado de diapositivas")
    args = parser.parse_args()

    live_pdf = compile_live_pdf(args.tex, Path("presentacion_vivo.pdf"))
    gif_paths = [Path(g) for g in args.gifs]
    build_pptx(live_pdf, gif_paths, args.out, dpi=args.dpi)


if __name__ == "__main__":
    main()
