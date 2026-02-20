import time
import socket
import pygetwindow as gw

class ContinueSaleError(Exception):
    """Excepción personalizada para errores al continuar con la venta."""
    pass

def check_internet_connection(timeout=3):
    """Verifica si hay conexión a internet intentando conectarse a Google DNS."""
    try:
        socket.setdefaulttimeout(timeout)
        host = socket.gethostbyname("8.8.8.8")
        s = socket.create_connection((host, 53), timeout)
        s.close()
        return True
    except Exception:
        return False

def get_current_windows():
    """Obtiene una lista actual de ventanas con título 'SimiPOS'."""
    return gw.getWindowsWithTitle("SimiPOS")

def continue_sale(driver):
    """Hace clic en el botón 'Continuar' solo si hay internet, asegurando que el clic fue exitoso."""
    try:
        # Espera hasta que haya internet
        while not check_internet_connection():
            print("[ADVERTENCIA] No hay conexión a internet. Esperando para reintentar...")
            time.sleep(5)

        # Capturar ventanas antes de hacer clic en continuar
        previous_windows = get_current_windows()
        print(f"[INFO] Ventanas antes de hacer clic en 'Continuar': {len(previous_windows)}")

        # Intenta hacer clic hasta que el botón desaparezca
        while True:
            try:
                continuar_btn = driver.find_element("name", "Continuar")
                continuar_btn.click()
                print("[INFO] Se hizo clic en 'Continuar'. Verificando si desaparece el botón...")
                time.sleep(2)
                # Verifica si el botón sigue presente
                driver.find_element("name", "Continuar")
                print("[ADVERTENCIA] El botón 'Continuar' sigue presente. Reintentando clic...")
                time.sleep(2)
            except Exception:
                print("[ÉXITO] Botón 'Continuar' ya no está presente. Continuando con la venta...")
                break
        
        # Esperar a que cambie de ventana después de continuar
        print("[INFO] Esperando cambio de ventana después de continuar con la venta...")
        time.sleep(1)  # Pequeño retraso inicial
        if len(previous_windows) > 0:
            # Usar la función auxiliar para esperar cambio de ventana
            from main import wait_for_window_change
            wait_for_window_change(previous_windows, timeout=5)
        else:
            print("[INFO] No hay ventanas previas para comparar, continuando...")
        
        return True
    except Exception as e:
        print(f"[ERROR] Fallo al continuar con la venta: {e}")
        raise ContinueSaleError(f"No se pudo continuar con la venta: {e}")
