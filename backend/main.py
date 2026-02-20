"""
POS Automation Studio — FastAPI Backend
Integra Appium/Selenium con el frontend React.
"""
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import asyncio
import json
import logging
import traceback
import threading

from services.appium_service import AppiumService
from services.debug_service import DebugService
from services.recorder_service import RecorderService
from services.select_combo_box import select_combo_box_option

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s: %(message)s")
logger = logging.getLogger("main")

app = FastAPI(title="POS Automation Studio API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global services
appium_service = AppiumService()
debug_service = DebugService()
recorder_service = RecorderService()

# WebSocket connections for real-time logs
ws_connections: list[WebSocket] = []

# Pending step failure resolution
step_failure_event: asyncio.Event = asyncio.Event()
step_failure_response: dict = {}


async def broadcast_log(level: str, message: str):
    """Send log to all connected WebSocket clients."""
    data = json.dumps({"type": "log", "level": level, "message": message})
    for ws in ws_connections[:]:
        try:
            await ws.send_text(data)
        except:
            ws_connections.remove(ws)


async def broadcast_status(status: str, data: dict = None):
    """Send status update to all connected WebSocket clients."""
    payload = {"type": "status", "status": status}
    if data:
        payload["data"] = data
    msg = json.dumps(payload)
    for ws in ws_connections[:]:
        try:
            await ws.send_text(msg)
        except:
            ws_connections.remove(ws)


# ── Models ──────────────────────────────────────────────

class ConfigPayload(BaseModel):
    app_path: str
    appium_url: str
    products_file: str
    products: list[dict]
    iterations: int = 1
    products_per_iteration: int = 10
    combo_box_name: str = ""
    combo_box_option: str = ""
    radio_button_name: str = ""
    payment_amount: float = 0
    enable_debug: bool = False


class StepPayload(BaseModel):
    action_type: str
    description: str
    selector_type: Optional[str] = None
    selector_value: Optional[str] = None
    value: Optional[str] = None
    wait_time: Optional[int] = None
    enabled: bool = True


class FlowPayload(BaseModel):
    name: str
    description: str
    steps: list[StepPayload]
    iterations: int = 1
    start_from_step: int = 0
    config: ConfigPayload


# ── WebSocket ───────────────────────────────────────────

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    ws_connections.append(websocket)
    try:
        while True:
            raw = await websocket.receive_text()
            try:
                msg = json.loads(raw)
                # Handle step failure responses from frontend
                if msg.get("type") == "step_response":
                    global step_failure_response
                    step_failure_response = msg
                    step_failure_event.set()
            except json.JSONDecodeError:
                pass
    except WebSocketDisconnect:
        ws_connections.remove(websocket)


# ── Health ──────────────────────────────────────────────

def _check_appium_session_alive() -> bool:
    """Actually ping Appium to verify the session is alive (not just check local property)."""
    if appium_service.driver is None:
        return False
    try:
        # This makes a real HTTP call to Appium server, unlike session_id which is local
        appium_service.driver.title
        return True
    except Exception:
        logger.warning("[SESSION] Appium session is dead. Cleaning up.")
        appium_service.driver = None
        appium_service.handle = None
        return False


@app.get("/api/health")
async def health():
    appium_connected = await asyncio.to_thread(_check_appium_session_alive)
    return {
        "status": "ok",
        "appium_connected": appium_connected,
        "version": "1.0.0",
    }


# ── Load Products from File ─────────────────────────────

@app.post("/api/load-products-file")
async def load_products_file(data: dict):
    """Read products from a text file on the server and return them."""
    file_path = data.get("file_path", "")
    if not file_path:
        return {"status": "error", "error": "No se proporcionó ruta de archivo"}
    
    import os
    if not os.path.exists(file_path):
        return {"status": "error", "error": f"Archivo no encontrado: {file_path}"}
    
    try:
        products = []
        with open(file_path, "r") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                parts = line.split(",")
                if len(parts) >= 2:
                    products.append({
                        "code": parts[0].strip(),
                        "quantity": int(parts[1].strip())
                    })
                elif len(parts) == 1 and parts[0].strip():
                    products.append({
                        "code": parts[0].strip(),
                        "quantity": 1
                    })
        return {"status": "success", "products": products, "count": len(products)}
    except Exception as e:
        return {"status": "error", "error": str(e)}


# ── Initialization ──────────────────────────────────────

@app.post("/api/initialize")
async def initialize(config: ConfigPayload):
    """Run the full initialization sequence (open app, connect appium, clear order, load products)."""
    results = []

    # Step 1: Verify Appium server is reachable
    await broadcast_log("info", "Ejecutando: Verificar servidor Appium...")
    await broadcast_status("init_step", {"step_id": "check_appium", "status": "running"})
    try:
        import urllib.request
        req = urllib.request.Request(f"{config.appium_url}/status", method="GET")
        with urllib.request.urlopen(req, timeout=5) as resp:
            if resp.status == 200:
                await broadcast_log("success", f"✓ Servidor Appium disponible en {config.appium_url}")
                await broadcast_status("init_step", {"step_id": "check_appium", "status": "success", "message": "OK"})
                results.append({"step": "check_appium", "status": "success"})
            else:
                raise RuntimeError(f"Appium respondió con status {resp.status}")
    except Exception as e:
        msg = f"✗ Servidor Appium no disponible en {config.appium_url}: {str(e)}"
        logger.error(f"[INIT] {msg}")
        await broadcast_log("error", msg)
        await broadcast_log("error", "¿Está corriendo el servidor Appium? Ejecuta: appium")
        await broadcast_status("init_step", {"step_id": "check_appium", "status": "error", "message": str(e)})
        return {"status": "error", "step": "check_appium", "error": str(e), "results": results}

    # Step 2: Open application
    await broadcast_log("info", "Ejecutando: Abrir aplicación POS...")
    await broadcast_status("init_step", {"step_id": "open_app", "status": "running"})
    try:
        await asyncio.to_thread(appium_service.open_application, config.app_path)
        await broadcast_log("success", "✓ Aplicación POS abierta")
        await broadcast_status("init_step", {"step_id": "open_app", "status": "success", "message": "OK"})
        results.append({"step": "open_app", "status": "success"})
    except Exception as e:
        msg = f"✗ Error abriendo aplicación: {str(e)}"
        logger.error(f"[INIT] {msg}\n{traceback.format_exc()}")
        await broadcast_log("error", msg)
        await broadcast_status("init_step", {"step_id": "open_app", "status": "error", "message": str(e)})
        return {"status": "error", "step": "open_app", "error": str(e), "results": results}

    # Step 3: Connect Appium session to POS window
    await broadcast_log("info", "Ejecutando: Conectar sesión Appium al POS...")
    await broadcast_status("init_step", {"step_id": "connect_appium", "status": "running"})
    try:
        await asyncio.to_thread(appium_service.connect, config.appium_url, config.app_path)
        await broadcast_log("success", "✓ Sesión Appium conectada al POS")
        await broadcast_status("init_step", {"step_id": "connect_appium", "status": "success", "message": "OK"})
        results.append({"step": "connect_appium", "status": "success"})
    except Exception as e:
        msg = f"✗ Error conectando sesión Appium: {str(e)}"
        logger.error(f"[INIT] {msg}\n{traceback.format_exc()}")
        await broadcast_log("error", msg)
        await broadcast_status("init_step", {"step_id": "connect_appium", "status": "error", "message": str(e)})
        return {"status": "error", "step": "connect_appium", "error": str(e), "results": results}

    # Step 4: Clear previous order
    await broadcast_log("info", "Ejecutando: Limpiar pedido anterior...")
    await broadcast_status("init_step", {"step_id": "clear_order", "status": "running"})
    try:
        await asyncio.to_thread(appium_service.clear_order)
        await broadcast_log("success", "✓ Pedido anterior limpiado")
        await broadcast_status("init_step", {"step_id": "clear_order", "status": "success", "message": "OK"})
        results.append({"step": "clear_order", "status": "success"})
    except Exception as e:
        msg = f"✗ Error limpiando pedido: {str(e)}"
        await broadcast_log("error", msg)
        await broadcast_status("init_step", {"step_id": "clear_order", "status": "error", "message": str(e)})
        return {"status": "error", "step": "clear_order", "error": str(e), "results": results}

    # Step 4: Load products
    await broadcast_log("info", "Ejecutando: Cargar lista de productos...")
    await broadcast_status("init_step", {"step_id": "load_products", "status": "running"})
    try:
        product_count = await asyncio.to_thread(appium_service.load_products, config.products_file, config.products)
        await broadcast_log("success", f"✓ {product_count} productos cargados")
        await broadcast_status("init_step", {"step_id": "load_products", "status": "success", "message": f"{product_count} productos"})
        results.append({"step": "load_products", "status": "success", "count": product_count})
    except Exception as e:
        msg = f"✗ Error cargando productos: {str(e)}"
        await broadcast_log("error", msg)
        await broadcast_status("init_step", {"step_id": "load_products", "status": "error", "message": str(e)})
        return {"status": "error", "step": "load_products", "error": str(e), "results": results}

    await broadcast_log("success", "✓ Inicialización completa. Listo para ejecutar flujos.")
    return {"status": "success", "results": results}


# ── Flow Execution ──────────────────────────────────────

@app.post("/api/run-flow")
async def run_flow(flow: FlowPayload):
    """Execute a complete automation flow with retry/skip support on failure."""
    alive = await asyncio.to_thread(_check_appium_session_alive)
    if not alive:
        await broadcast_log("warning", "⚠ Sesión de Appium expirada. Intentando reconectar automáticamente...")
        try:
            appium_url = flow.config.appium_url or "http://127.0.0.1:4723"
            import pygetwindow as gw
            windows = gw.getWindowsWithTitle("SimiPOS")
            app_window = None
            for win in windows:
                if win.title:
                    app_window = win
                    break
            if not app_window:
                all_windows = gw.getWindowsWithTitle("")
                for win in all_windows:
                    if "SimiPOS" in win.title:
                        app_window = win
                        break
            if not app_window:
                return {"status": "error", "error": "Sesión expirada y no se encontró la ventana del POS para reconectar."}
            appium_service.handle = hex(app_window._hWnd)
            await asyncio.to_thread(appium_service.connect, appium_url)
            await broadcast_log("success", "✓ Sesión de Appium reconectada automáticamente.")
        except Exception as e:
            logger.error(f"[RUN-FLOW] Auto-reconnect failed: {e}")
            return {"status": "error", "error": f"Sesión expirada y no se pudo reconectar: {str(e)}"}

    await broadcast_log("info", f'▶ Iniciando flujo: "{flow.name}"')
    await broadcast_status("execution", {"status": "running"})

    enabled_steps = [s for s in flow.steps if s.enabled]
    start_from = flow.start_from_step or 0

    if start_from > 0:
        await broadcast_log("info", f"⏩ Saltando los primeros {start_from} pasos, iniciando desde paso {start_from + 1}")

    i = start_from
    while i < len(enabled_steps):
        step = enabled_steps[i]
        # Handle search_product: select random products and search them (matching original main.py)
        if step.action_type == "search_product":
            all_products = flow.config.products or appium_service.products
            if not all_products:
                await broadcast_log("warning", f"⚠ No hay productos cargados. Omitiendo paso {i + 1}.")
                i += 1
                continue

            # Select random products for this iteration (matching original logic)
            import random
            products_per_iter = flow.config.products_per_iteration or len(all_products)
            if products_per_iter >= len(all_products):
                selected_products = all_products[:]
            else:
                selected_products = random.sample(all_products, min(products_per_iter, len(all_products)))

            await broadcast_log("info", f"Paso {i + 1}/{len(enabled_steps)}: {step.description} — {len(selected_products)} productos seleccionados de {len(all_products)} disponibles")
            try:
                for pi, product in enumerate(selected_products):
                    code = product.get("code", "")
                    qty = product.get("quantity", 1)
                    await broadcast_log("info", f"  📦 Producto {pi + 1}/{len(selected_products)}: {code} x{qty}")

                    # Search the product using the search field (matching original search_product.py)
                    def _search_and_add_product(code, qty):
                        from selenium.webdriver.common.by import By
                        from selenium.webdriver.common.keys import Keys
                        from selenium.webdriver.support.ui import WebDriverWait
                        from selenium.webdriver.support import expected_conditions as EC
                        import time as _time

                        driver = appium_service.driver

                        # Close possible modals first
                        try:
                            modal = driver.find_element(By.NAME, "Aceptar")
                            modal.click()
                            _time.sleep(0.5)
                        except:
                            pass

                        # Find and type in search box
                        wait = WebDriverWait(driver, 10)
                        search_box = wait.until(
                            EC.presence_of_element_located((By.NAME, "Buscar producto"))
                        )
                        search_box.click()
                        search_box.clear()
                        search_box.send_keys(code + Keys.ENTER)
                        logger.info(f"[SEARCH] Producto {code} buscado")

                        # Wait for product to load
                        _time.sleep(1)

                        # Click "Agregar" button for each quantity
                        for q in range(qty):
                            try:
                                agregar_btn = WebDriverWait(driver, 5).until(
                                    EC.element_to_be_clickable((By.NAME, "Agregar"))
                                )
                                agregar_btn.click()
                                logger.info(f"[SEARCH] Producto {code} agregado ({q+1}/{qty})")
                                _time.sleep(0.5)

                                # Handle recommendation windows
                                try:
                                    rec_elements = driver.find_elements(
                                        By.XPATH,
                                        "//*[contains(@Name, 'Oportunidad') or contains(@Name, 'Recomendación')]"
                                    )
                                    if rec_elements:
                                        try:
                                            accept_btn = driver.find_element(By.NAME, "Aceptar")
                                            accept_btn.click()
                                            logger.info("[SEARCH] Ventana de recomendación aceptada")
                                            _time.sleep(0.5)
                                        except:
                                            pass
                                except:
                                    pass
                            except Exception as e:
                                logger.warning(f"[SEARCH] No se pudo hacer clic en Agregar para {code}: {e}")

                    await asyncio.to_thread(_search_and_add_product, code, qty)
                    await broadcast_log("success", f"  ✓ {code} x{qty} agregado")

                await broadcast_log("success", f"✓ {len(selected_products)} productos procesados")
                i += 1
                continue
            except Exception as e:
                error_msg = str(e)
                logger.error(f"[RUN-FLOW] search_product falló: {error_msg}\n{traceback.format_exc()}")
                await broadcast_log("error", f"✗ Error buscando productos: {error_msg}")
                step_failure_event.clear()
                await broadcast_status("step_failed", {
                    "step_index": i,
                    "step_description": step.description,
                    "error": error_msg,
                    "selector_type": step.selector_type,
                    "selector_value": step.selector_value,
                    "action_type": step.action_type,
                })
                try:
                    await asyncio.wait_for(step_failure_event.wait(), timeout=300)
                except asyncio.TimeoutError:
                    await broadcast_log("error", "Tiempo de espera agotado.")
                    return {"status": "error", "failed_step": i, "error": "Timeout"}
                response = step_failure_response
                action = response.get("action", "stop")
                if action == "retry":
                    continue
                elif action == "skip":
                    i += 1
                    continue
                else:
                    return {"status": "stopped", "failed_step": i, "error": error_msg}

        await broadcast_status("execution", {"status": "running", "step_index": i})
        await broadcast_log("info", f"Paso {i + 1}/{len(enabled_steps)}: {step.description}")

        try:
            result = await asyncio.to_thread(
                appium_service.execute_step, step.model_dump(), flow.config.model_dump()
            )
            await broadcast_log("success", f"✓ {step.description} — completado")
            i += 1
        except Exception as e:
            error_msg = str(e)
            logger.error(f"[RUN-FLOW] Paso {i+1} falló: {error_msg}\n{traceback.format_exc()}")
            await broadcast_log("error", f"✗ {step.description} — falló: {error_msg}")

            # Notify frontend of failure and wait for user decision
            step_failure_event.clear()
            await broadcast_status("step_failed", {
                "step_index": i,
                "step_description": step.description,
                "error": error_msg,
                "selector_type": step.selector_type,
                "selector_value": step.selector_value,
                "action_type": step.action_type,
            })

            # Wait up to 5 minutes for user response
            try:
                await asyncio.wait_for(step_failure_event.wait(), timeout=300)
            except asyncio.TimeoutError:
                await broadcast_log("error", "Tiempo de espera agotado. Deteniendo flujo.")
                await broadcast_status("execution", {"status": "error", "step_index": i})
                return {"status": "error", "failed_step": i, "error": "Timeout esperando respuesta"}

            response = step_failure_response
            action = response.get("action", "stop")

            if action == "retry":
                # Update selector if provided
                new_selector_type = response.get("selector_type")
                new_selector_value = response.get("selector_value")
                if new_selector_type and new_selector_value:
                    # Create updated step
                    step_data = step.model_dump()
                    step_data["selector_type"] = new_selector_type
                    step_data["selector_value"] = new_selector_value
                    enabled_steps[i] = StepPayload(**step_data)
                await broadcast_log("info", f"🔄 Reintentando paso {i + 1}...")
                continue  # retry same step
            elif action == "skip":
                await broadcast_log("warning", f"⏭ Paso {i + 1} omitido por el usuario.")
                i += 1
                continue
            else:  # stop
                await broadcast_status("execution", {"status": "stopped", "step_index": i})
                return {"status": "stopped", "failed_step": i, "error": error_msg}

    await broadcast_status("execution", {"status": "completed"})
    await broadcast_log("success", f'✓ Flujo "{flow.name}" completado exitosamente.')
    return {"status": "completed", "steps_executed": len(enabled_steps)}


@app.post("/api/stop-flow")
async def stop_flow():
    """Stop the currently running flow."""
    appium_service.stop_requested = True
    await broadcast_log("warning", "⏹ Flujo detenido por el usuario.")
    await broadcast_status("execution", {"status": "stopped"})
    return {"status": "stopped"}


@app.post("/api/pause-flow")
async def pause_flow():
    """Pause the currently running flow."""
    appium_service.paused = True
    await broadcast_log("warning", "⏸ Flujo pausado.")
    await broadcast_status("execution", {"status": "paused"})
    return {"status": "paused"}


@app.post("/api/resume-flow")
async def resume_flow():
    """Resume a paused flow."""
    appium_service.paused = False
    await broadcast_log("info", "▶ Flujo reanudado.")
    await broadcast_status("execution", {"status": "running"})
    return {"status": "running"}


# ── Debug ───────────────────────────────────────────────

@app.post("/api/debug/capture-elements")
async def capture_elements():
    """Capture all UI elements from the current screen."""
    await broadcast_log("info", "[DEBUG] Capturando elementos de pantalla...")
    try:
        elements = await asyncio.to_thread(debug_service.capture_elements, appium_service.driver)
        await broadcast_log("success", f"[DEBUG] {len(elements)} elementos capturados")
        return {"status": "success", "elements": elements}
    except Exception as e:
        await broadcast_log("error", f"[DEBUG] Error: {str(e)}")
        return {"status": "error", "error": str(e)}


@app.post("/api/debug/pick-elements")
async def pick_elements():
    """Capture visible UI elements for the visual element picker."""
    alive = await asyncio.to_thread(_check_appium_session_alive)
    if not alive:
        return {"status": "error", "error": "session_expired", "message": "La sesión de Appium expiró. Usa 'Reconectar' o reinicia el sistema."}
    try:
        elements = await asyncio.to_thread(appium_service.capture_elements_for_picker)
        return {"status": "success", "elements": elements, "count": len(elements)}
    except Exception as e:
        error_str = str(e)
        if "terminated or not started" in error_str:
            appium_service.driver = None
            appium_service.handle = None
            return {"status": "error", "error": "session_expired", "message": "La sesión de Appium expiró."}
        return {"status": "error", "error": error_str}


@app.post("/api/debug/analyze-window")
async def analyze_window():
    """Analyze the current window properties."""
    try:
        info = debug_service.analyze_window(appium_service.driver)
        return {"status": "success", "window_info": info}
    except Exception as e:
        await broadcast_log("error", f"[DEBUG] Error analyzing window: {str(e)}")
        return {"status": "error", "error": str(e)}


# Radio button endpoints removed - using simple proven method directly
    except Exception as e:
        return {"status": "error", "error": str(e)}


# ── Recording ───────────────────────────────────────────

@app.post("/api/record/start")
async def start_recording():
    """Start recording user interactions with the POS."""
    if not appium_service.driver:
        await broadcast_log("error", "[RECORD] Appium no conectado. Inicializa primero.")
        return {"status": "error", "error": "Appium no conectado"}

    def on_step_captured(step_dict):
        """Called when a new step is captured during recording."""
        import asyncio
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.ensure_future(broadcast_status("recorded_step", step_dict))
                asyncio.ensure_future(broadcast_log(
                    "info",
                    f"[REC] ● {step_dict.get('action_type', '?')}: {step_dict.get('description', '?')}"
                ))
        except Exception as e:
            logger.warning(f"[RECORD] Error broadcasting step: {e}")

    try:
        recorder_service.start(appium_service.driver, on_step_captured, window_handle=appium_service.handle)
        await broadcast_log("success", "[RECORD] 🔴 Grabación iniciada. Interactúa con la aplicación POS...")
        return {"status": "recording"}
    except Exception as e:
        logger.error(f"[RECORD] Error starting: {e}", exc_info=True)
        await broadcast_log("error", f"[RECORD] Error: {str(e)}")
        return {"status": "error", "error": str(e)}


@app.post("/api/record/stop")
async def stop_recording():
    """Stop recording and return captured steps."""
    try:
        steps = recorder_service.stop()
        await broadcast_log("success", f"[RECORD] ⏹ Grabación detenida. {len(steps)} pasos capturados.")
        return {"status": "stopped", "steps": steps, "count": len(steps)}
    except Exception as e:
        logger.error(f"[RECORD] Error stopping: {e}", exc_info=True)
        return {"status": "error", "error": str(e)}


@app.get("/api/record/status")
async def record_status():
    """Get current recording status."""
    return {
        "recording": recorder_service.recording,
        "steps_count": len(recorder_service.steps),
        "steps": recorder_service.get_steps(),
    }


# ── Reconnect ───────────────────────────────────────────

@app.post("/api/reconnect")
async def reconnect(data: dict = None):
    """Re-establish Appium session by finding the POS window and connecting."""
    appium_url = "http://127.0.0.1:4723"
    if data:
        appium_url = data.get("appium_url", appium_url)

    try:
        # Try to find the POS window
        import pygetwindow as gw
        windows = gw.getWindowsWithTitle("SimiPOS")
        app_window = None
        for win in windows:
            if win.title:
                app_window = win
                break

        if not app_window:
            all_windows = gw.getWindowsWithTitle("")
            for win in all_windows:
                if "SimiPOS" in win.title:
                    app_window = win
                    break

        if not app_window:
            return {"status": "error", "error": "No se encontró la ventana del POS. ¿Está abierto SimiPOS?"}

        appium_service.handle = hex(app_window._hWnd)
        logger.info(f"[RECONNECT] Handle encontrado: {appium_service.handle}")

        # Connect Appium
        await asyncio.to_thread(appium_service.connect, appium_url)
        await broadcast_log("success", "✓ Sesión de Appium reconectada exitosamente.")
        return {"status": "success", "handle": appium_service.handle}
    except Exception as e:
        logger.error(f"[RECONNECT] Error: {e}", exc_info=True)
        return {"status": "error", "error": str(e)}


# ── Disconnect ──────────────────────────────────────────

@app.post("/api/disconnect")
async def disconnect():
    """Disconnect Appium session."""
    try:
        if recorder_service.recording:
            recorder_service.stop()
        appium_service.disconnect()
        await broadcast_log("info", "Sesión de Appium cerrada.")
        return {"status": "disconnected"}
    except Exception as e:
        return {"status": "error", "error": str(e)}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
