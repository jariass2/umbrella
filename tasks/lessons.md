# Lecciones

## No reiniciar el dashboard Flask mientras hay un run en curso (2026-06-03)

**Qué pasó:** Para cargar un cambio de plantilla, reinicié `flask_app.py` (kill + relanzar) mientras el run 39 tenía a Etiqueta en ejecución. El subproceso del orquestador (Popen) sobrevivió al kill, pero su stdout escribe a un pipe leído por el hilo consumidor de Flask; al morir Flask, ese pipe se rompió y el orquestador murió a mitad de Etiqueta. Run 39 quedó incompleto (sin Etiqueta ni informe) y hubo que marcarlo error.

**Regla:** Antes de reiniciar/matar el dashboard, comprobar que NO hay pipeline corriendo (`pgrep -f pipeline.orchestrator` y estado de runs en DB). Si lo hay, esperar a que termine, o avisar al usuario y pedir confirmación. Flask cachea plantillas sin debug, pero un cambio de plantilla/JS no justifica tirar un run en curso.

**Mejor aún:** para ver cambios de plantilla sin reiniciar, arrancar con `FLASK_DEBUG=1` (reloader + auto-reload de plantillas) cuando no haya runs activos.

## Mantener partials OOB de HTMX sincronizados con la plantilla principal (2026-06-10)

**Qué pasó:** Tras añadir el campo "Activo" (dosis de activo) al formulario en `index.html` durante la Fase 7, el usuario reportó que el campo no aparecía al recargar un run desde el historial. Dos causas concurrentes:

1. `dashboard/templates/partials/sidebar_oob.html` (el partial que se sirve out-of-band al hacer click en un run del historial) **se quedó en el layout antiguo de 3 campos** (`ing_name`, `ing_dosage`, `ing_unit`). Le faltaban los nuevos `ing_active`, `ing_active_name`, `ing_pct`.
2. `load_run()` en `flask_app.py` no leía `outputs/run_X/formula_canonica.json`, que es donde se persiste la dosis de activo desde el POST /analyze. Solo parseaba `formula_text`, que solo contiene materia prima (la activo se guarda a propósito en un archivo separado porque el `formula_text` alimenta al pipeline y la activo es un dato de cliente/confidencialidad).

**Regla:** Cuando se añade o renombra un campo en el formulario del sidebar, hay que tocar **dos** plantillas a la vez: `index.html` (form inicial) **y** `partials/sidebar_oob.html` (form OOB en reload de runs desde historial). Mejor aún: extraer un macro Jinja `{% macro ingredient_row(ing) %}` y usarlo en ambos sitios. Y siempre que un dato persista en un sitio distinto de la fuente canónica (`formula_canonica.json` aquí), añadir el path de lectura en `load_run` con un test de regresión (`test_load_run_rellena_campo_activo_desde_canonica`).

