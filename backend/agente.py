import time
import subprocess
import requests
import threading

BACKEND_URL = "https://pagepadre.onrender.com"
PC_ID = "pc-andres"
INTERVALO_SONDEO = 8  # segundos

def matar_arbol_proceso(pid):
    # En Windows, terminate() solo mata el cmd.exe, no al python.exe hijo.
    # taskkill /T mata todo el árbol de procesos.
    subprocess.call(["taskkill", "/F", "/T", "/PID", str(pid)],
                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def ejecutar_job(job_id: str, comando: str):
    proceso = subprocess.Popen(
        comando, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        text=True, bufsize=1,
    )

    cancelado = threading.Event()

    def vigilar_cancelacion():
        while proceso.poll() is None:  # mientras el proceso siga vivo
            try:
                job = requests.get(f"{BACKEND_URL}/jobs/{job_id}", timeout=5).json()
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
        print(linea)
        try:
            requests.post(
                f"{BACKEND_URL}/agente/jobs/{job_id}/log",
                params={"linea": linea, "stream": "stdout"}, timeout=5,
            )
        except requests.RequestException:
            pass

    proceso.wait()

    if cancelado.is_set():
        print(f"Job {job_id} cancelado por el usuario.")
        requests.post(f"{BACKEND_URL}/agente/jobs/{job_id}/cancelado", timeout=5)
        return "cancelado"

    exit_code = proceso.returncode
    error_mensaje = None if exit_code == 0 else f"El script terminó con código {exit_code}"
    requests.post(
        f"{BACKEND_URL}/agente/jobs/{job_id}/finalizar",
        params={"exit_code": exit_code, "error_mensaje": error_mensaje}, timeout=5,
    )
    return "normal"

def esperar_confirmacion_y_actuar(job_id: str, comando: str):
    # Aquí el agente espera a que TÚ confirmes desde el dashboard
    while True:
        resp = requests.get(f"{BACKEND_URL}/jobs/{job_id}", timeout=5).json()
        accion = resp.get("accion_usuario")

        if accion == "enviar_correo":
            # el propio script ya sabe mandar su correo (SMTP dentro del .py),
            # o aquí disparas ese envío como paso aparte
            exito = True  # reemplaza con el resultado real del envío
            requests.post(
                f"{BACKEND_URL}/agente/jobs/{job_id}/correo-enviado",
                params={"exito": exito}, timeout=5,
            )
            return
        elif accion == "reejecutar_sin_correo":
            ejecutar_job(job_id, comando)
            esperar_confirmacion_y_actuar(job_id, comando)
            return

        time.sleep(3)

def loop_principal():
    print("Agente iniciado, esperando trabajos...")
    while True:
        try:
            resp = requests.get(
                f"{BACKEND_URL}/agente/pendientes",
                params={"pc_id": PC_ID}, timeout=5,
            ).json()

            if resp.get("job_id"):
                job_id = resp["job_id"]
                comando = resp["comando"]
                print(f"Ejecutando job {job_id}: {comando}")
                resultado = ejecutar_job(job_id, comando)

                if resultado == "normal":
                    job_actual = requests.get(f"{BACKEND_URL}/jobs/{job_id}", timeout=5).json()
                    if job_actual["estado"] == "esperando_confirmacion":
                        esperar_confirmacion_y_actuar(job_id, comando)

        except requests.RequestException as e:
            print(f"No se pudo contactar al backend: {e}")

        time.sleep(INTERVALO_SONDEO)

if __name__ == "__main__":
    loop_principal()