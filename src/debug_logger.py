#src/debug_logger.py
"""
Moduł do zapisywania informacji debugowych.
"""
import os
from datetime import datetime
from selenium.webdriver.remote.webdriver import WebDriver
from config import settings


class DebugLogger:
    """Klasa do zapisywania screenshotów, logów i HTML."""
    
    def __init__(self, debug_dir: str = None):
        self.debug_dir = debug_dir or settings.DEBUG_DIR
        os.makedirs(self.debug_dir, exist_ok=True)
    
    def save_debug_snapshot(self, driver: WebDriver, event_name: str, additional_info: str = ""):
        """
        Zapisuje pełny snapshot stanu przeglądarki.
        
        Args:
            driver: Instancja WebDriver
            event_name: Nazwa zdarzenia (np. "new_message", "conversation_change")
            additional_info: Dodatkowe informacje do zapisania w logu
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        event_dir = os.path.join(self.debug_dir, f"{timestamp}_{event_name}")
        os.makedirs(event_dir, exist_ok=True)
        
        # 1. Screenshot
        screenshot_path = os.path.join(event_dir, "screenshot.png")
        try:
            driver.save_screenshot(screenshot_path)
            print(f"✓ Screenshot zapisany: {screenshot_path}")
        except Exception as e:
            print(f"✗ Błąd zapisu screenshota: {e}")
        
        # 2. HTML strony
        html_path = os.path.join(event_dir, "page_source.html")
        try:
            with open(html_path, 'w', encoding='utf-8') as f:
                f.write(driver.page_source)
            print(f"✓ HTML zapisany: {html_path}")
        except Exception as e:
            print(f"✗ Błąd zapisu HTML: {e}")
        
        # 3. Log tekstowy z informacjami
        log_path = os.path.join(event_dir, "debug.log")
        try:
            with open(log_path, 'w', encoding='utf-8') as f:
                f.write(f"=== DEBUG LOG ===\n")
                f.write(f"Timestamp: {datetime.now().isoformat()}\n")
                f.write(f"Event: {event_name}\n")
                f.write(f"Current URL: {driver.current_url}\n")
                f.write(f"Page Title: {driver.title}\n")
                f.write(f"\n=== Additional Info ===\n")
                f.write(additional_info)
                f.write(f"\n\n=== Browser Logs ===\n")
                
                # Logi przeglądarki (jeśli dostępne)
                try:
                    browser_logs = driver.get_log('browser')
                    for log_entry in browser_logs:
                        f.write(f"{log_entry}\n")
                except Exception as log_error:
                    f.write(f"Browser logs not available: {log_error}\n")
                
            print(f"✓ Log zapisany: {log_path}")
        except Exception as e:
            print(f"✗ Błąd zapisu logu: {e}")
        
        return event_dir
    
    def save_error_snapshot(self, driver: WebDriver, error: Exception):
        """
        Zapisuje snapshot w przypadku błędu.
        
        Args:
            driver: Instancja WebDriver
            error: Wyjątek, który wystąpił
        """
        import traceback
        additional_info = f"ERROR: {type(error).__name__}\n{str(error)}\n\n"
        additional_info += f"Traceback:\n{traceback.format_exc()}"
        return self.save_debug_snapshot(driver, "error", additional_info)