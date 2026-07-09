from pathlib import Path

ROOT = Path("automation-platform")

files = [
    # ===========================
    # Backend
    # ===========================
    "backend/app/__init__.py",
    "backend/app/main.py",

    "backend/app/core/__init__.py",
    "backend/app/core/config.py",
    "backend/app/core/security.py",
    "backend/app/core/database.py",
    "backend/app/core/websocket_manager.py",
    "backend/app/core/exceptions.py",

    "backend/app/api/__init__.py",

    "backend/app/api/v1/__init__.py",

    "backend/app/api/v1/routes/__init__.py",
    "backend/app/api/v1/routes/auth.py",
    "backend/app/api/v1/routes/scripts.py",
    "backend/app/api/v1/routes/executions.py",
    "backend/app/api/v1/routes/logs.py",
    "backend/app/api/v1/routes/metrics.py",

    "backend/app/api/v1/websockets/__init__.py",
    "backend/app/api/v1/websockets/agent_ws.py",
    "backend/app/api/v1/websockets/client_ws.py",

    "backend/app/services/__init__.py",
    "backend/app/services/agent_service.py",
    "backend/app/services/execution_service.py",
    "backend/app/services/email_service.py",
    "backend/app/services/scheduler_service.py",
    "backend/app/services/log_service.py",

    "backend/app/models/__init__.py",
    "backend/app/models/user.py",
    "backend/app/models/script.py",
    "backend/app/models/execution.py",
    "backend/app/models/log.py",

    "backend/app/models/schemas/__init__.py",
    "backend/app/models/schemas/user_schemas.py",
    "backend/app/models/schemas/script_schemas.py",
    "backend/app/models/schemas/execution_schemas.py",

    "backend/app/utils/__init__.py",
    "backend/app/utils/logger.py",
    "backend/app/utils/validators.py",
    "backend/app/utils/helpers.py",

    "backend/tests/__init__.py",
    "backend/tests/test_api/.gitkeep",
    "backend/tests/test_services/.gitkeep",

    "backend/requirements.txt",
    "backend/.env.example",
    "backend/docker-compose.yml",
    "backend/Dockerfile",

    # ===========================
    # Agent
    # ===========================

    "agent/__init__.py",
    "agent/agent.py",

    "agent/core/__init__.py",
    "agent/core/config.py",
    "agent/core/websocket_client.py",
    "agent/core/script_executor.py",
    "agent/core/log_capture.py",
    "agent/core/health_monitor.py",

    "agent/scripts/script1.py",
    "agent/scripts/script2.py",

    "agent/requirements.txt",
    "agent/.env.example",
    "agent/Dockerfile",
    "agent/agent.conf",

    # ===========================
    # Frontend
    # ===========================

    "frontend/src/app/layout.tsx",
    "frontend/src/app/page.tsx",

    "frontend/src/app/dashboard/page.tsx",
    "frontend/src/app/dashboard/components/.gitkeep",

    "frontend/src/app/executions/page.tsx",
    "frontend/src/app/executions/[id]/page.tsx",

    "frontend/src/app/scripts/page.tsx",
    "frontend/src/app/scripts/[id]/page.tsx",

    "frontend/src/app/settings/page.tsx",

    "frontend/src/app/auth/login/page.tsx",
    "frontend/src/app/auth/register/page.tsx",

    "frontend/src/components/common/Layout/.gitkeep",
    "frontend/src/components/common/Sidebar/.gitkeep",
    "frontend/src/components/common/Header/.gitkeep",

    "frontend/src/components/dashboard/ScriptCard.tsx",
    "frontend/src/components/dashboard/MetricsPanel.tsx",
    "frontend/src/components/dashboard/ExecutionLog.tsx",

    "frontend/src/components/executions/ExecutionHistory.tsx",
    "frontend/src/components/executions/ExecutionDetails.tsx",

    "frontend/src/components/ui/.gitkeep",

    "frontend/src/hooks/useWebSocket.ts",
    "frontend/src/hooks/useAuth.ts",
    "frontend/src/hooks/useScripts.ts",

    "frontend/src/services/api.ts",
    "frontend/src/services/websocket.ts",
    "frontend/src/services/auth.ts",

    "frontend/src/store/index.ts",

    "frontend/src/store/slices/scriptsSlice.ts",
    "frontend/src/store/slices/executionsSlice.ts",
    "frontend/src/store/slices/uiSlice.ts",

    "frontend/src/types/index.ts",
    "frontend/src/types/script.ts",

    "frontend/src/utils/formatters.ts",
    "frontend/src/utils/validators.ts",

    "frontend/src/styles/globals.css",

    "frontend/public/.gitkeep",

    "frontend/package.json",
    "frontend/tailwind.config.js",
    "frontend/next.config.js",
    "frontend/Dockerfile",

    # ===========================
    # Root
    # ===========================

    "docker-compose.yml",
    "README.md",
    ".gitignore",
]


def create_structure():
    for file in files:
        path = ROOT / file
        path.parent.mkdir(parents=True, exist_ok=True)

        if not path.exists():
            path.touch()

    print("=" * 60)
    print("✅ Estructura creada correctamente.")
    print(f"📁 Carpeta raíz: {ROOT.resolve()}")
    print("=" * 60)


if __name__ == "__main__":
    create_structure()