import time
import subprocess
import requests

BACKEND_URL = "https://pagepadre.onrender.com"
PC_ID = "pc-oficina-1"
INTERVALO_SONDEO = 8  # segundos

def ejecutar_job(job_id: str, comando: str):
    proceso = subprocess.Popen(
        comando,
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )

    # Va leyendo línea por línea y reportándola al backend en vivo
    for linea in proceso.stdout:
        linea = linea.rstrip()
        print(linea)  # para que también lo veas en tu propia terminal
        try:
            requests.post(
                f"{BACKEND_URL}/agente/jobs/{job_id}/log",
                params={"linea": linea, "stream": "stdout"},
                timeout=5,
            )
        except requests.RequestException:
            pass  # si falla el reporte, seguimos ejecutando igual

    exit_code = proceso.wait()
    error_mensaje = None if exit_code == 0 else f"El script terminó con código {exit_code}"

    requests.post(
        f"{BACKEND_URL}/agente/jobs/{job_id}/finalizar",
        params={"exit_code": exit_code, "error_mensaje": error_mensaje},
        timeout=5,
    )

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
                ejecutar_job(job_id, comando)
                esperar_confirmacion_y_actuar(job_id, comando)

        except requests.RequestException as e:
            print(f"No se pudo contactar al backend: {e}")

        time.sleep(INTERVALO_SONDEO)

if __name__ == "__main__":
    loop_principal()