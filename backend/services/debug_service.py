"""
DebugService — Screen element capture and analysis.
Integrates logic from debug_elements.py, debug_tool.py, config_debug.py, screen_debug.py.
"""
from typing import Optional


class DebugService:
    def capture_elements(self, driver) -> list[dict]:
        """Capture all UI elements from the current screen."""
        if not driver:
            raise RuntimeError("Appium no conectado. Inicializa primero.")

        elements = []
        try:
            # Verify session is still active
            try:
                session_id = driver.session_id
                if not session_id:
                    raise RuntimeError("Sesión de Appium inválida o expirada")
            except Exception as e:
                raise RuntimeError(f"No se pudo verificar la sesión de Appium: {e}")

            # Find all elements in the window
            all_elements = driver.find_elements("xpath", "//*")
            
            if not all_elements:
                logger.warning("[DEBUG] No se encontraron elementos. Verificando estado de la ventana...")
                # Try to get window title to verify connection
                try:
                    title = driver.title
                    logger.info(f"[DEBUG] Título de ventana actual: {title}")
                except Exception as title_e:
                    logger.warning(f"[DEBUG] No se pudo obtener título: {title_e}")
                    raise RuntimeError("La conexión con la ventana del POS puede estar perdida. Intenta reinicializar.")

            for el in all_elements:
                try:
                    tag = el.tag_name or ""
                    name = el.get_attribute("Name") or ""
                    automation_id = el.get_attribute("AutomationId") or ""
                    class_name = el.get_attribute("ClassName") or ""
                    control_type = el.get_attribute("LocalizedControlType") or tag
                    is_enabled = el.is_enabled()
                    is_displayed = el.is_displayed()
                    text = el.text or ""
                    location = el.location
                    size = el.size

                    elements.append({
                        "name": name,
                        "automationId": automation_id,
                        "className": class_name,
                        "controlType": control_type,
                        "text": text,
                        "visible": is_displayed,
                        "enabled": is_enabled,
                        "x": location.get("x", 0),
                        "y": location.get("y", 0),
                        "width": size.get("width", 0),
                        "height": size.get("height", 0),
                    })
                except:
                    continue

        except Exception as e:
            raise RuntimeError(f"Error capturando elementos: {str(e)}")

        return elements

    def analyze_window(self, driver) -> dict:
        """Analyze current window properties."""
        if not driver:
            raise RuntimeError("Appium no conectado")

        try:
            window_size = driver.get_window_size()
            window_rect = driver.get_window_rect()
            title = driver.title or "Desconocido"

            return {
                "title": title,
                "width": window_size.get("width", 0),
                "height": window_size.get("height", 0),
                "x": window_rect.get("x", 0),
                "y": window_rect.get("y", 0),
                "session_id": driver.session_id,
            }
        except Exception as e:
            raise RuntimeError(f"Error analizando ventana: {str(e)}")
