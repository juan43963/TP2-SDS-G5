"""Linter de presentacion.tex contra GuiaPresentaciones y el enunciado (DEL-03).

Esta maquina no tiene motor LaTeX: el PDF se compila en otra (plan 06-04). Todo lo que
se pueda juzgar sobre el codigo fuente se juzga aca, antes. Cada regla es una funcion
sobre el texto que devuelve problemas con el nombre de la regla.

    python3 presentacion/lint_deck.py                       # modo completo
    python3 presentacion/lint_deck.py --partial             # esqueleto o borrador
    python3 presentacion/lint_deck.py --allow-missing-figures

Salida: `LINT OK [(partial)] frames=<n> content=<n> time=<s>s A=<s> B=<s> C=<s>
warnings=<k>` o una linea `LINT FAILED: <regla>: <detalle>` por problema (exit 1).

Marcador de diapositiva (la linea de comentario justo antes de cada `\\begin{frame}`):

    % SLIDE <id> | S:<1|2|-> | V:<A|B|C> | T:<segundos>

S es el sistema (1 = oscilador, 2 = billar, - = ninguno), V la voz que presenta y T los
segundos planeados. Con eso el presupuesto de 13 minutos y el reparto entre los tres
expositores (guia 3.1 y 3.2) se pueden verificar mecanicamente.
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

PRES_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(PRES_DIR))

import links  # noqa: E402

DEFAULT_TEX = PRES_DIR / "presentacion.tex"

SLIDE_IDS = (
    "title", "intro_real", "intro_modelo", "impl_verlet", "impl_arquitectura",
    "sim_sistema", "sim_obs1", "sim_obs2", "sim_realizaciones",
    "res_ecm", "res_energia_t", "res_eps", "res_timing", "res_costo", "res_anim_x0",
    "res_fu", "res_t90_x0", "res_anim_sin", "res_ratio", "res_fv_evol", "res_fv_fit",
    "res_fit_error", "res_dens_t90", "res_dens_fu", "res_heatmap", "concl", "gracias",
)
SYSTEM_OF = {sid: "2" for sid in SLIDE_IDS}
SYSTEM_OF.update({"title": "-", "gracias": "-", "res_ecm": "1"})

SECTIONS = ("Introducción", "Implementación", "Simulaciones", "Resultados", "Conclusiones")

# Figura que tiene que mostrar cada diapositiva de resultados.
FIGURE_OF = {
    "res_ecm": "ecm_vs_dt.png",
    "res_energia_t": "energy_vs_time.png",
    "res_eps": "eps_vs_dt.png",
    "res_timing": "timing_vs_N.png",
    "res_costo": "cost_per_particle_step.png",
    "res_fu": "fu_vs_t_N100.png",
    "res_t90_x0": "t90_vs_x0_compare.png",
    "res_ratio": "ratio_vs_t.png",
    "res_fv_evol": "fv_evolution.png",
    "res_fv_fit": "fv_stationary_fit.png",
    "res_fit_error": "fit_error_kbt.png",
    "res_dens_t90": "t90_t100_vs_density.png",
    "res_dens_fu": "success_fu_vs_density.png",
    "res_heatmap": "heatmap_t90.png",
}
# Animaciones de cada diapositiva, de izquierda a derecha.
ANIMATIONS_OF = {
    "res_anim_x0": ("x0_r", "x0_central", "x0_Rmr"),
    "res_anim_sin": ("sin_obstaculos",),
}

TIME_MIN, TIME_MAX = 660, 780
VOICE_MIN, VOICE_MAX = 28.0, 38.0
INTRO_MAX_FRAMES = 3

SYSTEM1_WORDS = re.compile(
    r"\b(oscilador|amortiguad\w*|Beeman|Euler|Gear|ECM|Velocity\s+Verlet)\b", re.IGNORECASE)
FORBIDDEN_PACKAGES = ("media9", "animate", "multimedia", "movie15", "pdfpages", "attachfile")
FORBIDDEN_COMMANDS = ("includemovie", "animategraphics", "movie", "textattachfile", "attachfile")
MEDIA_EXT = re.compile(r"\.(mp4|gif|mov|avi|webm)\b", re.IGNORECASE)
CLOUD_WORDS = re.compile(r"\b(drive|dropbox|onedrive|campus)\b", re.IGNORECASE)
PLACEHOLDERS = (
    ("PENDIENTE", re.compile(r"\bPENDIENTE\b")),
    ("TODO", re.compile(r"\bTODO\b")),
    ("FIXME", re.compile(r"\bFIXME\b")),
    ("XXX", re.compile(r"\bXXX\b")),
    ("TBD", re.compile(r"\bTBD\b")),
    ("lorem", re.compile(r"lorem", re.IGNORECASE)),
    ("???", re.compile(r"\?\?\?")),
)
LOCAL_PATHS = (
    re.compile(r"(?<![A-Za-z0-9])[A-Za-z]:[\\/](?!/)"),
    re.compile(r"/Users/"),
    re.compile(r"/mnt/"),
    re.compile(r"/home/"),
    re.compile(r"Desktop", re.IGNORECASE),
    re.compile(r"OneDrive", re.IGNORECASE),
)

MARKER = re.compile(r"^\s*%\s*SLIDE\s+(\w+)\s*\|\s*S:([12-])\s*\|\s*V:([ABC])\s*\|\s*T:(\d+)\s*$")
MARKER_LOOSE = re.compile(r"^\s*%\s*SLIDE\b")
ANIM_CALL = re.compile(r"\\animacion\s*\{([^{}]*)\}")
INCLUDE_GFX = re.compile(r"\\includegraphics\s*(?:\[[^\]]*\])?\s*\{([^{}]*)\}")


@dataclass
class Problem:
    rule: str
    detail: str


@dataclass
class Frame:
    start: int           # offset de \begin{frame}
    end: int             # offset justo despues de \end{frame}
    body: str            # texto sin comentarios
    marker: tuple | None  # (id, S, V, T) o None
    line: int


@dataclass
class Result:
    problems: list = field(default_factory=list)
    warnings: list = field(default_factory=list)
    stats: dict = field(default_factory=dict)

    def failed(self, rule: str) -> bool:
        return any(p.rule == rule for p in self.problems)


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


def parse_frames(raw: str, clean: str) -> list[Frame]:
    """Frames despues de \\begin{document}, con su marcador SLIDE (None si falta)."""
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
        idx = line - 2  # linea anterior (indice 0-based)
        while idx >= 0 and not raw_lines[idx].strip():
            idx -= 1
        if idx >= 0:
            m = MARKER.match(raw_lines[idx])
            if m:
                marker = (m.group(1), m.group(2), m.group(3), int(m.group(4)))
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
    """R2: cada frame lleva un marcador SLIDE valido con id unico y conocido."""
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
        sid, sysid, _, _ = fr.marker
        if sid in seen:
            problems.append(Problem("R2-markers", f"id repetido: {sid}"))
        seen.add(sid)
        if sid not in SLIDE_IDS:
            problems.append(Problem("R2-markers", f"id desconocido: {sid}"))
        elif sysid != SYSTEM_OF[sid]:
            problems.append(Problem(
                "R2-markers", f"{sid}: S:{sysid} pero corresponde S:{SYSTEM_OF[sid]}"))
    return problems


def rule_order(frames: list[Frame]) -> list[Problem]:
    """R3 (completo): los ids aparecen exactamente en el orden previsto."""
    ids = [f.marker[0] for f in frames if f.marker]
    if ids == list(SLIDE_IDS):
        return []
    for k, (got, want) in enumerate(zip(ids, SLIDE_IDS)):
        if got != want:
            return [Problem("R3-order", f"posicion {k + 1}: aparece {got} y corresponde {want}")]
    if len(ids) < len(SLIDE_IDS):
        return [Problem("R3-order", f"faltan diapositivas desde {SLIDE_IDS[len(ids)]}")]
    return [Problem("R3-order", f"sobran diapositivas desde {ids[len(SLIDE_IDS)]}")]


def rule_system1(frames: list[Frame], partial: bool) -> list[Problem]:
    """R4: una unica diapositiva del Sistema 1, solo con la figura de ECM vs dt."""
    problems = []
    s1 = [f for f in frames if f.marker and f.marker[1] == "1"]
    if len(s1) > 1:
        problems.append(Problem("R4-system1", f"{len(s1)} diapositivas con S:1 (debe ser una)"))
    if not s1:
        if not partial:
            problems.append(Problem("R4-system1", "no hay diapositiva con S:1"))
        return problems
    body = s1[0].body
    if "ecm_vs_dt" not in body or not INCLUDE_GFX.search(body):
        problems.append(Problem("R4-system1", "la diapositiva S:1 no incluye ecm_vs_dt"))
    for bad in (r"\animacion", "itemize", "enumerate", "tikzpicture"):
        if bad in body:
            problems.append(Problem("R4-system1", f"la diapositiva S:1 contiene {bad}"))
    return problems


def rule_system1_words(clean: str, frames: list[Frame]) -> list[Problem]:
    """R5: fuera de la diapositiva S:1 no aparece vocabulario del Sistema 1."""
    spans = [(f.start, f.end) for f in frames if f.marker and f.marker[1] == "1"]
    problems = []
    for m in SYSTEM1_WORDS.finditer(clean):
        if any(a <= m.start() < b for a, b in spans):
            continue
        problems.append(Problem("R5-words", f"'{m.group(0)}' fuera de la diapositiva S:1 "
                                            f"(linea {line_of(clean, m.start())})"))
    return problems


def rule_forbidden(clean: str) -> list[Problem]:
    """R6: sin captions, paquetes de medios, comandos de video ni links a la nube."""
    problems = []
    for m in re.finditer(r"\\caption(?![A-Za-z])", clean):
        problems.append(Problem("R6-forbidden", f"\\caption (linea {line_of(clean, m.start())}): "
                                                f"la guia 1.7 prohibe leyendas bajo las figuras"))
    for m in re.finditer(r"\\usepackage\s*(?:\[[^\]]*\])?\s*\{([^{}]*)\}", clean):
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
    for sub in ("figuras", "frames"):
        for cand in (name, name + ".png"):
            if (base / sub / cand).is_file():
                return True
    return False


def rule_assets(clean: str, frames: list[Frame], base: Path, allow_missing_figures: bool):
    """R7: ids de animacion validos, fotogramas y figuras presentes, mapa de diapositivas."""
    problems, warnings = [], []
    doc = document_start(clean)
    calls = [(m.group(1), m.start()) for m in ANIM_CALL.finditer(clean, doc)]
    for cid, off in calls:
        if cid not in links.CASE_IDS:
            problems.append(Problem("R7-assets", f"\\animacion{{{cid}}}: id desconocido "
                                                 f"(validos: {', '.join(links.CASE_IDS)})"))
        elif not (base / "frames" / f"{cid}.png").is_file():
            problems.append(Problem("R7-assets", f"falta el fotograma frames/{cid}.png"))
    for m in INCLUDE_GFX.finditer(clean, doc):
        target = m.group(1).strip()
        if "#" in target or _figure_exists(target, base):
            continue
        detail = f"falta la figura {target} (figuras/ o frames/)"
        (warnings if allow_missing_figures else problems).append(Problem("R7-assets", detail))
    for fr in frames:
        if not fr.marker:
            continue
        sid = fr.marker[0]
        if sid in FIGURE_OF:
            targets = [Path(t.strip()).name for t in INCLUDE_GFX.findall(fr.body)]
            if FIGURE_OF[sid] not in targets and FIGURE_OF[sid][:-4] not in targets:
                problems.append(Problem("R7-assets",
                                        f"{sid}: debe incluir {FIGURE_OF[sid]}"))
        if sid in ANIMATIONS_OF:
            got = tuple(ANIM_CALL.findall(fr.body))
            if got != ANIMATIONS_OF[sid]:
                problems.append(Problem(
                    "R7-assets", f"{sid}: \\animacion debe llamarse con "
                                 f"{', '.join(ANIMATIONS_OF[sid])} en ese orden (hay: "
                                 f"{', '.join(got) or 'ninguna'})"))
    return problems, warnings, calls


def rule_placeholders(clean: str) -> list[Problem]:
    """R8: ningun marcador de pendiente fuera de los comentarios."""
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
            voices[fr.marker[2]] += fr.marker[3]
    return voices


def rule_budget(frames: list[Frame]) -> list[Problem]:
    """R9 (completo): 660 a 780 s en total y cada voz entre 28 y 38 por ciento."""
    voices = voice_seconds(frames)
    total = sum(voices.values())
    problems = []
    if not TIME_MIN <= total <= TIME_MAX:
        problems.append(Problem("R9-budget", f"tiempo total {total} s fuera de "
                                             f"[{TIME_MIN}, {TIME_MAX}] s"))
    if total > 0:
        for v, secs in voices.items():
            share = 100.0 * secs / total
            if not VOICE_MIN <= share <= VOICE_MAX:
                problems.append(Problem("R9-budget", f"la voz {v} tiene {share:.1f} % del "
                                                     f"tiempo (debe estar entre {VOICE_MIN:.0f} "
                                                     f"y {VOICE_MAX:.0f} %)"))
    return problems


def rule_sections(clean: str, frames: list[Frame], partial: bool) -> list[Problem]:
    """R10: secciones de la guia, en orden, sin plantilla numerada."""
    doc = document_start(clean)
    found = [(m.group(1).strip(), m.start())
             for m in re.finditer(r"\\section\s*(?:\[[^\]]*\])?\s*\{([^{}]*)\}", clean[doc:])]
    found = [(t, off + doc) for t, off in found]
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
        problems.append(Problem("R10-sections", "plantilla con secciones numeradas (guia 1.13)"))
    if not re.search(r"\\AtBeginSection", clean):
        problems.append(Problem("R10-sections", "falta \\AtBeginSection (diapositiva solo con "
                                                "el titulo de cada seccion)"))
    if not partial and titles == list(SECTIONS):
        def frames_in(title):
            k = titles.index(title)
            lo = found[k][1]
            hi = found[k + 1][1] if k + 1 < len(found) else len(clean)
            return [f for f in frames if lo <= f.start < hi]
        intro = frames_in("Introducción")
        if len(intro) > INTRO_MAX_FRAMES:
            problems.append(Problem("R10-sections", f"Introducción tiene {len(intro)} "
                                                    f"diapositivas (maximo {INTRO_MAX_FRAMES})"))
        concl = [f for f in frames_in("Conclusiones") if f.marker and f.marker[3] > 0]
        if len(concl) != 1:
            problems.append(Problem("R10-sections", f"Conclusiones debe tener exactamente una "
                                                    f"diapositiva con contenido (hay {len(concl)})"))
    return problems


def rule_paths(raw: str) -> list[Problem]:
    """R11: sin rutas locales ni nombres de maquina (ni siquiera en comentarios)."""
    problems = []
    for rx in LOCAL_PATHS:
        for m in rx.finditer(raw):
            problems.append(Problem("R11-paths", f"patron de ruta local '{m.group(0)}' en la "
                                                 f"linea {line_of(raw, m.start())}"))
    return problems


def rule_notation(clean: str) -> list[Problem]:
    """R12 (aviso): 1e-4 o punto decimal en el texto; la guia 1.9 pide 10^x y coma."""
    doc = document_start(clean)
    text = clean[doc:]
    text = re.sub(r"\\begin\{tikzpicture\}.*?\\end\{tikzpicture\}", " ", text, flags=re.DOTALL)
    for rx in (INCLUDE_GFX, ANIM_CALL):
        text = rx.sub(" ", text)
    text = re.sub(r"\\url\s*\{[^{}]*\}", " ", text)
    text = re.sub(r"\[[^\]]*\]", " ", text)
    text = re.sub(r"\d+(?:\.\d+)?\s*(?:\\(?:textwidth|textheight|linewidth|columnwidth)|em|ex|pt|"
                  r"cm|mm|bp)\b", " ", text)
    text = re.sub(r"\\(?:definecolor|vspace|hspace|setlength|hypersetup)\*?\s*\{[^{}]*\}"
                  r"(?:\s*\{[^{}]*\})?", " ", text)
    # Etiquetas que no son numeros: estudios 2.1a a 2.4b, g++ 13.3 y el codigo de la materia.
    text = re.sub(r"\b2\.[1-4][ab]?\b|\b13\.3\b|\b72\.25\b", " ", text)
    out = []
    for m in re.finditer(r"(?<![A-Za-z0-9_.])\d+(?:\.\d+)?[eE][-+]?\d+\b", text):
        out.append(Problem("R12-notation", f"notacion '{m.group(0)}': usar 10^x (guia 1.9)"))
    for m in re.finditer(r"\d\.\d", text):
        ctx = text[max(0, m.start() - 8):m.end() + 8].replace("\n", " ")
        out.append(Problem("R12-notation", f"punto decimal en '{ctx.strip()}': usar coma"))
    return out


def rule_preamble(clean: str) -> list[Problem]:
    """R13: el preambulo define el modo, \\animacion, \\params y carga links.tex."""
    doc = clean.find("\\begin{document}")
    pre = clean[:doc] if doc >= 0 else clean
    checks = (
        (r"\\providecommand\s*\{\\modo\}\s*\{entrega\}", "\\providecommand{\\modo}{entrega}"),
        (r"\\newcommand\s*\{\\animacion\}\s*\[2\]", "\\newcommand{\\animacion}[2]"),
        (r"\\newcommand\s*\{\\params\}", "\\newcommand{\\params}"),
        (r"\\input\s*\{links(?:\.tex)?\}", "\\input{links.tex}"),
        (r"\\graphicspath\s*\{.*frames/.*\}", "\\graphicspath con frames/"),
        (r"\\graphicspath\s*\{.*figuras/.*\}", "\\graphicspath con figuras/"),
        (r"\\documentclass\s*\[[^\]]*aspectratio=169[^\]]*\]\s*\{beamer\}",
         "\\documentclass[aspectratio=169]{beamer}"),
    )
    return [Problem("R13-preamble", f"el preambulo no tiene {label}")
            for rx, label in checks if not re.search(rx, pre, re.DOTALL)]


# --------------------------------------------------------------------------- agregado

def lint(text: str, partial: bool = False, allow_missing_figures: bool = False,
         base: Path = PRES_DIR) -> Result:
    base = Path(base)
    raw = text.replace("\r\n", "\n")
    clean = strip_comments(raw)
    frames = parse_frames(raw, clean)
    res = Result()
    res.problems += rule_balance(clean)
    res.problems += rule_markers(raw, frames)
    if not partial:
        res.problems += rule_order(frames)
    res.problems += rule_system1(frames, partial)
    res.problems += rule_system1_words(clean, frames)
    res.problems += rule_forbidden(clean)
    p7, w7, _ = rule_assets(clean, frames, base, allow_missing_figures)
    res.problems += p7
    res.warnings += w7
    res.problems += rule_placeholders(clean)
    if not partial:
        res.problems += rule_budget(frames)
    res.problems += rule_sections(clean, frames, partial)
    res.problems += rule_paths(raw)
    res.warnings += rule_notation(clean)
    res.problems += rule_preamble(clean)
    if not partial:
        calls = [m.group(1) for m in ANIM_CALL.finditer(clean, document_start(clean))]
        want = [c for ids in ANIMATIONS_OF.values() for c in ids]
        if calls != want:
            res.problems.append(Problem("R7-assets", f"las llamadas a \\animacion deben ser "
                                                     f"{want} en ese orden (hay {calls})"))
    voices = voice_seconds(frames)
    res.stats = {
        "frames": len(frames),
        "content": sum(1 for f in frames if f.marker and f.marker[3] > 0),
        "time": sum(voices.values()),
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
    lines.append(f"LINT OK{tag} frames={s['frames']} content={s['content']} time={s['time']}s "
                 f"A={s['A']} B={s['B']} C={s['C']} warnings={len(res.warnings)}")
    return lines


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--partial", action="store_true",
                        help="esqueleto o borrador: no exige el deck completo ni el presupuesto")
    parser.add_argument("--allow-missing-figures", action="store_true",
                        help="una figura ausente es un aviso (el plan 06-04 las exige)")
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
