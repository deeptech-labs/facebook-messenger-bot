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
from src.debug_logger import DebugLogger  # NOWE
import logging

logger = logging.getLogger(__name__)


class MessengerMonitor:
    def __init__(self, driver):
        self.driver = driver
        self.last_message_count = 0
        self.debug_logger = DebugLogger()  # NOWE
    
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
        """Sprawdza, czy są nowe wiadomości."""
        unread_conversations = self.get_unread_conversations()
        current_count = len(unread_conversations)
        
        if current_count > self.last_message_count:
            logger.info(f"Znaleziono nowe wiadomości! Liczba nieprzeczytanych rozmów: {current_count}")
            
            # NOWE: Zapisz debug snapshot przy nowych wiadomościach
            additional_info = f"Poprzednia liczba nieprzeczytanych: {self.last_message_count}\n"
            additional_info += f"Aktualna liczba nieprzeczytanych: {current_count}\n"
            additional_info += f"Nowych wiadomości: {current_count - self.last_message_count}\n"
            
            self.debug_logger.save_debug_snapshot(
                self.driver,
                "new_messages_detected",
                additional_info
            )
            
            # Tutaj możesz dodać logikę do przetwarzania nowych wiadomości
            self.last_message_count = current_count
            return True
        
        elif current_count < self.last_message_count:
            # NOWE: Zapisz gdy liczba nieprzeczytanych się zmniejszyła
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
    
    def run_monitoring_loop(self, interval):
        """Pętla monitorująca."""
        logger.info("Rozpoczynam pętlę monitorowania...")
        
        # NOWE: Zapisz initial state
        self.debug_logger.save_debug_snapshot(
            self.driver,
            "monitoring_start",
            f"Rozpoczęcie monitorowania z interwałem: {interval}s"
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
                    # NOWE: Zapisz błąd ale kontynuuj działanie
                    self.debug_logger.save_error_snapshot(self.driver, e)
                    time.sleep(interval)
                    
        except KeyboardInterrupt:
            logger.info("Zatrzymano monitorowanie przez użytkownika")
            # NOWE: Zapisz final state
            self.debug_logger.save_debug_snapshot(
                self.driver,
                "monitoring_stop",
                "Zakończenie monitorowania przez użytkownika (Ctrl+C)"
            )
        except Exception as e:
            logger.error(f"Krytyczny błąd w monitorowaniu: {e}")
            self.debug_logger.save_error_snapshot(self.driver, e)
            raise