import time

class RadioButtonSelectionError(Exception):
    """Excepción personalizada para errores al seleccionar un RadioButton."""
    pass

def select_radio_button(driver, radio_button_name):
    """Selecciona un RadioButton, reintentando hasta que esté disponible."""
    try:
        print(f"[INICIANDO] Buscando RadioButton '{radio_button_name}'...")

        while True:
            try:
                radio_button = driver.find_element("name", radio_button_name)
                radio_button.click()
                print(f"[ÉXITO] RadioButton '{radio_button_name}' seleccionado.")
                return True
            except Exception:
                print(f"[INFO] RadioButton '{radio_button_name}' no disponible aún. Reintentando en 2 segundos...")
                time.sleep(2)

    except Exception as e:
        print(f"[ERROR] Fallo al seleccionar el RadioButton: {e}")
        raise RadioButtonSelectionError(f"No se pudo seleccionar el RadioButton '{radio_button_name}': {e}")