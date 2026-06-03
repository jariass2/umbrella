# Lecciones

## No reiniciar el dashboard Flask mientras hay un run en curso (2026-06-03)

**Qué pasó:** Para cargar un cambio de plantilla, reinicié `flask_app.py` (kill + relanzar) mientras el run 39 tenía a Etiqueta en ejecución. El subproceso del orquestador (Popen) sobrevivió al kill, pero su stdout escribe a un pipe leído por el hilo consumidor de Flask; al morir Flask, ese pipe se rompió y el orquestador murió a mitad de Etiqueta. Run 39 quedó incompleto (sin Etiqueta ni informe) y hubo que marcarlo error.

**Regla:** Antes de reiniciar/matar el dashboard, comprobar que NO hay pipeline corriendo (`pgrep -f pipeline.orchestrator` y estado de runs en DB). Si lo hay, esperar a que termine, o avisar al usuario y pedir confirmación. Flask cachea plantillas sin debug, pero un cambio de plantilla/JS no justifica tirar un run en curso.

**Mejor aún:** para ver cambios de plantilla sin reiniciar, arrancar con `FLASK_DEBUG=1` (reloader + auto-reload de plantillas) cuando no haya runs activos.
