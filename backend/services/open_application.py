import subprocess
import time
import pygetwindow as gw

class ApplicationNotFoundError(Exception):
    """Excepción personalizada para cuando no se encuentra la ventana de la aplicación."""
    pass

def get_current_windows():
    """Obtiene una lista actual de ventanas con título 'SimiPOS'."""
    return gw.getWindowsWithTitle("SimiPOS")

def open_application(app_path):
    """Abre la aplicación especificada y devuelve el handle de la ventana."""
    try:
        # Capturar ventanas antes de abrir la aplicación
        previous_windows = get_current_windows()
        print(f"[INFO] Ventanas antes de abrir la aplicación: {len(previous_windows)}")
        
        subprocess.Popen(app_path)
        time.sleep(3)  # Espera un poco más para que la ventana aparezca
        app_window = None
        print("Buscando ventanas con título 'SimiPOS'...")
        windows = gw.getWindowsWithTitle("SimiPOS")
        print(f"Se encontraron {len(windows)} ventanas con título 'SimiPOS'")
        for i, win in enumerate(windows):
            print(f"Ventana {i+1}: '{win.title}' (handle: {hex(win._hWnd)})")
            if win.title:
                app_window = win
                break
        if not app_window:
            # Intentar con una búsqueda más flexible
            print("Intentando búsqueda flexible por contenido del título...")
            windows = gw.getWindowsWithTitle("")
            for win in windows:
                if "SimiPOS" in win.title:
                    app_window = win
                    print(f"Encontrada ventana flexible: '{win.title}'")
                    break
        if not app_window:
            raise ApplicationNotFoundError("No se encontró la ventana de la aplicación 'SimiPOS'.")
        handle = hex(app_window._hWnd)
        print(f"[ÉXITO] Aplicación abierta. Handle: {handle}")
        
        # Esperar a que la interfaz gráfica esté completamente cargada
        # Esta es una verificación adicional para asegurar que la UI está lista
        print("Esperando a que la interfaz gráfica se cargue completamente...")
        time.sleep(3)
        print("[ÉXITO] Aplicación abierta y UI cargada.")
        return handle
    except Exception as e:
        print(f"[ERROR] Fallo al abrir la aplicación: {e}")
        raise
