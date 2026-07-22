# cargar_scripts.py
# ─────────────────────────────────────────────────────────────────────────────
# Script de carga/actualización del catálogo de scripts en MongoDB.
# Ejecutar manualmente cuando se agregue o modifique un script:
#   python cargar_scripts.py
#
# Campos:
#   tipo_envio:    "correo"      → usuario confirma → agente envía correo
#                  "automatico"  → el propio script envía al terminar (sin confirmación)
#                  "ninguno"     → el script no envía nada
#
#   requiere_confirmacion_correo: True solo si tipo_envio == "correo"
#
#   comando_envio: comando separado para envío. None si está embebido en el script.
#
#   dependencias:  lista de NOMBRES de scripts que deben completarse hoy antes
#                  de que este pueda ejecutarse. [] = sin dependencias.
#
#   orden:         número para ordenar los botones en el panel (menor = primero)
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

# ─────────────────────────────────────────────────────────────────────────────
# Catálogo completo de scripts
# ─────────────────────────────────────────────────────────────────────────────
scripts = [

    # 1. Verificar Cierres
    # Refresca Excel, verifica fechas de cierre y envía correo con confirmación del usuario.
    {
        "nombre": "Verificar Cierres",
        "descripcion": "Verifica cierres por tipo de trabajo y notifica por correo",
        "comando": f'python "{BASE}\\CierresAuto\\verificar_cierres.py"',
        "pc_id": PC_ID,
        "tipo_envio": "correo",
        "requiere_confirmacion_correo": True,
        "comando_envio": None,      # el envío está embebido en el script
        "dependencias": [],
        "orden": 1,
        "activo": True,
        "creado_en": datetime.utcnow(),
    },

    # 2. Brownfield
    # Depende de Verificar Cierres: solo se puede ejecutar si cierres ya finalizó hoy.
    {
        "nombre": "Brownfield",
        "descripcion": "Seguimiento Migración Brownfield OTC R3 — requiere Verificar Cierres",
        "comando": f'python "{BASE}\\autBrown\\Brown.py"',
        "pc_id": PC_ID,
        "tipo_envio": "correo",
        "requiere_confirmacion_correo": True,
        "comando_envio": None,      # el envío está embebido en el script
        "dependencias": ["Verificar Cierres"],
        "orden": 2,
        "activo": True,
        "creado_en": datetime.utcnow(),
    },

    # 3. Power Aut (Afectación)
    # Extrae datos de Power BI y los escribe en Excel. El correo se envía tras confirmación.
    {
        "nombre": "Power Aut (Afectación)",
        "descripcion": "Extrae BackLog de Power BI y actualiza Excel de afectación/desempeño",
        "comando": f'python "{BASE}\\aut-afectacion\\poweraut.py"',
        "pc_id": PC_ID,
        "tipo_envio": "correo",
        "requiere_confirmacion_correo": True,
        "comando_envio": None,      # enviar_correo.py es llamado internamente por poweraut.py
        "dependencias": [],
        "orden": 3,
        "activo": True,
        "creado_en": datetime.utcnow(),
    },

    # 4. Backlog Mantenimiento
    # Toma screenshot + Excel de la web y envía correo tras confirmación.
    {
        "nombre": "Backlog Mantenimiento",
        "descripcion": "Descarga el reporte de backlog de mantenimiento y lo envía por correo",
        "comando": f'python "{BASE}\\mantenimientoaut\\backlog.py"',
        "pc_id": PC_ID,
        "tipo_envio": "correo",
        "requiere_confirmacion_correo": True,
        "comando_envio": None,      # el envío está embebido en backlog.py
        "dependencias": [],
        "orden": 4,
        "activo": True,
        "creado_en": datetime.utcnow(),
    },

    # 5. ClaroBox
    # Refresca Excel, filtra fechas, captura tabla y envía correo con confirmación.
    {
        "nombre": "ClaroBox",
        "descripcion": "Refresca datos de Claro Box y envía tabla por correo",
        "comando": f'python "{BASE}\\ClaroBoxaut\\copia.py"',
        "pc_id": PC_ID,
        "tipo_envio": "correo",
        "requiere_confirmacion_correo": True,
        "comando_envio": None,      # el envío está embebido en el script
        "dependencias": [],
        "orden": 5,
        "activo": True,
        "creado_en": datetime.utcnow(),
    },

    # 6. Nodos
    # Consulta nodos en el diagnosticador y envía Excel por correo con confirmación.
    {
        "nombre": "Nodos",
        "descripcion": "Consulta nodos en el diagnosticador residencial y notifica por correo",
        "comando": f'python "{BASE}\\NodosAut\\copia.py"',
        "pc_id": PC_ID,
        "tipo_envio": "correo",
        "requiere_confirmacion_correo": True,
        "comando_envio": None,      # el envío está embebido en el script
        "dependencias": [],
        "orden": 6,
        "activo": True,
        "creado_en": datetime.utcnow(),
    },

    # 7. OTs Final
    # Descarga base fibra de GIR, busca OTs en SharePoint y procesa resultados.
    # No envía correo: escribe resultados en Excel y en MySQL.
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

    # 8. Simple Aut
    # Descarga base fibra, ejecuta macros y sube datos a MySQL.
    # Depende de OTs Final para que la base esté actualizada.
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
# Actualiza o inserta cada script (upsert por nombre)
# ─────────────────────────────────────────────────────────────────────────────
for s in scripts:
    resultado = scripts_col.update_one(
        {"nombre": s["nombre"]},
        {"$set": s},
        upsert=True,
    )
    accion = "actualizado" if resultado.matched_count else "insertado"
    print(f"  [{s['orden']}] {accion}: {s['nombre']}")

print(f"\nListo — {len(scripts)} scripts procesados.")

