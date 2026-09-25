"""Figuras propias de la presentacion; las demas se toman tal cual de data/.

Sin titulo dentro de la figura (guia 1.7): el instante y los parametros van al
costado, escritos en la diapositiva. Ejes rotulados en palabras (guia 1.8) y
toda la letra en 20 (guia 1.8, correccion de la primera consulta).

    python3 presentacion/generar_figuras.py                 # todas, desde TP3/
    python3 presentacion/generar_figuras.py area_fija       # solo esa figura

Figuras: fotogramas (necesita la configuracion elegida en data/obstacles/),
ajuste_D (necesita `make diffusion`) y las tiras de casos area_fija, particion,
bloque y forma (no necesitan datos).
"""
import csv
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, "python")
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Circle, Rectangle
from matplotlib.ticker import NullFormatter, ScalarFormatter

from animate import FRESH_COLOR, GOAL_COLOR, OBSTACLE_COLOR, USED_COLOR
from block_shape_search import half_width_profile, shaped_block
from central_block_search import fill_wall_pockets
from explore_obstacles import fixed_area_candidates
from final_comparison import block_candidate, partition_candidate
from obstacle_experiments import LENGTH, WIDTH
from tp3io import read_static, read_trajectory

FS = 20
OUT = Path("presentacion")
RUNS = Path("data/presentacion")
# Configuracion elegida (reloj de arena); coincide con la entregada.
CONFIG = "data/obstacles/central_blocks/chosen_hourglass_config.txt"
GOAL_SIZE = 0.20   # m, valor por defecto del motor (--goal-size)
SEED = 42
T_FRAME = 8.0   # s: ya hay particulas usadas, pero todavia lejos de t90
T_DCM = 1.5     # s: fin del DCM graficado, poco despues del tramo ajustado
# Tercera consulta: D sale de la primera parte del DCM, desde que arranca hasta
# ~10^0 s (regimen difusivo inicial), no del tramo que detecta diffusion.py.
TRAMO_D = (0.0, 1.0)


def correr(tag: str, extra: list[str]):
    """Trayectoria corta de N=100 para el fotograma; se reutiliza si ya existe."""
    static = RUNS / f"{tag}_static.txt"
    traj = RUNS / f"{tag}_traj.txt"
    if not traj.exists():
        RUNS.mkdir(parents=True, exist_ok=True)
        subprocess.run(["./tp3", "--N", "100", "--tmax", "30", "--seed", str(SEED),
                        "--static-output", str(static), "--trajectory", str(traj),
                        "--output-every-events", "25", "--csv", *extra],
                       check=True, stdout=subprocess.DEVNULL)
    return read_static(static), read_trajectory(traj)


def mesa(system, frame=None):
    fig, ax = plt.subplots(figsize=(8.6, 5.0))
    L, W = system.length, system.width
    ax.add_patch(Rectangle((0, 0), L, W, facecolor="#f5f1e8", edgecolor="#252525",
                           linewidth=2.0, zorder=0))
    g0, g1 = W / 2 - system.goal_size / 2, W / 2 + system.goal_size / 2
    for x in (0.0, L):
        ax.plot([x, x], [g0, g1], color=GOAL_COLOR, linewidth=7, solid_capstyle="butt",
                zorder=2)
    for x, y, R in system.obstacles:
        ax.add_patch(Circle((x, y), R, facecolor=OBSTACLE_COLOR, edgecolor="#30343b",
                            linewidth=1.2, zorder=3))
    if frame is not None:
        for i, (x, y) in enumerate(frame.positions):
            color = USED_COLOR if frame.used[i] else FRESH_COLOR
            ax.add_patch(Circle((x, y), system.radii[i], facecolor=color,
                                edgecolor="white", linewidth=0.4, zorder=4))
    ax.set_xlim(-0.02 * L, 1.02 * L)
    ax.set_ylim(-0.03 * W, 1.03 * W)
    ax.set_aspect("equal")
    ax.set_xlabel("Posición x (m)", fontsize=FS)
    ax.set_ylabel("Posición y (m)", fontsize=FS)
    ax.tick_params(labelsize=FS)
    return fig


def tira_de_casos(nombre: str, casos):
    """Imagen del caso para una diapositiva de barrido: mesas en una grilla 2x2.

    `casos` es una lista de (rotulo, obstaculos). Sin ejes: la geometria se lee
    sola y el rotulo dice que varia. Va en la columna derecha de la diapositiva;
    el tamano hace que la letra 20 quede a la misma escala que los graficos.
    """
    filas = (len(casos) + 1) // 2
    fig, axes = plt.subplots(filas, 2, figsize=(5.4, 2.0 * filas))
    g0, g1 = WIDTH / 2 - GOAL_SIZE / 2, WIDTH / 2 + GOAL_SIZE / 2
    for ax in axes.flat[len(casos):]:
        ax.set_axis_off()
    for ax, (rotulo, obstaculos) in zip(axes.flat, casos):
        ax.add_patch(Rectangle((0, 0), LENGTH, WIDTH, facecolor="#f5f1e8",
                               edgecolor="#252525", linewidth=1.5, zorder=0))
        for x in (0.0, LENGTH):
            ax.plot([x, x], [g0, g1], color=GOAL_COLOR, linewidth=5,
                    solid_capstyle="butt", zorder=2)
        for x, y, R in obstaculos:
            ax.add_patch(Circle((x, y), R, facecolor=OBSTACLE_COLOR, edgecolor="#30343b",
                                linewidth=0.8, zorder=3))
        ax.set_xlim(-0.03 * LENGTH, 1.03 * LENGTH)
        ax.set_ylim(-0.04 * WIDTH, 1.04 * WIDTH)
        ax.set_aspect("equal")
        ax.set_axis_off()
        ax.set_title(rotulo, fontsize=FS, pad=4)
    fig.subplots_adjust(wspace=0.08, hspace=0.35)
    print(guardar(fig, nombre))


def casos_area_fija():
    """K = 1, 2, 4, 8, 16 obstaculos con area total fija (explore_obstacles.py)."""
    tira_de_casos("casos_area_fija.png",
                  [(f"K = {len(c.obstacles)}", c.obstacles) for c in fixed_area_candidates()])


def casos_particion():
    """Particion central: circulos chicos (pared fina) -> grandes (pared gruesa)."""
    tira_de_casos("casos_particion.png",
                  [(f"K = {k}", partition_candidate(k).obstacles) for k in (19, 10, 4, 2)])


def casos_bloque():
    """Bloque de columnas con los huecos tapados: engorda, pasa por la elegida y sigue."""
    tira_de_casos("casos_bloque.png",
                  [(f"{c} columna" + ("s" if c > 1 else ""),
                    fill_wall_pockets(block_candidate(c).obstacles)) for c in (1, 4, 7, 10)])


def casos_forma():
    """Cara del bloque: plana (base), en V y parabolica (block_shape_search.py)."""
    tira_de_casos("casos_forma.png", [
        ("Cara plana", fill_wall_pockets(block_candidate(7).obstacles)),
        ("En V", shaped_block(7, half_width_profile(0.22, 0.54, "v"))),
        ("Parabólica", shaped_block(7, half_width_profile(0.32, 0.54, "parab"))),
        ("Elegida", shaped_block(10, half_width_profile(0.28, 0.50, "v"))),
    ])


def guardar(fig, nombre: str):
    out = OUT / nombre
    fig.savefig(out, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return out


# Estudios de una variable (python/one_variable_studies.py): casos animados.
UNA_VARIABLE = "data/one_variable/{}/configs/{}.txt"
CASOS_ANIMADOS = [
    ("vacia", []),
    ("elegida", ["--config", CONFIG]),
    ("radio_R03", ["--config", UNA_VARIABLE.format("radio", "radio_R03")]),
    ("radio_R30", ["--config", UNA_VARIABLE.format("radio", "radio_R30")]),
    ("reloj_hc04", ["--config", UNA_VARIABLE.format("reloj", "reloj_hc04")]),
    ("reloj_hc40", ["--config", UNA_VARIABLE.format("reloj", "reloj_hc40")]),
]


def casos_radio():
    """Obstaculo central de radio creciente (one_variable_studies.py)."""
    tira_de_casos("casos_radio.png",
                  [(f"R = {R:.2f} m".replace(".", ","), ((LENGTH / 2, WIDTH / 2, R),))
                   for R in (0.03, 0.12, 0.21, 0.30)])


def casos_reloj():
    """Reloj de arena con h_w fijo y h_c creciente (one_variable_studies.py)."""
    tira_de_casos("casos_reloj.png",
                  [(f"$h_c$ = {hc:.2f} m".replace(".", ","),
                    shaped_block(10, half_width_profile(hc, 0.50, "v")))
                   for hc in (0.04, 0.16, 0.28, 0.40)])


def fotogramas():
    for tag, extra in CASOS_ANIMADOS:
        system, frames = correr(tag, extra)
        frame = min(frames, key=lambda f: abs(f.time - T_FRAME))
        out = guardar(mesa(system, frame), f"frame_{tag}.png")
        print(f"{out}  (t = {frame.time:.2f} s, Fu = {frame.goals / len(frame.used):.2f})")
    system, _ = correr("elegida", ["--config", CONFIG])
    print(guardar(mesa(system), "configuracion_elegida.png"))


def _fila_difusion(nombre: str) -> dict:
    with open("data/diffusion/summary.csv", newline="") as fh:
        return next(r for r in csv.DictReader(fh) if r["name"] == nombre)


def dcm_elegida():
    """DCM de la configuracion elegida y su pendiente local, con el tramo ajustado.

    Segunda consulta: una vez elegida la configuracion, el DCM se muestra solo
    para ella, y D sale del regimen inicial (antes de que la caja lo sature).
    """
    t0, t1 = TRAMO_D
    t, dcm = np.loadtxt("data/diffusion/msd/hourglass.csv", delimiter=",", skiprows=1).T
    # Solo la primera parte, antes de que el DCM sature.
    visible = (t > 0) & (t <= T_DCM)
    t, dcm = t[visible], dcm[visible]
    # Pendiente local en log-log con ventanas de 7 muestras (desde el inicio).
    lt, ld = np.log(t), np.log(dcm)
    alpha = np.array([np.polyfit(lt[max(0, i - 3):i + 4], ld[max(0, i - 3):i + 4], 1)[0]
                      for i in range(t.size)])
    t0 = max(t0, t[0])

    fig, (a1, a2) = plt.subplots(2, 1, figsize=(9.5, 6.0), sharex=True,
                                 gridspec_kw={"height_ratios": [1.6, 1]})
    for ax in (a1, a2):
        ax.axvspan(t0, t1, color="#d6e6f5", zorder=0)
    a1.loglog(t, dcm, color="#1f5fa8", lw=2.2)
    a1.set_ylabel("DCM (m$^2$)", fontsize=FS)
    # Menos de dos decadas: solo 10^-3 y 10^-2 rotulados, sin rotulos menores.
    a1.set_ylim(1e-3, 4e-2)
    a1.yaxis.set_minor_formatter(NullFormatter())
    a2.semilogx(t, alpha, color="#1f5fa8", lw=2.0)
    a2.axhline(1.0, color="black", ls="--", lw=1.2)
    a2.set_ylim(-0.3, 2.3)
    a2.set_yticks([0, 1, 2])
    a2.set_ylabel(r"$\alpha$", fontsize=FS)
    a2.set_xlabel("Tiempo (s)", fontsize=FS)
    a2.set_xlim(0.05, T_DCM)
    for ax in (a1, a2):
        ax.tick_params(labelsize=FS)
    fig.tight_layout()
    print(guardar(fig, "dcm_elegida.png"))


def ajuste_D(nombre: str = "hourglass"):
    """Guia 2.4.5 / Teorica 0: error cuadratico del ajuste en funcion de D.

    Ajuste DCM = 4 D t + b en el tramo inicial TRAMO_D, con ordenada libre b.
    Con b fijo en su optimo, E(D) tiene el minimo exactamente en el D ajustado
    (dE/dD = 0 en el optimo conjunto).
    """
    from diffusion import _linear_fit
    t0, t1 = TRAMO_D
    t, dcm = np.loadtxt(f"data/diffusion/msd/{nombre}.csv", delimiter=",", skiprows=1).T
    tramo = (t >= t0 - 1e-9) & (t <= t1 + 1e-9)
    pendiente, b, pendiente_std, r2 = _linear_fit(t[tramo], dcm[tramo])
    D_fit = pendiente / 4
    print(f"D = {D_fit:.6f} +- {pendiente_std / 4:.6f} m^2/s  (R^2 = {r2:.4f})")

    Ds = np.linspace(0.6 * D_fit, 1.4 * D_fit, 801)
    E = np.array([np.sum((dcm[tramo] - 4 * D * t[tramo] - b) ** 2) for D in Ds])
    D_min = Ds[np.argmin(E)]
    print(f"D reportado = {D_fit:.6f}  |  argmin E(D) = {D_min:.6f}  "
          f"(tramo {t0}-{t1} s, {tramo.sum()} puntos)")

    fig, (a1, a2) = plt.subplots(1, 2, figsize=(11.0, 5.2))
    vis = t <= 3.0
    a1.plot(t[vis & ~tramo], dcm[vis & ~tramo], "o", color="0.65", ms=5)
    a1.plot(t[tramo], dcm[tramo], "o", color="#1f5fa8", ms=6)
    tt = np.linspace(t0, t1, 50)
    a1.plot(tt, 4 * D_fit * tt + b, "-", color="#c0392b", lw=2.5)
    a1.set_xlabel("Tiempo (s)", fontsize=FS)
    a1.set_ylabel("DCM (m$^2$)", fontsize=FS)

    a2.plot(Ds, E, "-", color="#1f5fa8", lw=2.5)
    a2.plot([D_min], [E.min()], "o", color="#c0392b", ms=10)
    a2.axvline(D_min, color="#c0392b", ls="--", lw=1.5)
    a2.set_xlabel("D (m$^2$/s)", fontsize=FS)
    a2.set_ylabel("Error cuadrático E (m$^4$)", fontsize=FS)

    for ax in (a1, a2):
        ax.tick_params(labelsize=FS)
        fmt = ScalarFormatter(useMathText=True)
        fmt.set_powerlimits((-2, 2))
        ax.yaxis.set_major_formatter(fmt)
        ax.yaxis.get_offset_text().set_fontsize(FS)
    fmt = ScalarFormatter(useMathText=True)
    fmt.set_powerlimits((-2, 2))
    a2.xaxis.set_major_formatter(fmt)
    a2.xaxis.get_offset_text().set_fontsize(FS)
    fig.tight_layout()
    print(guardar(fig, f"ajuste_D_{nombre}.png"))


FIGURAS = {"fotogramas": fotogramas, "radio": casos_radio, "reloj": casos_reloj, "ajuste_D": ajuste_D, "dcm": dcm_elegida, "area_fija": casos_area_fija,
           "particion": casos_particion, "bloque": casos_bloque, "forma": casos_forma}

if __name__ == "__main__":
    pedidas = sys.argv[1:] or list(FIGURAS)
    desconocidas = set(pedidas) - set(FIGURAS)
    if desconocidas:
        raise SystemExit(f"figuras desconocidas: {sorted(desconocidas)}; opciones: {list(FIGURAS)}")
    for nombre in pedidas:
        FIGURAS[nombre]()
