"""Paso temporal dt* congelado: fuente unica para todos los barridos del billar (AN-02).

Este modulo guarda el dt elegido por el estudio 2.1a (`study_energy.py`) y la regla
declarada con la que se lo elige. Cada estudio posterior (2.1b, 2.2, 2.3, 2.4) hace
`from dt_star import DT_STAR` y lo pasa de forma explicita al corredor, de modo que
quede visible en el nombre del directorio de cada corrida.

Regla declarada (PD-51): dt* es el mayor dt de la grilla tal que todo dt de la grilla
menor o igual sea estable y tenga epsilon medio < EPS_THRESHOLD, sin superar el mayor
dt de la grilla con TC_PAIR/dt >= MIN_STEPS_PER_CONTACT.

DT_STAR se fija solo despues del barrido real y es lo que la regla elige de los datos:
`python3 python/study_energy.py --check-frozen` lo verifica. Cambiar las constantes de
la regla o DT_STAR es una decision del grupo que obliga a re-correr los barridos
posteriores.
"""

import math

# Umbral declarado: la energia total se conserva, en promedio, mejor que 0.1 por ciento.
EPS_THRESHOLD = 1e-3
# Practica de DEM: dt ~ tc/50 (el minimo aceptable es 10 pasos por contacto).
MIN_STEPS_PER_CONTACT = 50
# Replica physics.contact_time_pair para los parametros del enunciado (m = 0.025 kg,
# k = 1e4 N/m); un test compara ambas.
TC_PAIR = math.pi * math.sqrt((0.025 / 2.0) / 1e4)

# Congelado el 2026-10-02 desde el barrido real 2.1a (study_energy.py):
#   parametros: N = 300, sin obstaculos, tf = 5 s, dt2 = 0.01 s, semillas 1 a 5,
#               grilla (5e-3, 2e-3, 1e-3, 5e-4, 2e-4, 1e-4, 5e-5, 2e-5, 1e-5, 5e-6);
#   regla:      epsilon medio < EPS_THRESHOLD = 1e-3 (todo dt menor estable) y
#               TC_PAIR/dt >= MIN_STEPS_PER_CONTACT = 50;
#   criterio activo: contacto (dt_energy = 1e-4, dt_contact = 5e-5);
#   elegido:    dt* = 5e-5 s, epsilon medio 9.43e-5 (sigma 5.64e-5), 70.2 pasos por contacto;
#   descartado: el dt mayor siguiente, 1e-4 (35.1 pasos por contacto), tiene epsilon medio
#               4.95e-4 y cumple el umbral de energia pero no la regla de contacto.
DT_STAR = 5e-05
STEPS_PER_CONTACT = None if DT_STAR is None else TC_PAIR / DT_STAR


def require_dt_star():
    """Devuelve DT_STAR o falla si todavia no se congelo."""
    if DT_STAR is None:
        raise RuntimeError(
            "dt* todavia no esta congelado: correr `python3 python/study_energy.py` "
            "(estudio 2.1a) y fijar DT_STAR con lo que elige la regla; verificar con "
            "`python3 python/study_energy.py --check-frozen`"
        )
    return DT_STAR
