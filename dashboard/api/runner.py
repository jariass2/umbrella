"""Ejecuta el pipeline en un thread background, empujando eventos de estado a una Queue."""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import threading
import time
from pathlib import Path
from queue import Queue, Empty
from pipeline.config import build_agent_env_overrides

PROJECT_ROOT = str(Path(__file__).resolve().parent.parent.parent)

# Orden lógico para el dashboard (respeta el flujo regulatorio principal primero)
AGENT_ORDER = [
    "KIC",
    "Regulatorio",
    "Ficha Técnica",
    "Claims",
    "Etiqueta",
    "Formatos",
    "Docs Internos",
    "QC",
    "Portfolio",
]

# Agent key → prefijo numérico en el label del pipeline
_AGENT_NUM = {
    "KIC": 1, "Regulatorio": 2, "Ficha Técnica": 3, "Claims": 4,
    "Etiqueta": 5, "Formatos": 6, "Docs Internos": 7, "QC": 8,
    "Portfolio": 9,
}

# Agent key → nombre del fichero de salida (sin extensión)
_AGENT_FILENAME = {
    "KIC": "agente_1_kic_v2",
    "Regulatorio": "agente_2_regulatorio_v2",
    "Ficha Técnica": "agente_3_ficha_técnica_v2",
    "Claims": "agente_4_claims_v2",
    "Etiqueta": "agente_5_etiqueta_v2",
    "Formatos": "agente_6_formatos_v2",
    "Docs Internos": "agente_7_docs_internos_v2",
    "QC": "agente_8_qc_v2",
    "Portfolio": "agente_9_portfolio_v2",
}
_KNOWN_PROVIDER_KEYS = (
    "OPENROUTER_API_KEY",
    "OPENAI_API_KEY",
    "ANTHROPIC_API_KEY",
    "GEMINI_API_KEY",
    "ZAI_API_KEY",
)


def _agent_key_from_label(label: str) -> str | None:
    """Extrae la key del agente desde un label como 'Agente 3: Ficha Técnica v2'."""
    m = re.match(r"Agente (\d+):", label)
    if not m:
        return None
    num = int(m.group(1))
    for key, n in _AGENT_NUM.items():
        if n == num:
            return key
    return None


def _build_runtime_env(
    agent_settings: dict[str, dict[str, object]] | None = None,
    provider_api_keys: dict[str, str] | None = None,
) -> dict[str, str]:
    """Construye el entorno del subprocess con overrides opcionales por agente/proveedor."""
    runtime_env = {**os.environ, "PYTHONUNBUFFERED": "1"}

    # Permite inyectar claves de proveedor desde UI sin tocar el .env local.
    if provider_api_keys:
        for key in _KNOWN_PROVIDER_KEYS:
            raw = provider_api_keys.get(key) or provider_api_keys.get(key.lower())
            if raw is None:
                continue
            value = str(raw).strip()
            if value:
                runtime_env[key] = value

    # Permite setear model/base_url/api_key/temperature por agente para este run.
    runtime_env.update(build_agent_env_overrides(agent_settings))
    return runtime_env


def run_pipeline(
    formula_text: str,
    output_dir: str,
    status_queue: Queue,
    agent_settings: dict[str, dict[str, object]] | None = None,
    provider_api_keys: dict[str, str] | None = None,
):
    """Ejecuta el pipeline como subproceso, monitorizando stdout y ficheros de salida."""
    os.makedirs(output_dir, exist_ok=True)

    for agent in AGENT_ORDER:
        status_queue.put({"agent": agent, "status": "waiting"})

    proc = subprocess.Popen(
        [sys.executable, "-m", "pipeline.orchestrator",
         "--formula-text", formula_text,
         "--output-dir", output_dir],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        cwd=PROJECT_ROOT,
        env=_build_runtime_env(
            agent_settings=agent_settings,
            provider_api_keys=provider_api_keys,
        ),
    )
    status_queue.put({"type": "process", "pid": proc.pid})

    # Thread para leer stdout sin bloquear.
    # Cada línea se duplica a la Queue (para el dashboard) y a pipeline.log
    # (para diagnóstico — incluye stderr porque el Popen lo mergea en stdout).
    stdout_lines: Queue[str] = Queue()
    log_path = os.path.join(output_dir, "pipeline.log")

    def _reader():
        with open(log_path, "w", encoding="utf-8", buffering=1) as logf:
            for line in proc.stdout:
                stdout_lines.put(line)
                try:
                    logf.write(line)
                except OSError:
                    pass

    reader = threading.Thread(target=_reader, daemon=True)
    reader.start()

    seen_files: set[str] = set()
    running_agents: set[str] = set()

    while proc.poll() is None or not stdout_lines.empty():
        # Procesar líneas de stdout
        while True:
            try:
                line = stdout_lines.get_nowait()
            except Empty:
                break
            stripped = line.strip()

            # Detectar inicio de agente: "Agente N: Nombre v2"
            if stripped.startswith("Agente "):
                key = _agent_key_from_label(stripped)
                if key:
                    running_agents.add(key)
                    status_queue.put({"agent": key, "status": "running"})

            # Detectar JSON guardado: "✅ JSON guardado en ..."
            if "JSON guardado" in stripped:
                # Detectar finalización de agente por fichero
                pass

        # Comprobar ficheros de salida completados
        for agent_key, filename in _AGENT_FILENAME.items():
            if filename in seen_files:
                continue
            json_path = os.path.join(output_dir, f"{filename}.json")
            md_path = os.path.join(output_dir, f"{filename}.md")
            if os.path.exists(json_path):
                # Esperar brevemente a que el fichero se termine de escribir
                time.sleep(0.3)
                try:
                    with open(json_path, encoding="utf-8") as f:
                        data = json.load(f)
                except (json.JSONDecodeError, OSError):
                    continue

                if not isinstance(data, dict):
                    data = {"_payload": data}

                md_content = None
                if os.path.exists(md_path):
                    try:
                        md_content = Path(md_path).read_text(encoding="utf-8")
                    except OSError:
                        pass

                duration = None
                trace = data.get("_trazabilidad", {})
                if isinstance(trace, dict):
                    duration = trace.get("duration_s")

                # Un agente puede escribir su JSON pero con solo un dict de error
                # (p. ej. fallo de parseo del LLM). No es "completado": marcarlo
                # como error para que el dashboard no lo pinte OK con datos vacíos.
                is_error = "error" in data and set(data.keys()) <= {"error", "_trazabilidad"}

                seen_files.add(filename)
                running_agents.discard(agent_key)
                status_queue.put({
                    "agent": agent_key,
                    "status": "error" if is_error else "completed",
                    "data": data,
                    "output_md": md_content,
                    "duration_s": duration,
                })

        time.sleep(0.5)

    # Procesar stdout restante
    while True:
        try:
            line = stdout_lines.get_nowait()
            if line.strip().startswith("Agente "):
                key = _agent_key_from_label(line.strip())
                if key:
                    status_queue.put({"agent": key, "status": "running"})
        except Empty:
            break

    # Comprobar ficheros una última vez
    for agent_key, filename in _AGENT_FILENAME.items():
        if filename in seen_files:
            continue
        json_path = os.path.join(output_dir, f"{filename}.json")
        if os.path.exists(json_path):
            try:
                with open(json_path, encoding="utf-8") as f:
                    data = json.load(f)
            except (json.JSONDecodeError, OSError):
                data = {}
            md_content = None
            md_path = os.path.join(output_dir, f"{filename}.md")
            if os.path.exists(md_path):
                try:
                    md_content = Path(md_path).read_text(encoding="utf-8")
                except OSError:
                    pass
            seen_files.add(filename)
            trace = data.get("_trazabilidad", {})
            duration = trace.get("duration_s") if isinstance(trace, dict) else None
            status_queue.put({
                "agent": agent_key,
                "status": "completed",
                "data": data,
                "output_md": md_content,
                "duration_s": duration,
            })

    # Marcar agentes que no completaron como error
    for agent_key in AGENT_ORDER:
        if _AGENT_FILENAME[agent_key] not in seen_files:
            status_queue.put({"agent": agent_key, "status": "error"})

    status_queue.put({"pipeline": "completed"})
