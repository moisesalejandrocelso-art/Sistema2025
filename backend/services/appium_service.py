"""
AppiumService — Integrates with the existing Python automation scripts.
Bridges the FastAPI endpoints with Appium/Selenium WebDriver.
Uses pygetwindow for window detection (matching user's working scripts).
"""
import subprocess
import time
import os
import logging
from typing import Optional

import pygetwindow as gw
from appium import webdriver
from appium.options.windows import WindowsOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from services.click_button_service import ClickButtonService

logger = logging.getLogger("appium_service")


class AppiumService:
    def __init__(self):
        self.driver = None
        self.app_process = None
        self.products: list[dict] = []
        self.stop_requested = False
        self.paused = False
        self.handle = None

    # ── Initialization Steps ────────────────────────────

    def open_application(self, app_path: str):
        """Open the POS application using pygetwindow (matching working script)."""
        logger.info(f"[OPEN_APP] Abriendo aplicación: {app_path}")
        if not os.path.exists(app_path):
            raise FileNotFoundError(f"No se encontró la aplicación en: {app_path}")

        previous_windows = gw.getWindowsWithTitle("SimiPOS")
        logger.info(f"[OPEN_APP] Ventanas antes de abrir: {len(previous_windows)}")

        self.app_process = subprocess.Popen(app_path)
        time.sleep(3)

        app_window = None
        logger.info("[OPEN_APP] Buscando ventanas con título 'SimiPOS'...")
        windows = gw.getWindowsWithTitle("SimiPOS")
        logger.info(f"[OPEN_APP] Se encontraron {len(windows)} ventanas")

        for i, win in enumerate(windows):
            logger.info(f"[OPEN_APP] Ventana {i+1}: '{win.title}' (handle: {hex(win._hWnd)})")
            if win.title:
                app_window = win
                break

        if not app_window:
            # Flexible search
            logger.info("[OPEN_APP] Búsqueda flexible por contenido del título...")
            all_windows = gw.getWindowsWithTitle("")
            for win in all_windows:
                if "SimiPOS" in win.title:
                    app_window = win
                    logger.info(f"[OPEN_APP] Encontrada ventana flexible: '{win.title}'")
                    break

        if not app_window:
            raise RuntimeError("No se encontró la ventana de la aplicación 'SimiPOS'.")

        self.handle = hex(app_window._hWnd)
        logger.info(f"[OPEN_APP] Aplicación abierta. Handle: {self.handle}")

        logger.info("[OPEN_APP] Esperando a que la interfaz gráfica se cargue...")
        time.sleep(3)
        logger.info("[OPEN_APP] Aplicación abierta y UI cargada.")
        return self.handle

    def connect(self, appium_url: str, app_path: str = None):
        """Connect to Appium using the window handle (matching working script)."""
        handle = self.handle
        if not handle:
            raise RuntimeError("No hay handle de ventana. Ejecuta 'Abrir aplicación' primero.")

        logger.info(f"[CONNECT] Conectando con Appium usando handle: {handle}...")

        try:
            options = WindowsOptions()
            options.set_capability("appTopLevelWindow", handle)
            options.set_capability("newCommandTimeout", 300)
            # Minimal capabilities to avoid pointer issues while maintaining element detection
            options.set_capability("automationName", "Windows")
            options.set_capability("platformName", "Windows")

            self.driver = webdriver.Remote(
                command_executor=appium_url,
                options=options
            )
            logger.info(f"[CONNECT] Conexión establecida. Sesión: {self.driver.session_id}")
            time.sleep(1)
            logger.info("[CONNECT] Esperando a que inicie Punto de venta.")

        except Exception as e:
            logger.error(f"[CONNECT] ERROR: {e}", exc_info=True)
            raise RuntimeError(f"No se pudo conectar con Appium: {e}")

    def clear_order(self):
        """Clear previous order (matching working clear_order.py)."""
        if not self.driver:
            raise RuntimeError("Appium no conectado")

        logger.info("[CLEAR] Intentando borrar el pedido...")
        max_intentos = 1
        intento = 0

        while intento < max_intentos:
            try:
                wait = WebDriverWait(self.driver, 2)
                boton_borrar = wait.until(
                    EC.presence_of_element_located((By.NAME, "Borrar pedido"))
                )
                boton_borrar.click()
                logger.info("[CLEAR] Pedido borrado correctamente.")
                return True
            except Exception as e:
                intento += 1
                if intento < max_intentos:
                    logger.info(f"[CLEAR] Intento {intento} fallido. Reintentando en 4 segundos...")
                    time.sleep(4)

        logger.warning("[CLEAR] No se pudo borrar el pedido. Continuando ejecución...")
        return False

    def load_products(self, products_file: str, products: list[dict]) -> int:
        """Load products from file or provided list."""
        if products:
            self.products = products
        elif products_file and os.path.exists(products_file):
            self.products = []
            with open(products_file, "r") as f:
                for line in f:
                    parts = line.strip().split(",")
                    if len(parts) >= 2:
                        self.products.append({
                            "code": parts[0].strip(),
                            "quantity": int(parts[1].strip())
                        })
        else:
            raise FileNotFoundError(f"Archivo de productos no encontrado: {products_file}")

        return len(self.products)

    # ── Step Execution ──────────────────────────────────

    def execute_step(self, step: dict, config: dict):
        """Execute a single automation step with retry and delay support."""
        logger.info(f"[STEP] Ejecutando: action={step.get('action_type')}, selector=[{step.get('selector_type')}] {step.get('selector_value')}, value={step.get('value')}")

        if not self.driver:
            raise RuntimeError("Appium no conectado. Ejecuta la inicialización primero.")

        # Verify session
        try:
            _ = self.driver.session_id
        except Exception as e:
            raise RuntimeError(f"Sesión de Appium inválida: {e}")

        if self.stop_requested:
            self.stop_requested = False
            raise RuntimeError("Ejecución detenida por el usuario")

        while self.paused:
            time.sleep(0.5)

        # Apply step delay (wait between steps)
        step_delay = config.get("step_delay", 0)
        if step_delay > 0:
            logger.info(f"[STEP] Esperando {step_delay}ms antes de ejecutar...")
            time.sleep(step_delay / 1000)

        action = step.get("action_type")
        selector_type = step.get("selector_type")
        selector_value = step.get("selector_value")
        value = step.get("value", "")
        wait_time = step.get("wait_time", 2000)

        # Retry logic for finding elements
        retry_attempts = config.get("retry_attempts", 3)
        retry_delay = config.get("retry_delay", 2000)

        element = None
        if selector_type and selector_value:
            element = self._find_element_with_retry(selector_type, selector_value, retry_attempts, retry_delay)

        if action == "click":
            if element:
                # Special handling for unfocusable buttons and AutomationId elements
                if selector_type == "xpath" and "AutomationId" in selector_value:
                    logger.info(f"[CLICK] Using ClickButtonService for unfocusable button...")
                    try:
                        click_service = ClickButtonService(self.driver)
                        click_service.click_unfocusable_button(selector_type, selector_value, f"Button ({selector_value})")
                    except Exception as e:
                        logger.warning(f"[CLICK] ClickButtonService failed: {e}, falling back to regular click...")
                        element.click()
                elif selector_value == "Cobrar" or "Cobro" in selector_value:
                    logger.info(f"[CLICK] Using ClickButtonService for Cobrar button...")
                    try:
                        click_service = ClickButtonService(self.driver)
                        click_service.click_unfocusable_button(selector_type, selector_value, "Cobrar")
                    except Exception as e:
                        logger.warning(f"[CLICK] ClickButtonService failed: {e}, falling back to regular click...")
                        element.click()
                else:
                    element.click()
            else:
                raise RuntimeError("No se encontró el elemento para hacer clic")

        elif action == "double_click":
            if element:
                # For WPF apps, use JavaScript instead of ActionChains
                try:
                    self.driver.execute_script("arguments[0].click();", element)
                    time.sleep(0.1)
                    self.driver.execute_script("arguments[0].click();", element)
                except Exception as e:
                    logger.warning(f"[DOUBLE_CLICK] JavaScript approach failed: {e}, trying direct click twice...")
                    element.click()
                    time.sleep(0.1)
                    element.click()

        elif action == "type":
            # Resolve {{payment_amount}} placeholder
            actual_value = value
            if value == "{{payment_amount}}":
                actual_value = str(config.get("payment_amount", ""))
            if element:
                element.click()
                element.clear()
                element.send_keys(actual_value)
            else:
                raise RuntimeError("No se encontró el campo para escribir")

        elif action == "send_keys":
            key_map = {
                "Enter": Keys.ENTER,
                "Tab": Keys.TAB,
                "Escape": Keys.ESCAPE,
                "F5": Keys.F5,
                "Backspace": Keys.BACKSPACE,
                "Delete": Keys.DELETE,
            }
            key = key_map.get(value, value)
            if element:
                element.send_keys(key)
            else:
                # For WPF applications, try alternative methods without ActionChains
                logger.warning(f"[SEND_KEYS] No element found, trying driver level methods...")
                # Try sending key directly to the driver's active element if available
                try:
                    self.driver.switch_to.active_element.send_keys(key)
                except Exception as e2:
                        # If that fails, try using Windows-specific keys method which is available for WPF
                        logger.warning(f"[SEND_KEYS] Direct send_keys failed: {e2}. Trying Windows keys method...")
                        try:
                            # Use Windows-specific execute method with proper format
                            if key == Keys.ENTER:
                                self.driver.execute_script("windows: keys", ["{ENTER}"])
                                logger.info(f"[SEND_KEYS] Windows keys method sent: Enter")
                            elif key == Keys.TAB:
                                self.driver.execute_script("windows: keys", ["{TAB}"])
                                logger.info(f"[SEND_KEYS] Windows keys method sent: Tab")
                            elif key == Keys.ESCAPE:
                                self.driver.execute_script("windows: keys", ["{ESC}"])
                                logger.info(f"[SEND_KEYS] Windows keys method sent: Escape")
                            elif value == "F5":
                                self.driver.execute_script("windows: keys", ["{F5}"])
                                logger.info(f"[SEND_KEYS] Windows keys method sent: F5")
                            elif value == "Backspace":
                                self.driver.execute_script("windows: keys", ["{BACKSPACE}"])
                                logger.info(f"[SEND_KEYS] Windows keys method sent: Backspace")
                            elif value == "Delete":
                                self.driver.execute_script("windows: keys", ["{DELETE}"])
                                logger.info(f"[SEND_KEYS] Windows keys method sent: Delete")
                            else:
                                # For other values, try to send as string
                                self.driver.execute_script("windows: keys", [str(value)])
                                logger.info(f"[SEND_KEYS] Windows keys method sent: {value}")
                        except Exception as e3:
                            logger.warning(f"[SEND_KEYS] Windows keys method failed: {e3}")
                            # For certain keys like Enter that are commonly used, don't fail hard
                            if value in ["Enter", "Tab", "Escape"]:
                                logger.info(f"[SEND_KEYS] Key '{value}' is commonly used, continuing without sending...")
                                return {"status": "success", "message": f"Key '{value}' not sent but continuing"}
                            else:
                                raise RuntimeError(f"No se pudo enviar la tecla '{value}' sin un elemento válido")
                        # If all else fails, log warning and continue (the step might still work)
                        logger.warning(f"[SEND_KEYS] All methods failed to send key {key}. Continuing...")

        elif action == "wait":
            time.sleep(wait_time / 1000)

        elif action == "clear":
            if element:
                element.clear()

        elif action == "select_combo":
            combo_name = selector_value or config.get("combo_box_name", "")
            combo_option = config.get("combo_box_option", "")
            if not combo_name:
                combo_name = config.get("combo_box_name", "")
            try:
                # Import here to avoid circular imports
                from services.select_combo_box import select_combo_box_option
                select_combo_box_option(self.driver, combo_name, combo_option)
                logger.info(f"[COMBO] Opción '{combo_option}' seleccionada en '{combo_name}'.")
            except Exception as e:
                raise RuntimeError(f"Error seleccionando ComboBox: {str(e)}")

        elif action == "select_radio":
            radio_name = selector_value or config.get("radio_button_name", "")
            if not radio_name:
                radio_name = config.get("radio_button_name", "")
            self._select_radio(radio_name)

        elif action == "assert":
            if element is None:
                raise RuntimeError(f"Elemento no encontrado: {selector_value}")

        elif action == "scroll":
            if element:
                # For WPF apps, use JavaScript instead of ActionChains
                try:
                    self.driver.execute_script("arguments[0].scrollIntoView(true);", element)
                except Exception as e:
                    logger.warning(f"[SCROLL] JavaScript scroll failed: {e}, trying element scroll...")
                    try:
                        # Try native element scroll as fallback
                        self.driver.execute_script("arguments[0].scrollTop = 0;", element)
                    except Exception as e2:
                        logger.warning(f"[SCROLL] Element scroll failed: {e2}")
                        # Scroll is not critical, continue without it
                        pass

        elif action == "search_product":
            # This action is handled at flow level (iterates products), not here
            # If called directly, just type the value
            if element and value and value != "{{products}}":
                element.click()
                element.clear()
                element.send_keys(value)

        return {"status": "success"}

    def _find_element(self, selector_type: str, selector_value: str):
        """Find element by selector type (single attempt)."""
        by_map = {
            "name": By.NAME,
            "xpath": By.XPATH,
            "id": By.ID,
            "accessibility_id": "accessibility id",
            "css": By.CSS_SELECTOR,
            "class_name": By.CLASS_NAME,
        }
        by = by_map.get(selector_type, By.NAME)

        try:
            # Try the primary selector first
            element = WebDriverWait(self.driver, 5).until(
                EC.presence_of_element_located((by, selector_value))
            )
            if element:
                return element
        except Exception:
            pass

        # Special fallback strategies for xpath with AutomationId
        if selector_type == "xpath" and "AutomationId" in selector_value:
            logger.info(f"[FIND] XPath with AutomationId failed, trying alternative strategies...")
            try:
                # Try using accessibility_id instead
                automation_id = selector_value.split("'")[1] if "'" in selector_value else selector_value.split('"')[1]
                element = WebDriverWait(self.driver, 3).until(
                    EC.presence_of_element_located((By.ACCESSIBILITY_ID, automation_id))
                )
                if element:
                    logger.info(f"[FIND] Found element using accessibility_id: {automation_id}")
                    return element
            except Exception:
                pass

            try:
                # Try finding by exact AutomationId attribute
                xpath_alt = f"//*[@AutomationId='{automation_id}']"
                element = WebDriverWait(self.driver, 3).until(
                    EC.presence_of_element_located((By.XPATH, xpath_alt))
                )
                if element:
                    logger.info(f"[FIND] Found element using alternative xpath: {xpath_alt}")
                    return element
            except Exception:
                pass

        return None

    def _find_element_with_retry(self, selector_type: str, selector_value: str, max_retries: int = 3, retry_delay: int = 2000):
        """Find element with retry logic for slow-loading screens."""
        for attempt in range(1, max_retries + 1):
            element = self._find_element(selector_type, selector_value)
            if element is not None:
                if attempt > 1:
                    logger.info(f"[RETRY] Elemento encontrado en intento {attempt}: [{selector_type}] {selector_value}")
                return element
            if attempt < max_retries:
                logger.warning(f"[RETRY] Intento {attempt}/{max_retries} fallido para [{selector_type}] {selector_value}. Esperando {retry_delay}ms...")
                time.sleep(retry_delay / 1000)
        raise RuntimeError(f"Elemento no encontrado después de {max_retries} intentos: [{selector_type}] {selector_value}")

    def _select_combo(self, combo_name: str, option: str):
        """Select a combo box option (matching working select_combo_box.py)."""
        try:
            combo = self.driver.find_element(By.NAME, combo_name)
            combo.click()
            time.sleep(1)
            opt = self.driver.find_element(By.NAME, option)
            opt.click()
            logger.info(f"[COMBO] Opción '{option}' seleccionada en '{combo_name}'.")
        except Exception as e:
            raise RuntimeError(f"Error seleccionando ComboBox: {str(e)}")

    def _select_radio(self, radio_name: str):
        """Select a radio button using exactly the same method as the working project."""
        logger.info(f"[RADIO] Iniciando selección de RadioButton '{radio_name}'...")
        
        while True:
            try:
                # Use EXACTLY the same method as the working project
                radio_button = self.driver.find_element("name", radio_name)
                radio_button.click()
                logger.info(f"[RADIO] ✓ RadioButton '{radio_name}' seleccionado exitosamente")
                return
            except Exception:
                logger.info(f"[RADIO] RadioButton '{radio_name}' no disponible aún. Reintentando en 2 segundos...")
                time.sleep(2)
                
                # Check if we should stop
                if self.stop_requested:
                    raise RuntimeError("Ejecución detenida por el usuario")
    
    def _select_radio_fallback(self, radio_name: str):
        """Fallback method using the original implementation."""
        logger.info(f"[RADIO] Usando método fallback para '{radio_name}'...")

        max_wait = 60
        elapsed = 0
        interval = 2

        while elapsed < max_wait:
            if self.stop_requested:
                raise RuntimeError("Ejecución detenida por el usuario")

            # Try to find the element with multiple locators
            radio = None
            locators = [
                (By.NAME, radio_name),
                (By.XPATH, f"//RadioButton[@Name='{radio_name}']"),
                (By.XPATH, f"//*[@Name='{radio_name}' and @LocalizedControlType='radio button']"),
                (By.XPATH, f"//*[contains(@Name,'{radio_name}')]"),
            ]

            for by, value in locators:
                try:
                    radio = self.driver.find_element(by, value)
                    tag = radio.tag_name or "unknown"
                    class_name = ""
                    try:
                        class_name = radio.get_attribute("ClassName") or ""
                    except:
                        pass
                    logger.info(f"[RADIO] Encontrado con [{by}] {value} — tag={tag}, class={class_name}")
                    break
                except Exception:
                    continue

            if not radio:
                logger.info(f"[RADIO] '{radio_name}' no encontrado aún. Reintentando en {interval}s...")
                time.sleep(interval)
                elapsed += interval
                continue

            # === STRATEGY 1: Standard click (most reliable for WPF) ===
            try:
                radio.click()
                logger.info(f"[RADIO] Strategy 1: click() aplicado")
                # Add a small delay to let the UI update
                time.sleep(0.5)
                
                # Enhanced verification for WPF applications
                try:
                    # Method 1: Check IsChecked attribute (primary for WPF)
                    is_checked = radio.get_attribute("IsChecked")
                    logger.info(f"[RADIO] Estado actual después de click: IsChecked={is_checked}")
                    
                    # Method 2: Try alternative WPF attributes if IsChecked is not available
                    if is_checked is None:
                        # Check for other common WPF selection indicators
                        is_selected = radio.get_attribute("IsSelected")
                        is_pressed = radio.get_attribute("IsPressed")
                        value = radio.get_attribute("Value")
                        
                        logger.info(f"[RADIO] Verificando atributos alternativos: IsSelected={is_selected}, IsPressed={is_pressed}, Value={value}")
                        
                        # Consider selected if any of these indicators are positive
                        if (is_selected and is_selected.lower() == "true") or \
                           (is_pressed and is_pressed.lower() == "true"):
                            is_checked = "true"
                            logger.info(f"[RADIO] RadioButton seleccionado verificado por atributo alternativo")
                    
                    if is_checked and is_checked.lower() == "true":
                        logger.info(f"[RADIO] ✓ RadioButton '{radio_name}' seleccionado correctamente (IsChecked=true)")
                        return
                    elif is_checked is None:
                        # If no IsChecked attribute, try clicking again to ensure selection
                        logger.info(f"[RADIO] ! No se encontró IsChecked, intentando asegurar selección...")
                        radio.click()
                        time.sleep(0.5)
                        # Try to verify again after second click
                        is_checked = radio.get_attribute("IsChecked")
                        if is_checked and is_checked.lower() == "true":
                            logger.info(f"[RADIO] ✓ RadioButton '{radio_name}' seleccionado correctamente después de segundo intento")
                            return
                    else:
                        # Even if IsChecked is false, we should try to ensure it's selected
                        # For WPF apps, sometimes we need to use different approach like send_keys or javascript
                        logger.info(f"[RADIO] ! RadioButton '{radio_name}' podría no estar seleccionado (IsChecked={is_checked}), usando método alternativo...")
                        
                        # Try alternative approaches for WPF applications - but first check if we're in a problematic scenario
                        # If we've already tried all these strategies and it's failing with "pen and touch pointer input source types are supported", 
                        # then the problem might be that we should try to click on the parent container or use a different approach
                        
                        # Try to get more information about this element first
                        try:
                            logger.info(f"[RADIO] Información adicional del elemento: tag={radio.tag_name}, class={radio.get_attribute('ClassName')}")
                        except Exception as e_info:
                            logger.warning(f"[RADIO] No se pudo obtener información adicional del elemento: {e_info}")
                        
                        # Try alternative approaches for WPF applications
                        try:
                            # Method 1: Try sending SPACE key which often works for WPF radio buttons
                            logger.info(f"[RADIO] Intentando enviar SPACE key para forzar selección...")
                            try:
                                radio.send_keys(Keys.SPACE)
                                time.sleep(0.5)
                                
                                # Verify again after space key
                                is_checked = radio.get_attribute("IsChecked")
                                if is_checked and is_checked.lower() == "true":
                                    logger.info(f"[RADIO] ✓ RadioButton '{radio_name}' seleccionado correctamente después de SPACE key")
                                    return
                            except Exception as e2:
                                logger.warning(f"[RADIO] SPACE key falló: {e2}")
                            
                            # Method 2: Try JavaScript execution (most reliable for WPF)
                            try:
                                logger.info(f"[RADIO] Intentando usar JavaScript para forzar selección...")
                                self.driver.execute_script("arguments[0].click();", radio)
                                time.sleep(0.5)
                                
                                # Verify again after JavaScript click
                                is_checked = radio.get_attribute("IsChecked")
                                if is_checked and is_checked.lower() == "true":
                                    logger.info(f"[RADIO] ✓ RadioButton '{radio_name}' seleccionado correctamente después de JavaScript")
                                    return
                            except Exception as e3:
                                logger.warning(f"[RADIO] JavaScript falló: {e3}")
                                
                            # Method 2b: Try direct element click with fallback to JS
                            try:
                                logger.info(f"[RADIO] Intentando clic directo en elemento...")
                                radio.click()
                                time.sleep(0.5)
                                
                                # Verify again after direct click
                                is_checked = radio.get_attribute("IsChecked")
                                if is_checked and is_checked.lower() == "true":
                                    logger.info(f"[RADIO] ✓ RadioButton '{radio_name}' seleccionado correctamente después de clic directo")
                                    return
                            except Exception as e3b:
                                logger.warning(f"[RADIO] Clic directo falló: {e3b}")
                                
                            # Method 3: Try double click if single click failed
                            try:
                                logger.info(f"[RADIO] Intentando doble clic como último recurso...")
                                # Use JavaScript double click instead of ActionChains for WPF
                                self.driver.execute_script("arguments[0].click();", radio)
                                time.sleep(0.1)
                                self.driver.execute_script("arguments[0].click();", radio)
                                time.sleep(0.5)
                                
                                # Verify again after double click
                                is_checked = radio.get_attribute("IsChecked")
                                if is_checked and is_checked.lower() == "true":
                                    logger.info(f"[RADIO] ✓ RadioButton '{radio_name}' seleccionado correctamente después de doble clic")
                                    return
                            except Exception as e4:
                                logger.warning(f"[RADIO] Doble clic falló: {e4}")
                                
                        except Exception as e5:
                            logger.warning(f"[RADIO] Error en métodos alternativos: {e5}")
                            
                except Exception as e:
                    # If we can't check the state, make sure click was successful by trying a second time
                    logger.warning(f"[RADIO] No se pudo verificar estado: {e}")
                    radio.click()  # Try clicking again to ensure it's selected
                    time.sleep(0.5)
            except Exception as e:
                logger.warning(f"[RADIO] Strategy 1 falló: {e}")
                
            # If we get here and all strategies have failed, we should not assume success
            # Instead, we should throw an exception to indicate the selection failed
            logger.error(f"[RADIO] Todos los intentos de selección fallaron para '{radio_name}'. El radio button no pudo ser seleccionado.")
            raise RuntimeError(f"No se pudo seleccionar el RadioButton '{radio_name}' después de múltiples intentos.")
            
            # REMOVED: The problematic line that assumed success without verification
            # return

            time.sleep(0.3)

            # === STRATEGY 2: Click via coordinates (center of element) ===
            try:
                loc = radio.location
                size = radio.size
                cx = loc['x'] + size['width'] // 2
                cy = loc['y'] + size['height'] // 2
                # Use JavaScript click by coordinates instead of ActionChains for WPF
                try:
                    self.driver.execute_script(f"document.elementFromPoint({cx}, {cy}).click();")
                except Exception:
                    # If coordinate click fails, fallback to direct element click
                    radio.click()
                logger.info(f"[RADIO] Strategy 2: click por coordenadas ({cx},{cy}) aplicado")
                time.sleep(0.5)
            except Exception as e:
                logger.warning(f"[RADIO] Strategy 2 falló: {e}")

            time.sleep(0.3)

            # === STRATEGY 3: Send SPACE key to element (more reliable than ActionChains) ===
            try:
                radio.send_keys(Keys.SPACE)
                logger.info(f"[RADIO] Strategy 3: SPACE key enviado")
                time.sleep(0.5)
            except Exception as e:
                logger.warning(f"[RADIO] Strategy 3 falló: {e}")

            time.sleep(0.3)

            # === STRATEGY 4: Send ENTER key to element (alternative) ===
            try:
                radio.send_keys(Keys.ENTER)
                logger.info(f"[RADIO] Strategy 4: ENTER key enviado")
                time.sleep(0.5)
            except Exception as e:
                logger.warning(f"[RADIO] Strategy 4 falló: {e}")

            time.sleep(0.3)

            # === STRATEGY 5: Double click (last resort) ===
            try:
                # Use JavaScript double click instead of ActionChains for WPF
                self.driver.execute_script("arguments[0].click();", radio)
                time.sleep(0.1)
                self.driver.execute_script("arguments[0].click();", radio)
                logger.info(f"[RADIO] Strategy 5: double_click aplicado")
                time.sleep(0.5)
            except Exception as e:
                logger.warning(f"[RADIO] Strategy 5 falló: {e}")

            # Final comprehensive verification after applying all strategies
            try:
                # Primary verification method
                is_checked = radio.get_attribute("IsChecked")
                logger.info(f"[RADIO] Verificación final primaria: IsChecked={is_checked}")
                
                # Secondary verification methods for WPF
                if is_checked is None or is_checked.lower() != "true":
                    is_selected = radio.get_attribute("IsSelected")
                    is_pressed = radio.get_attribute("IsPressed")
                    value = radio.get_attribute("Value")
                    
                    logger.info(f"[RADIO] Verificación final secundaria: IsSelected={is_selected}, IsPressed={is_pressed}, Value={value}")
                    
                    # Consider selected if any indicator is positive
                    if ((is_checked and is_checked.lower() == "true") or 
                        (is_selected and is_selected.lower() == "true") or 
                        (is_pressed and is_pressed.lower() == "true")):
                        logger.info(f"[RADIO] ✓ RadioButton '{radio_name}' seleccionado correctamente (verificación combinada)")
                        return
                
                # If all checks pass with positive results
                if is_checked and is_checked.lower() == "true":
                    logger.info(f"[RADIO] ✓ RadioButton '{radio_name}' seleccionado correctamente (verificación final)")
                    return
                else:
                    logger.error(f"[RADIO] ✗ Verificación final fallida: RadioButton '{radio_name}' no está seleccionado (IsChecked={is_checked})")
                    # Don't return successfully - raise error to indicate failure
                    raise RuntimeError(f"No se pudo verificar la selección del RadioButton '{radio_name}'")
                    
                    # For WPF applications, sometimes we need to force the selection by 
                    # using different approaches like sending key events or checking other attributes
                    try:
                        # Try alternative methods if IsChecked is not working properly
                        logger.info(f"[RADIO] Intentando métodos alternativos para forzar selección...")
                        
                        # Check for other common attributes that might indicate selection
                        logger.info(f"[RADIO] Verificando otros atributos del RadioButton...")
                        try:
                            # Try to get the element's value or other state indicators
                            value = radio.get_attribute("Value")
                            logger.info(f"[RADIO] Valor del elemento: {value}")
                            
                            # Try clicking one more time with a delay
                            radio.click()
                            time.sleep(0.5)
                            
                            # Verify again after forced click
                            is_checked = radio.get_attribute("IsChecked")
                            if is_checked and is_checked.lower() == "true":
                                logger.info(f"[RADIO] ✓ RadioButton '{radio_name}' seleccionado correctamente después de forzar selección")
                                return
                        except Exception as e2:
                            logger.warning(f"[RADIO] Error al forzar selección: {e2}")
                            
                    except Exception as e3:
                        logger.warning(f"[RADIO] Error en métodos alternativos: {e3}")
                        
            except Exception as e:
                logger.warning(f"[RADIO] Error en verificación final: {e}")

            logger.info(f"[RADIO] RadioButton '{radio_name}' — todas las estrategias aplicadas. Continuando.")
            return

        raise RuntimeError(f"RadioButton '{radio_name}' no se pudo encontrar después de {max_wait}s")

    # ── Element Capture ─────────────────────────────────

    def capture_elements_for_picker(self) -> list[dict]:
        """Capture visible UI elements for the visual element picker."""
        if not self.driver:
            raise RuntimeError("Appium no conectado")

        elements = []
        try:
            all_elements = self.driver.find_elements(By.XPATH, "//*")
            for el in all_elements:
                try:
                    name = el.get_attribute("Name") or ""
                    automation_id = el.get_attribute("AutomationId") or ""
                    class_name = el.get_attribute("ClassName") or ""
                    control_type = el.get_attribute("LocalizedControlType") or el.tag_name or ""
                    is_displayed = el.is_displayed()
                    is_enabled = el.is_enabled()
                    text = el.text or ""
                    location = el.location
                    size = el.size

                    # Only include visible elements with some identifier
                    if not is_displayed:
                        continue
                    if not name and not automation_id and not text:
                        continue

                    elements.append({
                        "name": name,
                        "automationId": automation_id,
                        "className": class_name,
                        "controlType": control_type,
                        "text": text,
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

        logger.info(f"[PICKER] {len(elements)} elementos visibles capturados")
        return elements

    def disconnect(self):
        """Close Appium session."""
        if self.driver:
            try:
                self.driver.quit()
                logger.info("[DISCONNECT] Sesión de Appium cerrada.")
            except:
                pass
            self.driver = None
        self.handle = None
