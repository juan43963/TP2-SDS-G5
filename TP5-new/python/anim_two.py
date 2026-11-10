"""Animacion didactica del caso de 2 particulas: que pasa con la velocidad despues del choque.

Responde, paso a paso, la pregunta del profe: "despues del choque, entre 0 y 0.1 s hubo una traslacion:
¿cual fue la regla?, ¿como apuntaban las velocidades justo despues del choque?"

Lee SOLO el archivo de texto TP5_TRAJECTORY (generado por `tp5_scenario two`). El instante del choque y las
posiciones en los eventos (t_c y t_c + 0.1) se reconstruyen del propio archivo (antes del choque el vuelo es
recto, y entre t_c y t_c + 0.1 tambien) y se verifican contra el primer cuadro posterior al choque.

Escenas (cada una introduce UN concepto; las ecuaciones se escriben en sintaxis LaTeX de matplotlib):
  A) antes del choque        vienen hacia la puerta con v = v_d * e_target
  B1) hacia donde esta el otro            n
  B2) alejarse del otro                   n_alejar
  B3) no perder el rumbo a la puerta      e_target
  B4) sumar las dos intenciones           s = n_alejar + e_target
  B5) ajustar la rapidez                  v_nueva = v_d * s / |s|
  B6) resultado y por que la regla
  C) 0 -> 0.1 s              traslacion recta con esa velocidad
  D) 0.1 s                   la deseada vuelve a la puerta; la real NO salta
  E) despues                 la real converge a la deseada con inercia

Velocidad REAL en negro, DESEADA en verde.

Uso: python anim_two.py data/two.txt out.gif
"""
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.animation import FuncAnimation, PillowWriter
from matplotlib.patches import Circle

from trajectory_stream import iter_frames, read_header, header_float

DOOR = np.array([5.0, 0.0])
DOOR_W = 0.8
COLORS = ["#1f4e79", "#c0392b"]
NAMES = ["A", "B"]
BLUE, GREEN, ORANGE = "#2980b9", "#27ae60", "#e67e22"


def unit(v):
    return v / np.linalg.norm(v)


def load(path):
    header = read_header(path)
    vd = header_float(header, "vd", path)
    pulse = header_float(header, "steer_dt", path)
    tau = header_float(header, "tau", path)
    ts, xs, vs, rs = [], [], [], []
    for frame in iter_frames(path):
        rows = frame.rows[np.argsort(frame.rows[:, 0])]
        ts.append(frame.t)
        xs.append(rows[:, 1:3])
        vs.append(rows[:, 3:5])
        rs.append(rows[:, 5])
    return vd, pulse, tau, np.array(ts), np.array(xs), np.array(vs), np.array(rs)


def contact_time(x0, v0, r):
    """Primer t >= 0 con |(xB - xA) + (vB - vA) t| = rA + rB (vuelo recto antes del choque)."""
    d0 = x0[1] - x0[0]
    dv = v0[1] - v0[0]
    a = dv @ dv
    b = 2 * d0 @ dv
    c = d0 @ d0 - (r[0] + r[1]) ** 2
    disc = b * b - 4 * a * c
    return (-b - np.sqrt(disc)) / (2 * a)


def v2(v):
    """Vector como texto matematico: (+0.05, -1.00)."""
    return r"(%+.2f,\ %+.2f)" % (v[0] + 0.0, v[1] + 0.0)


def main(path, out):
    vd, pulse, tau, ts, xs, vs, rs = load(path)
    r = rs[0]
    x0, v0 = xs[0], vs[0]
    t_c = contact_time(x0, v0, r)
    x_c = x0 + v0 * t_c  # posiciones en el choque
    n = unit(x_c[1] - x_c[0])
    away = [-n, n]
    e_t = [unit(DOOR - x_c[i]) for i in range(2)]
    ssum = [away[i] + e_t[i] for i in range(2)]
    s_len = [np.linalg.norm(ssum[i]) for i in range(2)]
    s_hat = [ssum[i] / s_len[i] for i in range(2)]
    v_post = [vd * s_hat[i] for i in range(2)]
    x_end = [x_c[i] + v_post[i] * pulse for i in range(2)]  # posiciones a t_c + 0.1
    # verificacion contra el archivo (guarda 5 decimales): velocidad y posicion del primer cuadro posterior al choque
    k_after = int(np.argmax(ts > t_c))
    assert max(np.linalg.norm(vs[k_after][i] - v_post[i]) for i in range(2)) < 5e-5, "la regla no coincide con el archivo"
    assert max(np.linalg.norm(xs[k_after][i] - (x_c[i] + v_post[i] * (ts[k_after] - t_c))) for i in range(2)) < 5e-5
    t_end = t_c + pulse
    k_end = int(np.argmin(np.abs(ts - t_end)))

    fig = plt.figure(figsize=(12.5, 6.8))
    ax = fig.add_axes([0.05, 0.08, 0.47, 0.80])
    tx = fig.add_axes([0.54, 0.04, 0.45, 0.88])
    tx.axis("off")

    # ------------------------------------------------------------------ dibujo
    def scene(view):
        ax.clear()
        if view == "full":
            ax.set_xlim(3.4, 6.6)
            ax.set_ylim(-0.7, 4.6)
            ax.plot([3.4, 5.0 - DOOR_W / 2], [0, 0], color="#555", lw=4)
            ax.plot([5.0 + DOOR_W / 2, 6.6], [0, 0], color="#555", lw=4)
            ax.plot(*DOOR, marker="x", color=GREEN, ms=9)
            ax.text(5.05, -0.35, "puerta (target)", color=GREEN, fontsize=9)
        elif view == "rule":
            ax.set_xlim(3.3, 6.25)
            ax.set_ylim(2.3, 4.35)
        else:
            ax.set_xlim(4.15, 5.85)
            ax.set_ylim(3.05, 4.25)
        ax.set_aspect("equal")
        ax.set_xlabel("x [m]")
        ax.set_ylabel("y [m]")

    def body(pos, who=(0, 1), alpha=0.4):
        for i in who:
            ax.add_patch(Circle(pos[i], r[i], facecolor=COLORS[i], alpha=alpha, edgecolor=COLORS[i]))
            ax.text(*pos[i], NAMES[i], ha="center", va="center", fontsize=10)

    def vec(origin, v, color, lw=2.6, ls="-", alpha=1.0, label=None, off=(0.0, 0.0), fs=13):
        ax.annotate("", xy=np.asarray(origin) + v, xytext=origin,
                    arrowprops=dict(arrowstyle="-|>", color=color, lw=lw, ls=ls, alpha=alpha, shrinkA=0, shrinkB=0))
        if label:
            mid = np.asarray(origin) + 0.5 * np.asarray(v)
            ax.text(mid[0] + off[0], mid[1] + off[1], label, color=color, fontsize=fs, ha="center", va="center",
                    fontweight="bold")

    def real_des(pos, vel, des, scale=0.5, lw_real=1.8):
        for i in range(2):
            if des is not None:
                ax.annotate("", xy=pos[i] + scale * des[i] / vd, xytext=pos[i],
                            arrowprops=dict(arrowstyle="-|>", color=GREEN, lw=3.5, alpha=0.7))
            if vel is not None:
                ax.annotate("", xy=pos[i] + scale * vel[i] / vd, xytext=pos[i],
                            arrowprops=dict(arrowstyle="-|>", color="black", lw=lw_real))

    def ghost(pos, label):
        for i in range(2):
            ax.add_patch(Circle(pos[i], r[i], facecolor="none", edgecolor=COLORS[i], ls="--", lw=1.2))
        ax.text(pos[0][0], pos[0][1] - r[0] - 0.09, label, fontsize=8, color="gray", ha="center")

    def legend_vd():
        ax.plot([], [], color="black", lw=1.8, label=r"velocidad real $\vec v$")
        ax.plot([], [], color=GREEN, lw=3.5, alpha=0.7, label=r"velocidad deseada $\vec w$")
        ax.legend(loc="upper right", fontsize=8)

    def text(lines, head):
        """Panel de texto: una linea por elemento; '' = hueco; las que tienen $...$ van en mathtext."""
        tx.clear()
        tx.axis("off")
        tx.text(0, 1.0, head, fontsize=13.5, fontweight="bold", va="top")
        y = 0.90
        for line in lines:
            if line == "":
                y -= 0.025
                continue
            tall = "dfrac" in line
            big = line.startswith("##")
            if big:
                line = line[2:]
            tx.text(0, y, line, fontsize=15 if big else 12, va="top")
            y -= 0.125 if tall else (0.09 if big else 0.062)

    # ------------------------------------------------------------------ secuencia
    seq = []
    seq += [("A", 0.0)] * 45
    for name in ("B1", "B2", "B3", "B4", "B5", "B6"):
        seq += [(name, t_c)] * 75
    steps_c = 24
    seq += [("C", t_c + pulse * k / steps_c) for k in range(steps_c + 1)]
    seq += [("C", t_end)] * 30
    seq += [("D", t_end)] * 90
    t_e1 = t_end + 2.0
    seq += [("E", ts[k]) for k in range(k_end + 1, len(ts), 3) if ts[k] <= t_e1]

    nA = r"$\hat n_{alejar}$"

    def draw(f):
        phase, t = seq[f]
        fig.suptitle("Después del choque en EDMD: ¿qué velocidad tienen y por qué?", fontsize=13)

        if phase == "A":
            scene("zoom")
            body(x0)
            real_des(x0, v0, v0, scale=0.55)
            legend_vd()
            text(["Cada agente quiere llegar a la puerta:",
                  "va en línea recta con rapidez $v_d = %.1f$ m/s." % vd,
                  r"##$\vec v = v_d\,\hat e_{target}$",
                  r"$\hat e_{target}$: flecha de largo 1 hacia la puerta",
                  "(el sombrerito ^ significa «largo 1»).",
                  "",
                  "Aquí: $\\vec v_A=%s$ m/s, $\\vec v_B=%s$ m/s." % (v2(v0[0]), v2(v0[1])),
                  "Están a 1 mm: se tocan en $t_c=%.4f$ s." % t_c],
                 "A) Antes del choque")
            ax.set_title("t = 0   (vienen en línea recta hacia la puerta)", loc="left", fontsize=10)

        elif phase == "B1":
            scene("rule")
            body(x_c)
            vec(x_c[0], n * 1.0, BLUE, label=r"$\hat n$", off=(0, 0.12))
            text(["Para alejarnos hay que saber dónde está el otro.",
                  "",
                  r"##$\hat n = \dfrac{\vec x_B-\vec x_A}{|\vec x_B-\vec x_A|}$",
                  "• $\\vec x_B-\\vec x_A$: flecha del centro de A al de B.",
                  "• $|\\ldots|$ es su largo; al dividir queda de largo 1.",
                  "",
                  "Aquí: $\\hat n=%s$" % v2(n),
                  "(B está justo a la derecha de A)."],
                 "B1) ¿Dónde está el otro? ($\\hat n$)")
            ax.set_title("t = %.4f s: se tocan" % t_c, loc="left", fontsize=10)

        elif phase == "B2":
            scene("rule")
            body(x_c)
            vec(x_c[0], away[0] * 1.0, BLUE, label=r"$\hat n_{alejar,A}$", off=(0, 0.12))
            vec(x_c[1], away[1] * 1.0, BLUE, label=r"$\hat n_{alejar,B}$", off=(0, 0.12))
            text(["Cada uno se aleja del otro: va para el lado",
                  "contrario a donde lo está mirando.",
                  "",
                  r"##$\hat n_{alejar,A} = -\hat n = %s$" % v2(away[0]),
                  r"##$\hat n_{alejar,B} = +\hat n = %s$" % v2(away[1]),
                  "",
                  "A se va hacia la izquierda, B hacia la derecha."],
                 "B2) Alejarse del otro ($\\hat n_{alejar}$)")
            ax.set_title("t = %.4f s" % t_c, loc="left", fontsize=10)

        elif phase == "B3":
            scene("rule")
            body(x_c)
            for i in range(2):
                vec(x_c[i], e_t[i] * 1.0, GREEN, label=r"$\hat e_{target}$", off=(0.2 if i == 0 else -0.2, 0.0))
            text(["Si solo nos alejáramos, nos desviaríamos de la",
                  "puerta. Por eso también contamos hacia dónde está:",
                  "",
                  r"##$\hat e_{target} = \dfrac{\vec x_{puerta}-\vec x}{|\vec x_{puerta}-\vec x|}$",
                  "",
                  "Agente A: $\\hat e_{target}=%s$" % v2(e_t[0]),
                  "(casi derecho hacia abajo, un poquito a la derecha)."],
                 "B3) No perder el rumbo ($\\hat e_{target}$)")
            ax.set_title("t = %.4f s" % t_c, loc="left", fontsize=10)

        elif phase == "B4":
            scene("rule")
            body(x_c, who=(1,), alpha=0.15)
            body(x_c, who=(0,))
            a = x_c[0]
            vec(a, away[0], BLUE, label=r"$\hat n_{alejar}$", off=(0, 0.12))
            vec(a + away[0], e_t[0], GREEN, ls="--", label=r"$\hat e_{target}$", off=(-0.2, 0.0))
            vec(a, ssum[0], ORANGE, lw=3.2, label=r"$\vec s$", off=(0.16, 0.1))
            text(["Queremos las dos cosas a la vez:",
                  "alejarnos Y seguir hacia la puerta.",
                  "Se suman las flechas (una a continuación de la otra):",
                  "",
                  r"##$\vec s = \hat n_{alejar} + \hat e_{target}$",
                  "$%s + %s$" % (v2(away[0]), v2(e_t[0])),
                  "$= %s$,  largo $|\\vec s| = %.2f$" % (v2(ssum[0]), s_len[0]),
                  "",
                  "(agente A; B es el espejo)."],
                 "B4) Sumar las dos intenciones ($\\vec s$)")
            ax.set_title("t = %.4f s" % t_c, loc="left", fontsize=10)

        elif phase == "B5":
            scene("rule")
            body(x_c, who=(1,), alpha=0.15)
            body(x_c, who=(0,))
            a = x_c[0]
            # los tres vectores tienen la MISMA direccion: se dibujan en paralelo (corridos) para poder compararlos
            perp = np.array([-s_hat[0][1], s_hat[0][0]])  # perpendicular unitaria
            tips = []
            for shift, v, color, lw, ls, lab in (
                    (-0.30, ssum[0], ORANGE, 3.0, "-", r"$\vec s$: largo %.2f" % s_len[0]),
                    (0.0, s_hat[0], "gray", 3.0, "--", r"$\vec s/|\vec s|$: largo 1"),
                    (0.30, v_post[0], "black", 3.2, "-", r"$\vec v_{nueva}$: largo %.1f" % vd)):
                o = a + perp * shift
                vec(o, v, color, lw=lw, ls=ls)
                tips.append((o + v, lab, color))
            for tip, lab, color in tips:
                ax.text(tip[0] + 0.05, tip[1] - 0.03, lab, color=color, fontsize=10.5, fontweight="bold", ha="left", va="top")
            text(["La suma mide %.2f, pero queremos que salga" % s_len[0],
                  "a la rapidez de siempre, $v_d=%.1f$ m/s." % vd,
                  "• Normalizar = dividir por el largo (queda de largo 1).",
                  "• Después se multiplica por $v_d$.",
                  "",
                  r"##$\vec v_{nueva} = v_d\,\dfrac{\vec s}{|\vec s|}$",
                  "$\\vec s/|\\vec s| = %s$" % v2(s_hat[0]),
                  "$\\vec v_{nueva} = %.1f\\cdot%s = %s$ m/s" % (vd, v2(s_hat[0]), v2(v_post[0]))],
                 "B5) Ajustar la rapidez ($|\\vec v|=v_d$)")
            ax.set_title("t = %.4f s" % t_c, loc="left", fontsize=10)

        elif phase == "B6":
            scene("rule")
            body(x_c)
            for i in range(2):
                vec(x_c[i], v_post[i], "black", lw=3.0, label=r"$\vec v_{%s}$" % NAMES[i], off=(0.0, -0.17))
            text([r"##$\vec v_{nueva} = v_d\;\mathrm{normalizar}\left(\hat n_{alejar}+\hat e_{target}\right)$",
                  "",
                  "Misma regla para A y B (B es el espejo):",
                  "$\\vec v_A=%s$,  $\\vec v_B=%s$ m/s" % (v2(v_post[0]), v2(v_post[1])),
                  "",
                  "¿Por qué esta regla?",
                  "• alejarse del otro: evita que se solapen;",
                  "• sumar el rumbo: no se desvían de la puerta;",
                  "• rapidez $v_d$: salen a la velocidad de siempre.",
                  "",
                  "No conserva el impulso: es una regla del modelo",
                  "(como en el CPM), no una ley física."],
                 "B6) Resultado")
            ax.set_title("t = %.4f s: la velocidad cambia de golpe (único salto)" % t_c, loc="left", fontsize=10)

        elif phase == "C":
            scene("zoom")
            s = t - t_c
            pos = [x_c[i] + v_post[i] * s for i in range(2)]
            ghost(x_c, "choque")
            for i in range(2):
                ax.plot([x_c[i][0], x_end[i][0]], [x_c[i][1], x_end[i][1]], color=COLORS[i], ls=":", lw=1.4)
                ax.plot(*x_end[i], marker="o", ms=3, color=COLORS[i])
            body(pos)
            real_des(pos, v_post, v_post, scale=0.55)
            legend_vd()
            text(["Entre dos eventos no se calcula nada:",
                  "cada agente viaja en línea recta con la",
                  "velocidad con que salió del choque.",
                  "",
                  r"##$\vec x = \vec x_c + \vec v\,s$",
                  "• $\\vec x_c$: posición en el choque",
                  "• $s$: tiempo desde el choque",
                  "",
                  "A los $s=0.1$ s:  $A:\\ (%.3f,\\ %.3f)$" % tuple(x_end[0]),
                  "                          $B:\\ (%.3f,\\ %.3f)$" % tuple(x_end[1]),
                  "Por eso están ahí a los 0.1 s."],
                 "C) De 0 a 0.1 s: la traslación")
            ax.set_title("$s = t-t_c = %.0f$ ms   (deseada = real durante el pulso)" % (1000 * s), loc="left", fontsize=10)

        elif phase == "D":
            scene("zoom")
            ghost(x_c, "choque")
            for i in range(2):
                ax.plot([x_c[i][0], x_end[i][0]], [x_c[i][1], x_end[i][1]], color=COLORS[i], ls=":", lw=1.4)
            des = [vd * unit(DOOR - x_end[i]) for i in range(2)]
            body(x_end)
            real_des(x_end, v_post, des, scale=0.55, lw_real=2.2)
            legend_vd()
            text(["Termina el pulso (segundo y último evento):",
                  "• la DESEADA $\\vec w$ vuelve a apuntar a la puerta:",
                  r"$\vec w = v_d\,\hat e_{target}$ = $%s$ (A)" % v2(des[0]),
                  "• la REAL $\\vec v$ sigue siendo la de salida:",
                  "no puede saltar de golpe (tiene inercia).",
                  "",
                  "Desde acá la real se acerca a la deseada:",
                  r"##$\vec v(t') = \vec w + (\vec v_0-\vec w)\,e^{-t'/\tau}$",
                  "• $t'$: tiempo desde este instante",
                  "• $\\vec v_0$: la real ahora (la de salida)",
                  "• $\\tau=%.1f$ s: en $\\tau$ cierra el 63%% de la diferencia" % tau],
                 "D) A los 0.1 s del choque")
            ax.set_title("$t-t_c = 100$ ms", loc="left", fontsize=10)

        else:  # E
            scene("full")
            k = int(np.argmin(np.abs(ts - t)))
            des = [vd * unit(DOOR - xs[k][i]) for i in range(2)]
            body(xs[k])
            real_des(xs[k], vs[k], des, scale=0.5)
            for i in range(2):
                ax.plot(xs[: k + 1, i, 0], xs[: k + 1, i, 1], color=COLORS[i], lw=1, alpha=0.5)
            legend_vd()
            dev = max(np.linalg.norm(vs[k][i] - des[i]) for i in range(2))
            text(["La real se acerca a la deseada:",
                  r"##$|\vec v-\vec w| = %.2f$ m/s (cada vez menos)" % dev,
                  "",
                  "Mientras no coincidan se re-apunta la deseada",
                  "cada 0.1 s (si no, la trayectoria queda corrida",
                  "de la recta a la puerta).",
                  "Al coincidir: vuelo libre, sin eventos propios."],
                 r"E) Relajación con inercia ($\tau = %.1f$ s)" % tau)
            ax.set_title("$t-t_c = %.2f$ s" % (t - t_c), loc="left", fontsize=10)

    anim = FuncAnimation(fig, draw, frames=len(seq), interval=40)
    anim.save(out, writer=PillowWriter(fps=25))
    print("escrito", out, "| t_c = %.5f s | v_A = %s | cuadros: %d" % (t_c, v2(v_post[0]), len(seq)))


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit("uso: python anim_two.py trayectoria.txt salida.gif")
    main(sys.argv[1], sys.argv[2])
