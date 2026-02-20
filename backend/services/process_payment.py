import asyncio
import logging
import time
import platform
import pygetwindow as gw
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import (
    NoSuchElementException, TimeoutException, NoSuchWindowException, WebDriverException
)
import traceback

# Configuración de logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

class ProcessPaymentError(Exception):
    """Excepción personalizada para errores al procesar el pago."""
    pass

def is_driver_active(driver):
    """Verifica si el driver sigue activo y la ventana está disponible."""
    try:
        _ = driver.title
        return True
    except (NoSuchWindowException, WebDriverException):
        logger.error("El driver ya no está activo o la ventana se cerró.")
        return False

def validate_amount(amount):
    """Valida que el monto sea un número positivo."""
    if not isinstance(amount, (int, float)) or amount <= 0:
        raise ProcessPaymentError("El monto debe ser un número positivo.")

def get_current_windows():
    """Obtiene una lista actual de ventanas con título 'SimiPOS'."""
    return gw.getWindowsWithTitle("SimiPOS")

def process_payment(driver, amount, max_attempts=20, wait_timeout=10, short_timeout=5):
    """Ingresa un monto en el campo de cobro y finaliza el proceso de pago."""
    if not is_driver_active(driver):
        raise ProcessPaymentError("No se puede procesar el pago: el driver no está activo.")

    validate_amount(amount)
    
    try:
        logger.info(f"Buscando el campo de cobro con AutomationId='InputBox' para monto {amount}...")
        wait = WebDriverWait(driver, wait_timeout)
        campo_cobro = wait.until(EC.element_to_be_clickable((By.XPATH, "//*[@AutomationId='InputBox']")))
        logger.info("Campo encontrado. Ingresando el monto...")

        campo_cobro.click()  # Usar click para enfocar el campo
        campo_cobro.clear()
        campo_cobro.send_keys(str(amount))
        
        # Check if there's a Cobrar button step in the flow to avoid automatic Enter
        # This allows manual clicking of the Cobrar button
        logger.info(f"Se ingresó el valor {amount}. Esperando clic en botón 'Cobrar'...")

        # Capturar ventanas antes de procesar el pago
        previous_windows = get_current_windows()
        print(f"[INFO] Ventanas antes de procesar el pago: {len(previous_windows)}")

        for attempt in range(1, max_attempts + 1):
            try:
                logger.info(f"Intento {attempt}: Verificando botón 'Cobrar'...")
                short_wait = WebDriverWait(driver, short_timeout)
                # Try multiple selector strategies for the Cobrar button
                cobrar_btn = None
                selectors_to_try = [
                    (By.NAME, "Cobrar"),
                    (By.XPATH, "//*[@AutomationId='BtnCobro']"),
                    (By.XPATH, "//*[contains(@Name, 'Cobrar')]"),
                    (By.XPATH, "//*[contains(@AutomationId, 'Cobro')]")
                ]
                
                for selector_by, selector_value in selectors_to_try:
                    try:
                        cobrar_btn = short_wait.until(EC.element_to_be_clickable((selector_by, selector_value)))
                        logger.info(f"Botón 'Cobrar' encontrado con selector: {selector_by} = {selector_value}")
                        break
                    except:
                        continue
                
                if not cobrar_btn:
                    raise TimeoutException("No se encontró el botón 'Cobrar' con ningún selector")
                    
                cobrar_btn.click()
                logger.info(f"Botón 'Cobrar' clickeado en intento {attempt}.")
                
                # Espera dinámica para confirmación
                WebDriverWait(driver, 2).until(
                    lambda d: is_payment_complete(d, short_wait) or handle_modals(d, short_wait)
                )
                if is_payment_complete(driver, short_wait):
                    logger.info("Pago completado correctamente.")
                    # Esperar a que cambie de ventana después del pago
                    print("[INFO] Esperando cambio de ventana después de procesar el pago...")
                    time.sleep(1)  # Pequeño retraso inicial
                    if len(previous_windows) > 0:
                        # Usar la función auxiliar para esperar cambio de ventana
                        from main import wait_for_window_change
                        wait_for_window_change(previous_windows, timeout=5)
                    else:
                        print("[INFO] No hay ventanas previas para comparar, continuando...")
                    return True

            except (TimeoutException, NoSuchElementException):
                logger.info("Botón 'Cobrar' no disponible. Verificando si 'Métodos de pago' está visible...")
                try:
                    driver.find_element(By.XPATH, "//*[contains(@Name, 'Métodos de pago')]")
                    logger.info("Elemento 'Métodos de pago' visible. La venta NO se ha cobrado. Reintentando cobro...")
                    capture_amount(driver, amount, wait)
                    continue
                except NoSuchElementException:
                    logger.info("Elemento 'Métodos de pago' no visible. Verificando si el pago está completo...")
                    if is_payment_complete(driver, short_wait):
                        logger.info("Venta completada sin necesidad de botón 'Cobrar'.")
                        # Esperar a que cambie de ventana después del pago
                        print("[INFO] Esperando cambio de ventana después de procesar el pago...")
                        time.sleep(1)  # Pequeño retraso inicial
                        if len(previous_windows) > 0:
                            # Usar la función auxiliar para esperar cambio de ventana
                            from main import wait_for_window_change
                            wait_for_window_change(previous_windows, timeout=5)
                        else:
                            print("[INFO] No hay ventanas previas para comparar, continuando...")
                        return True
                    logger.warning("Venta incompleta. Reintentando...")
                    continue

            # Maneja modales y reintenta si es necesario
            if handle_modals(driver, short_wait):
                logger.info("Modal manejado. Reintentando captura del monto...")
                capture_amount(driver, amount, wait)
                continue

            if attempt > 5 and not is_driver_active(driver):
                raise ProcessPaymentError("Driver no activo tras múltiples intentos.")

            logger.warning("Pago no confirmado. Reintentando...")
            capture_amount(driver, amount, wait)

    except Exception as e:
        logger.error(f"Excepción general en proceso de pago: {e}")
        traceback.print_exc()
        raise ProcessPaymentError(f"No se pudo procesar el pago de {amount}: {e}")

    raise ProcessPaymentError(f"Pago de {amount} falló tras {max_attempts} intentos.")

def handle_modals(driver, wait):
    """Maneja cualquier modal visible, como 'Aceptar', 'OK', o 'Confirmar'."""
    modal_buttons = ["Aceptar"]
    for button_name in modal_buttons:
        try:
            btn = wait.until(EC.element_to_be_clickable((By.NAME, button_name)))
            btn.click()
            time.sleep(1)  # Espera breve para asegurar que el modal se cierre
            btn = wait.until(EC.element_to_be_clickable((By.NAME, button_name)))
            btn.click()
            logger.info(f"Modal '{button_name}' cerrado.")
            return True
        except (TimeoutException, NoSuchElementException):
            logger.info(f"No se detectó modal '{button_name}'.")
    return False

def handle_no_internet_modal(driver, wait):
    """Maneja el modal específico de 'Sin conexión'."""
    logger.info("Buscando modal 'Sin conexión'...")
    try:
        aceptar_btn = wait.until(EC.element_to_be_clickable((By.NAME, "Aceptar")))
        aceptar_btn.click()
        logger.info("Modal de 'Sin conexión' cerrado.")
        return True
    except (TimeoutException, NoSuchElementException):
        logger.info("No se detectó modal 'Sin conexión'.")
        return False

def is_payment_complete(driver, wait):
    """Evalúa si el pago ya ha sido completado."""
    try:
        # Condición principal: el campo de cobro ya no está presente
        wait.until_not(EC.presence_of_element_located((By.XPATH, "//*[@AutomationId='InputBox']")))
        logger.info("Campo de cobro ya no está presente.")
        
        # Validación secundaria: no hay modales pendientes
        try:
            wait.until(EC.presence_of_element_located((By.NAME, "Aceptar")))
            logger.info("Modal 'Aceptar' aún presente. Pago NO completo.")
            return False
        except TimeoutException:
            logger.info("No hay modales pendientes.")
            
        # Validación adicional: verifica que no exista el texto "Métodos de pago"
        try:
            driver.find_element(By.XPATH, "//*[contains(@Name, 'Métodos de pago')]")
            logger.info("'Métodos de pago' aún presente. Pago NO completo.")
            return False
        except NoSuchElementException:
            logger.info("'Métodos de pago' no presente. Pago completo.")
            return True
            
    except TimeoutException:
        logger.info("Campo de cobro aún presente. Pago NO completo.")
        return False

def capture_amount(driver, amount, wait):
    """Reingresa el monto en el campo de entrada, solo si el campo está disponible."""
    try:
        logger.info("Reingresando monto en campo...")
        campo_cobro = wait.until(EC.element_to_be_clickable((By.XPATH, "//*[@AutomationId='InputBox']")))
        campo_cobro.click()  # Usar click para enfocar el campo
        campo_cobro.clear()
        campo_cobro.send_keys(str(amount))
        campo_cobro.send_keys(Keys.ENTER)
        logger.info(f"Monto {amount} ingresado nuevamente.")
    except (TimeoutException, NoSuchElementException):
        logger.info("Campo de cobro no disponible. Es probable que el pago ya se haya completado.")
    except Exception as e:
        logger.error(f"Fallo al ingresar monto nuevamente: {e}")
        traceback.print_exc()
        raise ProcessPaymentError(f"No se pudo recapturar el monto {amount}: {e}")

# Para compatibilidad con Pyodide (si es necesario)
async def main():
    # Aquí iría la inicialización del driver y la llamada a process_payment
    pass

if platform.system() == "Emscripten":
    asyncio.ensure_future(main())
else:
    if __name__ == "__main__":
        asyncio.run(main())
