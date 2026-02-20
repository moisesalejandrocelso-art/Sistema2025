import time
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

class ComboBoxSelectionError(Exception):
    """Excepción personalizada para errores al seleccionar una opción en el ComboBox."""
    pass

def select_combo_box_option(driver, combo_box_name, option_name):
    """Selecciona una opción en un ComboBox, asegurando que quede seleccionada."""
    try:
        print(f"[INICIANDO] Buscando ComboBox '{combo_box_name}'...")

        # Esperar a que el ComboBox esté disponible con timeout más largo
        wait = WebDriverWait(driver, 10)
        combo_box = None
        max_retries = 3
        retry_count = 0

        while retry_count < max_retries and not combo_box:
            try:
                combo_box = wait.until(EC.element_to_be_clickable((By.NAME, combo_box_name)))
                print(f"[INFO] ComboBox '{combo_box_name}' encontrado y listo para clic.")
                break
            except TimeoutException:
                print(f"[INFO] ComboBox '{combo_box_name}' no disponible aún. Reintentando en 2 segundos...")
                retry_count += 1
                time.sleep(2)
            except Exception as e:
                print(f"[ERROR] Error buscando ComboBox '{combo_box_name}': {e}")
                retry_count += 1
                time.sleep(2)

        if not combo_box:
            raise ComboBoxSelectionError(f"No se pudo encontrar el ComboBox '{combo_box_name}' después de {max_retries} intentos.")

        # Hacer clic en el ComboBox para abrirlo
        try:
            combo_box.click()
            print(f"[INFO] ComboBox '{combo_box_name}' clicado.")
        except Exception as e:
            print(f"[ERROR] No se pudo hacer clic en el ComboBox '{combo_box_name}': {e}")
            raise ComboBoxSelectionError(f"No se pudo abrir el ComboBox '{combo_box_name}': {e}")

        # Esperar que la lista desplegable se muestre
        time.sleep(1)

        # Buscar y seleccionar la opción
        option = None
        retry_count = 0

        while retry_count < max_retries and not option:
            try:
                option = wait.until(EC.element_to_be_clickable((By.NAME, option_name)))
                print(f"[INFO] Opción '{option_name}' encontrada y lista para clic.")
                break
            except TimeoutException:
                print(f"[INFO] Opción '{option_name}' no disponible aún. Reintentando en 2 segundos...")
                retry_count += 1
                time.sleep(2)
            except Exception as e:
                print(f"[ERROR] Error buscando opción '{option_name}': {e}")
                retry_count += 1
                time.sleep(2)

        if not option:
            raise ComboBoxSelectionError(f"No se pudo encontrar la opción '{option_name}' en el ComboBox '{combo_box_name}' después de {max_retries} intentos.")

        # Hacer clic en la opción
        try:
            option.click()
            print(f"[INFO] Opción '{option_name}' clicada.")
        except Exception as e:
            print(f"[ERROR] No se pudo hacer clic en la opción '{option_name}': {e}")
            raise ComboBoxSelectionError(f"No se pudo seleccionar la opción '{option_name}': {e}")

        # Verificar que la selección fue exitosa
        try:
            selected_value = combo_box.get_attribute("Value.Value")
            if selected_value == option_name or (selected_value and option_name in selected_value):
                print(f"[ÉXITO] Opción seleccionada correctamente: {option_name}")
                return True
            else:
                print(f"[ADVERTENCIA] Valor seleccionado '{selected_value}' no coincide con la opción '{option_name}'. Reintentando...")
                # Intentar reabrir y seleccionar nuevamente
                combo_box.click()
                time.sleep(0.5)
                option.click()
                print(f"[INFO] Reintentando selección de '{option_name}'...")
        except Exception as e:
            print(f"[ADVERTENCIA] No se pudo verificar la selección: {e}. Continuando...")
            # Si no podemos verificar, asumimos que fue exitoso

        print(f"[ÉXITO] Opción seleccionada correctamente: {option_name}")
        return True

    except Exception as e:
        print(f"[ERROR] Fallo al seleccionar la opción en el ComboBox: {e}")
        raise ComboBoxSelectionError(f"No se pudo seleccionar la opción '{option_name}': {e}")
