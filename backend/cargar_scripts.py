# cargar_scripts.py
# ─────────────────────────────────────────────────────────────────────────────
# Ejecutar manualmente cuando se agregue o modifique un script:
#   python cargar_scripts.py
#
# CÓMO FUNCIONA EL ENVÍO:
#   - tipo_envio = "correo"  → el script principal NO envía nada por sí solo.
#     Cuando termina con exit 0, el agente pone el job en "esperando_confirmacion".
#     El usuario ve el botón "Enviar correo" en el dashboard.
#     Al confirmar, el agente ejecuta `comando_envio` (que sí hace el envío).
#
#   - comando_envio = None   → el agente no tiene qué ejecutar para el envío.
#     Úsalo solo si el script principal ya tiene el envío embebido Y ya no llama
#     send() de forma automática (o sea, si modificaste el script para que espere).
#     En ese caso el agente solo reporta "enviado" al backend sin hacer nada más.
#     *** Para los scripts que no modificamos internamente (Brown, backlog, ClaroBox),
#     hay que dejarlos como están — ellos envían solos, así que se marcan como
#     "automatico" en vez de "correo" para que no pidan confirmación. ***
#
# ─────────────────────────────────────────────────────────────────────────────

from pymongo import MongoClient
from datetime import datetime

client = MongoClient(
    "mongodb+srv://andresgranadadev07_db_user:Mt2M69,AG%40@cluster0.azlzgay.mongodb.net/"
    "?appName=Cluster0"
)
db = client["automatizaciones"]
scripts_col = db["scripts"]

BASE  = r"D:\OneDrive - Comunicacion Celular S.A.- Comcel S.A\Escritorio\AutsAndres"
PC_ID = "pc-andres"

scripts = [

    # ── 1. Verificar Cierres ──────────────────────────────────────────────────
    # El script verifica el Excel y guarda resultado_cierres.json.
    # NO envía correo por sí solo.
    # Al confirmar en el dashboard, el agente lo vuelve a llamar con --enviar-correo
    # que lee el JSON y lo envía por Outlook.
    {
        "nombre": "Verificar Cierres",
        "descripcion": "Verifica cierres por tipo de trabajo y notifica por correo",
        "comando": f'python "{BASE}\\CierresAuto\\verificar_cierres.py"',
        "pc_id": PC_ID,
        "tipo_envio": "correo",
        "requiere_confirmacion_correo": True,
        "comando_envio": f'python "{BASE}\\CierresAuto\\verificar_cierres.py" --enviar-correo',
        "dependencias": [],
        "orden": 1,
        "activo": True,
        "creado_en": datetime.utcnow(),
    },

    # ── 2. Brownfield ─────────────────────────────────────────────────────────
    # Brown.py ya tiene el envío embebido con Outlook (mail.Send()).
    # Lo marcamos como "automatico": envía solo al terminar, sin confirmación.
    # Depende de Verificar Cierres.
    {
        "nombre": "Brownfield",
        "descripcion": "Seguimiento Migración Brownfield OTC R3 — requiere Verificar Cierres",
        "comando": f'python "{BASE}\\autBrown\\Brown.py"',
        "pc_id": PC_ID,
        "tipo_envio": "automatico",
        "requiere_confirmacion_correo": False,
        "comando_envio": None,
        "dependencias": ["Verificar Cierres"],
        "orden": 2,
        "activo": True,
        "creado_en": datetime.utcnow(),
    },

    # ── 3. Power Aut (Afectación) ─────────────────────────────────────────────
    # poweraut.py extrae los datos y actualiza el Excel, pero NO envía correo.
    # Al confirmar en el dashboard, el agente ejecuta enviar_correo.py.
    {
        "nombre": "Power Aut (Afectación)",
        "descripcion": "Extrae BackLog de Power BI y actualiza Excel de afectación/desempeño",
        "comando": f'python "{BASE}\\aut-afectacion\\poweraut.py"',
        "pc_id": PC_ID,
        "tipo_envio": "correo",
        "requiere_confirmacion_correo": True,
        "comando_envio": f'python "{BASE}\\aut-afectacion\\enviar_correo.py"',
        "dependencias": [],
        "orden": 3,
        "activo": True,
        "creado_en": datetime.utcnow(),
    },

    # ── 4. Backlog Mantenimiento ──────────────────────────────────────────────
    # backlog.py ya tiene el envío embebido (send_email_outlook).
    # Lo marcamos como "automatico".
    {
        "nombre": "Backlog Mantenimiento",
        "descripcion": "Descarga el reporte de backlog de mantenimiento y lo envía por correo",
        "comando": f'python "{BASE}\\mantenimientoaut\\backlog.py"',
        "pc_id": PC_ID,
        "tipo_envio": "automatico",
        "requiere_confirmacion_correo": False,
        "comando_envio": None,
        "dependencias": [],
        "orden": 4,
        "activo": True,
        "creado_en": datetime.utcnow(),
    },

    # ── 5. ClaroBox ──────────────────────────────────────────────────────────
    # copia.py ya tiene el envío embebido (enviar_correo → mail.Send()).
    # Lo marcamos como "automatico".
    {
        "nombre": "ClaroBox",
        "descripcion": "Refresca datos de Claro Box y envía tabla por correo",
        "comando": f'python "{BASE}\\ClaroBoxaut\\copia.py"',
        "pc_id": PC_ID,
        "tipo_envio": "automatico",
        "requiere_confirmacion_correo": False,
        "comando_envio": None,
        "dependencias": [],
        "orden": 5,
        "activo": True,
        "creado_en": datetime.utcnow(),
    },

    # ── 6. Nodos ──────────────────────────────────────────────────────────────
    # copia.py procesa los nodos y guarda el Excel.
    # NO envía correo por sí solo.
    # Al confirmar, el agente lo llama con --enviar-correo.
    {
        "nombre": "Nodos",
        "descripcion": "Consulta nodos en el diagnosticador residencial y notifica por correo",
        "comando": f'python "{BASE}\\NodosAut\\copia.py"',
        "pc_id": PC_ID,
        "tipo_envio": "correo",
        "requiere_confirmacion_correo": True,
        "comando_envio": f'python "{BASE}\\NodosAut\\copia.py" --enviar-correo',
        "dependencias": [],
        "orden": 6,
        "activo": True,
        "creado_en": datetime.utcnow(),
    },

    # ── 7. OTs Final ──────────────────────────────────────────────────────────
    {
        "nombre": "OTs Final",
        "descripcion": "Descarga base fibra y verifica OTs en SharePoint",
        "comando": f'python "{BASE}\\OTsFinal\\ots\\copiaOTs.py"',
        "pc_id": PC_ID,
        "tipo_envio": "ninguno",
        "requiere_confirmacion_correo": False,
        "comando_envio": None,
        "dependencias": [],
        "orden": 7,
        "activo": True,
        "creado_en": datetime.utcnow(),
    },

    # ── 8. Simple Aut ─────────────────────────────────────────────────────────
    {
        "nombre": "Simple Aut",
        "descripcion": "Procesa base fibra, ejecuta macros y sube datos a MySQL",
        "comando": f'python "{BASE}\\SIMPLE\\autSimple\\simpeaut.py"',
        "pc_id": PC_ID,
        "tipo_envio": "ninguno",
        "requiere_confirmacion_correo": False,
        "comando_envio": None,
        "dependencias": [],
        "orden": 8,
        "activo": True,
        "creado_en": datetime.utcnow(),
    },
]

# ─────────────────────────────────────────────────────────────────────────────
# Upsert por nombre
# ─────────────────────────────────────────────────────────────────────────────
for s in scripts:
    resultado = scripts_col.update_one(
        {"nombre": s["nombre"]},
        {"$set": s},
        upsert=True,
    )
    accion = "actualizado" if resultado.matched_count else "insertado"
    print(f"  [{s['orden']}] {accion}: {s['nombre']}  (tipo_envio={s['tipo_envio']})")

print(f"\nListo — {len(scripts)} scripts procesados.")
