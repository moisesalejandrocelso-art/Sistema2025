# POS Automation Studio — Backend

## Requisitos previos

1. **Python 3.9+** instalado
2. **Appium Server** corriendo en `http://127.0.0.1:4723`
3. **WinAppDriver** instalado (para automatización Windows)

## Instalación

```bash
cd backend
pip install -r requirements.txt
```

## Ejecución

```bash
python main.py
```

El servidor se levanta en `http://localhost:8000`.

## Endpoints

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/api/health` | Estado del servidor |
| POST | `/api/initialize` | Inicialización completa (abrir app, conectar Appium, etc.) |
| POST | `/api/run-flow` | Ejecutar un flujo de automatización |
| POST | `/api/stop-flow` | Detener flujo |
| POST | `/api/pause-flow` | Pausar flujo |
| POST | `/api/resume-flow` | Reanudar flujo |
| POST | `/api/debug/capture-elements` | Capturar elementos de pantalla |
| POST | `/api/debug/analyze-window` | Analizar ventana actual |
| POST | `/api/disconnect` | Cerrar sesión Appium |
| WS | `/ws` | WebSocket para logs en tiempo real |

## Documentación interactiva

Visita `http://localhost:8000/docs` para Swagger UI.
