"""Linter del codigo fuente de presentacion.tex contra la Guia, el enunciado y D-10 a D-12.

Todo lo que se puede juzgar sobre el codigo fuente se juzga aca, antes de compilar. Cada
regla es una funcion sobre el texto que devuelve problemas con el nombre de la regla.

    python3 TP5/presentacion/lint_deck.py                       # modo completo
    python3 TP5/presentacion/lint_deck.py --partial             # esqueleto o borrador
    python3 TP5/presentacion/lint_deck.py --allow-missing-figures

Salida: `LINT OK [(partial)] frames=<n> time=<s>s A=<s> B=<s> C=<s> hyb=<s> warnings=<k>`
o una linea `LINT FAILED: <regla>: <detalle>` por problema (exit 1).

Marcador de diapositiva (comentario justo antes de cada `\\begin{frame}`):

    % SLIDE <id> | V:<A|B|C> | T:<segundos>

V es la voz que presenta y T los segundos planeados. Los ids, la voz y los segundos se leen
de los marcadores: un ajuste de tiempos no requiere tocar este archivo. Las secciones del
cuerpo se escriben en `secciones/*.tex` y se incluyen con `\\input`; el linter las expande.
Solo biblioteca estandar.
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

PRES_DIR = Path(__file__).resolve().parent
DEFAULT_TEX = PRES_DIR / "presentacion.tex"

# Orden de D-10.
SLIDE_IDS = (
    "title",
    "intro_real", "intro_sfm",
    "impl_arquitectura", "impl_uml", "impl_tsdmd", "impl_edmd", "impl_eventos", "impl_colision",
    "hyb_criterio", "hyb_sync", "hyb_contactos",
    "sim_sistema", "sim_observables", "sim_realizaciones",
    "res_anim", "res_fraccion", "res_poblacion", "res_tevac", "res_walltime", "res_sweep",
    "res_scale_a", "res_scale_b", "extra_kappa0", "extra_kappa0_anim",
    "concl", "gracias",
)
SECTIONS = ("Introducción", "Implementación", "Simulaciones", "Resultados", "Conclusiones")
SECTION_OF = {
    "intro_real": "Introducción", "intro_sfm": "Introducción",
    "impl_arquitectura": "Implementación", "impl_uml": "Implementación", "impl_tsdmd": "Implementación",
    "impl_edmd": "Implementación", "impl_eventos": "Implementación", "impl_colision": "Implementación",
    "hyb_criterio": "Implementación", "hyb_sync": "Implementación",
    "hyb_contactos": "Implementación",
    "sim_sistema": "Simulaciones", "sim_observables": "Simulaciones",
    "sim_realizaciones": "Simulaciones",
    "res_anim": "Resultados", "res_fraccion": "Resultados", "res_poblacion": "Resultados",
    "res_tevac": "Resultados", "res_walltime": "Resultados", "res_sweep": "Resultados",
    "res_scale_a": "Resultados", "res_scale_b": "Resultados",
    "extra_kappa0": "Resultados", "extra_kappa0_anim": "Resultados",
    "concl": "Conclusiones", "gracias": "Conclusiones",
}
# Figura que cada diapositiva de resultados tiene que mostrar (res_anim: las tres, en orden).
FIGURE_OF = {
    "res_fraccion": "pres_fraction",
    "res_poblacion": "pres_population",
    "res_tevac": "pres_tevac",
    "res_walltime": "pres_walltime",
    "res_sweep": "pres_sweep_T",
    "res_scale_a": "pres_scale_a",
    "res_scale_b": "pres_scale_b",
    "extra_kappa0": "pres_kappa0",
    "extra_kappa0_anim": "frame_kappa0",
    "impl_eventos": "frame_eventos",
    "res_anim": ("frame_tsdmd", "frame_edmd", "frame_hybrid"),
}
VIDEO_IDS = ("tsdmd_n500", "edmd_n500", "hybrid_n500")

TIME_MIN, TIME_MAX = 690, 780
SECTION_SECONDS = 2
VOICE_MIN, VOICE_MAX = 0.28, 0.38
HYB_MIN_SECONDS = 150
HYB_MIN_SHARE = 0.18
HYB_MIN_FRAMES = 3
INTRO_MAX_FRAMES = 3
NOT_COUNTED_IN_SECTION = ("title", "gracias")

FORBIDDEN_PACKAGES = ("media9", "animate", "multimedia", "movie15", "pdfpages", "attachfile",
                      "attachfile2", "embedfile", "bclogo")
FORBIDDEN_COMMANDS = ("includemovie", "animategraphics", "movie", "textattachfile",
                      "attachfile", "embedfile", "mediaplayer")
MEDIA_EXT = re.compile(r"\.(mp4|gif|mov|avi|webm)\b", re.IGNORECASE)
CLOUD_WORDS = re.compile(r"\b(drive|dropbox|onedrive|campus)\b", re.IGNORECASE)
PLACEHOLDERS = (
    ("TODO", re.compile(r"\bTODO\b")),
    ("FIXME", re.compile(r"\bFIXME\b")),
    ("XXX", re.compile(r"\bXXX\b")),
    ("TBD", re.compile(r"\bTBD\b")),
    ("lorem", re.compile(r"lorem", re.IGNORECASE)),
)
LOCAL_PATHS = (
    re.compile(r"(?<![A-Za-z0-9])[A-Za-z]:[\\/](?!/)"),
    re.compile(r"/Users/"),
    re.compile(r"/mnt/"),
    re.compile(r"/home/"),
    re.compile(r"Desktop", re.IGNORECASE),
    re.compile(r"OneDrive", re.IGNORECASE),
)
HYPOTHESIS_WORDS = re.compile(r"hip[oó]tesis|probablemente|seguramente|debido\s+a\b",
                              re.IGNORECASE)

MARKER = re.compile(r"^\s*%\s*SLIDE\s+(\w+)\s*\|\s*V:([ABC])\s*\|\s*T:(\d+)\s*$")
MARKER_LOOSE = re.compile(r"^\s*%\s*SLIDE\b")
INCLUDE_GFX = re.compile(r"\\includegraphics\s*(?:\[[^\]]*\])?\s*\{([^{}]*)\}")
INPUT_CMD = re.compile(r"\\input\s*\{([^{}]*)\}")

# Contenido obligatorio del hibrido (D-11): id -> lista de alternativas; cada elemento de la
# lista es una tupla de sinonimos (basta uno). Sin distinguir mayusculas.
HYBRID_CONTENT = {
    "hyb_criterio": ((r"\tau_c",), ("histéresis",), (r"\alpha",)),
    "hyb_sync": (("t_k",), ("promote", "pares mixtos")),
    "hyb_contactos": (("promote",), ("auditor",), ("contactos perdidos",)),
    "impl_colision": (("restitución",), ("v_d",)),
    "impl_edmd": (("generaci",),),
}


@dataclass
class Problem:
    rule: str
    detail: str


@dataclass
class Frame:
    start: int
    end: int
    body: str            # texto sin comentarios
    marker: tuple | None  # (id, V, T) o None
    line: int


@dataclass
class Result:
    problems: list = field(default_factory=list)
    warnings: list = field(default_factory=list)
    stats: dict = field(default_factory=dict)


def strip_comments(text: str) -> str:
    """Reemplaza cada comentario por espacios (mismos offsets); respeta \\% escapado."""
    out = []
    for line in text.split("\n"):
        cut = None
        i = 0
        while i < len(line):
            ch = line[i]
            if ch == "\\":
                i += 2
                continue
            if ch == "%":
                cut = i
                break
            i += 1
        out.append(line if cut is None else line[:cut] + " " * (len(line) - cut))
    return "\n".join(out)


def line_of(text: str, offset: int) -> int:
    return text.count("\n", 0, offset) + 1


def document_start(clean: str) -> int:
    m = re.search(r"\\begin\{document\}", clean)
    return m.end() if m else 0


# ------------------------------------------------------------------ expansion de \input

def _resolve_input(name: str, base: Path) -> Path | None:
    for cand in (name, name + ".tex"):
        p = base / cand
        if p.is_file():
            return p
    return None


def expand_inputs(raw: str, base: Path, problems: list, depth: int = 0,
                  in_document: bool = False) -> str:
    """Expande los \\input del cuerpo (despues de \\begin{document}); en el preambulo solo
    verifica que el archivo exista. Los \\input comentados se ignoran."""
    if depth > 5:
        problems.append(Problem("R0-input", "\\input anidado mas de 5 niveles"))
        return raw
    out = []
    for line in raw.split("\n"):
        if re.search(r"\\begin\{document\}", strip_comments(line)):
            in_document = True
        clean_line = strip_comments(line)
        m = INPUT_CMD.search(clean_line)
        if not m:
            out.append(line)
            continue
        name = m.group(1).strip()
        path = _resolve_input(name, base)
        if path is None:
            problems.append(Problem("R0-input", f"\\input{{{name}}}: el archivo no existe"))
            out.append(line)
            continue
        if not in_document:
            out.append(line)
            continue
        sub = path.read_text(encoding="utf-8").replace("\r\n", "\n")
        sub = expand_inputs(sub, base, problems, depth + 1, in_document=True)
        out.append(line[:m.start()] + sub + line[m.end():])
    return "\n".join(out)


def parse_frames(raw: str, clean: str) -> list[Frame]:
    start_doc = document_start(clean)
    frames = []
    pos = start_doc
    raw_lines = raw.split("\n")
    while True:
        b = re.compile(r"\\begin\{frame\}").search(clean, pos)
        if not b:
            break
        e = re.compile(r"\\end\{frame\}").search(clean, b.end())
        end = e.end() if e else len(clean)
        line = line_of(raw, b.start())
        marker = None
        idx = line - 2
        while idx >= 0 and not raw_lines[idx].strip():
            idx -= 1
        if idx >= 0:
            m = MARKER.match(raw_lines[idx])
            if m:
                marker = (m.group(1), m.group(2), int(m.group(3)))
        frames.append(Frame(b.start(), end, clean[b.end():(e.start() if e else len(clean))],
                            marker, line))
        pos = end
    return frames


# --------------------------------------------------------------------------- reglas

def rule_balance(clean: str) -> list[Problem]:
    """R1: llaves balanceadas y \\begin/\\end en orden."""
    problems = []
    depth, i, n = 0, 0, len(clean)
    while i < n:
        ch = clean[i]
        if ch == "\\":
            i += 2
            continue
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth < 0:
                problems.append(Problem("R1-balance", f"llave de cierre sobrante en la linea "
                                                      f"{line_of(clean, i)}"))
                depth = 0
        i += 1
    if depth > 0:
        problems.append(Problem("R1-balance", f"{depth} llave(s) sin cerrar"))
    stack = []
    for m in re.finditer(r"\\(begin|end)\{([^{}]*)\}", clean):
        kind, env = m.group(1), m.group(2)
        if kind == "begin":
            stack.append((env, line_of(clean, m.start())))
        elif not stack:
            problems.append(Problem("R1-balance", f"\\end{{{env}}} sin \\begin (linea "
                                                  f"{line_of(clean, m.start())})"))
        else:
            open_env, open_line = stack.pop()
            if open_env != env:
                problems.append(Problem(
                    "R1-balance", f"\\begin{{{open_env}}} (linea {open_line}) se cierra con "
                                  f"\\end{{{env}}} (linea {line_of(clean, m.start())})"))
                break
    for env, ln in stack:
        problems.append(Problem("R1-balance", f"falta \\end{{{env}}} (abierto en la linea {ln})"))
    if not re.search(r"\\end\{document\}", clean):
        problems.append(Problem("R1-balance", "falta \\end{document}"))
    return problems


def rule_markers(raw: str, frames: list[Frame]) -> list[Problem]:
    """R2: cada frame lleva un marcador SLIDE valido con id unico y de la lista."""
    problems = []
    for ln, line in enumerate(raw.split("\n"), 1):
        if MARKER_LOOSE.match(line) and not MARKER.match(line):
            problems.append(Problem("R2-markers", f"marcador mal formado en la linea {ln}"))
    seen = set()
    for fr in frames:
        if fr.marker is None:
            problems.append(Problem("R2-markers", f"el frame de la linea {fr.line} no tiene "
                                                  f"marcador SLIDE justo antes"))
            continue
        sid = fr.marker[0]
        if sid in seen:
            problems.append(Problem("R2-markers", f"id repetido: {sid}"))
        seen.add(sid)
        if sid not in SLIDE_IDS:
            problems.append(Problem("R2-markers", f"id desconocido: {sid}"))
    return problems


def rule_order(frames: list[Frame], partial: bool) -> list[Problem]:
    """R3: los ids aparecen en el orden previsto (completo: exactamente la lista)."""
    ids = [f.marker[0] for f in frames if f.marker and f.marker[0] in SLIDE_IDS]
    if partial:
        pos = [SLIDE_IDS.index(i) for i in ids]
        if pos != sorted(pos):
            return [Problem("R3-order", "diapositivas fuera del orden de D-10")]
        return []
    if ids == list(SLIDE_IDS):
        return []
    for k, (got, want) in enumerate(zip(ids, SLIDE_IDS)):
        if got != want:
            return [Problem("R3-order", f"posicion {k + 1}: aparece {got} y corresponde {want}")]
    if len(ids) < len(SLIDE_IDS):
        return [Problem("R3-order", f"faltan diapositivas desde {SLIDE_IDS[len(ids)]}")]
    return [Problem("R3-order", f"sobran diapositivas desde {ids[len(SLIDE_IDS)]}")]


def rule_forbidden(clean: str) -> list[Problem]:
    """R6: sin captions, paquetes de medios, comandos de video ni links a la nube."""
    problems = []
    for m in re.finditer(r"\\caption(?![A-Za-z])", clean):
        problems.append(Problem("R6-forbidden", f"\\caption (linea {line_of(clean, m.start())}): "
                                                f"la Guia 1.7 prohibe leyendas bajo las figuras"))
    for m in re.finditer(r"\\(?:usepackage|RequirePackage)\s*(?:\[[^\]]*\])?\s*\{([^{}]*)\}",
                         clean):
        for pkg in (p.strip() for p in m.group(1).split(",")):
            if pkg in FORBIDDEN_PACKAGES:
                problems.append(Problem("R6-forbidden", f"paquete prohibido: {pkg}"))
    for cmd in FORBIDDEN_COMMANDS:
        for m in re.finditer(r"\\" + cmd + r"(?![A-Za-z])", clean):
            problems.append(Problem("R6-forbidden", f"comando prohibido: \\{cmd} "
                                                    f"(linea {line_of(clean, m.start())})"))
    for m in re.finditer(r"href\s*\{\s*run:", clean):
        problems.append(Problem("R6-forbidden", "href{run:...}: lanza un archivo local"))
    for m in MEDIA_EXT.finditer(clean):
        problems.append(Problem("R6-forbidden", f"extension de video/animacion: {m.group(0)} "
                                                f"(linea {line_of(clean, m.start())})"))
    for m in CLOUD_WORDS.finditer(clean):
        problems.append(Problem("R6-forbidden", f"'{m.group(0)}': los links van a YouTube o "
                                                f"Vimeo (linea {line_of(clean, m.start())})"))
    return problems


def _figure_exists(name: str, base: Path) -> bool:
    name = Path(name.strip()).name
    for cand in (name, name + ".png"):
        if (base / "figuras" / cand).is_file():
            return True
    return False


def rule_assets(clean: str, frames: list[Frame], base: Path, allow_missing: bool,
                partial: bool = False):
    """R7: figuras presentes en figuras/ y figura correcta en cada diapositiva de resultados."""
    problems, warnings = [], []
    doc = document_start(clean)
    for m in INCLUDE_GFX.finditer(clean, doc):
        target = m.group(1).strip()
        if "#" in target or _figure_exists(target, base):
            continue
        detail = f"falta la figura {target} en figuras/ (linea {line_of(clean, m.start())})"
        (warnings if allow_missing else problems).append(Problem("R7-assets", detail))
    for fr in frames:
        if not fr.marker:
            continue
        sid = fr.marker[0]
        want = FIGURE_OF.get(sid)
        if want is None or (partial and sid == "res_anim"):
            continue  # el esqueleto todavia no tiene los tres fotogramas
        got = [Path(t.strip()).name for t in INCLUDE_GFX.findall(fr.body)]
        got = [g[:-4] if g.endswith(".png") else g for g in got]
        wanted = want if isinstance(want, tuple) else (want,)
        for w in wanted:
            if w not in got:
                problems.append(Problem("R7-assets", f"{sid}: debe incluir {w}"))
    return problems, warnings


def rule_placeholders(clean: str) -> list[Problem]:
    """R8: ningun marcador de pendiente literal en el codigo fuente (fuera de comentarios)."""
    problems = []
    for name, rx in PLACEHOLDERS:
        for m in rx.finditer(clean):
            problems.append(Problem("R8-placeholder", f"'{name}' en la linea "
                                                      f"{line_of(clean, m.start())}"))
    return problems


def voice_seconds(frames: list[Frame]) -> dict:
    voices = {"A": 0, "B": 0, "C": 0}
    for fr in frames:
        if fr.marker:
            voices[fr.marker[1]] += fr.marker[2]
    return voices


def hybrid_seconds(frames: list[Frame]) -> tuple[int, int]:
    secs = [fr.marker[2] for fr in frames if fr.marker and fr.marker[0].startswith("hyb_")]
    return sum(secs), len(secs)


def count_sections(clean: str) -> int:
    doc = document_start(clean)
    return len(re.findall(r"\\section\s*(?:\[[^\]]*\])?\s*\{", clean[doc:]))


def rule_budget(frames: list[Frame], n_sections: int) -> list[Problem]:
    """R9 (completo): 690 a 780 s, voces entre 28 y 38 %, hibrido >= 150 s, 18 % y 3 frames."""
    voices = voice_seconds(frames)
    frames_total = sum(voices.values())
    total = frames_total + SECTION_SECONDS * n_sections
    problems = []
    if not TIME_MIN <= total <= TIME_MAX:
        problems.append(Problem("R9-budget", f"tiempo total {total} s (con {SECTION_SECONDS} s "
                                             f"por seccion) fuera de [{TIME_MIN}, {TIME_MAX}] s"))
    if frames_total > 0:
        for v, secs in voices.items():
            share = secs / frames_total
            if not VOICE_MIN <= share <= VOICE_MAX:
                problems.append(Problem(
                    "R9-budget", f"la voz {v} tiene {100 * share:.1f} % del tiempo (debe estar "
                                 f"entre {100 * VOICE_MIN:.0f} y {100 * VOICE_MAX:.0f} %)"))
        hyb, hyb_n = hybrid_seconds(frames)
        if hyb < HYB_MIN_SECONDS:
            problems.append(Problem("R9-budget", f"las diapositivas hyb_* suman {hyb} s "
                                                 f"(minimo {HYB_MIN_SECONDS} s)"))
        if hyb / frames_total < HYB_MIN_SHARE:
            problems.append(Problem("R9-budget", f"las diapositivas hyb_* son el "
                                                 f"{100 * hyb / frames_total:.1f} % del tiempo "
                                                 f"(minimo {100 * HYB_MIN_SHARE:.0f} %)"))
        if hyb_n < HYB_MIN_FRAMES:
            problems.append(Problem("R9-budget", f"hay {hyb_n} diapositivas hyb_* (minimo "
                                                 f"{HYB_MIN_FRAMES})"))
    return problems


def rule_sections(clean: str, frames: list[Frame], partial: bool) -> list[Problem]:
    """R10: secciones de la Guia en orden; Introduccion <= 3; Conclusiones == 1."""
    doc = document_start(clean)
    found = [(m.group(1).strip(), m.start() + doc)
             for m in re.finditer(r"\\section\s*(?:\[[^\]]*\])?\s*\{([^{}]*)\}", clean[doc:])]
    titles = [t for t, _ in found]
    problems = []
    if not partial:
        if titles != list(SECTIONS):
            problems.append(Problem("R10-sections", f"secciones {titles}; deben ser "
                                                    f"{list(SECTIONS)}"))
    else:
        order = [SECTIONS.index(t) for t in titles if t in SECTIONS]
        if len(order) != len(titles) or order != sorted(set(order)):
            problems.append(Problem("R10-sections", f"secciones fuera de orden o ajenas: "
                                                    f"{titles}"))
    if re.search(r"sections\s+numbered|\\insertsectionnumber|\\thesection", clean):
        problems.append(Problem("R10-sections", "plantilla con secciones numeradas (Guia 1.13)"))
    if not re.search(r"\\AtBeginSection", clean):
        problems.append(Problem("R10-sections", "falta \\AtBeginSection (diapositiva solo con "
                                                "el titulo de cada seccion)"))

    def frames_in(title):
        k = titles.index(title)
        lo = found[k][1]
        hi = found[k + 1][1] if k + 1 < len(found) else len(clean)
        return [f for f in frames if lo <= f.start < hi]

    # Cada diapositiva conocida debe estar en su seccion.
    if all(t in titles for t in SECTIONS) and not problems:
        for title in SECTIONS:
            for fr in frames_in(title):
                sid = fr.marker[0] if fr.marker else None
                if sid in SECTION_OF and SECTION_OF[sid] != title:
                    problems.append(Problem("R10-sections",
                                            f"{sid} esta en {title} y corresponde a "
                                            f"{SECTION_OF[sid]}"))
    if "Introducción" in titles and not problems:
        n = len(frames_in("Introducción"))
        if n > INTRO_MAX_FRAMES:
            problems.append(Problem("R10-sections", f"Introducción tiene {n} diapositivas "
                                                    f"(maximo {INTRO_MAX_FRAMES})"))
    if not partial and "Conclusiones" in titles:
        concl = [f for f in frames_in("Conclusiones")
                 if not (f.marker and f.marker[0] in NOT_COUNTED_IN_SECTION)]
        if len(concl) != 1:
            problems.append(Problem("R10-sections", f"Conclusiones debe tener exactamente una "
                                                    f"diapositiva (hay {len(concl)})"))
    return problems


def rule_paths(raw: str) -> list[Problem]:
    """R11: sin rutas locales ni nombres de maquina (ni siquiera en comentarios)."""
    problems = []
    for rx in LOCAL_PATHS:
        for m in rx.finditer(raw):
            problems.append(Problem("R11-paths", f"patron de ruta local '{m.group(0)}' en la "
                                                 f"linea {line_of(raw, m.start())}"))
    return problems


MATH_PATTERNS = (
    re.compile(r"\$\$.*?\$\$", re.DOTALL),
    re.compile(r"(?<!\\)\$.*?(?<!\\)\$", re.DOTALL),
    re.compile(r"\\\[.*?\\\]", re.DOTALL),
    re.compile(r"\\\(.*?\\\)", re.DOTALL),
    re.compile(r"\\begin\{(equation\*?|align\*?|gather\*?|multline\*?)\}.*?"
               r"\\end\{\1\}", re.DOTALL),
)


def strip_math(text: str) -> str:
    for rx in MATH_PATTERNS:
        text = rx.sub(" ", text)
    return text


def rule_notation(clean: str) -> list[Problem]:
    """R12: potencias de 10 escritas como 1E2 o 10^2 fuera de modo matematico (Guia 1.9)."""
    text = strip_math(clean[document_start(clean):])
    text = re.sub(r"\\begin\{tikzpicture\}.*?\\end\{tikzpicture\}", " ", text, flags=re.DOTALL)
    text = INCLUDE_GFX.sub(" ", text)
    text = re.sub(r"\[[^\]]*\]", " ", text)
    problems = []
    for m in re.finditer(r"(?<![A-Za-z0-9_.])\d+(?:\.\d+)?[eE][-+]?\d+\b", text):
        problems.append(Problem("R12-notation", f"notacion '{m.group(0)}': usar 10^x en modo "
                                                f"matematico (Guia 1.9)"))
    for m in re.finditer(r"10\s*\^\s*\{?\s*[-+]?\d", text):
        problems.append(Problem("R12-notation", f"'{m.group(0)}' fuera de modo matematico"))
    return problems


def rule_hybrid_content(frames: list[Frame]) -> list[Problem]:
    """R13: contenido obligatorio de las diapositivas del hibrido (D-11)."""
    problems = []
    for fr in frames:
        if not fr.marker or fr.marker[0] not in HYBRID_CONTENT:
            continue
        sid = fr.marker[0]
        low = fr.body.lower()
        for alternatives in HYBRID_CONTENT[sid]:
            if not any(a.lower() in low for a in alternatives):
                problems.append(Problem("R13-hybrid", f"{sid}: falta '{' o '.join(alternatives)}' "
                                                      f"(D-11)"))
    return problems


def rule_results_content(frames: list[Frame], partial: bool):
    """R14: reglas de honestidad y de forma de los resultados (D-12, D-13)."""
    problems, warnings = [], []
    for fr in frames:
        if not fr.marker:
            continue
        sid = fr.marker[0]
        if sid.startswith("res_") and INCLUDE_GFX.search(fr.body) and "\\params{" not in fr.body:
            problems.append(Problem("R14-results", f"{sid}: la figura necesita \\params{{...}} "
                                                   f"al costado (Guia 1.7)"))
        if sid == "res_tevac":
            if "\\tablaTevac" not in fr.body:
                problems.append(Problem("R14-results", "res_tevac: falta \\tablaTevac"))
            if "completas" not in fr.body.lower():
                problems.append(Problem("R14-results", "res_tevac: debe decir que el promedio "
                                                       "es solo sobre corridas completas"))
        if sid == "res_anim" and not partial:
            for case in VIDEO_IDS:
                if not re.search(r"\\videolink\s*\{" + case + r"\}", fr.body):
                    problems.append(Problem("R14-results", f"res_anim: falta \\videolink{{{case}}}"))
        if (sid.startswith("res_") or sid == "concl") and HYPOTHESIS_WORDS.search(fr.body):
            m = HYPOTHESIS_WORDS.search(fr.body)
            warnings.append(Problem("R14-results", f"{sid}: '{m.group(0)}' parece una hipotesis "
                                                   f"de mecanismo (Guia 2.5, D-12)"))
    return problems, warnings


# --------------------------------------------------------------------------- agregado

def lint(text: str, partial: bool = False, allow_missing_figures: bool = False,
         base: Path = PRES_DIR) -> Result:
    base = Path(base)
    res = Result()
    raw = text.replace("\r\n", "\n")
    raw = expand_inputs(raw, base, res.problems)
    # El apendice (uso de IA) queda fuera del presupuesto y de las reglas del cuerpo.
    raw = re.sub(r"^\\appendix\b.*?(?=^\\end\{document\})", "", raw, flags=re.S | re.M)
    clean = strip_comments(raw)
    frames = parse_frames(raw, clean)
    res.problems += rule_balance(clean)
    res.problems += rule_markers(raw, frames)
    res.problems += rule_order(frames, partial)
    res.problems += rule_forbidden(clean)
    p7, w7 = rule_assets(clean, frames, base, allow_missing_figures, partial)
    res.problems += p7
    res.warnings += w7
    res.problems += rule_placeholders(clean)
    n_sections = count_sections(clean)
    if not partial:
        res.problems += rule_budget(frames, n_sections)
    res.problems += rule_sections(clean, frames, partial)
    res.problems += rule_paths(raw)
    res.problems += rule_notation(clean)
    res.problems += rule_hybrid_content(frames)
    p14, w14 = rule_results_content(frames, partial)
    res.problems += p14
    res.warnings += w14
    voices = voice_seconds(frames)
    hyb, _ = hybrid_seconds(frames)
    res.stats = {
        "frames": len(frames),
        "time": sum(voices.values()) + SECTION_SECONDS * n_sections,
        "hyb": hyb,
        **voices,
    }
    return res


def format_result(res: Result, partial: bool) -> list[str]:
    lines = [f"LINT WARNING: {w.rule}: {w.detail}" for w in res.warnings]
    if res.problems:
        lines += [f"LINT FAILED: {p.rule}: {p.detail}" for p in res.problems]
        return lines
    s = res.stats
    tag = " (partial)" if partial else ""
    lines.append(f"LINT OK{tag} frames={s['frames']} time={s['time']}s A={s['A']} B={s['B']} "
                 f"C={s['C']} hyb={s['hyb']}s warnings={len(res.warnings)}")
    return lines


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--partial", action="store_true",
                        help="esqueleto o borrador: no exige ids ausentes ni el presupuesto")
    parser.add_argument("--allow-missing-figures", action="store_true",
                        help="una figura ausente es un aviso")
    parser.add_argument("--tex", default=str(DEFAULT_TEX), metavar="PATH")
    parser.add_argument("tex_path", nargs="?", help="igual que --tex")
    args = parser.parse_args(argv)
    path = Path(args.tex_path or args.tex)
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        print(f"LINT FAILED: R0-input: no se puede leer {path.name}: {exc.strerror}")
        return 1
    res = lint(text, partial=args.partial, allow_missing_figures=args.allow_missing_figures,
               base=path.resolve().parent)
    for line in format_result(res, args.partial):
        print(line)
    return 1 if res.problems else 0


if __name__ == "__main__":
    sys.exit(main())
