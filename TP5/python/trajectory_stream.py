"""Lector en streaming del archivo `TP5_TRAJECTORY 1` (D-30).

Lo comparten `scheme_fraction.py` (fraccion de agentes por esquema vs tiempo) y
`animate.py` (instantanea y GIF coloreados por esquema). Ambos leen solo el
archivo de texto, sin ejecutar el simulador. El formato es el que escribe
`TrajectoryWriter` (TP5/src/utils/io.cpp): cabecera `clave valor`, linea
`COLUMNS id x y vx vy r scheme`, bloques `FRAME t n` con `n` filas y `END`.

Todo archivo malformado se rechaza con ValueError `ruta:linea: motivo`. Las claves
de cabecera desconocidas (por ejemplo `hybrid_T` y `hybrid_alpha`) se conservan.
"""

import collections

import numpy as np

MAGIC = "TP5_TRAJECTORY 1"
MIN_COLUMNS = 7  # id x y vx vy r scheme

# TSDMD azul, EDMD rojo: el mismo mapeo que population_compare.py.
SCHEME_COLORS = {0: "#1f4e79", 1: "#c0392b"}
SCHEME_LABELS = {0: "TSDMD", 1: "EDMD"}

Frame = collections.namedtuple("Frame", ["t", "rows"])


def read_header(path):
    """Diccionario clave -> valor (texto) de la cabecera, hasta la linea COLUMNS."""
    header = {}
    last_line = 0
    with open(path, "r") as f:
        for lineno, raw in enumerate(f, start=1):
            last_line = lineno
            line = raw.strip()
            if lineno == 1:
                if line != MAGIC:
                    raise ValueError(
                        f"{path}:{lineno}: primera linea invalida: {line!r} (se esperaba {MAGIC!r})")
                continue
            if not line:
                continue
            if line.startswith("COLUMNS"):
                return header
            key, _, value = line.partition(" ")
            header[key] = value
    if last_line == 0:
        raise ValueError(f"{path}: archivo vacio")
    raise ValueError(f"{path}:{last_line}: falta la linea COLUMNS en la cabecera")


def header_float(header, key, path):
    """float(header[key]) o ValueError si falta o no es numerica."""
    if key not in header:
        raise ValueError(f"{path}: falta la clave de cabecera '{key}'")
    try:
        return float(header[key])
    except ValueError:
        raise ValueError(f"{path}: valor no numerico en la cabecera: {key} {header[key]!r}")


def iter_frames(path):
    """Generador de `Frame(t, rows)` en una sola pasada.

    `rows` es un arreglo float64 de forma (n, 7) con las columnas
    id x y vx vy r scheme ((0, 7) si el frame esta vacio). Valida primera linea,
    COLUMNS, linea FRAME, cantidad exacta de filas, columnas, valores numericos,
    scheme en {0, 1}, contenido posterior a END y presencia de END (esta ultima
    al agotar el archivo, despues de entregar los frames validos).
    """
    in_header = True
    expected = None  # filas que faltan del frame actual
    current_t = None
    current_rows = []
    got_end = False
    last_line = 0

    def fail(lineno, msg):
        raise ValueError(f"{path}:{lineno}: {msg}")

    def build(lineno):
        if expected != 0:
            fail(lineno, f"el frame t={current_t} declara mas filas de las leidas")
        if current_rows:
            return Frame(current_t, np.array(current_rows, dtype=np.float64))
        return Frame(current_t, np.empty((0, MIN_COLUMNS), dtype=np.float64))

    with open(path, "r") as f:
        for lineno, raw in enumerate(f, start=1):
            last_line = lineno
            line = raw.strip()
            if lineno == 1:
                if line != MAGIC:
                    fail(lineno, f"primera linea invalida: {line!r} (se esperaba {MAGIC!r})")
                continue
            if not line:
                continue
            if got_end:
                fail(lineno, "contenido despues de END")
            if in_header:
                if line.startswith("COLUMNS"):
                    in_header = False
                continue
            if line.startswith("FRAME "):
                if current_t is not None:
                    frame = build(lineno)
                    current_t = None
                    yield frame
                parts = line.split()
                if len(parts) != 3:
                    fail(lineno, f"linea FRAME mal formada: {line!r}")
                try:
                    current_t = float(parts[1])
                    expected = int(parts[2])
                except ValueError:
                    fail(lineno, f"valor no numerico en {line!r}")
                if expected < 0:
                    fail(lineno, f"cuenta de filas negativa en {line!r}")
                current_rows = []
                continue
            if line == "END":
                if current_t is None:
                    fail(lineno, "END sin ningun FRAME")
                frame = build(lineno)
                current_t = None
                got_end = True
                yield frame
                continue
            if current_t is None:
                fail(lineno, f"fila fuera de un FRAME: {line!r}")
            cols = line.split()
            if len(cols) < MIN_COLUMNS:
                fail(lineno, f"fila con {len(cols)} columnas (minimo {MIN_COLUMNS})")
            try:
                values = [float(c) for c in cols[:MIN_COLUMNS]]
            except ValueError:
                fail(lineno, f"valor no numerico en la fila: {line!r}")
            if not all(np.isfinite(values)):
                fail(lineno, f"valor no finito en la fila: {line!r}")
            if values[6] not in (0.0, 1.0):
                fail(lineno, f"scheme fuera de {{0, 1}}: {cols[6]!r}")
            if expected <= 0:
                fail(lineno, "mas filas que las declaradas en FRAME")
            expected -= 1
            current_rows.append(values)
    if last_line == 0:
        raise ValueError(f"{path}: archivo vacio")
    if in_header:
        raise ValueError(f"{path}:{last_line}: falta la linea COLUMNS en la cabecera")
    if not got_end:
        raise ValueError(f"{path}:{last_line}: falta la linea END")
