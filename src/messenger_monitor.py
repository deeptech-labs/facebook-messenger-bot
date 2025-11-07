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
import re

logger = logging.getLogger(__name__)


def sanitize_folder_name(name):
    """
    Sanityzuje nazwę folderu, usuwając niedozwolone znaki.

    Args:
        name: Nazwa do sanityzacji

    Returns:
        str: Bezpieczna nazwa folderu
    """
    if not name:
        return "unknown"

    # Usuń niedozwolone znaki z nazwy folderu
    # Dozwolone: litery, cyfry, spacje, myślniki, podkreślniki
    sanitized = re.sub(r'[<>:"/\\|?*]', '', name)

    # Zamień wielokrotne spacje na pojedyncze
    sanitized = re.sub(r'\s+', ' ', sanitized)

    # Usuń spacje z początku i końca
    sanitized = sanitized.strip()

    # Zamień spacje na podkreślniki
    sanitized = sanitized.replace(' ', '_')

    # Ogranicz długość nazwy do 100 znaków
    sanitized = sanitized[:100]

    # Jeśli po sanityzacji nic nie zostało, użyj "unknown"
    if not sanitized:
        return "unknown"

    return sanitized


class MessengerMonitor:
    def __init__(self, driver, config=None):
        self.driver = driver
        self.config = config if config else settings.config
        self.last_message_count = 0
        self.debug_logger = DebugLogger()

        # Loguj konfigurację monitorowania
        logger.info(f"Monitor zainicjalizowany - tryb: {self.config.get_mode()}, zakres: {self.config.get_scope()}")

    def get_all_conversations(self):
        """
        Pobiera listę widocznych konwersacji z Messengera (bez scrollowania).
        """
        try:
            conversations = []
            seen_urls = set()

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

            logger.info(f"📋 Pobieranie widocznych czatów...")

            # Zbierz aktualnie widoczne czaty
            for selector in chat_selectors:
                try:
                    chat_elements = self.driver.find_elements(By.CSS_SELECTOR, selector)

                    if chat_elements:
                        logger.info(f"   Znaleziono {len(chat_elements)} elementów DOM dla selektora: {selector}")

                        for element in chat_elements:
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

                                    # Użyj URL jako klucza unikalności
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
                            logger.info(f"   ✅ Zebrano {len(conversations)} unikalnych czatów")
                            break

                except Exception as e:
                    logger.warning(f"   ⚠️ Błąd dla selektora '{selector}': {e}")
                    continue

            logger.info(f"✅ Znaleziono {len(conversations)} czatów")
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
        Zapisuje listę wszystkich widocznych czatów do plików w formacie JSON.
        Każda konwersacja jest zapisywana w osobnym folderze.

        Args:
            conversations: Lista konwersacji (jeśli None, pobierze automatycznie)
            output_dir: Katalog wyjściowy (domyślnie 'data')

        Returns:
            list: Lista ścieżek do zapisanych plików lub None w przypadku błędu
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

            # Wygeneruj timestamp dla tej sesji zapisywania
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

            saved_files = []
            saved_count = 0
            skipped_count = 0

            # Zapisz każdą konwersację w osobnym folderze
            for conv in conversations:
                try:
                    # Pobierz nazwę konwersacji
                    conv_name = conv.get('name')
                    if not conv_name:
                        skipped_count += 1
                        logger.warning("⚠️ Pominięto konwersację bez nazwy")
                        continue

                    # Sanityzuj nazwę folderu
                    folder_name = sanitize_folder_name(conv_name)

                    # Utwórz folder dla konwersacji
                    conv_dir = os.path.join(output_dir, folder_name)
                    os.makedirs(conv_dir, exist_ok=True)

                    # Wygeneruj nazwę pliku z timestamp
                    filename = f"conversation_{timestamp}.json"
                    filepath = os.path.join(conv_dir, filename)

                    # Przygotuj dane do zapisania
                    conversation_data = {
                        'name': conv.get('name'),
                        'url': conv.get('url'),
                        'timestamp': datetime.now().isoformat(),
                        'folder': folder_name
                    }

                    # Zapisz do pliku JSON
                    with open(filepath, 'w', encoding='utf-8') as f:
                        json.dump(conversation_data, f, ensure_ascii=False, indent=2)

                    saved_files.append(filepath)
                    saved_count += 1
                    logger.debug(f"✅ Zapisano konwersację '{conv_name}' do: {filepath}")

                except Exception as e:
                    skipped_count += 1
                    logger.error(f"❌ Błąd podczas zapisywania konwersacji '{conv.get('name', 'unknown')}': {e}")
                    continue

            # Podsumowanie
            logger.info(f"✅ Zapisano {saved_count} czatów w folderze: {output_dir}")
            logger.info(f"   Pominiętych: {skipped_count}")
            print(f"✅ Zapisano {saved_count} czatów w folderze: {output_dir}")
            if skipped_count > 0:
                print(f"   Pominiętych: {skipped_count}")

            return saved_files

        except Exception as e:
            logger.error(f"❌ Błąd podczas zapisywania czatów do plików: {e}")
            print(f"❌ Błąd podczas zapisywania czatów do plików: {e}")
            return None

    def open_conversation(self, conversation_url, wait_time=3):
        """
        Otwiera konkretną konwersację używając URL.

        Args:
            conversation_url: URL konwersacji do otwarcia
            wait_time: Czas oczekiwania po otwarciu (w sekundach)

        Returns:
            bool: True jeśli konwersacja została otwarta, False w przeciwnym razie
        """
        try:
            if not conversation_url:
                logger.warning("⚠️ Brak URL konwersacji")
                return False

            logger.info(f"🔗 Otwieranie konwersacji: {conversation_url}")
            self.driver.get(conversation_url)
            time.sleep(wait_time)

            # Sprawdź czy udało się otworzyć konwersację
            current_url = self.driver.current_url
            if "messages/t/" in current_url or "messenger.com" in current_url:
                logger.info("✅ Konwersacja otwarta pomyślnie")
                return True
            else:
                logger.warning(f"⚠️ Nie udało się otworzyć konwersacji. Current URL: {current_url}")
                return False

        except Exception as e:
            logger.error(f"❌ Błąd podczas otwierania konwersacji: {e}")
            if self.config.should_screenshot_on_error():
                self.debug_logger.save_error_snapshot(self.driver, e)
            return False

    def scroll_and_load_messages(self, max_scrolls=50, scroll_pause=2.0):
        """
        Scrolluje konwersację w górę aby załadować starsze wiadomości.

        Args:
            max_scrolls: Maksymalna liczba przewinięć
            scroll_pause: Pauza między przewinięciami (w sekundach)

        Returns:
            bool: True jeśli scrollowanie zakończyło się pomyślnie
        """
        try:
            logger.info(f"📜 Rozpoczynam scrollowanie wiadomości (max {max_scrolls} scrolli)...")

            # Znajdź kontener z wiadomościami
            message_container_selectors = [
                "div[role='main']",
                "div[aria-label='Messages']",
                "div[aria-label='Wiadomości']",
            ]

            message_container = None
            for selector in message_container_selectors:
                try:
                    containers = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if containers:
                        message_container = containers[0]
                        logger.debug(f"Znaleziono kontener wiadomości: {selector}")
                        break
                except:
                    continue

            previous_height = 0
            no_change_count = 0

            for scroll_num in range(max_scrolls):
                try:
                    # Scrolluj do góry kontenera
                    if message_container:
                        current_scroll = self.driver.execute_script(
                            "return arguments[0].scrollTop",
                            message_container
                        )

                        # Scrolluj do samej góry
                        self.driver.execute_script(
                            "arguments[0].scrollTop = 0",
                            message_container
                        )

                        time.sleep(scroll_pause)

                        new_scroll = self.driver.execute_script(
                            "return arguments[0].scrollTop",
                            message_container
                        )

                        # Sprawdź czy pozycja się zmieniła
                        if current_scroll == new_scroll or new_scroll == 0:
                            no_change_count += 1
                            if no_change_count >= 3:
                                logger.info(f"✅ Osiągnięto początek konwersacji po {scroll_num + 1} scrollach")
                                break
                        else:
                            no_change_count = 0

                        logger.debug(f"   Scroll {scroll_num + 1}/{max_scrolls}: position {new_scroll}")

                except Exception as e:
                    logger.debug(f"Błąd podczas scrollowania: {e}")
                    continue

            logger.info("✅ Scrollowanie zakończone")
            return True

        except Exception as e:
            logger.error(f"❌ Błąd podczas scrollowania wiadomości: {e}")
            if self.config.should_screenshot_on_error():
                self.debug_logger.save_error_snapshot(self.driver, e)
            return False

    def extract_messages_from_conversation(self):
        """
        Ekstraktuje wiadomości z aktualnie otwartej konwersacji.

        Returns:
            list: Lista wiadomości (dictionaries z danymi wiadomości)
        """
        try:
            logger.info("📥 Ekstraktuję wiadomości z konwersacji...")

            messages = []

            # Różne selektory dla wiadomości
            message_selectors = [
                "div[role='row']",
                "div[data-scope='messages_table']",
                "div[aria-label*='You sent']",
                "div[aria-label*='said']",
            ]

            message_elements = []
            for selector in message_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if elements:
                        message_elements = elements
                        logger.debug(f"Znaleziono {len(elements)} elementów wiadomości dla selektora: {selector}")
                        break
                except:
                    continue

            if not message_elements:
                logger.warning("⚠️ Nie znaleziono żadnych wiadomości")
                return messages

            logger.info(f"📊 Przetwarzam {len(message_elements)} elementów wiadomości...")

            for idx, element in enumerate(message_elements):
                try:
                    # Pobierz tekst wiadomości
                    message_text = element.text.strip()

                    # Pobierz aria-label (często zawiera dodatkowe info)
                    aria_label = element.get_attribute("aria-label")

                    # Pobierz timestamp jeśli dostępny
                    timestamp_element = None
                    try:
                        timestamp_element = element.find_element(By.CSS_SELECTOR, "span[aria-label*=':']")
                    except:
                        pass

                    timestamp = timestamp_element.get_attribute("aria-label") if timestamp_element else None

                    # Dodaj wiadomość jeśli ma treść
                    if message_text and len(message_text) > 0:
                        message_data = {
                            'index': idx,
                            'text': message_text,
                            'aria_label': aria_label,
                            'timestamp': timestamp,
                            'extracted_at': datetime.now().isoformat()
                        }
                        messages.append(message_data)

                except Exception as e:
                    logger.debug(f"Błąd podczas przetwarzania wiadomości {idx}: {e}")
                    continue

            logger.info(f"✅ Wyekstraktowano {len(messages)} wiadomości")
            return messages

        except Exception as e:
            logger.error(f"❌ Błąd podczas ekstraktowania wiadomości: {e}")
            if self.config.should_screenshot_on_error():
                self.debug_logger.save_error_snapshot(self.driver, e)
            return []

    def save_messages_to_folder(self, messages, conversation_name, output_dir='data'):
        """
        Zapisuje wiadomości do folderu konwersacji.

        Args:
            messages: Lista wiadomości do zapisania
            conversation_name: Nazwa konwersacji
            output_dir: Katalog bazowy (domyślnie 'data')

        Returns:
            str: Ścieżka do zapisanego pliku lub None
        """
        try:
            if not messages:
                logger.warning("⚠️ Brak wiadomości do zapisania")
                return None

            # Sanityzuj nazwę folderu
            folder_name = sanitize_folder_name(conversation_name)

            # Utwórz folder dla konwersacji
            conv_dir = os.path.join(output_dir, folder_name)
            os.makedirs(conv_dir, exist_ok=True)

            # Wygeneruj nazwę pliku z timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"messages_{timestamp}.json"
            filepath = os.path.join(conv_dir, filename)

            # Przygotuj dane do zapisania
            data = {
                'conversation_name': conversation_name,
                'folder': folder_name,
                'message_count': len(messages),
                'extracted_at': datetime.now().isoformat(),
                'messages': messages
            }

            # Zapisz do pliku JSON
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            logger.info(f"✅ Zapisano {len(messages)} wiadomości do: {filepath}")
            print(f"✅ Zapisano {len(messages)} wiadomości do: {filepath}")

            return filepath

        except Exception as e:
            logger.error(f"❌ Błąd podczas zapisywania wiadomości: {e}")
            print(f"❌ Błąd podczas zapisywania wiadomości: {e}")
            return None

    def extract_and_save_all_conversations(self, conversations=None, output_dir='data', max_conversations=None):
        """
        Ekstraktuje i zapisuje wiadomości ze wszystkich konwersacji.

        Args:
            conversations: Lista konwersacji (jeśli None, pobierze automatycznie)
            output_dir: Katalog wyjściowy
            max_conversations: Maksymalna liczba konwersacji do przetworzenia (None = wszystkie)

        Returns:
            dict: Statystyki ekstrakcji
        """
        try:
            # Pobierz konwersacje jeśli nie zostały podane
            if conversations is None:
                conversations = self.get_all_conversations()

            if not conversations:
                logger.warning("⚠️ Brak konwersacji do przetworzenia")
                return None

            # Ogranicz liczbę konwersacji jeśli podano
            if max_conversations:
                conversations = conversations[:max_conversations]

            logger.info(f"🚀 Rozpoczynam ekstrakcję wiadomości z {len(conversations)} konwersacji...")
            print(f"\n🚀 Rozpoczynam ekstrakcję wiadomości z {len(conversations)} konwersacji...")

            stats = {
                'total': len(conversations),
                'success': 0,
                'failed': 0,
                'total_messages': 0
            }

            for idx, conv in enumerate(conversations, 1):
                try:
                    conv_name = conv.get('name', 'Unknown')
                    conv_url = conv.get('url')

                    logger.info(f"\n[{idx}/{len(conversations)}] Przetwarzam: {conv_name}")
                    print(f"\n[{idx}/{len(conversations)}] Przetwarzam: {conv_name}")

                    if not conv_url:
                        logger.warning(f"⚠️ Brak URL dla konwersacji: {conv_name}")
                        stats['failed'] += 1
                        continue

                    # Otwórz konwersację
                    if not self.open_conversation(conv_url):
                        logger.warning(f"⚠️ Nie udało się otworzyć konwersacji: {conv_name}")
                        stats['failed'] += 1
                        continue

                    # Scrolluj aby załadować wiadomości
                    self.scroll_and_load_messages()

                    # Ekstraktuj wiadomości
                    messages = self.extract_messages_from_conversation()

                    if messages:
                        # Zapisz wiadomości
                        self.save_messages_to_folder(messages, conv_name, output_dir)
                        stats['success'] += 1
                        stats['total_messages'] += len(messages)
                        logger.info(f"✅ Pomyślnie przetworzono: {conv_name} ({len(messages)} wiadomości)")
                    else:
                        logger.warning(f"⚠️ Brak wiadomości w konwersacji: {conv_name}")
                        stats['failed'] += 1

                    # Krótka pauza między konwersacjami
                    time.sleep(2)

                except Exception as e:
                    logger.error(f"❌ Błąd podczas przetwarzania konwersacji '{conv_name}': {e}")
                    stats['failed'] += 1
                    continue

            # Podsumowanie
            logger.info(f"\n{'='*70}")
            logger.info(f"📊 PODSUMOWANIE EKSTRAKCJI")
            logger.info(f"{'='*70}")
            logger.info(f"Całkowita liczba konwersacji: {stats['total']}")
            logger.info(f"Pomyślnie przetworzonych:     {stats['success']}")
            logger.info(f"Nieudanych:                   {stats['failed']}")
            logger.info(f"Łączna liczba wiadomości:     {stats['total_messages']}")
            logger.info(f"{'='*70}\n")

            print(f"\n{'='*70}")
            print(f"📊 PODSUMOWANIE EKSTRAKCJI")
            print(f"{'='*70}")
            print(f"Całkowita liczba konwersacji: {stats['total']}")
            print(f"Pomyślnie przetworzonych:     {stats['success']}")
            print(f"Nieudanych:                   {stats['failed']}")
            print(f"Łączna liczba wiadomości:     {stats['total_messages']}")
            print(f"{'='*70}\n")

            return stats

        except Exception as e:
            logger.error(f"❌ Błąd podczas ekstrakcji konwersacji: {e}")
            if self.config.should_screenshot_on_error():
                self.debug_logger.save_error_snapshot(self.driver, e)
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