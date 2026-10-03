"""Registro de avisos de una ejecución del pipeline.

Hasta el 2026-08-29 los controles que SÍ detectaban problemas escribían a
stdout y ahí morían. El runner del dashboard (`dashboard/api/runner.py`)
solo parsea dos patrones de stdout — «Agente N:» y «JSON guardado» — y
descarta el resto, así que un run con drift de schema, fuga de idioma o
incoherencias en la fórmula canónica se pintaba en verde y el informe
salía con el problema dentro. Quien trabaja desde el dashboard nunca veía
la alarma.

Este módulo centraliza esos avisos en `avisos.json`, dentro del output_dir
del run. Es el fichero que leen luego el informe (sección «Avisos de la
ejecución») y el dashboard. Un aviso no bloquea nada: describe.

Severidades:
  alta  — la cifra publicada puede estar mal; no decidir sobre ella.
  media — contradicción o desviación que hay que mirar antes de entregar.
  info  — desviación menor, trazabilidad.
"""

from __future__ import annotations

import json
import os
import threading
from datetime import datetime

FICHERO = "avisos.json"

SEVERIDADES = ("alta", "media", "info")

_EMOJI = {"alta": "⛔", "media": "⚠️ ", "info": "ℹ️ "}

# Los agentes corren en un ThreadPoolExecutor, así que el read-modify-write
# del JSON necesita candado. Es un fichero pequeño y de escritura rara.
_LOCK = threading.Lock()


def _path(output_dir: str) -> str:
    return os.path.join(output_dir, FICHERO)


def limpiar(output_dir: str) -> None:
    """Borra los avisos de un run anterior en el mismo directorio.

    El orquestador reutiliza el output_dir (`--output-dir`), y arrastrar los
    avisos del run previo es el mismo bug que `_purge_stale_agent_outputs`
    resuelve para los JSON de agente: datos viejos leídos como nuevos.
    """
    with _LOCK:
        try:
            os.remove(_path(output_dir))
        except (FileNotFoundError, OSError):
            pass


def registrar(output_dir: str | None, origen: str, mensaje: str,
              severidad: str = "media") -> None:
    """Anota un aviso y lo imprime. Nunca lanza: un fallo aquí no puede
    tumbar el run que está intentando vigilar."""
    if severidad not in SEVERIDADES:
        severidad = "media"
    print(f"{_EMOJI[severidad]} [{origen}] {mensaje}")
    if not output_dir:
        return
    entrada = {
        "severidad": severidad,
        "origen": origen,
        "mensaje": mensaje,
        "ts": datetime.now().isoformat(timespec="seconds"),
    }
    with _LOCK:
        try:
            actuales = _leer_sin_lock(output_dir)
            # Un mismo control puede dispararse en varias fases; el aviso
            # repetido literalmente no aporta nada y ensucia el informe.
            if any(a.get("origen") == origen and a.get("mensaje") == mensaje
                   for a in actuales):
                return
            actuales.append(entrada)
            os.makedirs(output_dir, exist_ok=True)
            with open(_path(output_dir), "w", encoding="utf-8") as f:
                json.dump(actuales, f, ensure_ascii=False, indent=2)
        except OSError:
            pass


def _leer_sin_lock(output_dir: str) -> list[dict]:
    try:
        with open(_path(output_dir), encoding="utf-8") as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return []
    return [a for a in data if isinstance(a, dict)] if isinstance(data, list) else []


def ordenar(avisos: list[dict]) -> list[dict]:
    """Alta primero: quien mira la lista tiene que ver antes lo que invalida
    una cifra que lo que solo la matiza."""
    orden = {s: i for i, s in enumerate(SEVERIDADES)}
    return sorted(avisos, key=lambda a: orden.get(a.get("severidad", "media"), 1))


def cargar(output_dir: str | None) -> list[dict]:
    """Avisos del run, ordenados por severidad (alta primero)."""
    if not output_dir:
        return []
    with _LOCK:
        avisos = _leer_sin_lock(output_dir)
    return ordenar(avisos)


def resumen(avisos: list[dict]) -> dict[str, int]:
    """Cuenta por severidad. Lo usa el dashboard para el badge del run."""
    out = {s: 0 for s in SEVERIDADES}
    for a in avisos:
        sev = a.get("severidad", "media")
        if sev in out:
            out[sev] += 1
    return out
