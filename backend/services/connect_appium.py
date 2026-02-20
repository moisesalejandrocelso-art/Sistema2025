from appium import webdriver
from appium.options.windows import WindowsOptions
import time

class AppiumConnectionError(Exception):
    """Excepción personalizada para errores de conexión con Appium."""
    pass

def connect_appium(handle):
    """Conecta con Appium usando el handle de la ventana y devuelve el driver."""
    try:
        options = WindowsOptions()
        options.set_capability("appTopLevelWindow", handle)
        options.set_capability("newCommandTimeout", 300)
        # Minimal capabilities to avoid pointer issues while maintaining element detection
        options.set_capability("automationName", "Windows")
        options.set_capability("platformName", "Windows")
        driver = webdriver.Remote("http://127.0.0.1:4723", options=options)
        print("[ÉXITO] Conexión con Appium establecida.")
        time.sleep(1)  # Espera para asegurar que la conexión se establezca correctamente
        print("[ÉXITO] Esperando a que inicie Punto de venta.")
        return driver
    except Exception as e:
        print(f"[ERROR] Fallo al conectar con Appium: {e}")
        raise AppiumConnectionError(f"No se pudo conectar con Appium: {e}")
