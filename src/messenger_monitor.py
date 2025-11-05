#src/messenger_monitor.py
"""
Klasa do monitorowania wiadomości w Messenger.
"""
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from src import utils
from src.debug_logger import DebugLogger
from config import settings
import logging

logger = logging.getLogger(__name__)


class MessengerMonitor:
    def __init__(self, driver, config=None):
        self.driver = driver
        self.config = config if config else settings.config
        self.last_message_count = 0
        self.debug_logger = DebugLogger()

        # Loguj konfigurację monitorowania
        logger.info(f"Monitor zainicjalizowany - tryb: {self.config.get_mode()}, zakres: {self.config.get_scope()}")
    
    def get_unread_conversations(self):
        """Znajduje nieprzeczytane rozmowy (uproszczony przykład)."""
        try:
            # Selektor może się zmieniać w zależności od interfejsu Facebooka
            unread_selectors = [
                "div[role='gridcell'] div[aria-label='Unread']",
                "span[aria-label='Unread']",
                # Dodaj więcej selektorów w razie potrzeby
            ]
            
            for selector in unread_selectors:
                try:
                    unread_elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if unread_elements:
                        return unread_elements
                except Exception:
                    continue
            
            return []
            
        except Exception as e:
            logger.error(f"Błąd podczas pobierania nieprzeczytanych konwersacji: {e}")
            self.debug_logger.save_error_snapshot(self.driver, e)  # NOWE
            return []
    
    def check_new_messages(self):
        """Sprawdza, czy są nowe wiadomości zgodnie z konfiguracją."""
        # Sprawdź czy monitoring jest włączony
        if not self.config.is_monitoring_enabled():
            logger.debug("Monitoring jest wyłączony w konfiguracji")
            return False

        # Sprawdź czy wykrywanie nowych wiadomości jest włączone
        if not self.config.should_detect_new_messages():
            logger.debug("Wykrywanie nowych wiadomości jest wyłączone w konfiguracji")
            return False

        unread_conversations = self.get_unread_conversations()
        current_count = len(unread_conversations)

        if current_count > self.last_message_count:
            logger.info(f"🔔 Znaleziono nowe wiadomości! Liczba nieprzeczytanych rozmów: {current_count}")

            # Zapisz debug snapshot przy nowych wiadomościach (jeśli włączone)
            if self.config.should_save_screenshots():
                additional_info = f"Poprzednia liczba nieprzeczytanych: {self.last_message_count}\n"
                additional_info += f"Aktualna liczba nieprzeczytanych: {current_count}\n"
                additional_info += f"Nowych wiadomości: {current_count - self.last_message_count}\n"

                self.debug_logger.save_debug_snapshot(
                    self.driver,
                    "new_messages_detected",
                    additional_info
                )

            # Obsługa akcji na nowe wiadomości
            self._handle_new_messages(current_count - self.last_message_count)

            # Opcjonalnie: powiadomienia
            if self.config.are_notifications_enabled():
                self._send_notification(f"Nowe wiadomości: {current_count - self.last_message_count}")

            self.last_message_count = current_count
            return True

        elif current_count < self.last_message_count:
            # Zapisz gdy liczba nieprzeczytanych się zmniejszyła (jeśli włączone)
            if self.config.should_save_screenshots():
                additional_info = f"Liczba nieprzeczytanych zmniejszyła się\n"
                additional_info += f"Poprzednia: {self.last_message_count}\n"
                additional_info += f"Aktualna: {current_count}\n"

                self.debug_logger.save_debug_snapshot(
                    self.driver,
                    "messages_count_decreased",
                    additional_info
                )

            self.last_message_count = current_count

        return False

    def _handle_new_messages(self, count):
        """Obsługuje akcje na nowe wiadomości zgodnie z konfiguracją."""
        actions = self.config.get('on_new_message.actions', [])

        for action in actions:
            if not action.get('enabled', False):
                continue

            action_type = action.get('type')

            if action_type == 'log':
                logger.info(f"📝 Akcja: Logowanie {count} nowych wiadomości")

            elif action_type == 'save_to_file':
                file_path = action.get('file_path', './data/messages.txt')
                file_format = action.get('format', 'txt')
                logger.info(f"💾 Akcja: Zapisywanie do pliku {file_path} (format: {file_format})")
                # TODO: Implementacja zapisywania do pliku

            elif action_type == 'mark_as_read':
                logger.info("✅ Akcja: Oznaczanie jako przeczytane")
                # TODO: Implementacja oznaczania jako przeczytane

    def _send_notification(self, message):
        """Wysyła powiadomienie zgodnie z konfiguracją."""
        methods = self.config.get_notification_methods()

        if 'console' in methods:
            logger.info(f"🔔 Powiadomienie: {message}")

        if 'log_file' in methods:
            logger.info(f"📄 Powiadomienie zapisane do logu: {message}")
    
    def run_monitoring_loop(self, interval=None):
        """Pętla monitorująca z wykorzystaniem konfiguracji."""
        # Użyj interwału z konfiguracji jeśli nie podano
        if interval is None:
            interval = self.config.get_polling_interval()

        logger.info(f"🔄 Rozpoczynam pętlę monitorowania (interwał: {interval}s)...")

        # Zapisz initial state (jeśli włączone)
        if self.config.should_save_screenshots():
            self.debug_logger.save_debug_snapshot(
                self.driver,
                "monitoring_start",
                f"Rozpoczęcie monitorowania z interwałem: {interval}s\nTryb: {self.config.get_mode()}\nZakres: {self.config.get_scope()}"
            )

        try:
            while True:
                try:
                    if self.check_new_messages():
                        # Opcjonalnie: Oznacz jako przeczytane lub podejmij inną akcję
                        pass

                    time.sleep(interval)

                except Exception as e:
                    logger.error(f"Błąd w pętli monitorowania: {e}")
                    # Zapisz błąd ale kontynuuj działanie (jeśli włączone)
                    if self.config.should_screenshot_on_error():
                        self.debug_logger.save_error_snapshot(self.driver, e)
                    time.sleep(interval)

        except KeyboardInterrupt:
            logger.info("⏹️ Zatrzymano monitorowanie przez użytkownika")
            # Zapisz final state (jeśli włączone)
            if self.config.should_save_screenshots():
                self.debug_logger.save_debug_snapshot(
                    self.driver,
                    "monitoring_stop",
                    "Zakończenie monitorowania przez użytkownika (Ctrl+C)"
                )
        except Exception as e:
            logger.error(f"Krytyczny błąd w monitorowaniu: {e}")
            if self.config.should_screenshot_on_error():
                self.debug_logger.save_error_snapshot(self.driver, e)
            raise