import time
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

class ClearOrderError(Exception):
    """Excepción personalizada para errores al borrar el pedido."""
    pass

def clear_order(driver):
    """Limpia el pedido actual haciendo clic en 'Borrar pedido', con hasta 2 intentos. Si falla, continúa."""
    print("[INICIANDO] Intentando borrar el pedido...")
    max_intentos = 1
    intento = 0

    while intento < max_intentos:
        try:
            wait = WebDriverWait(driver, 2)
            boton_borrar = wait.until(
                EC.presence_of_element_located((By.NAME, "Borrar pedido"))
            )
            boton_borrar.click()
            print("[ÉXITO] Pedido borrado correctamente.")
            return True
        except Exception as e:
            intento += 1
            print(f"[INFO] Intento {intento} fallido. {('Reintentando en 4 segundos...' if intento < max_intentos else 'No se pudo borrar el pedido.')}")
            if intento < max_intentos:
                time.sleep(4)

    # No lanzar excepción: solo avisar
    print("[ADVERTENCIA] No se pudo borrar el pedido después de 2 intentos. Continuando ejecución...")
    return False
