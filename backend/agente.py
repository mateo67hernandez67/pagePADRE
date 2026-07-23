"""
agente.py — Agente local que ejecuta los scripts en el PC de trabajo.

Flujo:
  1. Cada INTERVALO_SONDEO segundos, pregunta al backend si hay un job pendiente.
  2. Si hay uno, verifica que sus dependencias hayan finalizado hoy.
  3. Ejecuta el comando capturando stdout/stderr línea a línea.
  4. Si el script requiere confirmación de correo, espera la decisión del usuario
     en el dashboard antes de continuar.
  5. Reporta el resultado final al backend.
"""

import time
import subprocess
import requests
import threading
import os
import sys
from datetime import date

# Forzar UTF-8 en la consola del agente (Windows usa cp1252 por defecto)
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

BACKEND_URL     = "https://pagepadre-akhc.onrender.com"
PC_ID           = "pc-andres"
INTERVALO_SONDEO = 8   # segundos


# ─────────────────────────────────────────────────────────────────────────────
# Utilidades
# ─────────────────────────────────────────────────────────────────────────────

def matar_arbol_proceso(pid):
    """En Windows, terminate() solo mata el cmd.exe.
    taskkill /T mata todo el árbol de procesos (el python.exe hijo incluido)."""
    subprocess.call(
        ["taskkill", "/F", "/T", "/PID", str(pid)],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )


def log_job(job_id: str, linea: str, stream: str = "stdout"):
    """Envía una línea de log al backend. Falla silenciosamente."""
    try:
        requests.post(
            f"{BACKEND_URL}/agente/jobs/{job_id}/log",
            params={"linea": linea, "stream": stream}, timeout=5,
        )
    except requests.RequestException:
        pass


def get_job(job_id: str) -> dict:
    """Obtiene el estado actual de un job desde el backend."""
    return requests.get(f"{BACKEND_URL}/jobs/{job_id}", timeout=5).json()


# ─────────────────────────────────────────────────────────────────────────────
# Verificación de dependencias
# ─────────────────────────────────────────────────────────────────────────────

def dependencias_cumplidas(dependencias: list) -> tuple[bool, list]:
    """
    Comprueba que todos los scripts en 'dependencias' hayan finalizado
    exitosamente HOY (estado == "finalizado" y finalizado_en del día de hoy).

    Retorna (True, []) si todo OK, o (False, [nombres_pendientes]) si falta alguno.
    """
    if not dependencias:
        return True, []

    hoy = date.today().isoformat()   # "2026-07-22"
    pendientes = []

    try:
        # Obtener lista de jobs del día de hoy
        todos_los_jobs = requests.get(
            f"{BACKEND_URL}/jobs", params={"limite": 100}, timeout=5
        ).json()
    except requests.RequestException:
        # Si no podemos consultar, bloqueamos por seguridad
        return False, dependencias

    # Construir conjunto de scripts que terminaron bien hoy
    finalizados_hoy = set()
    for job in todos_los_jobs:
        if job.get("estado") != "finalizado":
            continue
        finalizado_en = job.get("finalizado_en", "")
        if finalizado_en and finalizado_en[:10] == hoy:
            finalizados_hoy.add(job.get("nombre_script", ""))

    for dep in dependencias:
        if dep not in finalizados_hoy:
            pendientes.append(dep)

    return (len(pendientes) == 0), pendientes


# ─────────────────────────────────────────────────────────────────────────────
# Ejecución de un script
# ─────────────────────────────────────────────────────────────────────────────

def ejecutar_job(job_id: str, comando: str) -> str:
    """
    Corre el comando, envía los logs línea a línea y reporta el resultado.

    Retorna:
      "cancelado" — el usuario canceló mientras el proceso corría
      "error"     — el proceso terminó con exit_code != 0
      "ok"        — el proceso terminó exitosamente
    """
    proceso = subprocess.Popen(
        comando, shell=True,
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        text=True, bufsize=1,
        encoding="utf-8", errors="replace",
        env={**os.environ, "PYTHONIOENCODING": "utf-8", "PYTHONUNBUFFERED": "1"},
    )

    cancelado = threading.Event()

    def vigilar_cancelacion():
        """Hilo que pregunta cada 2 s si el usuario pidió cancelar."""
        while proceso.poll() is None:
            try:
                job = get_job(job_id)
                if job.get("estado") == "cancelando":
                    cancelado.set()
                    matar_arbol_proceso(proceso.pid)
                    break
            except requests.RequestException:
                pass
            time.sleep(2)

    vigilante = threading.Thread(target=vigilar_cancelacion, daemon=True)
    vigilante.start()

    for linea in proceso.stdout:
        linea = linea.rstrip()
        print(linea, flush=True)
        log_job(job_id, linea)

    proceso.wait()

    if cancelado.is_set():
        print(f"[agente] Job {job_id} cancelado por el usuario.")
        try:
            requests.post(f"{BACKEND_URL}/agente/jobs/{job_id}/cancelado", timeout=5)
        except requests.RequestException:
            pass
        return "cancelado"

    exit_code = proceso.returncode
    error_mensaje = None if exit_code == 0 else f"El script terminó con código {exit_code}"
    try:
        requests.post(
            f"{BACKEND_URL}/agente/jobs/{job_id}/finalizar",
            params={"exit_code": exit_code, "error_mensaje": error_mensaje}, timeout=5,
        )
    except requests.RequestException:
        pass

    return "ok" if exit_code == 0 else "error"


# ─────────────────────────────────────────────────────────────────────────────
# Manejo de la confirmación de correo
# ─────────────────────────────────────────────────────────────────────────────

def manejar_envio_correo(job_id: str, comando_envio: str | None, comando_original: str):
    """
    Espera a que el usuario confirme desde el dashboard y actúa según la acción elegida:
      - "enviar_correo"          → ejecuta el comando de envío (si lo hay) y reporta.
      - "reejecutar_sin_correo"  → vuelve a lanzar el script principal sin enviar.

    'comando_envio' puede ser None si el envío ya está embebido en el script principal;
    en ese caso el agente solo confirma el estado al backend.
    """
    print(f"[agente] Job {job_id} esperando confirmación en el dashboard...")

    while True:
        try:
            job = get_job(job_id)
        except requests.RequestException:
            time.sleep(3)
            continue

        accion = job.get("accion_usuario")

        if accion == "enviar_correo":
            exito = True
            if comando_envio:
                # Hay un comando separado para el envío — lo ejecutamos capturando salida
                print(f"[agente] Ejecutando envío para job {job_id}: {comando_envio}")
                log_job(job_id, "─── Iniciando envío de correo... ───")
                try:
                    proc = subprocess.Popen(
                        comando_envio, shell=True,
                        stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                        text=True, bufsize=1,
                        encoding="utf-8", errors="replace",
                        env={**os.environ, "PYTHONIOENCODING": "utf-8", "PYTHONUNBUFFERED": "1"},
                    )
                    for linea in proc.stdout:
                        linea = linea.rstrip()
                        print(linea, flush=True)
                        log_job(job_id, linea)
                    proc.wait()
                    if proc.returncode != 0:
                        exito = False
                        log_job(
                            job_id,
                            f"[agente] Error al enviar correo (código {proc.returncode})",
                            "stderr"
                        )
                    else:
                        log_job(job_id, "✅ Correo enviado correctamente.")
                except Exception as e:
                    exito = False
                    log_job(job_id, f"[agente] Excepción al ejecutar envío: {e}", "stderr")
            else:
                # Sin comando_envio: el script ya envió solo (tipo "automatico")
                # o simplemente confirmamos sin hacer nada adicional
                log_job(job_id, "✅ Envío confirmado por el usuario.")

            try:
                requests.post(
                    f"{BACKEND_URL}/agente/jobs/{job_id}/correo-enviado",
                    params={"exito": exito}, timeout=5,
                )
            except requests.RequestException:
                pass
            return

        elif accion == "reejecutar_sin_correo":
            print(f"[agente] Reejecutando job {job_id} sin enviar correo...")
            log_job(job_id, "[agente] Reejecutando sin enviar correo...")
            ejecutar_job(job_id, comando_original)
            # Después de reejecutar, el script vuelve a estado esperando_confirmacion
            manejar_envio_correo(job_id, comando_envio, comando_original)
            return

        time.sleep(3)


# ─────────────────────────────────────────────────────────────────────────────
# Loop principal del agente
# ─────────────────────────────────────────────────────────────────────────────

def loop_principal():
    print(f"[agente] Iniciado para PC_ID='{PC_ID}'. Esperando trabajos...")
    while True:
        try:
            resp = requests.get(
                f"{BACKEND_URL}/agente/pendientes",
                params={"pc_id": PC_ID}, timeout=5,
            ).json()

            if resp.get("job_id"):
                job_id        = resp["job_id"]
                comando       = resp["comando"]
                tipo_envio    = resp.get("tipo_envio", "ninguno")
                comando_envio = resp.get("comando_envio")      # None o string
                dependencias  = resp.get("dependencias", [])   # lista de nombres

                print(f"\n[agente] Job {job_id} recibido: {comando}")
                print(f"[agente]   tipo_envio={tipo_envio}, dependencias={dependencias}")

                # ── Verificar dependencias ────────────────────────────────
                ok_deps, faltantes = dependencias_cumplidas(dependencias)
                if not ok_deps:
                    msg = (
                        f"[agente] No se puede ejecutar: primero deben completarse hoy → "
                        f"{', '.join(faltantes)}"
                    )
                    print(msg)
                    log_job(job_id, msg, "stderr")
                    # Marcar el job como error para que el frontend lo muestre
                    try:
                        requests.post(
                            f"{BACKEND_URL}/agente/jobs/{job_id}/finalizar",
                            params={
                                "exit_code": 1,
                                "error_mensaje": f"Dependencias no cumplidas: {', '.join(faltantes)}"
                            },
                            timeout=5,
                        )
                    except requests.RequestException:
                        pass
                    time.sleep(INTERVALO_SONDEO)
                    continue

                # ── Ejecutar el script ────────────────────────────────────
                resultado = ejecutar_job(job_id, comando)

                if resultado == "ok":
                    job_actual = get_job(job_id)
                    estado = job_actual.get("estado")

                    if estado == "esperando_confirmacion":
                        if tipo_envio == "automatico":
                            # El script ya envió solo — solo cerramos el job
                            print(f"[agente] Job {job_id} (automatico): marcando como finalizado.")
                            try:
                                requests.post(
                                    f"{BACKEND_URL}/agente/jobs/{job_id}/correo-enviado",
                                    params={"exito": True}, timeout=5,
                                )
                            except requests.RequestException:
                                pass
                        else:
                            # El usuario debe confirmar desde el dashboard
                            manejar_envio_correo(job_id, comando_envio, comando)

                    elif estado == "finalizado":
                        print(f"[agente] Job {job_id} finalizado automáticamente.")

                elif resultado == "cancelado":
                    print(f"[agente] Job {job_id} cancelado por el usuario.")

                else:  # error
                    print(f"[agente] Job {job_id} finalizó con error.")

        except requests.RequestException as e:
            print(f"[agente] No se pudo contactar al backend: {e}")

        time.sleep(INTERVALO_SONDEO)


if __name__ == "__main__":
    loop_principal()
