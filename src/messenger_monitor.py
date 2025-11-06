#src/messenger_monitor.py
"""
Klasa do monitorowania wiadomości w Messenger.
"""
import time
import os
import json
from datetime import datetime
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

    def get_all_conversations(self, max_scrolls=15, scroll_pause=1.0):
        """
        Pobiera listę wszystkich dostępnych konwersacji z Messengera.

        Args:
            max_scrolls: Maksymalna liczba przewinięć (domyślnie 15)
            scroll_pause: Czas pauzy między przewinięciami w sekundach (domyślnie 1.0s)
        """
        try:
            conversations = []

            # Różne selektory dla kontenera czatów (do scrollowania)
            container_selectors = [
                "div[role='navigation']",
                "div[aria-label='Chats']",
                "div[aria-label='Conversations']",
            ]

            # Znajdź kontener z czatami
            scroll_container = None
            for selector in container_selectors:
                try:
                    containers = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if containers:
                        scroll_container = containers[0]
                        logger.debug(f"Znaleziono kontener czatów: {selector}")
                        break
                except:
                    continue

            # Różne selektory dla elementów czatów (Facebook często zmienia interfejs)
            chat_selectors = [
                # Selektor dla kontenera z czatami
                "div[role='navigation'] div[role='grid'] div[role='gridcell']",
                "div[role='navigation'] a[role='link']",
                "div[aria-label*='Czat']",
                "div[aria-label*='Conversation']",
                # Fallback - ogólny selektor dla linków czatów
                "a[href*='/t/']",
            ]

            # Scrolluj i zbieraj czaty
            logger.info(f"🔄 Rozpoczynam scrollowanie aby załadować wszystkie czaty...")
            previous_count = 0
            no_change_count = 0
            seen_urls = set()  # Zbiór już przetworzonych URL-i dla szybszego sprawdzania duplikatów

            for scroll_iteration in range(max_scrolls):
                # Zbierz aktualnie widoczne czaty
                for selector in chat_selectors:
                    try:
                        chat_elements = self.driver.find_elements(By.CSS_SELECTOR, selector)

                        if chat_elements:
                            logger.info(f"   Znaleziono {len(chat_elements)} elementów DOM dla selektora: {selector}")

                            # Ogranicz liczbę przetwarzanych elementów aby przyspieszyć
                            # Przetwarzaj tylko pierwsze 50 elementów lub wszystkie jeśli mniej
                            elements_to_process = chat_elements[:50] if len(chat_elements) > 50 else chat_elements

                            for element in elements_to_process:
                                try:
                                    # Pobierz nazwę czatu
                                    chat_name = None

                                    # Próbuj różne metody pobrania nazwy
                                    try:
                                        # Szukaj elementu span z nazwą użytkownika
                                        name_element = element.find_element(By.CSS_SELECTOR, "span[dir='auto']")
                                        chat_name = name_element.text.strip()
                                    except:
                                        pass

                                    if not chat_name:
                                        try:
                                            # Próbuj pobrać z aria-label
                                            chat_name = element.get_attribute("aria-label")
                                        except:
                                            pass

                                    if not chat_name:
                                        # Użyj całego tekstu elementu jako fallback
                                        chat_name = element.text.strip()

                                    # Pobierz URL czatu (jeśli istnieje)
                                    chat_url = None
                                    try:
                                        if element.tag_name == 'a':
                                            chat_url = element.get_attribute("href")
                                        else:
                                            link_element = element.find_element(By.TAG_NAME, "a")
                                            chat_url = link_element.get_attribute("href")
                                    except:
                                        pass

                                    # Dodaj do listy jeśli mamy nazwę
                                    if chat_name and len(chat_name) > 0:
                                        # Usuń zbędne białe znaki
                                        chat_name = ' '.join(chat_name.split())

                                        # Użyj URL jako klucza unikalności (szybsze niż sprawdzanie nazw)
                                        if chat_url and chat_url not in seen_urls:
                                            seen_urls.add(chat_url)
                                            conversations.append({
                                                'name': chat_name,
                                                'url': chat_url,
                                                'element': element
                                            })
                                        elif not chat_url and not any(conv['name'] == chat_name for conv in conversations):
                                            # Fallback dla czatów bez URL - sprawdź po nazwie
                                            conversations.append({
                                                'name': chat_name,
                                                'url': chat_url,
                                                'element': element
                                            })

                                except Exception as e:
                                    logger.debug(f"Błąd podczas przetwarzania elementu czatu: {e}")
                                    continue

                            # Jeśli znaleźliśmy czaty, przerwij pętlę selektorów
                            if conversations:
                                break

                    except Exception as e:
                        logger.debug(f"Błąd dla selektora '{selector}': {e}")
                        continue

                current_count = len(conversations)
                logger.info(f"   Scroll {scroll_iteration + 1}/{max_scrolls}: Łącznie {current_count} unikalnych czatów")

                # Sprawdź czy liczba czatów się nie zmienia
                if current_count == previous_count:
                    no_change_count += 1
                    if no_change_count >= 3:  # Jeśli 3 razy z rzędu brak zmian, zakończ
                        logger.info(f"✅ Osiągnięto koniec listy czatów (brak nowych czatów przez 3 scrolle)")
                        break
                else:
                    no_change_count = 0

                previous_count = current_count

                # Scrolluj w dół
                try:
                    if scroll_container:
                        # Scrolluj w kontenerze czatów
                        self.driver.execute_script(
                            "arguments[0].scrollTop = arguments[0].scrollHeight",
                            scroll_container
                        )
                    else:
                        # Fallback - scrolluj całą stronę
                        self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

                    # Poczekaj na załadowanie nowych czatów
                    time.sleep(scroll_pause)

                except Exception as e:
                    logger.debug(f"Błąd podczas scrollowania: {e}")

            logger.info(f"✅ Zakończono scrollowanie. Łącznie znaleziono {len(conversations)} czatów")
            return conversations

        except Exception as e:
            logger.error(f"Błąd podczas pobierania listy konwersacji: {e}")
            if self.config.should_screenshot_on_error():
                self.debug_logger.save_error_snapshot(self.driver, e)
            return []

    def list_all_conversations(self):
        """Wyświetla w logach listę wszystkich dostępnych czatów."""
        logger.info("📋 Pobieranie listy wszystkich dostępnych czatów...")

        conversations = self.get_all_conversations()

        if not conversations:
            logger.warning("⚠️ Nie znaleziono żadnych czatów lub nie udało się ich pobrać")
            return

        logger.info(f"\n{'='*70}")
        logger.info(f"📬 DOSTĘPNE CZATY W MESSENGERZE ({len(conversations)})")
        logger.info(f"{'='*70}")

        for i, conv in enumerate(conversations, 1):
            name = conv.get('name', 'Nieznana nazwa')
            url = conv.get('url', 'Brak URL')

            # Skróć URL dla czytelności
            if url and len(url) > 50:
                url_display = url[:47] + "..."
            else:
                url_display = url

            logger.info(f"{i:3d}. {name}")
            if url and url != 'Brak URL':
                logger.info(f"      URL: {url_display}")

        logger.info(f"{'='*70}\n")

        # Zapisz snapshot z listą czatów (jeśli debugging włączony)
        if self.config.should_save_screenshots():
            additional_info = f"Znaleziono {len(conversations)} czatów:\n"
            for i, conv in enumerate(conversations[:10], 1):  # Pokaż pierwsze 10
                additional_info += f"{i}. {conv.get('name', 'Nieznana nazwa')}\n"
            if len(conversations) > 10:
                additional_info += f"... i {len(conversations) - 10} więcej"

            self.debug_logger.save_debug_snapshot(
                self.driver,
                "conversations_list",
                additional_info
            )

        return conversations

    def save_conversations_to_file(self, conversations=None, output_dir='data'):
        """
        Zapisuje listę wszystkich widocznych czatów do pliku w formacie JSON.

        Args:
            conversations: Lista konwersacji (jeśli None, pobierze automatycznie)
            output_dir: Katalog wyjściowy (domyślnie 'data')

        Returns:
            str: Ścieżka do zapisanego pliku lub None w przypadku błędu
        """
        try:
            # Pobierz konwersacje jeśli nie zostały podane
            if conversations is None:
                conversations = self.get_all_conversations()

            if not conversations:
                logger.warning("⚠️ Brak czatów do zapisania")
                return None

            # Utwórz katalog data jeśli nie istnieje
            os.makedirs(output_dir, exist_ok=True)

            # Wygeneruj nazwę pliku z timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"conversations_{timestamp}.json"
            filepath = os.path.join(output_dir, filename)

            # Przygotuj dane do zapisania (bez elementu Selenium)
            conversations_data = []
            for conv in conversations:
                conversations_data.append({
                    'name': conv.get('name'),
                    'url': conv.get('url'),
                    'timestamp': datetime.now().isoformat()
                })

            # Zapisz do pliku JSON
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump({
                    'timestamp': datetime.now().isoformat(),
                    'total_count': len(conversations_data),
                    'conversations': conversations_data
                }, f, ensure_ascii=False, indent=2)

            logger.info(f"✅ Zapisano {len(conversations_data)} czatów do pliku: {filepath}")
            print(f"✅ Zapisano {len(conversations_data)} czatów do pliku: {filepath}")

            return filepath

        except Exception as e:
            logger.error(f"❌ Błąd podczas zapisywania czatów do pliku: {e}")
            print(f"❌ Błąd podczas zapisywania czatów do pliku: {e}")
            return None

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