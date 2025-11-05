# Przewodnik Konfiguracji - Facebook Messenger Bot

## 📋 Wprowadzenie

Bot teraz obsługuje zaawansowaną konfigurację przez plik `bot_config.md`. Wszystkie ustawienia są automatycznie wczytywane przy starcie i używane przez `FacebookBot` i `MessengerMonitor`.

## 🚀 Jak to działa?

### 1. Parser Konfiguracji

Parser (`config/config_parser.py`) automatycznie:
- Wczytuje plik `bot_config.md`
- Ekstrahuje wszystkie bloki YAML z markdown
- Parsuje je i scala w jedną konfigurację
- Udostępnia wygodne metody dostępu do ustawień

### 2. Integracja z Botami

Zarówno `FacebookBot` jak i `MessengerMonitor` teraz:
- Przyjmują obiekt konfiguracji w konstruktorze
- Używają ustawień z konfiguracji zamiast stałych wartości
- Automatycznie dostosowują zachowanie do konfiguracji

## 📝 Struktura Konfiguracji

### Główne Sekcje w bot_config.md

```yaml
# 1. Tryb działania
mode: "monitor"  # monitor, interactive, extract, auto

# 2. Parametry monitorowania
polling_interval: 10
wait_timeout: 10
headless_mode: false

# 3. Zakres monitorowania
scope: "specific"  # all, specific, groups, private

# 4. Konkretne konwersacje
specific_conversations:
  - name: "Rafał Szuwalski"
    priority: "high"
    enabled: true
    actions: ["monitor", "save_messages", "notify"]

# 5. Monitoring
monitoring:
  enabled: true
  detect_new_messages: true
  detect_typing: false

# 6. Powiadomienia
notifications:
  enabled: true
  methods: ["console", "log_file"]
  triggers:
    on_new_message: true

# 7. Debug
debugging:
  enabled: true
  save_screenshots: true
  screenshot_on_error: true
  log_level: "INFO"

# 8. Bezpieczeństwo
security:
  respect_rate_limits: true
  random_delays: true
  min_delay: 1
  max_delay: 3
```

## 🔧 Jak Używać Konfiguracji

### Metoda 1: Edytuj bot_config.md (Zalecane)

Otwórz `bot_config.md` i edytuj bloki YAML w sekcjach:

1. **Sekcja 1: USTAWIENIA OGÓLNE** - tryb, harmonogram, parametry
2. **Sekcja 2: KONFIGURACJA KONWERSACJI** - zakres, konkretne konwersacje
3. **Sekcja 3: POBIERANIE DANYCH** - jakie dane zbierać
4. **Sekcja 4: FUNKCJE BOTA** - monitoring, powiadomienia
5. **Sekcja 7: ZAAWANSOWANE** - debug, bezpieczeństwo

Przykład:
```markdown
## 1. USTAWIENIA OGÓLNE

### 1.1 Tryb Działania
```yaml
mode: "monitor"
```

### 1.3 Parametry Monitorowania
```yaml
polling_interval: 10
wait_timeout: 10
headless_mode: false
```
```

### Metoda 2: Użyj czystego YAML (Opcjonalne)

1. Skopiuj `bot_config.example.yaml` jako `bot_config.yaml`
2. Edytuj `config/settings.py`, zmień:
   ```python
   CONFIG_FILE = os.path.join(BASE_DIR, "bot_config.yaml")  # zamiast bot_config.md
   ```

## 🎯 Przykłady Użycia

### Przykład 1: Monitorowanie konkretnej osoby

W `bot_config.md`, znajdź sekcję "2.2 Określone Konwersacje" i ustaw:

```yaml
scope: "specific"

specific_conversations:
  - name: "Rafał Szuwalski"
    priority: "high"
    enabled: true
    actions:
      - "monitor"
      - "save_messages"
      - "notify"
```

### Przykład 2: Tryb headless (bez okna przeglądarki)

W sekcji "1.3 Parametry Monitorowania":

```yaml
polling_interval: 10
wait_timeout: 10
headless_mode: true  # Zmień na true
```

### Przykład 3: Wyłącz zapisywanie screenshots

W sekcji "7.1 Debug i Logi":

```yaml
debugging:
  enabled: true
  save_screenshots: false  # Zmień na false
  screenshot_on_error: true
  log_level: "INFO"
```

### Przykład 4: Zmień interwał monitorowania

W sekcji "1.3 Parametry Monitorowania":

```yaml
polling_interval: 30  # Zmień na 30 sekund zamiast 10
wait_timeout: 10
headless_mode: false
```

## 📊 API Parsera Konfiguracji

### Dostęp do Konfiguracji

```python
from config import settings

# Pobierz cały obiekt config
config = settings.config

# Metody dostępu
mode = config.get_mode()                    # "monitor"
interval = config.get_polling_interval()     # 10
is_headless = config.is_headless()          # False
is_debug = config.is_debugging_enabled()    # True

# Dostęp przez notację kropkową
value = config.get('debugging.log_level')    # "INFO"
value = config.get('scope')                  # "specific"
```

### Dostępne Metody

```python
# Główne ustawienia
config.get_mode()                          # Tryb działania
config.get_polling_interval()              # Interwał monitorowania
config.get_wait_timeout()                  # Timeout oczekiwania
config.is_headless()                       # Czy headless mode

# Monitoring
config.is_monitoring_enabled()             # Czy monitoring włączony
config.should_detect_new_messages()        # Czy wykrywać nowe wiadomości
config.should_track_message_count()        # Czy śledzić licznik

# Powiadomienia
config.are_notifications_enabled()         # Czy powiadomienia włączone
config.get_notification_methods()          # Metody powiadamiania

# Debug
config.is_debugging_enabled()              # Czy debug włączony
config.should_save_screenshots()           # Czy zapisywać screenshots
config.should_screenshot_on_error()        # Czy screenshot przy błędzie
config.get_log_level()                     # Poziom logowania

# Bezpieczeństwo
config.should_use_random_delays()          # Czy losowe opóźnienia
config.get_min_delay()                     # Min opóźnienie
config.get_max_delay()                     # Max opóźnienie
```

## 🔄 Użycie w Kodzie

### FacebookBot

```python
from src.facebook_bot import FacebookBot
from config import settings

# Bot automatycznie używa konfiguracji
bot = FacebookBot(email, password, config=settings.config)

# Bot używa:
# - config.is_headless() dla trybu headless
# - config.get_wait_timeout() dla timeoutów
# - config.should_save_screenshots() dla debugowania
# - config.should_use_random_delays() dla opóźnień
```

### MessengerMonitor

```python
from src.messenger_monitor import MessengerMonitor
from config import settings

# Monitor automatycznie używa konfiguracji
monitor = MessengerMonitor(bot.driver, config=settings.config)

# Monitor używa:
# - config.get_polling_interval() dla interwału
# - config.is_monitoring_enabled() czy monitoring włączony
# - config.should_detect_new_messages() czy wykrywać wiadomości
# - config.are_notifications_enabled() czy powiadamiać
```

## ✅ Test Konfiguracji

Uruchom bota, aby zobaczyć załadowaną konfigurację:

```bash
python main.py
```

Zobaczysz:

```
============================================================
📋 KONFIGURACJA BOTA
============================================================
Tryb działania:        monitor
Zakres monitorowania:  specific
Interwał monitorowania: 10s
Tryb headless:         False
Debugging włączony:    True
Powiadomienia:         True

Monitorowane konwersacje (1):
  • Rafał Szuwalski (priorytet: high)
============================================================
```

## 🐛 Rozwiązywanie Problemów

### Problem: Parser nie znajduje bot_config.md

**Rozwiązanie:**
1. Upewnij się, że `bot_config.md` jest w głównym katalogu projektu
2. Sprawdź `config/settings.py`, czy `CONFIG_FILE` wskazuje na prawidłowy plik

### Problem: Błąd parsowania YAML

**Rozwiązanie:**
1. Sprawdź czy bloki YAML w `bot_config.md` są poprawnie sformatowane
2. Upewnij się, że używasz ```yaml na początku i ``` na końcu bloku
3. Sprawdź wcięcia (YAML wymaga spacji, nie tabulatorów)

### Problem: Domyślne ustawienia są używane

**Rozwiązanie:**
1. Sprawdź logi - jeśli widzisz "Załadowano domyślną konfigurację", parser nie znalazł pliku
2. Uruchom: `python -c "from config import settings; print(settings.config.get_all())"`
3. Sprawdź czy PyYAML jest zainstalowany: `pip install -r requirements.txt`

## 📚 Więcej Informacji

- Pełna dokumentacja konfiguracji: `bot_config.md`
- Przykładowy YAML: `bot_config.example.yaml`
- Kod parsera: `config/config_parser.py`

## 🔐 Uwagi Bezpieczeństwa

⚠️ **WAŻNE:**
- Nie commituj `bot_config.md` z prawdziwymi nazwami użytkowników do publicznego repo
- Szanuj prywatność innych użytkowników
- Używaj z ostrożnością funkcji automatycznych odpowiedzi
- Facebook może zablokować konto za nadmierną automatyzację
