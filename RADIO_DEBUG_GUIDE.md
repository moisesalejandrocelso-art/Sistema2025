# Guía de Depuración de Radio Buttons

## 🚀 Solución Implementada

He creado un sistema completo para depurar y solucionar el problema del radio button de "Consumidor final".

## 📋 Nuevas Funcionalidades

### 1. Selector WPF Mejorado (`wpf_radio_selector.py`)
- **8 estrategias diferentes** de selección específicas para WPF
- Verificación múltiple de atributos (IsChecked, IsSelected, Value, etc.)
- Localizadores específicos para aplicaciones Windows

### 2. Depurador de Radio Buttons (`radio_debugger.py`)
- Analiza **todos los radio buttons** en la ventana actual
- Busca por texto específico ("consumidor final")
- Sugiere localizadores XPath óptimos
- Muestra detalles completos de cada elemento

### 3. Probador en Tiempo Real (`test_radio_selection.py`)
- Prueba **múltiples estrategias** simultáneamente
- Devuelve resultados detallados de cada intento
- Identifica la estrategia exitosa automáticamente

### 4. Nuevos Endpoints API

#### `POST /api/debug/radio-buttons`
Analiza todos los radio buttons en la ventana actual.

**Parámetros:**
- `search_text` (opcional): Texto a buscar (default: "consumidor final")

**Respuesta:**
```json
{
  "status": "success",
  "search_text": "consumidor final",
  "total_radio_buttons": 5,
  "matching_radios": 2,
  "all_radios": [...],
  "matching_radios": [...],
  "suggested_locators": [...]
}
```

#### `POST /api/debug/test-radio-selection`
Prueba estrategias de selección en tiempo real.

**Parámetros:**
- `radio_name` (opcional): Nombre del radio button (default: "consumidor final")

**Respuesta:**
```json
{
  "status": "success",
  "result": {
    "radio_name": "consumidor final",
    "total_strategies_tested": 8,
    "strategies_found": 2,
    "strategies_successful": 1,
    "successful_strategy": {...},
    "all_results": [...]
  }
}
```

## 🔧 Cómo Usar

### Método 1: Desde el Frontend (Recomendado)
1. Abre la aplicación POS
2. Ve a la vista donde está el radio button de "Consumidor final"
3. Usa los nuevos endpoints desde el navegador o Postman:
   - `http://localhost:8000/api/debug/radio-buttons`
   - `http://localhost:8000/api/debug/test-radio-selection`

### Método 2: Para Desarrolladores
Puedes usar el código directamente:

```python
# Para depurar radio buttons
from services.radio_debugger import debug_radio_buttons
debugger = debug_radio_buttons(driver, "consumidor final")

# Para probar estrategias
from services.test_radio_selection import test_radio_selection_realtime
result = test_radio_selection_realtime(driver, "consumidor final")

# Para seleccionar con el nuevo método
from services.wpf_radio_selector import select_wpf_radio_button
success = select_wpf_radio_button(driver, "consumidor final")
```

## 🎯 Estrategias Implementadas

El nuevo selector WPF intenta estas estrategias en orden:

1. **Click directo** - Método estándar
2. **Windows Click (ActionChains)** - Más robusto para Windows
3. **Tecla SPACE** - Método alternativo para radio buttons
4. **Tecla ENTER** - Opción secundaria
5. **JavaScript Click** - Para elementos difíciles
6. **Doble clic** - Para implementaciones especiales
7. **Click en coordenadas** - Cuando el elemento no responde
8. **Click en contenedor padre** - Último recurso

## 🐛 Pasos para Solucionar

### 1. Primero, Analiza el Problema
```bash
curl -X POST "http://localhost:8000/api/debug/radio-buttons" \
  -H "Content-Type: application/json" \
  -d '{"search_text": "consumidor final"}'
```

Esto te mostrará:
- Cuántos radio buttons hay
- Sus atributos exactos
- Localizadores sugeridos

### 2. Prueba Estrategias
```bash
curl -X POST "http://localhost:8000/api/debug/test-radio-selection" \
  -H "Content-Type: application/json" \
  -d '{"radio_name": "consumidor final"}'
```

Esto probará automáticamente todas las estrategias y te dirá cuál funciona.

### 3. Aplica la Solución
El sistema ahora usa automáticamente el selector mejorado. Si encuentra una estrategia exitosa, la usará en futuras ejecuciones.

## ⚠️ Notas Importantes

1. **El error que veías antes era correcto** - ahora el sistema reporta errores reales en lugar de éxitos falsos
2. **WinAppDriver debe estar corriendo** en `http://127.0.0.1:4723`
3. **La aplicación debe estar visible** cuando hagas las pruebas
4. **Los logs están mejorados** - mira la consola del backend para ver detalladamente qué está intentando

## 🔍 Qué Buscar en los Resultados

Cuando ejecutes el análisis, busca:

### Atributos del Radio Button Correcto:
- `name`: "Consumidor final" o similar
- `controltype`: "RadioButton" 
- `localizedcontroltype`: "radio button"
- `isenabled`: "true"
- `isvisible`: "true"

### Localizadores Sugeridos:
El sistema sugerirá XPath específicos como:
- `//RadioButton[@Name='Consumidor final']`
- `//*[@Name='Consumidor final' and @ControlType='RadioButton']`

### Estrategias Exitosas:
El probador mostrará qué estrategia funcionó, por ejemplo:
```
 Estrategia exitosa: name, locator: "Consumidor final"
```

## 📞 Si Hay Problemas

1. **Revisa los logs del backend** - ahora son muy detallados
2. **Verifica que WinAppDriver esté corriendo**
3. **Asegúrate que la aplicación esté visible**
4. **Usa los endpoints de depuración** para entender mejor el problema

---

**Listo para probar! 🚀**

Ejecuta los endpoints de depuración y dime qué resultados obtienes. Con esa información podré ajustar la solución perfectamente para tu aplicación específica.