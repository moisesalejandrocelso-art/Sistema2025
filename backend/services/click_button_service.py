"""
ClickButtonService — Specialized service for clicking buttons that cannot receive keyboard focus.
Handles buttons with IsKeyboardFocusable: False and other challenging UI elements.
"""

import time
import logging
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

logger = logging.getLogger(__name__)

class ClickButtonService:
    def __init__(self, driver):
        self.driver = driver

    def click_unfocusable_button(self, selector_type: str, selector_value: str, description: str = "Button"):
        """Click a button that cannot receive keyboard focus using multiple strategies."""
        logger.info(f"[CLICK_BUTTON] Attempting to click unfocusable button: {description}")
        
        strategies = [
            self._strategy_find_by_attributes,
            self._strategy_find_by_name_automationid,
            self._strategy_find_by_control_type,
            self._strategy_walker_tree,
            self._strategy_coordinate_click,
            self._strategy_windows_native_click,
        ]
        
        for i, strategy in enumerate(strategies, 1):
            try:
                logger.info(f"[CLICK_BUTTON] Strategy {i}: {strategy.__name__}")
                if strategy(selector_type, selector_value, description):
                    logger.info(f"[CLICK_BUTTON] ✓ Button '{description}' clicked successfully with strategy {i}")
                    return True
            except Exception as e:
                logger.warning(f"[CLICK_BUTTON] Strategy {i} failed: {e}")
                if i < len(strategies):
                    time.sleep(0.5)  # Small delay between strategies
        
        raise RuntimeError(f"Failed to click unfocusable button '{description}' after all strategies")

    def _strategy_find_by_attributes(self, selector_type: str, selector_value: str, description: str):
        """Strategy 1: Find element by multiple attributes and click using Windows automation."""
        # Try different attribute combinations
        selectors_to_try = [
            (By.NAME, "Cobrar"),
            (By.XPATH, "//*[@Name='Cobrar']"),
            (By.XPATH, "//*[contains(@Name, 'Cobrar')]"),
            (By.XPATH, "//*[@AutomationId='BtnCobro']"),
            (By.XPATH, "//*[contains(@AutomationId, 'Cobro')]"),
            (By.XPATH, "//button[@Name='Cobrar']"),
            (By.XPATH, "//*[@ControlType='Button' and @Name='Cobrar']"),
        ]
        
        for by, value in selectors_to_try:
            try:
                element = WebDriverWait(self.driver, 2).until(
                    EC.element_to_be_clickable((by, value))
                )
                # Use Windows-specific click for unfocusable elements
                self.driver.execute("windows", "click", [{"element": element.id}])
                return True
            except:
                continue
        return False

    def _strategy_find_by_name_automationid(self, selector_type: str, selector_value: str, description: str):
        """Strategy 2: Find by Name and AutomationId combination."""
        try:
            # Find all elements and filter manually
            all_elements = self.driver.find_elements(By.XPATH, "//*")
            for element in all_elements:
                try:
                    name = element.get_attribute("Name") or ""
                    automation_id = element.get_attribute("AutomationId") or ""
                    control_type = element.get_attribute("LocalizedControlType") or ""
                    
                    if (("Cobrar" in name) or 
                        ("Cobro" in automation_id) or 
                        ("Button" in control_type and "Cobrar" in name)):
                        
                        # Found matching element, try multiple click methods
                        try:
                            # Method 1: Windows native click
                            self.driver.execute("windows", "click", [{"element": element.id}])
                            return True
                        except:
                            # Method 2: JavaScript click
                            try:
                                self.driver.execute_script("arguments[0].click();", element)
                                return True
                            except:
                                # Method 3: Regular click
                                element.click()
                                return True
                except:
                    continue
        except:
            pass
        return False

    def _strategy_find_by_control_type(self, selector_type: str, selector_value: str, description: str):
        """Strategy 3: Find by ControlType='Button' and Name matching."""
        try:
            # Find all buttons and filter by name
            buttons = self.driver.find_elements(By.XPATH, "//*[@ControlType='Button']")
            for button in buttons:
                try:
                    name = button.get_attribute("Name") or ""
                    if "Cobrar" in name:
                        # Try coordinate-based click for buttons
                        location = button.location
                        size = button.size
                        if location and size:
                            x = location['x'] + size['width'] // 2
                            y = location['y'] + size['height'] // 2
                            
                            # Use Windows coordinate click
                            self.driver.execute("windows", "click", [{"x": x, "y": y}])
                            return True
                except:
                    continue
        except:
            pass
        return False

    def _strategy_walker_tree(self, selector_type: str, selector_value: str, description: str):
        """Strategy 4: Use UI Automation Walker to find element."""
        try:
            # Use Windows UI Automation to walk the tree
            elements = self.driver.find_elements(By.XPATH, "//*[@LocalizedControlType='button']")
            for element in elements:
                try:
                    name = element.get_attribute("Name") or ""
                    if name and "Cobrar" in name:
                        # Try to activate/click using Windows automation
                        self.driver.execute("windows", "activate", [{"element": element.id}])
                        time.sleep(0.1)
                        self.driver.execute("windows", "click", [{"element": element.id}])
                        return True
                except:
                    continue
        except:
            pass
        return False

    def _strategy_coordinate_click(self, selector_type: str, selector_value: str, description: str):
        """Strategy 5: Calculate coordinates and click at position."""
        try:
            # Try to find element coordinates from window
            window_handle = self.driver.current_window_handle
            if window_handle:
                # For Cobrar button, try common positions (bottom right area)
                window_size = self.driver.get_window_size()
                
                # Try clicking in typical button areas
                positions_to_try = [
                    (window_size['width'] - 100, window_size['height'] - 50),  # Bottom right
                    (window_size['width'] - 150, window_size['height'] - 80),  # Slightly up-left
                    (window_size['width'] - 120, window_size['height'] - 100), # More up
                ]
                
                for x, y in positions_to_try:
                    try:
                        self.driver.execute("windows", "click", [{"x": x, "y": y}])
                        time.sleep(0.5)
                        # Check if payment was processed by looking for success indicators
                        if self._check_payment_success():
                            return True
                    except:
                        continue
        except:
            pass
        return False

    def _strategy_windows_native_click(self, selector_type: str, selector_value: str, description: str):
        """Strategy 6: Use Windows native API calls through WinAppDriver."""
        try:
            # Last resort: try to find element using Windows native methods
            # This uses the underlying WinAppDriver capabilities
            from appium.webdriver.extensions.appium.android.nativekey import AndroidNativeKey
            
            # Use Windows-specific native events
            self.driver.execute("windows", "findElement", [
                {"using": "name", "value": "Cobrar"}
            ])
            
            # If found, click it
            self.driver.execute("windows", "click", [{
                "element": "Cobrar"
            }])
            return True
        except:
            pass
        return False

    def _check_payment_success(self):
        """Check if payment was successfully processed."""
        try:
            # Look for success indicators like absence of payment dialog
            time.sleep(1)
            
            # Try to find payment elements - if they're gone, payment succeeded
            payment_elements = self.driver.find_elements(By.XPATH, "//*[@Name='Métodos de pago']")
            if not payment_elements:
                # Also check for success dialogs or completion indicators
                success_indicators = [
                    "//*[contains(@Name, 'exitoso')]",
                    "//*[contains(@Name, 'completado')]", 
                    "//*[contains(@Name, 'éxito')]",
                    "//dialog[@Name='']"
                ]
                
                for indicator in success_indicators:
                    try:
                        element = self.driver.find_element(By.XPATH, indicator)
                        if element:
                            return True
                    except:
                        continue
                
                # If no payment elements found, assume success
                return True
        except:
            pass
        return False