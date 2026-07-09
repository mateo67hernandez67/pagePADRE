# cargar_scripts.py
from pymongo import MongoClient
from datetime import datetime

client = MongoClient("mongodb+srv://andresgranadadev07_db_user:Mt2M69,AG%40@cluster0.azlzgay.mongodb.net/?appName=Cluster0")
db = client["automatizaciones"]
scripts_col = db["scripts"]

BASE = r"D:\OneDrive - Comunicacion Celular S.A.- Comcel S.A\Escritorio\AutsAndres"
PC_ID = "pc-andres"

scripts = [
    {
        "nombre": "Verificar Cierres",
        "descripcion": "Verificación de cierres automáticos",
        "comando": f'python "{BASE}\\CierresAuto\\verificar_cierres.py"',
        "pc_id": PC_ID,
        "requiere_confirmacion_correo": False,
        "activo": True,
        "creado_en": datetime.utcnow(),
    },
    {
        "nombre": "Power Aut (Afectación)",
        "descripcion": "Automatización Power BI - Afectación",
        "comando": f'python "{BASE}\\aut-afectacion\\poweraut.py"',
        "pc_id": PC_ID,
        "requiere_confirmacion_correo": True,
        "activo": True,
        "creado_en": datetime.utcnow(),
    },
    {
        "nombre": "Simple Aut",
        "descripcion": "Automatización SIMPLE",
        "comando": f'python "{BASE}\\SIMPLE\\autSimple\\simpeaut.py"',
        "pc_id": PC_ID,
        "requiere_confirmacion_correo": False,
        "activo": True,
        "creado_en": datetime.utcnow(),
    },
    {
        "nombre": "Backlog Mantenimiento",
        "descripcion": "Automatización de backlog de mantenimiento",
        "comando": f'python "{BASE}\\mantenimientoaut\\backlog.py"',
        "pc_id": PC_ID,
        "requiere_confirmacion_correo": True,
        "activo": True,
        "creado_en": datetime.utcnow(),
    },
    {
        "nombre": "ClaroBox",
        "descripcion": "Automatización ClaroBox",
        "comando": f'python "{BASE}\\ClaroBoxaut\\ClaroBox.py"',
        "pc_id": PC_ID,
        "requiere_confirmacion_correo": True,
        "activo": True,
        "creado_en": datetime.utcnow(),
    },
]

resultado = scripts_col.insert_many(scripts)
print(f"Se insertaron {len(resultado.inserted_ids)} scripts")