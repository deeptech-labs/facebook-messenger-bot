#config/config_parser.py
"""
Parser konfiguracji z bot_config.md.
Ekstrahuje bloki YAML z pliku markdown i udostępnia ustawienia jako słownik.
"""
import os
import re
import yaml
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class ConfigParser:
    """Parser konfiguracji z bot_config.md."""

    def __init__(self, config_file: str = "bot_config.md"):
        """
        Inicjalizuje parser konfiguracji.

        Args:
            config_file: Ścieżka do pliku konfiguracyjnego
        """
        self.config_file = config_file
        self.config = {}
        self._load_config()

    def _load_config(self):
        """Wczytuje i parsuje plik konfiguracyjny."""
        try:
            # Sprawdź czy plik istnieje
            if not os.path.exists(self.config_file):
                logger.warning(f"Plik konfiguracyjny {self.config_file} nie istnieje. Używam domyślnych ustawień.")
                self._load_defaults()
                return

            # Wczytaj zawartość pliku
            with open(self.config_file, 'r', encoding='utf-8') as f:
                content = f.read()

            # Ekstrahuj wszystkie bloki YAML z markdown
            yaml_blocks = self._extract_yaml_blocks(content)

            # Parsuj każdy blok YAML i scal w jeden słownik
            for yaml_block in yaml_blocks:
                try:
                    parsed = yaml.safe_load(yaml_block)
                    if parsed and isinstance(parsed, dict):
                        self._merge_config(self.config, parsed)
                except yaml.YAMLError as e:
                    logger.warning(f"Błąd parsowania bloku YAML: {e}")
                    continue

            logger.info(f"Załadowano konfigurację z {self.config_file}")

            # Jeśli nie udało się załadować żadnej konfiguracji, użyj domyślnej
            if not self.config:
                logger.warning("Nie znaleziono poprawnych bloków YAML. Używam domyślnych ustawień.")
                self._load_defaults()

        except Exception as e:
            logger.error(f"Błąd wczytywania konfiguracji: {e}")
            self._load_defaults()

    def _extract_yaml_blocks(self, content: str) -> list:
        """
        Ekstrahuje bloki YAML z markdown.

        Args:
            content: Zawartość pliku markdown

        Returns:
            Lista bloków YAML jako stringów
        """
        # Wzorzec regex do znajdowania bloków YAML
        # Szuka bloków między ```yaml i ```
        pattern = r'```yaml\s*\n(.*?)\n```'
        matches = re.findall(pattern, content, re.DOTALL)

        return matches

    def _merge_config(self, target: dict, source: dict):
        """
        Scala konfigurację rekurencyjnie.

        Args:
            target: Docelowy słownik
            source: Źródłowy słownik
        """
        for key, value in source.items():
            if key in target and isinstance(target[key], dict) and isinstance(value, dict):
                self._merge_config(target[key], value)
            else:
                target[key] = value

    def _load_defaults(self):
        """Wczytuje domyślną konfigurację."""
        self.config = {
            'mode': 'monitor',
            'polling_interval': 10,
            'wait_timeout': 10,
            'headless_mode': False,
            'scope': 'all',
            'specific_conversations': [],
            'filters': {
                'exclude_archived': True,
                'exclude_muted': False,
                'only_unread': False,
                'min_message_count': 0
            },
            'data_to_collect': {
                'messages': {
                    'enabled': True,
                    'include_reactions': True,
                    'include_timestamps': True,
                    'include_sender_info': True
                },
                'media': {
                    'enabled': True,
                    'types': ['images', 'videos', 'audio', 'documents'],
                    'download_files': False
                },
                'metadata': {
                    'enabled': True,
                    'include_read_status': True,
                    'include_delivery_status': True,
                    'include_conversation_info': True
                },
                'user_info': {
                    'enabled': False,
                    'fields': ['name', 'profile_picture', 'status']
                }
            },
            'monitoring': {
                'enabled': True,
                'detect_new_messages': True,
                'detect_typing': False,
                'detect_online_status': False,
                'track_message_count': True
            },
            'notifications': {
                'enabled': True,
                'methods': ['console', 'log_file'],
                'triggers': {
                    'on_new_message': True,
                    'on_specific_keywords': False,
                    'on_mention': False
                },
                'keywords': []
            },
            'auto_reply': {
                'enabled': False,
                'delay': 5,
                'rules': []
            },
            'on_new_message': {
                'actions': [
                    {'type': 'log', 'enabled': True},
                    {'type': 'mark_as_read', 'enabled': False},
                    {'type': 'save_to_file', 'enabled': True, 'file_path': './data/messages.txt', 'format': 'json'}
                ]
            },
            'debugging': {
                'enabled': True,
                'save_screenshots': True,
                'save_page_source': True,
                'screenshot_on_error': True,
                'verbose_logging': False,
                'log_level': 'INFO',
                'log_file': './logs/bot.log',
                'debug_dir': './debug_res/'
            },
            'security': {
                'respect_rate_limits': True,
                'random_delays': True,
                'min_delay': 1,
                'max_delay': 3,
                'max_actions_per_hour': 100,
                'max_messages_per_conversation': 50
            },
            'schedule': {
                'enabled': False,
                'active_hours': {
                    'start': '08:00',
                    'end': '22:00'
                },
                'active_days': [1, 2, 3, 4, 5]
            }
        }
        logger.info("Załadowano domyślną konfigurację")

    def get(self, key: str, default: Any = None) -> Any:
        """
        Pobiera wartość z konfiguracji.

        Args:
            key: Klucz w notacji kropkowej (np. 'debugging.enabled')
            default: Wartość domyślna jeśli klucz nie istnieje

        Returns:
            Wartość z konfiguracji lub wartość domyślna
        """
        keys = key.split('.')
        value = self.config

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default

        return value

    def get_all(self) -> Dict[str, Any]:
        """
        Zwraca całą konfigurację.

        Returns:
            Słownik z konfiguracją
        """
        return self.config

    def get_mode(self) -> str:
        """Zwraca tryb działania bota."""
        return self.get('mode', 'monitor')

    def get_polling_interval(self) -> int:
        """Zwraca interwał monitorowania."""
        return self.get('polling_interval', 10)

    def get_wait_timeout(self) -> int:
        """Zwraca timeout oczekiwania."""
        return self.get('wait_timeout', 10)

    def is_headless(self) -> bool:
        """Sprawdza czy przeglądarka ma działać w trybie headless."""
        return self.get('headless_mode', False)

    def get_scope(self) -> str:
        """Zwraca zakres monitorowania."""
        return self.get('scope', 'all')

    def get_specific_conversations(self) -> list:
        """Zwraca listę konkretnych konwersacji do monitorowania."""
        return self.get('specific_conversations', [])

    def is_monitoring_enabled(self) -> bool:
        """Sprawdza czy monitoring jest włączony."""
        return self.get('monitoring.enabled', True)

    def should_detect_new_messages(self) -> bool:
        """Sprawdza czy wykrywać nowe wiadomości."""
        return self.get('monitoring.detect_new_messages', True)

    def should_detect_typing(self) -> bool:
        """Sprawdza czy wykrywać pisanie."""
        return self.get('monitoring.detect_typing', False)

    def should_track_message_count(self) -> bool:
        """Sprawdza czy śledzić licznik wiadomości."""
        return self.get('monitoring.track_message_count', True)

    def are_notifications_enabled(self) -> bool:
        """Sprawdza czy powiadomienia są włączone."""
        return self.get('notifications.enabled', True)

    def get_notification_methods(self) -> list:
        """Zwraca metody powiadamiania."""
        return self.get('notifications.methods', ['console', 'log_file'])

    def is_auto_reply_enabled(self) -> bool:
        """Sprawdza czy automatyczne odpowiedzi są włączone."""
        return self.get('auto_reply.enabled', False)

    def get_auto_reply_delay(self) -> int:
        """Zwraca opóźnienie przed automatyczną odpowiedzią."""
        return self.get('auto_reply.delay', 5)

    def get_auto_reply_rules(self) -> list:
        """Zwraca reguły automatycznych odpowiedzi."""
        return self.get('auto_reply.rules', [])

    def is_debugging_enabled(self) -> bool:
        """Sprawdza czy debugging jest włączony."""
        return self.get('debugging.enabled', True)

    def should_save_screenshots(self) -> bool:
        """Sprawdza czy zapisywać zrzuty ekranu."""
        return self.get('debugging.save_screenshots', True)

    def should_screenshot_on_error(self) -> bool:
        """Sprawdza czy zapisywać zrzut ekranu przy błędzie."""
        return self.get('debugging.screenshot_on_error', True)

    def get_log_level(self) -> str:
        """Zwraca poziom logowania."""
        return self.get('debugging.log_level', 'INFO')

    def get_log_file(self) -> str:
        """Zwraca ścieżkę do pliku logów."""
        return self.get('debugging.log_file', './logs/bot.log')

    def get_debug_dir(self) -> str:
        """Zwraca katalog debugowania."""
        return self.get('debugging.debug_dir', './debug_res/')

    def should_respect_rate_limits(self) -> bool:
        """Sprawdza czy szanować limity częstotliwości."""
        return self.get('security.respect_rate_limits', True)

    def should_use_random_delays(self) -> bool:
        """Sprawdza czy używać losowych opóźnień."""
        return self.get('security.random_delays', True)

    def get_min_delay(self) -> int:
        """Zwraca minimalne opóźnienie."""
        return self.get('security.min_delay', 1)

    def get_max_delay(self) -> int:
        """Zwraca maksymalne opóźnienie."""
        return self.get('security.max_delay', 3)

    def is_schedule_enabled(self) -> bool:
        """Sprawdza czy harmonogram jest włączony."""
        return self.get('schedule.enabled', False)

    def get_active_hours(self) -> dict:
        """Zwraca godziny aktywności."""
        return self.get('schedule.active_hours', {'start': '08:00', 'end': '22:00'})

    def get_active_days(self) -> list:
        """Zwraca dni aktywności."""
        return self.get('schedule.active_days', [1, 2, 3, 4, 5])

    def __repr__(self):
        """Reprezentacja tekstowa."""
        return f"<ConfigParser mode={self.get_mode()} scope={self.get_scope()}>"
