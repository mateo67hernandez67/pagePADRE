from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from bson import ObjectId
from datetime import datetime
from database import scripts_col, jobs_col, logs_col

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://candid-mochi-ccd7c4.netlify.app/"],
    allow_methods=["*"],
    allow_headers=["*"],
)

def serialize(doc):
    doc["_id"] = str(doc["_id"])
    return doc

# ---------- ENDPOINTS QUE USA EL FRONTEND ----------

@app.get("/scripts")
async def listar_scripts():
    scripts = await scripts_col.find({"activo": True}).to_list(100)
    return [serialize(s) for s in scripts]

@app.post("/jobs")
async def crear_job(script_id: str):
    script = await scripts_col.find_one({"_id": ObjectId(script_id)})
    if not script:
        raise HTTPException(404, "Script no encontrado")

    job = {
        "script_id": ObjectId(script_id),
        "pc_id": script["pc_id"],
        "estado": "pendiente",
        "creado_en": datetime.utcnow(),
        "iniciado_en": None,
        "finalizado_en": None,
        "exit_code": None,
        "error_mensaje": None,
        "requiere_confirmacion": script["requiere_confirmacion_correo"],
        "estado_correo": "no_enviado",
        "correo_enviado_en": None,
        "accion_usuario": None,
    }
    result = await jobs_col.insert_one(job)
    return {"job_id": str(result.inserted_id)}

@app.get("/jobs/{job_id}")
async def ver_job(job_id: str):
    job = await jobs_col.find_one({"_id": ObjectId(job_id)})
    if not job:
        raise HTTPException(404, "Job no encontrado")
    logs = await logs_col.find({"job_id": ObjectId(job_id)}).sort("timestamp", 1).to_list(1000)
    job = serialize(job)
    job["script_id"] = str(job["script_id"])
    job["logs"] = [l["linea"] for l in logs]
    return job

@app.get("/jobs")
async def listar_jobs(limite: int = 20):
    jobs = await jobs_col.find().sort("creado_en", -1).to_list(limite)
    return [serialize(j) | {"script_id": str(j["script_id"])} for j in jobs]

@app.post("/jobs/{job_id}/action")
async def confirmar_accion(job_id: str, accion: str):
    # accion: "enviar_correo" | "reejecutar_sin_correo"
    if accion not in ("enviar_correo", "reejecutar_sin_correo"):
        raise HTTPException(400, "Acción inválida")

    await jobs_col.update_one(
        {"_id": ObjectId(job_id)},
        {"$set": {"accion_usuario": accion}}
    )
    return {"ok": True}

# ---------- ENDPOINTS QUE USA EL AGENTE (PC LOCAL) ----------

@app.get("/agente/pendientes")
async def jobs_pendientes(pc_id: str):
    job = await jobs_col.find_one_and_update(
        {"pc_id": pc_id, "estado": "pendiente"},
        {"$set": {"estado": "ejecutando", "iniciado_en": datetime.utcnow()}},
        sort=[("creado_en", 1)]
    )
    if not job:
        return {"job": None}

    script = await scripts_col.find_one({"_id": job["script_id"]})
    return {
        "job_id": str(job["_id"]),
        "comando": script["comando"],
    }

@app.post("/agente/jobs/{job_id}/log")
async def agregar_log(job_id: str, linea: str, stream: str = "stdout"):
    await logs_col.insert_one({
        "job_id": ObjectId(job_id),
        "linea": linea,
        "stream": stream,
        "timestamp": datetime.utcnow(),
    })
    return {"ok": True}

@app.post("/agente/jobs/{job_id}/finalizar")
async def finalizar_job(job_id: str, exit_code: int, error_mensaje: str | None = None):
    nuevo_estado = "esperando_confirmacion" if exit_code == 0 else "error"
    await jobs_col.update_one(
        {"_id": ObjectId(job_id)},
        {"$set": {
            "estado": nuevo_estado,
            "finalizado_en": datetime.utcnow(),
            "exit_code": exit_code,
            "error_mensaje": error_mensaje,
        }}
    )
    return {"ok": True}

@app.post("/agente/jobs/{job_id}/correo-enviado")
async def confirmar_correo_enviado(job_id: str, exito: bool):
    await jobs_col.update_one(
        {"_id": ObjectId(job_id)},
        {"$set": {
            "estado_correo": "enviado" if exito else "error_envio",
            "correo_enviado_en": datetime.utcnow() if exito else None,
            "estado": "finalizado",
        }}
    )
    return {"ok": True}