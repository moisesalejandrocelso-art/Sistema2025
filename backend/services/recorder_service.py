"""
RecorderService — Records user interactions with the POS application.
Uses pynput for mouse/keyboard detection and pywinauto for element identification.
"""
import threading
import time
import logging
import ctypes
import ctypes.wintypes as wintypes
from typing import Callable, Optional, List
from pynput import mouse, keyboard

logger = logging.getLogger("recorder_service")

# Windows API for element identification
try:
    import comtypes
    from comtypes import CLSCTX_INPROC_SERVER
    import comtypes.client
    HAS_COMTYPES = True
except ImportError:
    HAS_COMTYPES = False


class RecordedStep:
    def __init__(self, action_type: str, description: str,
                 selector_type: str = None, selector_value: str = None,
                 value: str = None, wait_time: int = None):
        self.action_type = action_type
        self.description = description
        self.selector_type = selector_type
        self.selector_value = selector_value
        self.value = value
        self.wait_time = wait_time

    def to_dict(self):
        d = {
            "action_type": self.action_type,
            "description": self.description,
            "enabled": True,
        }
        if self.selector_type:
            d["selector_type"] = self.selector_type
        if self.selector_value:
            d["selector_value"] = self.selector_value
        if self.value:
            d["value"] = self.value
        if self.wait_time:
            d["wait_time"] = self.wait_time
        return d


class RecorderService:
    def __init__(self):
        self.recording = False
        self.steps: List[RecordedStep] = []
        self._on_step: Optional[Callable] = None
        self._mouse_listener: Optional[mouse.Listener] = None
        self._kb_listener: Optional[keyboard.Listener] = None
        self._appium_driver = None
        self._last_click_time = 0
        self._typing_buffer = ""
        self._typing_element_info = None
        self._last_action_time = 0
        self._target_window_rect = None
        self._target_window_handle = None

    def start(self, appium_driver, on_step: Callable, window_handle=None):
        """Start recording user interactions."""
        if self.recording:
            logger.warning("[RECORDER] Already recording")
            return

        self.recording = True
        self.steps = []
        self._appium_driver = appium_driver
        self._on_step = on_step
        self._typing_buffer = ""
        self._typing_element_info = None
        self._last_action_time = time.time()
        self._target_window_handle = window_handle

        # Get target window bounds if possible
        self._update_window_rect()

        # Start mouse listener
        self._mouse_listener = mouse.Listener(on_click=self._on_mouse_click)
        self._mouse_listener.start()

        # Start keyboard listener
        self._kb_listener = keyboard.Listener(
            on_press=self._on_key_press,
            on_release=self._on_key_release
        )
        self._kb_listener.start()

        logger.info("[RECORDER] Recording started")

    def stop(self):
        """Stop recording and return captured steps."""
        if not self.recording:
            return self.steps

        # Flush any pending typing
        self._flush_typing_buffer()

        self.recording = False

        if self._mouse_listener:
            self._mouse_listener.stop()
            self._mouse_listener = None

        if self._kb_listener:
            self._kb_listener.stop()
            self._kb_listener = None

        logger.info(f"[RECORDER] Recording stopped. {len(self.steps)} steps captured.")
        return [s.to_dict() for s in self.steps]

    def _update_window_rect(self):
        """Get the target window rectangle for filtering clicks."""
        try:
            if self._appium_driver:
                rect = self._appium_driver.get_window_rect()
                self._target_window_rect = rect
                logger.info(f"[RECORDER] Window rect: {rect}")
        except Exception as e:
            logger.warning(f"[RECORDER] Could not get window rect: {e}")
            self._target_window_rect = None

    def _is_in_target_window(self, x: int, y: int) -> bool:
        """Check if coordinates are within the target POS window."""
        if not self._target_window_rect:
            return True  # If we can't determine, assume yes

        r = self._target_window_rect
        return (r.get('x', 0) <= x <= r.get('x', 0) + r.get('width', 9999) and
                r.get('y', 0) <= y <= r.get('y', 0) + r.get('height', 9999))

    def _add_wait_if_needed(self):
        """Add a wait step if significant time passed between actions."""
        now = time.time()
        elapsed_ms = int((now - self._last_action_time) * 1000)
        if elapsed_ms > 2000:  # More than 2 seconds gap
            wait_step = RecordedStep(
                action_type="wait",
                description=f"Esperar {elapsed_ms}ms",
                wait_time=min(elapsed_ms, 10000)  # Cap at 10s
            )
            self.steps.append(wait_step)
            if self._on_step:
                self._on_step(wait_step.to_dict())
        self._last_action_time = now

    def _get_element_at_point(self, x: int, y: int) -> dict:
        """Get UI element info at the given screen coordinates using Appium."""
        element_info = {
            "name": "",
            "automation_id": "",
            "class_name": "",
            "control_type": "",
        }

        try:
            if not self._appium_driver:
                return element_info

            # Use pywinauto to get element at point
            from pywinauto import Desktop
            desktop = Desktop(backend="uia")

            element = desktop.from_point(x, y)
            if element:
                wrapper = element
                element_info["name"] = str(getattr(wrapper, 'element_info', wrapper).name or "")
                element_info["automation_id"] = str(getattr(wrapper, 'element_info', wrapper).automation_id or "")
                element_info["class_name"] = str(getattr(wrapper, 'element_info', wrapper).class_name or "")
                element_info["control_type"] = str(getattr(wrapper, 'element_info', wrapper).control_type or "")

                logger.info(f"[RECORDER] Element at ({x},{y}): name='{element_info['name']}', "
                           f"aid='{element_info['automation_id']}', class='{element_info['class_name']}', "
                           f"type='{element_info['control_type']}'")

        except Exception as e:
            logger.warning(f"[RECORDER] Could not identify element at ({x},{y}): {e}")

        return element_info

    def _determine_selector(self, element_info: dict) -> tuple:
        """Determine best selector type and value for an element."""
        # Priority: automation_id > name > class_name
        if element_info.get("automation_id"):
            return "accessibility_id", element_info["automation_id"]
        elif element_info.get("name"):
            return "name", element_info["name"]
        elif element_info.get("class_name"):
            return "class_name", element_info["class_name"]
        return None, None

    def _determine_action_type(self, element_info: dict) -> str:
        """Determine action type based on element control type."""
        control_type = element_info.get("control_type", "").lower()
        if "edit" in control_type or "text" in control_type:
            return "type"
        elif "combo" in control_type:
            return "select_combo"
        elif "radio" in control_type:
            return "select_radio"
        elif "button" in control_type or "menu" in control_type:
            return "click"
        elif "check" in control_type:
            return "click"
        return "click"

    def _on_mouse_click(self, x: int, y: int, button, pressed: bool):
        """Handle mouse click events."""
        if not self.recording or not pressed or button != mouse.Button.left:
            return

        # Debounce — ignore clicks within 300ms
        now = time.time()
        if now - self._last_click_time < 0.3:
            return
        self._last_click_time = now

        # Check if click is in target window
        if not self._is_in_target_window(x, y):
            return

        # Flush any pending typing first
        self._flush_typing_buffer()

        # Add wait if needed
        self._add_wait_if_needed()

        # Get element at click position
        element_info = self._get_element_at_point(x, y)
        selector_type, selector_value = self._determine_selector(element_info)
        action_type = self._determine_action_type(element_info)

        # If it's a text field, start capturing typing instead of click
        if action_type == "type":
            self._typing_element_info = element_info
            self._typing_buffer = ""
            logger.info(f"[RECORDER] Text field focused: {element_info.get('name', 'unknown')}")
            return

        # Build description
        el_name = element_info.get("name", "") or element_info.get("automation_id", "") or f"({x},{y})"
        description = f"Clic en '{el_name}'"

        step = RecordedStep(
            action_type=action_type,
            description=description,
            selector_type=selector_type,
            selector_value=selector_value,
        )
        self.steps.append(step)

        logger.info(f"[RECORDER] Step recorded: {step.to_dict()}")

        if self._on_step:
            self._on_step(step.to_dict())

    def _on_key_press(self, key):
        """Handle keyboard press events."""
        if not self.recording:
            return

        try:
            # Special keys
            if isinstance(key, keyboard.Key):
                key_name = key.name.capitalize()

                # If typing, flush buffer before recording special key
                if key_name in ("Enter", "Tab", "Escape", "F5", "Backspace", "Delete"):
                    self._flush_typing_buffer()
                    self._add_wait_if_needed()

                    step = RecordedStep(
                        action_type="send_keys",
                        description=f"Presionar tecla {key_name}",
                        value=key_name,
                    )
                    self.steps.append(step)

                    if self._on_step:
                        self._on_step(step.to_dict())
                    return

            # Regular character — add to typing buffer
            if hasattr(key, 'char') and key.char:
                self._typing_buffer += key.char

        except Exception as e:
            logger.warning(f"[RECORDER] Key press error: {e}")

    def _on_key_release(self, key):
        """Handle keyboard release events (unused but required by pynput)."""
        pass

    def _flush_typing_buffer(self):
        """Flush accumulated typing as a single 'type' step."""
        if not self._typing_buffer:
            return

        self._add_wait_if_needed()

        el_info = self._typing_element_info or {}
        selector_type, selector_value = self._determine_selector(el_info)
        el_name = el_info.get("name", "") or el_info.get("automation_id", "") or "campo"

        step = RecordedStep(
            action_type="type",
            description=f"Escribir '{self._typing_buffer}' en '{el_name}'",
            selector_type=selector_type,
            selector_value=selector_value,
            value=self._typing_buffer,
        )
        self.steps.append(step)

        logger.info(f"[RECORDER] Typing step recorded: {step.to_dict()}")

        if self._on_step:
            self._on_step(step.to_dict())

        self._typing_buffer = ""
        self._typing_element_info = None

    def get_steps(self) -> list:
        """Get all recorded steps."""
        return [s.to_dict() for s in self.steps]
