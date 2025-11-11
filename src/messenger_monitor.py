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
        Filtruje konwersacje zgodnie z konfiguracją (scope i specific_conversations).
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
                        logger.info(f"   Rozpoczynam przetwarzanie elementów...")

                        element_count = 0
                        for element in chat_elements:
                            element_count += 1
                            try:
                                # Log progress for every element
                                logger.info(f"   ━━━ Element {element_count}/{len(chat_elements)} ━━━")

                                # Pobierz nazwę czatu
                                chat_name = None

                                # Próbuj różne metody pobrania nazwy
                                try:
                                    # Szukaj elementu span z nazwą użytkownika
                                    logger.info(f"      🔍 Szukam nazwy czatu (span[dir='auto'])...")
                                    name_element = element.find_element(By.CSS_SELECTOR, "span[dir='auto']")
                                    chat_name = name_element.text.strip()
                                    logger.info(f"      ✅ Znaleziono nazwę: '{chat_name}'")
                                except Exception as e:
                                    logger.info(f"      ⚠️ Brak span[dir='auto'], próbuję inne metody...")
                                    pass

                                if not chat_name:
                                    try:
                                        # Próbuj pobrać z aria-label
                                        logger.info(f"      🔍 Próbuję pobrać aria-label...")
                                        chat_name = element.get_attribute("aria-label")
                                        if chat_name:
                                            logger.info(f"      ✅ Znaleziono aria-label: '{chat_name}'")
                                        else:
                                            logger.info(f"      ⚠️ aria-label jest pusty")
                                    except Exception as e:
                                        logger.info(f"      ⚠️ Nie znaleziono aria-label")
                                        pass

                                if not chat_name:
                                    # Użyj całego tekstu elementu jako fallback
                                    logger.info(f"      🔍 Próbuję pobrać tekst elementu...")
                                    chat_name = element.text.strip()
                                    if chat_name:
                                        logger.info(f"      ✅ Znaleziono tekst: '{chat_name[:50]}{'...' if len(chat_name) > 50 else ''}'")
                                    else:
                                        logger.info(f"      ⚠️ Element bez tekstu")

                                # Pobierz URL czatu (jeśli istnieje)
                                chat_url = None
                                try:
                                    logger.info(f"      🔗 Szukam URL...")
                                    if element.tag_name == 'a':
                                        chat_url = element.get_attribute("href")
                                    else:
                                        link_element = element.find_element(By.TAG_NAME, "a")
                                        chat_url = link_element.get_attribute("href")

                                    if chat_url:
                                        # Skróć URL dla lepszej czytelności
                                        url_display = chat_url if len(chat_url) <= 60 else chat_url[:57] + "..."
                                        logger.info(f"      ✅ URL: {url_display}")
                                    else:
                                        logger.info(f"      ⚠️ URL jest pusty")
                                except Exception as e:
                                    logger.info(f"      ⚠️ Nie znaleziono URL")
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
                                        logger.info(f"      ✅ DODANO czat: '{chat_name}' (URL: {'TAK' if chat_url else 'NIE'})")
                                    elif not chat_url and not any(conv['name'] == chat_name for conv in conversations):
                                        # Fallback dla czatów bez URL - sprawdź po nazwie
                                        conversations.append({
                                            'name': chat_name,
                                            'url': chat_url,
                                            'element': element
                                        })
                                        logger.info(f"      ✅ DODANO czat (bez URL): '{chat_name}'")
                                    else:
                                        logger.info(f"      ⏭️ POMINIĘTO duplikat: '{chat_name}' (URL już istnieje)")
                                else:
                                    logger.info(f"      ⏭️ POMINIĘTO: element bez nazwy")

                            except Exception as e:
                                logger.warning(f"   ⚠️ Błąd podczas przetwarzania elementu {element_count}: {e}")
                                continue

                        logger.info(f"   ✅ Zakończono przetwarzanie {element_count} elementów")

                        # Jeśli znaleźliśmy czaty, przerwij pętlę selektorów
                        if conversations:
                            logger.info(f"   ✅ Zebrano {len(conversations)} unikalnych czatów")
                            break

                except Exception as e:
                    logger.warning(f"   ⚠️ Błąd dla selektora '{selector}': {e}")
                    continue

            # Filtruj według konfiguracji
            filtered_conversations = self._filter_conversations_by_config(conversations)

            logger.info(f"✅ Znaleziono {len(filtered_conversations)} czatów (po filtrowaniu)")
            return filtered_conversations

        except Exception as e:
            logger.error(f"Błąd podczas pobierania listy konwersacji: {e}")
            if self.config.should_screenshot_on_error():
                self.debug_logger.save_error_snapshot(self.driver, e)
            return []

    def _filter_conversations_by_config(self, conversations):
        """
        Filtruje konwersacje zgodnie z konfiguracją (scope i specific_conversations).

        Args:
            conversations: Lista wszystkich znalezionych konwersacji

        Returns:
            Lista przefiltrowanych konwersacji
        """
        scope = self.config.get_scope()

        # Jeśli scope = "all", zwróć wszystkie
        if scope == 'all':
            logger.info(f"   Scope: all - zwracam wszystkie {len(conversations)} konwersacji")
            return conversations

        # Jeśli scope = "specific", filtruj według specific_conversations
        if scope == 'specific':
            specific_convs = self.config.get_specific_conversations()

            if not specific_convs:
                logger.warning("   Scope: specific, ale brak specific_conversations w konfiguracji")
                return conversations

            # Pobierz nazwy włączonych konwersacji z konfiguracji
            enabled_names = []
            for conv_config in specific_convs:
                if conv_config.get('enabled', True):  # domyślnie enabled=True
                    enabled_names.append(conv_config.get('name', '').strip())

            logger.info(f"   Scope: specific - filtruję według {len(enabled_names)} nazw z konfiguracji")
            logger.info(f"   Szukane konwersacje: {enabled_names}")

            # Filtruj konwersacje które pasują do nazw z konfiguracji
            filtered = []
            for conv in conversations:
                conv_name = conv.get('name', '').strip()
                # Dopasowanie: sprawdź czy nazwa z konfiguracji zawiera się w nazwie czatu
                # lub odwrotnie (dla elastyczności)
                for enabled_name in enabled_names:
                    if enabled_name.lower() in conv_name.lower() or conv_name.lower() in enabled_name.lower():
                        filtered.append(conv)
                        logger.info(f"   ✅ Dopasowano: '{conv_name}' do config: '{enabled_name}'")
                        break

            if not filtered:
                logger.warning(f"   ⚠️ Nie znaleziono żadnych konwersacji pasujących do konfiguracji")
                logger.info(f"   Dostępne konwersacje: {[c['name'] for c in conversations[:10]]}")

            return filtered

        # Jeśli scope = "groups" lub inne, na razie zwróć wszystkie
        # (można później dodać rozróżnienie groups vs individual)
        logger.info(f"   Scope: {scope} - zwracam wszystkie {len(conversations)} konwersacji")
        return conversations

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
        - Zapisuje plik z pełną listą konwersacji w głównym folderze data/
        - Zapisuje metadane każdej konwersacji w osobnym folderze

        Args:
            conversations: Lista konwersacji (jeśli None, pobierze automatycznie)
            output_dir: Katalog wyjściowy (domyślnie 'data')

        Returns:
            dict: Słownik z informacjami o zapisanych plikach lub None w przypadku błędu
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

            # 1. ZAPISZ PEŁNĄ LISTĘ KONWERSACJI DO GŁÓWNEGO FOLDERU
            list_filename = f"conversations_list_{timestamp}.json"
            list_filepath = os.path.join(output_dir, list_filename)

            conversations_list = []
            for conv in conversations:
                conversations_list.append({
                    'name': conv.get('name'),
                    'url': conv.get('url'),
                })

            list_data = {
                'timestamp': datetime.now().isoformat(),
                'total_count': len(conversations_list),
                'conversations': conversations_list
            }

            with open(list_filepath, 'w', encoding='utf-8') as f:
                json.dump(list_data, f, ensure_ascii=False, indent=2)

            logger.info(f"✅ Zapisano listę {len(conversations_list)} konwersacji do: {list_filepath}")
            print(f"✅ Zapisano listę {len(conversations_list)} konwersacji do: {list_filepath}")

            # 2. ZAPISZ METADANE KAŻDEJ KONWERSACJI W OSOBNYM FOLDERZE
            saved_files = [list_filepath]
            saved_count = 0
            skipped_count = 0

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
            logger.info(f"✅ Zapisano metadane {saved_count} czatów do osobnych folderów")
            logger.info(f"   Pominiętych: {skipped_count}")
            print(f"✅ Zapisano metadane {saved_count} czatów do osobnych folderów")
            if skipped_count > 0:
                print(f"   Pominiętych: {skipped_count}")

            return {
                'list_file': list_filepath,
                'conversation_files': saved_files,
                'saved_count': saved_count,
                'skipped_count': skipped_count
            }

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

                        logger.info(f"   📜 Scroll {scroll_num + 1}/{max_scrolls}: pozycja przed={current_scroll}")

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

                        logger.info(f"      ➜ pozycja po={new_scroll}")

                        # Sprawdź czy pozycja się zmieniła
                        if current_scroll == new_scroll or new_scroll == 0:
                            no_change_count += 1
                            logger.info(f"      ⚠️ Brak zmiany pozycji (próba {no_change_count}/3)")
                            if no_change_count >= 3:
                                logger.info(f"   ✅ Osiągnięto początek konwersacji po {scroll_num + 1} scrollach")
                                break
                        else:
                            no_change_count = 0
                            logger.info(f"      ✅ Załadowano więcej wiadomości")

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
        Pobiera dane zgodnie z konfiguracją data_to_collect.

        Returns:
            list: Lista wiadomości (dictionaries z danymi wiadomości)
        """
        try:
            logger.info("📥 Ekstraktuję wiadomości z konwersacji...")

            # Sprawdź co powinno być pobierane z konfiguracji
            data_config = self.config.get('data_to_collect', {})
            messages_config = data_config.get('messages', {})
            media_config = data_config.get('media', {})
            metadata_config = data_config.get('metadata', {})

            include_reactions = messages_config.get('include_reactions', True)
            include_timestamps = messages_config.get('include_timestamps', True)
            include_sender_info = messages_config.get('include_sender_info', True)
            include_media = media_config.get('enabled', True)

            logger.info(f"   Konfiguracja: reactions={include_reactions}, timestamps={include_timestamps}, sender={include_sender_info}, media={include_media}")

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
                    # Log progress for every message
                    logger.info(f"   ━━━ Wiadomość {idx + 1}/{len(message_elements)} ━━━")

                    # Pobierz tekst wiadomości
                    logger.info(f"      📝 Pobieram tekst wiadomości...")
                    message_text = element.text.strip()
                    if message_text:
                        text_preview = message_text[:50] + "..." if len(message_text) > 50 else message_text
                        logger.info(f"      ✅ Tekst: '{text_preview}'")
                    else:
                        logger.info(f"      ⚠️ Brak tekstu")

                    # Pobierz aria-label (często zawiera dodatkowe info)
                    logger.info(f"      🔍 Pobieram aria-label...")
                    aria_label = element.get_attribute("aria-label")

                    # Podstawowe dane wiadomości
                    message_data = {
                        'index': idx,
                        'text': message_text,
                        'extracted_at': datetime.now().isoformat()
                    }

                    # Pobierz timestamp jeśli włączone
                    if include_timestamps:
                        logger.info(f"      🕐 Szukam timestamp...")
                        timestamp_element = None
                        try:
                            timestamp_element = element.find_element(By.CSS_SELECTOR, "span[aria-label*=':']")
                        except:
                            pass

                        timestamp = timestamp_element.get_attribute("aria-label") if timestamp_element else None
                        message_data['timestamp'] = timestamp
                        if timestamp:
                            logger.info(f"      ✅ Timestamp: {timestamp}")
                        else:
                            logger.info(f"      ⚠️ Brak timestamp")

                    # Pobierz info o nadawcy jeśli włączone
                    if include_sender_info and aria_label:
                        logger.info(f"      👤 Ekstraktuję info o nadawcy...")
                        message_data['aria_label'] = aria_label
                        # Spróbuj wyekstraktować nadawcę z aria-label
                        # Format: "You sent 'text'" lub "Name said 'text'"
                        if 'You sent' in aria_label or 'You said' in aria_label:
                            message_data['sender'] = 'You'
                        elif ' said ' in aria_label or ' sent ' in aria_label:
                            # Spróbuj wyodrębnić nazwę
                            sender_match = aria_label.split(' said ')[0] if ' said ' in aria_label else aria_label.split(' sent ')[0]
                            message_data['sender'] = sender_match.strip()
                        else:
                            message_data['sender'] = 'Unknown'
                        logger.info(f"      ✅ Sender: {message_data.get('sender')}")

                    # Pobierz media jeśli włączone
                    if include_media:
                        logger.info(f"      🖼️ Szukam mediów...")
                        media_links = self._extract_media_from_element(element, media_config)
                        if media_links:
                            message_data['media'] = media_links
                            logger.info(f"      ✅ Znaleziono {len(media_links)} mediów")
                        else:
                            logger.info(f"      ⚠️ Brak mediów")

                    # Pobierz reakcje jeśli włączone
                    if include_reactions:
                        logger.info(f"      😊 Szukam reakcji...")
                        reactions = self._extract_reactions_from_element(element)
                        if reactions:
                            message_data['reactions'] = reactions
                            logger.info(f"      ✅ Znaleziono {len(reactions)} reakcji")
                        else:
                            logger.info(f"      ⚠️ Brak reakcji")

                    # Dodaj wiadomość jeśli ma treść lub media
                    if message_text or (include_media and message_data.get('media')):
                        messages.append(message_data)
                        logger.info(f"      ✅ DODANO wiadomość do listy")
                    else:
                        logger.info(f"      ⏭️ POMINIĘTO: brak treści i mediów")

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

    def _extract_media_from_element(self, element, media_config):
        """
        Ekstraktuje linki do mediów z elementu wiadomości.

        Args:
            element: Element Selenium zawierający wiadomość
            media_config: Konfiguracja media z data_to_collect

        Returns:
            list: Lista dictionaries z informacjami o mediach
        """
        try:
            media_items = []
            media_types = media_config.get('types', ['images', 'videos', 'audio', 'documents'])

            # Szukaj obrazków
            if 'images' in media_types:
                try:
                    images = element.find_elements(By.CSS_SELECTOR, "img")
                    for img in images:
                        src = img.get_attribute("src")
                        if src and not src.startswith('data:'):  # Pomiń data URLs
                            media_items.append({
                                'type': 'image',
                                'url': src,
                                'alt': img.get_attribute("alt") or ''
                            })
                except:
                    pass

            # Szukaj video
            if 'videos' in media_types:
                try:
                    videos = element.find_elements(By.CSS_SELECTOR, "video")
                    for video in videos:
                        src = video.get_attribute("src")
                        if src:
                            media_items.append({
                                'type': 'video',
                                'url': src
                            })
                except:
                    pass

            # Szukaj audio
            if 'audio' in media_types:
                try:
                    audios = element.find_elements(By.CSS_SELECTOR, "audio")
                    for audio in audios:
                        src = audio.get_attribute("src")
                        if src:
                            media_items.append({
                                'type': 'audio',
                                'url': src
                            })
                except:
                    pass

            # Szukaj linków do dokumentów
            if 'documents' in media_types:
                try:
                    links = element.find_elements(By.CSS_SELECTOR, "a[href]")
                    for link in links:
                        href = link.get_attribute("href")
                        text = link.text.strip()
                        # Sprawdź czy to link do dokumentu (zawiera rozszerzenie pliku)
                        if href and any(ext in href.lower() for ext in ['.pdf', '.doc', '.docx', '.xls', '.xlsx', '.zip', '.rar']):
                            media_items.append({
                                'type': 'document',
                                'url': href,
                                'filename': text or href.split('/')[-1]
                            })
                except:
                    pass

            return media_items if media_items else None

        except Exception as e:
            logger.debug(f"Błąd podczas ekstraktowania mediów: {e}")
            return None

    def _extract_reactions_from_element(self, element):
        """
        Ekstraktuje reakcje z elementu wiadomości.

        Args:
            element: Element Selenium zawierający wiadomość

        Returns:
            list: Lista reakcji (emoji) lub None
        """
        try:
            reactions = []

            # Szukaj reakcji - różne selektory dla różnych wersji Messengera
            reaction_selectors = [
                "div[aria-label*='reaction']",
                "span[aria-label*='reaction']",
                "img[alt*='reaction']",
                "[data-reaction]"
            ]

            for selector in reaction_selectors:
                try:
                    reaction_elements = element.find_elements(By.CSS_SELECTOR, selector)
                    for react_elem in reaction_elements:
                        # Spróbuj pobrać emoji lub opis reakcji
                        aria_label = react_elem.get_attribute("aria-label")
                        alt_text = react_elem.get_attribute("alt")
                        data_reaction = react_elem.get_attribute("data-reaction")

                        reaction_text = aria_label or alt_text or data_reaction or react_elem.text.strip()
                        if reaction_text:
                            reactions.append(reaction_text)
                except:
                    continue

            return reactions if reactions else None

        except Exception as e:
            logger.debug(f"Błąd podczas ekstraktowania reakcji: {e}")
            return None

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
        Zachowanie zależy od trybu w konfiguracji:
        - 'extract': Scrolluje aby pobrać całą historię
        - 'interactive': Pobiera tylko widoczne wiadomości (bez scrollowania)

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

            # Sprawdź tryb działania
            mode = self.config.get_mode()
            should_scroll = mode == 'extract'  # Scrolluj tylko w trybie extract

            logger.info(f"🚀 Rozpoczynam ekstrakcję wiadomości z {len(conversations)} konwersacji...")
            logger.info(f"   Tryb: {mode} (scrollowanie: {'TAK' if should_scroll else 'NIE'})")
            print(f"\n🚀 Rozpoczynam ekstrakcję wiadomości z {len(conversations)} konwersacji...")
            print(f"   Tryb: {mode} (scrollowanie: {'TAK' if should_scroll else 'NIE'})")

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

                    logger.info(f"\n{'='*70}")
                    logger.info(f"[{idx}/{len(conversations)}] 💬 PRZETWARZAM KONWERSACJĘ: {conv_name}")
                    logger.info(f"{'='*70}")
                    print(f"\n[{idx}/{len(conversations)}] 💬 Przetwarzam: {conv_name}")

                    if not conv_url:
                        logger.warning(f"⚠️ Brak URL dla konwersacji: {conv_name}")
                        stats['failed'] += 1
                        continue

                    # Otwórz konwersację
                    logger.info(f"   🔗 Otwieram konwersację...")
                    if not self.open_conversation(conv_url):
                        logger.warning(f"   ❌ Nie udało się otworzyć konwersacji: {conv_name}")
                        stats['failed'] += 1
                        continue
                    logger.info(f"   ✅ Konwersacja otwarta")

                    # Scrolluj aby załadować wiadomości TYLKO w trybie extract
                    if should_scroll:
                        logger.info(f"   📜 Scrolluję aby pobrać całą historię (tryb: extract)")
                        self.scroll_and_load_messages()
                    else:
                        logger.info(f"   ⏭️  Pomijam scrollowanie (tryb: {mode})")

                    # Ekstraktuj wiadomości
                    logger.info(f"   📥 Rozpoczynam ekstrakcję wiadomości...")
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
            logger.info(f"Tryb:                         {mode}")
            logger.info(f"Całkowita liczba konwersacji: {stats['total']}")
            logger.info(f"Pomyślnie przetworzonych:     {stats['success']}")
            logger.info(f"Nieudanych:                   {stats['failed']}")
            logger.info(f"Łączna liczba wiadomości:     {stats['total_messages']}")
            logger.info(f"{'='*70}\n")

            print(f"\n{'='*70}")
            print(f"📊 PODSUMOWANIE EKSTRAKCJI")
            print(f"{'='*70}")
            print(f"Tryb:                         {mode}")
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