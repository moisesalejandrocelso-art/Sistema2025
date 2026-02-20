import time
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

class SearchProductError(Exception):
    """Excepción personalizada para errores al buscar un producto."""
    pass

def close_possible_modals(driver):
    """Cierra posibles modales que puedan bloquear la búsqueda."""
    try:
        modal = driver.find_element(By.NAME, "Aceptar")
        modal.click()
        time.sleep(1)  # Espera un segundo para asegurarse de que el modal se cierre
        modal = driver.find_element(By.NAME, "Aceptar")
        modal.click()
        print("[INFO] Modal 'Aceptar' cerrado antes de buscar producto.")
        time.sleep(1)
    except Exception:
        pass  # No hay modal

def find_available_buttons(driver, timeout=5):
    """Encuentra todos los botones disponibles en la pantalla después de buscar un producto."""
    try:
        wait = WebDriverWait(driver, timeout)
        # Buscar todos los elementos que puedan ser botones (usando diferentes localizadores)
        buttons = []
        
        # Intentar encontrar botones por nombre (método más directo)
        try:
            button_elements = driver.find_elements(By.XPATH, "//Button")
            for btn in button_elements:
                if btn.is_displayed():
                    text = btn.text.strip()
                    if text and len(text) > 0:
                        buttons.append((text, btn))
                        print(f"[INFO] Botón encontrado: '{text}'")
        except Exception as e:
            print(f"[INFO] No se encontraron botones por XPath: {e}")

        # Intentar encontrar elementos con atributo "Name" que puedan ser botones
        try:
            button_elements = driver.find_elements(By.NAME, "*")
            for btn in button_elements:
                if btn.is_displayed() and btn.text.strip():
                    text = btn.text.strip()
                    if text and len(text) > 0 and text not in [b[0] for b in buttons]:
                        buttons.append((text, btn))
                        print(f"[INFO] Botón encontrado por nombre: '{text}'")
        except Exception as e:
            print(f"[INFO] No se encontraron botones por nombre: {e}")

        # Intentar encontrar elementos con tipo de control específico
        try:
            button_elements = driver.find_elements(By.XPATH, "//*[@ControlType='Button']")
            for btn in button_elements:
                if btn.is_displayed() and btn.text.strip():
                    text = btn.text.strip()
                    if text and len(text) > 0 and text not in [b[0] for b in buttons]:
                        buttons.append((text, btn))
                        print(f"[INFO] Botón encontrado por ControlType: '{text}'")
        except Exception as e:
            print(f"[INFO] No se encontraron botones por ControlType: {e}")

        return buttons
    except Exception as e:
        print(f"[ADVERTENCIA] Error al buscar botones disponibles: {e}")
        return []

def select_add_button(driver, product_code, max_retries=3):
    """Selecciona el botón 'Agregar' después de buscar un producto."""
    print(f"[INFO] Buscando botón 'Agregar' para el producto {product_code}...")
    retries = 0
    while retries < max_retries:
        try:
            # Primero intentamos encontrar el botón "Agregar" directamente
            wait = WebDriverWait(driver, 3)
            agregar_btn = wait.until(
                EC.presence_of_element_located((By.NAME, "Agregar"))
            )
            print(f"[ÉXITO] Botón 'Agregar' encontrado para {product_code}.")
            return agregar_btn
        except Exception as e:
            print(f"[INFO] No se encontró directamente el botón 'Agregar': {e}")
            
            # Si no encontramos el botón directamente, buscamos todos los botones disponibles
            available_buttons = find_available_buttons(driver, timeout=3)
            if available_buttons:
                print(f"[INFO] Botones disponibles: {[btn[0] for btn in available_buttons]}")
                
                # Buscar específicamente el botón "Agregar" entre los disponibles
                for btn_text, btn_element in available_buttons:
                    if "agregar" in btn_text.lower() or "add" in btn_text.lower():
                        print(f"[ÉXITO] Botón 'Agregar' encontrado: '{btn_text}'")
                        return btn_element
                
                # Si no encontramos exactamente "Agregar", buscamos por similitud
                for btn_text, btn_element in available_buttons:
                    if any(keyword in btn_text.lower() for keyword in ["agregar", "add", "plus", "+"]):
                        print(f"[ÉXITO] Botón similar a 'Agregar' encontrado: '{btn_text}'")
                        return btn_element
            else:
                print("[INFO] No se encontraron botones disponibles en la pantalla.")
            
            retries += 1
            if retries < max_retries:
                print(f"[INFO] Reintentando búsqueda del botón 'Agregar' (intento {retries}/{max_retries})...")
                time.sleep(1)
    
    print(f"[ERROR] No se pudo encontrar el botón 'Agregar' para el producto {product_code} después de {max_retries} intentos.")
    return None

def wait_for_product_load(driver, timeout=10):
    """Espera a que se cargue el producto después de la búsqueda."""
    try:
        wait = WebDriverWait(driver, timeout)
        # Esperar a que aparezca el botón "Agregar" o algún elemento que indique que el producto está cargado
        agregar_btn = wait.until(
            EC.presence_of_element_located((By.NAME, "Agregar"))
        )
        print("[INFO] Producto cargado correctamente, botón 'Agregar' disponible.")
        return True
    except Exception as e:
        print(f"[ADVERTENCIA] No se encontró el botón 'Agregar' después de buscar el producto: {e}")
        # Si no hay botón "Agregar", intentar encontrar otro indicador de carga
        try:
            # Intentar encontrar elementos que indiquen que el producto fue encontrado
            wait = WebDriverWait(driver, 3)
            # Buscar algún elemento que indique que se encontró el producto
            producto_encontrado = wait.until(
                EC.presence_of_element_located((By.NAME, "Producto encontrado"))
            )
            print("[INFO] Producto encontrado (indicador de carga).")
            return True
        except Exception:
            print("[ADVERTENCIA] No se pudo confirmar la carga del producto. Continuando...")
            return False

def search_product(driver, product_code, max_retries=5):
    """Busca un producto en la aplicación, reintentando si falla."""
    print(f"[INICIANDO] Buscando el producto {product_code}...")
    retries = 0
    while retries < max_retries:
        try:
            close_possible_modals(driver)
            wait = WebDriverWait(driver, 5)  # Aumenta el tiempo de espera
            search_box = wait.until(
                EC.presence_of_element_located((By.NAME, "Buscar producto"))
            )
            search_box.click()
            search_box.clear()
            search_box.send_keys(product_code + Keys.ENTER)
            print(f"[ÉXITO] Producto {product_code} buscado correctamente.")
            
            # Esperar a que se cargue el producto antes de continuar
            print("[INFO] Esperando carga del producto...")
            wait_for_product_load(driver, timeout=5)
            return True

        except Exception as e:
            retries += 1
            print(f"[INFO] Fallo al buscar el producto {product_code}. Reintentando en 10 segundos... (Intento {retries}/{max_retries}) ({e})")
            time.sleep(1)
    raise SearchProductError(f"No se pudo buscar el producto {product_code} después de {max_retries} intentos.")

def add_product_multiple_times(driver, product_code, quantity):
    """Agrega un producto la cantidad especificada sin volver a escribir el código."""
    print(f"[INFO] Agregando producto {product_code} {quantity} veces...")
    
    try:
        # Primero intentamos encontrar el botón "Agregar" 
        wait = WebDriverWait(driver, 10)
        agregar_btn = wait.until(
            EC.element_to_be_clickable((By.NAME, "Agregar"))
        )
        print(f"[ÉXITO] Botón 'Agregar' encontrado para {product_code}.")
        
        # Hacer clic en el botón "Agregar" la cantidad especificada
        for j in range(quantity):
            try:
                # Esperar un momento antes de hacer clic para asegurar que el botón esté listo
                time.sleep(0.5)
                
                # Asegurarse de que el botón esté visible y habilitado antes de hacer clic
                if agregar_btn.is_displayed() and agregar_btn.is_enabled():
                    print(f"[INFO] Haciendo clic en botón 'Agregar' para {product_code} (intentos: {j+1}/{quantity})")
                    agregar_btn.click()
                    print(f"[INFO] Producto {product_code} agregado {j+1}/{quantity} veces")
                else:
                    print(f"[ADVERTENCIA] Botón 'Agregar' no está visible o habilitado para {product_code}")
                    # Intentar encontrar el botón nuevamente si no está interactuable
                    wait = WebDriverWait(driver, 5)
                    agregar_btn = wait.until(
                        EC.element_to_be_clickable((By.NAME, "Agregar"))
                    )
                    print(f"[INFO] Botón 'Agregar' encontrado nuevamente para {product_code}")
                    time.sleep(0.3)  # Pequeño retraso antes del nuevo clic
                    agregar_btn.click()
                    print(f"[INFO] Producto {product_code} agregado {j+1}/{quantity} veces")
                
                # Aumentar el retraso entre clics para mayor estabilidad
                time.sleep(1.0)  # Más tiempo entre clics para asegurar que se procese cada uno
                
                # Después de cada clic, verificar si hay ventana de recomendación
                print("[INFO] Verificando si hay ventana de recomendación después del clic...")
                handle_all_recommendations(driver, action="accept")
                
            except Exception as e:
                print(f"[ERROR] No se pudo hacer clic en el botón 'Agregar' para {product_code} (intento {j+1}): {e}")
                # Intentar encontrar y hacer clic nuevamente
                try:
                    wait = WebDriverWait(driver, 5)
                    agregar_btn = wait.until(
                        EC.element_to_be_clickable((By.NAME, "Agregar"))
                    )
                    print(f"[INFO] Botón 'Agregar' encontrado nuevamente para {product_code}")
                    time.sleep(0.3)  # Pequeño retraso antes del nuevo clic
                    agregar_btn.click()
                    print(f"[INFO] Producto {product_code} agregado {j+1}/{quantity} veces")
                    time.sleep(1.0)  # Tiempo adicional entre clics
                    
                    # Después de cada clic, verificar si hay ventana de recomendación
                    print("[INFO] Verificando si hay ventana de recomendación después del clic...")
                    handle_all_recommendations(driver, action="accept")
                except Exception as e2:
                    print(f"[ERROR] No se pudo hacer clic en el botón 'Agregar' incluso después de reintentar: {e2}")
                    # Si aún no funciona, continuar con el siguiente producto
                    print(f"[ADVERTENCIA] Continuando con el siguiente producto después de fallo en {product_code}")
                    break
                    
        return True
        
    except Exception as e:
        print(f"[ERROR] No se pudo agregar el producto {product_code}: {e}")
        return False

def find_and_click_add_button(driver, product_code, max_retries=3):
    """Busca y hace clic en el botón adecuado para agregar el producto."""
    print(f"[INFO] Buscando y seleccionando botón para agregar producto {product_code}...")
    
    # Primero intentamos encontrar el botón "Agregar" directamente
    try:
        wait = WebDriverWait(driver, 3)
        agregar_btn = wait.until(
            EC.element_to_be_clickable((By.NAME, "Agregar"))
        )
        print(f"[ÉXITO] Botón 'Agregar' encontrado directamente para {product_code}.")
        return agregar_btn
    except Exception as e:
        print(f"[INFO] No se encontró directamente el botón 'Agregar': {e}")
        
        # Si no encontramos el botón "Agregar", buscamos entre todos los elementos disponibles
        try:
            # Buscar todos los elementos que puedan ser botones en la pantalla actual
            buttons = driver.find_elements(By.XPATH, "//Button | //*[@ControlType='Button']")
            
            # Filtrar solo los elementos visibles
            visible_buttons = [btn for btn in buttons if btn.is_displayed()]
            
            print(f"[INFO] Se encontraron {len(visible_buttons)} botones visibles en la pantalla")
            
            # Buscar el botón que contiene palabras clave para agregar
            for btn in visible_buttons:
                try:
                    text = btn.text.strip().lower()
                    if text and any(keyword in text for keyword in ["agregar", "add", "plus", "+"]):
                        print(f"[ÉXITO] Botón encontrado: '{text}'")
                        return btn
                except Exception:
                    continue  # Si no podemos leer el texto, continuamos
                    
            # Si no encontramos uno con palabras clave específicas, seleccionar el primero que parezca un botón de agregar
            for btn in visible_buttons:
                try:
                    text = btn.text.strip().lower()
                    if text and len(text) > 0 and len(text) < 20:  # Asumimos que es un botón válido si tiene texto corto
                        print(f"[INFO] Botón potencial encontrado: '{text}'")
                        return btn
                except Exception:
                    continue
                    
        except Exception as e:
            print(f"[ERROR] Error al buscar botones en pantalla: {e}")
            
        # Si todo falla, intentar usar una estrategia más general
        try:
            # Buscar elementos que puedan ser el botón de agregar por posición o atributos
            wait = WebDriverWait(driver, 2)
            # Intentar encontrar cualquier botón cerca del área donde se espera el producto
            all_elements = driver.find_elements(By.XPATH, "//*")
            for element in all_elements:
                try:
                    if element.is_displayed():
                        text = element.text.strip()
                        # Buscar elementos que puedan ser botones con texto corto y significativo
                        if text and len(text) < 15 and any(keyword in text.lower() for keyword in ["agregar", "add", "+"]):
                            print(f"[INFO] Botón encontrado por texto: '{text}'")
                            return element
                except Exception:
                    continue
        except Exception as e:
            print(f"[ERROR] Error en búsqueda alternativa: {e}")
    
    print(f"[ERROR] No se pudo encontrar botón para agregar producto {product_code}")
    return None

def handle_recommendation_window(driver, action="accept", max_retries=3):
    """Maneja la ventana de recomendación que aparece después de agregar un producto."""
    print("[INFO] Buscando ventana de recomendación...")
    
    recommendation_count = 0
    max_recommendations = 5  # Limitar a 5 recomendaciones para evitar bucles infinitos
    
    # Primero intentamos encontrar elementos con "OPORTUNIDAD" - esta es la parte crítica
    opportunity_elements = driver.find_elements(By.XPATH, "//*[contains(@Name, 'Oportunidad') or contains(@Name, 'oportunidad') or contains(@Name, 'Recomendación') or contains(@Name, 'recomendación')]") 
    
    # Si encontramos ventanas emergentes, procesarlas
    if opportunity_elements:
        print(f"[INFO] Ventana de recomendación encontrada")
        
        # Procesar cada ventana de recomendación encontrada (máximo max_recommendations veces)
        for i in range(max_recommendations):
            # Volver a buscar ventanas emergentes para cada iteración
            try:
                opportunity_elements = driver.find_elements(By.XPATH, "//*[contains(@Name, 'Oportunidad') or contains(@Name, 'oportunidad') or contains(@Name, 'Recomendación') or contains(@Name, 'recomendación')]") 
                
                if not opportunity_elements:
                    print("[INFO] No hay más ventanas de recomendación")
                    break
                    
                recommendation_count += 1
                print(f"[INFO] Procesando ventana de recomendación #{recommendation_count}")
                
                # Buscar botones de acción dentro de esta ventana
                action_buttons = []
                
                # Intentar encontrar botones específicos para aceptar o rechazar
                if action.lower() == "accept":
                    # Buscar botón de "Aceptar", "Accept", "Aprobar", etc.
                    accept_keywords = ["aceptar", "accept", "aprobar", "ok", "continuar", "sí", "si"]
                    for keyword in accept_keywords:
                        try:
                            btn = WebDriverWait(driver, 2).until(
                                EC.element_to_be_clickable((By.NAME, keyword))
                            )
                            action_buttons.append(btn)
                            print(f"[INFO] Botón de aceptación encontrado: '{keyword}'")
                            break  # Encontramos uno, salir del bucle
                        except Exception:
                            continue
                elif action.lower() == "reject":
                    # Buscar botón de "Rechazar", "Reject", etc.
                    reject_keywords = ["rechazar", "reject", "cancelar", "no"]
                    for keyword in reject_keywords:
                        try:
                            btn = WebDriverWait(driver, 2).until(
                                EC.element_to_be_clickable((By.NAME, keyword))
                            )
                            action_buttons.append(btn)
                            print(f"[INFO] Botón de rechazo encontrado: '{keyword}'")
                            break  # Encontramos uno, salir del bucle
                        except Exception:
                            continue
                
                # Si no encontramos botones específicos, intentar encontrar elementos que puedan ser botones
                if not action_buttons:
                    print("[INFO] No se encontraron botones específicos, buscando elementos que puedan actuar como botones...")
                    
                    # Primero, buscar directamente los elementos "Agregar" y "Rechazar"
                    try:
                        agregar_elements = driver.find_elements(By.XPATH, "//*[contains(@Name, 'Agregar') or contains(@Text, 'Agregar')]")
                        rechazar_elements = driver.find_elements(By.XPATH, "//*[contains(@Name, 'Rechazar') or contains(@Text, 'Rechazar')]")
                        
                        for element in agregar_elements:
                            if element.is_displayed():
                                action_buttons.append(element)
                                print(f"[INFO] Botón 'Agregar' encontrado directamente")
                                break
                                
                        for element in rechazar_elements:
                            if element.is_displayed():
                                action_buttons.append(element)
                                print(f"[INFO] Botón 'Rechazar' encontrado directamente")
                                break
                    except Exception as e:
                        print(f"[INFO] Error al buscar elementos directos: {e}")
                    
                    # Si aún no encontramos botones, intentar búsqueda más rápida
                    if not action_buttons:
                        # Primero intentar encontrar los botones "Siguiente" o similares (más rápido)
                        try:
                            siguiente_elements = driver.find_elements(By.XPATH, "//*[contains(@Name, 'Siguiente') or contains(@Text, 'Siguiente')]")
                            for element in siguiente_elements:
                                if element.is_displayed():
                                    action_buttons.append(element)
                                    print(f"[INFO] Botón 'Siguiente' encontrado para acción")
                                    break
                        except Exception as e:
                            print(f"[INFO] Error al buscar botones 'Siguiente': {e}")
                
                # Si encontramos botones de acción, hacer clic en el primero
                if action_buttons:
                    action_button = action_buttons[0]
                    try:
                        action_button.click()
                        print(f"[ÉXITO] Acción '{action}' realizada en ventana de recomendación #{recommendation_count}")
                    except Exception as click_error:
                        print(f"[ERROR] No se pudo hacer clic en el botón de acción: {click_error}")
                else:
                    print("[ADVERTENCIA] No se encontraron botones de acción en la ventana de recomendación")
                    break  # Si no hay botones, salir del bucle
                    
            except Exception as e:
                print(f"[INFO] Error procesando ventana de recomendación #{i+1}: {e}")
                break  # Si hay error, salir del bucle para evitar bucles infinitos
    
    else:
        print("[INFO] No se encontró ventana de recomendación")
    
    print(f"[INFO] Procesadas {recommendation_count} recomendaciones en total")
    return True

def handle_all_recommendations(driver, action="accept"):
    """Maneja todas las ventanas de recomendación que puedan aparecer después de agregar un producto."""
    print("[INFO] Manejando todas las recomendaciones posibles...")
    
    # Bucle para continuar procesando recomendaciones mientras existan
    max_iterations = 10  # Límite máximo para evitar bucles infinitos
    iteration = 0
    
    while iteration < max_iterations:
        try:
            # Primero verificamos si existe una ventana de oportunidad
            opportunity_elements = driver.find_elements(By.XPATH, "//*[contains(@Name, 'Oportunidad') or contains(@Name, 'oportunidad') or contains(@Name, 'Recomendación') or contains(@Name, 'recomendación')]") 
            
            if not opportunity_elements:
                print("[INFO] No se encontró ventana de recomendación")
                break  # Si no hay más ventanas, salir del bucle
            
            # Si hay ventana de oportunidad, procesarla
            print(f"[INFO] Ventana de recomendación encontrada, procesando...")
            
            # Buscar botones de acción dentro de esta ventana
            action_buttons = []
            
            # Intentar encontrar botones específicos para aceptar o rechazar
            if action.lower() == "accept":
                # Buscar botón de "Aceptar", "Accept", "Aprobar", etc.
                accept_keywords = ["aceptar", "accept", "aprobar", "ok", "continuar", "sí", "si"]
                for keyword in accept_keywords:
                    try:
                        btn = WebDriverWait(driver, 2).until(
                            EC.element_to_be_clickable((By.NAME, keyword))
                        )
                        action_buttons.append(btn)
                        print(f"[INFO] Botón de aceptación encontrado: '{keyword}'")
                        break  # Encontramos uno, salir del bucle
                    except Exception:
                        continue
            elif action.lower() == "reject":
                # Buscar botón de "Rechazar", "Reject", etc.
                reject_keywords = ["rechazar", "reject", "cancelar", "no"]
                for keyword in reject_keywords:
                    try:
                        btn = WebDriverWait(driver, 2).until(
                            EC.element_to_be_clickable((By.NAME, keyword))
                        )
                        action_buttons.append(btn)
                        print(f"[INFO] Botón de rechazo encontrado: '{keyword}'")
                        break  # Encontramos uno, salir del bucle
                    except Exception:
                        continue
            
            # Si no encontramos botones específicos, intentar encontrar elementos que puedan ser botones
            if not action_buttons:
                print("[INFO] No se encontraron botones específicos, buscando elementos que puedan actuar como botones...")
                
                # Primero, buscar directamente los elementos "Agregar" y "Rechazar"
                try:
                    agregar_elements = driver.find_elements(By.XPATH, "//*[contains(@Name, 'Agregar') or contains(@Text, 'Agregar')]")
                    rechazar_elements = driver.find_elements(By.XPATH, "//*[contains(@Name, 'Rechazar') or contains(@Text, 'Rechazar')]")
                    
                    for element in agregar_elements:
                        if element.is_displayed():
                            action_buttons.append(element)
                            print(f"[INFO] Botón 'Agregar' encontrado directamente")
                            break
                            
                    for element in rechazar_elements:
                        if element.is_displayed():
                            action_buttons.append(element)
                            print(f"[INFO] Botón 'Rechazar' encontrado directamente")
                            break
                except Exception as e:
                    print(f"[INFO] Error al buscar elementos directos: {e}")
                
                # Si aún no encontramos botones, intentar búsqueda más rápida
                if not action_buttons:
                    # Primero intentar encontrar los botones "Siguiente" o similares (más rápido)
                    try:
                        siguiente_elements = driver.find_elements(By.XPATH, "//*[contains(@Name, 'Siguiente') or contains(@Text, 'Siguiente')]")
                        for element in siguiente_elements:
                            if element.is_displayed():
                                action_buttons.append(element)
                                print(f"[INFO] Botón 'Siguiente' encontrado para acción")
                                break
                    except Exception as e:
                        print(f"[INFO] Error al buscar botones 'Siguiente': {e}")
            
            # Si encontramos botones de acción, hacer clic en el primero
            if action_buttons:
                action_button = action_buttons[0]
                try:
                    action_button.click()
                    print(f"[ÉXITO] Acción '{action}' realizada en ventana de recomendación")
                except Exception as click_error:
                    print(f"[ERROR] No se pudo hacer clic en el botón de acción: {click_error}")
            else:
                print("[ADVERTENCIA] No se encontraron botones de acción en la ventana de recomendación")
                break  # Si no hay botones, salir del bucle
                
            iteration += 1
            time.sleep(0.5)  # Pequeño retraso entre iteraciones
            
        except Exception as e:
            print(f"[ERROR] Error procesando recomendación: {e}")
            break  # Si hay error, salir del bucle para evitar bucles infinitos
    
    print(f"[INFO] Procesadas {iteration} recomendaciones en total")
    return True
