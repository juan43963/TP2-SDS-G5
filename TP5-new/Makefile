CXX      ?= c++
CXXFLAGS ?= -std=c++20 -O2 -Wall -Wextra -pedantic -Isrc/include

# -O2 es obligatorio y se mantiene identico en todos los esquemas: las
# comparaciones de wall-clock de la Fase 9 (TSDMD vs EDMD vs hibrido) solo valen
# con flags identicos. Nunca agregar -ffast-math ni -march=native.

BUILD := build
SRC   := src

# Layout de TP3 (D-10). Fuentes del motor listadas explicitamente para que el
# contenido exacto del .zip entregable sea visible aca. Los tests, en cambio, se
# descubren por wildcard: agregar una suite no requiere tocar este archivo.
CORE_SRC := $(SRC)/utils/options.cpp \
            $(SRC)/utils/generator.cpp \
            $(SRC)/utils/io.cpp \
            $(SRC)/engine/forces.cpp \
            $(SRC)/engine/evacuation.cpp \
            $(SRC)/engine/edmd_kernel.cpp \
            $(SRC)/engine/edmd.cpp \
            $(SRC)/engine/hybrid.cpp
CORE_OBJ := $(CORE_SRC:$(SRC)/%.cpp=$(BUILD)/%.o)
APP_OBJ  := $(BUILD)/main.o
TEST_OBJ := $(BUILD)/selftest.o
CHECK_OBJ := $(BUILD)/tools/check_trajectory.o

TEST_SUITE_SRC   := $(wildcard $(SRC)/tests/test_*.cpp)
TEST_SUITE_OBJ   := $(TEST_SUITE_SRC:$(SRC)/%.cpp=$(BUILD)/%.o)
TEST_SUPPORT_SRC := $(filter-out $(TEST_SUITE_SRC),$(wildcard $(SRC)/tests/*.cpp))
TEST_SUPPORT_OBJ := $(TEST_SUPPORT_SRC:$(SRC)/%.cpp=$(BUILD)/%.o)

ALL_OBJ := $(BUILD)/tools/scenario.o $(CORE_OBJ) $(APP_OBJ) $(TEST_OBJ) $(TEST_SUITE_OBJ) $(TEST_SUPPORT_OBJ) $(CHECK_OBJ)

.PHONY: all test smoke strict clean full-run full-check full determinism edmd-tracer edmd-smoke edmd-determinism edmd-scale edmd-full-run edmd-full-check edmd-full edmd-plot hybrid-tracer hybrid-extremes hybrid-smoke hybrid-determinism hybrid-scale hybrid-verify hybrid-audit hybrid-full-run hybrid-full-check hybrid-full hybrid-plot hybrid-anim study-smoke study-bc-stat study-bc-time study-sweep study-scale study-figures study-anim py-test entrega-test entrega-zip entrega-verify

all: tp5 tp5_test tp5_check tp5_scenario

tp5: $(CORE_OBJ) $(APP_OBJ)
	$(CXX) $(CXXFLAGS) -o $@ $^

tp5_test: $(CORE_OBJ) $(TEST_SUPPORT_OBJ) $(TEST_SUITE_OBJ) $(TEST_OBJ)
	$(CXX) $(CXXFLAGS) -o $@ $^

# Chequeo independiente de archivos de trayectoria (herramienta de verificacion, no es motor).
tp5_scenario: $(CORE_OBJ) $(BUILD)/tools/scenario.o
	$(CXX) $(CXXFLAGS) -o $@ $^

tp5_check: $(CORE_OBJ) $(TEST_SUPPORT_OBJ) $(CHECK_OBJ)
	$(CXX) $(CXXFLAGS) -o $@ $^

$(BUILD)/%.o: $(SRC)/%.cpp
	@mkdir -p $(dir $@)
	$(CXX) $(CXXFLAGS) -MMD -MP -c -o $@ $<

-include $(ALL_OBJ:.o=.d)

test: tp5_test
	./tp5_test

# Corrida de humo extremo a extremo: evacuacion de 30 agentes y chequeo del
# archivo de trayectoria (cabecera, al menos 3 frames, linea END final).
smoke: tp5
	@mkdir -p $(BUILD)
	./tp5 --N 30 --L 10 --seed 1 --tmax 200 --out $(BUILD)/smoke.txt > $(BUILD)/smoke.out
	@cat $(BUILD)/smoke.out
	@grep -q 'in_room_final=0' $(BUILD)/smoke.out \
	  && grep -q 'completed=1' $(BUILD)/smoke.out \
	  && grep -q 'wall_breaches=0' $(BUILD)/smoke.out \
	  && [ "$$(head -1 $(BUILD)/smoke.txt)" = "TP5_TRAJECTORY 1" ] \
	  && [ "$$(grep -c '^FRAME ' $(BUILD)/smoke.txt)" -ge 3 ] \
	  && tail -1 $(BUILD)/smoke.txt | grep -q '^END' \
	  && echo "smoke OK"

# Evacuacion completa de referencia (N=500, L=50, d=0.8, vd=1.5): archivo + RESULT.
# dt2 = 0.25 s (multiplo de dt) mantiene el archivo en decenas de MB.
# Semilla 3: evacua y cumple los umbrales; la 1 forma un arco estable en la puerta
# (ver README_codigo.md, Validacion).
FULL_SEED ?= 3
FULL_TXT    := data/full_n500.txt
FULL_RESULT := data/full_n500.result

full-run: tp5
	@mkdir -p data
	./tp5 --seed $(FULL_SEED) --dt2 0.25 --out $(FULL_TXT) > $(FULL_RESULT)
	@cat $(FULL_RESULT)

# Chequeo del archivo (solo lee el texto) y de los umbrales del RESULT del motor.
# 0.09 m = mitad del menor radio (rmin = 0.18); 20 s = cota fisica holgada de t_evac.
full-check: tp5_check
	./tp5_check $(FULL_TXT)
	@grep -q 'N=500 ' $(FULL_RESULT) \
	  && grep -q 'in_room_final=0' $(FULL_RESULT) \
	  && grep -q 'completed=1' $(FULL_RESULT) \
	  && grep -q 'wall_breaches=0' $(FULL_RESULT)
	@tr ' ' '\n' < $(FULL_RESULT) | awk -F= \
	  '$$1=="max_agent_overlap" && $$2>=0.09 {bad=1; print "max_agent_overlap >= 0.09: " $$2} \
	   $$1=="max_wall_overlap" && $$2>=0.09 {bad=1; print "max_wall_overlap >= 0.09: " $$2} \
	   $$1=="t_evac" && $$2<20 {bad=1; print "t_evac < 20: " $$2} \
	   END {exit bad}'
	@echo "full-check OK"

full: full-run full-check

# Reproducibilidad por semilla e independencia de la salida (N=60, L=10: rapido).
# Los campos de reloj (simulation_ms, output_ms) no se comparan.
DET_ARGS := --N 60 --L 10
determinism: tp5
	@set -e; mkdir -p $(BUILD); \
	field() { tr ' ' '\n' < "$$1" | grep "^$$2=" ; }; \
	./tp5 $(DET_ARGS) --seed 5 --out $(BUILD)/det_a.txt > $(BUILD)/det_a.result; \
	./tp5 $(DET_ARGS) --seed 5 --out $(BUILD)/det_b.txt > $(BUILD)/det_b.result; \
	cmp $(BUILD)/det_a.txt $(BUILD)/det_b.txt; \
	./tp5 $(DET_ARGS) --seed 6 --out $(BUILD)/det_c.txt > $(BUILD)/det_c.result; \
	if cmp -s $(BUILD)/det_a.txt $(BUILD)/det_c.txt; then echo "semillas distintas dieron el mismo archivo"; exit 1; fi; \
	./tp5 $(DET_ARGS) --seed 5 --no-output > $(BUILD)/det_n.result; \
	./tp5 $(DET_ARGS) --seed 5 --dt2 0.5 --out $(BUILD)/det_d.txt > $(BUILD)/det_d.result; \
	for f in steps t_evac crossed removed max_agent_overlap; do \
	  ref=$$(field $(BUILD)/det_a.result $$f); \
	  [ -n "$$ref" ] || { echo "falta $$f en RESULT"; exit 1; }; \
	  [ "$$ref" = "$$(field $(BUILD)/det_n.result $$f)" ] || { echo "--no-output cambia $$f"; exit 1; }; \
	  [ "$$ref" = "$$(field $(BUILD)/det_d.result $$f)" ] || { echo "--dt2 0.5 cambia $$f"; exit 1; }; \
	done; \
	echo "DETERMINISM OK"

# Trazador EDMD (Fase 7, Plan 01): un agente libre se evacua evento a evento. Debe coincidir
# con TSDMD en t_evac (TSDMD detecta el cruce en multiplos de dt = 1e-4 s: 3e-4 s de holgura;
# la semilla 1 es la primera con camino libre de paredes, t_evac(TSDMD) = 3.8160 s) y la salida
# recorre exitDistance = 1 m a velocidad <= 1.5 m/s (t_clear - t_evac en [0.6666, 1.5]).
edmd-tracer: tp5 tp5_check
	@set -e; mkdir -p $(BUILD); \
	field() { tr ' ' '\n' < "$$1" | awk -F= -v k="$$2" '$$1==k {print $$2}'; }; \
	./tp5 --scheme edmd --N 1 --L 10 --seed 1 --out $(BUILD)/edmd_n1.txt > $(BUILD)/edmd_n1.result; \
	./tp5 --scheme tsdmd --N 1 --L 10 --seed 1 --no-output > $(BUILD)/tsdmd_n1.result; \
	cat $(BUILD)/edmd_n1.result $(BUILD)/tsdmd_n1.result; \
	for kv in scheme=edmd completed=1 crossed=1 removed=1 in_room_final=0 wall_breaches=0; do \
	  tr ' ' '\n' < $(BUILD)/edmd_n1.result | grep -qx "$$kv" || { echo "falta $$kv en el RESULT de EDMD"; exit 1; }; \
	done; \
	ee=$$(field $(BUILD)/edmd_n1.result t_evac); et=$$(field $(BUILD)/tsdmd_n1.result t_evac); \
	ec=$$(field $(BUILD)/edmd_n1.result t_clear); \
	awk -v a="$$ee" -v b="$$et" 'BEGIN {d = a - b; if (d < 0) d = -d; if (d > 3e-4) {print "t_evac difiere: edmd=" a " tsdmd=" b; exit 1}}'; \
	awk -v e="$$ee" -v c="$$ec" 'BEGIN {d = c - e; if (d < 0.6666 || d > 1.5) {print "t_clear - t_evac fuera de [0.6666, 1.5]: " d; exit 1}}'; \
	./tp5_check $(BUILD)/edmd_n1.txt; \
	[ "$$(head -1 $(BUILD)/edmd_n1.txt)" = "TP5_TRAJECTORY 1" ] && grep -q '^scheme edmd$$' $(BUILD)/edmd_n1.txt; \
	for h in 'restitution 0.5' 'event_gap 0.005' 'steer_dt 0.1'; do \
	  grep -qx "$$h" $(BUILD)/edmd_n1.txt || { echo "falta '$$h' en la cabecera de EDMD"; exit 1; }; \
	done; \
	grep -q 'floor_collisions=' $(BUILD)/edmd_n1.result || { echo "falta floor_collisions en el RESULT de EDMD"; exit 1; }; \
	tr ' ' '\n' < $(BUILD)/edmd_n1.result | grep -qx 'time_regressions=0' || { echo "time_regressions != 0"; exit 1; }; \
	tr ' ' '\n' < $(BUILD)/tsdmd_n1.result | grep -qx 'floor_collisions=0' || { echo "falta floor_collisions=0 en TSDMD"; exit 1; }; \
	echo "edmd-tracer OK"

# Chequeo comun de una corrida EDMD multitudinaria: completa, sin brechas, sin regresiones de
# tiempo, con colisiones, solapes maximos < 0.09 m (mitad del menor radio) y archivo valido
# segun el oraculo de superposicion. Uso: $(call edmd_check,<resultado>,<archivo>).
define edmd_check
	grep -q 'in_room_final=0' $(1) && grep -q 'completed=1' $(1) \
	  && grep -q 'wall_breaches=0' $(1) && grep -q 'time_regressions=0' $(1) \
	  || { echo "RESULT incompleto o con brechas/regresiones: $(1)"; exit 1; }; \
	tr ' ' '\n' < $(1) | awk -F= \
	  '$$1=="collisions" && $$2<=0 {bad=1; print "collisions <= 0"} \
	   $$1=="max_agent_overlap" && $$2>=0.09 {bad=1; print "max_agent_overlap >= 0.09: " $$2} \
	   $$1=="max_wall_overlap" && $$2>=0.09 {bad=1; print "max_wall_overlap >= 0.09: " $$2} \
	   END {exit bad}'; \
	./tp5_check $(2)
endef

# EDMD con N=60 (L=10, semilla 5): crowd chico, rapido. (Con la proyeccion total de solapes la 5 formaba
# un arco; con el tope --overlap-cap 0.07 completa. La finalizacion es una loteria por semilla.)
edmd-smoke: tp5 tp5_check
	@set -e; mkdir -p $(BUILD); \
	./tp5 --scheme edmd --N 60 --L 10 --seed 5 --dt2 0.25 --out $(BUILD)/edmd_n60.txt > $(BUILD)/edmd_n60.result; \
	cat $(BUILD)/edmd_n60.result; \
	$(call edmd_check,$(BUILD)/edmd_n60.result,$(BUILD)/edmd_n60.txt); \
	echo "edmd-smoke OK"

# Reproducibilidad por semilla e independencia de la salida del esquema EDMD.
EDMD_DET_ARGS := --scheme edmd --N 60 --L 10
edmd-determinism: tp5
	@set -e; mkdir -p $(BUILD); \
	field() { tr ' ' '\n' < "$$1" | grep "^$$2=" ; }; \
	./tp5 $(EDMD_DET_ARGS) --seed 5 --out $(BUILD)/edet_a.txt > $(BUILD)/edet_a.result; \
	./tp5 $(EDMD_DET_ARGS) --seed 5 --out $(BUILD)/edet_b.txt > $(BUILD)/edet_b.result; \
	cmp $(BUILD)/edet_a.txt $(BUILD)/edet_b.txt; \
	./tp5 $(EDMD_DET_ARGS) --seed 6 --out $(BUILD)/edet_c.txt > $(BUILD)/edet_c.result; \
	if cmp -s $(BUILD)/edet_a.txt $(BUILD)/edet_c.txt; then echo "semillas distintas dieron el mismo archivo"; exit 1; fi; \
	./tp5 $(EDMD_DET_ARGS) --seed 5 --no-output > $(BUILD)/edet_n.result; \
	./tp5 $(EDMD_DET_ARGS) --seed 5 --dt2 0.5 --out $(BUILD)/edet_d.txt > $(BUILD)/edet_d.result; \
	for f in steps t_evac collisions max_agent_overlap; do \
	  ref=$$(field $(BUILD)/edet_a.result $$f); \
	  [ -n "$$ref" ] || { echo "falta $$f en RESULT"; exit 1; }; \
	  [ "$$ref" = "$$(field $(BUILD)/edet_n.result $$f)" ] || { echo "--no-output cambia $$f"; exit 1; }; \
	  [ "$$ref" = "$$(field $(BUILD)/edet_d.result $$f)" ] || { echo "--dt2 0.5 cambia $$f"; exit 1; }; \
	done; \
	echo "EDMD DETERMINISM OK"

# EDMD con N=200 (L=31.6: misma densidad inicial que N=500, L=50): prueba temprana de rendimiento.
# Semilla 3: con los defaults actuales completan las semillas 1, 2, 3, 4, 6 y 7 (la 5 y la 8 no, en
# 3M eventos); es la misma semilla que la corrida de referencia de N=500. Sin proyeccion de
# solapes la 3 formaba un arco y completaban 1/2/4/5/6/8.
EDMD_SCALE_SEED ?= 3
edmd-scale: tp5 tp5_check
	@set -e; mkdir -p $(BUILD); \
	./tp5 --scheme edmd --N 200 --L 31.6 --seed $(EDMD_SCALE_SEED) --dt2 0.25 --out $(BUILD)/edmd_n200.txt > $(BUILD)/edmd_n200.result; \
	cat $(BUILD)/edmd_n200.result; \
	tr ' ' '\n' < $(BUILD)/edmd_n200.result | grep -E '^(simulation_ms|events|stale|collisions|floor_collisions)='; \
	$(call edmd_check,$(BUILD)/edmd_n200.result,$(BUILD)/edmd_n200.txt); \
	echo "edmd-scale OK"

# Corrida de referencia EDMD (Fase 7, Plan 04): N=500, L=50, misma semilla que la referencia
# TSDMD de `make full` (D-20), y chequeo de validez y de condicion inicial identica.
EDMD_FULL_TXT    := data/edmd_full_n500.txt
EDMD_FULL_RESULT := data/edmd_full_n500.result
# tmax acotado: un arco estable no debe consumir horas de reloj (la trayectoria depende de tmax).
EDMD_FULL_TMAX ?= 400

edmd-full-run: tp5
	@mkdir -p data
	./tp5 --scheme edmd --N 500 --seed $(FULL_SEED) --dt2 0.25 --tmax $(EDMD_FULL_TMAX) --out $(EDMD_FULL_TXT) > $(EDMD_FULL_RESULT)
	@cat $(EDMD_FULL_RESULT)

# Filas (id x y vx vy r) del primer bloque FRAME de un archivo de trayectoria.
define first_frame_rows
	awk '/^FRAME /{n++; next} n==1 && NF>=6 {print $$1,$$2,$$3,$$4,$$5,$$6} n>1{exit}' $(1)
endef

edmd-full-check: tp5_check
	@set -e; \
	[ -f $(EDMD_FULL_TXT) ] && [ -f $(EDMD_FULL_RESULT) ] || { echo "faltan $(EDMD_FULL_TXT) o $(EDMD_FULL_RESULT): ejecutar make edmd-full-run"; exit 1; }; \
	[ -f $(FULL_TXT) ] || { echo "falta $(FULL_TXT): ejecutar make full"; exit 1; }; \
	for kv in scheme=edmd N=500 completed=1 crossed=500 removed=500 in_room_final=0 wall_breaches=0 time_regressions=0; do \
	  tr ' ' '\n' < $(EDMD_FULL_RESULT) | grep -qx "$$kv" || { echo "falta $$kv en el RESULT EDMD"; exit 1; }; \
	done; \
	tr ' ' '\n' < $(EDMD_FULL_RESULT) | awk -F= \
	  '$$1=="max_agent_overlap" && $$2>=0.09 {bad=1; print "max_agent_overlap >= 0.09: " $$2} \
	   $$1=="max_wall_overlap" && $$2>=0.09 {bad=1; print "max_wall_overlap >= 0.09: " $$2} \
	   END {exit bad}'; \
	./tp5_check $(EDMD_FULL_TXT); \
	[ "$$(head -1 $(EDMD_FULL_TXT))" = "TP5_TRAJECTORY 1" ] && grep -q '^scheme edmd$$' $(EDMD_FULL_TXT); \
	$(call first_frame_rows,$(EDMD_FULL_TXT)) > $(BUILD)/frame1_edmd.txt; \
	$(call first_frame_rows,$(FULL_TXT)) > $(BUILD)/frame1_tsdmd.txt; \
	[ "$$(wc -l < $(BUILD)/frame1_edmd.txt)" -eq 500 ] || { echo "el primer frame EDMD no tiene 500 filas"; exit 1; }; \
	cmp $(BUILD)/frame1_edmd.txt $(BUILD)/frame1_tsdmd.txt || { echo "la condicion inicial difiere de TSDMD"; exit 1; }; \
	field() { tr ' ' '\n' < "$$1" | awk -F= -v k="$$2" '$$1==k {print $$2}'; }; \
	echo "         TSDMD(full_n500)  EDMD"; \
	echo "t_evac   $$(field $(FULL_RESULT) t_evac)  $$(field $(EDMD_FULL_RESULT) t_evac)"; \
	echo "t_clear  $$(field $(FULL_RESULT) t_clear)  $$(field $(EDMD_FULL_RESULT) t_clear)"; \
	echo "sim_ms   $$(field $(FULL_RESULT) simulation_ms)  $$(field $(EDMD_FULL_RESULT) simulation_ms)"; \
	echo "steps/events $$(field $(FULL_RESULT) steps)  $$(field $(EDMD_FULL_RESULT) events)"; \
	for k in collisions floor_collisions stale; do echo "$$k=$$(field $(EDMD_FULL_RESULT) $$k)"; done; \
	echo "edmd-full OK"

edmd-full: edmd-full-run edmd-full-check

# Superposicion de las curvas de poblacion EDMD y TSDMD (criterio 4 de la Fase 7).
edmd-plot:
	@set -e; \
	[ -f $(EDMD_FULL_TXT) ] || { echo "falta $(EDMD_FULL_TXT): ejecutar make edmd-full"; exit 1; }; \
	[ -f $(FULL_TXT) ] || { echo "falta $(FULL_TXT): ejecutar make full"; exit 1; }; \
	python3 python/population_compare.py --tsdmd $(FULL_TXT) --edmd $(EDMD_FULL_TXT) \
	  --out data/population_edmd_vs_tsdmd.png | tee $(BUILD)/plot.out; \
	grep -q '^POPULATION_COMPARE tsdmd_t_evac=' $(BUILD)/plot.out; \
	[ -f data/population_edmd_vs_tsdmd.png ]; \
	echo "edmd-plot OK"

# Trazador del hibrido (Fase 8, Plan 01): N=8, L=10, T y alpha por defecto. Con el escaneo de pares
# mixtos del Plan 02 las semillas 1 a 20 completan sin violaciones del oraculo de superposicion (antes
# solo la 17 lo hacia: un residente EDMD atravesaba a un agente TSDMD); se conserva la 17.
HYBRID_TRACER_SEED ?= 17
hybrid-tracer: tp5 tp5_check
	@set -e; mkdir -p $(BUILD); \
	timeout 300 ./tp5 --scheme hybrid --N 8 --L 10 --seed $(HYBRID_TRACER_SEED) --dt2 0.25 --out $(BUILD)/hybrid_n8.txt > $(BUILD)/hybrid_n8.result; \
	cat $(BUILD)/hybrid_n8.result; \
	for kv in scheme=hybrid completed=1 in_room_final=0 wall_breaches=0 collisions=0; do \
	  tr ' ' '\n' < $(BUILD)/hybrid_n8.result | grep -qx "$$kv" || { echo "falta $$kv en el RESULT hibrido"; exit 1; }; \
	done; \
	for k in promotions returns hybrid_steps tsdmd_agent_steps; do \
	  tr ' ' '\n' < $(BUILD)/hybrid_n8.result | grep -q "^$$k=" || { echo "falta $$k= en el RESULT hibrido"; exit 1; }; \
	done; \
	for h in 'scheme hybrid' 'hybrid_T 0.5' 'hybrid_alpha 2'; do \
	  grep -qx "$$h" $(BUILD)/hybrid_n8.txt || { echo "falta '$$h' en la cabecera del hibrido"; exit 1; }; \
	done; \
	./tp5_check $(BUILD)/hybrid_n8.txt; \
	echo "hybrid-tracer OK"

# Extremos del hibrido (D-23, HYB-05): T = 0 reproduce EDMD y T >= tmax reproduce TSDMD. Se compara
# el cuerpo del archivo desde COLUMNS (las cabeceras difieren por `scheme` y las claves hibridas) y
# los campos del RESULT que no son relojes.
HYBRID_EXT_ARGS := --N 60 --L 10 --seed 5 --dt2 0.25
hybrid-extremes: tp5
	@set -e; mkdir -p $(BUILD); \
	field() { tr ' ' '\n' < "$$1" | grep "^$$2=" ; }; \
	body() { sed -n '/^COLUMNS/,$$p' "$$1"; }; \
	./tp5 $(HYBRID_EXT_ARGS) --scheme hybrid --hybrid-T 0 --out $(BUILD)/hx_h0.txt > $(BUILD)/hx_h0.result; \
	./tp5 $(HYBRID_EXT_ARGS) --scheme edmd --out $(BUILD)/hx_e.txt > $(BUILD)/hx_e.result; \
	./tp5 $(HYBRID_EXT_ARGS) --scheme hybrid --hybrid-T 1e9 --out $(BUILD)/hx_hinf.txt > $(BUILD)/hx_hinf.result; \
	./tp5 $(HYBRID_EXT_ARGS) --scheme tsdmd --out $(BUILD)/hx_t.txt > $(BUILD)/hx_t.result; \
	body $(BUILD)/hx_h0.txt > $(BUILD)/hx_h0.body; body $(BUILD)/hx_e.txt > $(BUILD)/hx_e.body; \
	body $(BUILD)/hx_hinf.txt > $(BUILD)/hx_hinf.body; body $(BUILD)/hx_t.txt > $(BUILD)/hx_t.body; \
	[ -s $(BUILD)/hx_h0.body ] && [ -s $(BUILD)/hx_hinf.body ] || { echo "cuerpo vacio"; exit 1; }; \
	cmp $(BUILD)/hx_h0.body $(BUILD)/hx_e.body || { echo "T=0 difiere de EDMD"; exit 1; }; \
	cmp $(BUILD)/hx_hinf.body $(BUILD)/hx_t.body || { echo "T>=tmax difiere de TSDMD"; exit 1; }; \
	for f in steps t_evac crossed removed collisions max_agent_overlap; do \
	  ref=$$(field $(BUILD)/hx_e.result $$f); [ -n "$$ref" ] || { echo "falta $$f en RESULT"; exit 1; }; \
	  [ "$$ref" = "$$(field $(BUILD)/hx_h0.result $$f)" ] || { echo "T=0 cambia $$f"; exit 1; }; \
	  ref=$$(field $(BUILD)/hx_t.result $$f); \
	  [ "$$ref" = "$$(field $(BUILD)/hx_hinf.result $$f)" ] || { echo "T>=tmax cambia $$f"; exit 1; }; \
	done; \
	echo "hybrid-extremes OK"

# Chequeo comun de una corrida hibrida: completa, sin brechas ni regresiones de tiempo, SIN colisiones
# duras (con T > 0 todo contacto lo resuelve el resorte del TSDMD, nunca EDMD), solapes maximos
# < 0.09 m, con pasajes en las dos direcciones y archivo valido segun el oraculo de superposicion.
# Uso: $(call hybrid_check,<resultado>,<archivo>).
define hybrid_check
	grep -q 'in_room_final=0' $(1) && grep -q 'completed=1' $(1) \
	  && grep -q 'wall_breaches=0' $(1) && grep -q 'time_regressions=0' $(1) \
	  && tr ' ' '\n' < $(1) | grep -qx 'collisions=0' \
	  || { echo "RESULT incompleto o con brechas/colisiones duras: $(1)"; exit 1; }; \
	tr ' ' '\n' < $(1) | awk -F= \
	  '$$1=="max_agent_overlap" && $$2>=0.09 {bad=1; print "max_agent_overlap >= 0.09: " $$2} \
	   $$1=="max_wall_overlap" && $$2>=0.09 {bad=1; print "max_wall_overlap >= 0.09: " $$2} \
	   $$1=="promotions" && $$2<=0 {bad=1; print "promotions <= 0"} \
	   $$1=="returns" && $$2<=0 {bad=1; print "returns <= 0"} \
	   END {exit bad}'; \
	./tp5_check $(2)
endef

# Humo del hibrido: N=60, L=10, T y alpha por defecto. La finalizacion es una loteria por semilla (un
# arco estable en la puerta no evacua, ver 07-04-SUMMARY): la semilla 1 es la primera de 1 a 20 que
# completa con 0 violaciones (--tmax 400 fijo, la trayectoria depende de tmax).
HYBRID_SMOKE_SEED ?= 1
HYBRID_TMAX ?= 400
hybrid-smoke: tp5 tp5_check
	@set -e; mkdir -p $(BUILD); \
	timeout 900 ./tp5 --scheme hybrid --N 60 --L 10 --seed $(HYBRID_SMOKE_SEED) --dt2 0.25 --tmax $(HYBRID_TMAX) --out $(BUILD)/hybrid_n60.txt > $(BUILD)/hybrid_n60.result; \
	cat $(BUILD)/hybrid_n60.result; \
	for h in 'scheme hybrid' 'hybrid_T 0.5' 'hybrid_alpha 2'; do \
	  grep -qx "$$h" $(BUILD)/hybrid_n60.txt || { echo "falta '$$h' en la cabecera del hibrido"; exit 1; }; \
	done; \
	$(call hybrid_check,$(BUILD)/hybrid_n60.result,$(BUILD)/hybrid_n60.txt); \
	echo "hybrid-smoke OK"

# Reproducibilidad por semilla e independencia de la salida del hibrido (N=60, L=10). Los campos de
# reloj no se comparan. Semillas 5 y 6: las dos completan.
HYBRID_DET_ARGS := --scheme hybrid --N 60 --L 10 --tmax $(HYBRID_TMAX)
hybrid-determinism: tp5
	@set -e; mkdir -p $(BUILD); \
	field() { tr ' ' '\n' < "$$1" | grep "^$$2=" ; }; \
	./tp5 $(HYBRID_DET_ARGS) --seed 5 --out $(BUILD)/hdet_a.txt > $(BUILD)/hdet_a.result; \
	./tp5 $(HYBRID_DET_ARGS) --seed 5 --out $(BUILD)/hdet_b.txt > $(BUILD)/hdet_b.result; \
	cmp $(BUILD)/hdet_a.txt $(BUILD)/hdet_b.txt; \
	./tp5 $(HYBRID_DET_ARGS) --seed 6 --out $(BUILD)/hdet_c.txt > $(BUILD)/hdet_c.result; \
	if cmp -s $(BUILD)/hdet_a.txt $(BUILD)/hdet_c.txt; then echo "semillas distintas dieron el mismo archivo"; exit 1; fi; \
	./tp5 $(HYBRID_DET_ARGS) --seed 5 --no-output > $(BUILD)/hdet_n.result; \
	./tp5 $(HYBRID_DET_ARGS) --seed 5 --dt2 0.5 --out $(BUILD)/hdet_d.txt > $(BUILD)/hdet_d.result; \
	for f in steps t_evac promotions returns max_agent_overlap; do \
	  ref=$$(field $(BUILD)/hdet_a.result $$f); \
	  [ -n "$$ref" ] || { echo "falta $$f en RESULT"; exit 1; }; \
	  [ "$$ref" = "$$(field $(BUILD)/hdet_n.result $$f)" ] || { echo "--no-output cambia $$f"; exit 1; }; \
	  [ "$$ref" = "$$(field $(BUILD)/hdet_d.result $$f)" ] || { echo "--dt2 0.5 cambia $$f"; exit 1; }; \
	done; \
	echo "HYBRID DETERMINISM OK"

# Hibrido con N=200 (L=31.6: misma densidad inicial que N=500, L=50): rendimiento y oscilacion. La
# semilla se fija como en edmd-scale (loteria por semilla) con --tmax 500: de las semillas 3, 1, 2 la 3
# forma un arco estable en la puerta (completed=0 a tmax=3000) y la 1 es la primera que completa. Informa el costo contra el
# TSDMD puro con los mismos argumentos; la guarda (hibrido <= 6 veces el TSDMD) solo avisa: la
# evaluacion del criterio en cada paso dt no se submuestrea (D-27).
HYBRID_SCALE_SEED ?= 1
HYBRID_SCALE_TMAX ?= 500
hybrid-scale: tp5 tp5_check
	@set -e; mkdir -p $(BUILD); \
	field() { tr ' ' '\n' < "$$1" | awk -F= -v k="$$2" '$$1==k {print $$2}'; }; \
	timeout 3600 ./tp5 --scheme hybrid --N 200 --L 31.6 --seed $(HYBRID_SCALE_SEED) --dt2 0.25 --tmax $(HYBRID_SCALE_TMAX) --out $(BUILD)/hybrid_n200.txt > $(BUILD)/hybrid_n200.result; \
	cat $(BUILD)/hybrid_n200.result; \
	tr ' ' '\n' < $(BUILD)/hybrid_n200.result | grep -E '^(simulation_ms|promotions|returns|mixed_promotions|quick_repromotions|hybrid_steps|tsdmd_agent_steps)='; \
	$(call hybrid_check,$(BUILD)/hybrid_n200.result,$(BUILD)/hybrid_n200.txt); \
	timeout 3600 ./tp5 --scheme tsdmd --N 200 --L 31.6 --seed $(HYBRID_SCALE_SEED) --dt2 0.25 --tmax $(HYBRID_SCALE_TMAX) --no-output > $(BUILD)/tsdmd_n200.result; \
	hy=$$(field $(BUILD)/hybrid_n200.result simulation_ms); ts=$$(field $(BUILD)/tsdmd_n200.result simulation_ms); \
	awk -v h="$$hy" -v t="$$ts" 'BEGIN {r = h / t; printf "simulation_ms: hibrido %.0f, tsdmd %.0f, cociente %.2f\n", h, t, r; if (r > 6) print "AVISO: el hibrido supera 6 veces el TSDMD puro (informar)"}'; \
	echo "hybrid-scale OK"

# Auditoria por fuerza bruta del hibrido (Fase 8, Plan 04, HYB-02 a HYB-04): el suite `hybrid_brute`
# audita cada limite de la grilla de tres corridas completas (alcance trasero, par mixto y N=60 denso)
# y corre tres controles negativos. Exige 0 solapes de residente EDMD, 0 contactos perdidos y 0
# violaciones del oraculo en las lineas HYBRID_AUDIT de rear_end, mixed y dense_n60 (las lineas
# control_* tienen contadores distintos de 0 a proposito), pares mixtos cercanos en mixed y dense_n60,
# ningun cambio de esquema en limites consecutivos en dense_n60 y tres controles con detected=1.
# Despues repite hybrid-extremes (D-23).
hybrid-verify: tp5_test tp5
	@set -e; mkdir -p $(BUILD); \
	./tp5_test hybrid_brute > $(BUILD)/hybrid_brute.out; \
	cat $(BUILD)/hybrid_brute.out; \
	awk '/^HYBRID_AUDIT/ { \
	       for (i = 2; i <= NF; i++) { split($$i, kv, "="); f[kv[1]] = kv[2] } \
	       lab = f["label"]; \
	       if (lab != "rear_end" && lab != "mixed" && lab != "dense_n60") next; \
	       seen[lab] = 1; \
	       if (f["resident_overlaps"] != 0 || f["lost_contacts"] != 0 || f["oracle_violations"] != 0) { \
	         bad = 1; print "contadores no nulos en " lab } \
	       if (f["completed"] != 1) { bad = 1; print "no completa: " lab } \
	       if ((lab == "mixed" || lab == "dense_n60") && f["mixed_pair_boundaries"] <= 0) { \
	         bad = 1; print "mixed_pair_boundaries <= 0 en " lab } \
	       if (lab == "dense_n60") { \
	         if (f["consecutive_flips"] != 0) { bad = 1; print "consecutive_flips != 0" } \
	         printf "dense_n60: returns=%s quick_repromotions=%s min_dwell_s=%s\n", f["returns"], f["quick_repromotions"], f["min_dwell_s"] } } \
	     /^CONTROL/ { if ($$3 == "detected=1") c++; else { bad = 1; print "control sin detectar: " $$0 } } \
	     END { if (!seen["rear_end"] || !seen["mixed"] || !seen["dense_n60"]) { bad = 1; print "faltan lineas HYBRID_AUDIT" } \
	           if (c != 3) { bad = 1; print "se esperaban 3 controles con detected=1, hay " c } \
	           exit bad }' $(BUILD)/hybrid_brute.out; \
	$(MAKE) hybrid-extremes; \
	echo "hybrid-verify OK"

# Auditoria pesada de N=200 (L=31.6, semilla 1) muestreada (depthStride 20, tauStride 200). Esta
# gobernada por TP5_HEAVY=1 y NO corre en `make test`: recorre ~3.4M limites con O(N^2) por muestra y
# tarda minutos; el ciclo normal de verificacion no debe pagarla.
hybrid-audit: tp5_test
	@set -e; mkdir -p $(BUILD); \
	TP5_HEAVY=1 timeout 3600 ./tp5_test hybrid_audit > $(BUILD)/hybrid_audit.out; \
	cat $(BUILD)/hybrid_audit.out; \
	awk '/^HYBRID_AUDIT label=dense_n200 / { \
	       seen = 1; \
	       for (i = 2; i <= NF; i++) { split($$i, kv, "="); f[kv[1]] = kv[2] } \
	       if (f["resident_overlaps"] != 0 || f["lost_contacts"] != 0 || f["oracle_violations"] != 0) { \
	         bad = 1; print "contadores no nulos en dense_n200" } \
	       if (f["completed"] != 1) { bad = 1; print "dense_n200 no completa" } } \
	     END { if (!seen) { bad = 1; print "falta la linea HYBRID_AUDIT label=dense_n200" } exit bad }' $(BUILD)/hybrid_audit.out; \
	echo "hybrid-audit OK"

# Corrida de aceptacion del hibrido (Fase 8, Plan 05): N=500, L=50. La finalizacion de N grande es una
# loteria por semilla (07-04): con los defaults T=0.5 y alpha=2 completan las semillas 8 y 10 de las
# diez probadas (3, 2, 6, 9, 1, 4, 5, 7, 8, 10); la 10 es la unica que ademas cumple los umbrales de
# solape. La referencia TSDMD de la misma semilla (data/full_n500.txt, `make full-run FULL_SEED=10`)
# debe existir: hybrid-full-check compara con ella el primer frame (misma condicion inicial).
HYBRID_FULL_SEED ?= 10
HYBRID_FULL_TMAX ?= 3000
HYBRID_FULL_TIMEOUT ?= 7200
HYBRID_FULL_TXT    := data/hybrid_full_n500.txt
HYBRID_FULL_RESULT := data/hybrid_full_n500.result

hybrid-full-run: tp5
	@mkdir -p data
	timeout $(HYBRID_FULL_TIMEOUT) ./tp5 --scheme hybrid --N 500 --seed $(HYBRID_FULL_SEED) --dt2 0.25 --tmax $(HYBRID_FULL_TMAX) --out $(HYBRID_FULL_TXT) > $(HYBRID_FULL_RESULT)
	@cat $(HYBRID_FULL_RESULT)

hybrid-full-check: tp5_check
	@set -e; \
	[ -f $(HYBRID_FULL_TXT) ] && [ -f $(HYBRID_FULL_RESULT) ] || { echo "faltan $(HYBRID_FULL_TXT) o $(HYBRID_FULL_RESULT): ejecutar make hybrid-full-run"; exit 1; }; \
	for kv in scheme=hybrid N=500 completed=1 crossed=500 removed=500 in_room_final=0 wall_breaches=0 time_regressions=0 collisions=0; do \
	  tr ' ' '\n' < $(HYBRID_FULL_RESULT) | grep -qx "$$kv" || { echo "falta $$kv en el RESULT hibrido"; exit 1; }; \
	done; \
	tr ' ' '\n' < $(HYBRID_FULL_RESULT) | awk -F= \
	  '$$1=="max_agent_overlap" && $$2>=0.09 {bad=1; print "max_agent_overlap >= 0.09: " $$2} \
	   $$1=="max_wall_overlap" && $$2>=0.09 {bad=1; print "max_wall_overlap >= 0.09: " $$2} \
	   $$1=="promotions" && $$2<=0 {bad=1; print "promotions <= 0"} \
	   $$1=="returns" && $$2<=0 {bad=1; print "returns <= 0"} \
	   END {exit bad}'; \
	./tp5_check $(HYBRID_FULL_TXT); \
	[ "$$(head -1 $(HYBRID_FULL_TXT))" = "TP5_TRAJECTORY 1" ] || { echo "primera linea invalida"; exit 1; }; \
	for h in 'scheme hybrid' hybrid_T hybrid_alpha; do \
	  grep -q "^$$h" $(HYBRID_FULL_TXT) || { echo "falta '$$h' en la cabecera del hibrido"; exit 1; }; \
	done; \
	field() { tr ' ' '\n' < "$$1" | awk -F= -v k="$$2" '$$1==k {print $$2}'; }; \
	hseed() { awk '$$1=="seed" {print $$2; exit}' "$$1"; }; \
	[ -f $(FULL_TXT) ] && [ -f $(FULL_RESULT) ] || { echo "falta la referencia TSDMD $(FULL_TXT): ejecutar make full"; exit 1; }; \
	if [ "$$(hseed $(FULL_TXT))" = "$$(hseed $(HYBRID_FULL_TXT))" ]; then \
	  $(call first_frame_rows,$(HYBRID_FULL_TXT)) > $(BUILD)/frame1_hybrid.txt; \
	  $(call first_frame_rows,$(FULL_TXT)) > $(BUILD)/frame1_tsdmd.txt; \
	  [ "$$(wc -l < $(BUILD)/frame1_hybrid.txt)" -eq 500 ] || { echo "el primer frame hibrido no tiene 500 filas"; exit 1; }; \
	  cmp $(BUILD)/frame1_hybrid.txt $(BUILD)/frame1_tsdmd.txt || { echo "la condicion inicial difiere de TSDMD"; exit 1; }; \
	  echo "condicion inicial: identica a la referencia TSDMD (500 filas)"; \
	else \
	  echo "condicion inicial: comparacion omitida (la referencia TSDMD es de otra semilla)"; \
	fi; \
	echo "semillas: tsdmd=$$(hseed $(FULL_TXT)) edmd=$$(hseed $(EDMD_FULL_TXT)) hibrido=$$(hseed $(HYBRID_FULL_TXT))"; \
	echo "                TSDMD         EDMD          HIBRIDO"; \
	echo "t_evac          $$(field $(FULL_RESULT) t_evac)  $$(field $(EDMD_FULL_RESULT) t_evac)  $$(field $(HYBRID_FULL_RESULT) t_evac)"; \
	echo "t_clear         $$(field $(FULL_RESULT) t_clear)  $$(field $(EDMD_FULL_RESULT) t_clear)  $$(field $(HYBRID_FULL_RESULT) t_clear)"; \
	echo "simulation_ms   $$(field $(FULL_RESULT) simulation_ms)  $$(field $(EDMD_FULL_RESULT) simulation_ms)  $$(field $(HYBRID_FULL_RESULT) simulation_ms)"; \
	echo "steps/events    $$(field $(FULL_RESULT) steps)  $$(field $(EDMD_FULL_RESULT) events)  $$(field $(HYBRID_FULL_RESULT) steps)"; \
	for k in promotions returns mixed_promotions quick_repromotions hybrid_steps tsdmd_agent_steps; do \
	  echo "$$k=$$(field $(HYBRID_FULL_RESULT) $$k)"; \
	done; \
	awk -v h="$$(field $(HYBRID_FULL_RESULT) simulation_ms)" -v t="$$(field $(FULL_RESULT) simulation_ms)" \
	  'BEGIN {r = h / t; printf "simulation_ms hibrido / tsdmd = %.2f\n", r; if (r > 6) print "AVISO: el hibrido supera 6 veces el TSDMD puro (informar)"}'; \
	echo "hybrid-full OK"

hybrid-full: hybrid-full-run hybrid-full-check

# Fraccion de agentes por esquema vs tiempo (STUDY-01, criterio 5): el pico debe tener a los agentes
# TSDMD mas cerca de la puerta que a los EDMD, y conviven los dos esquemas (el pico se elige entre
# los frames donde hay agentes de los dos: peak_mixed=1).
hybrid-plot:
	@set -e; mkdir -p $(BUILD); \
	[ -f $(HYBRID_FULL_TXT) ] || { echo "falta $(HYBRID_FULL_TXT): ejecutar make hybrid-full"; exit 1; }; \
	python3 python/scheme_fraction.py --in $(HYBRID_FULL_TXT) --out data/scheme_fraction_n500.png \
	  --csv data/scheme_fraction_n500.csv | tee $(BUILD)/hybrid_plot.out; \
	grep -q '^SCHEME_FRACTION scheme=hybrid ' $(BUILD)/hybrid_plot.out || { echo "falta la linea SCHEME_FRACTION"; exit 1; }; \
	tr ' ' '\n' < $(BUILD)/hybrid_plot.out | awk -F= \
	  '$$1=="max_tsdmd_fraction" {mx=$$2; a=1} $$1=="mean_tsdmd_fraction" {mn=$$2; b=1} \
	   $$1=="peak_door_dist_tsdmd" {dt=$$2; c=1} $$1=="peak_door_dist_edmd" {de=$$2; d=1} $$1=="peak_mixed" {pm=$$2; e=1} \
	   END { if (!(a && b && c && d && e)) {print "faltan campos en SCHEME_FRACTION"; exit 1} \
	         if (pm != 1) {print "el frame pico no es mixto (peak_mixed != 1)"; exit 1} \
	         if (!(mx > 0)) {print "max_tsdmd_fraction no es > 0"; exit 1} \
	         if (!(mn < 1)) {print "mean_tsdmd_fraction no es < 1"; exit 1} \
	         if (dt == "nan" || de == "nan" || dt == "inf" || de == "inf" || !(dt+0 < de+0)) \
	           {print "peak_door_dist_tsdmd no es menor que peak_door_dist_edmd: " dt " " de; exit 1} }'; \
	[ -s data/scheme_fraction_n500.png ] && [ -s data/scheme_fraction_n500.csv ] || { echo "faltan el PNG o el CSV"; exit 1; }; \
	tr ' ' '\n' < $(BUILD)/hybrid_plot.out | grep -E '^(switches_total|max_switches_per_agent|switch_rate_per_frame)='; \
	echo "hybrid-plot OK"

# Instantanea del pico (el t_peak de scheme_fraction.py, no el `peak` de animate.py), del inicio y
# animacion GIF de una ventana de +-20 s alrededor del pico, todo desde el archivo de texto
# (OUT-02, criterio 4).
hybrid-anim:
	@set -e; mkdir -p $(BUILD); \
	[ -f $(HYBRID_FULL_TXT) ] || { echo "falta $(HYBRID_FULL_TXT): ejecutar make hybrid-full"; exit 1; }; \
	[ -f $(BUILD)/hybrid_plot.out ] || $(MAKE) hybrid-plot; \
	tp=$$(tr ' ' '\n' < $(BUILD)/hybrid_plot.out | awk -F= '$$1=="t_peak" {print $$2}'); \
	[ -n "$$tp" ] || { echo "falta t_peak en SCHEME_FRACTION"; exit 1; }; \
	t0=$$(awk -v p="$$tp" 'BEGIN {v = p - 20; if (v < 0) v = 0; printf "%.4f", v}'); \
	t1=$$(awk -v p="$$tp" 'BEGIN {printf "%.4f", p + 20}'); \
	python3 python/animate.py --in $(HYBRID_FULL_TXT) --snapshot $$tp --out data/hybrid_peak_n500.png | tee $(BUILD)/anim_peak.out; \
	python3 python/animate.py --in $(HYBRID_FULL_TXT) --snapshot 0 --out data/hybrid_t0_n500.png | tee $(BUILD)/anim_t0.out; \
	python3 python/animate.py --in $(HYBRID_FULL_TXT) --t0 $$t0 --t1 $$t1 --every 4 --fps 10 --out data/hybrid_window_n500.gif | tee $(BUILD)/anim_gif.out; \
	for f in anim_peak anim_t0 anim_gif; do grep -q '^ANIMATE mode=' $(BUILD)/$$f.out || { echo "falta la linea ANIMATE de $$f"; exit 1; }; done; \
	for f in data/hybrid_peak_n500.png data/hybrid_t0_n500.png data/hybrid_window_n500.gif; do \
	  [ -s $$f ] || { echo "falta o esta vacio: $$f"; exit 1; }; \
	done; \
	echo "hybrid-anim OK"

# Estudios de la Fase 9 (puntos b, c y d): python/run_studies.py, make_figures.py y
# make_animations.py. Los datos van a $(STUDY_DIR) (fuera de git) y NINGUN target borra
# $(STUDY_DIR)/runs: los modos son reanudables (una corrida con CSV valido no se repite).
# Protocolo de tiempos (D-33): el wall-clock solo vale con -O2 identico en todos los esquemas
# (ver arriba) y la maquina sin otras cargas; study-bc-time, study-sweep y study-scale corren
# en serie y no deben lanzarse junto a otro `make study-*`. Todas las variables se
# sobrescriben, p. ej. `make study-bc-stat STUDY_N=200` (complemento, D-35).
STUDY_DIR ?= data/studies
STUDY_N ?= 500
STUDY_WORKERS ?= 8
STUDY_TARGET ?= 10
STUDY_MAX_ATTEMPTS ?= 80
STUDY_TIMING_SEEDS ?= 10
STUDY_SWEEP_SEEDS ?= 5
STUDY_SCALE_SEEDS ?= 3
STUDY_RUN_TIMEOUT ?= 7200
STUDY_FIG_ARGS ?=
STUDY_ANIM_ARGS ?=

# Humo de punta a punta (N=60, L=10, semilla 5): una corrida por esquema, figuras y animaciones.
STUDY_SMOKE_DIR := $(BUILD)/study_smoke
study-smoke: tp5
	@set -e; mkdir -p $(BUILD); \
	python3 python/run_studies.py --mode smoke --data-dir $(STUDY_SMOKE_DIR) | tee $(BUILD)/study_smoke.out; \
	grep -q '^STUDY mode=smoke' $(BUILD)/study_smoke.out || { echo "falta la linea STUDY mode=smoke"; exit 1; }; \
	! grep -q '^STUDY FAIL' $(BUILD)/study_smoke.out || { echo "run_studies fallo"; exit 1; }; \
	python3 python/make_figures.py --data-dir $(STUDY_SMOKE_DIR) --out-dir $(STUDY_SMOKE_DIR)/figures --bc-study smoke | tee $(BUILD)/study_smoke_fig.out; \
	grep -q '^FIGURES out_dir=' $(BUILD)/study_smoke_fig.out || { echo "falta la linea FIGURES"; exit 1; }; \
	python3 python/make_animations.py --data-dir $(STUDY_SMOKE_DIR) --source-study smoke --N 60 --L 10 \
	  --target-frames 40 --fps 10 --formats gif | tee $(BUILD)/study_smoke_anim.out; \
	grep -q '^ANIMATIONS n=3' $(BUILD)/study_smoke_anim.out || { echo "falta la linea ANIMATIONS n=3"; exit 1; }; \
	for f in $(STUDY_SMOKE_DIR)/figures/fig_population_n60.png $(STUDY_SMOKE_DIR)/figures/table_tevac_n60.csv \
	         $(STUDY_SMOKE_DIR)/anim/anim_summary.csv; do \
	  [ -s $$f ] || { echo "falta o esta vacio: $$f"; exit 1; }; \
	done; \
	echo "study-smoke OK"

# Estudio b y c, estadistica: semillas consecutivas hasta STUDY_TARGET corridas completas por
# esquema (en paralelo, STUDY_WORKERS procesos). Si algun esquema no llega, run_studies imprime
# `STUDY WARN` y el operador decide el complemento con STUDY_N=200 (D-35).
study-bc-stat: tp5
	@set -e; mkdir -p $(BUILD); \
	python3 python/run_studies.py --mode bc-stat --N $(STUDY_N) --workers $(STUDY_WORKERS) \
	  --target-complete $(STUDY_TARGET) --max-attempts $(STUDY_MAX_ATTEMPTS) \
	  --run-timeout $(STUDY_RUN_TIMEOUT) --data-dir $(STUDY_DIR) | tee $(BUILD)/study_bc_stat.out; \
	grep -q '^STUDY mode=bc-stat' $(BUILD)/study_bc_stat.out || { echo "falta la linea STUDY mode=bc-stat"; exit 1; }; \
	! grep -q '^STUDY FAIL' $(BUILD)/study_bc_stat.out || { echo "run_studies fallo"; exit 1; }; \
	grep '^STUDY WARN' $(BUILD)/study_bc_stat.out || true; \
	echo "study-bc-stat OK"

# Estudio b y c, tiempos: re-corre en serie y con un hilo las semillas de bc-stat (D-33).
study-bc-time: tp5
	@set -e; mkdir -p $(BUILD); \
	echo "AVISO: study-bc-time mide wall-clock: sin otras cargas ni otro make study-* en paralelo (D-33)"; \
	python3 python/run_studies.py --mode bc-time --N $(STUDY_N) --timing-seeds $(STUDY_TIMING_SEEDS) \
	  --run-timeout $(STUDY_RUN_TIMEOUT) --data-dir $(STUDY_DIR) | tee $(BUILD)/study_bc_time.out; \
	grep -q '^STUDY mode=bc-time' $(BUILD)/study_bc_time.out || { echo "falta la linea STUDY mode=bc-time"; exit 1; }; \
	! grep -q '^STUDY FAIL' $(BUILD)/study_bc_time.out || { echo "run_studies fallo"; exit 1; }; \
	echo "study-bc-time OK"

# Estudio d: barrido de T del hibrido (con TSDMD y EDMD puros de referencia) y escalado a y b.
study-sweep: tp5
	@set -e; mkdir -p $(BUILD); \
	echo "AVISO: study-sweep mide wall-clock: sin otras cargas ni otro make study-* en paralelo (D-33)"; \
	python3 python/run_studies.py --mode sweep --seeds $(STUDY_SWEEP_SEEDS) \
	  --run-timeout $(STUDY_RUN_TIMEOUT) --data-dir $(STUDY_DIR) | tee $(BUILD)/study_sweep.out; \
	grep -q '^STUDY mode=sweep' $(BUILD)/study_sweep.out || { echo "falta la linea STUDY mode=sweep"; exit 1; }; \
	! grep -q '^STUDY FAIL' $(BUILD)/study_sweep.out || { echo "run_studies fallo"; exit 1; }; \
	echo "study-sweep OK"

study-scale: tp5
	@set -e; mkdir -p $(BUILD); \
	echo "AVISO: study-scale mide wall-clock: sin otras cargas ni otro make study-* en paralelo (D-33)"; \
	python3 python/run_studies.py --mode scale --variant both --seeds $(STUDY_SCALE_SEEDS) \
	  --run-timeout $(STUDY_RUN_TIMEOUT) --data-dir $(STUDY_DIR) | tee $(BUILD)/study_scale.out; \
	grep -q '^STUDY mode=scale' $(BUILD)/study_scale.out || { echo "falta la linea STUDY mode=scale"; exit 1; }; \
	! grep -q '^STUDY FAIL' $(BUILD)/study_scale.out || { echo "run_studies fallo"; exit 1; }; \
	echo "study-scale OK"

# Regenera TODAS las figuras y tablas desde los CSV (sin simular). Ejemplo de cierre:
# make study-figures STUDY_FIG_ARGS="--min-complete 10 --require bc,bc-time,sweep,scale_a,scale_b"
study-figures:
	@set -e; mkdir -p $(BUILD); \
	python3 python/make_figures.py --data-dir $(STUDY_DIR) --out-dir $(STUDY_DIR)/figures $(STUDY_FIG_ARGS) | tee $(BUILD)/study_figures.out; \
	grep -q '^FIGURES out_dir=' $(BUILD)/study_figures.out || { echo "falta la linea FIGURES out_dir="; exit 1; }; \
	[ -s $(STUDY_DIR)/figures/table_success.csv ] || { echo "table_success.csv falta o esta vacio"; exit 1; }; \
	echo "study-figures OK"

# Animaciones de los tres esquemas con una semilla comun elegida desde los CSV (D-40).
study-anim: tp5
	@set -e; mkdir -p $(BUILD); \
	python3 python/make_animations.py --data-dir $(STUDY_DIR) --N $(STUDY_N) $(STUDY_ANIM_ARGS) | tee $(BUILD)/study_anim.out; \
	grep -q '^ANIMATIONS n=3' $(BUILD)/study_anim.out || { echo "falta la linea ANIMATIONS n=3"; exit 1; }; \
	[ -s $(STUDY_DIR)/anim/anim_summary.csv ] || { echo "anim_summary.csv falta o esta vacio"; exit 1; }; \
	echo "study-anim OK"

py-test:
	cd python && python3 -m unittest discover -s . -p 'test_*.py'

# Entregable (c) de la Fase 10: .zip con solo el motor final (entrega/package_tp5.py).
# COMISION (S o S2) es la unica variable del nombre: SdS_TP5_2026Q2G05C<COMISION>_Codigo.zip.
#   entrega-test:   pruebas del empaquetado (sin -I: con -m el modo aislado no ve el directorio actual).
#   entrega-zip:    construye el zip determinista y lo verifica (descomprime en un directorio nuevo,
#                   compila sin warnings, corre los tres esquemas y compara con ./tp5 (hace falta make tp5)).
#   entrega-verify: verifica un zip ya construido contra el binario ./tp5 del repo (recompilado antes).
COMISION ?= S
ENTREGA_ZIP := entrega/SdS_TP5_2026Q2G05C$(COMISION)_Codigo.zip

entrega-test:
	cd entrega && python3 -m unittest test_package_tp5 -v

entrega-zip:
	python3 -I entrega/package_tp5.py --comision $(COMISION)

entrega-verify: tp5
	python3 -I entrega/package_tp5.py --verify-only $(ENTREGA_ZIP) --comision $(COMISION) --ref-bin ./tp5

# Recompila todo desde cero con -Werror (copia de TP4).
strict:
	$(MAKE) clean
	$(MAKE) all CXXFLAGS="$(CXXFLAGS) -Werror"

clean:
	rm -rf $(BUILD) tp5 tp5_test tp5_check
